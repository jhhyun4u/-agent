"""
성과 추적 + 대시보드 API (§12-8, §12-9)

POST /api/proposals/{id}/result              — 제안 결과 등록
GET  /api/performance/individual/{user_id}   — 개인 성과 (§12-9)
GET  /api/performance/team/{id}              — 팀 성과
GET  /api/performance/division/{div_id}      — 본부 성과 (§12-9)
GET  /api/performance/company                — 전사 성과
GET  /api/performance/trends                 — 기간별 추이
GET  /api/dashboard/my-projects              — 내 프로젝트
GET  /api/dashboard/team                     — 팀 파이프라인
GET  /api/dashboard/team/performance         — 팀 성과 요약
"""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.deps import get_current_user, require_role
from app.exceptions import PropNotFoundError
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["performance"])


# ── 제안 결과 등록 (§12-9) ──

class ProposalResultBody(BaseModel):
    result: str  # 수주 | 패찰 | 유찰
    result_amount: int | None = None
    result_note: str = ""


@router.post("/api/proposals/{proposal_id}/result")
async def register_proposal_result(
    proposal_id: str,
    body: ProposalResultBody,
    user=Depends(require_role("lead", "director", "executive", "admin")),
):
    """제안 결과 등록 (수주/패찰/유찰) — 팀장 이상."""
    client = await get_async_client()

    proposal = await client.table("proposals").select("id").eq("id", proposal_id).single().execute()
    if not proposal.data:
        raise PropNotFoundError(proposal_id)

    await client.table("proposals").update({
        "result": body.result,
        "result_amount": body.result_amount,
        "result_note": body.result_note,
        "result_at": datetime.utcnow().isoformat(),
        "status": "won" if body.result == "수주" else "lost" if body.result == "패찰" else "cancelled",
    }).eq("id", proposal_id).execute()

    # Materialized View 갱신 트리거
    try:
        await client.rpc("refresh_team_performance").execute()
    except Exception:
        logger.warning("team_performance 뷰 갱신 실패 (무시)")

    # KB 환류 트리거 (§20-4: 발주기관 이력 + 콘텐츠 등록 후보 + 회고 알림)
    try:
        from app.services.feedback_loop import process_project_completion
        await process_project_completion(proposal_id, body.result)
    except Exception:
        logger.warning("KB 환류 트리거 실패 (무시)")

    return {"status": "ok", "result": body.result}


# ── 성과 추적 API (§12-9) ──

@router.get("/api/performance/individual/{user_id}")
async def get_individual_performance(user_id: str, user=Depends(get_current_user)):
    """개인 성과 (참여·완료·수주 건수)."""
    client = await get_async_client()

    # 생성한 프로젝트
    created = await client.table("proposals").select(
        "id, result, result_amount, created_at, result_at"
    ).eq("created_by", user_id).execute()

    # 참여한 프로젝트
    participated = await client.table("project_teams").select("proposal_id").eq("user_id", user_id).execute()
    participated_ids = [p["proposal_id"] for p in (participated.data or [])]

    participated_proposals = []
    if participated_ids:
        pp = await client.table("proposals").select(
            "id, result, result_amount, created_at, result_at"
        ).in_("id", participated_ids).execute()
        participated_proposals = pp.data or []

    # 중복 제거 (생성 + 참여)
    all_proposals = {d["id"]: d for d in (created.data or []) + participated_proposals}
    data = list(all_proposals.values())

    total = len(data)
    completed = sum(1 for d in data if d.get("result") is not None)
    won = sum(1 for d in data if d.get("result") == "수주")
    decided = sum(1 for d in data if d.get("result") in ("수주", "패찰"))
    won_amount = sum(d.get("result_amount", 0) or 0 for d in data if d.get("result") == "수주")

    # 평균 소요일 (created_at → result_at)
    durations = []
    for d in data:
        if d.get("result_at") and d.get("created_at"):
            try:
                c = datetime.fromisoformat(d["created_at"].replace("Z", "+00:00"))
                r = datetime.fromisoformat(d["result_at"].replace("Z", "+00:00"))
                durations.append((r - c).days)
            except (ValueError, TypeError):
                pass

    return {
        "user_id": user_id,
        "total_proposals": total,
        "completed": completed,
        "won_count": won,
        "decided_count": decided,
        "win_rate": round(won / decided * 100, 1) if decided else 0,
        "total_won_amount": won_amount,
        "avg_duration_days": round(sum(durations) / len(durations), 1) if durations else None,
    }


