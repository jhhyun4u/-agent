"""성과 도메인 응답 스키마."""

from pydantic import BaseModel


class IndividualPerformance(BaseModel):
    """GET /api/performance/individual/{user_id} 응답."""

    user_id: str
    total_proposals: int = 0
    completed: int = 0
    won_count: int = 0
    decided_count: int = 0
    win_rate: float = 0.0
    total_won_amount: int = 0
    avg_duration_days: float | None = None


class TeamQuarterPerformance(BaseModel):
    team_id: str
    quarters: list[dict] = []
    total_proposals: int = 0
    won_count: int = 0
    decided_count: int = 0
    win_rate: float = 0.0
    total_won_amount: int = 0
    avg_tech_score: float | None = None


class DivisionTeamStat(BaseModel):
    team_id: str
    total: int = 0
    won: int = 0
    amount: int = 0
    win_rate: float = 0.0


class DivisionPerformance(BaseModel):
    """GET /api/performance/division/{div_id} 응답."""

    division_id: str
    total_proposals: int = 0
    won_count: int = 0
    decided_count: int = 0
    win_rate: float = 0.0
    total_won_amount: int = 0
    teams: list[DivisionTeamStat] = []


class PositioningStat(BaseModel):
    total: int = 0
    won: int = 0
    win_rate: float = 0.0
    total_amount: int = 0


class CompanyPerformance(BaseModel):
    """GET /api/performance/company 응답."""

    by_positioning: dict[str, PositioningStat] = {}
    total_proposals: int = 0


class TrendItem(BaseModel):
    period: str
    submitted: int = 0
    won: int = 0
    lost: int = 0
    amount: int = 0


class PerformanceTrends(BaseModel):
    """GET /api/performance/trends 응답."""

    period: str  # monthly | quarterly | yearly
    data: list[TrendItem] = []


class MyProjectsDashboard(BaseModel):
    """GET /api/dashboard/my-projects 응답."""

    created: list[dict] = []
    participating: list[dict] = []


class TeamDashboard(BaseModel):
    """GET /api/dashboard/team 응답."""

    team_id: str
    proposals: list[dict] = []
    step_distribution: dict[str, int] = {}
    total: int = 0
