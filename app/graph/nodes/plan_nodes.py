"""
STEP 3: 실행 계획 5개 병렬 노드 (§4, §29-6)

plan_team, plan_assign, plan_schedule, plan_story, plan_price.
v3.3: plan_price에서 labor_rates, market_price_data DB 조회.
"""

import logging
from datetime import datetime

from app.graph.state import ProposalState
from app.graph.context_helpers import (
    extract_evidence_candidates,
    get_rfp_summary_compact,
    query_kb_context,
    rfp_to_dict,
)
from app.prompts.plan import (
    BUDGET_DETAIL_FRAMEWORK,
    PLAN_ASSIGN_PROMPT,
    PLAN_PRICE_PROMPT,
    PLAN_SCHEDULE_PROMPT,
    PLAN_STORY_PROMPT,
    PLAN_TEAM_PROMPT,
)
from app.services.claude_client import claude_generate
from app.services import prompt_registry, prompt_tracker

logger = logging.getLogger(__name__)


async def _get_evolved_prompt(state: ProposalState, prompt_id: str, fallback: str) -> str:
    """레지스트리에서 진화된 프롬프트 조회 (A/B 라우팅 포함). 실패 시 Python 상수 폴백."""
    try:
        proposal_id = state.get("project_id", "")
        text, _, _ = await prompt_registry.get_prompt_for_experiment(prompt_id, proposal_id)
        return text or fallback
    except Exception as e:
        logger.debug(f"보조 데이터 조회 실패 (무시): {e}")
        return fallback


async def _track_plan_prompt(state: ProposalState, step: str, prompt_id: str) -> None:
    """plan 노드 공통 프롬프트 추적 헬퍼."""
    proposal_id = state.get("project_id", "")
    if not proposal_id:
        return
    try:
        _, ver, hash_ = await prompt_registry.get_active_prompt(prompt_id)
        await prompt_tracker.record_usage(
            proposal_id=proposal_id,
            artifact_step=step,
            section_id=None,
            prompt_id=prompt_id,
            prompt_version=ver,
            prompt_hash=hash_,
        )
    except Exception as e:
        logger.debug(f"보조 데이터 조회 실패 (무시): {e}")


def _get_rfp_summary(state: ProposalState) -> str:
    """RFP 분석 결과를 텍스트 요약 (공통 헬퍼 위임)."""
    return get_rfp_summary_compact(rfp_to_dict(state.get("rfp_analysis")))


def _get_strategy_fields(state: ProposalState) -> dict:
    """전략 주요 필드 추출 (context_helpers.get_strategy_dict 활용)."""
    from app.graph.context_helpers import get_strategy_dict
    d = get_strategy_dict(state.get("strategy"))
    if not d:
        return {"win_theme": "", "ghost_theme": "", "key_messages": [], "action_forcing_event": "", "price_strategy": {}}
    return {
        "win_theme": d.get("win_theme", ""),
        "ghost_theme": d.get("ghost_theme", ""),
        "key_messages": d.get("key_messages", []),
        "action_forcing_event": d.get("action_forcing_event", ""),
        "price_strategy": d.get("price_strategy", {}),
    }


def _get_budget_constraint_text(state: ProposalState) -> str:
    """bid_budget_constraint에서 프롬프트 주입용 텍스트 생성."""
    bbc = state.get("bid_budget_constraint")
    if not bbc or not isinstance(bbc, dict) or not bbc.get("total_bid_price"):
        return ""
    return (
        f"\n\n## 예산 제약 (입찰가격계획 확정)\n"
        f"- 확정 입찰가: {bbc['total_bid_price']:,}원 (낙찰률 {bbc.get('bid_ratio', 0):.1f}%)\n"
        f"- 직접인건비 한도: {bbc.get('labor_budget', 0):,}원\n"
        f"- 최대 투입 인력: {bbc.get('max_team_mm', 0):.1f} M/M\n"
        f"- 시나리오: {bbc.get('scenario_name', 'balanced')}\n"
        f"- 비용 기준: {bbc.get('cost_standard', 'KOSA')}\n"
        f"\n위 예산 범위 내에서 팀을 구성하세요. 초과 시 명확한 근거를 제시하세요."
    )


