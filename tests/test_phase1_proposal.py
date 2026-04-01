"""Phase 1: 제안서 CRUD + 워크플로 API 테스트."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from tests.conftest import MockQueryBuilder


# ── Mock 헬퍼 ──

def setup_proposal_table_mock(supabase_mock, proposals_data=None):
    """proposal 테이블 mock 설정."""
    if proposals_data is None:
        proposals_data = []

    original_table = supabase_mock.table

    def _table(name):
        if name == "proposals":
            return MockQueryBuilder(proposals_data)
        return original_table(name)

    supabase_mock.table = _table


def setup_bid_announcements_mock(supabase_mock, bid_data):
    """bid_announcements 테이블 mock 설정."""
    original_table = supabase_mock.table

    def _table(name):
        if name == "bid_announcements":
            return MockQueryBuilder([bid_data])
        elif name == "proposals":
            return MockQueryBuilder([])
        return original_table(name)

    supabase_mock.table = _table


# ── 프로젝트 생성 (from-bid) ──

async def test_create_from_bid(client):
    """POST /api/proposals/from-bid 공고번호로 생성."""
    supabase_mock = client._supabase_mock
    bid_data = {
        "bid_no": "20260310001",
        "bid_title": "클라우드 ERP 구축",
        "agency": "한국산업은행",
        "budget_amount": 500000000,
        "deadline_date": "2026-06-30",
        "content_text": "## 과업 설명서\n사업명: 클라우드 ERP 구축",
        "raw_data": {},
        "decision": "Go",
        "md_rfp_analysis_path": None,
        "md_notice_path": None,
        "md_instruction_path": None,
    }

    setup_bid_announcements_mock(supabase_mock, bid_data)

    resp = await client.post("/api/proposals/from-bid", json={
        "bid_no": "20260310001",
    })
    assert resp.status_code == 201, f"Got {resp.status_code}: {resp.json()}"
    data = resp.json()
    assert data["entry_point"] == "from_bid"
    assert data["bid_no"] == "20260310001"
    assert data["status"] == "대기중"


async def test_create_from_bid_missing_field(client):
    """POST /api/proposals/from-bid 필수 필드 누락 → 422."""
    resp = await client.post("/api/proposals/from-bid", json={})
    assert resp.status_code == 422


async def test_create_from_bid_wrong_decision(client):
    """POST /api/proposals/from-bid 결정 = No-Go → 400 에러."""
    supabase_mock = client._supabase_mock
    bid_data = {
        "bid_no": "20260310002",
        "bid_title": "테스트 공고",
        "decision": "No-Go",  # Go가 아니면 실패
        "content_text": "공고문",
        "raw_data": {},
        "md_rfp_analysis_path": None,
        "md_notice_path": None,
        "md_instruction_path": None,
    }

    setup_bid_announcements_mock(supabase_mock, bid_data)

    resp = await client.post("/api/proposals/from-bid", json={"bid_no": "20260310002"})
    assert resp.status_code == 500  # G2BServiceError → 500
    assert "Go" in resp.json().get("message", "")


async def test_create_from_rfp(client):
    """POST /api/proposals/from-rfp RFP 파일로 생성."""
    resp = await client.post("/api/proposals/from-rfp", json={
        "title": "테스트 제안",
        "rfp_content": "## 과업 설명\n테스트 RFP 내용",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["entry_point"] == "from_rfp"
    assert data["title"] == "테스트 제안"
    assert data["status"] == "대기중"


async def test_create_from_rfp_missing_field(client):
    """POST /api/proposals/from-rfp 필수 필드 누락 → 422."""
    resp = await client.post("/api/proposals/from-rfp", json={})
    assert resp.status_code == 422


# ── 프로젝트 조회 ──

async def test_list_proposals(client):
    """GET /api/proposals 목록 조회."""
    resp = await client.get("/api/proposals")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data
    assert "total" in data["meta"]


async def test_list_proposals_with_scope(client):
    """GET /api/proposals?scope=my 스코프 필터."""
    resp = await client.get("/api/proposals?scope=my")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data


async def test_get_proposal_success(client):
    """GET /api/proposals/{id} 제안서 상세 조회."""
    supabase_mock = client._supabase_mock
    proposal_data = {
        "id": "prop-001",
        "title": "클라우드 ERP",
        "status": "대기중",
        "owner_id": "user-001",
        "created_at": "2026-04-01T10:00:00Z",
        "rfp_content": "과업 설명",
    }

    setup_proposal_table_mock(supabase_mock, [proposal_data])

    resp = await client.get("/api/proposals/prop-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == "prop-001"
    assert data["title"] == "클라우드 ERP"


async def test_get_proposal_not_found(client):
    """GET /api/proposals/{id} 존재하지 않는 프로젝트."""
    supabase_mock = client._supabase_mock
    setup_proposal_table_mock(supabase_mock, [])  # 빈 데이터

    resp = await client.get("/api/proposals/nonexistent-id")
    assert resp.status_code == 404


async def test_delete_proposal_success(client):
    """DELETE /api/proposals/{id} 제안서 삭제."""
    supabase_mock = client._supabase_mock
    proposal_data = {
        "id": "prop-del-001",
        "title": "삭제할 제안",
        "status": "대기중",
    }

    setup_proposal_table_mock(supabase_mock, [proposal_data])

    resp = await client.delete("/api/proposals/prop-del-001")
    assert resp.status_code == 204  # No Content


async def test_delete_proposal_not_found(client):
    """DELETE /api/proposals/{id} 없는 제안 삭제 → 404."""
    supabase_mock = client._supabase_mock
    setup_proposal_table_mock(supabase_mock, [])

    resp = await client.delete("/api/proposals/nonexistent-id")
    assert resp.status_code == 404


# ── 워크플로 상태 ──

async def test_workflow_history(client):
    """GET /api/proposals/{id}/history 이력 조회 (그래프 mock)."""
    mock_graph = AsyncMock()
    mock_graph.aget_state_history = MagicMock(return_value=aiter_empty())

    with patch("app.api.routes_workflow._get_graph", return_value=mock_graph):
        resp = await client.get("/api/proposals/test-id/history")
        assert resp.status_code == 200
        data = resp.json()
        assert "history" in data


async def aiter_empty():
    """빈 async iterator."""
    return
    yield  # noqa: make it an async generator
