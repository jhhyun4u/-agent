"""
Sub-agent들의 내부 상태 스키마.

v3.0: 각 Sub-agent는 독립적인 서브그래프로, 내부적으로만 사용하는 State를 가짐.
완료 후 결과는 ProposalState에 병합되어 Supervisor로 반환.
"""

from typing import TypedDict, Annotated, Literal, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime


# ═══════════════════════════════════════════════════════════════════════════
# 1. RFP 분석 에이전트의 내부 상태
# ═══════════════════════════════════════════════════════════════════════════

class RFPAnalysisState(TypedDict):
    """RFP 분석 Sub-agent의 내부 상태"""

    # 입력
    raw_document: str
    """원본 RFP 문서 (PDF/HWP/DOCX에서 추출된 텍스트)"""

    # 중간 결과
    cleaned_text: str
    """정제된 텍스트 (특수 기호 제거, 정규화)"""

    structural_result: dict
    """구조화 분석 결과 {sections, metadata}"""

    implicit_analysis: dict
    """숨은 의도 및 발주처 심리 분석 결과"""

    language_profile: dict
    """발주처 언어 프로필 {key_terms, writing_style, formal_level}"""

    qualifications: dict
    """자격 요건 검증 결과 {mandatory, optional, gaps}"""

    # 최종 결과
    rfp_analysis_result: dict
    """최종 분석 결과 (Supervisor로 반환 시)"""


# ═══════════════════════════════════════════════════════════════════════════
# 2. 전략 수립 에이전트의 내부 상태
# ═══════════════════════════════════════════════════════════════════════════

class StrategyState(TypedDict):
    """전략 수립 Sub-agent의 내부 상태"""

    # 입력
    rfp_analysis: dict
    """RFP 분석 결과 (이전 단계에서 전달)"""

    company_profile: dict
    """회사 정보 및 역량"""

    # 중간 결과
    competitive_analysis: dict
    """경쟁 환경 분석 {competitors, threats, opportunities}"""

    score_allocations: list[dict]
    """배점별 섹션 배분 결과"""

    strategy_draft: dict
    """전략 초안 {core_message, differentiators, attack_strategy}"""

    personnel_assignments: list[dict]
    """인력 배정 결과 [{role, candidate, qualification}]"""

    # 최종 결과
    strategy_result: dict
    """최종 전략 결과 (Supervisor로 반환 시)"""


# ═══════════════════════════════════════════════════════════════════════════
# 3. 섹션 생성 에이전트의 내부 상태
# ═══════════════════════════════════════════════════════════════════════════

class SectionGenerationState(TypedDict):
    """섹션 생성 Sub-agent의 내부 상태"""

    # 입력
    rfp_analysis: dict
    strategy: dict
    allocations: list[dict]

    # 실행 관리
    generation_phases: list[list[str]]
    """위상 정렬된 Phase: [[sec_01, sec_09], [sec_02, sec_04], ...]"""

    current_phase_index: int
    """현재 실행 중인 Phase 인덱스"""

    remaining_phases: list[list[str]]
    """남은 Phase들"""

    # 진행 상황
    generated_sections: dict[str, dict]
    """생성된 섹션 {section_id: {content, pages, status}}"""

    section_dependencies: dict[str, list[str]]
    """섹션 간 의존성 그래프"""

    # 최종 결과
    sections_result: dict
    """최종 섹션 결과 (Supervisor로 반환 시)"""


# ═══════════════════════════════════════════════════════════════════════════
# 4. 품질 관리 에이전트의 내부 상태
# ═══════════════════════════════════════════════════════════════════════════

class QualityState(TypedDict):
    """품질 관리 Sub-agent의 내부 상태"""

    # 입력
    sections: dict
    """현재까지의 섹션 내용"""

    rfp_analysis: dict
    """RFP 분석 결과 (요구사항 검증용)"""

    # 비평 결과
    critique_result: dict
    """구조, 논리, 정합성, 추적성 등에 대한 비평"""

    integration_issues: list[dict]
    """발견된 이슈 [{severity, type, location, description}]"""

    quality_score: float
    """종합 품질 점수 (0.0 ~ 1.0)"""

    revision_round: int
    """현재까지 수정 라운드 횟수"""

    # 의사결정
    quality_action: Literal["pass", "revise", "escalate"]
    """다음 액션: 통과 / 수정 / 에스컬레이션"""

    escalation_reason: str | None = None
    """에스컬레이션 사유 (있으면)"""

    # 최종 결과
    quality_result: dict
    """최종 품질 검토 결과 (Supervisor로 반환 시)"""


# ═══════════════════════════════════════════════════════════════════════════
# 5. 문서 출력 에이전트의 내부 상태
# ═══════════════════════════════════════════════════════════════════════════

class DocumentState(TypedDict):
    """문서 출력 Sub-agent의 내부 상태"""

    # 입력
    sections: dict
    """최종 섹션들"""

    metadata: dict
    """제안서 메타데이터"""

    # 중간 결과
    executive_summary: str
    """요약문"""

    final_edited: dict
    """최종 편집된 섹션들"""

    # 출력
    docx_content: bytes | None = None
    """DOCX 바이너리"""

    pptx_content: bytes | None = None
    """PPTX 바이너리"""

    export_paths: dict
    """export_docx, export_pptx 등"""

    # 최종 결과
    document_result: dict
    """최종 문서 출력 결과 (Supervisor로 반환 시)"""


# ═══════════════════════════════════════════════════════════════════════════
# 보조 모데을
# ═══════════════════════════════════════════════════════════════════════════

class RFPAnalysisOutput(BaseModel):
    """RFP 분석 에이전트의 최종 출력"""
    
    analysis_id: str = Field(description="분석 ID")
    rfp_title: str
    client_name: str
    evaluation_method: str  # "경쟁입찰", "수의계약", etc.
    mandatory_qualifications: list[dict] = Field(default_factory=list)
    evaluation_criteria: list[dict] = Field(default_factory=list)
    hidden_intent: str = Field(description="RFP의 숨은 의도")
    client_language_profile: dict = Field(description="발주처 언어 특성")
    completeness_score: float = Field(ge=0, le=1, description="분석 완성도")


class StrategyOutput(BaseModel):
    """전략 수립 에이전트의 최종 출력"""

    strategy_id: str
    core_message: str = Field(description="핵심 메시지")
    differentiators: list[str] = Field(description="차별화 포인트")
    attack_strategy: str = Field(description="경쟁 대응 전략")
    section_allocations: list[dict] = Field(description="섹션별 배점 배분")
    personnel_plan: dict = Field(description="인력 배정 계획")


class QualityOutput(BaseModel):
    """품질 관리 에이전트의 최종 출력"""

    quality_score: float = Field(ge=0, le=1)
    total_issues: int
    critical_issues: list[dict] = Field(description="중대 이슈")
    revision_recommendation: str

