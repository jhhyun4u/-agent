"""
LangGraph State 스키마 (§3)

ProposalState: 전체 워크플로 상태를 관리하는 TypedDict.
Annotated reducers로 병렬 노드 결과 병합 제어.
"""

from typing import Annotated, Any, Literal, Optional, TypedDict

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
    """STEP 1-②: Go/No-Go 의사결정 결과. v4.0: 4축 정량 스코어링."""
    rfp_analysis_ref: str = ""
    positioning: Literal["defensive", "offensive", "adjacent"]
    positioning_rationale: str
    feasibility_score: int                   # 4축 합산 (0~100)
    score_breakdown: dict                    # v4.0: 4축 구조
    pros: list[str]
    risks: list[str]
    recommendation: Literal["go", "no-go"]
    fatal_flaw: Optional[str] = None
    strategic_focus: Optional[str] = None
    decision: str = "pending"
    # v4.0 신규
    score_tag: str = ""                      # priority|standard|below_threshold|disqualified
    performance_detail: dict = {}            # 유사실적 상세
    qualification_detail: dict = {}          # 자격 적격성 상세
    competition_detail: dict = {}            # 경쟁 강도 상세


class PriceScoringFormula(BaseModel):
    """RFP에 명시된 가격점수 산정 방식. 없으면 표준 공식 적용."""
    formula_type: str = ""  # "lowest_ratio" | "fixed_rate" | "budget_ratio" | "custom" | ""
    description: str = ""   # RFP 원문 발췌 (가격점수 관련 조항)
    price_weight: float = 0  # 가격 배점 (예: 20점)
    parameters: dict = {}   # 공식별 추가 파라미터 (예: {"base_ratio": 87.745})


class RFPAnalysis(BaseModel):
    project_name: str
    client: str
    deadline: str
    case_type: Literal["A", "B"]
    eval_method: str = ""
    eval_items: list[dict]
    tech_price_ratio: dict
    hot_buttons: list[str]
    mandatory_reqs: list[str]
    format_template: dict
    volume_spec: dict
    special_conditions: list[str]
    price_scoring: PriceScoringFormula | None = None

    # v3.9: 전략·계획 수립 기초자료 확장 필드 (하위 호환 — 모두 Optional)
    domain: str = ""                              # 사업 분류: SI/SW개발, 컨설팅, 감리, 인프라구축, 운영유지보수
    project_scope: str = ""                       # 사업 범위 요약 (3~5문장)
    budget: str = ""                              # RFP 원문 예산 발췌
    duration: str = ""                            # 수행 기간 (예: "12개월", "2026.07~2027.06")
    contract_type: str = ""                       # 정액, 실비정산, T&M 등
    delivery_phases: list[dict] = []              # 단계별 마일스톤·산출물
    qualification_requirements: list[str] = []    # 업체 자격 요건 (참가자격, 인증)
    similar_project_requirements: list[str] = []  # 유사 수행실적 요건
    key_personnel_requirements: list[dict] = []   # 핵심인력 자격/인증 요건
    subcontracting_conditions: list[str] = []     # 하도급 조건 (구조화)


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


class BidPlanResult(BaseModel):
    """STEP 2.5: 입찰가격계획 결과."""
    recommended_bid: int = 0
    recommended_ratio: float = 0.0
    scenarios: list[dict] = []
    selected_scenario: str = ""
    cost_breakdown: dict = {}
    sensitivity_curve: list[dict] = []
    win_probability: float = 0.0
    market_context: dict = {}
    data_quality: str = "rule_based"
    user_override_price: int | None = None
    user_override_reason: str = ""


class PPTSlide(BaseModel):
    slide_id: str
    title: str
    content: str
    notes: str
    version: int


class ArtifactVersion(BaseModel):
    """산출물 버전 정보 — Phase 1: Artifact Versioning System."""
    node_name: str
    output_key: str
    version: int
    created_at: str
    created_by: str
    is_active: bool
    is_deprecated: bool = False
    parent_node_name: Optional[str] = None
    parent_version: Optional[int] = None
    used_by: list[dict] = []
    checksum: Optional[str] = None
    artifact_size: Optional[int] = None
    created_reason: Optional[str] = None


class VersionSelection(BaseModel):
    """버전 선택 이력 항목 — Phase 1: Artifact Versioning System."""
    timestamp: str
    from_node: str
    to_node: str
    input_key: str
    selected_version: int


# ── Phase 2: STEP 8A-8F New Node Models ──


class Stakeholder(BaseModel):
    """Decision-maker or influencer in client organization."""
    name: str
    title: str
    role: str  # "decision_maker" | "influencer" | "budget_holder" | "user"
    interests: list[str]
    influence_level: int  # 1-5 scale
    contact_info: Optional[str] = None


