"""
분석 대시보드 API (§12-13, v3.4)

GET /api/analytics/failure-reasons       — 실패 원인 분포 (파이 차트)
GET /api/analytics/positioning-win-rate  — 포지셔닝별 수주율 (바 차트)
GET /api/analytics/monthly-trends        — 월별 수주율 추이 (라인 차트)
GET /api/analytics/client-win-rate       — 기관별 수주 현황 (바 차트)

권한: lead, director, executive, admin
기간: period=2026Q1 / from=YYYY-MM&to=YYYY-MM
스코프: scope=team|division|company (기본: 역할 기반 자동 결정)
"""

import logging

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.models.auth_schemas import CurrentUser
from app.models.analytics_schemas import (
    FailureReasonsResponse, PositioningWinRateResponse, MonthlyTrendsResponse,
    WinRateResponse, TeamPerformanceResponse, CompetitorResponse, ClientWinRateResponse,
)
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


# ════════════════════════════════════════
# 공통 헬퍼
# ════════════════════════════════════════

def _resolve_scope(user: CurrentUser, scope: str | None) -> str:
    """사용자 역할에 따라 기본 스코프 결정."""
    if scope:
        return scope
    role = user.role
    if role in ("executive", "admin"):
        return "company"
    if role == "director":
        return "division"
    return "team"


def _period_to_date_range(period: str | None) -> tuple[str | None, str | None]:
    """
    기간 문자열을 (start_date, end_date) ISO 문자열로 변환.
    지원 형식: 2026Q1, 2026H1, 2025
    """
    if not period:
        return None, None

    try:
        if "Q" in period:
            year, q = period.split("Q")
            q = int(q)
            start_month = (q - 1) * 3 + 1
            end_month = q * 3
            return f"{year}-{start_month:02d}-01", f"{year}-{end_month:02d}-28"
        if "H" in period:
            year, h = period.split("H")
            h = int(h)
            start_month = (h - 1) * 6 + 1
            end_month = h * 6
            return f"{year}-{start_month:02d}-01", f"{year}-{end_month:02d}-28"
        # 연도만
        return f"{period}-01-01", f"{period}-12-31"
    except (ValueError, IndexError):
        return None, None


async def _fetch_proposals(
    user: CurrentUser,
    scope: str,
    date_start: str | None = None,
    date_end: str | None = None,
    fields: str = "id, win_result, bid_amount, positioning, status, created_at, team_id",
) -> list[dict]:
    """스코프에 따라 제안서 목록 조회."""
    client = await get_async_client()
    query = client.table("proposals").select(fields)

    if scope == "team":
        team_id = user.team_id or ""
        query = query.eq("team_id", team_id)
    elif scope == "division":
        # division_id가 teams에 없을 수 있으므로 안전하게 처리
        try:
            div_id = user.division_id or ""
            teams = await client.table("teams").select("id").eq("division_id", div_id).execute()
            team_ids = [t["id"] for t in (teams.data or [])]
            if team_ids:
                query = query.in_("team_id", team_ids)
            else:
                return []
        except Exception:
            # division_id 컬럼 없으면 company 스코프로 폴백
            pass
    # scope == "company" → 필터 없음

    if date_start:
        query = query.gte("created_at", date_start)
    if date_end:
        query = query.lte("created_at", date_end + "T23:59:59")

    result = await query.execute()
    return result.data or []


# ════════════════════════════════════════
# 실패 원인 분포
# ════════════════════════════════════════

