"""
STEP 2: 전략 수립 노드 (§29-5)

포지셔닝 매트릭스 기반 전략 + SWOT + 시나리오 + 대안 2가지.
v3.2: 경쟁분석 프레임워크 + 연구수행 전략.
토큰 예산: 25,000
"""

import logging

from app.graph.state import ProposalState, Strategy, StrategyAlternative
from app.prompts.strategy import (
    COMPETITIVE_ANALYSIS_FRAMEWORK,
    POSITIONING_STRATEGY_MATRIX,
    STRATEGY_GENERATE_PROMPT,
    STRATEGY_RESEARCH_FRAMEWORK,
)
from app.services.claude_client import claude_generate

logger = logging.getLogger(__name__)


async def strategy_generate(state: ProposalState) -> dict:
    """STEP 2: 포지셔닝 기반 전략 수립 + 대안 생성."""

    rfp = state.get("rfp_analysis")
    go_no_go = state.get("go_no_go")
    positioning = state.get("positioning", "defensive")

    if not rfp:
        return {"current_step": "strategy_error"}

    # RFP 요약
    if hasattr(rfp, "model_dump"):
        rfp_dict = rfp.model_dump()
    elif isinstance(rfp, dict):
        rfp_dict = rfp
    else:
        rfp_dict = {}

    rfp_summary = f"""
사업명: {rfp_dict.get('project_name', '')}
발주기관: {rfp_dict.get('client', '')}
핫버튼: {rfp_dict.get('hot_buttons', [])}
평가항목: {rfp_dict.get('eval_items', [])}
기술:가격 비중: {rfp_dict.get('tech_price_ratio', {})}
필수요건: {rfp_dict.get('mandatory_reqs', [])}
특수조건: {rfp_dict.get('special_conditions', [])}
"""

    # Go/No-Go 결과
    gng_dict = {}
    if go_no_go:
        gng_dict = go_no_go.model_dump() if hasattr(go_no_go, "model_dump") else (go_no_go if isinstance(go_no_go, dict) else {})

    # 포지셔닝 가이드
    pos_guide = POSITIONING_STRATEGY_MATRIX.get(positioning, POSITIONING_STRATEGY_MATRIX["defensive"])

    # 역량 + KB 조회
    capabilities_text = ""
    client_intel_text = ""
    competitor_text = ""

    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        org_id = state.get("org_id", "")

        if org_id:
            caps = await client.table("capabilities").select("type, title, detail").eq("org_id", org_id).execute()
            capabilities_text = "\n".join(
                f"- [{c['type']}] {c['title']}: {c['detail']}" for c in (caps.data or [])
            )

        client_name = rfp_dict.get("client", "")
        if client_name:
            intel = await client.table("client_intelligence").select("*").ilike("client_name", f"%{client_name}%").limit(5).execute()
            if intel.data:
                client_intel_text = "\n".join(f"- {r['aspect']}: {r['detail']}" for r in intel.data)

        comp = await client.table("competitors").select("*").limit(10).execute()
        if comp.data:
            competitor_text = "\n".join(
                f"- {c['company_name']}: 강점={c.get('strengths', '')} / 약점={c.get('weaknesses', '')}"
                for c in comp.data
            )
    except Exception as e:
        logger.warning(f"KB 조회 실패 (계속 진행): {e}")

    # 리서치 브리프
    research_brief = state.get("research_brief", {})
    research_text = ""
    if isinstance(research_brief, dict):
        research_text = research_brief.get("summary", str(research_brief) if research_brief else "")
    elif research_brief:
        research_text = str(research_brief)

    prompt = STRATEGY_GENERATE_PROMPT.format(
        rfp_summary=rfp_summary,
        positioning=positioning,
        positioning_label=pos_guide["label"],
        positioning_rationale=gng_dict.get("positioning_rationale", ""),
        pros=gng_dict.get("pros", []),
        risks=gng_dict.get("risks", []),
        positioning_guide=_format_positioning_guide(pos_guide),
        capabilities_text=capabilities_text or "(역량 DB 없음)",
        research_brief=research_text or "(리서치 미수행)",
        client_intel_text=client_intel_text or "(발주기관 정보 없음)",
        competitor_text=competitor_text or "(경쟁사 정보 없음)",
        competitive_analysis_framework=COMPETITIVE_ANALYSIS_FRAMEWORK,
        strategy_research_framework=STRATEGY_RESEARCH_FRAMEWORK,
    )

    result = await claude_generate(prompt, max_tokens=8000)

    # 전략 대안 구성
    alternatives = []
    for alt_data in result.get("alternatives", []):
        alternatives.append(StrategyAlternative(
            alt_id=alt_data.get("alt_id", f"ALT-{len(alternatives)+1}"),
            ghost_theme=alt_data.get("ghost_theme", ""),
            win_theme=alt_data.get("win_theme", ""),
            action_forcing_event=alt_data.get("action_forcing_event", ""),
            key_messages=alt_data.get("key_messages", []),
            price_strategy=alt_data.get("price_strategy", {}),
            risk_assessment=alt_data.get("risk_assessment", {}),
        ))

    # 첫 번째 대안을 기본값으로 설정
    first_alt = alternatives[0] if alternatives else None

    strategy = Strategy(
        positioning=positioning,
        positioning_rationale=result.get("positioning_rationale", gng_dict.get("positioning_rationale", "")),
        alternatives=alternatives,
        selected_alt_id=first_alt.alt_id if first_alt else "",
        ghost_theme=first_alt.ghost_theme if first_alt else "",
        win_theme=first_alt.win_theme if first_alt else "",
        action_forcing_event=first_alt.action_forcing_event if first_alt else "",
        key_messages=first_alt.key_messages if first_alt else [],
        focus_areas=result.get("focus_areas", []),
        price_strategy=first_alt.price_strategy if first_alt else {},
        competitor_analysis=result.get("competitor_analysis", {}),
        risks=[],
    )

    return {
        "strategy": strategy,
        "current_step": "strategy_complete",
    }


def _format_positioning_guide(guide: dict) -> str:
    """포지셔닝 가이드를 텍스트로 포맷."""
    return f"""
- 유형: {guide['label']}
- 핵심 메시지: {guide['core_message']}
- 톤앤매너: {guide['tone']}
- 가격 접근: {guide['price_approach']}
- Ghost 전략: {guide['ghost_strategy']}
- 집중 영역: {', '.join(guide['key_focus'])}
"""
