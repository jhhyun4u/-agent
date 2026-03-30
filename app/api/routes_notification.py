"""
알림 API (§12-10)

GET  /api/notifications          — 내 알림 목록
PUT  /api/notifications/{id}/read — 읽음 처리
PUT  /api/notifications/read-all  — 전체 읽음
GET  /api/notifications/settings  — 알림 설정 조회
PUT  /api/notifications/settings  — 알림 설정 변경
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.api.response import ok, ok_list
from app.models.auth_schemas import CurrentUser
from app.models.common import StatusResponse
from app.models.notification_schemas import NotificationListResponse, NotificationSettingsResponse
from app.utils.supabase_client import get_async_client

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


_EMAIL_SETTING_KEYS = [
    "email_monitoring", "email_proposal", "email_bidding", "email_learning",
]


class NotificationSettingsUpdate(BaseModel):
    teams: bool | None = None
    in_app: bool | None = None
    email_monitoring: bool | None = None
    email_proposal: bool | None = None
    email_bidding: bool | None = None
    email_learning: bool | None = None


@router.get("", response_model=NotificationListResponse)
async def list_notifications(
    is_read: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    user: CurrentUser = Depends(get_current_user),
):
    """내 알림 목록 (최신순)."""
    client = await get_async_client()
    query = (
        client.table("notifications")
        .select("id, proposal_id, type, title, body, link, is_read, teams_sent, created_at")
        .eq("user_id", user.id)
        .order("created_at", desc=True)
        .range(skip, skip + limit - 1)
    )
    if is_read is not None:
        query = query.eq("is_read", is_read)

    try:
        result = await query.execute()
    except Exception as e:
        if "PGRST205" in str(e):
            return ok_list([], total=0)
        raise

    # 안 읽은 알림 수
    unread = await (
        client.table("notifications")
        .select("id", count="exact")
        .eq("user_id", user.id)
        .eq("is_read", False)
        .execute()
    )

    return {
        "items": result.data or [],
        "unread_count": unread.count or 0,
    }


@router.put("/{notification_id}/read", response_model=StatusResponse)
async def mark_as_read(notification_id: str, user: CurrentUser = Depends(get_current_user)):
    """알림 읽음 처리."""
    client = await get_async_client()
    await (
        client.table("notifications")
        .update({"is_read": True})
        .eq("id", notification_id)
        .eq("user_id", user.id)
        .execute()
    )
    return ok(None, message="읽음 처리 완료")


@router.put("/read-all", response_model=StatusResponse)
async def mark_all_as_read(user: CurrentUser = Depends(get_current_user)):
    """전체 읽음 처리."""
    client = await get_async_client()
    await (
        client.table("notifications")
        .update({"is_read": True})
        .eq("user_id", user.id)
        .eq("is_read", False)
        .execute()
    )
    return ok(None, message="전체 읽음 처리 완료")


@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(user: CurrentUser = Depends(get_current_user)):
    """알림 설정 조회."""
    client = await get_async_client()
    result = await (
        client.table("users")
        .select("notification_settings")
        .eq("id", user.id)
        .single()
        .execute()
    )
    from app.config import settings as app_settings
    ns = result.data.get("notification_settings", {"teams": True, "in_app": True}) if result.data else {"teams": True, "in_app": True}
    ns["email_enabled"] = app_settings.email_enabled
    return ns


@router.put("/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    body: NotificationSettingsUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    """알림 설정 변경."""
    client = await get_async_client()

    # 기존 설정 조회
    current = await (
        client.table("users")
        .select("notification_settings")
        .eq("id", user.id)
        .single()
        .execute()
    )
    settings = current.data.get("notification_settings", {"teams": True, "in_app": True}) if current.data else {"teams": True, "in_app": True}

    # 변경 사항 적용
    if body.teams is not None:
        settings["teams"] = body.teams
    if body.in_app is not None:
        settings["in_app"] = body.in_app
    for key in _EMAIL_SETTING_KEYS:
        val = getattr(body, key, None)
        if val is not None:
            settings[key] = val

    await (
        client.table("users")
        .update({"notification_settings": settings})
        .eq("id", user.id)
        .execute()
    )

    from app.config import settings as app_settings
    settings["email_enabled"] = app_settings.email_enabled
    return settings
