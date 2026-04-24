"""프롬프트 카테고리 매핑 — 6개 카테고리 + 메타데이터 + 노드 사용처."""

import importlib
import logging

logger = logging.getLogger(__name__)

# ── 카테고리 정의 ──

PROMPT_CATEGORIES: dict[str, dict] = {
    "bid_analysis": {
        "label": "공고 분석",
        "icon": "Search",
        "description": "G2B 공고 전처리, 적합도 평가, 통합 분석",
        "source_modules": ["app.prompts.bid_review"],
    },
    "strategy": {
        "label": "전략 수립",
        "icon": "Target",
        "description": "포지셔닝, SWOT, 경쟁 분석, Win Theme",
        "source_modules": ["app.prompts.strategy"],
    },
    "planning": {
        "label": "계획 수립",
        "icon": "Calendar",
        "description": "팀 구성, 일정, 스토리라인, 예산",
        "source_modules": ["app.prompts.plan"],
    },
    "proposal_writing": {
        "label": "제안서 작성",
        "icon": "FileText",
        "description": "10개 섹션 유형 + 케이스 A/B + 자가진단",
        "source_modules": ["app.prompts.section_prompts", "app.prompts.proposal_prompts"],
    },
    "presentation": {
        "label": "발표 자료",
        "icon": "Presentation",
        "description": "PPT 3단계 파이프라인 (TOC→비주얼→스토리보드)",
        "source_modules": ["app.prompts.ppt_pipeline"],
    },
    "quality_assurance": {
        "label": "품질 보증",
        "icon": "Shield",
        "description": "신뢰성 규칙, 출처 태그, 제출서류 추출",
        "source_modules": ["app.prompts.trustworthiness", "app.prompts.submission_docs"],
    },
}

# ── 프롬프트 → 그래프 노드 매핑 ──

PROMPT_NODE_USAGE: dict[str, list[str]] = {
    # 공고 분석
    "bid_review.PREPROCESSOR_SYSTEM": ["rfp_search"],
    "bid_review.PREPROCESSOR_USER": ["rfp_search"],
    "bid_review.REVIEWER_SYSTEM": ["rfp_search"],
    "bid_review.REVIEWER_USER_SINGLE": ["rfp_search"],
    "bid_review.REVIEWER_USER_BATCH": ["rfp_search"],
    "bid_review.UNIFIED_ANALYSIS_SYSTEM": ["rfp_search"],
    "bid_review.UNIFIED_ANALYSIS_USER": ["rfp_search"],
    # 전략
    "strategy.GENERATE_PROMPT": ["strategy_generate"],
    "strategy.COMPETITIVE_ANALYSIS_FRAMEWORK": ["strategy_generate"],
    "strategy.RESEARCH_FRAMEWORK": ["strategy_generate"],
    # 계획
    "plan.TEAM_PROMPT": ["plan_team"],
    "plan.ASSIGN_PROMPT": ["plan_assign"],
    "plan.SCHEDULE_PROMPT": ["plan_schedule"],
    "plan.STORY_PROMPT": ["plan_story"],
    "plan.PRICE_PROMPT": ["plan_price"],
    "plan.BUDGET_DETAIL_FRAMEWORK": ["plan_price"],
    # 제안서 작성
    "section_prompts.EVALUATOR_PERSPECTIVE_BLOCK": ["proposal_write_next"],
    "section_prompts.UNDERSTAND": ["proposal_write_next"],
    "section_prompts.STRATEGY": ["proposal_write_next"],
    "section_prompts.METHODOLOGY": ["proposal_write_next"],
    "section_prompts.TECHNICAL": ["proposal_write_next"],
    "section_prompts.MANAGEMENT": ["proposal_write_next"],
    "section_prompts.PERSONNEL": ["proposal_write_next"],
    "section_prompts.TRACK_RECORD": ["proposal_write_next"],
    "section_prompts.SECURITY": ["proposal_write_next"],
    "section_prompts.MAINTENANCE": ["proposal_write_next"],
    "section_prompts.ADDED_VALUE": ["proposal_write_next"],
    "section_prompts.CASE_B": ["proposal_write_next"],
    "proposal_prompts.CASE_A_PROMPT": ["proposal_write_next"],
    "proposal_prompts.CASE_B_PROMPT": ["proposal_write_next"],
    "proposal_prompts.SELF_REVIEW": ["self_review"],
    # 발표 자료
    "proposal_prompts.PRESENTATION_STRATEGY": ["presentation_strategy"],
    "proposal_prompts.PPT_SLIDE": ["ppt_slide"],
    "ppt_pipeline.TOC_SYSTEM": ["ppt_toc"],
    "ppt_pipeline.TOC_USER": ["ppt_toc"],
    "ppt_pipeline.VISUAL_BRIEF_SYSTEM": ["ppt_visual_brief"],
    "ppt_pipeline.VISUAL_BRIEF_USER": ["ppt_visual_brief"],
    "ppt_pipeline.STORYBOARD_SYSTEM": ["ppt_storyboard"],
    "ppt_pipeline.STORYBOARD_USER": ["ppt_storyboard"],
    # 품질 보증
    "trustworthiness.SOURCE_TAG_FORMAT": ["proposal_write_next", "self_review"],
    "submission_docs.EXTRACT_SUBMISSION_DOCS_PROMPT": ["extract_submission_docs"],
}

