"""Phase 5: 관리자 + 감사 로그 + 대시보드 + 고도화 테스트."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from tests.conftest import make_supabase_mock


def _make_admin_mock(target_user: dict):
    """admin 라우트용 mock — maybe_single()이 단일 dict를 반환."""
    mock_client = AsyncMock()

    class _Chain:
        def select(self, *a, **kw): return self
        def eq(self, *a, **kw): return self
        def update(self, *a, **kw): return self
        def maybe_single(self): return self
        async def execute(self):
            r = MagicMock()
            r.data = target_user
            return r

    mock_client.table = MagicMock(return_value=_Chain())
    return mock_client


# ── 관리자: 사용자 관리 ──

async def test_admin_list_users(client):
    """GET /api/admin/users 사용자 목록 (admin 역할)."""
    resp = await client.get("/api/admin/users")
    assert resp.status_code == 200
    data = resp.json()
    assert "data" in data


async def test_admin_update_role(client):
    """PUT /api/admin/users/{id}/role 역할 변경."""
    mock_sb = _make_admin_mock({"id": "user-002", "org_id": "org-001", "role": "member"})
    with patch("app.api.routes_admin.get_async_client", return_value=mock_sb):
        resp = await client.put("/api/admin/users/user-002/role", json={"role": "lead"})
    assert resp.status_code == 200
    data = resp.json()["data"]
    assert data["role"] == "lead"


async def test_admin_update_invalid_role(client):
    """유효하지 않은 역할 → 400."""
    resp = await client.put("/api/admin/users/user-002/role", json={"role": "superadmin"})
    assert resp.status_code == 400


async def test_admin_update_status(client):
    """PUT /api/admin/users/{id}/status 상태 변경."""
    mock_sb = _make_admin_mock({"id": "user-002", "org_id": "org-001", "status": "active"})
    with patch("app.api.routes_admin.get_async_client", return_value=mock_sb):
        resp = await client.put("/api/admin/users/user-002/status", json={"status": "inactive"})
    assert resp.status_code == 200


async def test_admin_stats(client):
    """GET /api/admin/stats 시스템 통계."""
    resp = await client.get("/api/admin/stats")
    assert resp.status_code == 200
    data = resp.json()
    assert "users" in data
    assert "proposals" in data


# ── 감사 로그 ──

async def test_audit_logs_list(client):
    """GET /api/audit-logs 감사 로그 조회."""
    resp = await client.get("/api/audit-logs?days=7")
    assert resp.status_code == 200
    assert "data" in resp.json()


async def test_audit_logs_export(client):
    """GET /api/audit-logs/export CSV 내보내기."""
    resp = await client.get("/api/audit-logs/export?days=7")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")


# ── 대시보드 ──

async def test_division_dashboard(client):
    """GET /api/dashboard/division 본부장 대시보드."""
    resp = await client.get("/api/dashboard/division")
    assert resp.status_code == 200
    data = resp.json()
    assert "teams" in data
    assert "pending_approvals" in data


async def test_executive_dashboard(client):
    """GET /api/dashboard/executive 경영진 대시보드."""
    resp = await client.get("/api/dashboard/executive")
    assert resp.status_code == 200
    data = resp.json()
    assert "kpi" in data
    assert "by_positioning" in data
    assert "monthly_trends" in data


# ── No-Go 재전환 ──

async def test_reopen_non_cancelled(client):
    """cancelled 아닌 프로젝트 reopen → 400 또는 404 (mock 데이터에 따라)."""
    mock_sb = make_supabase_mock({
        "proposals": [{"id": "p1", "status": "running"}],
    })
    with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb):
        resp = await client.patch("/api/proposals/p1/reopen", json={"reason": "재검토"})
        # mock single()이 빈 데이터 → 404(not found), 또는 실제 데이터 → 400(not cancelled)
        assert resp.status_code in (400, 404)


# ── 역량 DB 인라인 편집 ──

async def test_capability_update_invalid_field(client):
    """허용되지 않은 필드 수정 시도 → 400."""
    resp = await client.put("/api/capabilities/cap-001", json={
        "field": "id",
        "value": "hacked",
    })
    assert resp.status_code == 400


async def test_capability_update_valid_field(client):
    """허용된 필드 수정."""
    resp = await client.put("/api/capabilities/cap-001", json={
        "field": "description",
        "value": "클라우드 네이티브 아키텍처 설계 역량",
    })
    assert resp.status_code == 200


# ── 감사 서비스 ──

async def test_audit_service_log_action():
    """감사 로그 기록 (실패해도 예외 발생 안 함)."""
    from app.services.audit_service import log_action

    mock_sb = make_supabase_mock()
    with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb):
        # 정상 케이스
        await log_action("user-001", "create", "proposal", "p1", {"test": True})

    # 실패 케이스 (예외 삼킴 확인)
    mock_fail = AsyncMock()
    mock_fail.table.side_effect = Exception("DB 연결 실패")
    with patch("app.utils.supabase_client.get_async_client", return_value=mock_fail):
        await log_action("user-001", "create", "proposal", "p1")  # 예외 없이 통과
