"""알림 도메인 응답 스키마."""

from datetime import datetime

from pydantic import BaseModel


class NotificationItem(BaseModel):
    """알림 단건."""

    id: str
    user_id: str
    type: str
    title: str
    body: str | None = None
    link: str | None = None
    is_read: bool = False
    created_at: datetime | None = None


class NotificationListResponse(BaseModel):
    """GET /api/notifications 응답."""

    items: list[NotificationItem] = []
    unread_count: int = 0


class NotificationSettingsResponse(BaseModel):
    """GET /api/notifications/settings 응답."""

    teams: bool = True
    in_app: bool = True
