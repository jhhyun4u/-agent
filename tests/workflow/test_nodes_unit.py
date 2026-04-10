"""워크플로 노드별 단위 테스트.

각 그래프 노드 함수를 개별 mock state로 호출하여
입출력 스키마, 필수 필드, 에러 처리를 검증한다.

테스트 흐름 (워크플로 순서):
  STEP 1-①: rfp_analyze
  STEP 1-R: research_gather
  STEP 1-②: go_no_go
  STEP 2:   strategy_generate
  STEP 2.5: bid_plan
  STEP 3:   plan_team / plan_assign / plan_schedule / plan_story / plan_price
  STEP 3-M: plan_merge
  STEP 4:   proposal_write_next / self_review_with_auto_improve
  STEP 5-0: presentation_strategy
  STEP 5-1: ppt_toc
  STEP 5-2: ppt_visual_brief
  STEP 5-3: ppt_storyboard_node
  라우팅: edges (route_after_*)
  리뷰:   review_node / review_section_node
"""

import pytest
from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

from tests.workflow.conftest import (
    _make_claude_mock,
    _mock_get_active_prompt,
    _mock_get_prompt_for_experiment,
    _mock_record_usage,
    _make_workflow_supabase_mock,
    load_fixture,
)


# ── 공통 헬퍼 ──


def _base_state(**overrides) -> dict:
    """모든 노드 테스트에 필요한 최소 state."""
    state = {
        "project_id": "test-001",
        "project_name": "테스트 프로젝트",
        "org_id": "org-001",
        "mode": "full",
        "positioning": "defensive",
        "current_step": "",
        "rfp_raw": "",
        "rfp_analysis": None,
        "go_no_go": None,
        "strategy": None,
        "plan": None,
        "research_brief": None,
        "bid_plan": None,
        "bid_budget_constraint": None,
        "bid_detail": None,
        "proposal_sections": [],
        "compliance_matrix": [],
        "dynamic_sections": [],
        "parallel_results": {},
        "feedback_history": [],
        "rework_targets": [],
        "current_section_index": 0,
        "kb_references": [],
        "ppt_slides": [],
        "ppt_storyboard": {},
        "approval": {},
        "token_usage": {},
        "presentation_strategy": None,
    }
    state.update(overrides)
    return state


def _mock_patches():
    """노드 실행에 필요한 모든 mock patch 목록 반환."""
    mock_claude = _make_claude_mock()
    mock_sb = _make_workflow_supabase_mock()

    patches = [
        patch("app.services.claude_client.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.rfp_analyze.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.research_gather.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.go_no_go.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.strategy_generate.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.plan_nodes.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.proposal_nodes.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.ppt_nodes.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.submission_nodes.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.evaluation_nodes.claude_generate", side_effect=mock_claude),
        patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=mock_sb)),
        patch("app.services.prompt_registry.get_prompt_for_experiment", side_effect=_mock_get_prompt_for_experiment),
        patch("app.services.prompt_registry.get_active_prompt", side_effect=_mock_get_active_prompt),
        patch("app.services.prompt_tracker.record_usage", side_effect=_mock_record_usage),
    ]
    return patches


def _rfp_analysis_obj():
    """fixture 기반 RFPAnalysis 객체 생성."""
    from app.graph.state import RFPAnalysis, PriceScoringFormula
    fix = load_fixture("rfp_analyze.json")
    ps = fix.get("price_scoring")
    return RFPAnalysis(
        project_name=fix.get("project_name", "테스트"),
        client=fix.get("client", "ABC"),
        deadline=fix.get("deadline", "2026-06-30"),
        case_type=fix.get("case_type", "A"),
        eval_method=fix.get("eval_method", "종합심사"),
        eval_items=fix.get("eval_items", []),
        tech_price_ratio=fix.get("tech_price_ratio", {"tech": 80, "price": 20}),
        hot_buttons=fix.get("hot_buttons", []),
        mandatory_reqs=fix.get("mandatory_reqs", []),
        format_template=fix.get("format_template", {"exists": False, "structure": None}),
        volume_spec=fix.get("volume_spec", {}),
        special_conditions=fix.get("special_conditions", []),
        price_scoring=PriceScoringFormula(**ps) if ps else None,
        domain=fix.get("domain", ""),
        project_scope=fix.get("project_scope", ""),
        budget=fix.get("budget", ""),
        duration=fix.get("duration", ""),
        contract_type=fix.get("contract_type", ""),
        delivery_phases=fix.get("delivery_phases", []),
        qualification_requirements=fix.get("qualification_requirements", []),
        similar_project_requirements=fix.get("similar_project_requirements", []),
        key_personnel_requirements=fix.get("key_personnel_requirements", []),
        subcontracting_conditions=fix.get("subcontracting_conditions", []),
    )


