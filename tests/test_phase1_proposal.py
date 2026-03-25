"""Phase 1: 제안서 CRUD + 워크플로 API 테스트."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from tests.conftest import make_supabase_mock


# ── 프로젝트 생성 (from-bid) ──

async def test_create_from_bid(client):
    """POST /api/proposals/from-bid 공고번호로 생성."""
    resp = await client.post("/api/proposals/from-bid", json={
        "bid_no": "20260310001",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["entry_point"] == "from_bid"
    assert data["bid_no"] == "20260310001"
    assert data["status"] == "대기중"


async def test_create_from_bid_missing_field(client):
    """POST /api/proposals/from-bid 필수 필드 누락 → 422."""
    resp = await client.post("/api/proposals/from-bid", json={})
    assert resp.status_code == 422


# ── 프로젝트 조회 ──

async def test_list_proposals(client):
    """GET /api/proposals 목록 조회."""
    resp = await client.get("/api/proposals")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data


async def test_list_proposals_with_scope(client):
    """GET /api/proposals?scope=my 스코프 필터."""
    resp = await client.get("/api/proposals?scope=my")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data


async def test_get_proposal_not_found(client):
    """GET /api/proposals/{id} 존재하지 않는 프로젝트."""
    resp = await client.get("/api/proposals/nonexistent-id")
    # mock은 빈 데이터 반환 → PropNotFoundError → 404
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
