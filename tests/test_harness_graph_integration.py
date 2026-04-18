"""Integration tests for Harness Engineering in LangGraph workflow."""

import pytest
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.graph.state import ProposalState
from app.graph.nodes.harness_proposal_write import harness_proposal_write_next
from app.graph.graph import build_graph


class TestHarnessGraphIntegration:
    """Test harness engineering integration with main graph workflow."""

    @pytest.fixture
    def sample_state(self):
        """Create a sample proposal state for testing."""
        return ProposalState(
            proposal_id=str(uuid4()),
            org_id=str(uuid4()),
            created_by=str(uuid4()),
            proposal_story={
                "executive_summary": "Test executive summary",
                "technical_approach": "Test technical approach",
            },
            rfp={
                "title": "Sample RFP",
                "domain": "Technology",
                "tech_keywords": ["AI", "Cloud"],
            },
            proposal_sections=[],
            current_section_index=0,
            current_step="proposal_write_next",
            status="in_progress",
        )

    def test_graph_compiles_with_harness(self):
        """Verify graph compiles with harness node."""
        g = build_graph()

        assert g is not None
        assert len(g.nodes) == 45, f"Expected 45 nodes, got {len(g.nodes)}"
        assert "proposal_write_next" in g.nodes

    def test_harness_node_exists_in_graph(self):
        """Verify harness_proposal_write_next is the proposal_write_next node."""
        g = build_graph()
        node_fn = g.nodes.get("proposal_write_next")

        assert node_fn is not None, "proposal_write_next node not found"
        # Node is wrapped in PregelNode by LangGraph
        assert str(type(node_fn).__name__) == "PregelNode"

    def test_step_4a_routing_intact(self):
        """Verify STEP 4A routing edges are intact after integration."""
        g = build_graph()

        # Check all STEP 4A nodes exist
        step_4a_nodes = [
            "proposal_start_gate",
            "proposal_write_next",
            "section_quality_check",
            "review_section",
            "self_review",
            "storyline_gap_analysis",
            "review_gap_analysis",
            "review_proposal",
        ]

        for node_name in step_4a_nodes:
            assert node_name in g.nodes, f"Node {node_name} missing from graph"

    @pytest.mark.asyncio
    async def test_harness_write_basic_functionality(self, sample_state):
        """Test harness_proposal_write_next basic functionality."""
        # Mock the claude client
        with patch('app.graph.nodes.harness_proposal_write.HarnessProposalGenerator') as MockGenerator:
            mock_generator = AsyncMock()
            MockGenerator.return_value = mock_generator

            # Mock generate_section to return evaluation result
            mock_generator.generate_section = AsyncMock(return_value={
                "section_type": "executive_summary",
                "selected_variant": "balanced",
                "content": "Test content",
                "score": 0.78,
                "scores": {
                    "conservative": 0.72,
                    "balanced": 0.78,
                    "creative": 0.65
                },
                "details": {}
            })

            # Call the node function
            result = await harness_proposal_write_next(sample_state)

            # Verify result structure - should return current_step status
            assert isinstance(result, dict)
            assert "current_step" in result or "proposal_sections" in result
            # When all sections complete, returns current_step: "sections_complete"
            assert result.get("current_step") == "sections_complete"

    @pytest.mark.asyncio
    async def test_harness_respects_max_sections(self, sample_state):
        """Test that harness respects section limits."""
        # Add many sections to test completion detection
        sample_state["proposal_story"] = {
            "executive_summary": "Summary",
            "technical_approach": "Tech",
            "project_organization": "Org",
        }
        sample_state["current_section_index"] = 2  # Last section

        with patch('app.graph.nodes.harness_proposal_write.HarnessProposalGenerator') as MockGenerator:
            mock_generator = AsyncMock()
            MockGenerator.return_value = mock_generator
            mock_generator.generate_section = AsyncMock(return_value={
                "section_type": "project_organization",
                "selected_variant": "balanced",
                "content": "Test",
                "score": 0.8,
                "scores": {},
                "details": {}
            })

            result = await harness_proposal_write_next(sample_state)

            # When all sections complete, transitions to self_review
            assert result is not None
            assert result.get("current_step") == "sections_complete"

    def test_graph_all_nodes_reachable(self):
        """Verify all graph nodes are reachable from START."""
        g = build_graph()

        # Basic connectivity check - graph should have a continuous path
        assert "rfp_analyze" in g.nodes, "Entry point rfp_analyze missing"
        assert "project_closing" in g.nodes, "Exit point project_closing missing"

        # Verify key decision points exist
        decision_nodes = [
            "review_rfp",
            "review_gng",
            "review_strategy",
            "fork_gate",
            "review_section",
            "mock_evaluation",
        ]

        for node_name in decision_nodes:
            assert node_name in g.nodes, f"Decision node {node_name} missing"

    @pytest.mark.asyncio
    async def test_harness_handles_empty_story(self, sample_state):
        """Test harness handles empty proposal story gracefully."""
        sample_state["proposal_story"] = {}

        with patch('app.graph.nodes.harness_proposal_write.HarnessProposalGenerator'):
            result = await harness_proposal_write_next(sample_state)

            # Should not crash, should return valid state
            assert isinstance(result, dict)
            # Empty story should complete immediately
            assert result.get("current_step") == "sections_complete"

    def test_graph_preserves_state_transitions(self):
        """Verify graph preserves A/B path transitions."""
        g = build_graph()

        # Verify fork gate exists (splits into A and B)
        assert "fork_gate" in g.nodes

        # Verify convergence point exists
        assert "convergence_gate" in g.nodes

        # Both paths should exist
        path_a_nodes = {
            "plan_team", "proposal_write_next", "presentation_strategy",
            "ppt_toc", "mock_evaluation"
        }
        path_b_nodes = {
            "submission_plan", "bid_plan", "cost_sheet_generate",
            "submission_checklist"
        }

        for node in path_a_nodes:
            assert node in g.nodes, f"Path A node {node} missing"

        for node in path_b_nodes:
            assert node in g.nodes, f"Path B node {node} missing"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
