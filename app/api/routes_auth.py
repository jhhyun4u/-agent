"""
인증 API (§17)

Azure AD(Entra ID) + Supabase Auth OAuth 흐름.
프론트엔드에서 Supabase Auth signInWithOAuth(azure) 직접 호출.
이 라우트는 콜백 처리 + 프로필 동기화 담당.
"""

import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.services.auth_service import get_or_create_user_profile

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/me")
async def get_my_profile(user: dict = Depends(get_current_user)):
    """현재 로그인 사용자 프로필 조회.

    프론트엔드 로그인 후 첫 호출 시 users 테이블 프로필 자동 생성.
    """
    return user


@router.post("/sync-profile")
async def sync_profile(user: dict = Depends(get_current_user)):
    """Supabase Auth → users 테이블 프로필 동기화.

    최초 로그인 시 프론트엔드에서 호출하여 프로필 생성 보장.
    """
    profile = await get_or_create_user_profile(
        auth_user_id=user["id"],
        email=user["email"],
        name=user.get("name", user["email"].split("@")[0]),
        azure_ad_oid=user.get("azure_ad_oid"),
    )
    return profile


@router.post("/logout")
async def logout():
    """로그아웃 처리.

    실제 세션 무효화는 프론트엔드 Supabase Auth signOut() 에서 처리.
    서버 측은 stateless (JWT).
    """
    return {"message": "로그아웃 완료. 클라이언트에서 토큰을 삭제하세요."}