def _go_no_go_obj():
    """fixture 기반 GoNoGoResult 객체."""
    from app.graph.state import GoNoGoResult
    fix = load_fixture("go_no_go.json")
    return GoNoGoResult(
        positioning=fix.get("positioning", "defensive"),
        positioning_rationale=fix.get("positioning_rationale", ""),
        feasibility_score=fix.get("feasibility_score", 75),
        score_breakdown=fix.get("score_breakdown", {}),
        pros=fix.get("pros", []),
        risks=fix.get("risks", []),
        recommendation=fix.get("recommendation", "go"),
        fatal_flaw=fix.get("fatal_flaw"),
        strategic_focus=fix.get("strategic_focus"),
    )


def _strategy_obj():
    """fixture 기반 Strategy 객체."""
    from app.graph.state import Strategy, StrategyAlternative
    fix = load_fixture("strategy.json")
    alts = []
    for a in fix.get("alternatives", []):
        alts.append(StrategyAlternative(
            alt_id=a.get("alt_id", "ALT-1"),
            ghost_theme=a.get("ghost_theme", ""),
            win_theme=a.get("win_theme", ""),
            action_forcing_event=a.get("action_forcing_event", ""),
            key_messages=a.get("key_messages", []),
            price_strategy=a.get("price_strategy", {}),
            risk_assessment=a.get("risk_assessment", {}),
        ))
    return Strategy(
        positioning="defensive",
        positioning_rationale=fix.get("positioning_rationale", ""),
        alternatives=alts,
        win_theme=alts[0].win_theme if alts else "",
        key_messages=alts[0].key_messages if alts else [],
    )


def _plan_obj():
    """fixture 기반 ProposalPlan 객체."""
    from app.graph.state import ProposalPlan
    return ProposalPlan(
        team=load_fixture("plan_team.json").get("team", []),
        deliverables=load_fixture("plan_assign.json").get("deliverables", []),
        schedule=load_fixture("plan_schedule.json").get("schedule", {}),
        storylines=load_fixture("plan_story.json").get("storylines", {}),
        bid_price=load_fixture("plan_price.json"),
    )


# ══════════════════════════════════════════════════════════
# STEP 1-①: rfp_analyze
# ══════════════════════════════════════════════════════════


