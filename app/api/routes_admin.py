"""
관리자 + 감사 로그 + 본부장/경영진 대시보드 API (§12-10, §12-11)

GET  /api/admin/users                   — 사용자 목록 (관리자)
PUT  /api/admin/users/{id}/role         — 역할 변경
PUT  /api/admin/users/{id}/status       — 상태 변경 (활성/비활성)
GET  /api/admin/stats                   — 시스템 통계

GET  /api/audit-logs                    — 감사 로그 조회
GET  /api/audit-logs/export             — 감사 로그 CSV 내보내기

GET  /api/dashboard/division            — 본부장 대시보드
GET  /api/dashboard/executive           — 경영진 대시보드

PATCH /api/proposals/{id}/reopen        — No-Go 재전환

GET  /api/proposals/{id}/versions       — 버전 비교
GET  /api/proposals/{id}/time-travel/{checkpoint_id} — 특정 체크포인트 상태 조회
"""

import csv
import io
import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from app.api.deps import get_current_user, get_current_user_or_none, require_role
from app.api.response import ok, ok_list
from app.exceptions import PropNotFoundError, TenopAPIError
from app.models.auth_schemas import CurrentUser
from app.models.common import StatusResponse
from app.models.admin_schemas import (
    SystemStatsResponse, RoleUpdateResponse, StatusUpdateResponse,
    DivisionDashboardResponse, ExecutiveDashboardResponse, ReopenResponse,
    ProposalVersionsResponse, TimeTravelResponse,
)
from app.services.audit_service import log_action
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin"])


# ── 관리자: 사용자 관리 ──

@router.get("/api/admin/users")
async def list_users(
    status: str | None = None,
    role: str | None = None,
    skip: int = 0,
    limit: int = 50,
    user: CurrentUser = Depends(require_role("admin")),
):
    """사용자 목록 (관리자 전용)."""
    client = await get_async_client()
    query = client.table("users").select(
        "id, email, name, role, team_id, division_id, org_id, status, created_at"
    ).eq("org_id", user.org_id).order("created_at", desc=True).range(skip, skip + limit - 1)

    if status:
        query = query.eq("status", status)
    if role:
        query = query.eq("role", role)

    result = await query.execute()
    return ok_list(result.data or [], total=len(result.data or []))


class RoleUpdateBody(BaseModel):
    role: str  # member | lead | director | executive | admin


@router.put("/api/admin/users/{user_id}/role")
async def update_user_role(
    user_id: str,
    body: RoleUpdateBody,
    user: CurrentUser = Depends(require_role("admin")),
):
    """사용자 역할 변경."""
    valid_roles = {"member", "lead", "director", "executive", "admin"}
    if body.role not in valid_roles:
        raise TenopAPIError("ADMIN_001", f"유효하지 않은 역할: {body.role}", 400)

    # H-3: 같은 조직의 사용자만 변경 가능
    client = await get_async_client()
    target = await client.table("users").select("org_id").eq("id", user_id).maybe_single().execute()
    if not target or not target.data:
        raise TenopAPIError("ADMIN_003", "대상 사용자를 찾을 수 없습니다.", 404)
    if target.data.get("org_id") != user.org_id:
        raise TenopAPIError("ADMIN_004", "다른 조직의 사용자를 수정할 수 없습니다.", 403)

    await client.table("users").update({"role": body.role}).eq("id", user_id).execute()
    await log_action(user.id, "update_role", "user", user_id, {"new_role": body.role})
    return ok({"user_id": user_id, "role": body.role})


class StatusUpdateBody(BaseModel):
    status: str  # active | inactive | suspended


