"""
Dashboard KPI 응답 스키마 (설계: 섹션 4)

대시보드 API 응답 데이터 모델:
- DashboardIndividualMetrics: 개인 대시보드 KPI
- DashboardTeamMetrics: 팀 대시보드 KPI
- DashboardDepartmentMetrics: 본부 대시보드 KPI
- DashboardExecutiveMetrics: 경영진 대시보드 KPI
- DashboardTimelineResponse: 월별 이력
- DashboardDetailsResponse: 상세 드릴다운
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


# ════════════════════════════════════════════════════════════════════
# 개인 대시보드 (Individual)
# ════════════════════════════════════════════════════════════════════

class DashboardIndividualMetrics(BaseModel):
    """개인 대시보드 메트릭"""
    in_progress_proposals: int = Field(..., description="진행 중인 제안서 수")
    completed_this_month: int = Field(..., description="이번 달 완료한 제안서 수")
    recent_won: int = Field(..., description="최근 수주한 제안서 수")
    recent_lost: int = Field(..., description="최근 낙찰한 제안서 수")
    total_amount_won: int = Field(..., description="수주한 총 금액 (원)")
    avg_days_to_complete: float = Field(..., description="평균 완료 소요일수")


# ════════════════════════════════════════════════════════════════════
# 팀 대시보드 (Team)
# ════════════════════════════════════════════════════════════════════

class PositioningBreakdown(BaseModel):
    """포지셔닝별 성공률"""
    positioning: str = Field(..., description="포지셔닝 이름")
    win_rate: float = Field(..., description="수주율 (%)")
    total: int = Field(..., description="총 제안 건수")
    won: int = Field(..., description="수주 건수")


class DashboardTeamMetrics(BaseModel):
    """팀 대시보드 메트릭"""
    team_id: str = Field(..., description="팀 ID")
    team_name: str = Field(..., description="팀 이름")
    division_name: Optional[str] = Field(None, description="본부 이름")
    win_rate: float = Field(..., description="팀 수주율 (%)")
    total_proposals: int = Field(..., description="총 제안서 수")
    won_count: int = Field(..., description="수주한 제안서 수")
    total_won_amount: int = Field(..., description="수주한 총 금액 (원)")
    avg_deal_size: int = Field(..., description="평균 건당 금액 (원)")
    avg_tech_score: float = Field(..., description="평균 기술점수")
    month_over_month_change: float = Field(..., description="전월 대비 수주율 변화율 (%)")
    positioning_breakdown: List[PositioningBreakdown] = Field(
        default_factory=list, description="포지셔닝별 성공률"
    )


# ════════════════════════════════════════════════════════════════════
# 본부 대시보드 (Department)
# ════════════════════════════════════════════════════════════════════

class TeamComparisonItem(BaseModel):
    """팀별 비교 항목"""
    team_id: str = Field(..., description="팀 ID")
    team_name: str = Field(..., description="팀 이름")
    win_rate: float = Field(..., description="수주율 (%)")
    won_count: int = Field(..., description="수주 건수")
    total_proposals: int = Field(..., description="총 제안 건수")
    total_won_amount: int = Field(..., description="수주한 총 금액 (원)")
    rank: int = Field(..., description="순위")


class CompetitorItem(BaseModel):
    """경쟁사 분석 항목"""
    competitor_name: str = Field(..., description="경쟁사 이름")
    lost_to_them_count: int = Field(..., description="경쟁사에게 진 건수")
    lost_rate: float = Field(..., description="패율 (%)")
    trend: str = Field(..., description="추이 (up/down/neutral)")


class DashboardDepartmentMetrics(BaseModel):
    """본부 대시보드 메트릭"""
    division_id: str = Field(..., description="본부 ID")
    division_name: str = Field(..., description="본부 이름")
    win_rate: float = Field(..., description="본부 수주율 (%)")
    target_win_rate: float = Field(..., description="목표 수주율 (%)")
    variance: float = Field(..., description="목표 대비 차이 (%)")
    status: str = Field(..., description="상태 (below_target/at_target/above_target)")
    total_proposals: int = Field(..., description="총 제안서 수")
    total_won_amount: int = Field(..., description="수주한 총 금액 (원)")
    team_comparison: List[TeamComparisonItem] = Field(
        default_factory=list, description="팀별 비교"
    )
    competitor_top_3: List[CompetitorItem] = Field(
        default_factory=list, description="경쟁사 상위 3개"
    )


# ════════════════════════════════════════════════════════════════════
# 경영진 대시보드 (Executive)
# ════════════════════════════════════════════════════════════════════

class KPICard(BaseModel):
    """KPI 카드"""
    label: str = Field(..., description="라벨")
    value: float = Field(..., description="값")
    unit: str = Field(..., description="단위")
    trend: Optional[str] = Field(None, description="추이 (up/down/neutral)")


class DivisionComparisonItem(BaseModel):
    """본부별 비교 항목"""
    division_id: str = Field(..., description="본부 ID")
    division_name: str = Field(..., description="본부 이름")
    win_rate: float = Field(..., description="수주율 (%)")
    target_win_rate: float = Field(..., description="목표 수주율 (%)")
    total_proposals: int = Field(..., description="총 제안 건수")
    total_won_amount: int = Field(..., description="수주한 총 금액 (원)")
    status: str = Field(..., description="상태 (below_target/at_target/above_target)")


class DashboardExecutiveMetrics(BaseModel):
    """경영진 대시보드 메트릭"""
    overall_win_rate: float = Field(..., description="전사 수주율 (%)")
    total_won_amount: int = Field(..., description="총 수주 금액 (원)")
    total_proposal_count: int = Field(..., description="총 제안서 수")
    avg_proposal_value: int = Field(..., description="평균 제안 건당 금액 (원)")
    division_comparison: List[DivisionComparisonItem] = Field(
        default_factory=list, description="본부별 비교"
    )


# ════════════════════════════════════════════════════════════════════
# 타임라인 (월별 이력)
# ════════════════════════════════════════════════════════════════════

class TimelineDataPoint(BaseModel):
    """타임라인 데이터 포인트"""
    month: str = Field(..., description="월 (YYYY-MM)")
    period_label: str = Field(..., description="기간 라벨 (e.g., 'May 2025')")
    win_rate: Optional[float] = Field(None, description="수주율 (%)")
    proposal_count: int = Field(..., description="제안서 수")
    won_count: int = Field(..., description="수주 건수")
    total_amount: int = Field(..., description="총 금액 (원)")


class TimelineSummary(BaseModel):
    """타임라인 요약"""
    trend: str = Field(..., description="추이 (up/down/flat)")
    avg_win_rate: float = Field(..., description="평균 수주율 (%)")
    best_month: str = Field(..., description="최고 성과 월")
    best_month_value: float = Field(..., description="최고 수주율 (%)")


class DashboardTimelineResponse(BaseModel):
    """타임라인 응답"""
    dashboard_type: str = Field(..., description="대시보드 유형")
    team_id: Optional[str] = Field(None, description="팀 ID (team 유형일 때)")
    division_id: Optional[str] = Field(None, description="본부 ID (department 유형일 때)")
    metric: str = Field(..., description="메트릭 유형")
    data: List[TimelineDataPoint] = Field(..., description="타임라인 데이터")
    summary: TimelineSummary = Field(..., description="요약")


# ════════════════════════════════════════════════════════════════════
# 상세 드릴다운 (Details)
# ════════════════════════════════════════════════════════════════════

class RecentProject(BaseModel):
    """최근 프로젝트"""
    proposal_id: str = Field(..., description="제안서 ID")
    title: str = Field(..., description="제목")
    result: str = Field(..., description="결과 (won/lost)")
    amount: int = Field(..., description="금액 (원)")
    result_date: str = Field(..., description="결과 날짜 (YYYY-MM-DD)")


class DetailTeamItem(BaseModel):
    """상세 조회 - 팀 항목"""
    team_id: str = Field(..., description="팀 ID")
    team_name: str = Field(..., description="팀 이름")
    team_lead: Optional[str] = Field(None, description="팀장 이름")
    team_size: int = Field(..., description="팀 규모 (명)")
    win_rate: float = Field(..., description="수주율 (%)")
    total_proposals: int = Field(..., description="총 제안 건수")
    won_count: int = Field(..., description="수주 건수")
    total_won_amount: int = Field(..., description="수주한 총 금액 (원)")
    recent_projects: List[RecentProject] = Field(
        default_factory=list, description="최근 프로젝트"
    )


class DashboardDetailsResponse(BaseModel):
    """상세 드릴다운 응답"""
    dashboard_type: str = Field(..., description="대시보드 유형")
    filter_type: str = Field(..., description="필터 유형 (team/region/client/positioning)")
    total_count: int = Field(..., description="총 항목 수")
    data: List[DetailTeamItem] = Field(..., description="상세 데이터")


# ════════════════════════════════════════════════════════════════════
# 통합 응답 (각 엔드포인트별)
# ════════════════════════════════════════════════════════════════════

class MetricsResponse(BaseModel):
    """메트릭 조회 응답"""
    dashboard_type: str = Field(..., description="대시보드 유형")
    period: str = Field(..., description="기간 (ytd/mtd/custom)")
    generated_at: datetime = Field(..., description="생성 시간")
    cache_hit: bool = Field(..., description="캐시 히트 여부")
    cache_ttl_seconds: int = Field(..., description="캐시 TTL (초)")
    metrics: dict = Field(..., description="메트릭 데이터")


class ErrorResponse(BaseModel):
    """표준 에러 응답"""
    error_code: str = Field(..., description="에러 코드")
    message: str = Field(..., description="에러 메시지")
    detail: Optional[dict] = Field(None, description="상세 정보")