class CustomerProfile(BaseModel):
    """Deep client intelligence for proposal strategy (Node 8A output)."""
    client_org: str
    market_segment: str  # Industry/market classification
    organization_size: str  # Small/Medium/Enterprise
    decision_drivers: list[str]  # Top 3-5 factors influencing decision
    budget_authority: str  # Description of how budget approved
    budget_range: Optional[str] = None
    internal_politics: str  # Org dynamics, power structures
    pain_points: list[str]  # Problems they're trying to solve
    success_metrics: list[str]  # How they measure project success
    key_stakeholders: list[Stakeholder]
    risk_perception: str  # What concerns them most
    timeline_pressure: str  # "low" | "medium" | "high" | "critical"
    procurement_process: str  # Formal/informal, approval gates
    competitive_landscape: str  # Who else might bid
    prior_experience: Optional[str] = None
    created_at: str  # ISO timestamp


class ValidationIssue(BaseModel):
    """Single validation finding."""
    section_id: str
    issue_type: str  # "compliance" | "style" | "consistency" | "completeness"
    severity: str  # "error" | "warning" | "info"
    description: str
    location: Optional[str] = None
    fix_guidance: Optional[str] = None
    estimated_fix_effort: str  # "quick" | "medium" | "complex"


class ValidationReport(BaseModel):
    """Quality assurance report for all proposal sections (Node 8B output)."""
    proposal_id: str
    total_sections: int
    sections_validated: int
    passed_sections: int
    failed_sections: int
    warning_sections: int

    errors: list[ValidationIssue] = []
    warnings: list[ValidationIssue] = []
    info: list[ValidationIssue] = []

    compliance_gaps: list[str] = []
    style_issues: list[str] = []
    cross_section_conflicts: list[str] = []

    quality_score: int
    is_ready_to_submit: bool
    primary_concern: Optional[str] = None
    recommendations: list[str] = []
    estimated_fix_time: str

    validated_at: str
    created_at: str = ""


class SectionLineage(BaseModel):
    """Track which version of each section was selected."""
    section_id: str
    original_version: int
    selected_version: int
    change_notes: Optional[str] = None


class ConsolidatedProposal(BaseModel):
    """Merged and validated proposal ready for submission/evaluation (Node 8C output)."""
    proposal_id: str
    final_sections: list[dict[str, Any]]
    section_count: int
    total_word_count: int

    section_lineage: list[SectionLineage] = []
    resolved_conflicts: list[str] = []
    merge_notes: Optional[str] = None

    quality_metrics: dict[str, Any] = {}
    completeness_score: int
    consistency_score: int
    compliance_score: int

    submission_ready: bool
    blockers: list[str] = []
    warnings: list[str] = []

    consolidated_at: str
    created_at: str = ""


class ScoreComponent(BaseModel):
    """Individual evaluation criterion score."""
    criterion: str
    max_points: int
    estimated_score: int
    feedback: str
    strengths: list[str] = []
    weaknesses: list[str] = []


class MockEvalResult(BaseModel):
    """Simulated evaluation from evaluator perspective (Node 8D output)."""
    proposal_id: str
    evaluation_method: str  # "A" | "B"
    evaluator_persona: str  # "strict" | "standard" | "lenient"

    total_max_points: int
    estimated_total_score: int
    estimated_percentage: float

    score_components: list[ScoreComponent] = []

    estimated_rank: str
    win_probability: float
    key_strengths: list[str] = []
    key_weaknesses: list[str] = []
    critical_gaps: list[str] = []

    estimated_max_score: int = 0
    potential_improvement: int = 0
    improvement_recommendations: list[str] = []

    pass_fail_risk: bool = False
    risk_factors: list[str] = []

    analysis_at: str
    created_at: str = ""


class FeedbackItem(BaseModel):
    """Prioritized feedback on specific section."""
    section_id: str
    section_title: str
    issue_category: str  # "critical_gap" | "improvement" | "minor"
    priority: int  # 1-10 scale
    issue_description: str
    rewrite_guidance: str
    example_improvement: Optional[str] = None
    estimated_effort: str


