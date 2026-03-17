"""
STEP 5: PPT 3단계 파이프라인 (TOC → Visual Brief → Storyboard)

presentation_strategy: 발표 전략 수립 (서류심사 시 건너뛰기).
ppt_toc: 평가항목 기반 25~35장 TOC 설계.
ppt_visual_brief: F-Pattern 시각 전략.
ppt_storyboard_node: 슬라이드 본문 + 발표자 노트.
"""

import json
import logging

from app.graph.state import PPTSlide, ProposalState
from app.prompts.ppt_pipeline import (
    PPT_STORYBOARD_SYSTEM,
    PPT_STORYBOARD_USER,
    PPT_TOC_SYSTEM,
    PPT_TOC_USER,
    PPT_VISUAL_BRIEF_SYSTEM,
    PPT_VISUAL_BRIEF_USER,
)
from app.prompts.proposal_prompts import PRESENTATION_STRATEGY_PROMPT
from app.services.claude_client import claude_generate

logger = logging.getLogger(__name__)


# ── 발표전략 (기존 유지) ──


async def presentation_strategy(state: ProposalState) -> dict:
    """v3.2: 발표전략 수립. 서류심사이면 건너뛰기."""
    rfp = state.get("rfp_analysis")
    rfp_dict = {}
    if rfp:
        rfp_dict = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})

    eval_method = str(rfp_dict.get("eval_method", ""))

    # 서류심사 → 발표전략 불필요
    if "document_only" in eval_method.lower() or "서류" in eval_method:
        logger.info("서류심사 — 발표전략 건너뛰기")
        return {
            "presentation_strategy": {"skipped": True, "reason": "서류심사"},
            "current_step": "presentation_strategy_document_only",
        }

    # 발표전략 수립
    strategy = state.get("strategy")
    s_dict = {}
    if strategy:
        s_dict = strategy.model_dump() if hasattr(strategy, "model_dump") else (strategy if isinstance(strategy, dict) else {})

    sections = state.get("proposal_sections", [])
    sections_summary = ""
    for s in sections:
        sd = s.model_dump() if hasattr(s, "model_dump") else (s if isinstance(s, dict) else {})
        sections_summary += f"- {sd.get('section_id', '')}: {sd.get('title', '')}\n"

    rfp_summary = f"""사업명: {rfp_dict.get('project_name', '')}
발주기관: {rfp_dict.get('client', '')}
평가방식: {eval_method}"""

    prompt = PRESENTATION_STRATEGY_PROMPT.format(
        rfp_summary=rfp_summary,
        eval_method=eval_method or "(평가 방식 미정)",
        positioning=state.get("positioning", "defensive"),
        win_theme=s_dict.get("win_theme", ""),
        sections_summary=sections_summary or "(섹션 없음)",
    )

    result = await claude_generate(prompt)

    return {
        "presentation_strategy": result,
        "current_step": "presentation_strategy_complete",
    }


# ── 공통 헬퍼 ──


def _build_ppt_context(state: ProposalState) -> dict:
    """ProposalState → 프롬프트 입력 dict 변환."""
    # RFP 분석
    rfp = state.get("rfp_analysis")
    rfp_dict = {}
    if rfp:
        rfp_dict = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})

    # 전략
    strategy = state.get("strategy")
    s_dict = {}
    if strategy:
        s_dict = strategy.model_dump() if hasattr(strategy, "model_dump") else (strategy if isinstance(strategy, dict) else {})

    # 계획
    plan = state.get("plan")
    plan_dict = {}
    if plan:
        plan_dict = plan.model_dump() if hasattr(plan, "model_dump") else (plan if isinstance(plan, dict) else {})

    # 섹션 계획 (score_weight DESC 정렬)
    eval_items = rfp_dict.get("eval_items", [])
    sorted_items = sorted(eval_items, key=lambda x: x.get("score_weight", 0), reverse=True)

    # 제안서 섹션 (content 요약)
    sections = state.get("proposal_sections", [])
    sections_data = []
    for s in sections:
        sd = s.model_dump() if hasattr(s, "model_dump") else (s if isinstance(s, dict) else {})
        sections_data.append({
            "section_id": sd.get("section_id", ""),
            "title": sd.get("title", ""),
            "content": sd.get("content", ""),
        })

    # 발표전략
    pres_strategy = state.get("presentation_strategy", {})
    pres_text = ""
    if isinstance(pres_strategy, dict) and not pres_strategy.get("skipped"):
        pres_text = json.dumps(pres_strategy, ensure_ascii=False)

    return {
        "project_name": state.get("project_name", ""),
        "evaluation_weights": eval_items,
        "evaluator_perspective": rfp_dict.get("evaluator_perspective", {}),
        "section_plan": sorted_items,
        "win_theme": s_dict.get("win_theme", ""),
        "differentiation_strategy": s_dict.get("competitor_analysis", {}),
        "team_plan": plan_dict.get("team", []),
        "schedule": plan_dict.get("schedule", {}),
        "proposal_sections": sections_data,
        "presentation_strategy": pres_text,
    }


