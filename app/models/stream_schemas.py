"""
3-Stream 병행 업무 Pydantic 스키마
"""

from typing import Literal

from pydantic import BaseModel


# ── Stream Progress ──

StreamName = Literal["proposal", "bidding", "documents"]
StreamStatus = Literal["not_started", "in_progress", "blocked", "completed", "error"]


class StreamProgressResponse(BaseModel):
    """단일 스트림 진행 상태."""
    stream: StreamName
    status: StreamStatus
    progress_pct: int = 0
    current_phase: str | None = None
    blocked_reason: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    metadata: dict = {}


class StreamsOverview(BaseModel):
    """3-스트림 통합 현황."""
    streams: list[StreamProgressResponse]
    convergence_ready: bool = False
    missing_streams: list[str] = []


class FinalSubmitRequest(BaseModel):
    """최종 제출 요청."""
    confirm: bool = True


class FinalSubmitResponse(BaseModel):
    """최종 제출 결과."""
    success: bool
    message: str
    submission_gate_status: str


# ── Submission Documents ──

DocCategory = Literal["proposal", "qualification", "certification", "financial", "other"]
DocFormat = Literal["HWPX", "PDF", "원본", "사본", "자유"]
DocStatus = Literal[
    "pending", "assigned", "in_progress", "uploaded",
    "verified", "rejected", "not_applicable", "expired",
]
DocPriority = Literal["high", "medium", "low"]


class SubmissionDocumentResponse(BaseModel):
    """제출서류 단건 응답."""
    id: str
    proposal_id: str
    doc_type: str
    doc_category: DocCategory
    required_format: DocFormat
    required_copies: int = 1
    source: str = "manual"
    status: DocStatus
    assignee_id: str | None = None
    deadline: str | None = None
    priority: DocPriority = "medium"
    notes: str | None = None
    file_path: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    file_format: str | None = None
    uploaded_by: str | None = None
    uploaded_at: str | None = None
    verified_by: str | None = None
    verified_at: str | None = None
    rejection_reason: str | None = None
    sort_order: int = 0
    rfp_reference: str | None = None
    created_at: str | None = None


# 별칭: routes_submission_docs.py에서 짧은 이름으로 import
SubmissionDocResponse = SubmissionDocumentResponse


class SubmissionDocCreate(BaseModel):
    """제출서류 수동 추가."""
    doc_type: str
    doc_category: DocCategory = "other"
    required_format: DocFormat = "자유"
    required_copies: int = 1
    priority: DocPriority = "medium"
    notes: str | None = None
    assignee_id: str | None = None
    deadline: str | None = None
    rfp_reference: str | None = None


class SubmissionDocUpdate(BaseModel):
    """제출서류 상태/담당 변경."""
    status: DocStatus | None = None
    assignee_id: str | None = None
    priority: DocPriority | None = None
    notes: str | None = None
    deadline: str | None = None
    rejection_reason: str | None = None


class SubmissionDocVerify(BaseModel):
    """검증 완료 요청."""
    pass


class ReadinessItem(BaseModel):
    """사전 점검 항목."""
    doc_id: str
    doc_type: str
    status: str
    issue: str | None = None


class ReadinessResponse(BaseModel):
    """사전 제출 점검 결과."""
    ready: bool
    total: int
    completed: int
    issues: list[ReadinessItem] = []


# ── Org Document Templates ──

class OrgDocTemplateResponse(BaseModel):
    """조직 공통 서류 응답."""
    id: str
    org_id: str
    doc_type: str
    doc_category: DocCategory
    required_format: str | None = None
    file_path: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    auto_include: bool = True
    notes: str | None = None
    created_at: str | None = None


class OrgDocTemplateCreate(BaseModel):
    """조직 공통 서류 등록/갱신."""
    doc_type: str
    doc_category: DocCategory = "qualification"
    required_format: str | None = None
    valid_from: str | None = None
    valid_until: str | None = None
    auto_include: bool = True
    notes: str | None = None


# ── Bidding Stream ──

class BidPriceAdjustRequest(BaseModel):
    """워크플로 완료 후 가격 조정."""
    adjusted_price: int
    reason: str


class BidPriceAdjustResponse(BaseModel):
    """가격 조정 결과."""
    success: bool
    new_price: int
    event_type: str
    message: str
