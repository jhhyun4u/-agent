"""
토큰 예산 관리 서비스 (§21)

STEP별 토큰 예산 할당, 컨텍스트 빌더, Prompt Caching 최적화.
"""

import logging
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

# STEP별 토큰 예산 (input tokens 기준)
STEP_TOKEN_BUDGETS: dict[str, int] = {
    "rfp_search": 8_000,
    "rfp_analyze": 20_000,
    "research_gather": 15_000,
    "go_no_go": 12_000,
    "strategy_generate": 25_000,
    "plan_team": 10_000,
    "plan_assign": 10_000,
    "plan_schedule": 10_000,
    "plan_story": 20_000,
    "plan_price": 15_000,
    "proposal_write_next": 30_000,
    "self_review": 25_000,
    "presentation_strategy": 10_000,
    "ppt_toc": 12_000,
    "ppt_visual_brief": 12_000,
    "ppt_storyboard": 15_000,
}

# KB 검색 설정
KB_TOP_K = 5
KB_MAX_BODY_LENGTH = 500

# 피드백 윈도우 크기
FEEDBACK_WINDOW_SIZE = 3


def get_budget(step: str) -> int:
    """주어진 STEP의 토큰 예산 반환. 미등록 시 기본 15K."""
    return STEP_TOKEN_BUDGETS.get(step, 15_000)


def check_budget(step: str, estimated_tokens: int) -> dict[str, Any]:
    """토큰 예산 초과 여부 확인.

    Returns:
        {"within_budget": bool, "budget": int, "estimated": int, "ratio": float}
    """
    budget = get_budget(step)
    ratio = estimated_tokens / budget if budget > 0 else 0
    return {
        "within_budget": estimated_tokens <= budget,
        "budget": budget,
        "estimated": estimated_tokens,
        "ratio": round(ratio, 2),
    }