@router.put("/api/admin/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    body: StatusUpdateBody,
    user: CurrentUser = Depends(require_role("admin")),
):
    """사용자 상태 변경 (활성/비활성/정지)."""
    valid_statuses = {"active", "inactive", "suspended"}
    if body.status not in valid_statuses:
        raise TenopAPIError("ADMIN_002", f"유효하지 않은 상태: {body.status}", 400)

    # H-3: 같은 조직의 사용자만 변경 가능
    client = await get_async_client()
    target = await client.table("users").select("org_id").eq("id", user_id).maybe_single().execute()
    if not target or not target.data:
        raise TenopAPIError("ADMIN_003", "대상 사용자를 찾을 수 없습니다.", 404)
    if target.data.get("org_id") != user.org_id:
        raise TenopAPIError("ADMIN_004", "다른 조직의 사용자를 수정할 수 없습니다.", 403)

    await client.table("users").update({"status": body.status}).eq("id", user_id).execute()
    await log_action(user.id, "update_status", "user", user_id, {"new_status": body.status})
    return ok({"user_id": user_id, "user_status": body.status})


@router.get("/api/admin/stats", response_model=SystemStatsResponse)
async def get_system_stats(user: CurrentUser = Depends(require_role("admin"))):
    """시스템 통계 (사용자·프로젝트·세션)."""
    client = await get_async_client()
    org_id = user.org_id

    users = await client.table("users").select("role, status").eq("org_id", org_id).execute()
    proposals = await client.table("proposals").select("status").eq("org_id", org_id).execute()

    user_data = users.data or []
    proposal_data = proposals.data or []

    return {
        "users": {
            "total": len(user_data),
            "active": sum(1 for u in user_data if u.get("status") == "active"),
            "by_role": _count_by(user_data, "role"),
        },
        "proposals": {
            "total": len(proposal_data),
            "by_status": _count_by(proposal_data, "status"),
        },
    }


# ── 감사 로그 ──

@router.get("/api/audit-logs")
async def list_audit_logs(
    action: str | None = None,
    resource_type: str | None = None,
    user_id_filter: str | None = Query(None, alias="user_id"),
    days: int = Query(30, ge=1, le=365),
    skip: int = 0,
    limit: int = 50,
    user: CurrentUser = Depends(require_role("admin", "executive")),
):
    """감사 로그 조회 (관리자·경영진)."""
    client = await get_async_client()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    query = client.table("audit_logs").select("*").gte("created_at", since).order(
        "created_at", desc=True
    ).range(skip, skip + limit - 1)

    if action:
        query = query.eq("action", action)
    if resource_type:
        query = query.eq("resource_type", resource_type)
    if user_id_filter:
        query = query.eq("user_id", user_id_filter)

    result = await query.execute()
    return ok_list(result.data or [], total=len(result.data or []))


@router.get("/api/audit-logs/export")
async def export_audit_logs(
    days: int = Query(30, ge=1, le=365),
    user: CurrentUser = Depends(require_role("admin")),
):
    """감사 로그 CSV 내보내기."""
    client = await get_async_client()
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    result = await client.table("audit_logs").select("*").gte("created_at", since).order(
        "created_at", desc=True
    ).limit(5000).execute()

    rows = result.data or []
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["timestamp", "user_id", "action", "resource_type", "resource_id", "detail"])
    for r in rows:
        writer.writerow([
            r.get("created_at", ""),
            r.get("user_id", ""),
            r.get("action", ""),
            r.get("resource_type", ""),
            r.get("resource_id", ""),
            str(r.get("detail", "")),
        ])

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=audit_logs.csv"},
    )


# ── 본부장 대시보드 ──

