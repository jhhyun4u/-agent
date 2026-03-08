"""Phase 간 전달되는 산출물 스키마 (v3.4)"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

from app.models.schemas import RFPData


class PhaseArtifact(BaseModel):
    """Phase 간 전달되는 압축 산출물 - 토큰 예산 최적화"""
    phase_num: int
    phase_name: str
    summary: str = Field(description="핵심 내용 요약 (3K 토큰 이하)")
    structured_data: dict = Field(default_factory=dict)
    token_count: int = 0
    created_at: datetime = Field(default_factory=datetime.now)


class Phase1Artifact(PhaseArtifact):
    """Phase 1 산출물: RFP 파싱 결과"""
    phase_num: int = 1
    phase_name: str = "research"
    rfp_data: Optional[RFPData] = None
    history_summary: str = ""
    g2b_competitor_data: dict = Field(
        default_factory=dict,
        description="나라장터 유사계약 및 경쟁사 사전 분석 데이터"
    )


class Phase2Artifact(PhaseArtifact):
    """Phase 2 산출물: RFP 구조화 분석 + 경쟁/가격 분석"""
    phase_num: int = 2
    phase_name: str = "analysis"
    key_requirements: list[str] = Field(default_factory=list)
    evaluation_weights: dict = Field(default_factory=dict)
    hidden_intent: str = ""
    risk_factors: list[str] = Field(default_factory=list)
    competitor_landscape: dict = Field(
        default_factory=dict,
        description="잠재 경쟁자 유형, 강점/약점 분석"
    )
    price_analysis: dict = Field(
        default_factory=dict,
        description="예산 범위 분석, 적정 입찰가 범위, 가격 포지셔닝 전략"
    )


class Phase3Artifact(PhaseArtifact):
    """Phase 3 산출물: 전략 계획 + 차별화 전략 + 입찰가 전략"""
    phase_num: int = 3
    phase_name: str = "plan"
    win_strategy: str = ""
    section_plan: list[dict] = Field(default_factory=list)
    page_allocation: dict = Field(default_factory=dict)
    team_plan: str = ""
    differentiation_strategy: list[str] = Field(
        default_factory=list,
        description="경쟁자 대비 핵심 차별화 포인트"
    )
    bid_price_strategy: dict = Field(
        default_factory=dict,
        description="추천 입찰가 범위, 가격 전략 논리, 가격-기술 트레이드오프"
    )
    bid_calculation: dict = Field(
        default_factory=dict,
        description="BidCalculator 원가 계산 결과 (인건비 기반 실제 원가)"
    )
    win_theme: dict = Field(
        default_factory=dict,
        description="제안서 전체 관통 Win Theme (메시지, 근거, 3축 증거)"
    )
    alternatives_considered: list[dict] = Field(
        default_factory=list,
        description="접근법 대안 비교 (approach, our_approach, why_better)"
    )
    risks_mitigations: list[dict] = Field(
        default_factory=list,
        description="리스크-대응방안 표 (risk, probability, impact, mitigation)"
    )
    implementation_checklist: list[dict] = Field(
        default_factory=list,
        description="단계별 추진 체계 (phase, duration, deliverables, milestones)"
    )
    logic_model: dict = Field(
        default_factory=dict,
        description="사업 논리 모델 (inputs→activities→outputs→단기성과→장기성과)"
    )
    objection_responses: list[dict] = Field(
        default_factory=list,
        description="평가위원 예상 반론 및 선제 대응 (objection/acknowledge/response/evidence)"
    )


class Phase4Artifact(PhaseArtifact):
    """Phase 4 산출물: 섹션 초안"""
    phase_num: int = 4
    phase_name: str = "implement"
    sections: dict[str, str] = Field(default_factory=dict)

class Phase5Artifact(PhaseArtifact):
    """Phase 5 산출물: 최종 완성본"""
    phase_num: int = 5
    phase_name: str = "test"
    quality_score: float = 0.0
    issues: list[dict] = Field(default_factory=list)
    docx_path: str = ""
    pptx_path: str = ""
    hwpx_path: str = ""
    executive_summary: str = ""
    win_probability: str = ""
    detailed_scores: dict = Field(default_factory=dict, description="항목별 세부 점수")
    alternatives_quality: str = Field(default="", description="대안 비교 설득력 평가")
    risks_coverage: str = Field(default="", description="리스크 대응 완성도 평가")
    checklist_specificity: str = Field(default="", description="추진 체계 구체성 평가")