async def plan_team(state: ProposalState) -> dict:
    """STEP 3: 팀 구성 계획. v3.8: bid_budget_constraint 반영."""
    rfp_summary = _get_rfp_summary(state)
    sf = _get_strategy_fields(state)

    # 역량 DB 조회 (공통 헬퍼)
    kb = await query_kb_context(
        org_id=state.get("org_id", ""),
        include_capabilities=True,
        include_client_intel=False,
        include_competitors=False,
        include_lessons=False,
    )
    capabilities_text = kb.get("capabilities", "")

    evolved = await _get_evolved_prompt(state, "plan.TEAM_PROMPT", PLAN_TEAM_PROMPT)
    prompt = evolved.format(
        rfp_summary=rfp_summary,
        positioning=state.get("positioning", "defensive"),
        win_theme=sf["win_theme"],
        key_messages=sf["key_messages"],
        capabilities_text=capabilities_text or "(역량 DB 없음)",
    )

    # v3.8: 예산 제약 주입
    budget_constraint_text = _get_budget_constraint_text(state)
    if budget_constraint_text:
        prompt += budget_constraint_text

    result = await claude_generate(prompt)
    await _track_plan_prompt(state, "plan_team", "plan.TEAM_PROMPT")
    return {"parallel_results": {"team": result.get("team", [])}}


async def plan_assign(state: ProposalState) -> dict:
    """STEP 3: 산출물 + 역할 배분."""
    rfp_summary = _get_rfp_summary(state)
    team = state.get("parallel_results", {}).get("team", [])
    team_summary = "\n".join(f"- {t.get('role', '')}: {t.get('grade', '')}, {t.get('mm', 0)} M/M" for t in team) if team else "(팀 구성 미정)"

    evolved = await _get_evolved_prompt(state, "plan.ASSIGN_PROMPT", PLAN_ASSIGN_PROMPT)
    prompt = evolved.format(
        rfp_summary=rfp_summary,
        team_summary=team_summary,
    )

    result = await claude_generate(prompt)
    await _track_plan_prompt(state, "plan_assign", "plan.ASSIGN_PROMPT")
    return {"parallel_results": {"deliverables": result.get("deliverables", [])}}


async def plan_schedule(state: ProposalState) -> dict:
    """STEP 3: 추진 일정."""
    rfp_summary = _get_rfp_summary(state)
    rfp = state.get("rfp_analysis")
    deadline = ""
    if rfp:
        deadline = rfp.deadline if hasattr(rfp, "deadline") else (rfp.get("deadline", "") if isinstance(rfp, dict) else "")

    deliverables = state.get("parallel_results", {}).get("deliverables", [])
    deliverables_summary = "\n".join(f"- {d.get('name', '')}" for d in deliverables) if deliverables else "(산출물 미정)"

    evolved = await _get_evolved_prompt(state, "plan.SCHEDULE_PROMPT", PLAN_SCHEDULE_PROMPT)
    prompt = evolved.format(
        rfp_summary=rfp_summary,
        deadline=deadline,
        deliverables_summary=deliverables_summary,
    )

    result = await claude_generate(prompt)
    await _track_plan_prompt(state, "plan_schedule", "plan.SCHEDULE_PROMPT")
    return {"parallel_results": {"schedule": result.get("schedule", {})}}


async def plan_story(state: ProposalState) -> dict:
    """STEP 3: 목차 확정 + 섹션별 스토리라인 설계."""
    rfp_summary = _get_rfp_summary(state)
    sf = _get_strategy_fields(state)
    rfp = state.get("rfp_analysis")
    eval_items = []
    if rfp:
        eval_items = rfp.eval_items if hasattr(rfp, "eval_items") else (rfp.get("eval_items", []) if isinstance(rfp, dict) else [])

    # 현재 목차 (RFP 분석 기반 초안)
    current_sections = state.get("dynamic_sections", [])
    current_sections_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(current_sections)) if current_sections else "(목차 미생성)"

    # research_brief에서 고신뢰 근거 추출 (공통 헬퍼)
    evidence_text = extract_evidence_candidates(state.get("research_brief", {}))

    # KB 유사 콘텐츠 보강 (C-4)
    try:
        from app.services.content_library import suggest_content_for_section
        rfp_dict_for_kb = rfp_to_dict(rfp) if rfp else {}
        suggestions = await suggest_content_for_section(
            section_topic=rfp_dict_for_kb.get("project_name", ""),
            org_id=state.get("org_id", ""),
            top_k=5,
        )
        if suggestions:
            kb_evidence = "\n\n과거 수주 제안서 참고 콘텐츠:\n"
            for s in suggestions[:5]:
                kb_evidence += f"- {s.get('title', '')}: {(s.get('body_excerpt') or '')[:200]}\n"
            evidence_text += kb_evidence
    except Exception as e:
        logger.debug(f"보조 데이터 조회 실패 (무시): {e}")

    # 평가항목 ID 목록 (커버리지 검증용)
    eval_item_ids = [item.get("item", "") for item in eval_items if isinstance(item, dict)]
    eval_item_ids_text = ", ".join(eval_item_ids) if eval_item_ids else "(평가항목 미추출)"

    evolved = await _get_evolved_prompt(state, "plan.STORY_PROMPT", PLAN_STORY_PROMPT)
    prompt = evolved.format(
        rfp_summary=rfp_summary,
        current_sections=current_sections_text,
        positioning=state.get("positioning", "defensive"),
        win_theme=sf["win_theme"],
        ghost_theme=sf["ghost_theme"],
        key_messages=sf["key_messages"],
        action_forcing_event=sf["action_forcing_event"],
        eval_items=eval_items,
        evidence_candidates=evidence_text,
        eval_item_ids=eval_item_ids_text,
    )

    result = await claude_generate(prompt)
    await _track_plan_prompt(state, "plan_story", "plan.STORY_PROMPT")
    return {"parallel_results": {"storylines": result.get("storylines", {})}}