@router.get("/failure-reasons", response_model=FailureReasonsResponse)
async def failure_reasons(
    period: str | None = Query(None, description="기간 (예: 2026Q1, 2026H1, 2025)"),
    scope: str | None = Query(None, pattern="^(team|division|company)$"),
    user: CurrentUser = Depends(get_current_user),
):
    """실패 원인 분포 (파이 차트 데이터)."""
    resolved_scope = _resolve_scope(user, scope)
    date_start, date_end = _period_to_date_range(period)

    data = await _fetch_proposals(user, resolved_scope, date_start, date_end)

    # 패찰 건만 필터
    failed = [d for d in data if d.get("win_result") == "lost"]
    total_failed = len(failed)

    if total_failed == 0:
        return {
            "period": period,
            "scope": resolved_scope,
            "total_failed": 0,
            "reasons": [],
        }

    # result_note에서 패찰 사유 분류
    reason_counts: dict[str, int] = {}
    for d in failed:
        reason = (d.get("result_note") or "기타/불명").strip()
        if not reason:
            reason = "기타/불명"
        reason_counts[reason] = reason_counts.get(reason, 0) + 1

    reasons = sorted(reason_counts.items(), key=lambda x: x[1], reverse=True)

    return {
        "period": period,
        "scope": resolved_scope,
        "total_failed": total_failed,
        "reasons": [
            {
                "reason": reason,
                "count": count,
                "percentage": round(count / total_failed * 100, 1),
            }
            for reason, count in reasons
        ],
    }


# ════════════════════════════════════════
# 포지셔닝별 수주율
# ════════════════════════════════════════

@router.get("/positioning-win-rate", response_model=PositioningWinRateResponse)
async def positioning_win_rate(
    period: str | None = Query(None, description="기간 (예: 2026Q1)"),
    scope: str | None = Query(None, pattern="^(team|division|company)$"),
    user: CurrentUser = Depends(get_current_user),
):
    """포지셔닝별 수주율 (바 차트 데이터)."""
    resolved_scope = _resolve_scope(user, scope)
    date_start, date_end = _period_to_date_range(period)

    data = await _fetch_proposals(user, resolved_scope, date_start, date_end)

    # 결과 확정 건만 (수주 or 패찰)
    decided = [d for d in data if d.get("win_result") in ("won", "lost")]

    by_pos: dict[str, dict] = {}
    for d in decided:
        pos = d.get("positioning") or "unknown"
        if pos not in by_pos:
            by_pos[pos] = {"total": 0, "won": 0}
        by_pos[pos]["total"] += 1
        if d.get("win_result") == "won":
            by_pos[pos]["won"] += 1

    positionings = []
    for pos, stats in sorted(by_pos.items()):
        positionings.append({
            "positioning": pos,
            "total": stats["total"],
            "won": stats["won"],
            "win_rate": round(stats["won"] / stats["total"] * 100, 1) if stats["total"] else 0,
        })

    return {
        "period": period,
        "scope": resolved_scope,
        "positionings": positionings,
    }


# ════════════════════════════════════════
# 월별 수주율 추이
# ════════════════════════════════════════

@router.get("/monthly-trends", response_model=MonthlyTrendsResponse)
async def monthly_trends(
    date_from: str | None = Query(None, alias="from", description="시작월 (YYYY-MM)"),
    date_to: str | None = Query(None, alias="to", description="종료월 (YYYY-MM)"),
    scope: str | None = Query(None, pattern="^(team|division|company)$"),
    user: CurrentUser = Depends(get_current_user),
):
    """월별 수주율 추이 (라인 차트 데이터)."""
    resolved_scope = _resolve_scope(user, scope)

    start = f"{date_from}-01" if date_from else None
    end = f"{date_to}-28" if date_to else None

    data = await _fetch_proposals(user, resolved_scope, start, end)

    # 월별 집계
    by_month: dict[str, dict] = {}
    for d in data:
        month = (d.get("created_at") or "")[:7]  # YYYY-MM
        if not month:
            continue
        if month not in by_month:
            by_month[month] = {"month": month, "submitted": 0, "won": 0, "lost": 0, "won_amount": 0}
        by_month[month]["submitted"] += 1
        if d.get("win_result") == "won":
            by_month[month]["won"] += 1
            by_month[month]["won_amount"] += d.get("result_amount", 0) or 0
        elif d.get("win_result") == "lost":
            by_month[month]["lost"] += 1

    # 수주율 계산 + 정렬
    trends = []
    for month in sorted(by_month.keys()):
        m = by_month[month]
        decided = m["won"] + m["lost"]
        m["win_rate"] = round(m["won"] / decided * 100, 1) if decided else None
        trends.append(m)

    return {
        "scope": resolved_scope,
        "from": date_from,
        "to": date_to,
        "data": trends,
    }


