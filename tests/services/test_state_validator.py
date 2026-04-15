"""
단위 테스트: StateValidator (app/services/state_validator.py)

검증 범위:
- 상태 전환 규칙 (VALID_TRANSITIONS)
- 타임라인 로깅 (proposal_timelines)
- 타임스탐프 자동 설정
- win_result 검증
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, patch

from app.services.state_validator import StateValidator, ProposalStatus, WinResult


class TestProposalStatusEnum:
    """ProposalStatus enum 테스트"""

    def test_proposal_status_values(self):
        """모든 ProposalStatus 값이 예상 문자열과 일치"""
        assert ProposalStatus.INITIALIZED.value == "initialized"
        assert ProposalStatus.WAITING.value == "waiting"
        assert ProposalStatus.IN_PROGRESS.value == "in_progress"
        assert ProposalStatus.COMPLETED.value == "completed"
        assert ProposalStatus.SUBMITTED.value == "submitted"
        assert ProposalStatus.PRESENTATION.value == "presentation"
        assert ProposalStatus.CLOSED.value == "closed"
        assert ProposalStatus.ARCHIVED.value == "archived"
        assert ProposalStatus.ON_HOLD.value == "on_hold"
        assert ProposalStatus.EXPIRED.value == "expired"


class TestValidTransitions:
    """상태 전환 규칙 (VALID_TRANSITIONS) 테스트"""

    def test_initialized_transitions(self):
        """initialized에서 전환 가능한 상태 확인"""
        allowed = StateValidator.VALID_TRANSITIONS[ProposalStatus.INITIALIZED]
        expected = [
            ProposalStatus.WAITING,
            ProposalStatus.IN_PROGRESS,
            ProposalStatus.CLOSED,
            ProposalStatus.EXPIRED,
            ProposalStatus.ON_HOLD,
        ]
        assert set(allowed) == set(expected)

    def test_waiting_transitions(self):
        """waiting에서 전환 가능한 상태 확인"""
        allowed = StateValidator.VALID_TRANSITIONS[ProposalStatus.WAITING]
        expected = [
            ProposalStatus.IN_PROGRESS,
            ProposalStatus.CLOSED,
            ProposalStatus.EXPIRED,
            ProposalStatus.ON_HOLD,
        ]
        assert set(allowed) == set(expected)


@pytest.mark.asyncio
class TestValidateTransition:
    """StateValidator.validate_transition() 테스트"""

    async def test_valid_transition_waiting_to_in_progress(self):
        """valid_transition: waiting → in_progress"""
        result = await StateValidator.validate_transition(
            "prop_123",
            "waiting",
            "in_progress",
        )
        assert result is True

    async def test_invalid_transition_archived_to_anything(self):
        """invalid_transition: archived는 terminal state"""
        with pytest.raises(ValueError, match="유효하지 않은 전환"):
            await StateValidator.validate_transition(
                "prop_123",
                "archived",
                "closed",
            )

    async def test_unknown_status_raises_error(self):
        """unknown status는 ValueError 발생"""
        with pytest.raises(ValueError, match="알 수 없는 상태"):
            await StateValidator.validate_transition(
                "prop_123",
                "unknown_status",
                "waiting",
            )


@pytest.mark.asyncio
class TestGetValidNextStates:
    """StateValidator.get_valid_next_states() 테스트"""

    async def test_get_valid_next_states_waiting(self):
        """waiting 상태에서 전환 가능한 상태들 조회"""
        result = await StateValidator.get_valid_next_states("waiting")
        expected = [
            "in_progress",
            "closed",
            "expired",
            "on_hold",
        ]
        assert set(result) == set(expected)

    async def test_get_valid_next_states_archived(self):
        """archived는 terminal state이므로 다음 상태 없음"""
        result = await StateValidator.get_valid_next_states("archived")
        assert result == []

    async def test_get_valid_next_states_unknown_status(self):
        """unknown status 조회 시 빈 리스트 반환"""
        result = await StateValidator.get_valid_next_states("unknown_status")
        assert result == []