async def plan_price(state: ProposalState) -> dict:
    """STEP 3: 예산산정. v3.8: bid_plan 앵커 기반 Budget Narrative 중심 작성."""
    rfp_summary = _get_rfp_summary(state)
    sf = _get_strategy_fields(state)
    rfp = state.get("rfp_analysis")
    budget_str = ""
    if rfp:
        budget_str = rfp.budget if hasattr(rfp, "budget") else (rfp.get("budget", "") if isinstance(rfp, dict) else "")

    team = state.get("parallel_results", {}).get("team", [])
    team_summary = "\n".join(f"- {t.get('role', '')}: {t.get('grade', '')}, {t.get('mm', 0)} M/M" for t in team) if team else "(팀 구성 미정)"

    # ── v3.8: bid_plan 결과를 앵커로 사용 ──
    bid_plan_context = ""
    bbc = state.get("bid_budget_constraint")
    bp = state.get("bid_plan")
    if bbc and isinstance(bbc, dict) and bbc.get("total_bid_price"):
        bid_plan_context = (
            f"\n## 확정된 입찰가격계획 (STEP 2.5)\n"
            f"- 확정 입찰가: {bbc['total_bid_price']:,}원 (낙찰률 {bbc.get('bid_ratio', 0):.1f}%)\n"
            f"- 시나리오: {bbc.get('scenario_name', 'balanced')}\n"
            f"- 직접인건비 한도: {bbc.get('labor_budget', 0):,}원\n"
            f"- 비용 기준: {bbc.get('cost_standard', 'KOSA')}\n"
        )
        if bp:
            bp_dict = bp.model_dump() if hasattr(bp, "model_dump") else (bp if isinstance(bp, dict) else {})
            if bp_dict.get("user_override_price"):
                bid_plan_context += f"- 사용자 오버라이드: {bp_dict['user_override_price']:,}원 ({bp_dict.get('user_override_reason', '')})\n"
            if bp_dict.get("win_probability"):
                bid_plan_context += f"- 예측 수주확률: {bp_dict['win_probability']:.0%}\n"

    # ── PricingEngine 재실행 (팀 구성 확정 후 정확한 원가 산출) ──
    algorithmic_pricing = "(알고리즘 분석 미수행)"
    try:
        from app.services.bid_calculator import parse_budget_string
        from app.services.pricing import PricingEngine, PricingSimulationRequest
        from app.services.pricing.models import PersonnelInput as PricingPersonnel

        budget_val = parse_budget_string(budget_str) if budget_str else None
        rfp_dict = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})

        if budget_val and budget_val > 0:
            pricing_personnel = []
            for t in team:
                if isinstance(t, dict) and t.get("grade") and t.get("mm"):
                    pricing_personnel.append(PricingPersonnel(
                        role=t.get("role", ""),
                        grade=t.get("grade", "중급"),
                        person_months=float(t.get("mm", 0)),
                    ))

            engine = PricingEngine()
            sim = await engine.simulate(PricingSimulationRequest(
                budget=budget_val,
                domain=rfp_dict.get("domain", "SI/SW개발"),
                evaluation_method=rfp_dict.get("eval_method", "종합심사"),
                tech_price_ratio=rfp_dict.get("tech_price_ratio", {"tech": 80, "price": 20}),
                positioning=state.get("positioning", "defensive"),
                competitor_count=5,
                personnel=pricing_personnel,
                client_name=rfp_dict.get("client", ""),
            ))
            algorithmic_pricing = sim.to_prompt_context()
    except Exception as e:
        logger.warning(f"PricingEngine 분석 실패 (Claude fallback): {e}")

    # ── 기존 DB 기반 벤치마크 (fallback 보완) ──
    labor_rates_table = "(노임단가 데이터 없음)"
    benchmark_summary = "(시장 벤치마크 없음)"
    cost_standard = bbc.get("cost_standard", "KOSA") if bbc else "KOSA"

    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        current_year = datetime.now().year

        for year in [current_year, current_year - 1]:
            rates = await client.table("labor_rates").select("grade, monthly_rate, daily_rate").eq("year", year).order("monthly_rate", desc=True).execute()
            if rates.data:
                labor_rates_table = "| 등급 | 월단가(원) | 일단가(원) |\n|------|-----------|----------|\n"
                for r in rates.data:
                    labor_rates_table += f"| {r['grade']} | {r['monthly_rate']:,} | {r['daily_rate']:,} |\n"
                break

        market = await client.table("market_price_data").select("domain, bid_ratio, num_bidders, evaluation_method, year").order("year", desc=True).limit(20).execute()
        if market.data:
            avg_ratio = sum(r.get("bid_ratio", 0) for r in market.data) / len(market.data)
            avg_bidders = sum(r.get("num_bidders", 0) for r in market.data) / len(market.data)
            benchmark_summary = f"평균 낙찰률: {avg_ratio:.1f}% | 평균 참여 업체 수: {avg_bidders:.1f}개"
    except Exception as e:
        logger.warning(f"노임단가/벤치마크 조회 실패: {e}")

    budget_framework = BUDGET_DETAIL_FRAMEWORK.format(
        cost_standard=cost_standard,
        labor_rates_table=labor_rates_table,
        benchmark_summary=benchmark_summary,
    )

    evolved = await _get_evolved_prompt(state, "plan.PRICE_PROMPT", PLAN_PRICE_PROMPT)
    prompt = evolved.format(
        rfp_summary=rfp_summary,
        budget=budget_str or "(예산 미정)",
        positioning=state.get("positioning", "defensive"),
        price_strategy=sf["price_strategy"],
        team_summary=team_summary,
        budget_framework=budget_framework,
    )

    # v3.8: bid_plan 앵커 컨텍스트 주입
    if bid_plan_context:
        prompt += f"\n\n{bid_plan_context}\n위 확정된 입찰가를 앵커로 하여, 상세 원가 구조와 가격 경쟁력 내러티브(Budget Narrative)를 작성하세요."

    # v3.9: RFP 가격점수 산식 주입 (price_scoring이 있으면 산식 준수 필수)
    if rfp:
        ps = rfp.price_scoring if hasattr(rfp, "price_scoring") else (rfp.get("price_scoring") if isinstance(rfp, dict) else None)
        if ps:
            ps_dict = ps.model_dump() if hasattr(ps, "model_dump") else (ps if isinstance(ps, dict) else {})
            if ps_dict.get("formula_type"):
                prompt += (
                    f"\n\n## RFP 가격점수 산식 (반드시 준수)\n"
                    f"- 산식 유형: {ps_dict.get('formula_type', '')}\n"
                    f"- 설명: {ps_dict.get('description', '')}\n"
                    f"- 가격 배점: {ps_dict.get('price_weight', 0)}점\n"
                    f"- 파라미터: {ps_dict.get('parameters', {})}\n"
                    f"\n위 산식에 따라 가격점수가 계산되므로, 입찰가 산정 시 이를 반영하세요."
                )

    # 알고리즘 분석 결과를 프롬프트에 추가
    if algorithmic_pricing != "(알고리즘 분석 미수행)":
        prompt += f"\n\n{algorithmic_pricing}\n\n위 알고리즘 분석 결과를 참고하되, 정성적 판단(발주기관 특성, 전략적 맥락)을 추가하여 최종 원가 내역을 작성하세요."

    result = await claude_generate(prompt, max_tokens=6000)
    await _track_plan_prompt(state, "plan_price", "plan.PRICE_PROMPT")
    bid_price = result.get("bid_price", result)

    return {
        "parallel_results": {"bid_price": bid_price},
        "budget_detail": bid_price,
    }