class TestRfpAnalyze:
    """RFP 분석 노드 단위 테스트."""

    @pytest.mark.asyncio
    async def test_rfp_analyze_returns_required_fields(self):
        """rfp_analyze가 필수 출력 필드를 모두 반환하는지 검증."""
        from app.graph.nodes.rfp_analyze import rfp_analyze

        state = _base_state(rfp_raw="제안요청서\n사업명: 테스트\n발주기관: ABC\n예산: 5억원")

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)

            result = await rfp_analyze(state)

        assert "rfp_analysis" in result
        assert "compliance_matrix" in result
        assert "dynamic_sections" in result
        assert "current_step" in result
        assert result["current_step"] == "rfp_analyze_complete"

    @pytest.mark.asyncio
    async def test_rfp_analyze_no_rfp_raw(self):
        """rfp_raw가 빈 문자열이면 에러 step 반환."""
        from app.graph.nodes.rfp_analyze import rfp_analyze

        state = _base_state(rfp_raw="")

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)

            result = await rfp_analyze(state)

        assert result["current_step"] == "rfp_analyze_error"

    @pytest.mark.asyncio
    async def test_rfp_analysis_is_valid_model(self):
        """반환된 rfp_analysis가 RFPAnalysis 모델인지 확인."""
        from app.graph.nodes.rfp_analyze import rfp_analyze
        from app.graph.state import RFPAnalysis

        state = _base_state(rfp_raw="제안요청서\n사업명: ERP 구축\n평가항목: 기술이해도(30)")

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)

            result = await rfp_analyze(state)

        assert isinstance(result["rfp_analysis"], RFPAnalysis)
        assert result["rfp_analysis"].case_type in ("A", "B")

    @pytest.mark.asyncio
    async def test_rfp_analyze_v39_extended_fields(self):
        """v3.9 확장 필드가 정상 추출되는지 검증."""
        from app.graph.nodes.rfp_analyze import rfp_analyze

        state = _base_state(rfp_raw="제안요청서\n사업명: ERP 구축\n예산: 30억")

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)

            result = await rfp_analyze(state)

        rfp = result["rfp_analysis"]
        # fixture에 신규 필드가 포함되어 있으므로 값이 있어야 함
        assert rfp.domain == "SI/SW개발"
        assert rfp.project_scope != ""
        assert rfp.budget != ""
        assert rfp.duration != ""
        assert rfp.contract_type != ""
        assert len(rfp.delivery_phases) > 0
        assert len(rfp.qualification_requirements) > 0
        assert len(rfp.similar_project_requirements) > 0
        assert len(rfp.key_personnel_requirements) > 0
        assert len(rfp.subcontracting_conditions) > 0


# ══════════════════════════════════════════════════════════
# STEP 1-R: research_gather
# ══════════════════════════════════════════════════════════


class TestResearchGather:
    """선행 리서치 노드 단위 테스트."""

    @pytest.mark.asyncio
    async def test_research_gather_with_rfp(self):
        """rfp_analysis가 있으면 research_brief를 반환."""
        from app.graph.nodes.research_gather import research_gather

        state = _base_state(rfp_analysis=_rfp_analysis_obj())

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)

            result = await research_gather(state)

        assert "research_brief" in result
        assert result["current_step"] == "research_gather_complete"
        assert isinstance(result["research_brief"], dict)

    @pytest.mark.asyncio
    async def test_research_gather_no_rfp(self):
        """rfp_analysis가 None이면 빈 결과로 통과."""
        from app.graph.nodes.research_gather import research_gather

        state = _base_state(rfp_analysis=None)

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)

            result = await research_gather(state)

        assert result["current_step"] == "research_gather_complete"


# ══════════════════════════════════════════════════════════
# STEP 1-②: go_no_go
# ══════════════════════════════════════════════════════════


class TestGoNoGo:
    """Go/No-Go 판정 노드 단위 테스트."""

    @pytest.mark.asyncio
    async def test_go_no_go_returns_result(self):
        """go_no_go가 GoNoGoResult를 반환."""
        from app.graph.nodes.go_no_go import go_no_go
        from app.graph.state import GoNoGoResult

        state = _base_state(
            rfp_analysis=_rfp_analysis_obj(),
            research_brief=load_fixture("research_gather.json"),
        )

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)

            result = await go_no_go(state)

        assert "go_no_go" in result
        assert isinstance(result["go_no_go"], GoNoGoResult)
        assert result["go_no_go"].positioning in ("defensive", "offensive", "adjacent")
        assert result["current_step"] == "go_no_go_complete"

    @pytest.mark.asyncio
    async def test_go_no_go_no_rfp(self):
        """rfp_analysis 없으면 에러 step."""
        from app.graph.nodes.go_no_go import go_no_go

        state = _base_state()

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)

            result = await go_no_go(state)

        assert result["current_step"] == "go_no_go_error"

    @pytest.mark.asyncio
    async def test_go_no_go_lite_mode(self):
        """lite 모드에서도 정상 동작 (perf=0 + qual=0 + comp=10 + strategic=10 = 20)."""
        from app.graph.nodes.go_no_go import go_no_go

        state = _base_state(
            mode="lite",
            rfp_analysis=_rfp_analysis_obj(),
        )

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)

            result = await go_no_go(state)

        assert result["go_no_go"].feasibility_score == 20


