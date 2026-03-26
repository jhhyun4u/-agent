"""알림 도메인 응답 스키마."""

from datetime import datetime

from pydantic import BaseModel


class NotificationItem(BaseModel):
    """알림 단건."""

    id: str
    proposal_id: str | None = None
    type: str
    title: str
    body: str | None = None
    link: str | None = None
    is_read: bool = False
    teams_sent: bool = False
    created_at: datetime | None = None


class NotificationListResponse(BaseModel):
    """GET /api/notifications 응답."""

    items: list[NotificationItem] = []
    unread_count: int = 0


class NotificationSettingsResponse(BaseModel):
    """GET /api/notifications/settings 응답."""

    teams: bool = True
    in_app: bool = True
    email_monitoring: bool = False
    email_proposal: bool = False
    email_bidding: bool = False
    email_learning: bool = False
    email_enabled: bool = False  # 서버 이메일 기능 활성화 상태 (읽기 전용)
