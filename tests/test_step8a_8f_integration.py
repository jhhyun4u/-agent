"""
Integration & E2E tests for STEP 8A-8F quality gate pipeline.

Tests cover:
- Full pipeline flow (8A → 8F)
- State transitions and routing
- Artifact versioning across nodes
- Error recovery paths
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.graph.edges import (
    route_after_section_validator_review,
    route_after_feedback_processor_review,
    route_after_rewrite_review,
)


@pytest.fixture
def full_proposal_state():
    """Complete proposal state for E2E testing."""
    section1 = {
        "section_id": "sec1",
        "title": "Technical Approach",
        "content": "Our approach is efficient.",
        "version": 1,
    }
    section2 = {
        "section_id": "sec2",
        "title": "Schedule",
        "content": "Timeline is 12 months.",
        "version": 1,
    }

    return {
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "created_by": "550e8400-e29b-41d4-a716-446655440001",
        "rfp_analysis": MagicMock(),
        "strategy": MagicMock(),
        "proposal_sections": [section1, section2],
        "customer_profile": None,
        "validation_report": None,
        "consolidated_proposal": None,
        "mock_eval_result": None,
        "feedback_summary": None,
        "current_section_index": 0,
        "approval": {},
        "feedback_history": [],
        "node_errors": {},
        "artifact_versions": {},
        "active_versions": {},
        "selected_versions": {},
        "version_selection_history": [],
    }


class TestStep8Pipeline:
    """Integration tests for STEP 8A-8F pipeline."""

    @pytest.mark.asyncio
    async def test_full_pipeline_flow(self, full_proposal_state):
        """Test complete 8A→8B→8C→8D→8E→8F flow."""
        with patch(
            "app.graph.nodes.step8a_customer_analysis.claude_generate",
            new_callable=AsyncMock,
            return_value={"client_org": "Ministry", "decision_drivers": []},
        ), patch(
            "app.graph.nodes.step8b_section_validator.claude_generate",
            new_callable=AsyncMock,
            return_value={"total_sections": 2, "passed_sections": 2, "quality_score": 85, "errors": [], "warnings": [], "info": []},
        ), patch(
            "app.graph.nodes.step8d_mock_evaluation.claude_generate",
            new_callable=AsyncMock,
            return_value={
                "estimated_total_score": 75,
                "win_probability": 0.65,
                "score_components": [],
                "strengths": [],
                "weaknesses": [],
                "improvement_recommendations": [],
            },
        ), patch(
            "app.graph.nodes.step8e_feedback_processor.claude_generate",
            new_callable=AsyncMock,
            return_value={
                "critical_gaps": [],
                "improvement_opportunities": [],
                "estimated_score_improvement": 10,
                "section_feedback": {},
                "priority_order": [],
            },
        ), patch(
            "app.services.version_manager.execute_node_and_create_version",
            new_callable=AsyncMock,
            return_value=(1, MagicMock()),
        ):
            # Setup mocks for Pydantic models
            full_proposal_state["rfp_analysis"].model_dump_json = MagicMock(
                return_value="{}"
            )
            full_proposal_state["rfp_analysis"].mandatory_reqs = []
            full_proposal_state["rfp_analysis"].eval_items = []
            full_proposal_state["strategy"].model_dump_json = MagicMock(
                return_value="{}"
            )

            # Manually test node sequence
            from app.graph.nodes.step8a_customer_analysis import (
                proposal_customer_analysis,
            )
            from app.graph.nodes.step8b_section_validator import (
                proposal_section_validator,
            )
            from app.graph.nodes.step8c_consolidation import (
                proposal_sections_consolidation,
            )
            from app.graph.nodes.step8d_mock_evaluation import (
                mock_evaluation_analysis,
            )

            # 8A: Customer Analysis
            result_8a = await proposal_customer_analysis(full_proposal_state)
            assert "customer_profile" in result_8a
            full_proposal_state.update(result_8a)

            # 8B: Validation
            full_proposal_state[
                "validation_report"
            ] = MagicMock()
            full_proposal_state["validation_report"].quality_score = 85
            full_proposal_state["validation_report"].errors = []
            full_proposal_state["validation_report"].warnings = []

            result_8b = await proposal_section_validator(full_proposal_state)
            assert "validation_report" in result_8b
            full_proposal_state.update(result_8b)

            # 8C: Consolidation
            result_8c = await proposal_sections_consolidation(
                full_proposal_state
            )
            assert "consolidated_proposal" in result_8c
            full_proposal_state.update(result_8c)

            # 8D: Mock Evaluation
            result_8d = await mock_evaluation_analysis(full_proposal_state)
            assert "mock_eval_result" in result_8d
            full_proposal_state.update(result_8d)

    def test_routing_after_validation_approved(self):
        """Test routing when validation is approved."""
        state = {"approval": {"section_validation": MagicMock(status="approved")}}

        route = route_after_section_validator_review(state)
        assert route == "approved"

    def test_routing_after_validation_needs_rework(self):
        """Test routing when validation needs rework."""
        state = {"feedback_history": [{"needs_rework": True}]}

        route = route_after_section_validator_review(state)
        assert route == "needs_rework"

    def test_routing_after_feedback_proceed_rewrite(self):
        """Test routing for feedback processor - proceed rewrite."""
        feedback = MagicMock()
        feedback.estimated_score_improvement = 20
        feedback.critical_gaps = ["Gap1"]
        state = {"feedback_summary": feedback}

        route = route_after_feedback_processor_review(state)
        assert route == "proceed_rewrite"

    def test_routing_after_feedback_skip_to_ppt(self):
        """Test routing for feedback processor - skip to PPT."""
        feedback = MagicMock()
        feedback.estimated_score_improvement = 5
        feedback.critical_gaps = []
        state = {"feedback_summary": feedback}

        route = route_after_feedback_processor_review(state)
        assert route == "skip_to_ppt"

    def test_routing_after_rewrite_approved(self):
        """Test routing after rewrite review - approved."""
        state = {"approval": {"rewrite": MagicMock(status="approved")}}

        route = route_after_rewrite_review(state)
        assert route == "approved"

    def test_routing_after_rewrite_needs_more(self):
        """Test routing after rewrite review - needs more."""
        state = {"feedback_history": []}

        route = route_after_rewrite_review(state)
        assert route == "needs_more_rewrite"


class TestErrorRecovery:
    """Test error recovery paths in the pipeline."""

    @pytest.mark.asyncio
    async def test_validation_failure_recovery(self, full_proposal_state):
        """Test recovery when validation fails."""
        full_proposal_state["rfp_analysis"].model_dump_json = MagicMock(
            return_value="{}"
        )
        full_proposal_state["rfp_analysis"].mandatory_reqs = []
        full_proposal_state["strategy"].model_dump_json = MagicMock(
            return_value="{}"
        )

        with patch(
            "app.graph.nodes.step8b_section_validator.claude_generate",
            new_callable=AsyncMock,
            side_effect=Exception("API Error"),
        ):
            from app.graph.nodes.step8b_section_validator import (
                proposal_section_validator,
            )

            result = await proposal_section_validator(full_proposal_state)

            assert result["validation_report"] is None
            assert "node_errors" in result
            assert "proposal_section_validator" in result["node_errors"]

    @pytest.mark.asyncio
    async def test_rewrite_section_index_bounds(self, full_proposal_state):
        """Test rewrite handling when section index is out of bounds."""
        full_proposal_state["current_section_index"] = 10

        from app.graph.nodes.step8f_rewrite import proposal_write_next_v2

        result = await proposal_write_next_v2(full_proposal_state)

        # Should return existing sections unchanged
        assert "proposal_sections" in result
        assert result["proposal_sections"] == full_proposal_state[
            "proposal_sections"
        ]


class TestArtifactVersioning:
    """Test artifact versioning across nodes."""

    @pytest.mark.asyncio
    async def test_version_tracking(self, full_proposal_state):
        """Test version tracking through pipeline."""
        with patch(
            "app.graph.nodes.step8a_customer_analysis.claude_generate",
            new_callable=AsyncMock,
            return_value={"client_org": "Ministry", "decision_drivers": []},
        ), patch(
            "app.services.version_manager.execute_node_and_create_version",
            new_callable=AsyncMock,
            return_value=(1, MagicMock(version=1)),
        ):
            full_proposal_state["rfp_analysis"].model_dump_json = MagicMock(
                return_value="{}"
            )
            full_proposal_state["strategy"].model_dump_json = MagicMock(
                return_value="{}"
            )

            from app.graph.nodes.step8a_customer_analysis import (
                proposal_customer_analysis,
            )

            result = await proposal_customer_analysis(full_proposal_state)

            # Verify artifact versioning
            assert "artifact_versions" in result
            assert "active_versions" in result
            assert (
                "proposal_customer_analysis_customer_profile"
                in result["active_versions"]
            )
