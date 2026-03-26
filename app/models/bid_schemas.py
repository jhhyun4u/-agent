"""입찰 추천 기능 Pydantic 스키마"""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ── 공고 원문 ────────────────────────────────────────────────

class BidAnnouncement(BaseModel):
    bid_no: str
    bid_title: str
    agency: str
    bid_type: Optional[str] = None
    budget_amount: Optional[int] = None
    announce_date: Optional[date] = None
    deadline_date: Optional[datetime] = None
    days_remaining: Optional[int] = None
    content_text: Optional[str] = None
    qualification_available: bool = True


# ── 팀 입찰 프로필 ───────────────────────────────────────────

class TeamBidProfile(BaseModel):
    team_id: str
    expertise_areas: list[str] = []
    tech_keywords: list[str] = []
    past_projects: str = ""
    company_size: Optional[str] = None
    certifications: list[str] = []
    business_registration_type: Optional[str] = None
    employee_count: Optional[int] = None
    founded_year: Optional[int] = None


class TeamBidProfileCreate(BaseModel):
    expertise_areas: list[str] = []
    tech_keywords: list[str] = []
    past_projects: str = ""
    company_size: Optional[str] = None
    certifications: list[str] = []
    business_registration_type: Optional[str] = None
    employee_count: Optional[int] = Field(default=None, ge=0)
    founded_year: Optional[int] = Field(default=None, ge=1900, le=2100)


# ── 검색 프리셋 ──────────────────────────────────────────────

class SearchPresetCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    keywords: list[str] = Field(min_length=1, max_length=5)
    min_budget: int = Field(default=100_000_000, ge=0, le=100_000_000_000)
    min_days_remaining: int = Field(default=5, ge=1, le=30)
    bid_types: list[str] = Field(default=["용역"], min_length=1)
    preferred_agencies: list[str] = []
    announce_date_range_days: int = Field(default=14, ge=0, le=365)

    @field_validator("bid_types")
    @classmethod
    def validate_bid_types(cls, v: list[str]) -> list[str]:
        allowed = {"용역", "공사", "물품"}
        invalid = set(v) - allowed
        if invalid:
            raise ValueError(f"허용되지 않는 공고종류: {invalid}. 허용값: {allowed}")
        return v

    @field_validator("keywords")
    @classmethod
    def validate_keywords(cls, v: list[str]) -> list[str]:
        for kw in v:
            if len(kw) > 20:
                raise ValueError(f"키워드는 20자 이하여야 합니다: '{kw[:20]}...'")
        return v


class SearchPreset(SearchPresetCreate):
    id: str
    team_id: str
    is_active: bool = False
    last_fetched_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ── Claude 1단계: 자격 판정 응답 스키마 ─────────────────────

class QualificationResult(BaseModel):
    bid_no: str
    qualification_status: Literal["pass", "fail", "ambiguous"]
    disqualification_reason: Optional[str] = None   # fail일 때
    qualification_notes: Optional[str] = None        # ambiguous일 때


# ── Claude 2단계: 매칭 점수 응답 스키마 ─────────────────────

class RecommendationReason(BaseModel):
    category: Literal["전문성", "실적", "규모", "기술", "지역", "기타"]
    reason: str
    strength: Literal["high", "medium", "low"]


class RiskFactor(BaseModel):
    risk: str
    level: Literal["high", "medium", "low"]


class BidRecommendation(BaseModel):
    bid_no: str
    match_score: int = Field(ge=0, le=100)
    match_grade: Literal["S", "A", "B", "C", "D"]
    recommendation_summary: str
    recommendation_reasons: list[RecommendationReason] = Field(min_length=1)
    risk_factors: list[RiskFactor] = []
    win_probability_hint: str
    recommended_action: str


# ── API 응답 복합 스키마 ─────────────────────────────────────

class RecommendedBid(BaseModel):
    """추천 공고 카드 (공고 정보 + AI 분석 합산)"""
    bid_no: str
    bid_title: str
    agency: str
    budget_amount: Optional[int] = None
    deadline_date: Optional[datetime] = None
    days_remaining: Optional[int] = None
    qualification_status: Literal["pass", "ambiguous"]
    qualification_notes: Optional[str] = None
    match_score: int
    match_grade: str
    recommendation_summary: str
    recommendation_reasons: list[RecommendationReason]
    risk_factors: list[RiskFactor] = []
    win_probability_hint: str
    recommended_action: str


class ExcludedBid(BaseModel):
    """제외된 공고 (자격 불충족)"""
    bid_no: str
    bid_title: str
    agency: str
    budget_amount: Optional[int] = None
    deadline_date: Optional[datetime] = None
    qualification_status: Literal["fail"]
    disqualification_reason: Optional[str] = None


class RecommendationsMeta(BaseModel):
    total_fetched: int
    analyzed_at: datetime


class RecommendationsData(BaseModel):
    recommended: list[RecommendedBid] = []
    excluded: list[ExcludedBid] = []


class RecommendationsResponse(BaseModel):
    data: RecommendationsData
    meta: RecommendationsMeta


# ── 전처리 요약 (Stage 1) ────────────────────────────────────

class BidSummary(BaseModel):
    """전처리 에이전트 출력: 공고문 핵심 섹션 추출 결과"""
    bid_no: str
    organization: str = ""
    budget_detail: str = ""
    period: str = ""
    purpose: str = ""
    core_tasks: list[str] = []
    required_license: str = ""
    experience_needed: str = ""
    restriction: str = ""
    evaluation_points: str = ""

    def to_text(self) -> str:
        """리뷰어 프롬프트에 주입할 텍스트 변환."""
        lines = []
        if self.organization:
            lines.append(f"발주기관: {self.organization}")
        if self.budget_detail:
            lines.append(f"예산: {self.budget_detail}")
        if self.period:
            lines.append(f"기간: {self.period}")
        if self.core_tasks:
            lines.append("주요 과업:")
            for t in self.core_tasks:
                lines.append(f"  - {t}")
        if self.required_license:
            lines.append(f"필수 면허: {self.required_license}")
        if self.experience_needed:
            lines.append(f"실적 요건: {self.experience_needed}")
        if self.restriction:
            lines.append(f"제한 사항: {self.restriction}")
        if self.evaluation_points:
            lines.append(f"평가 배점: {self.evaluation_points}")
        return "\n".join(lines)


# ── TENOPA 리뷰 결과 (Stage 2) ──────────────────────────────

class ReasonAnalysis(BaseModel):
    """TENOPA 리뷰어 강점/리스크 분석"""
    strengths: list[str] = []
    risks: list[str] = []


class TenopaBidReview(BaseModel):
    """TENOPA 수주 심의위원 평가 결과"""
    bid_no: str
    bid_title: str = ""
    suitability_score: int = Field(ge=0, le=100)
    verdict: Literal["추천", "검토 필요", "제외"]
    reason_analysis: ReasonAnalysis = ReasonAnalysis()
    action_plan: str = ""
