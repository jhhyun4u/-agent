"""
STEP 2: 전략 수립 노드 (§29-5)

포지셔닝 매트릭스 기반 전략 + SWOT + 시나리오 + 대안 2가지.
v3.2: 경쟁분석 프레임워크 + 연구수행 전략.
토큰 예산: 25,000
"""

import logging
from uuid import UUID

from app.graph.state import ProposalState, Strategy, StrategyAlternative
from app.graph.context_helpers import (
    extract_credible_research,
    get_rfp_summary,
    query_kb_context,
    rfp_to_dict,
)
from app.prompts.strategy import (
    COMPETITIVE_ANALYSIS_FRAMEWORK,
    POSITIONING_STRATEGY_MATRIX,
    STRATEGY_GENERATE_PROMPT,
    STRATEGY_RESEARCH_FRAMEWORK,
)
from app.services.claude_client import claude_generate
from app.services import prompt_registry, prompt_tracker
from app.services.version_manager import execute_node_and_create_version

logger = logging.getLogger(__name__)


async def strategy_generate(state: ProposalState) -> dict:
    """STEP 2: 포지셔닝 기반 전략 수립 + 대안 생성."""

    rfp = state.get("rfp_analysis")
    go_no_go = state.get("go_no_go")
    positioning = state.get("positioning", "defensive")

    if not rfp:
        return {"current_step": "strategy_error"}

    rfp_dict = rfp_to_dict(rfp)
    rfp_summary = get_rfp_summary(rfp_dict)

    # Go/No-Go 결과
    gng_dict = {}
    if go_no_go:
        gng_dict = go_no_go.model_dump() if hasattr(go_no_go, "model_dump") else (go_no_go if isinstance(go_no_go, dict) else {})

    # 포지셔닝 가이드
    pos_guide = POSITIONING_STRATEGY_MATRIX.get(positioning, POSITIONING_STRATEGY_MATRIX["defensive"])

    # KB 조회 (go_no_go와 동일 테이블이지만, competitor_history도 포함)
    kb = await query_kb_context(
        org_id=state.get("org_id", ""),
        client_name=rfp_dict.get("client", ""),
        include_capabilities=True,
        include_client_intel=True,
        include_competitors=True,
        include_lessons=True,
        include_competitor_history=True,
    )

    # 과거 전략 레코드 조회 (C-2)
    past_strategy_text = ""
    try:
        from app.utils.supabase_client import get_async_client as _get_db
        db = await _get_db()
        past = await (
            db.table("content_library")
            .select("title, body, tags")
            .eq("type", "strategy_record")
            .ilike("title", f"%{rfp_dict.get('client', '')}%")
            .order("created_at", desc=True)
            .limit(2)
            .execute()
        )
        if past.data:
            parts = []
            for p in past.data:
                parts.append(f"- {p['title']}\n  {(p.get('body') or '')[:300]}")
            past_strategy_text = "\n\n## 과거 전략 레코드 (이 발주기관)\n" + "\n".join(parts)
    except Exception as e:
        logger.debug(f"보조 데이터 조회 실패 (무시): {e}")
        pass

    # 리서치 브리프 + credibility 필터링
    research_text = extract_credible_research(
        state.get("research_brief"), max_evidence=20
    )

    # 가격전략 시장 데이터 (PricingEngine 연동)
    pricing_strategy_context = ""
    try:
        from app.services.bid_calculator import parse_budget_string
        from app.services.pricing import PricingEngine, QuickEstimateRequest

        budget_str = rfp_dict.get("budget", "")
        budget_val = parse_budget_string(budget_str) if budget_str else None
        if budget_val and budget_val > 0:
            engine = PricingEngine()
            qe = await engine.quick_estimate(QuickEstimateRequest(
                budget=budget_val,
                evaluation_method=rfp_dict.get("eval_method", "종합심사"),
                domain=rfp_dict.get("domain", "SI/SW개발"),
                positioning=positioning,
                competitor_count=5,
            ))
            pricing_strategy_context = (
                f"\n## 시장 기반 가격 전략 데이터\n"
                f"- 추천 낙찰률: {qe.recommended_ratio}% (시장 평균: {qe.market_avg_ratio * 100:.1f}%)\n" if qe.market_avg_ratio else
                f"\n## 시장 기반 가격 전략 데이터\n"
                f"- 추천 낙찰률: {qe.recommended_ratio}%\n"
            )
            pricing_strategy_context += (
                f"- 수주확률: {qe.win_probability:.0%} (유사 사례 {qe.comparable_cases}건)\n"
                f"- 포지셔닝별 가격 가이드: {qe.positioning_adjustment}\n"
            )
    except Exception as e:
        logger.debug(f"PricingEngine 가격전략 조회 실패 (무시): {e}")

    # Go/No-Go에서 도출한 핵심 승부수
    strategic_focus = gng_dict.get("strategic_focus", "")

    # 레지스트리에서 진화된 프롬프트 조회 (A/B 라우팅 포함)
    proposal_id = state.get("project_id", "")
    try:
        reg_text, _, _ = await prompt_registry.get_prompt_for_experiment(
            "strategy.GENERATE_PROMPT", proposal_id
        )
    except Exception as e:
        logger.debug(f"프롬프트 레지스트리 조회 실패 (무시): {e}")
        reg_text = ""

    prompt = (reg_text or STRATEGY_GENERATE_PROMPT).format(
        rfp_summary=rfp_summary,
        positioning=positioning,
        positioning_label=pos_guide["label"],
        positioning_rationale=gng_dict.get("positioning_rationale", ""),
        pros=gng_dict.get("pros", []),
        risks=gng_dict.get("risks", []),
        strategic_focus=strategic_focus or "(미도출)",
        positioning_guide=_format_positioning_guide(pos_guide),
        capabilities_text=kb.get("capabilities", "(역량 DB 없음)"),
        research_brief=research_text or "(리서치 미수행)",
        client_intel_text=kb.get("client_intel", "(발주기관 정보 없음)"),
        competitor_text=kb.get("competitors", "(경쟁사 정보 없음)"),
        lessons_text=kb.get("lessons", "(과거 교훈 없음 — 첫 번째 제안)"),
        competitor_history_text=kb.get("competitor_history", "(대전 기록 없음)"),
        competitive_analysis_framework=COMPETITIVE_ANALYSIS_FRAMEWORK,
        strategy_research_framework=STRATEGY_RESEARCH_FRAMEWORK,
    )

    # 과거 전략 참조 추가 (C-2)
    if past_strategy_text:
        prompt += past_strategy_text

    # 가격전략 시장 데이터 추가
    if pricing_strategy_context:
        prompt += f"\n\n{pricing_strategy_context}\n위 시장 데이터를 price_strategy 설정 시 참고하세요."

    result = await claude_generate(prompt, max_tokens=8000, step_name="strategy_generate")

    # DEBUG: 상세 로깅
    import json as _json
    logger.info(f"STEP 2 Claude 응답 키: {list(result.keys())}")
    logger.info(f"STEP 2 alternatives 키 존재: {'alternatives' in result}")
    logger.info(f"STEP 2 alternatives 값: {result.get('alternatives')}")
    logger.info(f"STEP 2 alternatives 개수: {len(result.get('alternatives', []))}")

    if result.get("_parse_error"):
        logger.warning(f"STEP 2 JSON 파싱 오류! 원본 응답 (처음 1000자):")
        logger.warning(result.get('text', '')[:1000])
    else:
        # JSON 전체 출력 (파싱이 성공한 경우)
        result_str = _json.dumps(result, ensure_ascii=False, default=str, indent=2)
        logger.info(f"STEP 2 완전한 Claude JSON 응답:\n{result_str[:2000]}")

    # 프롬프트 사용 기록
    if proposal_id:
        try:
            _, sg_ver, sg_hash = await prompt_registry.get_active_prompt("strategy.GENERATE_PROMPT")
            await prompt_tracker.record_usage(
                proposal_id=proposal_id,
                artifact_step="strategy_generate",
                section_id=None,
                prompt_id="strategy.GENERATE_PROMPT",
                prompt_version=sg_ver,
                prompt_hash=sg_hash,
            )
        except Exception as e:
            logger.debug(f"보조 데이터 조회 실패 (무시): {e}")
            pass

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

    # 전략 대안 없음 방어: 기본 대안 생성
    if not alternatives:
        logger.error("전략 대안 없음 — 기본 대안으로 진행")
        alternatives = [StrategyAlternative(
            alt_id="default",
            ghost_theme="차별화 없음",
            win_theme="차별화 제안",
            action_forcing_event="품질·비용 우위",
            key_messages=["품질 중심의 제안"],
            price_strategy={},
            risk_assessment={},
        )]

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

    # KB 자동 축적 (A-3: 전략 결과)
    try:
        from app.services.kb_updater import save_strategy_to_kb
        await save_strategy_to_kb(
            org_id=state.get("org_id", ""),
            proposal_id=state.get("project_id", ""),
            client_name=rfp_dict.get("client", ""),
            positioning=positioning,
            strategy_result=result,
        )
    except Exception as e:
        logger.debug(f"전략 KB 축적 실패 (무시): {e}")

    # Phase 1: Create artifact version
    try:
        strategy_data = strategy.model_dump() if hasattr(strategy, "model_dump") else strategy
        version_num, artifact_version = await execute_node_and_create_version(
            proposal_id=UUID(state.get("project_id")),
            node_name="strategy_generate",
            output_key="strategy",
            artifact_data=strategy_data,
            user_id=UUID(state.get("created_by")),
            state=state
        )
        logger.info(f"Strategy v{version_num} created for proposal {state.get('project_id')}")
    except Exception as e:
        logger.warning(f"Strategy versioning 실패 (계속 진행): {e}")

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