class FeedbackSummary(BaseModel):
    """Consolidated feedback for proposal improvement (Node 8E output)."""
    proposal_id: str

    critical_gaps: list[FeedbackItem] = []
    improvement_opportunities: list[FeedbackItem] = []

    section_feedback: dict[str, Any] = {}

    highest_impact_issues: list[str] = []

    rewrite_strategy: str
    affected_sections: list[str] = []

    estimated_total_effort: str
    critical_path_effort: str

    estimated_score_improvement: int
    estimated_new_score: int
    estimated_new_rank: str

    recommended_timeline: str

    processed_at: str
    created_at: str = ""


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
    project_id: Annotated[str, _replace]
    project_name: Annotated[str, _replace]

    # v2.0: 소유·조직 컨텍스트
    team_id: Annotated[str, _replace]
    division_id: Annotated[str, _replace]
    created_by: Annotated[str, _replace]
    participants: Annotated[list[str], _replace]

    # 실행 모드
    mode: Annotated[Literal["lite", "full"], _replace]

    # 포지셔닝 (STEP 1-②에서 확정, STEP 2에서 변경 가능)
    positioning: Annotated[Literal["defensive", "offensive", "adjacent"], _replace]

    # 단계별 산출물
    search_query: Annotated[dict, _replace]
    search_results: Annotated[list[RfpRecommendation], _replace]
    picked_bid_no: Annotated[str, _replace]
    bid_detail: Annotated[Optional[BidDetail], _replace]
    go_no_go: Annotated[Optional[GoNoGoResult], _replace]
    rfp_raw: Annotated[str, _replace]
    rfp_analysis: Annotated[Optional[RFPAnalysis], _replace]
    strategy: Annotated[Optional[Strategy], _replace]
    plan: Annotated[Optional[ProposalPlan], _replace]
    proposal_sections: Annotated[list[ProposalSection], _replace]
    ppt_slides: Annotated[list[PPTSlide], _replace]

    # Compliance Matrix
    compliance_matrix: Annotated[list[ComplianceItem], _replace]

    # 단계별 승인 상태
    approval: Annotated[dict[str, ApprovalStatus], _merge_dict]

    # 현재 실행 중인 단계 (fork 병렬 실행 시 last-write-wins)
    current_step: Annotated[str, _replace]

    # 피드백 이력
    feedback_history: Annotated[list[dict], _append_list]

    # 품질 게이트 경고 (Pre-Flight Check + self_check)
    quality_warnings: Annotated[list[dict], _append_list]

    # 부분 재작업 대상 (fork 병렬 실행 시 last-write-wins)
    rework_targets: Annotated[list[str], _replace]

    # 동적 섹션 목록 (fork 병렬 실행 시 last-write-wins)
    dynamic_sections: Annotated[list[str], _replace]

    # 병렬 작업 중간 결과
    parallel_results: Annotated[dict, _merge_dict]

    # v3.0: KB 참조
    kb_references: Annotated[list[dict], _append_list]
    client_intel_ref: Annotated[Optional[dict], _replace]
    competitor_refs: Annotated[list[dict], _replace]

    # v3.0: AI 상태 추적
    ai_task_id: Annotated[str, _replace]

    # v3.0: 토큰 사용 추적
    token_usage: Annotated[dict, _merge_dict]

    # v3.0: 피드백 윈도우
    feedback_window_size: Annotated[int, _replace]

    # v3.2: ProposalForge 통합
    research_brief: Annotated[Optional[dict], _replace]
    presentation_strategy: Annotated[Optional[dict], _replace]
    budget_detail: Annotated[Optional[dict], _replace]
    evaluation_simulation: Annotated[Optional[dict], _replace]

    # v3.5: 섹션별 순차 작성 인덱스
    current_section_index: Annotated[int, lambda a, b: b]
    rewrite_iteration_count: Annotated[int, lambda a, b: b]  # 8F: 섹션 재작성 반복 횟수

    # MON-02: 노드별 에러 정보 (프론트엔드 표시용)
    node_errors: Annotated[dict, lambda a, b: {**a, **b}]

    # v3.8: 입찰가격계획
    bid_plan: Optional[BidPlanResult]
    bid_budget_constraint: Optional[dict]

    # v4.0: 분기 워크플로 신규 노드
    submission_plan: Optional[dict]      # 3B: 제출서류 계획
    cost_sheet: Optional[dict]           # 5B: 산출내역서
    submission_checklist_result: Optional[dict]  # 6B: 제출서류 확인 결과
    mock_evaluation_result: Optional[dict]       # 6A: 모의 평가 최종 결과 (실제 평가 후)
    eval_result: Optional[dict]          # 7: 평가결과
    project_closing_result: Optional[dict]       # 8: Closing

    # Phase 4: 3단계 PPT 파이프라인 최종 결과
    ppt_storyboard: Optional[dict]

    # Phase 1: Artifact Versioning System
    artifact_versions: Annotated[
        dict[str, list[ArtifactVersion]],
        lambda a, b: {**a, **{k: (a.get(k, []) + v) for k, v in b.items()}}  # Merge (append per key)
    ]
    active_versions: Annotated[
        dict[str, int],  # {f"{node_name}_{output_key}": version_number}
        lambda a, b: {**a, **b}  # Merge active versions
    ]
    version_selection_history: Annotated[
        list[dict],  # [{timestamp, from_node, to_node, choices, selected}]
        _append_list  # Append to history
    ]
    selected_versions: Annotated[
        dict[str, int],  # {f"{node_name}_{output_key}": version} — 사용자가 선택한 버전
        lambda a, b: {**a, **b}  # Merge selected versions
    ]

    # Phase 2: STEP 8A-8F Node Outputs (Quality Gate Pipeline)
    # IMPORTANT: mock_eval_result (8D) is different from mock_evaluation_result (6A)
    # - mock_eval_result: Evaluator perspective simulation (8D) for proposal feedback
    # - mock_evaluation_result: Final evaluation scores (6A) after actual presentation
    customer_profile: Annotated[Optional[CustomerProfile], _replace]  # 8A: 고객 분석
    validation_report: Annotated[Optional[ValidationReport], _replace]  # 8B: 섹션 검증
    consolidated_proposal: Annotated[Optional[ConsolidatedProposal], _replace]  # 8C: 통합
    mock_eval_result: Annotated[Optional[MockEvalResult], _replace]  # 8D: 평가자 시뮬레이션 분석
    feedback_summary: Annotated[Optional[FeedbackSummary], _replace]  # 8E: 피드백 처리
