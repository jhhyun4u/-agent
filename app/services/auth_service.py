"""
인증 서비스 (§17-1)

Azure AD(Entra ID) + Supabase Auth OAuth 흐름:
1. 프론트엔드에서 Supabase Auth signInWithOAuth(azure) 호출
2. Azure AD 로그인 → Supabase Auth callback → JWT 발급
3. FastAPI에서 JWT 검증 + users 테이블 역할 매핑

AUTH-06: AI 작업은 세션과 독립적으로 실행.
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


async def get_or_create_user_profile(
    auth_user_id: str,
    email: str,
    name: str,
    azure_ad_oid: str | None = None,
) -> dict:
    """Supabase Auth 사용자 → users 테이블 프로필 조회 또는 생성.

    최초 로그인 시 users 행 자동 생성 (기본 role='member').
    org_id는 관리자가 사전 배정하거나, 도메인 기반 자동 매핑.
    """
    client = await get_async_client()

    # 기존 프로필 조회
    res = (
        await client.table("users")
        .select("*")
        .eq("id", auth_user_id)
        .maybe_single()
        .execute()
    )
    if res.data:
        return res.data

    # Azure AD OID로 사전 등록된 프로필 매칭
    if azure_ad_oid:
        oid_res = (
            await client.table("users")
            .select("*")
            .eq("azure_ad_oid", azure_ad_oid)
            .maybe_single()
            .execute()
        )
        if oid_res.data:
            # id를 auth user id로 업데이트
            await client.table("users").update(
                {"id": auth_user_id}
            ).eq("azure_ad_oid", azure_ad_oid).execute()
            return oid_res.data

    # 이메일 도메인으로 조직 자동 매핑
    org_id = await _resolve_org_by_email(email)
    if not org_id:
        logger.warning(f"조직 매핑 실패: {email} — 관리자 배정 필요")
        return None

    # 신규 프로필 생성
    new_user = {
        "id": auth_user_id,
        "email": email,
        "name": name,
        "role": "member",
        "org_id": org_id,
        "azure_ad_oid": azure_ad_oid,
    }
    insert_res = await client.table("users").insert(new_user).execute()
    logger.info(f"신규 사용자 프로필 생성: {email}")
    return insert_res.data[0] if insert_res.data else new_user


async def _resolve_org_by_email(email: str) -> Optional[str]:
    """이메일 도메인으로 조직 ID 자동 매핑.

    같은 도메인의 기존 사용자가 있으면 해당 org_id 사용.
    """
    domain = email.split("@")[-1] if "@" in email else None
    if not domain:
        return None

    client = await get_async_client()
    res = (
        await client.table("users")
        .select("org_id")
        .ilike("email", f"%@{domain}")
        .limit(1)
        .execute()
    )
    if res.data:
        return res.data[0]["org_id"]
    return None


async def update_user_profile(user_id: str, updates: dict) -> dict:
    """사용자 프로필 업데이트."""
    client = await get_async_client()
    res = (
        await client.table("users")
        .update(updates)
        .eq("id", user_id)
        .execute()
    )
    return res.data[0] if res.data else {}


async def deactivate_user(user_id: str, reason: str = "") -> dict:
    """사용자 비활성화 (ULM — 퇴사·이동)."""
    client = await get_async_client()
    res = (
        await client.table("users")
        .update({
            "status": "inactive",
            "deactivated_at": datetime.now(timezone.utc).isoformat(),
        })
        .eq("id", user_id)
        .execute()
    )
    # 감사 로그
    await client.table("audit_logs").insert({
        "user_id": user_id,
        "action": "deactivate",
        "resource_type": "user",
        "resource_id": user_id,
        "detail": {"reason": reason},
    }).execute()
    return res.data[0] if res.data else {}