# ════════════════════════════════════════
# 기관별 수주 현황
# ════════════════════════════════════════

# ════════════════════════════════════════
# 수주율 트렌드 (분기별/연도별) — Phase 4-4
# ════════════════════════════════════════

@router.get("/win-rate", response_model=WinRateResponse)
async def win_rate_trend(
    granularity: str = Query("quarterly", pattern="^(quarterly|yearly)$"),
    period: str | None = Query(None, description="기간 (예: 2026Q1)"),
    scope: str | None = Query(None, pattern="^(team|division|company)$"),
    user: CurrentUser = Depends(get_current_user),
):
    """수주율 트렌드 (분기별/연도별)."""
    resolved_scope = _resolve_scope(user, scope)
    date_start, date_end = _period_to_date_range(period)

    data = await _fetch_proposals(user, resolved_scope, date_start, date_end)
    decided = [d for d in data if d.get("win_result") in ("won", "lost")]

    by_period: dict[str, dict] = {}
    for d in decided:
        created = d.get("created_at", "")[:7]
        if granularity == "quarterly":
            parts = created.split("-")
            if len(parts) == 2:
                q = (int(parts[1]) - 1) // 3 + 1
                key = f"{parts[0]}-Q{q}"
            else:
                key = created
        else:
            key = created[:4]

        if key not in by_period:
            by_period[key] = {"period": key, "total": 0, "won": 0, "lost": 0, "won_amount": 0}
        by_period[key]["total"] += 1
        if d.get("win_result") == "won":
            by_period[key]["won"] += 1
            by_period[key]["won_amount"] += d.get("result_amount", 0) or 0
        else:
            by_period[key]["lost"] += 1

    trends = []
    for key in sorted(by_period.keys()):
        m = by_period[key]
        m["win_rate"] = round(m["won"] / m["total"] * 100, 1) if m["total"] else 0
        trends.append(m)

    return {"granularity": granularity, "scope": resolved_scope, "data": trends}


# ════════════════════════════════════════
# 부서/팀별 성과 비교 — Phase 4-4
# ════════════════════════════════════════

@router.get("/team-performance")
async def team_performance(
    period: str | None = Query(None, description="기간 (예: 2026Q1)"),
    scope: str | None = Query(None, pattern="^(team|division|company)$"),
    user: CurrentUser = Depends(get_current_user),
):
    """부서/팀별 성과 비교."""
    resolved_scope = _resolve_scope(user, scope)
    date_start, date_end = _period_to_date_range(period)

    data = await _fetch_proposals(
        user, resolved_scope, date_start, date_end,
        fields="id, win_result, bid_amount, team_id, created_at",
    )

    by_team: dict[str, dict] = {}
    for d in data:
        tid = d.get("team_id") or "unassigned"
        if tid not in by_team:
            by_team[tid] = {"team_id": tid, "total": 0, "won": 0, "lost": 0, "won_amount": 0}
        by_team[tid]["total"] += 1
        if d.get("win_result") == "won":
            by_team[tid]["won"] += 1
            by_team[tid]["won_amount"] += d.get("result_amount", 0) or 0
        elif d.get("win_result") == "lost":
            by_team[tid]["lost"] += 1

    teams = []
    for stats in by_team.values():
        decided = stats["won"] + stats["lost"]
        stats["win_rate"] = round(stats["won"] / decided * 100, 1) if decided else 0
        teams.append(stats)

    teams.sort(key=lambda x: x["win_rate"], reverse=True)
    return {"period": period, "scope": resolved_scope, "teams": teams}