# ── Step 1: TOC 생성 ──


async def ppt_toc(state: ProposalState) -> dict:
    """Step 1: 평가항목 기반 25~35장 TOC 설계."""
    ctx = _build_ppt_context(state)

    prompt_user = PPT_TOC_USER.format(
        project_name=ctx["project_name"],
        section_plan=json.dumps(ctx["section_plan"], ensure_ascii=False),
        win_theme=json.dumps(ctx["win_theme"], ensure_ascii=False) if ctx["win_theme"] else "(Win Theme 미정)",
        presentation_strategy=ctx["presentation_strategy"] or "(발표전략 없음)",
    )

    result = await claude_generate(
        prompt_user,
        system_prompt=PPT_TOC_SYSTEM,
        max_tokens=4096,
    )

    toc = result.get("toc", [])
    total_slides = result.get("total_slides", len(toc))
    logger.info(f"[PPT Step 1] TOC 완료 — {len(toc)}개 슬라이드")

    return {
        "ppt_storyboard": {"toc": toc, "total_slides": total_slides},
        "current_step": "ppt_toc_complete",
    }


# ── Step 2: Visual Brief ──


async def ppt_visual_brief(state: ProposalState) -> dict:
    """Step 2: F-Pattern 시각 전략."""
    ctx = _build_ppt_context(state)
    storyboard = state.get("ppt_storyboard", {})
    toc = storyboard.get("toc", [])

    prompt_user = PPT_VISUAL_BRIEF_USER.format(
        toc=json.dumps(toc, ensure_ascii=False),
        win_theme=json.dumps(ctx["win_theme"], ensure_ascii=False) if ctx["win_theme"] else "(Win Theme 미정)",
        differentiation_strategy=json.dumps(ctx["differentiation_strategy"], ensure_ascii=False),
    )

    result = await claude_generate(
        prompt_user,
        system_prompt=PPT_VISUAL_BRIEF_SYSTEM,
        max_tokens=4096,
    )

    visual_briefs = result.get("visual_briefs", [])
    logger.info(f"[PPT Step 2] Visual Brief 완료 — {len(visual_briefs)}개 슬라이드 시각 전략")

    # 기존 storyboard에 visual_briefs 병합
    updated = {**storyboard, "visual_briefs": visual_briefs}

    return {
        "ppt_storyboard": updated,
        "current_step": "ppt_visual_brief_complete",
    }


# ── Step 3: Storyboard ──


async def ppt_storyboard_node(state: ProposalState) -> dict:
    """Step 3: 슬라이드 본문 + 발표자 노트."""
    ctx = _build_ppt_context(state)
    storyboard = state.get("ppt_storyboard", {})
    toc = storyboard.get("toc", [])
    visual_briefs = storyboard.get("visual_briefs", [])

    prompt_user = PPT_STORYBOARD_USER.format(
        toc=json.dumps(toc, ensure_ascii=False),
        visual_brief=json.dumps(visual_briefs, ensure_ascii=False),
        win_theme=json.dumps(ctx["win_theme"], ensure_ascii=False) if ctx["win_theme"] else "(Win Theme 미정)",
        differentiation_strategy=json.dumps(ctx["differentiation_strategy"], ensure_ascii=False),
        evaluator_perspective=json.dumps(ctx["evaluator_perspective"], ensure_ascii=False),
        proposal_sections=json.dumps(ctx["proposal_sections"], ensure_ascii=False),
        schedule=json.dumps(ctx["schedule"], ensure_ascii=False),
        team_plan=json.dumps(ctx["team_plan"], ensure_ascii=False),
    )

    result = await claude_generate(
        prompt_user,
        system_prompt=PPT_STORYBOARD_SYSTEM,
        max_tokens=16384,
    )

    slides = result.get("slides", [])
    eval_coverage = result.get("eval_coverage", {})
    total_slides = storyboard.get("total_slides", len(slides))

    logger.info(
        f"[PPT Step 3] Storyboard 완료 — {len(slides)}장 "
        f"/ eval_coverage: {list(eval_coverage.keys())}"
    )

    # 최종 storyboard (presentation_pptx_builder 직접 소비)
    final_storyboard = {
        "slides": slides,
        "total_slides": total_slides,
        "eval_coverage": eval_coverage,
        "toc": toc,
        "visual_briefs": visual_briefs,
    }

    # 호환용 PPTSlide 리스트 (간략 변환)
    ppt_slides = []
    for s in slides:
        slide_num = s.get("slide_num", 0)
        ppt_slides.append(PPTSlide(
            slide_id=f"slide_{slide_num}",
            title=s.get("title", ""),
            content=json.dumps(s, ensure_ascii=False)[:4000],
            notes=s.get("speaker_notes", ""),
            version=1,
        ))

    return {
        "ppt_storyboard": final_storyboard,
        "ppt_slides": ppt_slides,
        "current_step": "ppt_storyboard_complete",
    }
