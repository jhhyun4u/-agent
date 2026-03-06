"""
Supabase 비동기 클라이언트 유틸리티 (platform v1)

acreate_client + asyncio.Lock 싱글턴 패턴.
service_role_key 우선 사용 (RLS 우회).
"""

import asyncio
from typing import Optional
from supabase import acreate_client, AsyncClient
from app.config import settings

_async_client: Optional[AsyncClient] = None
_lock = asyncio.Lock()


async def get_async_client() -> AsyncClient:
    """비동기 Supabase 클라이언트 싱글턴 반환"""
    global _async_client
    async with _lock:
        if _async_client is None:
            api_key = settings.supabase_service_role_key or settings.supabase_key
            _async_client = await acreate_client(
                settings.supabase_url,
                api_key,
            )
    return _async_client