@router.get("/api/dashboard/division", response_model=DivisionDashboardResponse)
async def division_dashboard(user: CurrentUser = Depends(require_role("director", "executive", "admin"))):
    """본부장 대시보드 — 본부 내 팀별 KPI + 결재 대기."""
    client = await get_async_client()
    division_id = user.division_id or ""

    # 본부 내 팀 목록
    teams = await client.table("teams").select("id, name").eq("division_id", division_id).execute()
    team_ids = [t["id"] for t in (teams.data or [])]

    # 팀별 프로젝트 현황
    proposals = await client.table("proposals").select(
        "team_id, status, result, result_amount, positioning"
    ).in_("team_id", team_ids).execute() if team_ids else type("R", (), {"data": []})()

    data = proposals.data or []
    team_kpi = {}
    for t in (teams.data or []):
        tid = t["id"]
        team_proposals = [d for d in data if d.get("team_id") == tid]
        won = sum(1 for d in team_proposals if d.get("result") == "수주")
        decided = sum(1 for d in team_proposals if d.get("result") in ("수주", "패찰"))
        team_kpi[t["name"]] = {
            "team_id": tid,
            "total": len(team_proposals),
            "running": sum(1 for d in team_proposals if d.get("status") == "running"),
            "won": won,
            "win_rate": round(won / decided * 100, 1) if decided else 0,
            "total_amount": sum(d.get("result_amount", 0) or 0 for d in team_proposals if d.get("result") == "수주"),
        }

    # 결재 대기 건
    pending_approvals = await client.table("approval_requests").select(
        "id, proposal_id, step, requested_at"
    ).eq("approver_id", user.id).eq("status", "pending").order(
        "requested_at", desc=True
    ).limit(20).execute()

    return {
        "division_id": division_id,
        "teams": team_kpi,
        "pending_approvals": pending_approvals.data or [],
    }


# ── 경영진 대시보드 ──

@router.get("/api/dashboard/executive", response_model=ExecutiveDashboardResponse)
async def executive_dashboard(user: CurrentUser = Depends(require_role("executive", "admin"))):
    """경영진 대시보드 — 전사 KPI + 포지셔닝별 수주율 + 추이."""
    client = await get_async_client()
    org_id = user.org_id

    proposals = await client.table("proposals").select(
        "status, result, result_amount, positioning, created_at, team_id"
    ).eq("org_id", org_id).execute()

    data = proposals.data or []
    total = len(data)
    won = sum(1 for d in data if d.get("result") == "수주")
    decided = sum(1 for d in data if d.get("result") in ("수주", "패찰"))
    running = sum(1 for d in data if d.get("status") == "running")
    won_amount = sum(d.get("result_amount", 0) or 0 for d in data if d.get("result") == "수주")

    # 포지셔닝별 수주율
    by_pos = {}
    for d in data:
        if not d.get("result"):
            continue
        pos = d.get("positioning", "unknown")
        if pos not in by_pos:
            by_pos[pos] = {"won": 0, "total": 0}
        by_pos[pos]["total"] += 1
        if d.get("result") == "수주":
            by_pos[pos]["won"] += 1

    positioning_stats = {
        pos: {**s, "win_rate": round(s["won"] / s["total"] * 100, 1) if s["total"] else 0}
        for pos, s in by_pos.items()
    }

    # 월별 추이 (최근 12개월)
    monthly = {}
    for d in data:
        month = (d.get("created_at") or "")[:7]
        if not month:
            continue
        if month not in monthly:
            monthly[month] = {"submitted": 0, "won": 0, "amount": 0}
        monthly[month]["submitted"] += 1
        if d.get("result") == "수주":
            monthly[month]["won"] += 1
            monthly[month]["amount"] += d.get("result_amount", 0) or 0

    return {
        "kpi": {
            "total_proposals": total,
            "running": running,
            "won": won,
            "decided": decided,
            "win_rate": round(won / decided * 100, 1) if decided else 0,
            "total_won_amount": won_amount,
        },
        "by_positioning": positioning_stats,
        "monthly_trends": [{"month": k, **v} for k, v in sorted(monthly.items())[-12:]],
    }


# ── No-Go 재전환 ──

class ReopenBody(BaseModel):
    reason: str = ""


@router.patch("/api/proposals/{proposal_id}/reopen", response_model=ReopenResponse)
async def reopen_proposal(
    proposal_id: str,
    body: ReopenBody,
    user: CurrentUser = Depends(require_role("lead", "director", "executive", "admin")),
):
    """No-Go 프로젝트 재전환 (reopen) — 팀장 이상."""
    client = await get_async_client()

    proposal = await client.table("proposals").select("id, status").eq("id", proposal_id).single().execute()
    if not proposal.data:
        raise PropNotFoundError(proposal_id)
    if proposal.data["status"] != "cancelled":
        raise TenopAPIError("WF_010", "취소 상태의 프로젝트만 재전환할 수 있습니다.", 400)

    await client.table("proposals").update({
        "status": "draft",
        "current_step": "go_no_go_complete",
    }).eq("id", proposal_id).execute()

    await log_action(user.id, "reopen", "proposal", proposal_id, {"reason": body.reason})
    return ok({"proposal_id": proposal_id, "new_status": "draft"})


