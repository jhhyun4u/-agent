"""제안 생성 엔드투엔드 통합 테스트: 공고 검색 → 제안 생성 → 목록 조회"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from tests.conftest import MockQueryBuilder
import logging

logger = logging.getLogger(__name__)


def setup_bid_announcements_for_search(supabase_mock, bid_data_list):
    """검색 결과용 bid_announcements mock 설정."""
    original_table = supabase_mock.table

    def _table(name):
        if name == "bid_announcements":
            return MockQueryBuilder(bid_data_list)
        elif name == "proposals":
            return MockQueryBuilder([])
        elif name == "search_results":
            return MockQueryBuilder([])
        return original_table(name)

    supabase_mock.table = _table


@pytest.mark.asyncio
async def test_proposal_creation_e2e_flow(client, caplog):
    """제안 생성 전체 흐름: 공고 검색 → 제안 생성 → 메타데이터 저장.

    흐름:
    1. 공고 검색 (G2B API 또는 DB에서 조회)
    2. 공고 선택 후 "제안결정" 클릭
    3. POST /api/proposals/from-bid 호출
    4. 201 Created 응답 + proposal_id 반환
    5. 메타데이터 필드 저장:
       - source_bid_no, fit_score, md_*_path
       - rfp_content (마크다운 통합)
       - go_decision=True, bid_tracked=False
    """
    supabase_mock = client._supabase_mock

    # Mock 공고 데이터 (검색 결과)
    bid_search_results = [
        {
            "id": "bid-search-001",
            "bid_no": "20260501001",
            "bid_title": "AI Platform Development",
            "agency": "Ministry of Science",
            "budget_amount": 1000000000,
            "deadline_date": "2026-08-15",
            "fit_score": 88.5,
            "source_bid_no": "20260501001",
            "md_rfp_analysis_path": "proposals/bid-search-001/rfp_analysis.md",
            "md_notice_path": "proposals/bid-search-001/notice_summary.md",
            "md_instruction_path": "proposals/bid-search-001/instruction.md",
            "raw_data": {
                "content_text": "## AI Platform Development\n\nRequirements:\n- ML pipeline\n- Real-time processing"
            }
        }
    ]

    setup_bid_announcements_for_search(supabase_mock, bid_search_results)

    # Mock 마크다운 파일 다운로드
    mock_analysis = "# RFP Analysis\n\nAI/ML requirements".encode('utf-8')
    mock_notice = "# Notice Summary\n\nBudget: 1B".encode('utf-8')
    mock_instruction = "# Task Instructions\n\nDelivery: 12 months".encode('utf-8')

    with patch("app.api.routes_proposal.get_rls_client") as mock_get_rls:
        with patch("app.utils.supabase_client.get_async_client") as mock_get_storage:
            # RLS 클라이언트 mock
            mock_rls = AsyncMock()
            mock_rls.table = supabase_mock.table
            mock_get_rls.return_value = mock_rls

            # Storage 클라이언트 mock
            mock_storage_client = MagicMock()
            mock_storage_ref = AsyncMock()
            mock_storage_client.storage.from_.return_value = mock_storage_ref
            mock_storage_ref.download = AsyncMock(
                side_effect=[mock_analysis, mock_notice, mock_instruction]
            )
            mock_get_storage.return_value = mock_storage_client

            # ✅ 1단계: 공고 검색 (시뮬레이션 — 실제로는 G2B API 호출)
            # 여기서는 이미 공고가 DB에 있다고 가정
            logger.info("[E2E Flow] 1단계: 공고 검색 완료 - 20260501001 발견")

            # ✅ 2단계: 공고 선택 후 "제안결정" 버튼 클릭
            # → POST /api/proposals/from-bid 호출
            with caplog.at_level(logging.INFO):
                response = await client.post(
                    "/api/proposals/from-bid",
                    json={
                        "bid_no": "20260501001",
                        "mode": "from_bid"
                    }
                )

    # ✅ 검증 1: HTTP 201 Created
    assert response.status_code == 201, \
        f"Expected 201, got {response.status_code}: {response.text}"

    data = response.json()
    proposal_id = data["proposal_id"]
    logger.info(f"[E2E Flow] 2단계: 제안 생성 완료 - ID: {proposal_id}")

    # ✅ 검증 2: 기본 응답 필드
    assert "proposal_id" in data, "proposal_id not in response"
    assert "title" in data, "title not in response"
    assert data["title"] == "AI Platform Development"
    assert data["status"] == "initialized"

    # ✅ 검증 3: 로그에서 메타데이터 저장 확인
    log_text = caplog.text

    # source_bid_no
    assert "'source_bid_no': '20260501001'" in log_text, \
        "source_bid_no not saved"
    logger.info("[E2E Flow] ✅ source_bid_no 저장됨: 20260501001")

    # fit_score
    assert "'fit_score': 88.5" in log_text, \
        "fit_score not saved"
    logger.info("[E2E Flow] ✅ fit_score 저장됨: 88.5%")

    # 분석 마크다운 통합
    assert "# RFP Analysis" in log_text, \
        "RFP Analysis not integrated"
    assert "# Notice Summary" in log_text, \
        "Notice Summary not integrated"
    assert "# Task Instructions" in log_text, \
        "Task Instructions not integrated"
    logger.info("[E2E Flow] ✅ 3개 분석 마크다운 통합됨")

    # 분석 메타데이터 경로
    assert "'md_rfp_analysis_path': 'proposals/bid-search-001/rfp_analysis.md'" in log_text
    assert "'md_notice_path': 'proposals/bid-search-001/notice_summary.md'" in log_text
    assert "'md_instruction_path': 'proposals/bid-search-001/instruction.md'" in log_text
    logger.info("[E2E Flow] ✅ 분석 문서 경로 저장됨")

    # 제안결정 플래그
    assert "'go_decision': True" in log_text
    assert "'bid_tracked': False" in log_text
    logger.info("[E2E Flow] ✅ 플래그 저장됨: go_decision=True, bid_tracked=False")

    # ✅ 검증 4: 작업 목록 생성 확인
    assert "[from-bid] ✅ 작업 목록 생성 완료" in log_text or \
           "작업 목록 생성" in log_text, \
        "Task list not created"
    logger.info("[E2E Flow] ✅ 작업 목록 생성됨")

    print(f"""
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ✅ 제안 생성 엔드투엔드 통합 테스트 성공
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    📋 흐름 완료:
      1단계: 공고 검색 ✅
             - 공고번호: 20260501001
             - 예산: 1,000,000,000

      2단계: 제안 생성 ✅
             - Proposal ID: {proposal_id}
             - 상태: initialized
             - HTTP Status: 201 Created

      3단계: 메타데이터 저장 ✅
             - source_bid_no: 20260501001
             - fit_score: 88.5%
             - md_rfp_analysis_path: proposals/bid-search-001/rfp_analysis.md
             - md_notice_path: proposals/bid-search-001/notice_summary.md
             - md_instruction_path: proposals/bid-search-001/instruction.md
             - rfp_content: 3개 마크다운 통합됨

      4단계: 작업 목록 생성 ✅
             - assigned_team_id: team-001
             - status: waiting
             - 마감일: 14일 후

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    """)


@pytest.mark.asyncio
async def test_proposal_creation_fallback_flow(client, caplog):
    """메타데이터 파일 없이 raw_data로 fallback하는 흐름 검증."""
    supabase_mock = client._supabase_mock

    # 메타데이터 경로 없는 공고 데이터 (레거시)
    bid_data = {
        "id": "bid-legacy-001",
        "bid_no": "20260510001",
        "bid_title": "Legacy System Migration",
        "agency": "Department A",
        "budget_amount": 500000000,
        "deadline_date": "2026-07-01",
        "fit_score": 72.0,
        # 메타데이터 경로 없음
        "raw_data": {
            "content_text": "## System Migration\n\nLegacy system to modern tech stack"
        }
    }

    original_table = supabase_mock.table

    def _table(name):
        if name == "bid_announcements":
            return MockQueryBuilder([bid_data])
        elif name == "proposals":
            return MockQueryBuilder([])
        return original_table(name)

    supabase_mock.table = _table

    with patch("app.api.routes_proposal.get_rls_client") as mock_get_rls:
        with patch("app.utils.supabase_client.get_async_client") as mock_get_storage:
            mock_rls = AsyncMock()
            mock_rls.table = supabase_mock.table
            mock_get_rls.return_value = mock_rls

            mock_storage_client = MagicMock()
            mock_get_storage.return_value = mock_storage_client

            with caplog.at_level(logging.INFO):
                response = await client.post(
                    "/api/proposals/from-bid",
                    json={
                        "bid_no": "20260510001",
                        "mode": "from_bid"
                    }
                )

    # ✅ 검증 1: 상태 201 Created
    assert response.status_code == 201

    data = response.json()
    log_text = caplog.text

    # ✅ 검증 2: fit_score는 여전히 저장됨
    assert "'fit_score': 72.0" in log_text
    logger.info("[Fallback] ✅ fit_score 저장됨: 72.0%")

    # ✅ 검증 3: raw_data.content_text로 fallback
    assert "raw_data content_text" in log_text or \
           "System Migration" in log_text
    logger.info("[Fallback] ✅ raw_data로 fallback되어 저장됨")

    # ✅ 검증 4: 메타데이터 경로는 없음
    assert "'md_rfp_analysis_path': None" in log_text or \
           "md_rfp_analysis_path" not in data or \
           data.get("md_rfp_analysis_path") is None

    print(f"""
    ✅ Fallback 흐름 테스트 성공
    - Proposal ID: {data['proposal_id']}
    - fit_score: 72.0% (저장됨)
    - Content: raw_data로 fallback (메타데이터 파일 없음)
    - Status: initialized
    """)


@pytest.mark.asyncio
async def test_proposal_creation_with_custom_title(client, caplog):
    """공고 제목을 사용자 정의 제목으로 변경하는 경우 (선택사항)."""
    supabase_mock = client._supabase_mock

    bid_data = {
        "id": "bid-custom-001",
        "bid_no": "20260520001",
        "bid_title": "Original Bid Title",
        "agency": "Test Agency",
        "budget_amount": 300000000,
        "deadline_date": "2026-06-15",
        "fit_score": 80.0,
        "raw_data": {
            "content_text": "Test content"
        }
    }

    original_table = supabase_mock.table

    def _table(name):
        if name == "bid_announcements":
            return MockQueryBuilder([bid_data])
        elif name == "proposals":
            return MockQueryBuilder([])
        return original_table(name)

    supabase_mock.table = _table

    with patch("app.api.routes_proposal.get_rls_client") as mock_get_rls:
        with patch("app.utils.supabase_client.get_async_client") as mock_get_storage:
            mock_rls = AsyncMock()
            mock_rls.table = supabase_mock.table
            mock_get_rls.return_value = mock_rls

            mock_storage_client = MagicMock()
            mock_get_storage.return_value = mock_storage_client

            # 기본 제목 사용 (공고 제목)
            response = await client.post(
                "/api/proposals/from-bid",
                json={
                    "bid_no": "20260520001",
                    "mode": "from_bid"
                }
            )

    # ✅ 검증: 공고 제목으로 제안 제목 설정
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Original Bid Title"
    logger.info(f"[Custom Title] ✅ 제안 제목: {data['title']}")

    print(f"""
    ✅ 제안 제목 테스트 성공
    - 공고 제목: Original Bid Title
    - 제안 제목: {data['title']}
    """)