# ── prompt_id → 카테고리 역매핑 ──

_CATEGORY_BY_MODULE: dict[str, str] = {}
for cat_id, cat_info in PROMPT_CATEGORIES.items():
    for mod in cat_info["source_modules"]:
        _CATEGORY_BY_MODULE[mod] = cat_id


def get_category_for_module(module_path: str) -> str:
    """모듈 경로 → 카테고리 ID."""
    return _CATEGORY_BY_MODULE.get(module_path, "quality_assurance")


async def get_categories_with_prompts() -> dict:
    """카테고리별 프롬프트 목록 + DB 메타 조합."""
    from app.services.domains.proposal.prompt_registry import (
        PROMPT_SOURCES, _make_prompt_id, _estimate_tokens, _extract_variables,
    )

    categories = []
    total = 0

    for cat_id, cat_info in PROMPT_CATEGORIES.items():
        prompts = []
        for module_path in cat_info["source_modules"]:
            if module_path not in PROMPT_SOURCES:
                continue
            try:
                mod = importlib.import_module(module_path)
            except ImportError:
                continue

            for const_name in PROMPT_SOURCES[module_path]:
                text = getattr(mod, const_name, None)
                if not text or not isinstance(text, str):
                    continue

                prompt_id = _make_prompt_id(module_path, const_name)
                prompts.append({
                    "prompt_id": prompt_id,
                    "label": const_name.replace("_", " ").title(),
                    "source_file": module_path.replace(".", "/") + ".py",
                    "const_name": const_name,
                    "token_estimate": _estimate_tokens(text),
                    "variables": _extract_variables(text),
                    "category": cat_id,
                    "node_usage": PROMPT_NODE_USAGE.get(prompt_id, []),
                })

        total += len(prompts)
        categories.append({
            "id": cat_id,
            "label": cat_info["label"],
            "icon": cat_info["icon"],
            "description": cat_info["description"],
            "prompt_count": len(prompts),
            "prompts": prompts,
        })

    # DB에서 active 버전 정보 병합
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        registry = await (
            client.table("prompt_registry")
            .select("prompt_id, version, status")
            .eq("status", "active")
            .execute()
        )
        version_map = {r["prompt_id"]: r["version"] for r in (registry.data or [])}
        for cat in categories:
            for p in cat["prompts"]:
                p["active_version"] = version_map.get(p["prompt_id"], 0)
                p["status"] = "active" if p["prompt_id"] in version_map else "unregistered"
    except Exception:
        for cat in categories:
            for p in cat["prompts"]:
                p["active_version"] = 0
                p["status"] = "unregistered"

    return {"categories": categories, "total_prompts": total}


async def get_worst_performers(limit: int = 5) -> dict:
    """수정율/품질 기준 워스트 프롬프트."""
    from app.services.domains.proposal.prompt_tracker import check_prompts_needing_attention

    attention = await check_prompts_needing_attention(
        edit_ratio_threshold=0.0, min_edits=1,
    )
    worst_edit = sorted(
        attention, key=lambda x: x["avg_edit_ratio"], reverse=True,
    )[:limit]

    worst_quality: list[dict] = []
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        result = await (
            client.table("mv_prompt_effectiveness")
            .select("prompt_id, avg_quality_score, proposals_used")
            .not_.is_("avg_quality_score", "null")
            .order("avg_quality_score")
            .limit(limit)
            .execute()
        )
        worst_quality = result.data or []
    except Exception:
        pass

    return {
        "worst_by_edit_ratio": worst_edit,
        "worst_by_quality": worst_quality,
    }
