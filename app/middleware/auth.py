"""
JWT 인증 미들웨어 (레거시 호환)

새 코드는 app.api.deps.get_current_user 사용 권장.
기존 routes_team.py 등 레거시 라우트 호환을 위해 유지.
"""

from typing import Optional

from fastapi import Header, HTTPException

from app.utils.supabase_client import get_async_client


async def get_current_user(authorization: Optional[str] = Header(None)):
    """Bearer 토큰 검증 후 Supabase user 객체 반환.

    레거시 호환: user.id만 반환. 역할/소속 정보 필요 시 deps.get_current_user 사용.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = authorization.removeprefix("Bearer ")
    try:
        client = await get_async_client()
        response = await client.auth.get_user(token)
        return response.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