# ══════════════════════════════════════════════════════════
# STEP 2: strategy_generate
# ══════════════════════════════════════════════════════════


class TestStrategyGenerate:
    """전략 수립 노드 단위 테스트."""

    @pytest.mark.asyncio
    async def test_strategy_generate_returns_strategy(self):
        """strategy_generate가 Strategy 모델을 반환."""
        from app.graph.nodes.strategy_generate import strategy_generate
        from app.graph.state import Strategy

        state = _base_state(
            rfp_analysis=_rfp_analysis_obj(),
            go_no_go=_go_no_go_obj(),
            research_brief=load_fixture("research_gather.json"),
        )

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)

            result = await strategy_generate(state)

        assert "strategy" in result
        assert isinstance(result["strategy"], Strategy)
        assert result["current_step"] == "strategy_complete"

    @pytest.mark.asyncio
    async def test_strategy_no_rfp(self):
        """rfp_analysis 없으면 에러."""
        from app.graph.nodes.strategy_generate import strategy_generate

        state = _base_state()

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)

            result = await strategy_generate(state)

        assert result["current_step"] == "strategy_error"


# ══════════════════════════════════════════════════════════
# STEP 2.5: bid_plan
# ══════════════════════════════════════════════════════════


class TestBidPlan:
    """입찰가격계획 노드 단위 테스트."""

    @pytest.mark.asyncio
    async def test_bid_plan_returns_result(self):
        """bid_plan이 BidPlanResult와 bid_budget_constraint를 반환."""
        from app.graph.nodes.bid_plan import bid_plan
        from app.graph.state import BidPlanResult

        rfp = _rfp_analysis_obj()
        # budget 필드가 필요 — RFPAnalysis에 없으므로 dict로 주입
        state = _base_state(rfp_analysis=rfp, positioning="defensive")

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)

            result = await bid_plan(state)

        assert "bid_plan" in result
        assert isinstance(result["bid_plan"], BidPlanResult)
        assert "bid_budget_constraint" in result
        assert result["current_step"] == "bid_plan_complete"


# ══════════════════════════════════════════════════════════
# STEP 3: plan_nodes (5개 병렬)
# ══════════════════════════════════════════════════════════


class TestPlanNodes:
    """실행 계획 5개 병렬 노드 단위 테스트."""

    def _plan_state(self, **extra):
        """plan 노드 공통 state."""
        return _base_state(
            rfp_analysis=_rfp_analysis_obj(),
            strategy=_strategy_obj(),
            go_no_go=_go_no_go_obj(),
            positioning="defensive",
            parallel_results={
                "team": load_fixture("plan_team.json").get("team", []),
                "deliverables": load_fixture("plan_assign.json").get("deliverables", []),
            },
            **extra,
        )

    @pytest.mark.asyncio
    async def test_plan_team(self):
        from app.graph.nodes.plan_nodes import plan_team

        state = self._plan_state()
        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)
            result = await plan_team(state)

        assert "parallel_results" in result
        assert "team" in result["parallel_results"]
        assert isinstance(result["parallel_results"]["team"], list)

    @pytest.mark.asyncio
    async def test_plan_assign(self):
        from app.graph.nodes.plan_nodes import plan_assign

        state = self._plan_state()
        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)
            result = await plan_assign(state)

        assert "deliverables" in result["parallel_results"]

    @pytest.mark.asyncio
    async def test_plan_schedule(self):
        from app.graph.nodes.plan_nodes import plan_schedule

        state = self._plan_state()
        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)
            result = await plan_schedule(state)

        assert "schedule" in result["parallel_results"]

    @pytest.mark.asyncio
    async def test_plan_story(self):
        from app.graph.nodes.plan_nodes import plan_story

        state = self._plan_state()
        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)
            result = await plan_story(state)

        assert "storylines" in result["parallel_results"]

    @pytest.mark.skip(reason="plan_price removed in v4.0 — pricing moved to STEP 4B (bid_plan)")
    @pytest.mark.asyncio
    async def test_plan_price(self):
        from app.graph.nodes.plan_nodes import plan_price

        state = self._plan_state()
        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)
            result = await plan_price(state)

        assert "bid_price" in result["parallel_results"]

    @pytest.mark.asyncio
    async def test_plan_team_with_budget_constraint(self):
        """bid_budget_constraint가 있으면 프롬프트에 예산 제약이 포함."""
        from app.graph.nodes.plan_nodes import plan_team

        state = self._plan_state(bid_budget_constraint={
            "total_bid_price": 450_000_000,
            "bid_ratio": 90.0,
            "labor_budget": 279_000_000,
            "max_team_mm": 41.0,
            "scenario_name": "balanced",
            "cost_standard": "KOSA",
        })

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)
            result = await plan_team(state)

        # 결과가 나오면 OK (프롬프트에 제약이 주입되었음)
        assert "team" in result["parallel_results"]


