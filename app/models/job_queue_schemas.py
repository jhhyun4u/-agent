"""
STEP 8: 비동기 Job Queue 시스템 - Pydantic 스키마

Job 생명주기: PENDING → RUNNING → SUCCESS/FAILED/CANCELLED
재시도: FAILED → PENDING (max_retries 초과 시 DLQ)
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict


# ============================================
# Enums
# ============================================

class JobStatus(str, Enum):
    """Job 생명주기 상태"""

    PENDING = "pending"      # 큐 대기 중
    RUNNING = "running"      # 처리 중
    SUCCESS = "success"      # 완료 (성공)
    FAILED = "failed"        # 실패 (최대 재시도 초과)
    CANCELLED = "cancelled"  # 취소됨 (사용자)


class JobType(str, Enum):
    """작업 분류"""

    STEP4A_DIAGNOSIS = "step4a_diagnosis"        # STEP 4A: 정확도 검증
    STEP4A_REGENERATE = "step4a_regenerate"      # STEP 4A: 섹션 재작성
    STEP4B_PRICING = "step4b_pricing"            # STEP 4B: 입찰가 산정
    STEP5A_PPTX = "step5a_pptx"                  # STEP 5A: PPT 생성
    STEP5B_SUBMISSION = "step5b_submission"      # STEP 5B: 제출서류
    STEP6_EVALUATION = "step6_evaluation"        # STEP 6: 모의평가


class JobPriority(int, Enum):
    """우선도 (낮은 수일수록 높은 우선도)"""

    HIGH = 0
    NORMAL = 1
    LOW = 2


class JobEventType(str, Enum):
    """Job 이벤트 타입"""

    CREATED = "created"
    STARTED = "started"
    PROGRESS = "progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRIED = "retried"


# ============================================
# Core Models
# ============================================

class Job(BaseModel):
    """비동기 작업 단위 (DB 모델)"""

    model_config = ConfigDict()

    id: UUID
    proposal_id: UUID
    step: str = Field(..., pattern="^(4a|4b|5a|5b|6)$")  # "4a", "4b", "5a", "5b", "6"
    type: JobType
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL

    # 입력
    payload: dict = Field(
        default_factory=dict,
        description="작업 입력 파라미터 (< 1MB)"
    )

    # 출력 & 에러
    result: Optional[dict] = None
    error: Optional[str] = None

    # 재시도
    retries: int = Field(default=0, ge=0)
    max_retries: int = Field(default=3, ge=1)

    # 타이밍
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None

    # 추적
    created_by: UUID
    assigned_worker_id: Optional[str] = None  # "worker-1", "worker-2" 등

    # 태그
    tags: dict = Field(default_factory=dict)  # e.g., {"section_id": "s1", ...}

    # 메타데이터
    updated_at: Optional[datetime] = None


# ============================================
# Request/Response Schemas
# ============================================

class JobCreateRequest(BaseModel):
    """Job 생성 요청"""

    proposal_id: UUID
    type: JobType
    payload: dict = Field(default_factory=dict)
    priority: JobPriority = JobPriority.NORMAL
    max_retries: int = Field(default=3, ge=1, le=10)
    tags: dict = Field(default_factory=dict)


class JobStatusResponse(BaseModel):
    """Job 상태 조회 응답"""

    id: UUID
    status: JobStatus
    progress: float = Field(default=0.0, ge=0.0, le=100.0)  # 진행률
    retries: int
    max_retries: int
    duration_seconds: Optional[float] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    queue_position: Optional[int] = None  # 큐 내 위치 (pending 상태일 때만)


class JobResultResponse(BaseModel):
    """Job 결과 조회 응답 (SUCCESS 시)"""

    id: UUID
    result: dict
    duration_seconds: float
    completed_at: datetime
    created_at: datetime


class JobListResponse(BaseModel):
    """Job 목록 조회 응답"""

    total: int = Field(..., ge=0)
    page: int = Field(..., ge=1)
    limit: int = Field(..., ge=1, le=100)
    items: list[JobStatusResponse] = Field(default_factory=list)


class JobCancelResponse(BaseModel):
    """Job 취소 응답"""

    cancelled: bool
    job_id: UUID
    message: str


class JobRetryResponse(BaseModel):
    """Job 수동 재시도 응답"""

    job_id: UUID
    status: JobStatus
    retry_attempt: int


# ============================================
# Metrics & Events
# ============================================

class JobMetric(BaseModel):
    """Job 성과 메트릭"""

    id: UUID
    job_id: UUID
    step: str
    type: str
    status: str  # "success", "failed"
    duration_seconds: float
    memory_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    worker_id: Optional[str] = None
    recorded_at: datetime


class JobMetricsAggregation(BaseModel):
    """Job 메트릭 집계 (대시보드용)"""

    step: str
    total: int = 0
    success_count: int = 0
    failed_count: int = 0
    success_rate: float = 0.0  # 0.0~1.0
    avg_duration_seconds: float = 0.0
    p95_duration_seconds: float = 0.0
    p99_duration_seconds: float = 0.0


class JobEvent(BaseModel):
    """Job 이벤트 (이벤트 로그)"""

    id: UUID
    job_id: UUID
    event_type: JobEventType
    details: dict = Field(default_factory=dict)
    occurred_at: datetime


class JobEventLog(BaseModel):
    """Job 이벤트 로그 조회 응답"""

    job_id: UUID
    events: list[JobEvent] = Field(default_factory=list)
    total: int = 0


# ============================================
# DLQ (Dead Letter Queue)
# ============================================

class DLQItem(BaseModel):
    """Dead Letter Queue 아이템"""

    job_id: UUID
    job_type: JobType
    error: str
    failed_at: datetime
    retries_exhausted: int
    last_error_detail: Optional[str] = None


class DLQResponse(BaseModel):
    """DLQ 조회 응답"""

    total: int = 0
    items: list[DLQItem] = Field(default_factory=list)


# ============================================
# WebSocket Messages
# ============================================

class JobStatusMessage(BaseModel):
    """WebSocket: Job 상태 메시지"""

    type: str = "status"
    job_id: UUID
    status: JobStatus
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    timestamp: datetime


class JobCompletionMessage(BaseModel):
    """WebSocket: Job 완료 메시지"""

    type: str = "completion"
    job_id: UUID
    status: JobStatus  # success, failed, cancelled
    result: Optional[dict] = None
    error: Optional[str] = None
    duration_seconds: float
    timestamp: datetime


class JobErrorMessage(BaseModel):
    """WebSocket: Job 에러 메시지"""

    type: str = "error"
    job_id: UUID
    error: str
    message: str
    timestamp: datetime


class JobHeartbeatMessage(BaseModel):
    """WebSocket: Heartbeat 메시지"""

    type: str = "heartbeat"
    job_id: UUID
    status: JobStatus
    timestamp: datetime


# ============================================
# Query Filters
# ============================================

class JobListFilter(BaseModel):
    """Job 목록 필터링"""

    proposal_id: Optional[UUID] = None
    status: Optional[JobStatus] = None
    step: Optional[str] = None
    type: Optional[JobType] = None
    created_by: Optional[UUID] = None
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    order_by: str = Field(default="created_at", pattern="^(created_at|status|priority)$")
    order_direction: str = Field(default="desc", pattern="^(asc|desc)$")


# ============================================
# Errors
# ============================================

class JobNotFoundError(BaseModel):
    """Job을 찾을 수 없음"""

    detail: str = "Job not found"


class JobInvalidStateError(BaseModel):
    """Job 상태가 유효하지 않음"""

    detail: str = "Invalid job state for operation"


class JobCancelError(BaseModel):
    """Job 취소 불가"""

    detail: str = "Cannot cancel job in current state"


class JobRetryError(BaseModel):
    """Job 재시도 불가"""

    detail: str = "Job does not exist in DLQ or already completed"


__all__ = [
    # Enums
    "JobStatus",
    "JobType",
    "JobPriority",
    "JobEventType",
    # Core
    "Job",
    # Requests/Responses
    "JobCreateRequest",
    "JobStatusResponse",
    "JobResultResponse",
    "JobListResponse",
    "JobCancelResponse",
    "JobRetryResponse",
    # Metrics & Events
    "JobMetric",
    "JobMetricsAggregation",
    "JobEvent",
    "JobEventLog",
    # DLQ
    "DLQItem",
    "DLQResponse",
    # WebSocket
    "JobStatusMessage",
    "JobCompletionMessage",
    "JobErrorMessage",
    "JobHeartbeatMessage",
    # Filters
    "JobListFilter",
    # Errors
    "JobNotFoundError",
    "JobInvalidStateError",
    "JobCancelError",
    "JobRetryError",
]
