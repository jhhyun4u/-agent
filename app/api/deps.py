"""
인증·인가 의존성 (§17 + §12-0)

FastAPI Depends()로 주입:
- get_current_user: JWT 검증 + DB 프로필 조회
- get_current_user_or_none: AI 백그라운드 작업용 (세션 만료 허용)
- require_role(*roles): 역할 기반 접근 제어
- require_project_access(proposal_id): 프로젝트 접근 권한 확인
"""

import logging
from typing import Optional

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.exceptions import (
    AuthInsufficientRoleError,
    AuthProjectAccessError,
    AuthTokenExpiredError,
    TenopAPIError,
)
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> dict:
    """JWT에서 현재 사용자 정보 추출 + DB 역할 조회.

    반환 dict 키: id, email, name, role, team_id, division_id, org_id, ...
    """
    if not credentials:
        raise AuthTokenExpiredError()

    token = credentials.credentials
    try:
        client = await get_async_client()
        response = await client.auth.get_user(token)
        user_auth = response.user
    except Exception:
        raise AuthTokenExpiredError()

    if not user_auth:
        raise AuthTokenExpiredError()

    # DB에서 역할·소속 조회
    try:
        profile = (
            await client.table("users")
            .select("*")
            .eq("id", str(user_auth.id))
            .single()
            .execute()
        )
        if not profile.data:
            raise AuthTokenExpiredError({"reason": "사용자 프로필 없음"})
        return profile.data
    except TenopAPIError:
        raise
    except Exception:
        raise AuthTokenExpiredError({"reason": "프로필 조회 실패"})


async def get_current_user_or_none(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> dict | None:
    """세션 만료 여부만 확인 (AI 작업 백그라운드 실행에 사용).

    AUTH-06: AI 작업은 세션과 독립적으로 실행.
    """
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except TenopAPIError:
        return None


def require_role(*roles: str):
    """역할 기반 접근 제어 데코레이터.

    사용법:
        @router.get("/admin")
        async def admin_page(user=Depends(require_role("admin", "executive"))):
            ...
    """
    async def _check(user: dict = Depends(get_current_user)) -> dict:
        if user["role"] not in roles:
            raise AuthInsufficientRoleError(list(roles), user["role"])
        # 비활성 사용자 차단
        if user.get("status") != "active":
            raise TenopAPIError(
                "AUTH_004", "비활성 계정입니다. 관리자에게 문의하세요.", 403,
                {"status": user.get("status")},
            )
        return user
    return _check


async def require_project_access(
    proposal_id: str,
    user: dict = Depends(get_current_user),
) -> dict:
    """프로젝트 접근 권한 확인.

    접근 가능 조건 (계층적):
    - admin / executive: 전사 접근
    - director: 소속 본부 프로젝트
    - lead: 소속 팀 프로젝트
    - member: 참여자이거나 생성자
    """
    client = await get_async_client()
    res = (
        await client.table("proposals")
        .select("*")
        .eq("id", proposal_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        from app.exceptions import PropNotFoundError
        raise PropNotFoundError(proposal_id)

    proposal = res.data
    role = user["role"]

    # admin / executive: 같은 org면 전사 접근
    if role in ("admin", "executive") and proposal["org_id"] == user["org_id"]:
        return proposal

    # director: 같은 division
    if role == "director" and proposal["division_id"] == user.get("division_id"):
        return proposal

    # lead: 같은 team
    if role == "lead" and proposal["team_id"] == user.get("team_id"):
        return proposal

    # member: 참여자 또는 생성자
    if proposal["created_by"] == user["id"]:
        return proposal

    participants = (
        await client.table("project_participants")
        .select("user_id")
        .eq("proposal_id", proposal_id)
        .eq("user_id", user["id"])
        .maybe_single()
        .execute()
    )
    if participants.data:
        return proposal

    raise AuthProjectAccessError(proposal_id)
