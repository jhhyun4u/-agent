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
from app.utils.supabase_client import get_async_client

router = APIRouter(prefix="/api/notifications", tags=["notifications"])


class NotificationSettingsUpdate(BaseModel):
    teams: bool | None = None
    in_app: bool | None = None


@router.get("")
async def list_notifications(
    is_read: bool | None = None,
    skip: int = 0,
    limit: int = 20,
    user=Depends(get_current_user),
):
    """내 알림 목록 (최신순)."""
    client = await get_async_client()
    query = (
        client.table("notifications")
        .select("id, proposal_id, type, title, body, link, is_read, teams_sent, created_at")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .range(skip, skip + limit - 1)
    )
    if is_read is not None:
        query = query.eq("is_read", is_read)

    try:
        result = await query.execute()
    except Exception as e:
        if "PGRST205" in str(e):
            return {"items": [], "unread_count": 0}
        raise

    # 안 읽은 알림 수
    unread = await (
        client.table("notifications")
        .select("id", count="exact")
        .eq("user_id", user["id"])
        .eq("is_read", False)
        .execute()
    )

    return {
        "items": result.data or [],
        "unread_count": unread.count or 0,
    }


@router.put("/{notification_id}/read")
async def mark_as_read(notification_id: str, user=Depends(get_current_user)):
    """알림 읽음 처리."""
    client = await get_async_client()
    await (
        client.table("notifications")
        .update({"is_read": True})
        .eq("id", notification_id)
        .eq("user_id", user["id"])
        .execute()
    )
    return {"status": "ok"}


@router.put("/read-all")
async def mark_all_as_read(user=Depends(get_current_user)):
    """전체 읽음 처리."""
    client = await get_async_client()
    await (
        client.table("notifications")
        .update({"is_read": True})
        .eq("user_id", user["id"])
        .eq("is_read", False)
        .execute()
    )
    return {"status": "ok"}


@router.get("/settings")
async def get_notification_settings(user=Depends(get_current_user)):
    """알림 설정 조회."""
    client = await get_async_client()
    result = await (
        client.table("users")
        .select("notification_settings")
        .eq("id", user["id"])
        .single()
        .execute()
    )
    return result.data.get("notification_settings", {"teams": True, "in_app": True}) if result.data else {"teams": True, "in_app": True}


@router.put("/settings")
async def update_notification_settings(
    body: NotificationSettingsUpdate,
    user=Depends(get_current_user),
):
    """알림 설정 변경."""
    client = await get_async_client()

    # 기존 설정 조회
    current = await (
        client.table("users")
        .select("notification_settings")
        .eq("id", user["id"])
        .single()
        .execute()
    )
    settings = current.data.get("notification_settings", {"teams": True, "in_app": True}) if current.data else {"teams": True, "in_app": True}

    # 변경 사항 적용
    if body.teams is not None:
        settings["teams"] = body.teams
    if body.in_app is not None:
        settings["in_app"] = body.in_app

    await (
        client.table("users")
        .update({"notification_settings": settings})
        .eq("id", user["id"])
        .execute()
    )
    return settings
