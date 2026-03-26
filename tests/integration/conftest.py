"""통합 테스트 공통 fixture — Mock 기반 (Level 1, CI 실행).

기존 tests/workflow/conftest.py의 Claude mock + Supabase mock을 재활용하고,
MCP 도구 mock, 에러 시뮬레이션, 그래프 빌드 헬퍼를 추가.
"""

# 레거시 테스트 파일 제외 (구 아키텍처 기반, 임포트 불가)
collect_ignore = [
    "test_agent_pipeline.py",
    "test_integrated_supervisor.py",
    "test_phased_supervisor.py",
]

import json
import pytest
from contextlib import ExitStack
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import Command


# ── 기존 fixture 재활용 ──

# workflow/conftest.py에서 가져오기
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from workflow.conftest import (  # noqa: E402
    _make_claude_mock,
    _make_pricing_mock,
    _make_workflow_supabase_mock,
    _mock_get_active_prompt,
    _mock_get_prompt_for_experiment,
    _mock_record_usage,
    load_fixture,
)


FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_integration_fixture(name: str) -> dict:
    """integration/fixtures/ 디렉토리에서 JSON 로드."""
    with open(FIXTURES_DIR / name, encoding="utf-8") as f:
        return json.load(f)


# ── 표준 테스트 상태 ──

@pytest.fixture
def standard_rfp_state():
    """표준 RFP 테스트 상태 (Case A + PPT)."""
    return {
        "project_id": "integ-test-001",
        "rfp_raw": """제안요청서
사업명: 클라우드 기반 ERP 시스템 구축
발주기관: ABC 주식회사
예산: 5억원
기간: 6개월
평가항목: 기술 이해도(30), 수행 방안(40), 프로젝트 관리(30)
필수요건: ISO 27001 인증, 5년 이상 ERP 구축 경험""",
        "current_step": "",
        "error": None,
    }


@pytest.fixture
def doc_only_rfp_state():
    """서류심사 전용 RFP 테스트 상태 (PPT 스킵)."""
    return {
        "project_id": "integ-test-002",
        "rfp_raw": """제안요청서
사업명: 데이터 분석 플랫폼 구축
발주기관: XYZ 공공기관
예산: 3억원
기간: 4개월
심사방법: 서류심사(document_only)""",
        "current_step": "",
        "error": None,
    }


# ── Claude Mock 변형 ──

@pytest.fixture
def claude_mock():
    """기본 Claude mock (키워드 디스패치)."""
    return _make_claude_mock()


def _make_claude_error_mock(error_type: str):
    """Claude API 에러 시뮬레이션 mock 생성."""
    from app.exceptions import AIServiceError, AITimeoutError, RateLimitError

    error_map = {
        "timeout": AITimeoutError(step="test_node"),
        "rate_limit": RateLimitError("Claude API 요청 한도 초과"),
        "connection": AIServiceError("Claude API 서버에 연결할 수 없습니다."),
        "auth": AIServiceError("Claude API 인증 오류: API 키를 확인하세요."),
    }
    error = error_map.get(error_type, AIServiceError(f"테스트 에러: {error_type}"))

    async def _failing_claude(*args, **kwargs):
        raise error

    return _failing_claude


@pytest.fixture
def claude_timeout_mock():
    """Claude 타임아웃 에러 mock."""
    return _make_claude_error_mock("timeout")


@pytest.fixture
def claude_rate_limit_mock():
    """Claude Rate Limit 에러 mock."""
    return _make_claude_error_mock("rate_limit")


# ── MCP 도구 Mock ──

@pytest.fixture
def mcp_searxng_mock():
    """SearXNG 웹 검색 mock."""
    return AsyncMock(return_value={
        "results": [
            {
                "title": "클라우드 ERP 도입 사례 — 한국정보화진흥원",
                "url": "https://example.com/cloud-erp",
                "snippet": "2025년 공공기관 클라우드 ERP 전환율 42% 달성",
                "source": "searxng",
            },
            {
                "title": "ERP 시스템 구축 가이드라인",
                "url": "https://example.com/erp-guide",
                "snippet": "공공기관 ERP 구축 시 필수 고려사항 10가지",
                "source": "searxng",
            },
        ],
    })


