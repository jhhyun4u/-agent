"""
인증·인가 의존성 (§17 + §12-0)

FastAPI Depends()로 주입:
- get_current_user: JWT 검증 + DB 프로필 조회 → CurrentUser 반환
- get_current_user_or_none: AI 백그라운드 작업용 (세션 만료 허용)
- require_role(*roles): 역할 기반 접근 제어
- require_project_access(proposal_id): 프로젝트 접근 권한 확인
"""

import logging
from typing import Literal

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings
from app.exceptions import (
    AuthInsufficientRoleError,
    AuthProjectAccessError,
    AuthTokenExpiredError,
    TenopAPIError,
)
from app.models.auth_schemas import CurrentUser
from app.utils.supabase_client import get_async_client, get_user_client

logger = logging.getLogger(__name__)

_bearer_scheme = HTTPBearer(auto_error=False)

# 역할 타입
UserRole = Literal["admin", "executive", "director", "lead", "member"]


async def _init_dev_user():
    """환경변수에서 개발 모드 사용자 정보 검증 + DB 생성."""
    if settings.dev_mode:
        if not all([settings.dev_user_id, settings.dev_user_email, settings.dev_user_org_id]):
            raise RuntimeError(
                "DEV_MODE=true일 때 필수: DEV_USER_ID, DEV_USER_EMAIL, DEV_USER_ORG_ID"
            )
        logger.warning(f"⚠️ DEV_MODE: Mock 사용자 [{settings.dev_user_id}] 활성화됨")

        # DB에 개발 사용자 자동 생성
        try:
            from datetime import datetime
            client = await get_async_client()

            # 조직 생성
            await client.table("organizations").upsert({
                "id": settings.dev_user_org_id,
                "name": "Dev Organization",
                "created_at": datetime.utcnow().isoformat(),
            }).execute()

            # 사용자 생성
            await client.table("users").upsert({
                "id": settings.dev_user_id,
                "email": settings.dev_user_email,
                "name": "Dev User",
                "role": "admin",
                "org_id": settings.dev_user_org_id,
                "created_at": datetime.utcnow().isoformat(),
                "status": "active",
            }).execute()

            logger.info("✅ 개발 DB 사용자 준비 완료")
        except Exception as e:
            logger.warning(f"⚠️ 개발 사용자 DB 생성 실패 (무시): {e}")


def _should_bypass_auth() -> bool:
    """인증 우회 여부 판단 (DEV_MODE에서만 true)."""
    return settings.dev_mode


async def _get_dev_user() -> CurrentUser:
    """개발 모드: 설정에서 읽은 사용자 정보 반환."""
    if not _should_bypass_auth():
        raise AuthTokenExpiredError({"reason": "DEV_MODE 비활성화됨"})

    if not all([settings.dev_user_id, settings.dev_user_email, settings.dev_user_org_id]):
        raise AuthTokenExpiredError({"reason": "DEV_MODE 설정 불완전"})

    # DEBUG: 실제로 어떤 값이 사용되는지 확인
    print(f"\n[_get_dev_user] Loading user: id={settings.dev_user_id}, email={settings.dev_user_email}, org={settings.dev_user_org_id}, team={settings.dev_user_team_id}")
    logger.warning(f"[_get_dev_user] Loading user: id={settings.dev_user_id}")

    user = CurrentUser(
        id=settings.dev_user_id,
        email=settings.dev_user_email,
        name="Dev User",
        role="lead",
        org_id=settings.dev_user_org_id,
        team_id=settings.dev_user_team_id or None,
        division_id=None,
        status="active",
    )
    print(f"[_get_dev_user] Returning user: id={user.id}")
    return user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser:
    """JWT에서 현재 사용자 정보 추출 + DB 역할 조회 → CurrentUser 반환."""
    # 개발 모드: 토큰 없거나 빈 토큰이면 mock 사용자 반환
    if settings.dev_mode and (not credentials or not credentials.credentials):
        return await _get_dev_user()

    if not credentials:
        raise AuthTokenExpiredError()

    token = credentials.credentials
    try:
        client = await get_async_client()
        response = await client.auth.get_user(token)
        user_auth = response.user
    except Exception:
        if settings.dev_mode:
            return await _get_dev_user()
        raise AuthTokenExpiredError()

    if not user_auth:
        if settings.dev_mode:
            return await _get_dev_user()
        raise AuthTokenExpiredError()

    # DB에서 역할·소속 조회
    try:
        profile = (
            await client.table("users")
            .select("id, email, name, role, org_id, team_id, division_id, status")
            .eq("id", str(user_auth.id))
            .single()
            .execute()
        )
        if not profile.data:
            raise AuthTokenExpiredError({"reason": "사용자 프로필 없음"})
        return CurrentUser(**profile.data)
    except TenopAPIError:
        raise
    except Exception:
        raise AuthTokenExpiredError({"reason": "프로필 조회 실패"})


