"""edges.py 라우팅 함수 유닛 테스트.

순수 함수 테스트 — mock/IO 없이 state dict만 전달하고 반환값 검증.
"""
from unittest.mock import MagicMock

from app.graph.edges import (
    route_after_bid_plan_review,
    route_after_gng_review,
    route_after_plan_review,
    route_after_ppt_review,
    route_after_presentation_strategy,
    route_after_proposal_review,
    route_after_rfp_review,
    route_after_section_review,
    route_after_self_review,
    route_after_strategy_review,
)


# ── route_after_rfp_review ──

class TestRouteAfterRfpReview:
    def test_approved(self):
        approval = MagicMock(status="approved")
        state = {"approval": {"rfp": approval}}
        assert route_after_rfp_review(state) == "approved"

    def test_rejected(self):
        approval = MagicMock(status="rejected")
        state = {"approval": {"rfp": approval}}
        assert route_after_rfp_review(state) == "rejected"

    def test_no_approval(self):
        state = {"approval": {}}
        assert route_after_rfp_review(state) == "rejected"

    def test_empty_state(self):
        assert route_after_rfp_review({}) == "rejected"


# ── route_after_gng_review ──

class TestRouteAfterGngReview:
    def test_go(self):
        state = {"current_step": "go_no_go_go"}
        assert route_after_gng_review(state) == "go"

    def test_no_go(self):
        state = {"current_step": "go_no_go_no_go"}
        assert route_after_gng_review(state) == "no_go"

    def test_rejected(self):
        state = {"current_step": "go_no_go_rejected"}
        assert route_after_gng_review(state) == "rejected"

    def test_empty_step(self):
        state = {"current_step": ""}
        assert route_after_gng_review(state) == "rejected"


# ── route_after_strategy_review ──

class TestRouteAfterStrategyReview:
    def test_approved(self):
        approval = MagicMock(status="approved")
        state = {"approval": {"strategy": approval}, "current_step": ""}
        assert route_after_strategy_review(state) == "approved"

    def test_positioning_changed(self):
        state = {"current_step": "strategy_positioning_changed", "approval": {}}
        assert route_after_strategy_review(state) == "positioning_changed"

    def test_rejected(self):
        approval = MagicMock(status="rejected")
        state = {"approval": {"strategy": approval}, "current_step": ""}
        assert route_after_strategy_review(state) == "rejected"


# ── route_after_bid_plan_review ──

class TestRouteAfterBidPlanReview:
    def test_approved(self):
        approval = MagicMock(status="approved")
        state = {"approval": {"bid_plan": approval}, "feedback_history": []}
        assert route_after_bid_plan_review(state) == "approved"

    def test_back_to_strategy(self):
        state = {
            "approval": {"bid_plan": MagicMock(status="rejected")},
            "feedback_history": [{"step": "bid_plan", "back_to_strategy": True}],
        }
        assert route_after_bid_plan_review(state) == "back_to_strategy"

    def test_rejected(self):
        state = {
            "approval": {"bid_plan": MagicMock(status="rejected")},
            "feedback_history": [{"step": "bid_plan", "back_to_strategy": False}],
        }
        assert route_after_bid_plan_review(state) == "rejected"

    def test_no_approval(self):
        state = {"approval": {}, "feedback_history": []}
        assert route_after_bid_plan_review(state) == "rejected"


# ── route_after_plan_review ──

class TestRouteAfterPlanReview:
    def test_approved(self):
        approval = MagicMock(status="approved")
        state = {"approval": {"plan": approval}, "feedback_history": []}
        assert route_after_plan_review(state) == "approved"

    def test_rework_with_strategy(self):
        state = {
            "approval": {"plan": MagicMock(status="rejected")},
            "feedback_history": [{"rework_targets": ["strategy_generate"]}],
        }
        assert route_after_plan_review(state) == "rework_with_strategy"

    def test_rework_bid_plan(self):
        state = {
            "approval": {"plan": MagicMock(status="rejected")},
            "feedback_history": [{"rework_targets": ["bid_plan"]}],
        }
        assert route_after_plan_review(state) == "rework_bid_plan"

    def test_rework_default(self):
        state = {
            "approval": {"plan": MagicMock(status="rejected")},
            "feedback_history": [{"rework_targets": []}],
        }
        assert route_after_plan_review(state) == "rework"

    def test_no_feedback(self):
        state = {"approval": {}, "feedback_history": []}
        assert route_after_plan_review(state) == "rework"


# ── route_after_self_review ──

class TestRouteAfterSelfReview:
    def test_pass(self):
        state = {"current_step": "self_review_pass"}
        assert route_after_self_review(state) == "pass"

    def test_retry_research(self):
        state = {"current_step": "self_review_retry_research"}
        assert route_after_self_review(state) == "retry_research"

    def test_retry_strategy(self):
        state = {"current_step": "self_review_retry_strategy"}
        assert route_after_self_review(state) == "retry_strategy"

    def test_force_review(self):
        state = {"current_step": "self_review_force_review"}
        assert route_after_self_review(state) == "force_review"

    def test_retry_sections_default(self):
        state = {"current_step": "self_review_retry_sections"}
        assert route_after_self_review(state) == "retry_sections"

    def test_unknown_defaults_to_retry_sections(self):
        state = {"current_step": "something_else"}
        assert route_after_self_review(state) == "retry_sections"


# ── route_after_section_review ──

class TestRouteAfterSectionReview:
    def test_all_done(self):
        state = {"current_step": "sections_complete"}
        assert route_after_section_review(state) == "all_done"

    def test_next_section(self):
        state = {"current_step": "section_approved"}
        assert route_after_section_review(state) == "next_section"

    def test_rewrite(self):
        state = {"current_step": "section_rejected"}
        assert route_after_section_review(state) == "rewrite"


# ── route_after_proposal_review ──

class TestRouteAfterProposalReview:
    def test_approved(self):
        approval = MagicMock(status="approved")
        state = {"approval": {"proposal": approval}}
        assert route_after_proposal_review(state) == "approved"

    def test_rework(self):
        approval = MagicMock(status="rejected")
        state = {"approval": {"proposal": approval}}
        assert route_after_proposal_review(state) == "rework"


# ── route_after_presentation_strategy ──

class TestRouteAfterPresentationStrategy:
    def test_proceed_with_ppt(self):
        rfp = MagicMock()
        rfp.eval_method = "기술+발표심사"
        state = {"rfp_analysis": rfp}
        assert route_after_presentation_strategy(state) == "proceed"

    def test_document_only_skip_ppt(self):
        rfp = MagicMock()
        rfp.eval_method = "document_only"
        state = {"rfp_analysis": rfp}
        assert route_after_presentation_strategy(state) == "document_only"

    def test_document_only_dict(self):
        state = {"rfp_analysis": {"eval_method": "document_only"}}
        assert route_after_presentation_strategy(state) == "document_only"

    def test_no_rfp_analysis(self):
        state = {"rfp_analysis": None}
        assert route_after_presentation_strategy(state) == "proceed"


# ── route_after_ppt_review ──

class TestRouteAfterPptReview:
    def test_approved(self):
        approval = MagicMock(status="approved")
        state = {"approval": {"ppt": approval}}
        assert route_after_ppt_review(state) == "approved"

    def test_rework(self):
        approval = MagicMock(status="rejected")
        state = {"approval": {"ppt": approval}}
        assert route_after_ppt_review(state) == "rework"
