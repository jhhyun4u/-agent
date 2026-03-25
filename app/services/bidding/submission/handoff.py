"""
투찰 핸드오프 서비스

bid_plan 확정 → DB 저장 → artifact 기록 → 알림 → 투찰 기록 관리.
워크플로에서 확정된 입찰가를 proposals 테이블에 persist하고,
투찰 담당자에게 전달하여 나라장터 투찰까지 추적한다.
"""

import json
import logging
from datetime import datetime, timezone

from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


async def persist_bid_confirmation(
    proposal_id: str,
    bid_price: int,
    bid_ratio: float,
    scenario_name: str,
    user_id: str,
    user_name: str = "",
    override_reason: str = "",
    bid_plan_data: dict | None = None,
) -> None:
    """bid_plan 리뷰 승인 시 호출: 확정가를 proposals 테이블에 저장 + 이력 기록."""
    client = await get_async_client()
    now = datetime.now(timezone.utc).isoformat()

    # 1. proposals 테이블 업데이트
    res = await (
        client.table("proposals")
        .update({
            "bid_confirmed_price": bid_price,
            "bid_confirmed_ratio": bid_ratio,
            "bid_confirmed_scenario": scenario_name,
            "bid_confirmed_at": now,
            "bid_confirmed_by": user_id,
            "bid_amount": bid_price,
            "bid_submission_status": "ready",
            "updated_at": now,
        })
        .eq("id", proposal_id)
        .execute()
    )
    if not res.data:
        logger.warning(f"bid 확정 DB 업데이트 0건: proposal_id={proposal_id}")

    # 2. bid_price_history 이력 기록
    event_type = "override" if override_reason else "confirmed"
    await client.table("bid_price_history").insert({
        "proposal_id": proposal_id,
        "event_type": event_type,
        "price": bid_price,
        "ratio": bid_ratio,
        "scenario_name": scenario_name,
        "reason": override_reason or f"{scenario_name} 시나리오 선택",
        "actor_id": user_id,
        "actor_name": user_name,
        "metadata": json.dumps({
            "data_quality": (bid_plan_data or {}).get("data_quality", ""),
            "win_probability": (bid_plan_data or {}).get("win_probability", 0),
        }, ensure_ascii=False),
    }).execute()

    # 3. artifacts 테이블에 bid_plan 산출물 저장
    if bid_plan_data:
        await _save_bid_plan_artifact(proposal_id, bid_plan_data, user_id)

    logger.info(
        f"입찰가 확정: proposal={proposal_id}, "
        f"price={bid_price:,}원, ratio={bid_ratio}%, scenario={scenario_name}"
    )


async def _save_bid_plan_artifact(
    proposal_id: str,
    bid_plan_data: dict,
    user_id: str,
) -> None:
    """bid_plan 결과를 artifacts 테이블에 저장."""
    client = await get_async_client()

    # 기존 버전 조회
    ver_res = await (
        client.table("artifacts")
        .select("version")
        .eq("proposal_id", proposal_id)
        .eq("step", "bid_plan")
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    next_ver = (ver_res.data[0]["version"] + 1) if ver_res.data else 1

    content_str = json.dumps(bid_plan_data, ensure_ascii=False, default=str)
    await client.table("artifacts").insert({
        "proposal_id": proposal_id,
        "step": "bid_plan",
        "version": next_ver,
        "content": content_str[:50000],
        "change_source": "workflow_confirmed",
        "change_summary": f"입찰가 확정 v{next_ver}",
        "created_by": user_id,
    }).execute()


async def record_bid_submission(
    proposal_id: str,
    submitted_price: int,
    user_id: str,
    user_name: str = "",
    note: str = "",
) -> dict:
    """투찰 담당자가 나라장터에 실제 투찰한 가격 기록."""
    client = await get_async_client()
    now = datetime.now(timezone.utc).isoformat()

    # proposals 업데이트
    await (
        client.table("proposals")
        .update({
            "bid_submitted_price": submitted_price,
            "bid_submitted_at": now,
            "bid_submitted_by": user_id,
            "bid_submission_note": note,
            "bid_submission_status": "submitted",
            "updated_at": now,
        })
        .eq("id", proposal_id)
        .execute()
    )

    # 이력 기록
    await client.table("bid_price_history").insert({
        "proposal_id": proposal_id,
        "event_type": "submitted",
        "price": submitted_price,
        "reason": note or "나라장터 투찰 완료",
        "actor_id": user_id,
        "actor_name": user_name,
    }).execute()

    logger.info(f"투찰 기록: proposal={proposal_id}, price={submitted_price:,}원")
    return {"status": "submitted", "submitted_at": now}


async def verify_bid_submission(
    proposal_id: str,
    user_id: str,
    user_name: str = "",
) -> dict:
    """투찰 완료 확인 (팀장/관리자)."""
    client = await get_async_client()
    now = datetime.now(timezone.utc).isoformat()

    # 실제 투찰가 조회 (price=0 오염 방지)
    prop = await (
        client.table("proposals")
        .select("bid_submitted_price, bid_submission_status")
        .eq("id", proposal_id)
        .single()
        .execute()
    )
    if not prop.data:
        raise ValueError(f"proposal {proposal_id} not found")
    submitted_price = prop.data.get("bid_submitted_price") or 0

    await (
        client.table("proposals")
        .update({
            "bid_submission_status": "verified",
            "updated_at": now,
        })
        .eq("id", proposal_id)
        .execute()
    )

    await client.table("bid_price_history").insert({
        "proposal_id": proposal_id,
        "event_type": "verified",
        "price": submitted_price,
        "reason": "투찰 완료 확인",
        "actor_id": user_id,
        "actor_name": user_name,
    }).execute()

    return {"status": "verified", "verified_at": now}


async def get_bid_price_history(proposal_id: str) -> list[dict]:
    """투찰가 변경 이력 조회."""
    client = await get_async_client()
    res = await (
        client.table("bid_price_history")
        .select("*")
        .eq("proposal_id", proposal_id)
        .order("created_at", desc=True)
        .execute()
    )
    return res.data or []


async def get_bid_submission_status(proposal_id: str) -> dict:
    """투찰 상태 조회."""
    client = await get_async_client()
    res = await (
        client.table("proposals")
        .select(
            "bid_confirmed_price, bid_confirmed_ratio, bid_confirmed_scenario, "
            "bid_confirmed_at, bid_confirmed_by, "
            "bid_submitted_price, bid_submitted_at, bid_submitted_by, "
            "bid_submission_note, bid_submission_status"
        )
        .eq("id", proposal_id)
        .single()
        .execute()
    )
    return res.data or {}
