"""낙찰률 통계 API (Phase D)

GET /api/stats/win-rate — scope별 낙찰률 집계.
모든 엔드포인트는 Bearer JWT 인증 필수.
"""

import logging
from collections import defaultdict
from typing import List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.middleware.auth import get_current_user
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["stats"])


# ── 응답 스키마 ───────────────────────────────────────────────────────

class OverallStat(BaseModel):
    total: int
    won: int
    rate: float


class AgencyStat(BaseModel):
    agency: str
    total: int
    won: int
    rate: float


class MonthStat(BaseModel):
    month: str  # YYYY-MM 포맷
    total: int
    won: int
    rate: float


class WinRateResponse(BaseModel):
    overall: OverallStat
    by_agency: List[AgencyStat]
    by_month: List[MonthStat]


# ── 헬퍼 ─────────────────────────────────────────────────────────────

def _calc_rate(won: int, total: int) -> float:
    """낙찰률 계산 (소수점 2자리 반올림)"""
    if total == 0:
        return 0.0
    return round(won / total, 2)


def _aggregate(records: list) -> WinRateResponse:
    """레코드 목록에서 전체·기관별·월별 통계 계산"""
    total = len(records)
    won_total = sum(1 for r in records if r.get("win_result") == "won")

    # 기관별
    agency_map: dict[str, dict] = defaultdict(lambda: {"total": 0, "won": 0})
    for r in records:
        agency = r.get("client_name") or "미분류"
        agency_map[agency]["total"] += 1
        if r.get("win_result") == "won":
            agency_map[agency]["won"] += 1

    by_agency = [
        AgencyStat(
            agency=agency,
            total=data["total"],
            won=data["won"],
            rate=_calc_rate(data["won"], data["total"]),
        )
        for agency, data in sorted(agency_map.items())
    ]

    # 월별 (created_at 기준 YYYY-MM)
    month_map: dict[str, dict] = defaultdict(lambda: {"total": 0, "won": 0})
    for r in records:
        created_at = r.get("created_at") or ""
        month = created_at[:7] if len(created_at) >= 7 else "unknown"
        month_map[month]["total"] += 1
        if r.get("win_result") == "won":
            month_map[month]["won"] += 1

    by_month = [
        MonthStat(
            month=month,
            total=data["total"],
            won=data["won"],
            rate=_calc_rate(data["won"], data["total"]),
        )
        for month, data in sorted(month_map.items())
    ]

    return WinRateResponse(
        overall=OverallStat(total=total, won=won_total, rate=_calc_rate(won_total, total)),
        by_agency=by_agency,
        by_month=by_month,
    )


# ── 엔드포인트 ────────────────────────────────────────────────────────

@router.get("/stats/win-rate", response_model=WinRateResponse)
async def get_win_rate(
    user=Depends(get_current_user),
    scope: str = Query("personal", description="personal | team | company"),
):
    """낙찰률 통계 조회

    - personal: 본인 소유 proposals
    - team: 본인이 속한 팀의 proposals
    - company: 접근 가능한 모든 proposals
    win_result IN ('won', 'lost') 인 레코드만 집계.
    """
    client = await get_async_client()

    # proposals 기본 쿼리: win_result 확정된 건만
    query = client.table("proposals").select(
        "id, win_result, client_name, owner_id, team_id, created_at"
    ).in_("win_result", ["won", "lost"])

    if scope == "personal":
        query = query.eq("owner_id", user.id)
    elif scope == "team":
        team_res = (
            await client.table("team_members")
            .select("team_id")
            .eq("user_id", user.id)
            .execute()
        )
        my_team_ids = [r["team_id"] for r in (team_res.data or [])]
        if my_team_ids:
            team_ids_csv = ",".join(my_team_ids)
            query = query.or_(f"owner_id.eq.{user.id},team_id.in.({team_ids_csv})")
        else:
            query = query.eq("owner_id", user.id)
    else:
        # company: 본인 소유 + 팀 소속
        team_res = (
            await client.table("team_members")
            .select("team_id")
            .eq("user_id", user.id)
            .execute()
        )
        my_team_ids = [r["team_id"] for r in (team_res.data or [])]
        if my_team_ids:
            team_ids_csv = ",".join(my_team_ids)
            query = query.or_(f"owner_id.eq.{user.id},team_id.in.({team_ids_csv})")
        else:
            query = query.eq("owner_id", user.id)

    res = await query.execute()
    records = res.data or []

    return _aggregate(records)
