"""
ProposalState: 제안서 전체 상태 (v2.0 호환, v3.0 확장).

이 State는 Supervisor State 내에 포함되어 있고,
각 Sub-agent의 결과가 이곳에 병합됩니다.
"""

from typing import TypedDict, Literal
from pydantic import BaseModel, Field
from datetime import datetime


class ProposalState(TypedDict):
    """제안서 전체 상태"""

    # ═══ 기본 정보 ═══
    proposal_id: str
    """이 제안서의 고유 ID"""

    created_at: datetime
    """생성 시간"""

    updated_at: datetime
    """마지막 수정 시간"""

    # ═══ RFP 데이터 ═══
    rfp_document: str
    """원본 RFP 문서 (텍스트)"""

    rfp_analysis: dict
    """RFP 분석 결과"""

    # RFP 분석의 주요 필드
    rfp_title: str | None = None
    client_name: str | None = None
    project_scope: str | None = None
    duration: str | None = None
    budget_range: str | None = None
    evaluation_criteria: list[dict] = []
    evaluation_method: str | None = None  # "경쟁입찰", "수의계약", etc.
    mandatory_qualifications: list[dict] = []
    hidden_intent: str | None = None
    client_language_profile: dict = {}

    # ═══ 회사 정보 ═══
    company_profile: dict
    """회사 정보 및 현황"""

    company_name: str | None = None
    company_id: str | None = None
    existing_capabilities: list[dict] = []

    # ═══ 전략 데이터 ═══
    competitive_analysis: dict
    """경쟁 환경 분석 (경쟁 회사, 위협 요소 등)"""

    strategy: dict
    """제안 전략 및 포지셔닝"""

    core_message: str | None = None
    differentiators: list[str] = []
    attack_strategy: str | None = None

    # ═══ 배점 및 인력 ═══
    section_allocations: list[dict] = []
    """섹션별 배점 배분"""

    personnel_assignments: list[dict] = []
    """배정된 인력 목록"""

    # ═══ 섹션 내용 ═══
    sections: dict[str, dict] = {}
    """생성된 섹션들 {section_id: {name, content, pages, status}}"""

    # ═══ 품질 관리 ═══
    quality_score: float = 0.0
    """종합 품질 점수 (0.0 ~ 1.0)"""

    quality_feedback: list[dict] = []
    """품질 비평 항목들"""

    revision_round: int = 0
    """수정 라운드 횟수"""

    revision_history: list[dict] = []
    """수정 이력"""

    # ═══ 최종 문서 ═══
    executive_summary: str | None = None
    """요약문"""

    final_sections: dict[str, dict] = {}
    """최종 편집된 섹션들"""

    export_format: Literal["docx", "hwp", "pdf"] = "docx"
    """export 포맷"""

    export_path: str | None = None
    """생성된 문서 경로"""

    # ═══ 메타 정보 ═══
    total_pages: int = 0
    """전체 페이지 수"""

    token_usage: dict = {}
    """토큰 사용량 로그"""

    cost_estimate: float = 0.0
    """비용 추정"""


class SectionDraft(BaseModel):
    """개별 섹션 드래프트"""

    section_id: str
    section_name: str
    content: str
    target_pages: float
    actual_pages: float = 0.0
    word_count: int = 0
    token_count: int = 0
    status: Literal["pending", "generated", "reviewed", "revised", "finalized"] = "pending"
    weight: float = Field(default=0.0, ge=0, le=1)
    priority: Literal["critical", "high", "normal", "low"] = "normal"
    depth: Literal["deep", "standard", "brief"] = "standard"
    dependencies: list[str] = Field(default_factory=list)
    quality_issues: list[dict] = Field(default_factory=list)
    revision_notes: list[str] = Field(default_factory=list)


class EvaluationCriterion(BaseModel):
    """평가 기준"""

    name: str
    score: int
    description: str | None = None
    subcriteria: list[str] = Field(default_factory=list)


class PersonnelAssignment(BaseModel):
    """인력 배정"""

    role: str
    candidate_name: str
    candidate_id: str | None = None
    qualifications: list[str] = Field(default_factory=list)
    experience_years: int | None = None
    utilization_rate: float = 1.0
    monthly_cost: float | None = None
    is_subcontracted: bool = False


def initialize_proposal_state(
    proposal_id: str,
    rfp_document: str,
    company_profile: dict,
) -> ProposalState:
    """ProposalState 초기화"""
    now = datetime.now()
    return {
        "proposal_id": proposal_id,
        "created_at": now,
        "updated_at": now,
        "rfp_document": rfp_document,
        "rfp_analysis": {},
        "company_profile": company_profile,
        "competitive_analysis": {},
        "strategy": {},
        "section_allocations": [],
        "personnel_assignments": [],
        "sections": {},
        "quality_score": 0.0,
        "quality_feedback": [],
        "revision_round": 0,
        "revision_history": [],
        "executive_summary": None,
        "final_sections": {},
        "export_format": "docx",
        "export_path": None,
        "total_pages": 0,
        "token_usage": {},
        "cost_estimate": 0.0,
    }
