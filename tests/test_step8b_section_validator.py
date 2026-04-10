"""
Unit tests for STEP 8B: proposal_section_validator node.

Tests cover:
- Input validation (sections, RFP analysis)
- Section content truncation
- Validation report generation
- Error handling
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.graph.state import (
    ValidationReport,
    ProposalSection,
    RFPAnalysis,
    Strategy,
)
from app.graph.nodes.step8b_section_validator import proposal_section_validator


@pytest.fixture
def mock_state():
    """Minimal valid proposal state with sections."""
    section = MagicMock(spec=ProposalSection)
    section.model_dump.return_value = {
        "section_id": "sec1",
        "title": "Technical Approach",
        "content": "A" * 2000,
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
def mock_validation_response():
    """Mock Claude validation response."""
    return {
        "total_sections": 1,
        "passed_sections": 1,
        "quality_score": 85,
        "errors": [],
        "warnings": [],
        "info": [],
    }


@pytest.mark.asyncio
async def test_validation_success(mock_state, mock_validation_response):
    """Test successful section validation."""
    with patch(
        "app.graph.nodes.step8b_section_validator.claude_generate",
        new_callable=AsyncMock,
        return_value=mock_validation_response,
    ), patch(
        "app.graph.nodes.step8b_section_validator.execute_node_and_create_version",
        new_callable=AsyncMock,
        return_value=(1, MagicMock()),
    ):
        mock_state["rfp_analysis"].model_dump_json = MagicMock(
            return_value="{}"
        )
        mock_state["rfp_analysis"].mandatory_reqs = ["Req1", "Req2"]
        mock_state["strategy"].model_dump_json = MagicMock(
            return_value="{}"
        )

        result = await proposal_section_validator(mock_state)

        assert "validation_report" in result
        assert isinstance(result["validation_report"], ValidationReport)
        assert result["validation_report"].quality_score == 85


@pytest.mark.asyncio
async def test_validation_missing_sections(mock_state):
    """Test error when sections are missing."""
    mock_state["proposal_sections"] = []

    result = await proposal_section_validator(mock_state)

    assert result["validation_report"] is None
    assert "node_errors" in result


@pytest.mark.asyncio
async def test_validation_missing_rfp(mock_state):
    """Test error when RFP analysis is missing."""
    mock_state["rfp_analysis"] = None

    result = await proposal_section_validator(mock_state)

    assert result["validation_report"] is None
    assert "node_errors" in result


@pytest.mark.asyncio
async def test_validation_error_handling(mock_state):
    """Test error handling for Claude failures."""
    with patch(
        "app.graph.nodes.step8b_section_validator.claude_generate",
        new_callable=AsyncMock,
        side_effect=Exception("Validation Error"),
    ):
        mock_state["rfp_analysis"].model_dump_json = MagicMock(
            return_value="{}"
        )
        mock_state["rfp_analysis"].mandatory_reqs = []
        mock_state["strategy"].model_dump_json = MagicMock(
            return_value="{}"
        )

        result = await proposal_section_validator(mock_state)

        assert result["validation_report"] is None
        assert "Validation Error" in result["node_errors"][
            "proposal_section_validator"
        ]


@pytest.mark.asyncio
async def test_validation_section_truncation(mock_state, mock_validation_response):
    """Test that section content is truncated appropriately."""
    large_section = MagicMock(spec=ProposalSection)
    large_section.model_dump.return_value = {
        "section_id": "sec1",
        "title": "Section",
        "content": "A" * 5000,  # Very long content
        "version": 1,
    }
    mock_state["proposal_sections"] = [large_section]

    with patch(
        "app.graph.nodes.step8b_section_validator.claude_generate",
        new_callable=AsyncMock,
        return_value=mock_validation_response,
    ) as mock_claude, patch(
        "app.graph.nodes.step8b_section_validator.execute_node_and_create_version",
        new_callable=AsyncMock,
        return_value=(1, MagicMock()),
    ):
        mock_state["rfp_analysis"].model_dump_json = MagicMock(
            return_value="{}"
        )
        mock_state["rfp_analysis"].mandatory_reqs = []
        mock_state["strategy"].model_dump_json = MagicMock(
            return_value="{}"
        )

        await proposal_section_validator(mock_state)

        # Verify content was truncated
        call_args = mock_claude.call_args
        prompt = call_args.kwargs["prompt"]
        # Content should be limited
        assert len(prompt) < 5000
