"""제안결정 워크플로우 테스트: 공고 모니터링 → 제안 프로젝트 생성 + 분석 메타데이터 연동."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tests.conftest import MockQueryBuilder
import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)


def setup_bid_announcements_with_metadata(supabase_mock, bid_data):
    """적합도 점수 & 분석 메타데이터가 포함된 bid_announcements mock 설정."""
    original_table = supabase_mock.table

    def _table(name):
        if name == "bid_announcements":
            return MockQueryBuilder([bid_data])
        elif name == "proposals":
            return MockQueryBuilder([])
        elif name == "search_results":
            return MockQueryBuilder([])
        return original_table(name)

    supabase_mock.table = _table


@pytest.mark.asyncio
async def test_proposal_decision_with_metadata(client, caplog):
    """제안결정: bid_announcements에서 메타데이터를 proposals로 연동.

    흐름:
    1. 공고 모니터링에서 공고 선택 (bid_announcements)
    2. "제안결정" 클릭 → POST /api/proposals/from-bid
    3. 새 제안 프로젝트 생성
    4. source_bid_no, fit_score, md_*_path 포함 확인 (로그에서)
    """
    supabase_mock = client._supabase_mock

    # Mock 공고 데이터 (적합도 점수 & 분석 메타데이터 포함)
    bid_data = {
        "id": "bid-001",
        "bid_no": "20260410001",
        "bid_title": "Cloud Migration",
        "agency": "Korea Development Bank",
        "budget_amount": 800000000,
        "deadline_date": "2026-07-15",
        "fit_score": 85.5,  # ✅ 적합도 점수
        "source_bid_no": "20260410001",
        # ✅ 분석 메타데이터 경로
        "md_rfp_analysis_path": "proposals/bid-001/rfp_analysis.md",
        "md_notice_path": "proposals/bid-001/notice_summary.md",
        "md_instruction_path": "proposals/bid-001/instruction.md",
        "raw_data": {
            "content_text": "## Cloud Migration Project"
        }
    }

    setup_bid_announcements_with_metadata(supabase_mock, bid_data)

    # Mock: Supabase Storage에서 마크다운 파일 다운로드
    mock_analysis = "# RFP Analysis\n\nKey requirements: Cloud migration".encode('utf-8')
    mock_notice = "# Notice Summary\n\nBudget: 800M".encode('utf-8')
    mock_instruction = "# Task Instructions\n\nSchedule: 6 months".encode('utf-8')

    with patch("app.api.routes_proposal.get_rls_client") as mock_get_rls:
        with patch("app.utils.supabase_client.get_async_client") as mock_get_storage:
            # RLS 클라이언트 mock
            mock_rls = AsyncMock()
            mock_rls.table = supabase_mock.table
            mock_get_rls.return_value = mock_rls

            # Storage 클라이언트 mock
            mock_storage_client = MagicMock()  # Non-async object
            mock_storage_ref = AsyncMock()
            mock_storage_client.storage.from_.return_value = mock_storage_ref

            # Storage download mock
            mock_storage_ref.download = AsyncMock(side_effect=[mock_analysis, mock_notice, mock_instruction])

            mock_get_storage.return_value = mock_storage_client

            # POST /api/proposals/from-bid 요청
            with caplog.at_level(logging.INFO):
                response = await client.post(
                    "/api/proposals/from-bid",
                    json={
                        "bid_no": "20260410001",
                        "mode": "from_bid"
                    }
                )

    # ✅ 검증 1: 상태 코드 201 Created
    assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"

    data = response.json()

    # ✅ 검증 2: 응답에 필수 필드 포함
    assert "proposal_id" in data, "proposal_id not in response"
    assert "title" in data, "title not in response"
    assert data["status"] == "initialized", f"Expected status=initialized, got {data.get('status')}"

    # ✅ 검증 3: 로그에서 메타데이터 저장 확인
    log_text = caplog.text

    # source_bid_no가 저장되었는지 확인
    assert "'source_bid_no': '20260410001'" in log_text, \
        "source_bid_no not saved in INSERT log"

    # fit_score가 저장되었는지 확인
    assert "'fit_score': 85.5" in log_text, \
        "fit_score not saved in INSERT log"

    # rfp_content에 분석 마크다운이 통합되었는지 확인
    assert "# RFP Analysis" in log_text, \
        "RFP Analysis content not in rfp_content"
    assert "# Notice Summary" in log_text, \
        "Notice Summary content not in rfp_content"
    assert "# Task Instructions" in log_text, \
        "Task Instructions content not in rfp_content"

    # go_decision = True 확인
    assert "'go_decision': True" in log_text, \
        "go_decision not True in INSERT log"

    # bid_tracked = False 확인
    assert "'bid_tracked': False" in log_text, \
        "bid_tracked not False in INSERT log"

    print(f"""
    ✅ 제안결정 워크플로우 테스트 통과
    - Proposal ID: {data['proposal_id']}
    - Title: {data['title']}
    - Source Bid: 20260410001
    - Fit Score: 85.5%
    - Analysis Metadata: Saved
    - Go Decision: True
    - Markdown Integration: Complete
    """)


@pytest.mark.asyncio
async def test_proposal_decision_fallback_to_raw_data(client, caplog):
    """분석 메타데이터 파일이 없을 때 raw_data.content_text로 fallback."""
    supabase_mock = client._supabase_mock

    # 분석 메타데이터 경로 없음 (legacy data)
    bid_data = {
        "id": "bid-002",
        "bid_no": "20260420002",
        "bid_title": "System Improvement",
        "agency": "Ministry of SMEs",
        "budget_amount": 300000000,
        "deadline_date": "2026-08-01",
        "fit_score": 65.0,
        # ✅ 메타데이터 경로 없음
        "raw_data": {
            "content_text": "## System Improvement Project\nKey features: UI/UX improvement, Performance optimization"
        }
    }

    setup_bid_announcements_with_metadata(supabase_mock, bid_data)

    with patch("app.api.routes_proposal.get_rls_client") as mock_get_rls:
        with patch("app.utils.supabase_client.get_async_client") as mock_get_storage:
            mock_rls = AsyncMock()
            mock_rls.table = supabase_mock.table
            mock_get_rls.return_value = mock_rls

            mock_storage_client = AsyncMock()
            mock_get_storage.return_value = mock_storage_client

            with caplog.at_level(logging.INFO):
                response = await client.post(
                    "/api/proposals/from-bid",
                    json={
                        "bid_no": "20260420002",
                        "mode": "from_bid"
                    }
                )

    # ✅ 검증 1: 상태 코드 201 Created
    assert response.status_code == 201

    data = response.json()
    log_text = caplog.text

    # ✅ 검증 2: raw_data.content_text가 사용되었는지 확인
    assert "raw_data content_text" in log_text, \
        "raw_data.content_text fallback not logged"

    # ✅ 검증 3: fit_score는 여전히 저장됨
    assert "'fit_score': 65.0" in log_text, \
        "fit_score not saved in fallback case"

    # ✅ 검증 4: rfp_content에 raw_data가 포함됨
    assert "## System Improvement Project" in log_text, \
        "System Improvement Project content not in rfp_content"

    print(f"""
    ✅ Fallback 테스트 통과
    - Proposal ID: {data['proposal_id']}
    - Source Bid: 20260420002
    - Fit Score: 65.0%
    - Content Fallback: raw_data.content_text
    - Status: Success
    """)


def test_list_proposals_select_includes_metadata():
    """list_proposals 엔드포인트의 SELECT 쿼리에 새로운 메타데이터 필드 포함 확인.

    검증:
    - routes_proposal.py의 base_cols에 5개 새로운 필드 포함
      - source_bid_no
      - fit_score
      - md_rfp_analysis_path
      - md_notice_path
      - md_instruction_path
    """
    # routes_proposal.py 파일 읽기
    routes_file = Path("c:\\project\\tenopa proposer\\-agent-master\\app\\api\\routes_proposal.py")
    content = routes_file.read_text(encoding='utf-8')

    # base_cols 변수 검색
    # line 472: base_cols = "id, title, ..., source_bid_no, fit_score, ..."
    assert "source_bid_no" in content, "source_bid_no not found in routes_proposal.py"
    assert "fit_score" in content, "fit_score not found in routes_proposal.py"
    assert "md_rfp_analysis_path" in content, "md_rfp_analysis_path not found in routes_proposal.py"
    assert "md_notice_path" in content, "md_notice_path not found in routes_proposal.py"
    assert "md_instruction_path" in content, "md_instruction_path not found in routes_proposal.py"

    # 이 필드들이 list_proposals 함수 내에 포함되어 있는지 확인
    # 정확한 위치: @router.get("") 함수의 base_cols 정의
    list_proposals_match = re.search(
        r'@router\.get\(""\).*?async def list_proposals.*?base_cols\s*=\s*"([^"]+)"',
        content,
        re.DOTALL
    )

    assert list_proposals_match is not None, "Could not find list_proposals function or base_cols"
    base_cols = list_proposals_match.group(1)

    # ✅ 검증: 모든 새로운 필드가 base_cols에 포함
    for field in ["source_bid_no", "fit_score", "md_rfp_analysis_path", "md_notice_path", "md_instruction_path"]:
        assert field in base_cols, f"{field} not in base_cols: {base_cols}"

    print(f"""
    ✅ SELECT 쿼리 메타데이터 필드 테스트 통과
    - list_proposals의 base_cols:
      {base_cols}
    - 포함된 새로운 필드:
      ✅ source_bid_no (원본 공고번호)
      ✅ fit_score (적합도 점수)
      ✅ md_rfp_analysis_path (RFP 분석 문서 경로)
      ✅ md_notice_path (공고문 요약 경로)
      ✅ md_instruction_path (과업지시서 경로)
    - Status: ✅ Complete
    """)
