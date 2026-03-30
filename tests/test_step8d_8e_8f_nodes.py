"""
Unit tests for STEP 8D, 8E, 8F nodes.

- 8D: mock_evaluation_analysis
- 8E: mock_evaluation_feedback_processor
- 8F: proposal_write_next_v2 (rewrite)
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

from app.graph.state import (
    ProposalState,
    MockEvalResult,
    FeedbackSummary,
    ProposalSection,
    RFPAnalysis,
    Strategy,
)
from app.graph.nodes.step8d_mock_evaluation import mock_evaluation_analysis
from app.graph.nodes.step8e_feedback_processor import (
    mock_evaluation_feedback_processor,
)
from app.graph.nodes.step8f_rewrite import proposal_write_next_v2


# ── STEP 8D: Mock Evaluation Tests ──


@pytest.fixture
def mock_eval_state():
    """State for mock evaluation."""
    section = MagicMock(spec=ProposalSection)
    section.model_dump.return_value = {
        "section_id": "sec1",
        "title": "Approach",
        "content": "Content here.",
        "version": 1,
    }

    return {
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "created_by": "550e8400-e29b-41d4-a716-446655440001",
        "proposal_sections": [section],
        "rfp_analysis": MagicMock(spec=RFPAnalysis),
        "strategy": MagicMock(spec=Strategy),
        "node_errors": {},
        "artifact_versions": {},
        "active_versions": {},
    }


@pytest.fixture
def mock_eval_response():
    """Mock evaluation response."""
    return {
        "estimated_total_score": 75,
        "win_probability": 0.65,
        "score_components": [
            {"dimension": "Technical", "score": 80, "notes": "Good approach"}
        ],
        "strengths": ["Clear timeline"],
        "weaknesses": ["Budget needs clarification"],
        "improvement_recommendations": ["Enhance cost justification"],
    }


@pytest.mark.asyncio
async def test_mock_evaluation_success(mock_eval_state, mock_eval_response):
    """Test successful mock evaluation."""
    with patch(
        "app.graph.nodes.step8d_mock_evaluation.claude_generate",
        new_callable=AsyncMock,
        return_value=mock_eval_response,
    ), patch(
        "app.graph.nodes.step8d_mock_evaluation.execute_node_and_create_version",
        new_callable=AsyncMock,
        return_value=(1, MagicMock()),
    ):
        mock_eval_state["rfp_analysis"].eval_items = [
            {"name": "Technical", "description": "Tech approach", "points": 40}
        ]
        mock_eval_state["rfp_analysis"].model_dump_json = MagicMock(
            return_value="{}"
        )
        mock_eval_state["strategy"].model_dump_json = MagicMock(
            return_value="{}"
        )

        result = await mock_evaluation_analysis(mock_eval_state)

        assert "mock_eval_result" in result
        assert isinstance(result["mock_eval_result"], MockEvalResult)
        assert result["mock_eval_result"].estimated_total_score == 75


@pytest.mark.asyncio
async def test_mock_evaluation_error(mock_eval_state):
    """Test error handling in mock evaluation."""
    mock_eval_state["proposal_sections"] = []

    result = await mock_evaluation_analysis(mock_eval_state)

    assert result["mock_eval_result"] is None
    assert "node_errors" in result


# ── STEP 8E: Feedback Processing Tests ──


@pytest.fixture
def feedback_state():
    """State for feedback processing."""
    section = MagicMock(spec=ProposalSection)
    section.model_dump.return_value = {
        "section_id": "sec1",
        "title": "Section",
        "content": "Content.",
        "version": 1,
    }

    return {
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "created_by": "550e8400-e29b-41d4-a716-446655440001",
        "proposal_sections": [section],
        "mock_eval_result": MagicMock(),
        "rfp_analysis": MagicMock(spec=RFPAnalysis),
        "node_errors": {},
        "artifact_versions": {},
        "active_versions": {},
    }


@pytest.fixture
def feedback_response():
    """Mock feedback response."""
    return {
        "critical_gaps": ["Gap 1"],
        "improvement_opportunities": ["Opportunity 1"],
        "estimated_score_improvement": 20,
        "section_feedback": {"sec1": [{"issue_description": "Issue", "estimated_effort": "medium"}]},
        "priority_order": ["sec1"],
    }


@pytest.mark.asyncio
async def test_feedback_processing_success(feedback_state, feedback_response):
    """Test successful feedback processing."""
    with patch(
        "app.graph.nodes.step8e_feedback_processor.claude_generate",
        new_callable=AsyncMock,
        return_value=feedback_response,
    ), patch(
        "app.graph.nodes.step8e_feedback_processor.execute_node_and_create_version",
        new_callable=AsyncMock,
        return_value=(1, MagicMock()),
    ):
        feedback_state["mock_eval_result"].model_dump_json = MagicMock(
            return_value="{}"
        )
        feedback_state["rfp_analysis"].model_dump_json = MagicMock(
            return_value="{}"
        )

        result = await mock_evaluation_feedback_processor(feedback_state)

        assert "feedback_summary" in result
        assert isinstance(result["feedback_summary"], FeedbackSummary)


@pytest.mark.asyncio
async def test_feedback_processing_missing_eval(feedback_state):
    """Test error when mock eval is missing."""
    feedback_state["mock_eval_result"] = None

    result = await mock_evaluation_feedback_processor(feedback_state)

    assert result["feedback_summary"] is None
    assert "node_errors" in result


# ── STEP 8F: Rewrite Tests ──


@pytest.fixture
def rewrite_state():
    """State for rewrite node."""
    section1 = {"section_id": "sec1", "title": "Section 1", "content": "Original content 1"}
    section2 = {"section_id": "sec2", "title": "Section 2", "content": "Original content 2"}

    feedback = MagicMock()
    feedback.critical_gaps = []
    feedback.section_feedback = {"sec1": [{"issue_description": "Issue", "estimated_effort": "low"}]}

    return {
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "created_by": "550e8400-e29b-41d4-a716-446655440001",
        "proposal_sections": [section1, section2],
        "feedback_summary": feedback,
        "current_section_index": 0,
        "strategy": MagicMock(spec=Strategy),
        "node_errors": {},
        "artifact_versions": {},
        "active_versions": {},
    }


@pytest.mark.asyncio
async def test_rewrite_success(rewrite_state):
    """Test successful section rewrite."""
    rewrite_state["strategy"].model_dump_json = MagicMock(return_value="{}")

    with patch(
        "app.graph.nodes.step8f_rewrite.claude_generate",
        new_callable=AsyncMock,
        return_value={"text": "Rewritten content"},
    ), patch(
        "app.graph.nodes.step8f_rewrite.execute_node_and_create_version",
        new_callable=AsyncMock,
        return_value=(2, MagicMock()),
    ):
        result = await proposal_write_next_v2(rewrite_state)

        assert "proposal_sections" in result
        assert result["current_section_index"] == 1  # Incremented
        assert len(result["proposal_sections"]) == 2


@pytest.mark.asyncio
async def test_rewrite_section_index_out_of_range(rewrite_state):
    """Test error when section index is invalid."""
    rewrite_state["current_section_index"] = 5

    result = await proposal_write_next_v2(rewrite_state)

    assert "proposal_sections" in result
    assert result["proposal_sections"] == rewrite_state["proposal_sections"]


@pytest.mark.asyncio
async def test_rewrite_error_handling(rewrite_state):
    """Test error handling in rewrite."""
    rewrite_state["strategy"].model_dump_json = MagicMock(return_value="{}")

    with patch(
        "app.graph.nodes.step8f_rewrite.claude_generate",
        new_callable=AsyncMock,
        side_effect=Exception("Rewrite Error"),
    ):
        result = await proposal_write_next_v2(rewrite_state)

        # Should not destroy proposal_sections on error
        assert "proposal_sections" not in result or result["proposal_sections"] is None
        assert "node_errors" in result
        assert "Rewrite Error" in result["node_errors"]["proposal_write_next_v2"]


@pytest.mark.asyncio
async def test_rewrite_feedback_guidance(rewrite_state):
    """Test feedback guidance extraction."""
    rewrite_state["feedback_summary"].section_feedback = {
        "sec1": [
            {"issue_description": "Clarity issue", "estimated_effort": "high"},
            {"issue_description": "Format issue", "estimated_effort": "low"},
        ]
    }
    rewrite_state["strategy"].model_dump_json = MagicMock(return_value="{}")

    with patch(
        "app.graph.nodes.step8f_rewrite.claude_generate",
        new_callable=AsyncMock,
        return_value={"text": "Rewritten"},
    ) as mock_claude, patch(
        "app.graph.nodes.step8f_rewrite.execute_node_and_create_version",
        new_callable=AsyncMock,
        return_value=(2, MagicMock()),
    ):
        await proposal_write_next_v2(rewrite_state)

        # Verify guidance was included
        call_args = mock_claude.call_args
        prompt = call_args.kwargs["prompt"]
        assert "Clarity issue" in prompt or "guidance" in prompt
