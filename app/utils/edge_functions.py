"""
Supabase Edge Functions HTTP 호출 유틸리티

알림 실패는 치명적이지 않으므로 예외를 외부로 전파하지 않음.
"""

import logging
import aiohttp
from app.config import settings

logger = logging.getLogger(__name__)


async def _call(function_name: str, payload: dict) -> bool:
    """Edge Function 비동기 POST 호출. 실패 시 False 반환."""
    if not settings.supabase_url or not settings.supabase_key:
        logger.debug(f"Edge Function [{function_name}] 스킵: Supabase URL/key 미설정")
        return False

    url = f"{settings.supabase_url}/functions/v1/{function_name}"
    headers = {
        "Authorization": f"Bearer {settings.supabase_key}",
        "Content-Type": "application/json",
    }
    try:
        timeout = aiohttp.ClientTimeout(total=settings.edge_function_timeout_seconds)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    logger.warning(f"Edge Function [{function_name}] 오류 {resp.status}: {body}")
                    return False
                return True
    except Exception as e:
        logger.warning(f"Edge Function [{function_name}] 호출 실패: {e}")
        return False


async def notify_proposal_complete(
    proposal_id: str,
    owner_email: str = "",
    proposal_title: str = "",
) -> bool:
    """
    Phase 5 완료 후 소유자에게 완료 이메일 발송.

    owner_email, proposal_title을 직접 전달하면 Edge Function이 DB 조회를 건너뜀.
    proposals 테이블에 proposal_id가 없는 경우(인메모리 세션) 반드시 직접 전달.
    """
    return await _call(
        "proposal-complete",
        {
            "proposal_id": proposal_id,
            "owner_email": owner_email,
            "proposal_title": proposal_title,
        },
    )


async def notify_comment_created(comment_id: str) -> bool:
    """댓글 작성 후 팀원에게 알림 이메일 발송."""
    return await _call("comment-notify", {"comment_id": comment_id})
