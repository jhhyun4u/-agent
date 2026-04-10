"""
Unit tests for STEP 8C: proposal_sections_consolidation node.

Tests cover:
- Deterministic consolidation logic (no Claude call)
- Quality metrics calculation
- Section lineage tracking
- State management
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.graph.state import (
    ProposalSection,
    ConsolidatedProposal,
    ValidationReport,
)
from app.graph.nodes.step8c_consolidation import proposal_sections_consolidation


@pytest.fixture
def mock_state():
    """State with sections and validation report."""
    section1 = MagicMock(spec=ProposalSection)
    section1.model_dump.return_value = {
        "section_id": "sec1",
        "title": "Technical",
        "content": "Technical content here.",
        "version": 1,
    }

    section2 = MagicMock(spec=ProposalSection)
    section2.model_dump.return_value = {
        "section_id": "sec2",
        "title": "Schedule",
        "content": "Schedule details.",
        "version": 1,
    }

    validation_report = MagicMock(spec=ValidationReport)
    validation_report.quality_score = 85
    validation_report.errors = []
    validation_report.warnings = []

    return {
        "project_id": "550e8400-e29b-41d4-a716-446655440000",
        "created_by": "550e8400-e29b-41d4-a716-446655440001",
        "proposal_sections": [section1, section2],
        "validation_report": validation_report,
        "selected_versions": {},
        "node_errors": {},
        "artifact_versions": {},
        "active_versions": {},
    }


@pytest.mark.asyncio
async def test_consolidation_success(mock_state):
    """Test successful consolidation."""
    with patch(
        "app.graph.nodes.step8c_consolidation.execute_node_and_create_version",
        new_callable=AsyncMock,
        return_value=(1, MagicMock()),
    ) as mock_version:
        result = await proposal_sections_consolidation(mock_state)

        assert "consolidated_proposal" in result
        assert isinstance(result["consolidated_proposal"], ConsolidatedProposal)
        assert result["consolidated_proposal"].section_count == 2
        # Verify artifacts were created (2 calls: consolidated + sections v2)
        assert mock_version.call_count == 2


@pytest.mark.asyncio
async def test_consolidation_missing_sections(mock_state):
    """Test error when sections are missing."""
    mock_state["proposal_sections"] = []

    result = await proposal_sections_consolidation(mock_state)

    assert result["consolidated_proposal"] is None
    assert "node_errors" in result


@pytest.mark.asyncio
async def test_consolidation_quality_metrics(mock_state):
    """Test quality metrics calculation."""
    mock_state["validation_report"].quality_score = 90

    with patch(
        "app.graph.nodes.step8c_consolidation.execute_node_and_create_version",
        new_callable=AsyncMock,
        return_value=(1, MagicMock()),
    ):
        result = await proposal_sections_consolidation(mock_state)

        consolidated = result["consolidated_proposal"]
        assert consolidated.quality_metrics["compliance"] == 90
        assert consolidated.completeness_score == 90


@pytest.mark.asyncio
async def test_consolidation_word_count(mock_state):
    """Test word count calculation."""
    mock_state["proposal_sections"][
        0
    ].model_dump.return_value["content"] = "word " * 100  # 500 words

    with patch(
        "app.graph.nodes.step8c_consolidation.execute_node_and_create_version",
        new_callable=AsyncMock,
        return_value=(1, MagicMock()),
    ):
        result = await proposal_sections_consolidation(mock_state)

        # Should count ~550 words (500 + ~50 from section 2)
        assert result["consolidated_proposal"].total_word_count > 500


@pytest.mark.asyncio
async def test_consolidation_submission_readiness(mock_state):
    """Test submission readiness determination."""
    # No errors, high quality
    mock_state["validation_report"].errors = []
    mock_state["validation_report"].quality_score = 85

    with patch(
        "app.graph.nodes.step8c_consolidation.execute_node_and_create_version",
        new_callable=AsyncMock,
        return_value=(1, MagicMock()),
    ):
        result = await proposal_sections_consolidation(mock_state)

        assert result["consolidated_proposal"].submission_ready is True


@pytest.mark.asyncio
async def test_consolidation_with_errors(mock_state):
    """Test submission readiness when errors exist."""
    mock_state["validation_report"].errors = [MagicMock(description="Error 1")]
    mock_state["validation_report"].quality_score = 70

    with patch(
        "app.graph.nodes.step8c_consolidation.execute_node_and_create_version",
        new_callable=AsyncMock,
        return_value=(1, MagicMock()),
    ):
        result = await proposal_sections_consolidation(mock_state)

        assert result["consolidated_proposal"].submission_ready is False
        assert len(result["consolidated_proposal"].blockers) > 0
