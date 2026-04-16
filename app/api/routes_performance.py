"""
성과 추적 + 대시보드 + 교훈 API (Phase 4)

POST /api/proposals/{id}/result              — 제안 결과 등록 (4-2)
GET  /api/proposals/{id}/result              — 제안 결과 조회
PUT  /api/proposals/{id}/result              — 제안 결과 수정
POST /api/proposals/{id}/lessons             — 교훈 등록 (4-5)
GET  /api/proposals/{id}/lessons             — 교훈 조회
GET  /api/lessons                            — 교훈 검색
GET  /api/performance/individual/{user_id}   — 개인 성과
GET  /api/performance/team/{id}              — 팀 성과
GET  /api/performance/division/{div_id}      — 본부 성과
GET  /api/performance/company                — 전사 성과
GET  /api/performance/trends                 — 기간별 추이
GET  /api/dashboard/my-projects              — 내 프로젝트
GET  /api/dashboard/team                     — 팀 파이프라인
GET  /api/dashboard/team/performance         — 팀 성과 요약
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, require_role
from app.api.response import ok, ok_list
from app.exceptions import PropNotFoundError, TenopAPIError
from app.models.auth_schemas import CurrentUser
from app.models.proposal_schemas import ProposalResultResponse
from app.models.common import StatusResponse
from app.models.performance_schemas import (
    IndividualPerformance, TeamQuarterPerformance, DivisionPerformance,
    CompanyPerformance, PerformanceTrends, MyProjectsDashboard, TeamDashboard,
)
from app.models.schemas import ProposalResultCreate, ProposalResultUpdate, LessonCreate
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["performance"])


# ════════════════════════════════════════
# 4-2. 제안 결과 등록/조회/수정
# ════════════════════════════════════════

STATUS_MAP = {"won": "won", "lost": "lost", "void": "cancelled"}


async def _get_proposal_or_404(client, proposal_id: str) -> dict:
    result = await client.table("proposals").select("id, status").eq("id", proposal_id).single().execute()
    if not result.data:
        raise PropNotFoundError(proposal_id)
    return result.data


async def _refresh_views(client):
    """Materialized View 갱신 (실패 시 무시)."""
    try:
        await client.rpc("refresh_performance_views").execute()
    except Exception:
        logger.warning("성과 MV 갱신 실패 (무시)")


async def _resolve_pricing_predictions(client, proposal_id: str, body) -> None:
    """결과 등록 시 해당 proposal의 pricing_predictions 해소."""
    preds = await client.table("pricing_predictions").select(
        "id, predicted_ratio"
    ).eq("proposal_id", proposal_id).is_("resolved_at", "null").execute()

    if not preds.data:
        return

    # 실제 낙찰률 계산
    actual_ratio = None
    if body.final_price and body.final_price > 0:
        # proposals에서 budget 가져오기
        prop = await client.table("proposals").select("budget_amount").eq("id", proposal_id).single().execute()
        budget = prop.data.get("budget_amount", 0) if prop.data else 0
        if budget and budget > 0:
            actual_ratio = round(body.final_price / budget, 4)

    now = datetime.now(timezone.utc).isoformat()
    for pred in preds.data:
        pred_ratio = pred.get("predicted_ratio")
        error = round(abs(pred_ratio - actual_ratio), 4) if pred_ratio and actual_ratio else None

        await client.table("pricing_predictions").update({
            "actual_ratio": actual_ratio,
            "actual_result": body.result,
            "prediction_error": error,
            "resolved_at": now,
        }).eq("id", pred["id"]).execute()

    logger.info(f"가격 예측 {len(preds.data)}건 해소: proposal={proposal_id}")


@router.post("/api/proposals/{proposal_id}/result", status_code=201, response_model=StatusResponse)
async def register_proposal_result(
    proposal_id: str,
    body: ProposalResultCreate,
    user: CurrentUser = Depends(require_role("lead", "director", "executive", "admin")),
):
    """제안 결과 등록 (수주/패찰/유찰) — 팀장 이상."""
    client = await get_async_client()
    await _get_proposal_or_404(client, proposal_id)

    # 중복 등록 방지
    existing = await client.table("proposal_results").select("id").eq("proposal_id", proposal_id).execute()
    if existing.data:
        raise TenopAPIError("PROP_003", "이미 결과가 등록되어 있습니다. PUT으로 수정하세요.", 409)

    # proposal_results 테이블에 상세 저장
    result_row = {
        "proposal_id": proposal_id,
        "result": body.result,
        "final_price": body.final_price,
        "competitor_count": body.competitor_count,
        "ranking": body.ranking,
        "tech_score": body.tech_score,
        "price_score": body.price_score,
        "total_score": body.total_score,
        "feedback_notes": body.feedback_notes,
        "won_by": body.won_by,
        "registered_by": user.id,
    }
    await client.table("proposal_results").insert(result_row).execute()

    # proposals 테이블 상태 업데이트
    now = datetime.now(timezone.utc).isoformat()
    await client.table("proposals").update({
        "status": STATUS_MAP[body.result],
        "result": {"won": "수주", "lost": "패찰", "void": "유찰"}[body.result],
        "result_amount": body.final_price,
        "result_reason": body.feedback_notes or "",
        "result_at": now,
        "updated_at": now,
    }).eq("id", proposal_id).execute()

    await _refresh_views(client)

    # KB 환류 트리거
    try:
        from app.services.kb_updater import trigger_kb_update
        await trigger_kb_update(proposal_id, body.result)
    except Exception:
        logger.warning("KB 환류 트리거 실패 (무시)")

    # 가격 예측 정확도 해소 (pricing_predictions)
    try:
        await _resolve_pricing_predictions(client, proposal_id, body)
    except Exception:
        logger.warning("가격 예측 해소 실패 (무시)")

    return ok({"result": body.result, "proposal_id": proposal_id})


@router.get("/api/proposals/{proposal_id}/result", response_model=ProposalResultResponse)
async def get_proposal_result(proposal_id: str, user: CurrentUser = Depends(get_current_user)):
    """제안 결과 조회."""
    client = await get_async_client()
    await _get_proposal_or_404(client, proposal_id)

    result = await client.table("proposal_results").select("*").eq("proposal_id", proposal_id).single().execute()
    if not result.data:
        raise TenopAPIError("PROP_004", "결과가 등록되지 않았습니다.", 404)
    return result.data


@router.put("/api/proposals/{proposal_id}/result", response_model=StatusResponse)
async def update_proposal_result(
    proposal_id: str,
    body: ProposalResultUpdate,
    user: CurrentUser = Depends(require_role("lead", "director", "executive", "admin")),
):
    """제안 결과 수정 — 팀장 이상."""
    client = await get_async_client()
    await _get_proposal_or_404(client, proposal_id)

    existing = await client.table("proposal_results").select("id").eq("proposal_id", proposal_id).single().execute()
    if not existing.data:
        raise TenopAPIError("PROP_004", "결과가 등록되지 않았습니다.", 404)

    update_data = {k: v for k, v in body.model_dump().items() if v is not None}
    if not update_data:
        return ok(None, message="변경 없음")

    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    await client.table("proposal_results").update(update_data).eq("proposal_id", proposal_id).execute()

    # proposals 테이블도 동기화
    proposals_update = {"updated_at": update_data["updated_at"]}
    if body.final_price is not None:
        proposals_update["result_amount"] = body.final_price
    if body.feedback_notes is not None:
        proposals_update["result_reason"] = body.feedback_notes
    await client.table("proposals").update(proposals_update).eq("id", proposal_id).execute()

    await _refresh_views(client)

    return ok({"proposal_id": proposal_id})


# ════════════════════════════════════════
# 4-5. 교훈(Lessons Learned) 등록/조회
# ════════════════════════════════════════

@router.post("/api/proposals/{proposal_id}/lessons", status_code=201, response_model=StatusResponse)
async def create_lesson(
    proposal_id: str,
    body: LessonCreate,
    user: CurrentUser = Depends(get_current_user),
):
    """프로젝트 교훈 등록."""
    client = await get_async_client()
    proposal = await client.table("proposals").select("id, org_id, positioning, client_name, result").eq("id", proposal_id).single().execute()
    if not proposal.data:
        raise PropNotFoundError(proposal_id)

    p = proposal.data
    lesson_row = {
        "org_id": p.get("org_id", ""),
        "proposal_id": proposal_id,
        "strategy_summary": body.title,
        "effective_points": body.description if body.category != "strategy" else None,
        "weak_points": body.description if body.category == "strategy" else None,
        "improvements": "\n".join(body.action_items) if body.action_items else None,
        "failure_category": body.category,
        "failure_detail": body.description,
        "positioning": p.get("positioning"),
        "client_name": p.get("client_name"),
        "industry": ", ".join(body.applicable_domains) if body.applicable_domains else None,
        "result": p.get("result"),
        "author_id": user.id,
    }
    result = await client.table("lessons_learned").insert(lesson_row).execute()
    lesson_id = result.data[0]["id"] if result.data else None

    # 벡터 임베딩 생성 (비동기, 실패 무시)
    try:
        from app.services.kb_updater import generate_lesson_embedding
        await generate_lesson_embedding(lesson_id, body.title, body.description)
    except Exception:
        logger.warning(f"교훈 임베딩 생성 실패 (무시): {lesson_id}")

    return ok({"lesson_id": lesson_id})


@router.get("/api/proposals/{proposal_id}/lessons")
async def get_proposal_lessons(proposal_id: str, user: CurrentUser = Depends(get_current_user)):
    """프로젝트 교훈 조회."""
    client = await get_async_client()
    result = await client.table("lessons_learned").select(
        "id, strategy_summary, failure_category, failure_detail, improvements, positioning, result, created_at"
    ).eq("proposal_id", proposal_id).order("created_at", desc=True).execute()
    return ok_list(result.data or [], total=len(result.data or []))


@router.get("/api/lessons")
async def search_lessons(
    keyword: str | None = Query(None, description="키워드 검색"),
    category: str | None = Query(None, description="카테고리 필터"),
    domain: str | None = Query(None, description="도메인 필터"),
    skip: int = 0,
    limit: int = 20,
    user: CurrentUser = Depends(get_current_user),
):
    """교훈 검색 (키워드, 카테고리, 도메인)."""
    client = await get_async_client()
    query = client.table("lessons_learned").select(
        "id, proposal_id, strategy_summary, failure_category, failure_detail, improvements, positioning, client_name, industry, result, created_at"
    ).order("created_at", desc=True).range(skip, skip + limit - 1)

    if category:
        query = query.eq("failure_category", category)
    if domain:
        query = query.ilike("industry", f"%{domain}%")
    if keyword:
        query = query.or_(f"strategy_summary.ilike.%{keyword}%,failure_detail.ilike.%{keyword}%")

    result = await query.execute()
    return ok_list(result.data or [], total=len(result.data or []))


# ════════════════════════════════════════
# 성과 추적 API (§12-9)
# ════════════════════════════════════════

@router.get("/api/performance/individual/{user_id}", response_model=IndividualPerformance)
async def get_individual_performance(user_id: str, user: CurrentUser = Depends(get_current_user)):
    """개인 성과 (참여·완료·수주 건수)."""
    client = await get_async_client()

    created = await client.table("proposals").select(
        "id, result, result_amount, created_at, result_at"
    ).eq("owner_id", user_id).execute()

    participated = await client.table("project_participants").select("proposal_id").eq("user_id", user_id).execute()
    participated_ids = [p["proposal_id"] for p in (participated.data or [])]

    participated_proposals = []
    if participated_ids:
        pp = await client.table("proposals").select(
            "id, result, result_amount, created_at, result_at"
        ).in_("id", participated_ids).execute()
        participated_proposals = pp.data or []

    all_proposals = {d["id"]: d for d in (created.data or []) + participated_proposals}
    data = list(all_proposals.values())

    total = len(data)
    completed = sum(1 for d in data if d.get("result") is not None)
    won = sum(1 for d in data if d.get("result") == "수주")
    decided = sum(1 for d in data if d.get("result") in ("수주", "패찰"))
    won_amount = sum(d.get("result_amount", 0) or 0 for d in data if d.get("result") == "수주")

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


@router.get("/api/performance/team/{team_id}", response_model=TeamQuarterPerformance)
async def get_team_performance(team_id: str, user: CurrentUser = Depends(get_current_user)):
    """팀 성과 (수주율·건수·평균 점수)."""
    client = await get_async_client()

    # MV 우선 조회
    try:
        mv = await client.table("mv_team_performance").select("*").eq("team_id", team_id).execute()
        if mv.data:
            return {"team_id": team_id, "quarters": mv.data}
    except Exception:
        pass

    # MV 없으면 직접 계산
    proposals = await client.table("proposals").select(
        "status, result, result_amount, created_at, result_at"
    ).eq("team_id", team_id).execute()
    data = proposals.data or []
    total = len(data)
    won = sum(1 for d in data if d.get("result") == "수주")
    decided = sum(1 for d in data if d.get("result") in ("수주", "패찰"))
    won_amount = sum(d.get("result_amount", 0) or 0 for d in data if d.get("result") == "수주")

    # 평균 점수 (proposal_results 조인)
    avg_tech = None
    try:
        proposal_ids = [d["id"] for d in data if "id" in d]
        if proposal_ids:
            scores = await client.table("proposal_results").select("tech_score").in_("proposal_id", proposal_ids).not_.is_("tech_score", "null").execute()
            if scores.data:
                avg_tech = round(sum(s["tech_score"] for s in scores.data) / len(scores.data), 1)
    except Exception:
        pass

    return {
        "team_id": team_id,
        "total_proposals": total,
        "won_count": won,
        "decided_count": decided,
        "win_rate": round(won / decided * 100, 1) if decided else 0,
        "total_won_amount": won_amount,
        "avg_tech_score": avg_tech,
    }


@router.get("/api/performance/division/{div_id}", response_model=DivisionPerformance)
async def get_division_performance(div_id: str, user: CurrentUser = Depends(get_current_user)):
    """본부 성과 (수주율·누적 수주액)."""
    client = await get_async_client()

    teams = await client.table("teams").select("id").eq("division_id", div_id).execute()
    team_ids = [t["id"] for t in (teams.data or [])]

    if not team_ids:
        return {
            "division_id": div_id,
            "total_proposals": 0, "won_count": 0, "decided_count": 0,
            "win_rate": 0, "total_won_amount": 0, "teams": [],
        }

    proposals = await client.table("proposals").select(
        "id, team_id, result, result_amount"
    ).in_("team_id", team_ids).execute()
    data = proposals.data or []

    total = len(data)
    won = sum(1 for d in data if d.get("result") == "수주")
    decided = sum(1 for d in data if d.get("result") in ("수주", "패찰"))
    won_amount = sum(d.get("result_amount", 0) or 0 for d in data if d.get("result") == "수주")

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


@router.get("/api/performance/company", response_model=CompanyPerformance)
async def get_company_performance(user: CurrentUser = Depends(get_current_user)):
    """전사 성과 (포지셔닝별 수주율)."""
    client = await get_async_client()

    # MV 우선 조회
    try:
        mv = await client.table("mv_positioning_accuracy").select("*").execute()
        if mv.data:
            return {"by_positioning": {r["positioning"]: r for r in mv.data}, "total_proposals": sum(r["total"] for r in mv.data)}
    except Exception:
        pass

    proposals = await client.table("proposals").select(
        "positioning, result, result_amount"
    ).not_.is_("result", "null").execute()
    data = proposals.data or []

    by_positioning: dict[str, dict] = {}
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


@router.get("/api/performance/trends", response_model=PerformanceTrends)
async def get_performance_trends(
    period: str = Query("monthly", pattern="^(monthly|quarterly|yearly)$"),
    months: int = Query(12, ge=1, le=60),
    user: CurrentUser = Depends(get_current_user),
):
    """기간별 추이 (월/분기/연)."""
    client = await get_async_client()
    proposals = await client.table("proposals").select(
        "created_at, result, result_at, result_amount"
    ).order("created_at").execute()
    data = proposals.data or []

    trends: dict[str, dict] = {}
    for d in data:
        created = d.get("created_at", "")[:7]
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


# ════════════════════════════════════════
# 대시보드 API (§12-8)
# ════════════════════════════════════════

@router.get("/api/dashboard/my-projects", response_model=MyProjectsDashboard)
async def my_projects(user: CurrentUser = Depends(get_current_user)):
    """내 참여 프로젝트 현황."""
    client = await get_async_client()

    created = await client.table("proposals").select(
        "id, title, status, positioning, current_phase, created_at"
    ).eq("owner_id", user.id).order("created_at", desc=True).limit(20).execute()

    participated = await client.table("project_participants").select("proposal_id").eq("user_id", user.id).execute()
    participated_ids = [p["proposal_id"] for p in (participated.data or [])]

    participant_proposals = []
    if participated_ids:
        pp = await client.table("proposals").select(
            "id, title, status, positioning, current_phase, created_at"
        ).in_("id", participated_ids).order("created_at", desc=True).execute()
        participant_proposals = pp.data or []

    return {
        "created": created.data or [],
        "participating": participant_proposals,
    }


@router.get("/api/dashboard/team", response_model=TeamDashboard)
async def team_dashboard(user: CurrentUser = Depends(get_current_user)):
    """팀 제안 파이프라인 (STEP별 분포)."""
    client = await get_async_client()
    team_id = user.team_id or ""

    proposals = await client.table("proposals").select(
        "id, title, status, current_phase, positioning"
    ).eq("team_id", team_id).order("created_at", desc=True).limit(50).execute()

    data = proposals.data or []
    step_distribution: dict[str, int] = {}
    for d in data:
        step = d.get("current_phase", "unknown")
        step_distribution[step] = step_distribution.get(step, 0) + 1

    return {
        "team_id": team_id,
        "proposals": data,
        "step_distribution": step_distribution,
        "total": len(data),
    }


@router.get("/api/dashboard/team/performance", response_model=TeamQuarterPerformance)
async def team_performance_summary(user: CurrentUser = Depends(get_current_user)):
    """팀 성과 요약 (수주율·건수)."""
    team_id = user.team_id or ""
    return await get_team_performance(team_id, user)


# ════════════════════════════════════════
# 통합 대시보드 엔드포인트 (스코프별)
# ════════════════════════════════════════

@router.get("/api/dashboard/team")
async def dashboard_team(user: CurrentUser = Depends(get_current_user)):
    """팀 스코프 대시보드 — 팀 데이터 통합.
    
    반환 데이터:
    - stats: win_rate 통계
    - performance: 팀 성과 요약
    - pipeline: 제안 파이프라인
    """
    client = await get_async_client()
    team_id = user.team_id or ""
    
    if not team_id:
        return ok({
            "scope": "team",
            "stats": {"overall": {"total": 0, "won": 0, "lost": 0, "rate": 0.0}, "by_month": [], "by_agency": []},
            "performance": None,
            "pipeline": {"registered": 0, "inProgress": 0, "completed": 0, "pending": 0, "won": 0, "lost": 0},
        })
    
    # 팀 성과
    performance = await get_team_performance(team_id, user)
    
    # 팀의 제안서 통계
    proposals = await client.table("proposals").select(
        "id, status, win_result, created_at"
    ).eq("team_id", team_id).execute()
    
    data = proposals.data or []
    pipeline = {
        "registered": len([p for p in data if p["status"] == "initialized"]),
        "inProgress": len([p for p in data if p["status"] in ("waiting", "in_progress")]),
        "completed": len([p for p in data if p["status"] == "completed" and p["win_result"] is None]),
        "pending": len([p for p in data if p["status"] in ("submitted", "presentation")]),
        "won": len([p for p in data if p["win_result"] == "won"]),
        "lost": len([p for p in data if p["win_result"] == "lost"]),
    }
    
    return ok({
        "scope": "team",
        "performance": performance.model_dump() if performance else None,
        "pipeline": pipeline,
    })


@router.get("/api/dashboard/division")
async def dashboard_division(user: CurrentUser = Depends(require_role("director", "executive", "admin"))):
    """본부 스코프 대시보드 — 본부 데이터 통합.
    
    권한: 본부장(director) 이상
    """
    if not user.division_id:
        return ok({
            "scope": "division",
            "teams": [],
            "stats": {"overall": {"total": 0, "won": 0, "lost": 0, "rate": 0.0}, "by_month": [], "by_agency": []},
        })
    
    client = await get_async_client()
    
    # 본부 내 팀 목록
    teams_res = await client.table("teams").select("id, name").eq("division_id", user.division_id).execute()
    teams_data = teams_res.data or []
    team_ids = [t["id"] for t in teams_data]
    
    if not team_ids:
        return ok({
            "scope": "division",
            "teams": [],
            "stats": {"overall": {"total": 0, "won": 0, "lost": 0, "rate": 0.0}, "by_month": [], "by_agency": []},
        })
    
    # 팀별 성과
    proposals = await client.table("proposals").select(
        "team_id, win_result, created_at"
    ).in_("team_id", team_ids).execute()
    
    data = proposals.data or []
    teams_perf = []
    for team in teams_data:
        tid = team["id"]
        team_data = [p for p in data if p["team_id"] == tid and p["win_result"] in ("won", "lost")]
        if team_data:
            won = len([p for p in team_data if p["win_result"] == "won"])
            total = len(team_data)
            teams_perf.append({
                "team_id": tid,
                "team_name": team["name"],
                "total": total,
                "won": won,
                "win_rate": round(won / total * 100, 1) if total else 0,
            })
    
    return ok({
        "scope": "division",
        "teams": teams_perf,
    })


@router.get("/api/dashboard/company")
async def dashboard_company(user: CurrentUser = Depends(require_role("executive", "admin"))):
    """전사 스코프 대시보드 — 경영진 전체 데이터.
    
    권한: 경영진(executive) 이상
    """
    client = await get_async_client()
    
    # 전사 제안서 통계
    proposals = await client.table("proposals").select(
        "id, team_id, win_result, created_at"
    ).in_("win_result", ["won", "lost"]).execute()
    
    data = proposals.data or []
    if not data:
        return ok({
            "scope": "company",
            "stats": {"overall": {"total": 0, "won": 0, "lost": 0, "rate": 0.0}, "by_month": [], "by_agency": []},
        })
    
    won = len([p for p in data if p["win_result"] == "won"])
    total = len(data)
    
    # 월별 통계
    by_month = {}
    for p in data:
        month = p["created_at"][:7] if p["created_at"] else "unknown"
        if month not in by_month:
            by_month[month] = {"total": 0, "won": 0}
        by_month[month]["total"] += 1
        if p["win_result"] == "won":
            by_month[month]["won"] += 1
    
    by_month_data = [
        {
            "month": k,
            "total": v["total"],
            "won": v["won"],
            "rate": round(v["won"] / v["total"] * 100, 1) if v["total"] else 0,
        }
        for k, v in sorted(by_month.items())
    ]
    
    return ok({
        "scope": "company",
        "stats": {
            "overall": {
                "total": total,
                "won": won,
                "lost": total - won,
                "rate": round(won / total * 100, 1) if total else 0,
            },
            "by_month": by_month_data,
        },
    })
