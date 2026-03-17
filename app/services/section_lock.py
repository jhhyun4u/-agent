"""
섹션 동시 편집 잠금 서비스 (§24)

제안서 섹션별 배타적 잠금 관리. 5분 자동 해제.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from app.exceptions import SectLockConflictError
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

LOCK_DURATION_MINUTES = 5


async def acquire_lock(
    proposal_id: str,
    section_id: str,
    user_id: str,
) -> dict[str, Any]:
    """섹션 잠금 획득.

    이미 잠긴 경우 SectLockConflictError 발생 (다른 사용자).
    같은 사용자의 기존 잠금은 갱신.

    Returns:
        {"acquired": True, "locked_by": user_id, "locked_at": ISO, "expires_at": ISO}
    """
    client = await get_async_client()
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=LOCK_DURATION_MINUTES)

    # 만료 잠금 정리
    await _cleanup_expired(client, proposal_id)

    # 기존 잠금 확인
    existing = (
        await client.table("section_locks")
        .select("*")
        .eq("proposal_id", proposal_id)
        .eq("section_id", section_id)
        .maybe_single()
        .execute()
    )

    if existing.data:
        lock = existing.data
        # 같은 사용자면 갱신
        if lock["locked_by"] == user_id:
            await (
                client.table("section_locks")
                .update({
                    "locked_at": now.isoformat(),
                    "expires_at": expires_at.isoformat(),
                })
                .eq("id", lock["id"])
                .execute()
            )
            return {
                "acquired": True,
                "locked_by": user_id,
                "locked_at": now.isoformat(),
                "expires_at": expires_at.isoformat(),
            }

        # 다른 사용자 — 잠금 충돌
        # 사용자 이름 조회
        locker = (
            await client.table("users")
            .select("name")
            .eq("id", lock["locked_by"])
            .maybe_single()
            .execute()
        )
        locker_name = locker.data.get("name", lock["locked_by"]) if locker.data else lock["locked_by"]
        raise SectLockConflictError(
            locked_by=locker_name,
            locked_at=lock["locked_at"],
            expires_at=lock["expires_at"],
        )

    # 새 잠금 생성
    await (
        client.table("section_locks")
        .insert({
            "proposal_id": proposal_id,
            "section_id": section_id,
            "locked_by": user_id,
            "locked_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        })
        .execute()
    )

    logger.debug(f"섹션 잠금 획득: {proposal_id}/{section_id} by {user_id}")
    return {
        "acquired": True,
        "locked_by": user_id,
        "locked_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
    }


async def release_lock(
    proposal_id: str,
    section_id: str,
    user_id: str,
) -> bool:
    """섹션 잠금 해제. 본인 잠금만 해제 가능."""
    client = await get_async_client()

    result = (
        await client.table("section_locks")
        .delete()
        .eq("proposal_id", proposal_id)
        .eq("section_id", section_id)
        .eq("locked_by", user_id)
        .execute()
    )

    released = bool(result.data)
    if released:
        logger.debug(f"섹션 잠금 해제: {proposal_id}/{section_id} by {user_id}")
    return released


async def get_locks(proposal_id: str) -> list[dict[str, Any]]:
    """제안서의 모든 활성 잠금 목록 조회."""
    client = await get_async_client()
    now = datetime.now(timezone.utc).isoformat()

    result = (
        await client.table("section_locks")
        .select("section_id, locked_by, locked_at, expires_at")
        .eq("proposal_id", proposal_id)
        .gt("expires_at", now)
        .execute()
    )
    return result.data or []


async def force_release(proposal_id: str, section_id: str) -> bool:
    """관리자용 강제 잠금 해제."""
    client = await get_async_client()
    result = (
        await client.table("section_locks")
        .delete()
        .eq("proposal_id", proposal_id)
        .eq("section_id", section_id)
        .execute()
    )
    return bool(result.data)


async def _cleanup_expired(client: Any, proposal_id: str) -> None:
    """만료된 잠금 정리."""
    now = datetime.now(timezone.utc).isoformat()
    try:
        await (
            client.table("section_locks")
            .delete()
            .eq("proposal_id", proposal_id)
            .lt("expires_at", now)
            .execute()
        )
    except Exception as e:
        logger.debug(f"만료 잠금 정리 실패 (무시): {e}")
