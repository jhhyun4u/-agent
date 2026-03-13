"""Phase 3: 산출물 + 알림 + Compliance + DOCX 빌더 테스트."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from tests.conftest import make_supabase_mock


# ── 알림 API ──

async def test_list_notifications(client):
    """GET /api/notifications 목록 조회."""
    resp = await client.get("/api/notifications")
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "unread_count" in data


async def test_mark_notification_read(client):
    """PUT /api/notifications/{id}/read 읽음 처리."""
    resp = await client.put("/api/notifications/noti-001/read")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


async def test_mark_all_read(client):
    """PUT /api/notifications/read-all 전체 읽음."""
    resp = await client.put("/api/notifications/read-all")
    assert resp.status_code == 200


async def test_notification_settings_get(client):
    """GET /api/notifications/settings 설정 조회."""
    resp = await client.get("/api/notifications/settings")
    assert resp.status_code == 200


async def test_notification_settings_update(client):
    """PUT /api/notifications/settings 설정 변경."""
    resp = await client.put("/api/notifications/settings", json={
        "teams": False,
        "in_app": True,
    })
    assert resp.status_code == 200


# ── DOCX 빌더 ──

async def test_docx_builder_import():
    """DOCX 빌더 import + 기본 함수 존재."""
    from app.services.docx_builder import build_docx
    assert callable(build_docx)


# ── Compliance Tracker ──

def test_compliance_tracker_import():
    """ComplianceTracker import 가능."""
    from app.services.compliance_tracker import ComplianceTracker
    assert hasattr(ComplianceTracker, "create_initial")
    assert hasattr(ComplianceTracker, "update_from_strategy")
    assert hasattr(ComplianceTracker, "check_compliance")


# ── Notification Service ──

def test_notification_service_import():
    """알림 서비스 import 가능."""
    from app.services.notification_service import (
        create_notification,
        notify_approval_request,
        notify_ai_complete,
    )
