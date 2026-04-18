from datetime import datetime

from pydantic import BaseModel, field_validator

from app.models.types import (
    EvaluatorReaction,
    ImpactLevel,
    LessonCategory,
    ProposalResult,
    QACategory,
)


class ProjectInput(BaseModel):
    """직접 입력 기반 제안서 생성 요청"""

    project_name: str
    client_name: str
    project_scope: str
    duration: str
    budget: str | None = None
    requirements: list[str] = []
    additional_info: str | None = None


class RFPData(BaseModel):
    """RFP 파싱 결과 구조"""

    title: str = ""
    client_name: str = ""
    project_scope: str = ""
    duration: str = ""
    budget: str | None = None
    requirements: list[str] = []
    evaluation_criteria: list[str] = []
    table_of_contents: list[str] = []
    raw_text: str

    @field_validator("title", "client_name", "project_scope", "duration", mode="before")
    @classmethod
    def coerce_none_to_str(cls, v):
        return v if v is not None else ""


class ProposalSection(BaseModel):
    """제안서 개별 섹션 (v4.0: 하네스 엔지니어링 지원)"""

    title: str
    content: str
    section_id: str | None = None  # 섹션 ID (section_type)
    version: int = 1
    case_type: str | None = None  # "A" | "B" (케이스 분류)
    template_structure: dict | None = None  # 케이스 B용 서식 구조
    self_review_score: dict | None = None  # 자가진단 점수

    # ── v4.0: 하네스 엔지니어링 메타데이터 ──
    harness_score: float | None = None  # 종합 평가 점수 (0~1)
    harness_variant: str | None = None  # "conservative" | "balanced" | "creative"
    harness_improved: bool = False  # 피드백 루프로 개선됨 여부


class ProposalContent(BaseModel):
    """Claude가 생성한 제안서 전체 내용"""

    project_overview: str
    understanding: str
    approach: str
    methodology: str
    schedule: str
    team_composition: str
    expected_outcomes: str
    budget_plan: str | None = None


class ProposalResponse(BaseModel):
    """제안서 생성 API 응답"""

    proposal_id: str
    message: str
    docx_path: str | None = None
    pptx_path: str | None = None
    hwpx_path: str | None = None


# ── Phase 4: 제안 결과 + 교훈 ──


class ProposalResultCreate(BaseModel):
    """제안 결과 등록 (§12-4, Phase 4-2)"""

    result: ProposalResult
    final_price: int | None = None
    competitor_count: int | None = None
    ranking: int | None = None
    tech_score: float | None = None
    price_score: float | None = None
    total_score: float | None = None
    feedback_notes: str | None = None
    won_by: str | None = None


class ProposalResultUpdate(BaseModel):
    """제안 결과 수정"""

    final_price: int | None = None
    competitor_count: int | None = None
    ranking: int | None = None
    tech_score: float | None = None
    price_score: float | None = None
    total_score: float | None = None
    feedback_notes: str | None = None
    won_by: str | None = None


class LessonCreate(BaseModel):
    """교훈 등록 (§20-5, Phase 4-5)"""

    category: LessonCategory
    title: str
    description: str
    impact: ImpactLevel
    action_items: list[str] = []
    applicable_domains: list[str] = []


# ── PSM-16: Q&A 기록 ──

# 하위 호환: 기존 코드에서 QA_CATEGORIES로 참조하는 곳 지원
QA_CATEGORIES = QACategory


class QARecordCreate(BaseModel):
    """Q&A 기록 생성."""

    question: str
    answer: str
    category: QACategory = "general"
    evaluator_reaction: EvaluatorReaction | None = None
    memo: str | None = None


class QARecordUpdate(BaseModel):
    """Q&A 기록 수정."""

    question: str | None = None
    answer: str | None = None
    category: QACategory | None = None
    evaluator_reaction: EvaluatorReaction | None = None
    memo: str | None = None


class QARecordResponse(BaseModel):
    """Q&A 기록 응답."""

    id: str
    proposal_id: str
    question: str
    answer: str
    category: QACategory
    evaluator_reaction: EvaluatorReaction | None = None
    memo: str | None = None
    content_library_id: str | None = None
    created_at: datetime | None = None
    created_by: str | None = None


class QASearchResult(BaseModel):
    """Q&A 검색 결과."""

    id: str
    proposal_id: str
    question: str
    answer: str
    category: QACategory
    evaluator_reaction: EvaluatorReaction | None = None
    memo: str | None = None
    created_at: datetime | None = None
    similarity: float | None = None
    proposal_name: str | None = None
    client: str | None = None