# ══════════════════════════════════════════════════════════
# STEP 3-M: plan_merge
# ══════════════════════════════════════════════════════════


class TestPlanMerge:
    """plan_merge 병합 노드 테스트."""

    def test_plan_merge_initial(self):
        """최초 실행: parallel_results에서 ProposalPlan 생성."""
        from app.graph.nodes.merge_nodes import plan_merge
        from app.graph.state import ProposalPlan

        state = _base_state(
            parallel_results={
                "team": [{"role": "PM", "grade": "특급", "mm": 6}],
                "deliverables": [{"name": "설계서"}],
                "schedule": {"phases": [{"name": "분석"}]},
                "storylines": {"sections": [{"eval_item": "기술이해도", "key_message": "테스트"}]},
                "bid_price": {"total": 500_000_000},
            },
            dynamic_sections=["기술이해도"],
        )

        result = plan_merge(state)

        assert "plan" in result
        assert isinstance(result["plan"], ProposalPlan)
        assert result["rework_targets"] == []

    def test_plan_merge_rework_preserves_existing(self):
        """부분 재작업 시 기존 plan의 다른 필드를 보존."""
        from app.graph.nodes.merge_nodes import plan_merge

        existing_plan = _plan_obj()
        state = _base_state(
            plan=existing_plan,
            rework_targets=["plan_team"],
            parallel_results={"team": [{"role": "PM-new", "grade": "고급", "mm": 5}]},
            dynamic_sections=["기술이해도"],
        )

        result = plan_merge(state)

        # 기존 schedule은 보존
        assert result["plan"].schedule == existing_plan.schedule
        # team은 업데이트
        assert result["plan"].team[0]["role"] == "PM-new"


# ══════════════════════════════════════════════════════════
# STEP 4: proposal_write_next
# ══════════════════════════════════════════════════════════


class TestProposalWriteNext:
    """제안서 섹션 순차 작성 노드 테스트."""

    @pytest.mark.asyncio
    async def test_write_first_section(self):
        """첫 번째 섹션 작성 → proposal_sections에 추가."""
        from app.graph.nodes.proposal_nodes import proposal_write_next
        from app.graph.state import ProposalSection

        state = _base_state(
            rfp_analysis=_rfp_analysis_obj(),
            strategy=_strategy_obj(),
            plan=_plan_obj(),
            research_brief=load_fixture("research_gather.json"),
            dynamic_sections=["기술이해도", "수행방안", "프로젝트관리"],
            current_section_index=0,
            parallel_results={"_section_type_map": {"기술이해도": "UNDERSTAND"}},
        )

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)
            result = await proposal_write_next(state)

        assert "proposal_sections" in result
        assert len(result["proposal_sections"]) == 1
        assert isinstance(result["proposal_sections"][0], ProposalSection)
        assert result["current_step"] == "section_written"

    @pytest.mark.asyncio
    async def test_write_out_of_range_index(self):
        """index가 섹션 수를 초과하면 sections_complete."""
        from app.graph.nodes.proposal_nodes import proposal_write_next

        state = _base_state(
            rfp_analysis=_rfp_analysis_obj(),
            dynamic_sections=["기술이해도"],
            current_section_index=5,  # 초과
        )

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)
            result = await proposal_write_next(state)

        assert result["current_step"] == "sections_complete"


