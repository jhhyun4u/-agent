"""인증 관련 스키마."""

from datetime import datetime

from pydantic import BaseModel

from app.models.types import UserRole, UserStatus


class CurrentUser(BaseModel):
    """JWT 인증 후 반환되는 사용자 정보.

    deps.py의 get_current_user() 반환 타입.
    DB users 테이블의 SELECT * 결과와 호환.
    """

    id: str
    email: str
    name: str
    role: UserRole = "member"
    org_id: str | None = None
    team_id: str | None = None
    division_id: str | None = None
    status: UserStatus = "active"
    azure_ad_oid: str | None = None
    notification_settings: dict | None = None
    must_change_password: bool = False
    deactivated_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class AuthMessageResponse(BaseModel):
    """인증 관련 메시지 응답."""

    message: str
