"""
STEP 5: PPT 슬라이드 생성 + v3.2 발표전략 (§29)

ppt_slide: 섹션 → 슬라이드 변환.
presentation_strategy: 발표 전략 수립 (서류심사 시 건너뛰기).
"""

import logging

from app.graph.state import PPTSlide, ProposalState
from app.prompts.proposal_prompts import (
    PPT_SLIDE_PROMPT,
    PRESENTATION_STRATEGY_PROMPT,
)
from app.services.claude_client import claude_generate

logger = logging.getLogger(__name__)


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


async def ppt_slide(state: ProposalState) -> dict:
    """STEP 5: 섹션을 PPT 슬라이드로 변환."""
    slide_id = state.get("_current_slide_id", "slide_0")

    # 해당 섹션 내용 찾기
    sections = state.get("proposal_sections", [])
    section_content = ""
    for s in sections:
        sid = s.section_id if hasattr(s, "section_id") else s.get("section_id", "")
        if sid == slide_id:
            section_content = s.content if hasattr(s, "content") else s.get("content", "")
            break

    if not section_content and sections:
        # fallback: 인덱스 기반
        try:
            idx = int(slide_id.replace("slide_", "")) if "slide_" in slide_id else 0
            s = sections[idx] if idx < len(sections) else sections[0]
            section_content = s.content if hasattr(s, "content") else s.get("content", "")
        except (ValueError, IndexError):
            section_content = "(섹션 내용 없음)"

    # 전략 + 발표전략
    strategy = state.get("strategy")
    s_dict = {}
    if strategy:
        s_dict = strategy.model_dump() if hasattr(strategy, "model_dump") else (strategy if isinstance(strategy, dict) else {})

    pres_strategy = state.get("presentation_strategy", {})
    pres_text = ""
    if isinstance(pres_strategy, dict) and not pres_strategy.get("skipped"):
        pres_text = str(pres_strategy)

    prompt = PPT_SLIDE_PROMPT.format(
        section_content=section_content[:4000],
        win_theme=s_dict.get("win_theme", ""),
        key_messages=s_dict.get("key_messages", []),
        presentation_strategy=pres_text or "(발표전략 없음)",
        slide_id=slide_id,
    )

    result = await claude_generate(prompt)

    slide = PPTSlide(
        slide_id=result.get("slide_id", slide_id),
        title=result.get("title", slide_id),
        content=result.get("content", ""),
        notes=result.get("notes", ""),
        version=1,
    )

    return {"parallel_results": {"slides": [slide]}}
