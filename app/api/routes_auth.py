"""
인증 API (§17)

이메일+비밀번호 로그인 (Supabase Auth).
관리자가 사전 등록한 계정으로만 접근 가능.
"""

import logging

from fastapi import APIRouter, Depends, Request

from app.api.deps import get_current_user
from app.exceptions import TenopAPIError
from app.middleware.rate_limit import limiter
from app.models.auth_schemas import AuthMessageResponse, CurrentUser
from app.models.user_schemas import PasswordChangeRequest
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me", response_model=CurrentUser)
async def get_my_profile(user: CurrentUser = Depends(get_current_user)):
    """현재 로그인 사용자 프로필 조회.

    must_change_password 필드 포함.
    """
    return user


@router.post("/change-password", response_model=AuthMessageResponse)
@limiter.limit("5/minute")
async def change_password(
    request: Request,
    body: PasswordChangeRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """비밀번호 변경.

    첫 로그인 시 임시 비밀번호를 변경할 때 사용.
    현재 비밀번호 검증 후 새 비밀번호로 업데이트.
    """
    client = await get_async_client()

    # 현재 비밀번호 검증 (로그인 시도)
    try:
        await client.auth.sign_in_with_password({
            "email": user.email,
            "password": body.current_password,
        })
    except Exception:
        raise TenopAPIError("AUTH_005", "현재 비밀번호가 올바르지 않습니다.", 400)

    # 새 비밀번호로 업데이트
    try:
        await client.auth.admin.update_user_by_id(
            user.id,
            {"password": body.new_password},
        )
    except Exception as e:
        logger.error(f"비밀번호 변경 실패: user={user.id}: {e}")
        raise TenopAPIError("AUTH_005", "비밀번호 변경에 실패했습니다. 관리자에게 문의하세요.", 500)

    # must_change_password 해제
    await client.table("users").update(
        {"must_change_password": False}
    ).eq("id", user.id).execute()

    return {"message": "비밀번호가 변경되었습니다."}


@router.post("/logout", response_model=AuthMessageResponse)
async def logout():
    """로그아웃 처리.

    실제 세션 무효화는 프론트엔드 Supabase Auth signOut() 에서 처리.
    서버 측은 stateless (JWT).
    """
    return {"message": "로그아웃 완료. 클라이언트에서 토큰을 삭제하세요."}
