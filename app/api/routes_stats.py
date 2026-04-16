"""낙찰률 통계 API (Phase D)

GET /api/stats/win-rate — scope별 낙찰률 집계.
모든 엔드포인트는 Bearer JWT 인증 필수.
"""

import logging
from collections import defaultdict
from typing import List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.api.response import ok
from app.exceptions import InternalServiceError, TenopAPIError
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["stats"])


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

async def get_win_rate(
    user=Depends(get_current_user),
    scope: str = Query("team", description="team | division | company"),
):
    """낙찰률 통계 조회 (3개 스코프만 지원)

    - team: 본인이 속한 팀의 proposals
    - division: 본인이 속한 본부의 proposals  
    - company: 전사 proposals (경영진만 접근 가능)
    win_result IN ('won', 'lost') 인 레코드만 집계.
    """
    try:
        from fastapi import HTTPException
        client = await get_async_client()

        # proposals 기본 쿼리: win_result 확정된 건만
        query = client.table("proposals").select(
            "id, win_result, owner_id, team_id, created_at"
        ).in_("win_result", ["won", "lost"])

        if scope == "team":
            # 팀원: 자신의 팀 데이터만
            team_res = (
                await client.table("team_members")
                .select("team_id")
                .eq("user_id", user.id)
                .execute()
            )
            my_team_ids = [r["team_id"] for r in (team_res.data or [])]
            if my_team_ids:
                # team_id가 내 팀 중 하나인 proposals
                query = query.in_("team_id", my_team_ids)
            else:
                # 팀 미할당: 빈 결과
                return ok({
                    "overall": {"total": 0, "won": 0, "lost": 0, "rate": 0.0},
                    "by_month": [],
                    "by_agency": [],
                })
        elif scope == "division":
            # 본부장/경영진: 자신의 본부 데이터
            if not user.division_id:
                return ok({
                    "overall": {"total": 0, "won": 0, "lost": 0, "rate": 0.0},
                    "by_month": [],
                    "by_agency": [],
                })
            # division_id가 같은 팀의 proposals
            teams = await client.table("teams").select("id").eq("division_id", user.division_id).execute()
            div_team_ids = [t["id"] for t in (teams.data or [])]
            if div_team_ids:
                query = query.in_("team_id", div_team_ids)
            else:
                return ok({
                    "overall": {"total": 0, "won": 0, "lost": 0, "rate": 0.0},
                    "by_month": [],
                    "by_agency": [],
                })
        elif scope == "company":
            # 경영진: 전사 데이터
            # 권한 체크: 경영진만 접근 가능
            if user.role not in ("executive", "admin"):
                raise HTTPException(status_code=403, detail="경영진만 접근 가능")
            # 모든 proposals 포함 (필터 없음)
        else:
            raise HTTPException(status_code=400, detail="유효한 scope: team, division, company")

        res = await query.execute()
        records = res.data or []

        result = _aggregate(records)
        return ok(result.model_dump())
    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"낙찰률 통계 조회 실패 (scope={scope}): {e}", exc_info=True)
        raise InternalServiceError("낙찰률 통계 조회 중 오류가 발생했습니다.")
