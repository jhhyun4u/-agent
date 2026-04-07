"""분석 도메인 응답 스키마."""

from pydantic import BaseModel


# ── 하위 아이템 모델 ──

class FailureReasonItem(BaseModel):
    reason: str
    count: int
    percentage: float


class PositioningItem(BaseModel):
    positioning: str
    total: int
    won: int
    win_rate: float


class MonthlyTrendItem(BaseModel):
    month: str
    submitted: int = 0
    won: int = 0
    lost: int = 0
    won_amount: int = 0
    win_rate: float | None = None


class WinRateItem(BaseModel):
    period: str
    total: int = 0
    won: int = 0
    lost: int = 0
    won_amount: int = 0
    win_rate: float = 0.0


class TeamPerformanceItem(BaseModel):
    team_id: str
    total: int = 0
    won: int = 0
    lost: int = 0
    won_amount: int = 0
    win_rate: float = 0.0


class CompetitorItem(BaseModel):
    competitor: str
    encounters: int = 0
    won_against: int = 0
    lost_to: int = 0


class ClientWinRateItem(BaseModel):
    client: str
    total: int = 0
    won: int = 0
    win_rate: float = 0.0
    won_amount: int = 0


# ── 응답 모델 ──

class FailureReasonsResponse(BaseModel):
    period: str | None = None
    scope: str = ""
    total_failed: int = 0
    reasons: list[FailureReasonItem] = []


class PositioningWinRateResponse(BaseModel):
    period: str | None = None
    scope: str = ""
    positionings: list[PositioningItem] = []


class MonthlyTrendsResponse(BaseModel):
    scope: str = ""
    from_date: str | None = None
    to_date: str | None = None
    data: list[MonthlyTrendItem] = []


class WinRateResponse(BaseModel):
    granularity: str = ""
    scope: str = ""
    data: list[WinRateItem] = []


class TeamPerformanceResponse(BaseModel):
    period: str | None = None
    scope: str = ""
    teams: list[TeamPerformanceItem] = []


class CompetitorResponse(BaseModel):
    period: str | None = None
    scope: str = ""
    competitors: list[CompetitorItem] = []


class ClientWinRateResponse(BaseModel):
    period: str | None = None
    scope: str = ""
    clients: list[ClientWinRateItem] = []