def truncate_context(text: str, max_chars: int) -> str:
    """컨텍스트 텍스트를 최대 문자 수로 자르기. 문장 단위 절단."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_period = truncated.rfind(".")
    if last_period > max_chars * 0.7:
        return truncated[: last_period + 1]
    return truncated + "..."


def trim_feedback_history(
    feedback_history: list[dict],
    window_size: int | None = None,
) -> list[dict]:
    """피드백 이력을 최근 N개 + 이전 요약으로 관리 (토큰 절약).

    최근 window_size개는 원본 유지, 이전 것들은 1건 요약으로 압축.
    """
    size = window_size or FEEDBACK_WINDOW_SIZE
    if len(feedback_history) <= size:
        return feedback_history

    older = feedback_history[:-size]
    recent = feedback_history[-size:]

    summary = _summarize_feedbacks(older)
    return [summary] + recent


def _summarize_feedbacks(feedbacks: list[dict]) -> dict:
    """오래된 피드백들을 1건의 요약 dict로 압축."""
    if not feedbacks:
        return {"step": "summary", "decision": "요약", "feedback": ""}

    steps = list({f.get("step", "") for f in feedbacks if f.get("step")})
    decisions = list({f.get("decision", "") for f in feedbacks if f.get("decision")})
    key_points = []
    for f in feedbacks:
        fb = f.get("feedback", "")
        if fb:
            # 첫 50자만 유지
            key_points.append(fb[:50].rstrip() + ("..." if len(fb) > 50 else ""))

    summary_text = (
        f"이전 {len(feedbacks)}건 피드백 요약 — "
        f"단계: {', '.join(steps[:5])}; "
        f"결정: {', '.join(decisions[:5])}; "
        f"핵심: {' | '.join(key_points[:5])}"
    )
    return {"step": "summary", "decision": "요약", "feedback": summary_text}


def truncate_kb_results(
    kb_results: dict[str, list[dict]],
    top_k: int | None = None,
    max_body_length: int | None = None,
) -> dict[str, list[dict]]:
    """KB 검색 결과를 top_k + body 길이 제한으로 자르기."""
    k = top_k or KB_TOP_K
    max_len = max_body_length or KB_MAX_BODY_LENGTH
    trimmed: dict[str, list[dict]] = {}

    for area, items in kb_results.items():
        area_items = []
        for item in items[:k]:
            item_copy = dict(item)
            if "body" in item_copy and isinstance(item_copy["body"], str):
                if len(item_copy["body"]) > max_len:
                    item_copy["body"] = item_copy["body"][:max_len] + "..."
            area_items.append(item_copy)
        trimmed[area] = area_items

    return trimmed


def build_context(
    step: str,
    rfp_summary: str = "",
    strategy: str = "",
    plan: str = "",
    feedback_history: list[dict] | None = None,
    kb_results: dict[str, list[dict]] | None = None,
    section_specific: str = "",
) -> tuple[list[dict], dict]:
    """STEP별 최적화된 컨텍스트 메시지 + Prompt Caching 설정 반환.

    Returns:
        (messages, cache_config) — messages는 시스템 프롬프트용 content 블록 리스트,
        cache_config는 캐싱 설정 dict.
    """
    budget = get_budget(step)

    # 공통 컨텍스트 (캐싱 대상)
    common_parts: list[str] = []
    if rfp_summary:
        common_parts.append(f"[RFP 요약]\n{truncate_context(rfp_summary, budget // 3)}")
    if strategy:
        common_parts.append(f"[제안전략]\n{truncate_context(strategy, budget // 4)}")
    if plan:
        common_parts.append(f"[실행계획]\n{truncate_context(plan, budget // 4)}")

    # 피드백 윈도우 (캐싱 미대상 — 변동성)
    trimmed_feedback = trim_feedback_history(feedback_history or [])
    if trimmed_feedback:
        fb_text = "\n".join(
            f"- [{f.get('step', '')}] {f.get('decision', '')}: {f.get('feedback', '')}"
            for f in trimmed_feedback
        )
        common_parts.append(f"[리뷰 피드백 (최근 {len(trimmed_feedback)}건)]\n{fb_text}")

    # KB 결과 (캐싱 대상)
    if kb_results:
        trimmed_kb = truncate_kb_results(kb_results)
        kb_parts = []
        for area, items in trimmed_kb.items():
            if items:
                area_text = "\n".join(
                    f"  - {it.get('title', it.get('name', ''))}: {it.get('body', it.get('description', ''))[:200]}"
                    for it in items
                )
                kb_parts.append(f"[{area}]\n{area_text}")
        if kb_parts:
            common_parts.append("[KB 참조 자료]\n" + "\n".join(kb_parts))

    # 섹션별 컨텍스트
    if section_specific:
        common_parts.append(f"[섹션 컨텍스트]\n{section_specific}")

    common_text = "\n\n".join(common_parts)

    # Prompt Caching 설정
    content_blocks: list[dict] = []
    cache_config: dict = {}

    if common_text:
        block: dict = {"type": "text", "text": common_text}
        if settings.enable_prompt_caching:
            block["cache_control"] = {"type": "ephemeral"}
            cache_config["cached"] = True
        content_blocks.append(block)

    return content_blocks, cache_config


def estimate_tokens(text: str) -> int:
    """텍스트의 대략적인 토큰 수 추정 (한국어: 약 1.5자/토큰)."""
    if not text:
        return 0
    korean_chars = sum(1 for c in text if "\uac00" <= c <= "\ud7a3")
    english_chars = len(text) - korean_chars
    return int(korean_chars / 1.5 + english_chars / 4)


def build_structured_output_schema(step: str) -> dict | None:
    """TKN-09: STEP별 JSON Structured Output 스키마 반환.

    Claude structured output 사용 시 각 STEP의 기대 출력 형식을 정의.
    미지원 STEP이면 None 반환.

    Args:
        step: STEP 이름 (STEP_TOKEN_BUDGETS 키와 동일)

    Returns:
        JSON 스키마 dict (OpenAI tool/response_format 형식) 또는 None
    """
    schemas: dict[str, dict] = {
        "rfp_analyze": {
            "type": "json_schema",
            "json_schema": {
                "name": "rfp_analysis",
                "schema": {
                    "type": "object",
                    "properties": {
                        "project_name": {"type": "string"},
                        "client": {"type": "string"},
                        "deadline": {"type": "string"},
                        "case_type": {"type": "string", "enum": ["A", "B"]},
                        "eval_items": {"type": "array"},
                        "tech_price_ratio": {"type": "object"},
                        "hot_buttons": {"type": "array"},
                        "mandatory_reqs": {"type": "array"},
                        "format_template": {"type": "object"},
                        "volume_spec": {"type": "object"},
                        "special_conditions": {"type": "array"},
                    },
                    "required": [
                        "project_name", "client", "case_type",
                        "eval_items", "hot_buttons",
                    ],
                },
            },
        },
        "go_no_go": {
            "type": "json_schema",
            "json_schema": {
                "name": "go_no_go_decision",
                "schema": {
                    "type": "object",
                    "properties": {
                        "decision": {"type": "string", "enum": ["go", "no_go", "conditional"]},
                        "score": {"type": "number"},
                        "rationale": {"type": "string"},
                        "conditions": {"type": "array"},
                        "positioning": {"type": "string"},
                    },
                    "required": ["decision", "score", "rationale"],
                },
            },
        },
        "strategy_generate": {
            "type": "json_schema",
            "json_schema": {
                "name": "proposal_strategy",
                "schema": {
                    "type": "object",
                    "properties": {
                        "win_theme": {"type": "string"},
                        "positioning": {"type": "string"},
                        "differentiators": {"type": "array"},
                        "swot": {"type": "object"},
                        "scenarios": {"type": "array"},
                    },
                    "required": ["win_theme", "positioning", "differentiators"],
                },
            },
        },
    }
    return schemas.get(step)
