"""
STEP 3: 실행 계획 5개 병렬 노드 (§4, §29-6)

plan_team, plan_assign, plan_schedule, plan_story, plan_price.
v3.3: plan_price에서 labor_rates, market_price_data DB 조회.
"""

import logging
from uuid import UUID

from app.graph.state import ProposalState, CustomerProfile
from app.graph.context_helpers import (
    extract_evidence_candidates,
    get_rfp_summary_compact,
    query_kb_context,
    rfp_to_dict,
)
from app.prompts.plan import (
    PLAN_ASSIGN_PROMPT,
    PLAN_SCHEDULE_PROMPT,
    PLAN_STORY_PROMPT,
    PLAN_TEAM_PROMPT,
    # NOTE: PLAN_PRICE_PROMPT and BUDGET_DETAIL_FRAMEWORK removed (v4.0 - pricing moved to STEP 4B)
)
from app.prompts.step8a import CUSTOMER_INTELLIGENCE_PROMPT
from app.services.claude_client import claude_generate
from app.services import prompt_registry, prompt_tracker
from app.services.version_manager import execute_node_and_create_version

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


async def proposal_customer_analysis(state: ProposalState) -> dict:
    """
    Deep client intelligence analysis (moved from STEP 8A to STEP 3A).

    Input:
        - rfp_analysis: RFP analysis results
        - strategy: Proposal strategy
        - kb_references: Knowledge base references

    Output:
        - customer_profile: Structured customer profile (versioned)

    Returns:
        Updated state dict with customer_profile and version info
    """
    try:
        # Step 1: Validate required inputs exist
        rfp_analysis = state.get("rfp_analysis")
        if not rfp_analysis:
            logger.warning("No RFP analysis available for proposal_customer_analysis")
            return {
                "customer_profile": None,
                "node_errors": {
                    **state.get("node_errors", {}),
                    "proposal_customer_analysis": "Missing rfp_analysis input",
                },
            }

        # Step 2: Gather context data
        strategy = state.get("strategy")
        kb_refs = state.get("kb_references", [])
        competitor_refs = state.get("competitor_refs", [])

        # Build context for Claude
        kb_context = []
        if kb_refs:
            kb_context.extend(
                [
                    f"- {ref.get('title', 'Reference')}: {ref.get('summary', '')}"
                    for ref in kb_refs[:5]
                ]
            )  # Limit to 5 refs
        if competitor_refs:
            kb_context.extend(
                [
                    f"- Competitor: {ref.get('name', 'Unknown')}"
                    for ref in competitor_refs[:3]
                ]
            )

        # Step 3: Call Claude for analysis
        prompt = CUSTOMER_INTELLIGENCE_PROMPT.format(
            rfp_analysis=rfp_analysis.model_dump_json()
            if hasattr(rfp_analysis, "model_dump_json")
            else str(rfp_analysis),
            strategy=strategy.model_dump_json()
            if strategy and hasattr(strategy, "model_dump_json")
            else "{}",
            kb_references="\n".join(kb_context)
            if kb_context
            else "No KB references available",
        )

        logger.info(
            f"Calling Claude for customer analysis (proposal {state.get('project_id')})"
        )

        response = await claude_generate(
            prompt=prompt,
            response_format="json",
            max_tokens=3500,
            step_name="proposal_customer_analysis",
        )

        # Step 4: Parse response into Pydantic model
        customer_profile = CustomerProfile(**response)

        logger.info(f"Generated customer profile for {customer_profile.client_org}")

        # Step 5: Create version artifact
        version_num, artifact_version = await execute_node_and_create_version(
            proposal_id=UUID(state["project_id"]),
            node_name="proposal_customer_analysis",
            output_key="customer_profile",
            artifact_data=customer_profile.model_dump(),
            user_id=UUID(state["created_by"]),
            state=state,
            parent_node_name="strategy_generate",
        )

        logger.info(
            f"Created customer_profile v{version_num} for proposal {state['project_id']}"
        )

        # Step 6: Return state update
        return {
            "customer_profile": customer_profile,
            "artifact_versions": {"customer_profile": [artifact_version]},
            "active_versions": {
                "proposal_customer_analysis_customer_profile": version_num
            },
        }

    except Exception as e:
        logger.exception(f"Error in proposal_customer_analysis: {str(e)}")
        return {
            "customer_profile": None,
            "node_errors": {
                **state.get("node_errors", {}),
                "proposal_customer_analysis": f"Analysis failed: {str(e)}",
            },
        }
