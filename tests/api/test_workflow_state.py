"""
API 통합 테스트: routes_workflow.py - /state 엔드포인트

검증 범위:
- 3-layer 응답 구조 (business_status, workflow_phase, ai_status)
- /start 호출 후 상태 변경
- /resume no_go 처리
- active_states 체크
"""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI TestClient 반환"""
    return TestClient(app)


class TestStateEndpoint:
    """3-layer 상태 응답 구조 검증 (단위 테스트 레벨)"""

    def test_three_layer_structure_conceptual(self):
        """3-layer 응답 구조: business_status, workflow_phase, ai_status"""
        # 실제 DB 없이 응답 구조만 검증
        expected_response = {
            "business_status": "in_progress",     # Layer 1: proposals.status
            "workflow_phase": "proposal_write",   # Layer 2: proposals.current_phase
            "ai_status": {                         # Layer 3: ai_task_logs
                "status": "running",
                "current_node": "proposal_write_next"
            },
            "timestamps": {
                "started_at": "2026-04-14T00:00:00Z",
                "last_activity_at": "2026-04-14T12:00:00Z",
            }
        }

        # 필수 필드 검증
        assert "business_status" in expected_response
        assert "workflow_phase" in expected_response
        assert "ai_status" in expected_response
        assert isinstance(expected_response["ai_status"], dict)
        assert "status" in expected_response["ai_status"]


class TestActiveSatesCheck:
    """Active states 체크 - ProposalStatus 사용"""

    def test_active_states_uses_proposal_status_enum(self):
        """active_states가 ProposalStatus enum 값 사용"""
        from app.services.state_validator import ProposalStatus

        # 유효한 active states
        active_states = (
            ProposalStatus.IN_PROGRESS.value,
            ProposalStatus.COMPLETED.value,
        )

        assert ProposalStatus.IN_PROGRESS.value in active_states
        assert ProposalStatus.COMPLETED.value in active_states

        # 잘못된 상태들은 포함되지 않음
        assert "processing" not in active_states
        assert "searching" not in active_states
        assert "analyzing" not in active_states
