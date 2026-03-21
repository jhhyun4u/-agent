"""
사람 수정 추적 서비스 — 만족도 프록시.

edit_ratio: 0=무수정(만족), 1=전체 재작성(불만)
difflib.SequenceMatcher로 경량 계산, 외부 의존성 없음.
"""

import difflib
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def compute_edit_ratio(original: str, edited: str) -> float:
    """두 텍스트의 수정 비율 계산 (0.0~1.0)."""
    if not original and not edited:
        return 0.0
    if not original:
        return 1.0
    if original == edited:
        return 0.0

    matcher = difflib.SequenceMatcher(None, original, edited)
    similarity = matcher.ratio()
    return round(1.0 - similarity, 4)


async def record_action(
    proposal_id: str,
    section_id: str,
    action: str,
    original: str = "",
    edited: str = "",
    user_id: Optional[str] = None,
) -> None:
    """사람의 편집 행동을 기록.

    action: accept | edit | reject | regenerate
    """
    edit_ratio = compute_edit_ratio(original, edited) if action == "edit" else (
        0.0 if action == "accept" else 1.0
    )

    # prompt_artifact_link에서 해당 섹션의 prompt 정보 자동 매핑
    prompt_id = None
    prompt_version = None

    try:
        from app.utils.supabase_client import get_async_client

        client = await get_async_client()

        # 가장 최근 프롬프트 링크 조회
        link = await (
            client.table("prompt_artifact_link")
            .select("prompt_id, prompt_version")
            .eq("proposal_id", proposal_id)
            .eq("section_id", section_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )

        if link.data:
            prompt_id = link.data[0]["prompt_id"]
            prompt_version = link.data[0]["prompt_version"]

        await client.table("human_edit_tracking").insert({
            "proposal_id": proposal_id,
            "section_id": section_id,
            "prompt_id": prompt_id,
            "prompt_version": prompt_version,
            "action": action,
            "original_length": len(original),
            "edited_length": len(edited),
            "edit_ratio": edit_ratio,
            "user_id": user_id,
        }).execute()

    except Exception as e:
        logger.warning(f"수정 추적 기록 실패 (무시): {e}")
