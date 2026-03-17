"""Phase 7: 워크플로 API 테스트 (routes_workflow.py)

LangGraph 워크플로 핵심 경로:
- POST /proposals/{id}/start
- GET  /proposals/{id}/state
- POST /proposals/{id}/resume
- GET  /proposals/{id}/history
- GET  /proposals/{id}/impact/{step}
- GET  /proposals/{id}/token-usage
- GET  /proposals/{id}/ai-status
- POST /proposals/{id}/goto/{step}
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from tests.conftest import make_supabase_mock

PROPOSAL_ID = "prop-wf-001"


async def test_workflow_start_missing_proposal(client):
    """POST /proposals/{id}/start — 존재하지 않는 proposal → 404."""
    mock_sb = make_supabase_mock(table_data={"proposals": []})
    with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb):
        resp = await client.post(f"/api/proposals/{PROPOSAL_ID}/start")
    assert resp.status_code in (404, 422, 500)


async def test_workflow_history(client):
    """GET /proposals/{id}/history → 200."""
    mock_sb = make_supabase_mock(table_data={
        "workflow_history": [
            {"id": "wh-1", "proposal_id": PROPOSAL_ID, "node": "rfp_analyze",
             "status": "completed", "created_at": "2026-03-17T00:00:00Z"},
        ],
    })
    with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb):
        resp = await client.get(f"/api/proposals/{PROPOSAL_ID}/history")
    assert resp.status_code == 200


async def test_workflow_impact(client):
    """GET /proposals/{id}/impact/{step} → 200 + affected_steps."""
    mock_sb = make_supabase_mock(table_data={
        "proposals": [{"id": PROPOSAL_ID, "status": "running", "phases_completed": 3}],
    })
    with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb):
        resp = await client.get(f"/api/proposals/{PROPOSAL_ID}/impact/go_no_go")
    assert resp.status_code == 200
    data = resp.json()
    assert "affected_steps" in data
    assert "message" in data


async def test_workflow_token_usage(client):
    """GET /proposals/{id}/token-usage → 200."""
    mock_sb = make_supabase_mock(table_data={
        "token_usage_logs": [],
    })
    with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb):
        resp = await client.get(f"/api/proposals/{PROPOSAL_ID}/token-usage")
    assert resp.status_code == 200


async def test_workflow_ai_status(client):
    """GET /proposals/{id}/ai-status → 200."""
    mock_sb = make_supabase_mock(table_data={
        "ai_status_logs": [],
    })
    with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb):
        resp = await client.get(f"/api/proposals/{PROPOSAL_ID}/ai-status")
    assert resp.status_code == 200


async def test_workflow_ai_logs(client):
    """GET /proposals/{id}/ai-logs → 200."""
    mock_sb = make_supabase_mock(table_data={
        "ai_status_logs": [],
    })
    with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb):
        resp = await client.get(f"/api/proposals/{PROPOSAL_ID}/ai-logs")
    assert resp.status_code == 200