@pytest.fixture
def mcp_openalex_mock():
    """OpenAlex 학술 검색 mock."""
    return AsyncMock(return_value={
        "results": [
            {
                "title": "Cloud ERP Migration in Public Sector",
                "doi": "10.1234/test.2025.001",
                "abstract": "This study examines cloud ERP migration patterns...",
                "source": "openalex",
            },
        ],
    })


@pytest.fixture
def mcp_g2b_mock():
    """G2B 유사 공고 검색 mock."""
    return AsyncMock(return_value={
        "similar_bids": [
            {"bid_no": "20250101001", "title": "클라우드 ERP 시스템 구축", "amount": 480_000_000},
        ],
        "competitor_history": [
            {"company": "A사", "win_count": 3, "total_bids": 5},
        ],
    })


@pytest.fixture
def mcp_tools_mock(mcp_searxng_mock, mcp_openalex_mock, mcp_g2b_mock):
    """MCP 도구 통합 mock 세트."""
    return {
        "searxng": mcp_searxng_mock,
        "openalex": mcp_openalex_mock,
        "g2b": mcp_g2b_mock,
    }


# ── 그래프 빌드 헬퍼 ──

def build_all_patches(claude_side_effect=None, supabase_mock=None):
    """워크플로 실행에 필요한 모든 patch 목록 생성.

    Returns:
        (patches_list, mock_claude, mock_supabase)
    """
    mock_claude = claude_side_effect or _make_claude_mock()
    mock_sb = supabase_mock or _make_workflow_supabase_mock()
    mock_pricing = _make_pricing_mock()

    claude_patches = [
        patch("app.services.claude_client.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.rfp_analyze.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.research_gather.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.go_no_go.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.strategy_generate.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.plan_nodes.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.proposal_nodes.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.ppt_nodes.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.submission_nodes.claude_generate", side_effect=mock_claude),
        patch("app.graph.nodes.evaluation_nodes.claude_generate", side_effect=mock_claude),
    ]
    other_patches = [
        patch("app.utils.supabase_client.get_async_client", AsyncMock(return_value=mock_sb)),
        patch("app.services.prompt_registry.get_prompt_for_experiment", side_effect=_mock_get_prompt_for_experiment),
        patch("app.services.prompt_registry.get_active_prompt", side_effect=_mock_get_active_prompt),
        patch("app.services.prompt_tracker.record_usage", side_effect=_mock_record_usage),
    ]
    return claude_patches + other_patches, mock_claude, mock_sb


@pytest.fixture
async def graph_with_mocks():
    """모든 외부 의존성이 mock된 컴파일된 그래프 + ExitStack.

    Returns:
        (graph, exit_stack) — exit_stack은 테스트 종료 시 자동 정리
    """
    from app.graph.graph import build_graph

    patches, _, _ = build_all_patches()
    stack = ExitStack()
    for p in patches:
        stack.enter_context(p)

    graph = build_graph(checkpointer=MemorySaver())
    yield graph

    stack.close()


# ── Resume 헬퍼 ──

def resume_approved(**extra):
    """표준 승인 resume 데이터."""
    data = {"approved": True, "approved_by": "tester", "feedback": ""}
    data.update(extra)
    return data


def resume_go(**extra):
    """Go/No-Go 승인 resume 데이터."""
    data = {"decision": "go", "approved": True, "approved_by": "tester"}
    data.update(extra)
    return data


def resume_rejected(**extra):
    """거부 resume 데이터."""
    data = {"approved": False, "approved_by": "tester", "feedback": "수정 필요"}
    data.update(extra)
    return data