# ══════════════════════════════════════════════════════════
# STEP 4: self_review_with_auto_improve
# ══════════════════════════════════════════════════════════


class TestSelfReview:
    """AI 자가진단 노드 테스트."""

    @pytest.mark.asyncio
    async def test_self_review_pass(self):
        """80점 이상이면 pass."""
        from app.graph.nodes.proposal_nodes import self_review_with_auto_improve
        from app.graph.state import ProposalSection

        sections = [ProposalSection(
            section_id="기술이해도",
            title="기술 이해도",
            content="클라우드 기반 ERP 시스템에 대한 깊은 이해...",
            version=1,
            case_type="A",
        )]

        state = _base_state(
            rfp_analysis=_rfp_analysis_obj(),
            strategy=_strategy_obj(),
            proposal_sections=sections,
            compliance_matrix=[],
        )

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)
            result = await self_review_with_auto_improve(state)

        # self_review_pass.json fixture 기준으로 80점 이상
        assert result.get("current_step") in (
            "self_review_pass",
            "self_review_retry_sections",
            "self_review_retry_research",
            "self_review_retry_strategy",
            "self_review_force_review",
        )

    @pytest.mark.asyncio
    async def test_self_review_no_sections(self):
        """섹션이 없으면 바로 pass."""
        from app.graph.nodes.proposal_nodes import self_review_with_auto_improve

        state = _base_state(proposal_sections=[])

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)
            result = await self_review_with_auto_improve(state)

        assert result["current_step"] == "self_review_pass"


# ══════════════════════════════════════════════════════════
# STEP 5-0: presentation_strategy
# ══════════════════════════════════════════════════════════


class TestPresentationStrategy:
    """발표전략 노드 테스트."""

    @pytest.mark.asyncio
    async def test_presentation_strategy_normal(self):
        """종합심사 → 발표전략 수립."""
        from app.graph.nodes.ppt_nodes import presentation_strategy

        state = _base_state(
            rfp_analysis=_rfp_analysis_obj(),
            strategy=_strategy_obj(),
            proposal_sections=[],
        )

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)
            result = await presentation_strategy(state)

        assert "presentation_strategy" in result
        assert result["current_step"] == "presentation_strategy_complete"

    @pytest.mark.asyncio
    async def test_presentation_strategy_document_only(self):
        """서류심사 → 건너뛰기."""
        from app.graph.nodes.ppt_nodes import presentation_strategy
        from app.graph.state import RFPAnalysis

        rfp = _rfp_analysis_obj()
        # eval_method를 서류심사로 변경
        rfp_dict = rfp.model_dump()
        rfp_dict["eval_method"] = "서류심사(document_only)"
        rfp_doc_only = RFPAnalysis(**rfp_dict)

        state = _base_state(rfp_analysis=rfp_doc_only)

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)
            result = await presentation_strategy(state)

        assert result["presentation_strategy"]["skipped"] is True
        assert result["current_step"] == "presentation_strategy_document_only"


# ══════════════════════════════════════════════════════════
# STEP 5: PPT 3단계 파이프라인
# ══════════════════════════════════════════════════════════