@router.get("/api/performance/team/{team_id}")
async def get_team_performance(team_id: str, user=Depends(get_current_user)):
    """팀 성과 (수주율·건수·평균 소요일)."""
    client = await get_async_client()
    result = await client.table("team_performance").select("*").eq("team_id", team_id).execute()
    if result.data:
        return result.data[0]

    # Materialized View 없으면 직접 계산
    proposals = await client.table("proposals").select("status, result, result_amount, created_at, result_at").eq("team_id", team_id).execute()
    data = proposals.data or []
    total = len(data)
    won = sum(1 for d in data if d.get("result") == "수주")
    decided = sum(1 for d in data if d.get("result") in ("수주", "패찰"))
    won_amount = sum(d.get("result_amount", 0) or 0 for d in data if d.get("result") == "수주")

    return {
        "team_id": team_id,
        "total_proposals": total,
        "won_count": won,
        "decided_count": decided,
        "win_rate": round(won / decided * 100, 1) if decided else 0,
        "total_won_amount": won_amount,
    }


@router.get("/api/performance/division/{div_id}")
async def get_division_performance(div_id: str, user=Depends(get_current_user)):
    """본부 성과 (수주율·누적 수주액)."""
    client = await get_async_client()

    # 본부 소속 팀 목록 조회
    teams = await client.table("teams").select("id").eq("division_id", div_id).execute()
    team_ids = [t["id"] for t in (teams.data or [])]

    if not team_ids:
        return {
            "division_id": div_id,
            "total_proposals": 0,
            "won_count": 0,
            "decided_count": 0,
            "win_rate": 0,
            "total_won_amount": 0,
            "teams": [],
        }

    # 본부 전체 제안 조회
    proposals = await client.table("proposals").select(
        "id, team_id, result, result_amount"
    ).in_("team_id", team_ids).execute()
    data = proposals.data or []

    total = len(data)
    won = sum(1 for d in data if d.get("result") == "수주")
    decided = sum(1 for d in data if d.get("result") in ("수주", "패찰"))
    won_amount = sum(d.get("result_amount", 0) or 0 for d in data if d.get("result") == "수주")

    # 팀별 요약
    by_team: dict[str, dict] = {}
    for d in data:
        tid = d.get("team_id", "")
        if tid not in by_team:
            by_team[tid] = {"team_id": tid, "total": 0, "won": 0, "amount": 0}
        by_team[tid]["total"] += 1
        if d.get("result") == "수주":
            by_team[tid]["won"] += 1
            by_team[tid]["amount"] += d.get("result_amount", 0) or 0

    team_summaries = []
    for stats in by_team.values():
        team_summaries.append({
            **stats,
            "win_rate": round(stats["won"] / stats["total"] * 100, 1) if stats["total"] else 0,
        })

    return {
        "division_id": div_id,
        "total_proposals": total,
        "won_count": won,
        "decided_count": decided,
        "win_rate": round(won / decided * 100, 1) if decided else 0,
        "total_won_amount": won_amount,
        "teams": team_summaries,
    }


