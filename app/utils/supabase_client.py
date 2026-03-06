"""
Supabase 비동기 클라이언트 유틸리티 (platform v1)

acreate_client + asyncio.Lock 싱글턴 패턴.

클라이언트 종류:
- get_async_client(): service_role_key 사용 — 서버 내부 작업 전용 (RLS 우회)
- get_user_client(jwt): anon_key + 사용자 JWT — RLS 적용, 사용자 컨텍스트 작업용
"""

import asyncio
from typing import Optional
from supabase import acreate_client, AsyncClient
from app.config import settings

_server_client: Optional[AsyncClient] = None
_server_lock = asyncio.Lock()


async def get_async_client() -> AsyncClient:
    """서버 내부용 Supabase 클라이언트 싱글턴 반환 (service_role_key, RLS 우회)"""
    global _server_client
    async with _server_lock:
        if _server_client is None:
            api_key = settings.supabase_service_role_key or settings.supabase_key
            _server_client = await acreate_client(
                settings.supabase_url,
                api_key,
            )
    return _server_client


async def get_user_client(user_jwt: str) -> AsyncClient:
    """사용자 JWT 기반 Supabase 클라이언트 반환 (RLS 적용, 요청마다 생성)"""
    client = await acreate_client(
        settings.supabase_url,
        settings.supabase_key,
    )
    await client.auth.set_session(user_jwt, "")
    return client
