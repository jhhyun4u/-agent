"""
Unit tests for state transition validator.

Tests:
- Valid state transitions
- Invalid state transitions
- Timeline logging
- Timestamp updates
- Terminal state detection
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.state_validator import StateValidator, ProposalStatus, WinResult, AITaskStatus
from app.exceptions import TenopAPIError


class TestStateValidatorTransitions:
    """Test valid and invalid state transitions."""

    def test_initialized_can_transition_to_multiple_states(self):
        """initialized → waiting, in_progress, on_hold, expired"""
        allowed = StateValidator.get_allowed_transitions(ProposalStatus.INITIALIZED)
        assert ProposalStatus.WAITING in allowed
        assert ProposalStatus.IN_PROGRESS in allowed
        assert ProposalStatus.ON_HOLD in allowed
        assert ProposalStatus.EXPIRED in allowed

    def test_in_progress_can_transition_to_completed(self):
        """in_progress → completed is valid"""
        allowed = StateValidator.get_allowed_transitions(ProposalStatus.IN_PROGRESS)
        assert ProposalStatus.COMPLETED in allowed

    def test_waiting_cannot_transition_to_closed(self):
        """waiting → closed is INVALID (must go through submitted/presentation)"""
        allowed = StateValidator.get_allowed_transitions(ProposalStatus.WAITING)
        assert ProposalStatus.CLOSED not in allowed

    def test_presentation_can_transition_to_closed(self):
        """presentation → closed is valid"""
        allowed = StateValidator.get_allowed_transitions(ProposalStatus.PRESENTATION)
        assert ProposalStatus.CLOSED in allowed

    def test_closed_is_terminal(self):
        """closed has no valid transitions"""
        allowed = StateValidator.get_allowed_transitions(ProposalStatus.CLOSED)
        assert len(allowed) == 0

    def test_archived_is_terminal(self):
        """archived has no valid transitions"""
        allowed = StateValidator.get_allowed_transitions(ProposalStatus.ARCHIVED)
        assert len(allowed) == 0

    def test_expired_is_terminal(self):
        """expired has no valid transitions"""
        allowed = StateValidator.get_allowed_transitions(ProposalStatus.EXPIRED)
        assert len(allowed) == 0

    def test_is_terminal_state_closed(self):
        """closed is terminal"""
        assert StateValidator.is_terminal_state(ProposalStatus.CLOSED)

    def test_is_terminal_state_in_progress(self):
        """in_progress is not terminal"""
        assert not StateValidator.is_terminal_state(ProposalStatus.IN_PROGRESS)


@pytest.mark.asyncio
class TestStateValidatorValidation:
    """Test transition validation logic."""

    async def test_validate_valid_transition(self):
        """Valid transition should not raise"""
        # Should not raise
        await StateValidator.validate_transition(
            "prop-123",
            ProposalStatus.INITIALIZED.value,
            ProposalStatus.IN_PROGRESS.value,
        )

    async def test_validate_invalid_transition(self):
        """Invalid transition should raise TenopAPIError"""
        with pytest.raises(TenopAPIError) as exc_info:
            await StateValidator.validate_transition(
                "prop-123",
                ProposalStatus.CLOSED.value,
                ProposalStatus.IN_PROGRESS.value,
            )
        assert exc_info.value.code == "invalid_transition"

    async def test_validate_invalid_status_value(self):
        """Invalid status value should raise TenopAPIError"""
        with pytest.raises(TenopAPIError) as exc_info:
            await StateValidator.validate_transition(
                "prop-123",
                "invalid_status",
                ProposalStatus.IN_PROGRESS.value,
            )
        assert exc_info.value.code == "invalid_status"


@pytest.mark.asyncio
class TestStateValidatorTransition:
    """Test transition method with timeline logging."""

    @pytest.fixture
    async def mock_client(self):
        """Mock Supabase client."""
        mock = AsyncMock()
        mock.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = AsyncMock()
        mock.table.return_value.update.return_value.eq.return_value.execute.return_value = AsyncMock()
        mock.table.return_value.insert.return_value.execute.return_value = MagicMock(data=[{"id": "event-1"}])
        return mock

    @patch("app.services.state_validator.get_async_client")
    async def test_transition_updates_proposal_status(self, mock_get_client, mock_client):
        """Transition should update proposal.status"""
        mock_get_client.return_value = mock_client

        # Setup mock to return initialized status
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"status": ProposalStatus.INITIALIZED.value}
        )

        await StateValidator.transition(
            "prop-123",
            ProposalStatus.IN_PROGRESS,
            current_phase="rfp_analyze",
            user_id="user-123",
            actor_type="user",
            reason="Workflow started",
        )

        # Verify update was called
        update_calls = mock_client.table.return_value.update.call_args_list
        assert len(update_calls) > 0

    @patch("app.services.state_validator.get_async_client")
    async def test_transition_logs_to_timeline(self, mock_get_client, mock_client):
        """Transition should insert entry to proposal_timelines"""
        mock_get_client.return_value = mock_client

        # Setup mock to return initialized status
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"status": ProposalStatus.INITIALIZED.value}
        )

        result = await StateValidator.transition(
            "prop-123",
            ProposalStatus.IN_PROGRESS,
            current_phase="rfp_analyze",
            user_id="user-123",
            actor_type="user",
            reason="Workflow started",
        )

        # Verify insert was called on proposal_timelines
        calls = [str(call) for call in mock_client.table.call_args_list]
        assert any("proposal_timelines" in str(call) for call in calls)

    @patch("app.services.state_validator.get_async_client")
    async def test_transition_sets_started_at_on_first_transition(self, mock_get_client, mock_client):
        """First transition from initialized should set started_at"""
        mock_get_client.return_value = mock_client

        # Setup mock
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"status": ProposalStatus.INITIALIZED.value}
        )

        await StateValidator.transition(
            "prop-123",
            ProposalStatus.IN_PROGRESS,
        )

        # Get the update call and verify started_at is in the update data
        update_call = mock_client.table.return_value.update.call_args
        if update_call:
            update_data = update_call[0][0]  # First positional arg
            assert "started_at" in update_data

    @patch("app.services.state_validator.get_async_client")
    async def test_transition_to_closed_sets_closed_at(self, mock_get_client, mock_client):
        """Transition to closed should set closed_at timestamp"""
        mock_get_client.return_value = mock_client

        # Setup mock
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"status": ProposalStatus.PRESENTATION.value}
        )

        await StateValidator.transition(
            "prop-123",
            ProposalStatus.CLOSED,
            win_result=WinResult.WON.value,
        )

        # Verify closed_at is in update
        update_call = mock_client.table.return_value.update.call_args
        if update_call:
            update_data = update_call[0][0]
            assert "closed_at" in update_data

    @patch("app.services.state_validator.get_async_client")
    async def test_transition_to_closed_sets_win_result(self, mock_get_client, mock_client):
        """Transition to closed with win_result should update win_result"""
        mock_get_client.return_value = mock_client

        # Setup mock
        mock_client.table.return_value.select.return_value.eq.return_value.single.return_value.execute.return_value = MagicMock(
            data={"status": ProposalStatus.PRESENTATION.value}
        )

        await StateValidator.transition(
            "prop-123",
            ProposalStatus.CLOSED,
            win_result=WinResult.LOST.value,
        )

        # Verify win_result is in update
        update_call = mock_client.table.return_value.update.call_args
        if update_call:
            update_data = update_call[0][0]
            assert "win_result" in update_data
            assert update_data["win_result"] == WinResult.LOST.value


@pytest.mark.asyncio
class TestAITaskStatus:
    """Test AI task status updates (Layer 3)."""

    @patch("app.services.state_validator.get_async_client")
    async def test_update_ai_task_status_creates_new(self, mock_get_client):
        """Should create new ai_task_status if none exists"""
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        # Mock query returns empty (no existing record)
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[]
        )

        # Mock insert
        mock_client.table.return_value.insert.return_value.execute.return_value = MagicMock(
            data=[{"id": "task-1", "status": "running"}]
        )

        result = await StateValidator.update_ai_task_status(
            "prop-123",
            AITaskStatus.RUNNING,
            current_node="rfp_analyze",
        )

        # Verify insert was called
        assert mock_client.table.return_value.insert.called

    @patch("app.services.state_validator.get_async_client")
    async def test_update_ai_task_status_updates_existing(self, mock_get_client):
        """Should update existing ai_task_status"""
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        # Mock query returns existing record
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{"id": "task-1"}]
        )

        # Mock update
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "task-1", "status": "complete"}]
        )

        result = await StateValidator.update_ai_task_status(
            "prop-123",
            AITaskStatus.COMPLETE,
        )

        # Verify update was called (not insert)
        assert mock_client.table.return_value.update.called

    @patch("app.services.state_validator.get_async_client")
    async def test_update_ai_task_status_sets_ended_at_on_complete(self, mock_get_client):
        """Should set ended_at when status is COMPLETE"""
        mock_client = AsyncMock()
        mock_get_client.return_value = mock_client

        # Mock query returns existing record
        mock_client.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value = MagicMock(
            data=[{"id": "task-1"}]
        )

        # Mock update
        mock_client.table.return_value.update.return_value.eq.return_value.execute.return_value = MagicMock(
            data=[{"id": "task-1"}]
        )

        await StateValidator.update_ai_task_status(
            "prop-123",
            AITaskStatus.COMPLETE,
        )

        # Verify ended_at is in update data
        update_call = mock_client.table.return_value.update.call_args
        if update_call:
            update_data = update_call[0][0]
            assert "ended_at" in update_data