class TestPPTPipeline:
    """PPT TOC → Visual Brief → Storyboard 테스트."""

    def _ppt_state(self, **extra):
        return _base_state(
            rfp_analysis=_rfp_analysis_obj(),
            strategy=_strategy_obj(),
            plan=_plan_obj(),
            proposal_sections=[],
            presentation_strategy=load_fixture("presentation_strategy.json"),
            **extra,
        )

    @pytest.mark.asyncio
    async def test_ppt_toc(self):
        from app.graph.nodes.ppt_nodes import ppt_toc

        state = self._ppt_state()

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)
            result = await ppt_toc(state)

        assert "ppt_storyboard" in result
        assert "toc" in result["ppt_storyboard"]
        assert result["current_step"] == "ppt_toc_complete"

    @pytest.mark.asyncio
    async def test_ppt_visual_brief(self):
        from app.graph.nodes.ppt_nodes import ppt_visual_brief

        ppt_fix = load_fixture("ppt_slide.json")
        state = self._ppt_state(
            ppt_storyboard={"toc": ppt_fix["toc"], "total_slides": ppt_fix["total_slides"]},
        )

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)
            result = await ppt_visual_brief(state)

        assert "visual_briefs" in result["ppt_storyboard"]
        assert result["current_step"] == "ppt_visual_brief_complete"

    @pytest.mark.asyncio
    async def test_ppt_storyboard(self):
        from app.graph.nodes.ppt_nodes import ppt_storyboard_node

        ppt_fix = load_fixture("ppt_slide.json")
        state = self._ppt_state(
            ppt_storyboard={
                "toc": ppt_fix["toc"],
                "visual_briefs": ppt_fix["visual_briefs"],
                "total_slides": ppt_fix["total_slides"],
            },
        )

        with ExitStack() as stack:
            for p in _mock_patches():
                stack.enter_context(p)
            result = await ppt_storyboard_node(state)

        assert "slides" in result["ppt_storyboard"]
        assert "ppt_slides" in result
        assert result["current_step"] == "ppt_storyboard_complete"


# ══════════════════════════════════════════════════════════
# 라우팅 함수 (edges)
# ══════════════════════════════════════════════════════════


class TestEdges:
    """Conditional edge 라우팅 함수 테스트."""

    def test_route_after_rfp_review_approved(self):
        from app.graph.edges import route_after_rfp_review
        from app.graph.state import ApprovalStatus

        state = _base_state(approval={"rfp": ApprovalStatus(status="approved")})
        assert route_after_rfp_review(state) == "approved"

    def test_route_after_rfp_review_rejected(self):
        from app.graph.edges import route_after_rfp_review
        from app.graph.state import ApprovalStatus

        state = _base_state(approval={"rfp": ApprovalStatus(status="rejected")})
        assert route_after_rfp_review(state) == "rejected"

    def test_route_after_gng_review_go(self):
        from app.graph.edges import route_after_gng_review
        state = _base_state(current_step="go_no_go_go")
        assert route_after_gng_review(state) == "go"

    def test_route_after_gng_review_no_go(self):
        from app.graph.edges import route_after_gng_review
        state = _base_state(current_step="go_no_go_no_go")
        assert route_after_gng_review(state) == "no_go"

    def test_route_after_strategy_review_approved(self):
        from app.graph.edges import route_after_strategy_review
        from app.graph.state import ApprovalStatus

        state = _base_state(
            current_step="strategy_approved",
            approval={"strategy": ApprovalStatus(status="approved")},
        )
        assert route_after_strategy_review(state) == "approved"

    def test_route_after_strategy_review_positioning_changed(self):
        from app.graph.edges import route_after_strategy_review
        state = _base_state(current_step="strategy_positioning_changed")
        assert route_after_strategy_review(state) == "positioning_changed"

    def test_route_after_bid_plan_review_approved(self):
        from app.graph.edges import route_after_bid_plan_review
        from app.graph.state import ApprovalStatus

        state = _base_state(approval={"bid_plan": ApprovalStatus(status="approved")})
        assert route_after_bid_plan_review(state) == "approved"

    def test_route_after_bid_plan_review_back_to_strategy(self):
        from app.graph.edges import route_after_bid_plan_review

        state = _base_state(
            approval={},
            feedback_history=[{"step": "bid_plan", "back_to_strategy": True}],
        )
        assert route_after_bid_plan_review(state) == "back_to_strategy"

    def test_route_after_plan_review_rework_with_strategy(self):
        from app.graph.edges import route_after_plan_review

        state = _base_state(
            approval={},
            feedback_history=[{"step": "plan", "rework_targets": ["strategy_generate"]}],
        )
        assert route_after_plan_review(state) == "rework_with_strategy"

    def test_route_after_plan_review_rework_bid_plan(self):
        from app.graph.edges import route_after_plan_review

        state = _base_state(
            approval={},
            feedback_history=[{"step": "plan", "rework_targets": ["bid_plan"]}],
        )
        assert route_after_plan_review(state) == "rework_bid_plan"

    def test_route_after_self_review_pass(self):
        from app.graph.edges import route_after_self_review
        state = _base_state(current_step="self_review_pass")
        assert route_after_self_review(state) == "pass"

    def test_route_after_self_review_retry_research(self):
        from app.graph.edges import route_after_self_review
        state = _base_state(current_step="self_review_retry_research")
        assert route_after_self_review(state) == "retry_research"

    def test_route_after_self_review_force_review(self):
        from app.graph.edges import route_after_self_review
        state = _base_state(current_step="self_review_force_review")
        assert route_after_self_review(state) == "force_review"

    def test_route_after_section_review_all_done(self):
        from app.graph.edges import route_after_section_review
        state = _base_state(current_step="sections_complete")
        assert route_after_section_review(state) == "all_done"

    def test_route_after_section_review_next(self):
        from app.graph.edges import route_after_section_review
        state = _base_state(current_step="section_approved")
        assert route_after_section_review(state) == "next_section"

    def test_route_after_section_review_rewrite(self):
        from app.graph.edges import route_after_section_review
        state = _base_state(current_step="section_rejected")
        assert route_after_section_review(state) == "rewrite"

    def test_route_after_proposal_review_approved(self):
        from app.graph.edges import route_after_proposal_review
        from app.graph.state import ApprovalStatus

        state = _base_state(approval={"proposal": ApprovalStatus(status="approved")})
        assert route_after_proposal_review(state) == "approved"

    def test_route_after_presentation_strategy_proceed(self):
        from app.graph.edges import route_after_presentation_strategy
        state = _base_state(rfp_analysis=_rfp_analysis_obj())
        assert route_after_presentation_strategy(state) == "proceed"

    def test_route_after_presentation_strategy_document_only(self):
        from app.graph.edges import route_after_presentation_strategy
        from app.graph.state import RFPAnalysis

        rfp_dict = _rfp_analysis_obj().model_dump()
        rfp_dict["eval_method"] = "document_only 서류심사"
        rfp = RFPAnalysis(**rfp_dict)

        state = _base_state(rfp_analysis=rfp)
        assert route_after_presentation_strategy(state) == "document_only"

    def test_route_after_ppt_review_approved(self):
        from app.graph.edges import route_after_ppt_review
        from app.graph.state import ApprovalStatus

        state = _base_state(approval={"ppt": ApprovalStatus(status="approved")})
        assert route_after_ppt_review(state) == "approved"

    def test_route_after_ppt_review_rework(self):
        from app.graph.edges import route_after_ppt_review
        state = _base_state(approval={})
        assert route_after_ppt_review(state) == "rework"