@router.get("/api/performance/company")
async def get_company_performance(user=Depends(get_current_user)):
    """전사 성과 (포지셔닝별 수주율)."""
    client = await get_async_client()
    proposals = await client.table("proposals").select("positioning, result, result_amount").not_.is_("result", "null").execute()
    data = proposals.data or []

    by_positioning = {}
    for d in data:
        pos = d.get("positioning", "unknown")
        if pos not in by_positioning:
            by_positioning[pos] = {"total": 0, "won": 0, "amount": 0}
        by_positioning[pos]["total"] += 1
        if d.get("result") == "수주":
            by_positioning[pos]["won"] += 1
            by_positioning[pos]["amount"] += d.get("result_amount", 0) or 0

    result = {}
    for pos, stats in by_positioning.items():
        result[pos] = {
            "total": stats["total"],
            "won": stats["won"],
            "win_rate": round(stats["won"] / stats["total"] * 100, 1) if stats["total"] else 0,
            "total_amount": stats["amount"],
        }

    return {"by_positioning": result, "total_proposals": len(data)}


@router.get("/api/performance/trends")
async def get_performance_trends(
    period: str = Query("monthly", pattern="^(monthly|quarterly|yearly)$"),
    months: int = Query(12, ge=1, le=60),
    user=Depends(get_current_user),
):
    """기간별 추이 (월/분기/연)."""
    client = await get_async_client()
    proposals = await client.table("proposals").select("created_at, result, result_at, result_amount").order("created_at").execute()
    data = proposals.data or []

    # 간이 월별 집계
    trends = {}
    for d in data:
        created = d.get("created_at", "")[:7]  # YYYY-MM
        if period == "quarterly":
            parts = created.split("-")
            if len(parts) == 2:
                q = (int(parts[1]) - 1) // 3 + 1
                created = f"{parts[0]}-Q{q}"
        elif period == "yearly":
            created = created[:4]

        if created not in trends:
            trends[created] = {"period": created, "submitted": 0, "won": 0, "lost": 0, "amount": 0}
        trends[created]["submitted"] += 1
        if d.get("result") == "수주":
            trends[created]["won"] += 1
            trends[created]["amount"] += d.get("result_amount", 0) or 0
        elif d.get("result") == "패찰":
            trends[created]["lost"] += 1

    return {"period": period, "data": list(trends.values())}


# ── 대시보드 API (§12-8) ──

@router.get("/api/dashboard/my-projects")
async def my_projects(user=Depends(get_current_user)):
    """내 참여 프로젝트 현황."""
    client = await get_async_client()

    # 내가 생성한 프로젝트
    created = await client.table("proposals").select(
        "id, project_name, status, positioning, current_step, created_at, deadline"
    ).eq("created_by", user["id"]).order("created_at", desc=True).limit(20).execute()

    # 내가 참여자인 프로젝트
    participated = await client.table("project_teams").select("proposal_id").eq("user_id", user["id"]).execute()
    participated_ids = [p["proposal_id"] for p in (participated.data or [])]

    participant_proposals = []
    if participated_ids:
        pp = await client.table("proposals").select(
            "id, project_name, status, positioning, current_step, created_at, deadline"
        ).in_("id", participated_ids).order("created_at", desc=True).execute()
        participant_proposals = pp.data or []

    return {
        "created": created.data or [],
        "participating": participant_proposals,
    }


@router.get("/api/dashboard/team")
async def team_dashboard(user=Depends(get_current_user)):
    """팀 제안 파이프라인 (STEP별 분포)."""
    client = await get_async_client()
    team_id = user.get("team_id", "")

    proposals = await client.table("proposals").select(
        "id, project_name, status, current_step, positioning, deadline"
    ).eq("team_id", team_id).order("created_at", desc=True).limit(50).execute()

    data = proposals.data or []
    step_distribution = {}
    for d in data:
        step = d.get("current_step", "unknown")
        step_distribution[step] = step_distribution.get(step, 0) + 1

    return {
        "team_id": team_id,
        "proposals": data,
        "step_distribution": step_distribution,
        "total": len(data),
    }


@router.get("/api/dashboard/team/performance")
async def team_performance_summary(user=Depends(get_current_user)):
    """팀 성과 요약 (수주율·건수)."""
    team_id = user.get("team_id", "")
    return await get_team_performance(team_id, user)
