"""
Unit tests for STEP 8A: proposal_customer_analysis node.

Tests cover:
- Input validation (required fields)
- Claude API integration
- Pydantic model parsing
- Error handling
- Artifact versioning
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.graph.state import CustomerProfile, RFPAnalysis, Strategy
from app.graph.nodes.step8a_customer_analysis import proposal_customer_analysis


@pytest.fixture
def mock_state():
    """Minimal valid proposal state."""
    return {
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "created_by": "550e8400-e29b-41d4-a716-446655440001",
        "rfp_analysis": MagicMock(spec=RFPAnalysis),
        "strategy": MagicMock(spec=Strategy),
        "kb_references": [
            {"title": "Similar Project 1", "summary": "Description"},
        ],
        "competitor_refs": [{"name": "Competitor A"}],
        "node_errors": {},
        "artifact_versions": {},
        "active_versions": {},
    }


@pytest.fixture
def mock_customer_profile_response():
    """Mock Claude API response for customer profile."""
    return {
        "client_org": "Ministry of Health",
        "decision_drivers": ["Cost efficiency", "Compliance"],
        "budget_authority": "CFO approval required",
        "stakeholders": [
            {
                "title": "Project Director",
                "influence": "high",
                "concerns": ["Timeline", "Quality"],
            }
        ],
        "decision_timeline": "90 days",
        "key_constraints": ["Government procurement rules"],
    }


@pytest.mark.asyncio
async def test_customer_analysis_success(
    mock_state, mock_customer_profile_response
):
    """Test successful customer analysis."""
    with patch(
        "app.graph.nodes.step8a_customer_analysis.claude_generate",
        new_callable=AsyncMock,
    ) as mock_claude, patch(
        "app.graph.nodes.step8a_customer_analysis.execute_node_and_create_version",
        new_callable=AsyncMock,
    ) as mock_version:
        # Setup mocks
        mock_claude.return_value = mock_customer_profile_response
        mock_version.return_value = (1, MagicMock())

        mock_state["rfp_analysis"].model_dump_json = MagicMock(
            return_value='{"test": "data"}'
        )
        mock_state["strategy"].model_dump_json = MagicMock(
            return_value='{"strategy": "data"}'
        )

        # Execute
        result = await proposal_customer_analysis(mock_state)

        # Assertions
        assert "customer_profile" in result
        assert isinstance(result["customer_profile"], CustomerProfile)
        assert result["customer_profile"].client_org == "Ministry of Health"
        assert "artifact_versions" in result
        assert "active_versions" in result
        mock_claude.assert_called_once()
        mock_version.assert_called_once()


@pytest.mark.asyncio
async def test_customer_analysis_missing_rfp(mock_state):
    """Test error handling when RFP analysis is missing."""
    mock_state["rfp_analysis"] = None

    result = await proposal_customer_analysis(mock_state)

    assert result["customer_profile"] is None
    assert "node_errors" in result
    assert "proposal_customer_analysis" in result["node_errors"]


@pytest.mark.asyncio
async def test_customer_analysis_claude_error(mock_state):
    """Test error handling for Claude API failure."""
    with patch(
        "app.graph.nodes.step8a_customer_analysis.claude_generate",
        new_callable=AsyncMock,
        side_effect=Exception("API Error"),
    ):
        mock_state["rfp_analysis"].model_dump_json = MagicMock(
            return_value="{}"
        )
        mock_state["strategy"].model_dump_json = MagicMock(
            return_value="{}"
        )

        result = await proposal_customer_analysis(mock_state)

        assert result["customer_profile"] is None
        assert "node_errors" in result
        assert "API Error" in result["node_errors"]["proposal_customer_analysis"]


@pytest.mark.asyncio
async def test_customer_analysis_artifact_versioning(
    mock_state, mock_customer_profile_response
):
    """Test artifact versioning integration."""
    mock_artifact = MagicMock()
    mock_artifact.version = 1

    with patch(
        "app.graph.nodes.step8a_customer_analysis.claude_generate",
        new_callable=AsyncMock,
        return_value=mock_customer_profile_response,
    ), patch(
        "app.graph.nodes.step8a_customer_analysis.execute_node_and_create_version",
        new_callable=AsyncMock,
        return_value=(1, mock_artifact),
    ):
        mock_state["rfp_analysis"].model_dump_json = MagicMock(
            return_value="{}"
        )
        mock_state["strategy"].model_dump_json = MagicMock(
            return_value="{}"
        )

        result = await proposal_customer_analysis(mock_state)

        # Verify version tracking
        assert result["artifact_versions"]["customer_profile"] == [
            mock_artifact
        ]
        assert (
            result["active_versions"][
                "proposal_customer_analysis_customer_profile"
            ]
            == 1
        )


@pytest.mark.asyncio
async def test_customer_analysis_kb_context(
    mock_state, mock_customer_profile_response
):
    """Test knowledge base context handling."""
    with patch(
        "app.graph.nodes.step8a_customer_analysis.claude_generate",
        new_callable=AsyncMock,
        return_value=mock_customer_profile_response,
    ) as mock_claude, patch(
        "app.graph.nodes.step8a_customer_analysis.execute_node_and_create_version",
        new_callable=AsyncMock,
        return_value=(1, MagicMock()),
    ):
        mock_state["rfp_analysis"].model_dump_json = MagicMock(
            return_value="{}"
        )
        mock_state["strategy"].model_dump_json = MagicMock(
            return_value="{}"
        )

        await proposal_customer_analysis(mock_state)

        # Verify KB context was included in prompt
        call_args = mock_claude.call_args
        prompt = call_args.kwargs["prompt"]
        assert "kb_references" in prompt or "Similar Project" in prompt
