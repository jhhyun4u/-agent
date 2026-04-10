"""
인증·인가 의존성 (§17 + §12-0)

FastAPI Depends()로 주입:
- get_current_user: JWT 검증 + DB 프로필 조회 → CurrentUser 반환
- get_current_user_or_none: AI 백그라운드 작업용 (세션 만료 허용)
- require_role(*roles): 역할 기반 접근 제어
- require_project_access(proposal_id): 프로젝트 접근 권한 확인
"""

import logging

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

# 개발 모드 mock 사용자 - 환경변수에서 읽음 (DEV_MODE=true일 때만 사용)
_DEV_USER_ID = None
_DEV_USER_EMAIL = None
_DEV_USER_ORG_ID = None
_DEV_USER_TEAM_ID = None


def _init_dev_user():
    """환경변수에서 개발 모드 사용자 정보 읽기."""
    global _DEV_USER_ID, _DEV_USER_EMAIL, _DEV_USER_ORG_ID, _DEV_USER_TEAM_ID
    if settings.dev_mode:
        if not all([settings.dev_user_id, settings.dev_user_email, settings.dev_user_org_id]):
            raise RuntimeError(
                "DEV_MODE=true일 때 필수: DEV_USER_ID, DEV_USER_EMAIL, DEV_USER_ORG_ID"
            )
        _DEV_USER_ID = settings.dev_user_id
        _DEV_USER_EMAIL = settings.dev_user_email
        _DEV_USER_ORG_ID = settings.dev_user_org_id
        _DEV_USER_TEAM_ID = settings.dev_user_team_id or None
        logger.warning(f"⚠️ DEV_MODE: Mock 사용자 [{_DEV_USER_ID}] 활성화됨")


async def _get_dev_user() -> CurrentUser:
    """개발 모드: 환경변수에서 읽은 사용자 정보 반환.

    참고: _init_dev_user()는 app.main의 startup에서 한 번만 호출되므로
    여기서는 이미 초기화된 전역변수를 그대로 사용함 (race condition 방지)
    """
    if not _DEV_USER_ID:
        raise AuthTokenExpiredError({"reason": "DEV_MODE 초기화 실패"})

    return CurrentUser(
        id=_DEV_USER_ID,
        email=_DEV_USER_EMAIL or "dev@tenopa.co.kr",
        name="Dev User",
        role="lead",
        org_id=_DEV_USER_ORG_ID,
        team_id=_DEV_USER_TEAM_ID or None,
        division_id=None,
        status="active",
    )


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
        # 비활성 사용자 차단
        if user.status != "active":
            raise TenopAPIError(
                "AUTH_004", "비활성 계정입니다. 관리자에게 문의하세요.", 403,
                {"status": user.status},
            )
        return user
    return _check


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
        .select("*")
        .eq("id", proposal_id)
        .maybe_single()
        .execute()
    )
    if not res.data:
        from app.exceptions import PropNotFoundError
        raise PropNotFoundError(proposal_id)

    proposal = res.data
    role = user.role

    # admin / executive: 같은 org면 전사 접근
    if role in ("admin", "executive") and proposal.get("org_id") == user.org_id:
        return proposal

    # director: 같은 division
    if role == "director" and proposal.get("division_id") == user.division_id:
        return proposal

    # lead: 같은 team
    if role == "lead" and proposal["team_id"] == user.team_id:
        return proposal

    # member: 참여자 또는 생성자
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


async def get_db():
    """DB 의존성 (레거시 호환 - 실제로 사용되지 않음)"""
    return None
