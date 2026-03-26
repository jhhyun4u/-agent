"""관리자 도메인 응답 스키마."""

from pydantic import BaseModel


class UserStats(BaseModel):
    total: int = 0
    active: int = 0
    by_role: dict[str, int] = {}


class ProposalStats(BaseModel):
    total: int = 0
    by_status: dict[str, int] = {}


class SystemStatsResponse(BaseModel):
    """GET /api/admin/stats 응답."""

    users: UserStats = UserStats()
    proposals: ProposalStats = ProposalStats()


class RoleUpdateResponse(BaseModel):
    """PUT /api/admin/users/{user_id}/role 응답."""

    status: str = "ok"
    user_id: str
    role: str


class StatusUpdateResponse(BaseModel):
    """PUT /api/admin/users/{user_id}/status 응답."""

    status: str = "ok"
    user_id: str
    user_status: str


class DivisionTeamDashboardItem(BaseModel):
    team_id: str
    total: int = 0
    running: int = 0
    won: int = 0
    win_rate: float = 0.0
    total_amount: int = 0


class DivisionDashboardResponse(BaseModel):
    """GET /api/dashboard/division 응답."""

    division_id: str
    teams: dict[str, DivisionTeamDashboardItem] = {}
    pending_approvals: list[dict] = []


class MonthlyTrendItem(BaseModel):
    month: str
    submitted: int = 0
    won: int = 0
    amount: int = 0


class PositioningStat(BaseModel):
    won: int = 0
    total: int = 0
    win_rate: float = 0.0


class KpiSummary(BaseModel):
    total_proposals: int = 0
    running: int = 0
    won: int = 0
    decided: int = 0
    win_rate: float = 0.0
    total_won_amount: int = 0


class ExecutiveDashboardResponse(BaseModel):
    """GET /api/dashboard/executive 응답."""

    kpi: KpiSummary = KpiSummary()
    by_positioning: dict[str, PositioningStat] = {}
    monthly_trends: list[MonthlyTrendItem] = []


class VersionItem(BaseModel):
    checkpoint_id: str
    step: str
    next: list[str] = []
    has_sections: bool = False
    has_strategy: bool = False
    has_plan: bool = False


class ProposalVersionsResponse(BaseModel):
    """GET /api/proposals/{proposal_id}/versions 응답."""

    proposal_id: str
    versions: list[VersionItem] = []


class TimeTravelResponse(BaseModel):
    """GET /api/proposals/{proposal_id}/time-travel/{checkpoint_id} 응답."""

    proposal_id: str
    checkpoint_id: str
    current_step: str = ""
    positioning: str | None = None
    mode: str | None = None
    has_rfp_analysis: bool = False
    has_go_no_go: bool = False
    has_strategy: bool = False
    has_plan: bool = False
    sections_count: int = 0
    slides_count: int = 0
    compliance_count: int = 0
    next_nodes: list[str] = []


class ReopenResponse(BaseModel):
    status: str = "ok"
    proposal_id: str
    new_status: str = "draft"