# ════════════════════════════════════════
# 경쟁사별 대전 기록 — Phase 4-4
# ════════════════════════════════════════

@router.get("/competitor", response_model=CompetitorResponse)
async def competitor_record(
    period: str | None = Query(None, description="기간 (예: 2026Q1)"),
    scope: str | None = Query(None, pattern="^(team|division|company)$"),
    user: CurrentUser = Depends(get_current_user),
):
    """경쟁사별 대전 기록 (패찰 시 낙찰업체 기준)."""
    resolved_scope = _resolve_scope(user, scope)
    date_start, date_end = _period_to_date_range(period)

    # proposal_results에서 won_by 필드 활용
    client = await get_async_client()
    data = await _fetch_proposals(user, resolved_scope, date_start, date_end, fields="id, win_result, bid_amount")

    proposal_ids = [d["id"] for d in data if d.get("win_result") in ("won", "lost")]
    if not proposal_ids:
        return {"period": period, "scope": resolved_scope, "competitors": []}

    results = await client.table("proposal_results").select(
        "proposal_id, result, won_by"
    ).in_("proposal_id", proposal_ids).execute()
    result_map = {r["proposal_id"]: r for r in (results.data or [])}

    by_competitor: dict[str, dict] = {}
    for d in data:
        pr = result_map.get(d["id"])
        if not pr:
            continue
        competitor = pr.get("won_by") or ""
        if not competitor:
            continue

        if competitor not in by_competitor:
            by_competitor[competitor] = {"competitor": competitor, "encounters": 0, "won_against": 0, "lost_to": 0}
        by_competitor[competitor]["encounters"] += 1
        if pr.get("result") == "won":
            by_competitor[competitor]["won_against"] += 1
        elif pr.get("result") == "lost":
            by_competitor[competitor]["lost_to"] += 1

    competitors = sorted(by_competitor.values(), key=lambda x: x["encounters"], reverse=True)
    return {"period": period, "scope": resolved_scope, "competitors": competitors}


# ════════════════════════════════════════
# 기관별 수주 현황
# ════════════════════════════════════════

@router.get("/client-win-rate", response_model=ClientWinRateResponse)
async def client_win_rate(
    period: str | None = Query(None, description="기간 (예: 2026Q1)"),
    scope: str | None = Query(None, pattern="^(team|division|company)$"),
    top_k: int = Query(15, ge=1, le=50, description="상위 기관 수"),
    user: CurrentUser = Depends(get_current_user),
):
    """기관별 수주 현황 (바 차트 데이터)."""
    resolved_scope = _resolve_scope(user, scope)
    date_start, date_end = _period_to_date_range(period)

    data = await _fetch_proposals(user, resolved_scope, date_start, date_end)

    # 결과 확정 건만
    decided = [d for d in data if d.get("win_result") in ("won", "lost")]

    by_client: dict[str, dict] = {}
    for d in decided:
        client_name = (d.get("client_name") or "미지정").strip()
        if not client_name:
            client_name = "미지정"
        if client_name not in by_client:
            by_client[client_name] = {"total": 0, "won": 0, "amount": 0}
        by_client[client_name]["total"] += 1
        if d.get("win_result") == "won":
            by_client[client_name]["won"] += 1
            by_client[client_name]["amount"] += d.get("result_amount", 0) or 0

    # 총 건수 기준 정렬, 상위 N개
    sorted_clients = sorted(by_client.items(), key=lambda x: x[1]["total"], reverse=True)[:top_k]

    clients = []
    for name, stats in sorted_clients:
        clients.append({
            "client": name,
            "total": stats["total"],
            "won": stats["won"],
            "win_rate": round(stats["won"] / stats["total"] * 100, 1) if stats["total"] else 0,
            "won_amount": stats["amount"],
        })

    return {
        "period": period,
        "scope": resolved_scope,
        "clients": clients,
    }