# ══════════════════════════════════════════════════════════
# 그래프 헬퍼: _proposal_start_gate, _passthrough
# ══════════════════════════════════════════════════════════


class TestGraphHelpers:
    """그래프 내부 헬퍼 함수 테스트."""

    def test_proposal_start_gate(self):
        from app.graph.nodes.gate_nodes import proposal_start_gate
        result = proposal_start_gate(_base_state())
        assert result == {"current_section_index": 0}

    def test_passthrough(self):
        from app.graph.nodes.gate_nodes import passthrough
        result = passthrough(_base_state())
        assert result == {}

    def test_plan_selective_fan_out_all(self):
        """rework_targets가 비면 5개 전체 fan-out (plan_team/assign/schedule/story/price)."""
        from app.graph.nodes.gate_nodes import plan_selective_fan_out

        state = _base_state(rework_targets=[])
        sends = plan_selective_fan_out(state)
        assert len(sends) == 5

    def test_plan_selective_fan_out_partial(self):
        """rework_targets가 있으면 해당 항목만 fan-out (plan_assign은 targets에 없으므로 제외)."""
        from app.graph.nodes.gate_nodes import plan_selective_fan_out

        state = _base_state(rework_targets=["plan_team", "plan_assign"])
        sends = plan_selective_fan_out(state)
        assert len(sends) == 2
        node_names = [s.node for s in sends]
        assert "plan_team" in node_names
        assert "plan_assign" in node_names
        assert "plan_schedule" not in node_names
