"""
비딩 가격 산정 모듈 — Pydantic 스키마

PricingSimulationRequest/Result 및 하위 모델 정의.
"""

from datetime import UTC, datetime

from pydantic import BaseModel, Field


# ── 입력 모델 ──

class PersonnelInput(BaseModel):
    role: str
    grade: str
    person_months: float
    labor_type: str = "SW"  # SW | ENG


class PricingSimulationRequest(BaseModel):
    budget: int = Field(..., description="사업예산 (원)")
    domain: str = "SI/SW개발"
    evaluation_method: str = "종합심사"  # 종합심사 | 적격심사 | 최저가 | 수의계약
    tech_price_ratio: dict = Field(default_factory=lambda: {"tech": 80, "price": 20})
    positioning: str = "defensive"  # defensive | offensive | adjacent
    competitor_count: int = 5
    cost_standard: str | None = None  # None = 자동 선택
    personnel: list[PersonnelInput] = Field(default_factory=list)
    client_name: str | None = None
    rfp_text: str | None = None  # RFP 텍스트 (비용 기준 자동 탐색)
    proposal_id: str | None = None
    price_scoring_formula: dict | None = None  # RFP에서 추출한 가격점수 산식
    assumed_tech_score: float | None = None     # 가정 기술점수 (시뮬레이션용)


class QuickEstimateRequest(BaseModel):
    budget: int
    evaluation_method: str = "종합심사"
    domain: str = "SI/SW개발"
    positioning: str = "defensive"
    competitor_count: int = 5


# ── 원가 관련 ──

class PersonnelCostDetail(BaseModel):
    role: str
    grade: str
    monthly_rate: int
    person_months: float
    amount: int
    amount_fmt: str


class CostBreakdownDetail(BaseModel):
    direct_labor: int
    direct_labor_fmt: str
    indirect_cost: int
    indirect_fmt: str
    technical_fee: int
    tech_fee_fmt: str
    subtotal: int
    subtotal_fmt: str
    vat: int
    vat_fmt: str
    total_cost: int
    total_cost_fmt: str
    personnel_detail: list[PersonnelCostDetail] = Field(default_factory=list)


class CostStandardRecommendation(BaseModel):
    standard: str  # KOSA | KEA | MOEF
    confidence: str  # high | medium | low
    reason: str


# ── 수주확률 ──

class BidRange(BaseModel):
    min_price: int
    max_price: int
    min_ratio: float
    max_ratio: float


class SensitivityPoint(BaseModel):
    ratio: float
    bid_price: int
    win_prob: float
    expected_payoff: int


class PriceScoreDetail(BaseModel):
    """시나리오별 가격점수 산출 결과."""
    price_score: float = 0       # 가격점수
    price_weight: float = 0      # 가격 배점
    score_ratio: float = 0       # 득점률
    total_score: float = 0       # 기술 + 가격 총점 (기술점수 가정 시)
    formula_used: str = ""       # 적용 공식
    estimated_min_bid: int = 0   # 추정 최저입찰가
    is_disqualified: bool = False


class Scenario(BaseModel):
    name: str  # conservative | balanced | aggressive
    label: str  # 보수적 | 균형 | 공격적
    bid_ratio: float
    bid_price: int
    win_probability: float
    expected_payoff: int
    risk_level: str  # low | medium | high
    price_score_detail: PriceScoreDetail | None = None


class MarketContext(BaseModel):
    domain: str
    avg_bid_ratio: float | None = None
    avg_num_bidders: float | None = None
    total_cases: int = 0
    evaluation_method_distribution: dict = Field(default_factory=dict)
    budget_tier_distribution: dict = Field(default_factory=dict)


class CompetitorPricingProfile(BaseModel):
    company_name: str
    avg_bid_ratio: float | None = None
    win_count: int = 0
    total_bids: int = 0
    preferred_positioning: str | None = None


class ClientPricingPreference(BaseModel):
    client_name: str
    avg_winning_ratio: float | None = None
    preferred_evaluation_method: str | None = None
    total_projects: int = 0
    avg_budget: int | None = None


# ── 결과 모델 ──

class PricingSimulationResult(BaseModel):
    # 원가
    cost_breakdown: CostBreakdownDetail | None = None
    cost_standard_used: str = ""
    cost_standard_reason: str = ""
    # 추천 입찰가
    recommended_bid: int = 0
    recommended_ratio: float = 0.0
    bid_range: BidRange | None = None
    # 수주확률
    win_probability: float = 0.0
    win_probability_confidence: str = "low"  # high | medium | low
    comparable_cases: int = 0
    # 민감도
    sensitivity_curve: list[SensitivityPoint] = Field(default_factory=list)
    optimal_ratio: float = 0.0
    # 시나리오
    scenarios: list[Scenario] = Field(default_factory=list)
    # 시장 컨텍스트
    market_context: MarketContext | None = None
    # 경쟁사/발주기관
    competitor_profiles: list[CompetitorPricingProfile] = Field(default_factory=list)
    client_preference: ClientPricingPreference | None = None
    # 가격점수 시뮬레이션
    score_simulation: list[dict] = Field(default_factory=list)  # PriceScoreCalculator 결과
    # 메타
    data_quality: str = "rule_based"  # rule_based | statistical | hybrid
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

    def to_prompt_context(self) -> str:
        """LangGraph 노드 프롬프트에 주입할 텍스트 생성."""
        lines = [
            "## 알고리즘 기반 가격 분석 결과",
            f"- 추천 입찰가: {self.recommended_bid:,}원 (낙찰률 {self.recommended_ratio:.1f}%)",
            f"- 수주확률: {self.win_probability:.0%} (신뢰도: {self.win_probability_confidence})",
            f"- 데이터 기반: {self.data_quality} (유사 사례 {self.comparable_cases}건)",
        ]
        if self.cost_breakdown:
            lines.append(f"- 총원가: {self.cost_breakdown.total_cost_fmt}")
        if self.bid_range:
            lines.append(f"- 입찰가 범위: {self.bid_range.min_ratio:.1f}%~{self.bid_range.max_ratio:.1f}%")
        if self.optimal_ratio > 0:
            lines.append(f"- 기대수익 최적 비율: {self.optimal_ratio:.1f}%")
        if self.scenarios:
            lines.append("\n### 시나리오 비교")
            for s in self.scenarios:
                lines.append(f"- {s.label}: {s.bid_ratio:.1f}% → 수주확률 {s.win_probability:.0%}")
        if self.market_context and self.market_context.avg_bid_ratio:
            lines.append("\n### 시장 컨텍스트")
            lines.append(f"- 도메인 평균 낙찰률: {self.market_context.avg_bid_ratio:.1f}%")
            lines.append(f"- 평균 참여 업체: {self.market_context.avg_num_bidders:.1f}개")
        return "\n".join(lines)


class QuickEstimateResult(BaseModel):
    recommended_ratio: float
    recommended_bid: int
    win_probability: float
    win_probability_confidence: str
    comparable_cases: int
    data_quality: str
    market_avg_ratio: float | None = None
    positioning_adjustment: str = ""
