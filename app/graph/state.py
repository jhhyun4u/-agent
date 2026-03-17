"""
LangGraph State 스키마 (§3)

ProposalState: 전체 워크플로 상태를 관리하는 TypedDict.
Annotated reducers로 병렬 노드 결과 병합 제어.
"""

from typing import Annotated, Literal, Optional, TypedDict

from pydantic import BaseModel


# ── 서브 모델 ──


class ApprovalChainEntry(BaseModel):
    """결재선 단일 항목 — 예산 기준에 따라 1~3단계."""
    role: Literal["lead", "director", "executive"]
    user_id: str
    user_name: str
    status: Literal["pending", "approved", "rejected"] = "pending"
    decided_at: str = ""
    feedback: str = ""


class ApprovalStatus(BaseModel):
    status: str = "pending"  # pending | approved | rejected
    approved_by: str = ""
    approved_at: str = ""
    feedback: str = ""
    chain: list[ApprovalChainEntry] = []


class RfpRecommendation(BaseModel):
    """STEP 0: 공고 검색 추천 결과 (최대 5건)."""
    bid_no: str
    project_name: str
    client: str
    budget: str
    deadline: str
    project_summary: str
    key_requirements: list[str]
    eval_method: str
    competition_level: str
    fit_score: int
    fit_rationale: str
    expected_positioning: Literal["defensive", "offensive", "adjacent"]
    brief_analysis: str


class BidDetail(BaseModel):
    """STEP 0→1: G2B 공고 상세 정보."""
    bid_no: str
    project_name: str
    client: str
    budget: str
    deadline: str
    description: str
    requirements_summary: str
    attachments: list[dict]
    rfp_auto_text: str = ""


class GoNoGoResult(BaseModel):
    """STEP 1-②: Go/No-Go 의사결정 결과."""
    rfp_analysis_ref: str = ""
    positioning: Literal["defensive", "offensive", "adjacent"]
    positioning_rationale: str
    feasibility_score: int
    score_breakdown: dict
    pros: list[str]
    risks: list[str]
    recommendation: Literal["go", "no-go"]
    decision: str = "pending"


class RFPAnalysis(BaseModel):
    project_name: str
    client: str
    deadline: str
    case_type: Literal["A", "B"]
    eval_items: list[dict]
    tech_price_ratio: dict
    hot_buttons: list[str]
    mandatory_reqs: list[str]
    format_template: dict
    volume_spec: dict
    special_conditions: list[str]


class StrategyAlternative(BaseModel):
    """전략 대안 — 최소 2가지."""
    alt_id: str
    ghost_theme: str
    win_theme: str
    action_forcing_event: str
    key_messages: list[str]
    price_strategy: dict
    risk_assessment: dict


class Strategy(BaseModel):
    positioning: Literal["defensive", "offensive", "adjacent"]
    positioning_rationale: str
    alternatives: list[StrategyAlternative]
    selected_alt_id: str = ""
    ghost_theme: str = ""
    win_theme: str = ""
    action_forcing_event: str = ""
    key_messages: list[str] = []
    focus_areas: list[dict] = []
    price_strategy: dict = {}
    competitor_analysis: dict = {}
    risks: list[dict] = []


class ComplianceItem(BaseModel):
    req_id: str
    content: str
    source_step: str
    status: Literal["미확인", "충족", "미충족", "해당없음"] = "미확인"
    proposal_section: str = ""


class ProposalSection(BaseModel):
    section_id: str
    title: str
    content: str
    version: int
    case_type: Literal["A", "B"]
    template_structure: Optional[dict] = None
    self_review_score: Optional[dict] = None


class ProposalPlan(BaseModel):
    team: list[dict]
    deliverables: list[dict]
    schedule: dict
    storylines: dict
    bid_price: dict


class PPTSlide(BaseModel):
    slide_id: str
    title: str
    content: str
    notes: str
    version: int


# ── Annotated Reducers ──


def _merge_dict(existing: dict, new: dict) -> dict:
    """dict 병합 (새 값이 기존 값을 덮어씀)."""
    return {**existing, **new}


def _append_list(existing: list, new: list) -> list:
    """리스트 누적 (피드백 이력 등)."""
    return existing + new


def _replace(existing, new):
    """전체 교체 (검색 결과, 섹션 목록 등)."""
    return new


# ── 핵심 State 정의 ──


class ProposalState(TypedDict):
    """LangGraph 워크플로 전체 상태."""

    # 프로젝트 메타
    project_id: str
    project_name: str

    # v2.0: 소유·조직 컨텍스트
    team_id: str
    division_id: str
    created_by: str
    participants: list[str]

    # 실행 모드
    mode: Literal["lite", "full"]

    # 포지셔닝 (STEP 1-②에서 확정, STEP 2에서 변경 가능)
    positioning: Literal["defensive", "offensive", "adjacent"]

    # 단계별 산출물
    search_query: dict
    search_results: Annotated[list[RfpRecommendation], _replace]
    picked_bid_no: str
    bid_detail: Optional[BidDetail]
    go_no_go: Optional[GoNoGoResult]
    rfp_raw: str
    rfp_analysis: Optional[RFPAnalysis]
    strategy: Optional[Strategy]
    plan: Optional[ProposalPlan]
    proposal_sections: Annotated[list[ProposalSection], _replace]
    ppt_slides: Annotated[list[PPTSlide], _replace]

    # Compliance Matrix
    compliance_matrix: Annotated[list[ComplianceItem], _replace]

    # 단계별 승인 상태
    approval: Annotated[dict[str, ApprovalStatus], _merge_dict]

    # 현재 실행 중인 단계
    current_step: str

    # 피드백 이력
    feedback_history: Annotated[list[dict], _append_list]

    # 부분 재작업 대상
    rework_targets: list[str]

    # 동적 섹션 목록
    dynamic_sections: list[str]

    # 병렬 작업 중간 결과
    parallel_results: Annotated[dict, _merge_dict]

    # v3.0: KB 참조
    kb_references: Annotated[list[dict], _append_list]
    client_intel_ref: Optional[dict]
    competitor_refs: list[dict]

    # v3.0: AI 상태 추적
    ai_task_id: str

    # v3.0: 토큰 사용 추적
    token_usage: Annotated[dict, _merge_dict]

    # v3.0: 피드백 윈도우
    feedback_window_size: int

    # v3.2: ProposalForge 통합
    research_brief: Optional[dict]
    presentation_strategy: Optional[dict]
    budget_detail: Optional[dict]
    evaluation_simulation: Optional[dict]

    # v3.5: 섹션별 순차 작성 인덱스
    current_section_index: Annotated[int, lambda a, b: b]

    # Phase 4: 3단계 PPT 파이프라인 최종 결과
    ppt_storyboard: Optional[dict]
