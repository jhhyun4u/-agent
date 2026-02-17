"""pytest 호환 통합 테스트"""
import pytest
from graph.integrated_supervisor import (
    build_integrated_supervisor,
    get_supervisor_status,
    create_initial_state,
)


@pytest.fixture
def mock_rfp():
    """Mock RFP 문서"""
    return """
    제안요청서

    사업명: 테스트 프로젝트
    발주기관: 테스트 기관

    1. 사업 개요
    테스트 프로젝트입니다.

    2. 평가 기준
    - 기술 능력: 50점
    - 사업 수행 계획: 50점

    3. 예산: 10억원
    4. 기간: 12개월
    """


@pytest.fixture
def mock_company_profile():
    """Mock 회사 프로필"""
    return {
        "name": "테스트 회사",
        "strengths": ["기술력", "경험"],
        "experience_years": 10,
    }


class TestIntegratedSupervisor:
    """통합 Supervisor 테스트 클래스"""

    def test_build_supervisor(self):
        """Supervisor 빌드 테스트"""
        graph = build_integrated_supervisor()
        assert graph is not None

    def test_supervisor_status(self):
        """Supervisor 상태 확인 테스트"""
        graph = build_integrated_supervisor()
        status = get_supervisor_status(graph)

        assert status["status"] == "operational"
        assert status["subagents"] == 5
        assert status["hitl_gates"] == 3
        assert status["checkpointer"] == "memory"

    def test_create_initial_state(self, mock_rfp, mock_company_profile):
        """초기 상태 생성 테스트"""
        state = create_initial_state(
            rfp_document=mock_rfp,
            company_profile=mock_company_profile
        )

        assert state is not None
        assert state["current_phase"] == "initialization"
        assert "proposal_state" in state
        assert "workflow_plan" in state
        assert state["proposal_state"]["rfp_document"] == mock_rfp
        assert state["proposal_state"]["company_profile"] == mock_company_profile

    def test_proposal_id_generation(self, mock_rfp):
        """제안서 ID 자동 생성 테스트"""
        state = create_initial_state(rfp_document=mock_rfp)
        proposal_id = state["proposal_state"]["proposal_id"]

        assert proposal_id.startswith("proposal_")
        assert len(proposal_id) > len("proposal_")

    def test_state_structure(self, mock_rfp, mock_company_profile):
        """상태 구조 검증 테스트"""
        state = create_initial_state(
            rfp_document=mock_rfp,
            company_profile=mock_company_profile
        )

        # SupervisorState 필드 확인
        required_fields = [
            "proposal_state",
            "current_phase",
            "workflow_plan",
            "agent_status",
            "messages",
            "errors",
        ]

        for field in required_fields:
            assert field in state, f"Missing required field: {field}"

        # ProposalState 필드 확인
        proposal_state = state["proposal_state"]
        proposal_required = [
            "proposal_id",
            "created_at",
            "updated_at",
            "rfp_document",
            "company_profile",
        ]

        for field in proposal_required:
            assert field in proposal_state, f"Missing proposal field: {field}"


class TestSubAgents:
    """Sub-agent 개별 테스트"""

    @pytest.mark.asyncio
    async def test_all_agents_importable(self):
        """모든 에이전트 import 가능 여부 테스트"""
        from agents import (
            build_rfp_analysis_graph,
            build_strategy_graph,
            build_section_generation_graph,
            build_quality_graph,
            build_document_graph,
        )

        # 모든 빌더 함수가 그래프를 반환하는지 확인
        rfp_graph = build_rfp_analysis_graph()
        assert rfp_graph is not None

        strategy_graph = build_strategy_graph()
        assert strategy_graph is not None

        section_graph = build_section_generation_graph()
        assert section_graph is not None

        quality_graph = build_quality_graph()
        assert quality_graph is not None

        document_graph = build_document_graph()
        assert document_graph is not None


# pytest 실행 명령어:
# uv run pytest tests/test_integration.py -v
# uv run pytest tests/test_integration.py::TestIntegratedSupervisor::test_build_supervisor -v