# ── 버전 비교 ──

@router.get("/api/proposals/{proposal_id}/versions", response_model=ProposalVersionsResponse)
async def get_proposal_versions(proposal_id: str, user: CurrentUser = Depends(get_current_user)):
    """프로젝트 체크포인트 목록 (버전 비교용)."""
    from app.api.routes_workflow import _get_graph

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    versions = []
    try:
        async for snapshot in graph.aget_state_history(config):
            step = snapshot.values.get("current_step", "")
            versions.append({
                "checkpoint_id": snapshot.config.get("configurable", {}).get("checkpoint_id", ""),
                "step": step,
                "next": list(snapshot.next) if snapshot.next else [],
                "has_sections": bool(snapshot.values.get("proposal_sections")),
                "has_strategy": bool(snapshot.values.get("strategy")),
                "has_plan": bool(snapshot.values.get("plan")),
            })
            if len(versions) >= 30:
                break
    except Exception as e:
        logger.warning(f"버전 이력 조회 실패: {e}")

    return {"proposal_id": proposal_id, "versions": versions}


# ── Time-travel ──

@router.get("/api/proposals/{proposal_id}/time-travel/{checkpoint_id}", response_model=TimeTravelResponse)
async def time_travel(
    proposal_id: str,
    checkpoint_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """특정 체크포인트 시점의 상태 조회."""
    from app.api.routes_workflow import _get_graph

    graph = await _get_graph()
    config = {
        "configurable": {
            "thread_id": proposal_id,
            "checkpoint_id": checkpoint_id,
        }
    }

    try:
        snapshot = await graph.aget_state(config)
        if not snapshot:
            raise TenopAPIError("WF_011", "해당 체크포인트를 찾을 수 없습니다.", 404)

        state = snapshot.values
        # 핵심 필드만 반환 (대용량 텍스트 제외)
        return {
            "proposal_id": proposal_id,
            "checkpoint_id": checkpoint_id,
            "current_step": state.get("current_step", ""),
            "positioning": state.get("positioning"),
            "mode": state.get("mode"),
            "has_rfp_analysis": bool(state.get("rfp_analysis")),
            "has_go_no_go": bool(state.get("go_no_go")),
            "has_strategy": bool(state.get("strategy")),
            "has_plan": bool(state.get("plan")),
            "sections_count": len(state.get("proposal_sections") or []),
            "slides_count": len(state.get("ppt_slides") or []),
            "compliance_count": len(state.get("compliance_matrix") or []),
            "next_nodes": list(snapshot.next) if snapshot.next else [],
        }
    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"time-travel 실패: {e}")
        raise TenopAPIError("WF_012", f"상태 조회 실패: {str(e)}", 500)


# ── 역량 DB 인라인 편집 ──

class CapabilityUpdateBody(BaseModel):
    field: str      # 수정 대상 필드명
    value: str      # 새 값


@router.put("/api/capabilities/{capability_id}", response_model=StatusResponse)
async def update_capability_inline(
    capability_id: str,
    body: CapabilityUpdateBody,
    user: CurrentUser = Depends(require_role("lead", "director", "admin")),
):
    """역량 DB 인라인 편집 — 팀장 이상."""
    allowed_fields = {"description", "tech_area", "track_record", "keywords", "notes"}
    if body.field not in allowed_fields:
        raise TenopAPIError("KB_001", f"수정 불가 필드: {body.field}", 400)

    client = await get_async_client()
    await client.table("capabilities").update({
        body.field: body.value,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }).eq("id", capability_id).execute()

    await log_action(user.id, "update_inline", "capability", capability_id, {
        "field": body.field, "value_preview": body.value[:100],
    })
    return ok({"capability_id": capability_id})


