"""Phase 8: 미커버 API 테스트 (calendar, resources, stats, templates)

레거시 라우트가 user.id (dot-access)를 사용하므로 DotDict mock 필요.
"""

import pytest
from unittest.mock import patch
from httpx import AsyncClient, ASGITransport

from tests.conftest import _get_test_app, make_supabase_mock
from app.api.deps import get_current_user

app = _get_test_app()


class DotDict(dict):
    """dict + attribute access."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)


MOCK_USER = DotDict(
    id="user-001", email="admin@tenopa.com", name="관리자",
    role="admin", team_id="team-001", division_id="div-001",
    org_id="org-001", status="active",
)


@pytest.fixture
async def legacy_client():
    """레거시 라우트용 클라이언트 (DotDict user mock)."""
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    mock_sb = make_supabase_mock()
    with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac
    app.dependency_overrides.pop(get_current_user, None)


# ══════════════════════════════════════
# Calendar API
# ══════════════════════════════════════

async def test_calendar_list(legacy_client):
    """GET /api/calendar → 200."""
    mock_sb = make_supabase_mock(table_data={"rfp_calendar": []})
    with patch("app.api.routes_calendar.get_async_client", return_value=mock_sb):
        resp = await legacy_client.get("/api/calendar")
    assert resp.status_code == 200


async def test_calendar_create(legacy_client):
    """POST /api/calendar → 200/201."""
    mock_sb = make_supabase_mock()
    with patch("app.api.routes_calendar.get_async_client", return_value=mock_sb):
        resp = await legacy_client.post("/api/calendar", json={
            "title": "ERP 구축 RFP",
            "agency": "행안부",
            "deadline": "2026-05-01",
        })
    assert resp.status_code in (200, 201)


# ══════════════════════════════════════
# Resources API (섹션 라이브러리)
# ══════════════════════════════════════

async def test_sections_list(legacy_client):
    """GET /api/resources/sections → 200."""
    mock_sb = make_supabase_mock(table_data={
        "sections": [],
        "team_members": [{"user_id": "user-001", "team_id": "team-001"}],
    })
    with patch("app.api.routes_resources.get_async_client", return_value=mock_sb):
        resp = await legacy_client.get("/api/resources/sections")
    assert resp.status_code == 200


# ══════════════════════════════════════
# Stats API (수주율 통계)
# ══════════════════════════════════════

async def test_stats_win_rate(legacy_client):
    """GET /api/stats/win-rate → 200."""
    mock_sb = make_supabase_mock(table_data={"proposals": []})
    with patch("app.api.routes_stats.get_async_client", return_value=mock_sb):
        resp = await legacy_client.get("/api/stats/win-rate?scope=personal")
    assert resp.status_code == 200


# ══════════════════════════════════════
# Form Templates API
# ══════════════════════════════════════

async def test_templates_list(legacy_client):
    """GET /api/form-templates → 200."""
    mock_sb = make_supabase_mock(table_data={
        "form_templates": [],
        "team_members": [],
    })
    with patch("app.api.routes_templates.get_async_client", return_value=mock_sb):
        resp = await legacy_client.get("/api/form-templates")
    assert resp.status_code == 200
