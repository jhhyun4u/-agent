"""제안서 도메인 응답 스키마."""

from datetime import datetime

from pydantic import BaseModel

from app.models.types import ImpactLevel, LessonCategory, ProposalResult, ProposalStatus


class ProposalListItem(BaseModel):
    """GET /api/proposals 목록 아이템."""

    model_config = {"extra": "ignore"}

    id: str
    title: str | None = None
    status: ProposalStatus = "initialized"
    owner_id: str | None = None
    team_id: str | None = None
    division_id: str | None = None
    org_id: str | None = None
    rfp_filename: str | None = None
    current_phase: str | None = None
    bid_amount: int | None = None
    go_decision: bool = False  # 제안결정 여부
    bid_tracked: bool = True   # 공고 모니터링 표시 여부
    # 공고 연동 정보
    source_bid_no: str | None = None  # 원본 공고번호
    fit_score: float | None = None  # 적합도 점수 (0-100)
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProposalDetail(ProposalListItem):
    """GET /api/proposals/{id} 상세.

    Inherits model_config extra='ignore' from ProposalListItem.
    """

    rfp_content: str | None = None
    rfp_content_truncated: bool = False
    phases_completed: int = 0
    failed_phase: str | None = None
    storage_path_docx: str | None = None
    storage_path_pptx: str | None = None
    storage_path_hwpx: str | None = None
    storage_path_rfp: str | None = None
    storage_upload_failed: bool = False
    win_result: str | None = None
    decision_date: datetime | None = None  # 제안결정 일시
    # 분석 메타데이터
    md_rfp_analysis_path: str | None = None  # RFP 분석 마크다운 경로
    md_notice_path: str | None = None  # 공고문 요약 마크다운 경로
    md_instruction_path: str | None = None  # 과업지시서 마크다운 경로
    notes: str | None = None


class ProposalCreateResponse(BaseModel):
    """POST /api/proposals 응답."""

    proposal_id: str
    title: str | None = None
    status: str = "initialized"
    entry_point: str
    bid_no: str | None = None
    mode: str | None = None


class ProposalResultResponse(BaseModel):
    """GET /api/proposals/{id}/result 응답."""

    id: str
    proposal_id: str
    result: ProposalResult
    final_price: int | None = None
    competitor_count: int | None = None
    ranking: int | None = None
    tech_score: float | None = None
    price_score: float | None = None
    total_score: float | None = None
    feedback_notes: str | None = None
    won_by: str | None = None
    created_at: datetime | None = None


class ProposalTaskResponse(BaseModel):
    """제안 작업 목록 응답."""

    id: str
    proposal_id: str
    assigned_team_id: str
    description: str | None = None
    status: str = "waiting"  # waiting | in_progress | completed | blocked
    priority: str = "normal"  # low | normal | high
    due_date: datetime | None = None
    created_by_id: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class LessonResponse(BaseModel):
    """교훈 응답."""

    id: str
    proposal_id: str
    category: LessonCategory
    title: str
    description: str
    impact: ImpactLevel
    action_items: list[str] = []
    applicable_domains: list[str] = []
    created_at: datetime | None = None
    created_by: str | None = None
