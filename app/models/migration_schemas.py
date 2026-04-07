"""
Migration Service Pydantic 스키마

마이그레이션 배치 및 스케줄 관련 데이터 모델
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


# ===== Request/Response 스키마 =====

class MigrationBatch(BaseModel):
    """배치 작업 기록"""
    id: UUID
    batch_name: str
    status: str  # pending|processing|completed|failed|partial_failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    scheduled_at: datetime
    total_documents: int
    processed_documents: int
    failed_documents: int
    skipped_documents: int
    batch_type: str
    source_system: str
    error_message: Optional[str] = None
    error_details: Optional[dict] = None
    created_by: UUID
    updated_at: datetime

    @property
    def duration_minutes(self) -> Optional[int]:
        """배치 처리 시간 (분)"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() / 60)
        return None

    @property
    def success_rate(self) -> float:
        """성공률 (0-100)"""
        if self.total_documents == 0:
            return 0.0
        return (self.processed_documents / self.total_documents) * 100

    model_config = ConfigDict(from_attributes=True)


class MigrationSchedule(BaseModel):
    """스케줄 설정"""
    id: UUID
    enabled: bool
    cron_expression: str
    schedule_name: str
    schedule_type: str
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    last_batch_id: Optional[UUID] = None
    timeout_seconds: int
    max_retries: int
    retry_delay_seconds: int
    notify_on_success: bool
    notify_on_failure: bool
    notification_channels: List[str]
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class MigrationTriggerRequest(BaseModel):
    """배치 즉시 시작 요청"""
    batch_type: str = Field(default="manual", description="배치 유형: manual|monthly|incremental")
    include_failed_docs: bool = Field(default=False, description="이전 실패 문서 재처리")
    document_limit: Optional[int] = Field(default=None, description="최대 처리 문서 수")


class BatchListParams(BaseModel):
    """배치 목록 조회 파라미터"""
    status: Optional[str] = Field(default=None, description="배치 상태 필터")
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)
    sort_by: str = Field(default="scheduled_at", description="정렬 기준: scheduled_at|started_at|created_by")
    order: str = Field(default="desc", description="정렬 순서: asc|desc")


class MigrationScheduleUpdate(BaseModel):
    """스케줄 업데이트 요청"""
    enabled: Optional[bool] = None
    cron_expression: Optional[str] = None
    timeout_seconds: Optional[int] = None
    max_retries: Optional[int] = None
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
    notification_channels: Optional[List[str]] = None


class BatchResult(BaseModel):
    """배치 처리 결과"""
    batch_id: UUID
    status: str
    processed: int
    failed: int
    errors: List[str] = Field(default_factory=list)
    duration_seconds: Optional[int] = None


class BatchListResponse(BaseModel):
    """배치 목록 조회 응답"""
    total: int
    limit: int
    offset: int
    batches: List[MigrationBatch]


class MigrationTriggerResponse(BaseModel):
    """배치 시작 응답 (202 Accepted)"""
    batch_id: Optional[UUID] = None
    batch_name: str
    status: str
    scheduled_at: datetime
    estimated_duration_minutes: int = Field(default=45)
    message: str = "Migration batch started in background"


class IntranetDocument(BaseModel):
    """인트라넷 문서"""
    path: str
    filename: str
    modified_date: datetime
    size_bytes: int
    project_id: Optional[UUID] = None
    doc_type: Optional[str] = None


class DocumentProcessResult(BaseModel):
    """단일 문서 처리 결과"""
    status: str  # success|failed|skipped
    file: str
    error: Optional[str] = None
    chunks_created: int = 0
    duration_seconds: Optional[float] = None
