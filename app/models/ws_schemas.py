"""WebSocket 메시지 스키마 (§26)

클라이언트-서버 간 WebSocket 통신을 위한 Pydantic 모델.
"""

from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field


# ── 메시지 타입 ──────────────────────────────────────────────────────

MessageType = Literal[
    "proposal_status",      # 제안서 상태 변경
    "monthly_trends",       # 월별 추이 업데이트
    "team_performance",     # 팀 성과 지표
    "notification",         # 알림
    "heartbeat",           # 하트비트 (ping/pong)
    "error",               # 에러 메시지
]

ChannelType = Literal[
    "team",        # team:<team_id>
    "division",    # division:<division_id>
    "company",     # company:<org_id>
]


# ── 서버 → 클라이언트 (Push) ──────────────────────────────────────────

class WsMessage(BaseModel):
    """서버에서 클라이언트로 보내는 메시지"""
    
    type: MessageType = Field(..., description="메시지 타입")
    channel: str = Field(..., description="채널 (team:<id> / division:<id> / company:<id>)")
    data: dict[str, Any] = Field(default_factory=dict, description="메시지 페이로드")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat(), description="ISO 타임스탬프")
    
    model_config = {"json_schema_extra": {
        "examples": [
            {
                "type": "proposal_status",
                "channel": "team:team-abc",
                "data": {
                    "proposal_id": "prop-123",
                    "old_status": "in_progress",
                    "new_status": "on_hold",
                    "title": "용역과제명",
                },
                "timestamp": "2026-04-16T20:30:00.123456",
            },
            {
                "type": "heartbeat",
                "channel": "team:team-abc",
                "data": {},
                "timestamp": "2026-04-16T20:30:00.123456",
            }
        ]
    }}


# ── 클라이언트 → 서버 (Subscribe/Unsubscribe) ──────────────────────────

class WsSubscribeMessage(BaseModel):
    """클라이언트가 채널 구독/구독취소를 요청하는 메시지"""
    
    action: Literal["subscribe", "unsubscribe"] = Field(..., description="구독/구독취소")
    channel: str = Field(..., description="채널 (team:<id> / division:<id> / company:<id>)")
    
    model_config = {"json_schema_extra": {
        "examples": [
            {"action": "subscribe", "channel": "division:div-xyz"},
            {"action": "unsubscribe", "channel": "team:team-abc"},
        ]
    }}


# ── 데이터 페이로드 ──────────────────────────────────────────────────

class ProposalStatusUpdate(BaseModel):
    """제안서 상태 변경 알림"""
    
    proposal_id: str
    old_status: str | None = None
    new_status: str
    title: str | None = None
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class MonthlyTrendsUpdate(BaseModel):
    """월별 추이 업데이트 신호"""
    
    team_id: str | None = None
    division_id: str | None = None
    org_id: str | None = None
    message: str = "월별 추이 데이터 갱신 필요"


class TeamPerformanceUpdate(BaseModel):
    """팀 성과 지표 업데이트"""
    
    team_id: str
    total: int
    won: int
    lost: int
    win_rate: float
    updated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class NotificationPayload(BaseModel):
    """알림 메시지"""
    
    notification_id: str
    user_id: str
    type: str  # "approval_request", "approval_result", "ai_complete", etc.
    title: str
    message: str
    link: str | None = None
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class HeartbeatPayload(BaseModel):
    """하트비트/Keep-alive"""
    
    client_timestamp: str | None = None
    server_timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ErrorPayload(BaseModel):
    """에러 메시지"""
    
    code: str
    message: str
    details: dict[str, Any] | None = None


# ── 내부용 메타데이터 ──────────────────────────────────────────────────

class WsConnectionMeta(BaseModel):
    """WebSocket 연결 메타데이터 (서버 내부용)"""
    
    user_id: str
    org_id: str
    team_id: str | None = None
    division_id: str | None = None
    role: str  # "admin", "executive", "director", "lead", "member"
    channels: set[str] = Field(default_factory=set)
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        arbitrary_types_allowed = True
