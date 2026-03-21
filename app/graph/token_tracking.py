"""
노드별 토큰 비용 자동 추적 데코레이터.

graph.py에서 AI 호출 노드를 track_tokens()로 래핑하면
ContextVar에서 토큰 사용량을 수집 → 비용 계산 → state.token_usage에 주입 → DB 저장.
"""

import functools
import logging
import time

from app.services.claude_client import get_accumulated_usage, reset_usage_context
from app.services.token_manager import check_budget
from app.services.token_pricing import summarize_usage

logger = logging.getLogger(__name__)


def track_tokens(node_name: str):
    """노드 실행 전후로 토큰 사용량을 자동 추적하는 데코레이터."""

    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(state, *args, **kwargs):
            reset_usage_context()
            started_at = time.time()

            result = await fn(state, *args, **kwargs)

            duration_ms = int((time.time() - started_at) * 1000)
            records = get_accumulated_usage()

            if records:
                summary = summarize_usage(records)
                summary["duration_ms"] = duration_ms

                # 토큰 예산 체크 (경고 로그)
                budget_check = check_budget(node_name, summary.get("input_tokens", 0))
                if not budget_check["within_budget"]:
                    logger.warning(
                        f"[TOKEN BUDGET] {node_name}: "
                        f"{budget_check['estimated']:,} / {budget_check['budget']:,} "
                        f"({budget_check['ratio']:.1f}x 초과)"
                    )
                summary["budget_check"] = budget_check

                if isinstance(result, dict):
                    existing = result.get("token_usage", {})
                    result["token_usage"] = {**existing, node_name: summary}

                # DB 저장 (fire-and-forget)
                try:
                    proposal_id = state.get("project_id", "")
                    if proposal_id:
                        await _persist_ai_task_log(
                            proposal_id, node_name, summary, duration_ms,
                        )
                except Exception as e:
                    logger.warning(f"ai_task_log 저장 실패: {e}")

            return result

        return wrapper

    return decorator


async def _persist_ai_task_log(
    proposal_id: str,
    step: str,
    summary: dict,
    duration_ms: int,
) -> None:
    """ai_task_logs 테이블에 토큰 사용량 기록."""
    try:
        from app.utils.supabase_client import get_async_client

        client = await get_async_client()
        row = {
            "proposal_id": proposal_id,
            "step": step,
            "status": "complete",
            "duration_ms": duration_ms,
            "input_tokens": summary.get("input_tokens", 0),
            "output_tokens": summary.get("output_tokens", 0),
            "cost_usd": summary.get("cost_usd", 0),
            "model": summary.get("model", ""),
        }
        try:
            await client.table("ai_task_logs").insert(row).execute()
        except Exception:
            # cache 토큰 컬럼 포함하여 재시도
            row["cache_read_tokens"] = summary.get("cache_read_tokens", 0)
            row["cache_create_tokens"] = summary.get("cache_create_tokens", 0)
            await client.table("ai_task_logs").insert(row).execute()
    except Exception as e:
        logger.warning(f"ai_task_log DB insert 실패: {e}")
