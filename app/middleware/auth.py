"""
JWT 인증 미들웨어

get_current_user: Authorization: Bearer <token> 헤더 검증.
Optional[str] = Header(None) 패턴으로 미제공 시 401 반환 (422 방지).
"""

from typing import Optional
from fastapi import Header, HTTPException

from app.utils.supabase_client import get_async_client


async def get_current_user(authorization: Optional[str] = Header(None)):
    """Bearer 토큰 검증 후 Supabase user 객체 반환"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Bearer token required")
    token = authorization.removeprefix("Bearer ")
    try:
        client = await get_async_client()
        response = await client.auth.get_user(token)
        return response.user
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
