"""
Unit Tests for Artifact Versioning System (Phase 1)

Tests cover:
- Version creation with checksum-based deduplication
- Dependency validation
- Version recommendation logic
- State updates
"""

import pytest
from uuid import UUID

from app.services.version_manager import (
    validate_move_and_resolve_versions,
    check_node_move_feasibility,
    DependencyLevel,
    VersionConflict,
    _calculate_checksum,
    _determine_reason,
    _get_node_dependencies,
    _classify_dependency_level,
    _recommend_version,
)
from app.graph.state import ArtifactVersion, ProposalState


# ── Fixtures ──


@pytest.fixture
def mock_proposal_id() -> UUID:
    """Mock proposal ID."""
    return UUID("12345678-1234-5678-1234-567812345678")


@pytest.fixture
def mock_user_id() -> UUID:
    """Mock user ID."""
    return UUID("87654321-4321-8765-4321-876543218765")


@pytest.fixture
def mock_state() -> ProposalState:
    """Mock workflow state."""
    return {
        "project_id": "12345678-1234-5678-1234-567812345678",
        "created_by": "87654321-4321-8765-4321-876543218765",
        "org_id": "org-uuid",
        "artifact_versions": {},
        "active_versions": {},
        "version_selection_history": [],
    }


@pytest.fixture
def mock_artifact_data() -> dict:
    """Mock artifact data."""
    return {
        "title": "Test Strategy",
        "content": "This is a test strategy",
        "positioning": "offensive",
        "alternatives": [
            {
                "alt_id": "alt_1",
                "ghost_theme": "Test Ghost Theme",
                "win_theme": "Test Win Theme",
            }
        ],
    }


# ── Tests: Checksum Calculation ──


class TestChecksumCalculation:
    """Test checksum-based duplicate detection."""

    def test_checksum_consistency(self):
        """Checksum should be consistent for same data."""
        data = {"title": "Test", "content": "Content"}
        checksum1 = _calculate_checksum(data)
        checksum2 = _calculate_checksum(data)

        assert checksum1 == checksum2

    def test_checksum_differs_on_change(self):
        """Checksum should differ when data changes."""
        data1 = {"title": "Test1"}
        data2 = {"title": "Test2"}

        checksum1 = _calculate_checksum(data1)
        checksum2 = _calculate_checksum(data2)

        assert checksum1 != checksum2

    def test_checksum_order_insensitive(self):
        """Checksum should be same regardless of dict key order."""
        data1 = {"a": 1, "b": 2, "c": 3}
        data2 = {"c": 3, "a": 1, "b": 2}

        checksum1 = _calculate_checksum(data1)
        checksum2 = _calculate_checksum(data2)

        assert checksum1 == checksum2


# ── Tests: Reason Determination ──


class TestReasonDetermination:
    """Test version creation reason classification."""

    def test_first_run_reason(self):
        """Version 1 should be marked as first_run."""
        reason = _determine_reason("test_node", 1, None)
        assert reason == "first_run"

    def test_manual_rerun_reason(self, mock_state):
        """Version > 1 with active versions should be manual_rerun."""
        mock_state["active_versions"] = {"test_node_output": 1}
        reason = _determine_reason("test_node", 2, mock_state)
        assert reason == "manual_rerun"

    def test_rerun_after_change_reason(self):
        """Version > 1 without state should be rerun_after_change."""
        reason = _determine_reason("test_node", 2, None)
        assert reason == "rerun_after_change"


# ── Tests: Node Dependencies ──


class TestNodeDependencies:
    """Test node dependency map lookups."""

    def test_proposal_write_next_dependencies(self):
        """proposal_write_next should depend on strategy and customer_context."""
        deps = _get_node_dependencies("proposal_write_next")
        assert "strategy" in deps
        assert "customer_context" in deps

    def test_unknown_node_dependencies(self):
        """Unknown node should return empty list."""
        deps = _get_node_dependencies("unknown_node_xyz")
        assert deps == []

    def test_strategy_generate_dependencies(self):
        """strategy_generate should depend on go_no_go and rfp_analysis."""
        deps = _get_node_dependencies("strategy_generate")
        assert "go_no_go" in deps
        assert "rfp_analysis" in deps


# ── Tests: Dependency Classification ──


class TestDependencyClassification:
    """Test version conflict severity classification."""

    def test_no_conflicts_classification(self):
        """No conflicts should be NONE level."""
        conflicts = [
            VersionConflict(input_key="test", versions=[1], status="SINGLE")
        ]
        level = _classify_dependency_level(conflicts, "test_node")
        assert level == DependencyLevel.NONE

    def test_missing_input_classification(self):
        """Missing critical input should be CRITICAL level."""
        conflicts = [
            VersionConflict(input_key="required", status="MISSING")
        ]
        level = _classify_dependency_level(conflicts, "test_node")
        assert level == DependencyLevel.CRITICAL

    def test_multiple_versions_classification(self):
        """Multiple versions should be HIGH level."""
        conflicts = [
            VersionConflict(input_key="test", versions=[1, 2, 3], status="MULTIPLE")
        ]
        level = _classify_dependency_level(conflicts, "test_node")
        assert level == DependencyLevel.HIGH

    def test_mixed_conflicts_critical_wins(self):
        """CRITICAL level should override others."""
        conflicts = [
            VersionConflict(input_key="required", status="MISSING"),
            VersionConflict(input_key="optional", versions=[1, 2], status="MULTIPLE"),
        ]
        level = _classify_dependency_level(conflicts, "test_node")
        assert level == DependencyLevel.CRITICAL