async def get_current_user_or_none(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> CurrentUser | None:
    """세션 만료 여부만 확인 (AI 작업 백그라운드 실행에 사용).

    AUTH-06: AI 작업은 세션과 독립적으로 실행.
    """
    if not credentials:
        return None
    try:
        return await get_current_user(credentials)
    except TenopAPIError:
        return None


async def get_rls_client(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
):
    """사용자 JWT 기반 Supabase 클라이언트 반환 (RLS 적용).

    C-2 보안 수정: 사용자 대면 API에서는 service_role 대신 이 의존성을 사용하여
    Supabase RLS 정책을 활성화. 서버 내부/시스템 작업에만 get_async_client() 사용.

    사용법:
        @router.get("/my-data")
        async def my_data(
            user=Depends(get_current_user),
            rls_client=Depends(get_rls_client),
        ):
            # rls_client는 해당 사용자의 JWT로 RLS 필터링된 결과 반환
            result = await rls_client.table("proposals").select("*").execute()
    """
    # 개발 모드: 토큰 없으면 service_role 클라이언트로 폴백 (RLS 우회)
    # H-2: 프로덕션에서는 이 경로에 도달할 수 없음 (DEV_MODE 가드가 서버 시작 시 차단)
    if settings.dev_mode and (not credentials or not credentials.credentials):
        return await get_async_client()

    if not credentials:
        raise AuthTokenExpiredError()
    try:
        return await get_user_client(credentials.credentials)
    except Exception:
        if settings.dev_mode:
            return await get_async_client()
        raise


def require_role(*roles: str):
    """역할 기반 접근 제어 데코레이터.

    사용법:
        @router.get("/admin")
        async def admin_page(user=Depends(require_role("admin", "executive"))):
            ...
    """
    async def _check(user: CurrentUser = Depends(get_current_user)) -> CurrentUser:
        if user.role not in roles:
            raise AuthInsufficientRoleError(list(roles), user.role)
        _validate_user_status(user)
        return user
    return _check


def _validate_user_status(user: CurrentUser) -> None:
    """사용자 활성 상태 검증."""
    if user.status != "active":
        raise TenopAPIError(
            "AUTH_004", "비활성 계정입니다. 관리자에게 문의하세요.", 403,
            {"status": user.status},
        )


def _has_access_by_role(user: CurrentUser, proposal: dict) -> bool:
    """역할 기반 프로젝트 접근 권한 확인."""
    role: UserRole = user.role  # type: ignore

    # admin / executive: 같은 org면 전사 접근
    if role in ("admin", "executive"):
        return proposal.get("org_id") == user.org_id

    # director: 같은 division
    if role == "director":
        return proposal.get("division_id") == user.division_id

    # lead: 같은 team
    if role == "lead":
        return proposal.get("team_id") == user.team_id

    return False


async def require_project_access(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
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
        .select("id, team_id, division_id, org_id, owner_id")
        .eq("id", proposal_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        from app.exceptions import PropNotFoundError
        raise PropNotFoundError(proposal_id)

    proposal = res.data

    # 역할 기반 접근 확인
    if _has_access_by_role(user, proposal):
        return proposal

    # 참여자 또는 생성자 확인
    if proposal.get("owner_id") == user.id:
        return proposal

    participants = (
        await client.table("project_participants")
        .select("user_id")
        .eq("proposal_id", proposal_id)
        .eq("user_id", user.id)
        .maybe_single()
        .execute()
    )
    if participants.data:
        return proposal

    raise AuthProjectAccessError(proposal_id)


async def require_knowledge_access(
    user: CurrentUser = Depends(get_current_user),
) -> CurrentUser:
    """지식 관리 시스템 접근 권한 RLS 의존성.

    모든 knowledge API 라우트에서 사용. 다음을 검증:
    1. 사용자가 인증되어 있을 것 (get_current_user 통해)
    2. 사용자에게 team_id 또는 org_id가 있을 것 (RLS 필터링 필수)
    3. 사용자 계정이 활성 상태일 것

    Design Ref: §5 RLS Policies, SC-4 (zero RLS breaches)

    Returns:
        검증된 CurrentUser 객체

    Raises:
        AuthInsufficientRoleError: team_id가 없어 RLS 필터링 불가한 경우
        TenopAPIError: 비활성 계정인 경우
    """
    _validate_user_status(user)

    # Knowledge RLS requires team_id to scope queries correctly
    if not user.team_id and user.role not in ("admin", "executive"):
        raise TenopAPIError(
            "KNOWLEDGE_ACCESS_DENIED",
            "지식 시스템 접근에는 팀 소속이 필요합니다.",
            403,
            {"user_id": str(user.id), "role": user.role},
        )

    return user


async def get_db():
    """DB 의존성 (레거시 호환 - 실제로 사용되지 않음)"""
    return None
