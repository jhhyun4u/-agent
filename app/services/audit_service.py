"""
감사 로그 서비스

모든 주요 행위(생성/수정/삭제/승인/거부)를 audit_logs 테이블에 기록.
"""

import logging
from typing import Any

from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


async def log_action(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    """감사 로그 기록."""
    try:
        client = await get_async_client()
        await client.table("audit_logs").insert({
            "user_id": user_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "detail": detail or {},
        }).execute()
    except Exception as e:
        # 감사 로그 실패가 비즈니스 로직을 차단하면 안 됨
        logger.error(f"감사 로그 기록 실패: {e}")