# ── Tests: Version Recommendation ──


class TestVersionRecommendation:
    """Test smart version recommendation logic."""

    def test_recommend_active_version(self, mock_state):
        """Should recommend active version if in available list."""
        mock_state["active_versions"] = {"test_key": 2}
        available = [1, 2, 3]

        recommended = _recommend_version("test_key", available, mock_state)
        assert recommended == 2

    def test_recommend_latest_version(self, mock_state):
        """Should recommend latest version if active not available."""
        mock_state["active_versions"] = {}
        available = [1, 2, 3]

        recommended = _recommend_version("test_key", available, mock_state)
        assert recommended == 3

    def test_recommend_first_version(self, mock_state):
        """Should recommend first version if nothing else available."""
        mock_state["active_versions"] = {}
        available = [5]

        recommended = _recommend_version("test_key", available, mock_state)
        assert recommended == 5


# ── Tests: Version Conflict Detection ──


@pytest.mark.asyncio
async def test_validate_move_single_version(mock_state):
    """Move validation should pass with single version."""
    mock_state["active_versions"] = {"strategy_v1": 1}

    result = await validate_move_and_resolve_versions(
        proposal_id=UUID("12345678-1234-5678-1234-567812345678"),
        target_node="proposal_write_next",
        state=mock_state,
    )

    assert result.can_move is True
    assert result.dependency_level in [DependencyLevel.NONE, DependencyLevel.LOW]


@pytest.mark.asyncio
async def test_validate_move_missing_required_input(mock_state):
    """Move validation should fail if required input is missing."""
    mock_state["active_versions"] = {}  # No strategy

    result = await validate_move_and_resolve_versions(
        proposal_id=UUID("12345678-1234-5678-1234-567812345678"),
        target_node="proposal_write_next",
        state=mock_state,
    )

    assert result.can_move is False
    assert result.dependency_level == DependencyLevel.CRITICAL


# ── Tests: Move Feasibility Check ──


@pytest.mark.asyncio
async def test_check_move_feasibility_no_conflicts(mock_state):
    """Should indicate no modal needed if no conflicts."""
    mock_state["active_versions"] = {"strategy": 1}

    result = await check_node_move_feasibility(
        proposal_id=UUID("12345678-1234-5678-1234-567812345678"),
        target_node="proposal_write_next",
        state=mock_state,
    )

    assert result["can_move"] is True
    assert result["needs_modal"] is False


@pytest.mark.asyncio
async def test_check_move_feasibility_impossible_move(mock_state):
    """Should indicate cannot move if required inputs missing."""
    mock_state["active_versions"] = {}

    result = await check_node_move_feasibility(
        proposal_id=UUID("12345678-1234-5678-1234-567812345678"),
        target_node="proposal_write_next",
        state=mock_state,
    )

    assert result["can_move"] is False


# ── Tests: ArtifactVersion Model ──


class TestArtifactVersionModel:
    """Test ArtifactVersion Pydantic model."""

    def test_artifact_version_creation(self):
        """Should create ArtifactVersion with valid data."""
        artifact = ArtifactVersion(
            node_name="test_node",
            output_key="test_output",
            version=1,
            created_at="2026-03-30T10:00:00Z",
            created_by="user-uuid",
            is_active=True,
        )

        assert artifact.node_name == "test_node"
        assert artifact.version == 1
        assert artifact.is_active is True

    def test_artifact_version_optional_fields(self):
        """Should handle optional fields gracefully."""
        artifact = ArtifactVersion(
            node_name="test_node",
            output_key="test_output",
            version=1,
            created_at="2026-03-30T10:00:00Z",
            created_by="user-uuid",
            is_active=True,
            used_by=[],
            checksum=None,
        )

        assert artifact.used_by == []
        assert artifact.checksum is None


# ── Integration Tests ──


@pytest.mark.asyncio
async def test_version_creation_and_state_update(mock_proposal_id, mock_user_id, mock_artifact_data, mock_state):
    """
    Integration test: Create version and verify state update.

    NOTE: This test is marked for manual execution with real DB.
    In CI/CD, mock Supabase responses instead.
    """
    pytest.skip("Requires real Supabase connection - run manually")

    # This would require:
    # 1. Real or mocked Supabase client
    # 2. Real or mocked UUID values
    # 3. Proper async test setup with database transactions


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
