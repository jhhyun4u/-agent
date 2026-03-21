"""
사용자·조직 Pydantic 스키마 (Phase 0)
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


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
    teams_webhook_url: Optional[str] = None


class TeamUpdate(BaseModel):
    name: Optional[str] = None
    teams_webhook_url: Optional[str] = None


class TeamResponse(BaseModel):
    id: str
    division_id: str
    name: str
    teams_webhook_url: Optional[str] = None
    created_at: datetime


# ── 사용자 ──

class UserCreate(BaseModel):
    """관리자가 사용자 사전 등록 시 사용"""
    email: str
    name: str
    role: str = Field(default="member", pattern="^(member|lead|director|executive|admin)$")
    team_id: Optional[str] = None
    division_id: Optional[str] = None
    org_id: str
    azure_ad_oid: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = Field(default=None, pattern="^(member|lead|director|executive|admin)$")
    team_id: Optional[str] = None
    division_id: Optional[str] = None
    notification_settings: Optional[dict] = None


class UserCreateWithPassword(BaseModel):
    """관리자가 사용자 등록 시 사용 (Supabase Auth 계정 동시 생성)"""
    email: str
    name: str
    role: str = Field(default="member", pattern="^(member|lead|director|executive|admin)$")
    team_id: Optional[str] = None
    division_id: Optional[str] = None
    org_id: str
    password: Optional[str] = None  # 미입력 시 임시 비밀번호 자동 생성


class PasswordResetRequest(BaseModel):
    new_password: Optional[str] = None  # 미입력 시 임시 비밀번호 자동 생성


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8)


class BulkCreateResult(BaseModel):
    total: int
    success_count: int
    failed_count: int
    results: list[dict]


class UserResponse(BaseModel):
    id: str
    email: str
    name: str
    role: str
    team_id: Optional[str] = None
    division_id: Optional[str] = None
    org_id: str
    status: str = "active"
    must_change_password: bool = False
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int


# ── 프로젝트 참여자 ──

class ParticipantAdd(BaseModel):
    user_id: str
    role_in_project: str = Field(default="member", pattern="^(member|section_lead)$")


class ParticipantResponse(BaseModel):
    user_id: str
    role_in_project: str
    assigned_at: datetime
    user_name: Optional[str] = None
    user_email: Optional[str] = None


# ── 결재 위임 ──

class DelegationCreate(BaseModel):
    delegate_id: str
    start_date: str  # YYYY-MM-DD
    end_date: str
    reason: Optional[str] = None


class DelegationResponse(BaseModel):
    id: str
    delegator_id: str
    delegate_id: str
    start_date: str
    end_date: str
    reason: Optional[str] = None
    is_active: bool
    created_at: datetime
