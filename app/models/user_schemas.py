"""
사용자·조직 Pydantic 스키마 (Phase 0)
"""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.types import ProjectRole, UserRole, UserStatus


# ── 조직 ──

class OrganizationCreate(BaseModel):
    name: str


class OrganizationResponse(BaseModel):
    id: str
    name: str
    created_at: datetime


# ── 본부 ──

class DivisionCreate(BaseModel):
    name: str
    org_id: str


class DivisionResponse(BaseModel):
    id: str
    org_id: str
    name: str
    created_at: datetime


# ── 팀 ──

class TeamCreate(BaseModel):
    name: str
    division_id: str
    teams_webhook_url: str | None = None


class TeamUpdate(BaseModel):
    name: str | None = None
    teams_webhook_url: str | None = None


class TeamResponse(BaseModel):
    id: str
    division_id: str
    name: str
    teams_webhook_url: str | None = None
    created_at: datetime


# ── 사용자 ──

class UserCreate(BaseModel):
    """관리자가 사용자 사전 등록 시 사용"""
    email: str
    name: str
    role: UserRole = "member"
    team_id: str | None = None
    division_id: str | None = None
    org_id: str
    azure_ad_oid: str | None = None


class UserUpdate(BaseModel):
    name: str | None = None
    role: UserRole | None = None
    team_id: str | None = None
    division_id: str | None = None
    notification_settings: dict | None = None


class UserCreateWithPassword(BaseModel):
    """관리자가 사용자 등록 시 사용 (Supabase Auth 계정 동시 생성)"""
    email: str
    name: str
    role: UserRole = "member"
    team_id: str | None = None
    division_id: str | None = None
    org_id: str
    password: str | None = None  # 미입력 시 임시 비밀번호 자동 생성


class PasswordResetRequest(BaseModel):
    new_password: str | None = None  # 미입력 시 임시 비밀번호 자동 생성


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def validate_password_complexity(cls, v: str) -> str:
        """H-5: 비밀번호 복잡성 — 대문자+소문자+숫자+특수문자 중 3종 이상."""
        checks = [
            any(c.isupper() for c in v),
            any(c.islower() for c in v),
            any(c.isdigit() for c in v),
            any(not c.isalnum() for c in v),
        ]
        if sum(checks) < 3:
            raise ValueError("비밀번호는 대문자, 소문자, 숫자, 특수문자 중 3종 이상 포함해야 합니다.")
        return v


class BulkCreateResult(BaseModel):
    total: int
    success_count: int
    failed_count: int
    results: list[dict]


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: UserRole
    team_id: str | None = None
    division_id: str | None = None
    org_id: str
    status: UserStatus = "active"
    must_change_password: bool = False
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int


# ── 프로젝트 참여자 ──

class ParticipantAdd(BaseModel):
    user_id: str
    role_in_project: ProjectRole = "member"


class ParticipantResponse(BaseModel):
    user_id: str
    role_in_project: str
    assigned_at: datetime
    user_name: str | None = None
    user_email: str | None = None


# ── 결재 위임 ──

class DelegationCreate(BaseModel):
    delegate_id: str
    start_date: str  # YYYY-MM-DD
    end_date: str
    reason: str | None = None


class DelegationResponse(BaseModel):
    id: str
    delegator_id: str
    delegate_id: str
    start_date: str
    end_date: str
    reason: str | None = None
    is_active: bool
    created_at: datetime
