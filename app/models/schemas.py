from typing import Literal

from pydantic import BaseModel, field_validator


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
    """제안서 개별 섹션"""

    title: str
    content: str


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

    result: Literal["won", "lost", "void"]
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

    category: Literal["strategy", "pricing", "team", "technical", "process", "other"]
    title: str
    description: str
    impact: Literal["high", "medium", "low"]
    action_items: list[str] = []
    applicable_domains: list[str] = []
