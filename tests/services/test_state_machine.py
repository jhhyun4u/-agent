"""
단위 테스트: StateMachine (app/state_machine.py)

검증 범위:
- start_workflow()
- close_proposal()
- hold_proposal()
- resume_proposal()
- expire_proposal()
- archive_proposal()
"""

import pytest
from unittest.mock import AsyncMock, patch

from app.state_machine import StateMachine
from app.services.state_validator import StateValidator


@pytest.mark.asyncio
class TestStateMachineWorkflow:
    """StateMachine 워크플로우 메서드 테스트"""

    @patch.object(StateValidator, "transition", new_callable=AsyncMock)
    async def test_start_workflow_transition(self, mock_transition):
        """start_workflow() - waiting/initialized → in_progress 전환"""
        mock_transition.return_value = {"event": "status_change"}

        sm = StateMachine("prop_123")
        result = await sm.start_workflow(user_id="user_1", initial_phase="start")

        assert result is not None
        mock_transition.assert_called_once()

    @patch.object(StateValidator, "transition", new_callable=AsyncMock)
    async def test_close_proposal_with_won(self, mock_transition):
        """close_proposal() - win_result='won'"""
        mock_transition.return_value = {"event": "close"}

        sm = StateMachine("prop_123")
        result = await sm.close_proposal(
            user_id="user_1",
            win_result="won",
            reason="수주 확정",
        )

        assert result is not None
        mock_transition.assert_called_once()

    @patch.object(StateValidator, "transition", new_callable=AsyncMock)
    async def test_close_proposal_with_lost(self, mock_transition):
        """close_proposal() - win_result='lost'"""
        mock_transition.return_value = {"event": "close"}

        sm = StateMachine("prop_123")
        result = await sm.close_proposal(
            user_id="user_1",
            win_result="lost",
            reason="패찰",
        )

        assert result is not None
        mock_transition.assert_called_once()

    @patch.object(StateValidator, "transition", new_callable=AsyncMock)
    async def test_hold_proposal(self, mock_transition):
        """hold_proposal() - in_progress → on_hold"""
        mock_transition.return_value = {"event": "hold"}

        sm = StateMachine("prop_123")
        result = await sm.hold_proposal(
            user_id="user_1",
            reason="일시 보류"
        )

        assert result is not None
        mock_transition.assert_called_once()

    @patch.object(StateValidator, "transition", new_callable=AsyncMock)
    async def test_resume_proposal(self, mock_transition):
        """resume_proposal() - on_hold → waiting/in_progress"""
        mock_transition.return_value = {"event": "resume"}

        sm = StateMachine("prop_123")
        result = await sm.resume_proposal(
            user_id="user_1",
            to_status="waiting"
        )

        assert result is not None
        mock_transition.assert_called_once()

    @patch.object(StateValidator, "transition", new_callable=AsyncMock)
    async def test_expire_proposal(self, mock_transition):
        """expire_proposal() - → expired"""
        mock_transition.return_value = {"event": "expire"}

        sm = StateMachine("prop_123")
        result = await sm.expire_proposal()

        assert result is not None
        mock_transition.assert_called_once()
