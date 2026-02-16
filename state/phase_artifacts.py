"""
Phase Artifact 스키마 (v3.1.1)

각 Phase의 산출물을 다음 Phase로 전달하기 위한 구조화된 요약.
- Phase 1 → Artifact #1 (~8K tok)
- Phase 2 → Artifact #2 (~10K tok)  
- Phase 3 → Artifact #3 (~12K tok)
- Phase 4 → Artifact #4 (~15K tok)
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class PhaseArtifact_1_Research(BaseModel):
    """Phase 1 (Research) → Phase 2 (Analysis)로 전달하는 Artifact"""

    class Config:
        # 최대 ~8,000 토큰 (한국어 기준)
        json_schema_extra = {"max_tokens": 8_000}

    # ── RFP 핵심 정보 (원문 요약) ──
    rfp_title: str = Field(description="RFP 제목")
    client_name: str = Field(description="발주처명")
    submission_deadline: str = Field(description="제출 마감정")
    budget_range: Optional[str] = Field(default=None, description="예산 범위")
    page_limit: Optional[int] = Field(default=None, description="페이지 제한")
    evaluation_method: str = Field(description="평가 방식 (적격심사/종합평가/수의계약 등)")

    # ── RFP 요구사항 추출 ──
    requirements_summary: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="핵심 요구사항 (전문 아닌 구조화 추출, 최대 20개)",
    )
    evaluation_criteria_raw: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="평가 기준 (배점, 세부 항목)",
    )

    # ── 수집된 참조 데이터 (요약) ──
    past_proposals_summary: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="과거 제안서 이력 (최대 5건, 각 필드 최소화)",
    )
    competition_history: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="경쟁 이력 조회 결과",
    )
    company_capabilities_relevant: List[str] = Field(
        default_factory=list,
        description="이 RFP에 관련된 역량 (최대 10개)",
    )
    available_personnel_count: int = Field(
        default=0,
        description="현재 가용 인력 수",
    )

    # ── 원본 참조 경로 (MCP 경유 접근) ──
    rfp_document_ref: str = Field(
        description="MCP document_store의 RFP 문서 경로"
    )
    full_data_refs: Dict[str, str] = Field(
        default_factory=dict,
        description="기타 자료 참조 경로 {data_type: mcp_ref}",
    )


class PhaseArtifact_2_Analysis(BaseModel):
    """Phase 2 (Analysis) → Phase 3 (Plan)으로 전달하는 Artifact"""

    class Config:
        json_schema_extra = {"max_tokens": 10_000}

    # ── RFP 분석 결과 ──
    evaluation_criteria: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="평가 기준 해석 (카테고리, 배점, 가중치)",
    )
    mandatory_requirements: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="필수 요건 및 충족 여부",
    )
    implicit_intent: str = Field(
        default="",
        description="발주처 숨은 의도 추론 (300자 이내)",
    )
    risk_factors: List[str] = Field(
        default_factory=list,
        description="리스크 요인 (최대 5개)",
    )

    # ── 발주처 언어 프로파일 ──
    client_vocabulary: Dict[str, Any] = Field(
        default_factory=dict,
        description="발주처 선호 용어, 톤, 형식 레벨",
    )
    client_priorities: List[str] = Field(
        default_factory=list,
        description="발주처가 중시하는 것 (우선순위 순)",
    )

    # ── 경쟁 분석 결과 ──
    competitive_landscape: str = Field(
        default="",
        description="경쟁 환경 요약 (200자)",
    )
    our_strengths: List[str] = Field(
        default_factory=list,
        description="우리 강점 (최대 5개)",
    )
    our_weaknesses: List[str] = Field(
        default_factory=list,
        description="우리 약점 (최대 3개)",
    )
    attack_strategy_hint: str = Field(
        default="",
        description="공략 방향 힌트 (100자)",
    )

    # ── 배점 기반 자원 배분 (계산 결과) ──
    section_allocations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="섹션별 배분 (섹션 ID, 배점, 페이지, 깊이)",
    )
    total_target_pages: int = Field(
        default=0,
        description="총 목표 페이지",
    )

    # ── 자격 요건 검증 ──
    qualification_status: str = Field(
        default="충족",
        description="자격 요건 상태 (충족/조건부/미충족)",
    )
    qualification_gaps: List[str] = Field(
        default_factory=list,
        description="부족한 자격 사항",
    )

    # ── 이전 Artifact 참조 ──
    phase1_artifact_ref: str = Field(default="phase_artifact_1")


class PhaseArtifact_3_Plan(BaseModel):
    """Phase 3 (Plan) → Phase 4 (Implement)로 전달하는 Artifact"""

    class Config:
        json_schema_extra = {"max_tokens": 12_000}

    # ── 핵심 전략 ──
    core_message: str = Field(
        description="제안의 핵심 메시지 (200자)"
    )
    win_themes: List[str] = Field(
        default_factory=list,
        description="수주 테마 (3~5개)",
    )
    differentiators: List[str] = Field(
        default_factory=list,
        description="차별화 포인트 (3~5개)",
    )

    # ── 섹션별 작성 지침 ──
    section_plans: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="각 섹션의 작성 계획 (ID, 이름, 분량, 전략, 의존성 등)",
    )

    # ── 인력 배정 ──
    personnel_assignments: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="인력 배정 현황 (직급, 이름, 자격증, 배치율)",
    )

    # ── 발주처 언어 지침 ──
    language_guidelines: Dict[str, Any] = Field(
        default_factory=dict,
        description="톤, 선호 용어, 피할 용어",
    )

    # ── 생성 순서 (위상 정렬) ──
    generation_phases: List[List[str]] = Field(
        default_factory=list,
        description="섹션 생성 순서 [[sec_01, sec_09], [sec_02, sec_04], ...]",
    )

    # ── RAG 참조 미리 수집 (Token #4) ──
    # Phase 3에서 1회 수집 → Artifact에 포함 → Phase 4에서 캐싱
    rag_references: Dict[str, List[Dict[str, Any]]] = Field(
        default_factory=dict,
        description="도메인별 RAG 참조 자료",
    )

    # ── 이전 Artifact 참조 ──
    phase2_artifact_ref: str = Field(default="phase_artifact_2")


class PhaseArtifact_4_Implement(BaseModel):
    """Phase 4 (Implement) → Phase 5 (Test)로 전달하는 Artifact"""

    class Config:
        json_schema_extra = {"max_tokens": 15_000}

    # ── 각 섹션의 요약 + 메타데이터 ──
    section_summaries: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="섹션별 요약 (ID, 이름, 핵심, 페이지, 주장, 수치)",
    )

    # ── 전체 통계 ──
    total_pages: float = Field(
        default=0.0,
        description="생성된 총 페이지",
    )
    total_target_pages: int = Field(
        default=0,
        description="목표 총 페이지",
    )
    overall_traceability: float = Field(
        default=0.0,
        description="전체 요구사항 커버리지 (0~1)",
    )

    # ── 섹션 전문 참조 (MCP 경유) ──
    section_full_refs: Dict[str, str] = Field(
        default_factory=dict,
        description="섹션별 전문 MCP 참조 {section_id: ref}",
    )

    # ── 이전 Artifact 참조 ──
    phase3_artifact_ref: str = Field(default="phase_artifact_3")

    # ── 생성 과정 메모 ──
    generation_notes: List[str] = Field(
        default_factory=list,
        description="생성 중 발생한 이슈/결정",
    )


class PhaseResult(BaseModel):
    """Phase 실행 결과 (모든 Phase 공통 래퍼)"""

    phase_number: int = Field(
        description="Phase 번호 (1~5)"
    )
    phase_name: str = Field(
        description="Phase 이름 (RESEARCH, ANALYSIS, PLAN, IMPLEMENT, TEST)"
    )
    artifact: Dict[str, Any] = Field(
        description="PhaseArtifact_N 인스턴스"
    )
    execution_time_seconds: float = Field(
        default=0.0,
        description="Phase 실행 시간 (초)",
    )
    tokens_used: Dict[str, int] = Field(
        default_factory=dict,
        description="토큰 사용량 {input, output, cache_hit, cache_write}",
    )
    issues: List[str] = Field(
        default_factory=list,
        description="발생한 이슈",
    )
    hitl_recommendation: str = Field(
        default="skip_ok",
        description="HITL 권장사항 (required/recommended/skip_ok)",
    )
    hitl_reason: str = Field(
        default="",
        description="HITL 권장 사유",
    )