# ── 프론트엔드 에러 수집 (MON-10) ──

class ClientErrorReport(BaseModel):
    url: str
    error: str
    stack: str | None = None
    metadata: dict | None = None


@router.post("/api/client-errors", status_code=201, response_model=StatusResponse)
async def report_client_error(
    body: ClientErrorReport,
    user: CurrentUser | None = Depends(get_current_user_or_none),
):
    """프론트엔드 JS 에러 수집."""
    client = await get_async_client()
    await client.table("client_error_logs").insert({
        "user_id": user.id if user else None,
        "url": body.url[:500],
        "error": body.error[:2000],
        "stack": (body.stack or "")[:5000],
        "metadata": body.metadata or {},
    }).execute()
    return ok({"status": "recorded"})


# ── 모니터링 API (MON-08, MON-09) ──

@router.get("/api/admin/monitoring/node-health")
async def get_node_health(
    user: CurrentUser = Depends(require_role("admin")),
):
    """노드별 헬스 메트릭 조회 (mv_node_health)."""
    client = await get_async_client()
    # MV 리프레시 (concurrent)
    try:
        await client.rpc("refresh_materialized_view_concurrently", {
            "view_name": "mv_node_health",
        }).execute()
    except Exception as e:
        logger.debug(f"MV 리프레시 실패 (stale 데이터 반환): {e}")

    result = await client.table("mv_node_health").select("*").execute()
    return ok_list(result.data or [])


@router.get("/api/admin/monitoring/recent-errors")
async def get_recent_errors(
    limit: int = Query(20, le=100),
    node: str | None = Query(None),
    user: CurrentUser = Depends(require_role("admin")),
):
    """최근 에러 로그 조회 (ai_task_logs status='error')."""
    client = await get_async_client()
    query = (
        client.table("ai_task_logs")
        .select("id, proposal_id, step, error_message, duration_ms, model, created_at")
        .eq("status", "error")
        .order("created_at", desc=True)
        .limit(limit)
    )
    if node:
        query = query.eq("step", node)

    result = await query.execute()
    return ok_list(result.data or [])


# ── 헬퍼 ──

def _count_by(data: list[dict], key: str) -> dict[str, int]:
    """리스트에서 특정 키로 그룹별 카운트."""
    counts = {}
    for d in data:
        val = d.get(key, "unknown")
        counts[val] = counts.get(val, 0) + 1
    return counts


# ── 자가검증 관리자 API ──────────────────────────────────────


@router.get("/api/admin/health/detail")
async def health_detail(
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    hours: int = Query(default=24, ge=1, le=168),
    current_user: CurrentUser = Depends(get_current_user),
):
    """최근 검증 이력 상세 (관리자 전용)"""
    await require_role(current_user, "admin")
    client = await get_async_client()
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    query = client.table("health_check_logs").select("*").gte("checked_at", since)
    if category:
        query = query.eq("category", category)
    if status:
        query = query.eq("status", status)

    res = await query.order("checked_at", desc=True).limit(200).execute()
    return ok(res.data or [])


@router.post("/api/admin/health/run")
async def health_run(
    category: str | None = Query(default=None),
    check_id: str | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
):
    """검증 수동 실행 (관리자 전용)"""
    await require_role(current_user, "admin")

    from app.services.health_checker import HealthCheckRunner
    from app.services.alert_manager import AlertManager

    runner = HealthCheckRunner()
    alerter = AlertManager()

    if check_id:
        results = [await runner.run_single(check_id)]
    elif category:
        results = await runner.run_category(category)
    else:
        results = await runner.run_all()

    await alerter.handle_results(results)

    return ok([{
        "check_id": r.check_id,
        "category": r.category,
        "status": r.status,
        "message": r.message,
        "auto_recovered": r.auto_recovered,
        "duration_ms": round(r.duration_ms, 1),
    } for r in results])
