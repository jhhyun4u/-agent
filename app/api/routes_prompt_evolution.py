"""
프롬프트 진화 + Admin API

고정 경로를 패턴 경로보다 먼저 등록하여 라우트 충돌 방지.

── 고정 경로 (GET) ──
GET  /api/prompts/dashboard                    — 대시보드 집계
GET  /api/prompts/section-heatmap              — 섹션 유형별 히트맵
GET  /api/prompts/list                         — 전체 목록
GET  /api/prompts/categories                   — 카테고리별 프롬프트 (Admin)
GET  /api/prompts/worst-performers             — 워스트 퍼포머 (Admin)
GET  /api/prompts/simulation-quota             — 시뮬레이션 잔여 한도 (Admin)

── 고정 경로 (POST) ──
POST /api/prompts/edit-action                  — 사람 수정 기록 (Phase C)
POST /api/prompts/experiments/create           — 실험 시작
GET  /api/prompts/experiments/list             — 실험 목록
POST /api/prompts/experiments/{id}/evaluate    — 실험 평가
POST /api/prompts/experiments/{id}/promote     — 승격
POST /api/prompts/experiments/{id}/rollback    — 롤백

── 패턴 경로 (반드시 고정 경로 뒤에 배치) ──
GET  /api/prompts/{prompt_id}/detail           — 상세 + 버전 이력
GET  /api/prompts/{prompt_id}/effectiveness    — 버전별 성과 메트릭
POST /api/prompts/{prompt_id}/suggest-improvement  — AI 개선 제안
POST /api/prompts/{prompt_id}/create-candidate     — 후보 등록
POST /api/prompts/{prompt_id}/simulate             — 시뮬레이션 (Admin)
POST /api/prompts/{prompt_id}/simulate-compare     — A/B 비교 시뮬 (Admin)
GET  /api/prompts/{prompt_id}/simulations          — 시뮬레이션 이력 (Admin)
GET  /api/prompts/{prompt_id}/suggestions          — AI 제안 이력 (Admin)
POST /api/prompts/{prompt_id}/suggestions/{id}/feedback — 제안 피드백 (Admin)
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.deps import get_current_user, require_role
from app.api.response import ok

router = APIRouter(prefix="/api/prompts", tags=["prompt-evolution"])
logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════
# 고정 경로 (패턴 경로보다 반드시 먼저 등록)
# ════════════════════════════════════════════════════════


@router.get("/dashboard")
async def prompt_dashboard(user=Depends(get_current_user)):
    """프롬프트 대시보드 집계."""
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()

    # 활성 프롬프트 목록
    prompts = await (
        client.table("prompt_registry")
        .select("prompt_id, version, source_file, metadata, created_at")
        .eq("status", "active")
        .order("prompt_id")
        .execute()
    )

    # 성과 집계 (MV 사용 시도, 실패 시 직접 쿼리)
    effectiveness = []
    try:
        eff_result = await (
            client.table("mv_prompt_effectiveness")
            .select("*")
            .execute()
        )
        effectiveness = eff_result.data or []
    except Exception:
        pass

    # 수정율 집계
    edit_stats = []
    try:
        edit_result = await (
            client.table("human_edit_tracking")
            .select("prompt_id, action, edit_ratio")
            .execute()
        )
        edit_map: dict = {}
        for e in (edit_result.data or []):
            pid = e.get("prompt_id")
            if not pid:
                continue
            if pid not in edit_map:
                edit_map[pid] = {"count": 0, "total_ratio": 0.0, "actions": {}}
            edit_map[pid]["count"] += 1
            edit_map[pid]["total_ratio"] += e.get("edit_ratio", 0) or 0
            a = e.get("action", "unknown")
            edit_map[pid]["actions"][a] = edit_map[pid]["actions"].get(a, 0) + 1

        for pid, stats in edit_map.items():
            edit_stats.append({
                "prompt_id": pid,
                "edit_count": stats["count"],
                "avg_edit_ratio": round(stats["total_ratio"] / stats["count"], 4) if stats["count"] else 0,
                "actions": stats["actions"],
            })
    except Exception:
        pass

    # 진행 중 실험
    experiments = []
    try:
        exp_result = await (
            client.table("prompt_ab_experiments")
            .select("id, experiment_name, prompt_id, status, started_at")
            .eq("status", "running")
            .execute()
        )
        experiments = exp_result.data or []
    except Exception:
        pass

    return ok({
        "prompts": prompts.data or [],
        "effectiveness": effectiveness,
        "edit_stats": edit_stats,
        "running_experiments": experiments,
        "total_prompts": len(prompts.data or []),
    })


@router.get("/section-heatmap")
async def section_heatmap(user=Depends(get_current_user)):
    """섹션 유형별 히트맵 데이터."""
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()

    links = await (
        client.table("prompt_artifact_link")
        .select("prompt_id, section_id, quality_score")
        .execute()
    )

    heatmap: dict = {}
    for link in (links.data or []):
        section = link.get("section_id") or "unknown"
        prompt = link.get("prompt_id", "")
        if section not in heatmap:
            heatmap[section] = {"count": 0, "total_quality": 0.0, "prompts": set()}
        heatmap[section]["count"] += 1
        if link.get("quality_score"):
            heatmap[section]["total_quality"] += link["quality_score"]
        heatmap[section]["prompts"].add(prompt)

    result = []
    for section, stats in heatmap.items():
        result.append({
            "section_id": section,
            "usage_count": stats["count"],
            "avg_quality": round(stats["total_quality"] / stats["count"], 2) if stats["count"] and stats["total_quality"] else None,
            "unique_prompts": len(stats["prompts"]),
        })

    return ok({"heatmap": sorted(result, key=lambda x: x["usage_count"], reverse=True)})


@router.get("/list")
async def list_prompts(
    status: str = Query("active", description="active|candidate|retired|baseline"),
    user=Depends(get_current_user),
):
    """프롬프트 목록 조회."""
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()
    result = await (
        client.table("prompt_registry")
        .select("prompt_id, version, source_file, status, content_hash, metadata, created_at, created_by")
        .eq("status", status)
        .order("prompt_id")
        .execute()
    )
    return ok({"prompts": result.data or []})


# ── Admin: 카테고리 + 워스트 + 한도 (GET 고정 경로) ──


@router.get("/categories")
async def get_categories(user=Depends(require_role("admin"))):
    """카테고리별 프롬프트 목록 + 메타데이터."""
    from app.services.domains.proposal.prompt_categories import get_categories_with_prompts

    return ok(await get_categories_with_prompts())


@router.get("/worst-performers")
async def get_worst_performers(
    limit: int = Query(5, ge=1, le=20),
    user=Depends(require_role("admin")),
):
    """수정율/품질 기준 워스트 프롬프트."""
    from app.services.domains.proposal.prompt_categories import get_worst_performers

    return ok(await get_worst_performers(limit))


@router.get("/simulation-quota")
async def get_simulation_quota(user=Depends(require_role("admin"))):
    """현재 사용자의 일일 시뮬레이션 잔여 한도."""
    from app.services.domains.proposal.prompt_simulator import get_quota_info

    return ok(await get_quota_info(user.id))


# ── v2.0: 학습 분석 API ──


@router.get("/learning-dashboard")
async def get_learning_dashboard(user=Depends(require_role("admin"))):
    """학습 대시보드 전체 데이터."""
    from app.services.domains.proposal.prompt_analyzer import run_batch_analysis

    top_needs = await run_batch_analysis(top_n=5)

    # 전체 평균 추이 (최근 스냅샷에서 집계)
    overview = {"avg_win_rate": 0, "avg_quality": 0, "avg_edit_ratio": 0, "running_experiments": 0, "delta": {}}
    if top_needs:
        qualities = [t["metrics"].get("avg_quality", 0) for t in top_needs if t["metrics"].get("avg_quality")]
        edit_ratios = [t["metrics"].get("avg_edit_ratio", 0) for t in top_needs if t["metrics"].get("avg_edit_ratio")]
        win_rates = [t["metrics"].get("win_rate", 0) for t in top_needs if t["metrics"].get("win_rate")]
        overview["avg_quality"] = round(sum(qualities) / max(1, len(qualities)), 1)
        overview["avg_edit_ratio"] = round(sum(edit_ratios) / max(1, len(edit_ratios)), 4)
        overview["avg_win_rate"] = round(sum(win_rates) / max(1, len(win_rates)), 1)

    # 실험 중 건수
    try:
        from app.utils.supabase_client import get_async_client
        db = await get_async_client()
        exp = await db.table("prompt_ab_experiments").select("id").eq("status", "running").execute()
        overview["running_experiments"] = len(exp.data) if exp.data else 0
    except Exception:
        pass

    # 최근 학습 이력 (승격/롤백/실험 완료)
    recent_learnings = []
    try:
        from app.utils.supabase_client import get_async_client as _get_client
        _db = await _get_client()
        events = await (
            _db.table("prompt_ab_experiments")
            .select("prompt_id, experiment_name, status, started_at, ended_at")
            .in_("status", ["promoted", "rolled_back", "completed"])
            .order("ended_at", desc=True)
            .limit(10)
            .execute()
        )
        for ev in (events.data or []):
            recent_learnings.append({
                "date": (ev.get("ended_at") or ev.get("started_at", ""))[:10],
                "prompt_id": ev["prompt_id"],
                "event": {
                    "promoted": "승격",
                    "rolled_back": "롤백",
                    "completed": "실험 완료",
                }.get(ev["status"], ev["status"]),
                "experiment_name": ev.get("experiment_name", ""),
            })
    except Exception:
        pass

    # 전체 월별 추이 (최근 6개월 스냅샷 집계)
    trend = []
    try:
        from datetime import date, timedelta
        _db2 = await _get_client()
        since = (date.today() - timedelta(days=180)).isoformat()
        snaps = await (
            _db2.table("prompt_analysis_snapshots")
            .select("period_end, avg_quality, avg_edit_ratio, win_rate")
            .gte("period_end", since)
            .order("period_end")
            .execute()
        )
        # 월별 평균
        by_month: dict[str, dict] = {}
        for s in (snaps.data or []):
            month = s["period_end"][:7]
            if month not in by_month:
                by_month[month] = {"quality": [], "edit_ratio": [], "win_rate": []}
            if s.get("avg_quality") is not None:
                by_month[month]["quality"].append(float(s["avg_quality"]))
            if s.get("avg_edit_ratio") is not None:
                by_month[month]["edit_ratio"].append(float(s["avg_edit_ratio"]))
            if s.get("win_rate") is not None:
                by_month[month]["win_rate"].append(float(s["win_rate"]))
        for month, vals in sorted(by_month.items()):
            trend.append({
                "period": month,
                "avg_quality": round(sum(vals["quality"]) / len(vals["quality"]), 1) if vals["quality"] else None,
                "avg_edit_ratio": round(sum(vals["edit_ratio"]) / len(vals["edit_ratio"]), 4) if vals["edit_ratio"] else None,
                "avg_win_rate": round(sum(vals["win_rate"]) / len(vals["win_rate"]), 1) if vals["win_rate"] else None,
            })
    except Exception:
        pass

    return ok({
        "overview": overview,
        "top_needs_improvement": [
            {
                "prompt_id": t["prompt_id"],
                "label": t.get("label", t["prompt_id"]),
                "priority": t["priority"],
                "metrics": t["metrics"],
                "top_pattern": t["edit_patterns"][0] if t["edit_patterns"] else None,
                "feedback_theme": t["feedback_summary"].get("themes", [None])[0],
            }
            for t in top_needs
        ],
        "recent_learnings": recent_learnings,
        "trend": trend,
    })


@router.get("/workflow-map")
async def get_workflow_map(user=Depends(require_role("admin"))):
    """워크플로 맵 데이터."""
    from app.services.domains.proposal.prompt_categories import PROMPT_NODE_USAGE

    # 노드별 프롬프트 그룹핑
    node_prompts: dict[str, list[str]] = {}
    for pid, nodes in PROMPT_NODE_USAGE.items():
        for n in nodes:
            if n not in node_prompts:
                node_prompts[n] = []
            node_prompts[n].append(pid)

    nodes = [
        {"id": "rfp_search", "label": "공고 검색"},
        {"id": "rfp_analyze", "label": "RFP 분석"},
        {"id": "go_no_go", "label": "Go/No-Go"},
        {"id": "strategy_generate", "label": "전략 수립"},
        {"id": "plan_story", "label": "스토리라인"},
        {"id": "plan_team", "label": "팀 구성"},
        {"id": "plan_price", "label": "예산 전략"},
        {"id": "proposal_write_next", "label": "제안서 작성"},
        {"id": "self_review", "label": "자가진단"},
        {"id": "ppt_toc", "label": "PPT 목차"},
        {"id": "ppt_storyboard", "label": "PPT 스토리보드"},
    ]
    for n in nodes:
        n["prompts"] = node_prompts.get(n["id"], [])
        n["prompt_count"] = len(n["prompts"])

    workflow_edges = [
        {"from": "rfp_search", "to": "rfp_analyze"},
        {"from": "rfp_analyze", "to": "go_no_go"},
        {"from": "go_no_go", "to": "strategy_generate"},
        {"from": "strategy_generate", "to": "plan_story"},
        {"from": "plan_story", "to": "proposal_write_next"},
        {"from": "proposal_write_next", "to": "self_review"},
        {"from": "self_review", "to": "ppt_toc"},
        {"from": "ppt_toc", "to": "ppt_storyboard"},
    ]

    return ok({"nodes": nodes, "edges": workflow_edges})


# ── Phase C: 사람 수정 기록 (POST 고정 경로) ──


class EditActionRequest(BaseModel):
    """사람 수정 행동 기록 요청."""
    proposal_id: str
    section_id: str
    action: str  # accept | edit | reject | regenerate
    original: str = ""
    edited: str = ""


@router.post("/edit-action")
async def record_edit_action(body: EditActionRequest, user=Depends(get_current_user)):
    """사람의 편집 행동 기록."""
    from app.services.domains.proposal.human_edit_tracker import record_action

    await record_action(
        proposal_id=body.proposal_id,
        section_id=body.section_id,
        action=body.action,
        original=body.original,
        edited=body.edited,
        user_id=user.id,
    )
    return ok(None, message="기록 완료")


# ── Phase D: 실험 API (고정 경로, 패턴 경로보다 먼저) ──


class ExperimentRequest(BaseModel):
    """A/B 실험 시작 요청."""
    prompt_id: str
    candidate_version: int
    traffic_pct: int = 20
    experiment_name: str = ""
    min_samples: int = 5


@router.post("/experiments/create")
async def start_experiment_endpoint(
    body: ExperimentRequest,
    user=Depends(get_current_user),
):
    """A/B 실험 시작."""
    from app.services.domains.proposal.prompt_evolution import start_experiment

    exp_id = await start_experiment(
        prompt_id=body.prompt_id,
        candidate_version=body.candidate_version,
        traffic_pct=body.traffic_pct,
        experiment_name=body.experiment_name,
        min_samples=body.min_samples,
    )
    if not exp_id:
        return ok({"error": "실험 시작 실패"})
    return ok({"experiment_id": exp_id, "status": "running"})


@router.get("/experiments/list")
async def list_experiments(
    status: Optional[str] = None,
    user=Depends(get_current_user),
):
    """실험 목록."""
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()
    query = client.table("prompt_ab_experiments").select("*").order("started_at", desc=True)
    if status:
        query = query.eq("status", status)

    result = await query.execute()
    return ok({"experiments": result.data or []})


@router.post("/experiments/{experiment_id}/evaluate")
async def evaluate_experiment_endpoint(
    experiment_id: str,
    user=Depends(get_current_user),
):
    """실험 결과 평가."""
    from app.services.domains.proposal.prompt_evolution import evaluate_experiment

    result = await evaluate_experiment(experiment_id)
    return ok(result)


@router.post("/experiments/{experiment_id}/promote")
async def promote_endpoint(
    experiment_id: str,
    user=Depends(get_current_user),
):
    """후보 승격."""
    from app.services.domains.proposal.prompt_evolution import promote_candidate

    result = await promote_candidate(experiment_id)
    return ok(result)


@router.post("/experiments/{experiment_id}/rollback")
async def rollback_endpoint(
    experiment_id: str,
    user=Depends(get_current_user),
):
    """실험 롤백."""
    from app.services.domains.proposal.prompt_evolution import rollback_experiment

    result = await rollback_experiment(experiment_id)
    return ok(result)


# ════════════════════════════════════════════════════════
# 패턴 경로 (/{prompt_id}/... — 반드시 고정 경로 뒤에 배치)
# ════════════════════════════════════════════════════════


@router.get("/{prompt_id}/analysis")
async def get_prompt_analysis(prompt_id: str, user=Depends(require_role("admin"))):
    """개별 프롬프트 심층 패턴 분석."""
    from app.services.domains.proposal.prompt_analyzer import analyze_prompt, _prompt_id_to_label

    result = await analyze_prompt(prompt_id, days=90)
    result["label"] = _prompt_id_to_label(prompt_id)
    return ok(result)


@router.post("/{prompt_id}/run-analysis")
async def run_prompt_analysis(prompt_id: str, user=Depends(require_role("admin"))):
    """온디맨드 패턴 분석 실행 (결과 갱신)."""
    from app.services.domains.proposal.prompt_analyzer import analyze_prompt, _prompt_id_to_label

    result = await analyze_prompt(prompt_id, days=90)
    result["label"] = _prompt_id_to_label(prompt_id)
    return ok(result)


@router.get("/{prompt_id}/detail")
async def get_prompt_detail(prompt_id: str, user=Depends(get_current_user)):
    """프롬프트 상세 + 전체 버전 이력."""
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()
    result = await (
        client.table("prompt_registry")
        .select("*")
        .eq("prompt_id", prompt_id)
        .order("version", desc=True)
        .execute()
    )

    versions = result.data or []
    active = next((v for v in versions if v["status"] == "active"), None)

    return ok({
        "prompt_id": prompt_id,
        "active_version": active,
        "versions": versions,
        "total_versions": len(versions),
    })


@router.get("/{prompt_id}/effectiveness")
async def get_effectiveness(
    prompt_id: str,
    version: Optional[int] = None,
    user=Depends(get_current_user),
):
    """프롬프트 성과 메트릭."""
    from app.services.domains.proposal.prompt_tracker import compute_effectiveness

    metrics = await compute_effectiveness(prompt_id, version)
    return ok(metrics)


class CandidateRequest(BaseModel):
    """후보 프롬프트 등록 요청."""
    text: str
    reason: str


@router.post("/{prompt_id}/suggest-improvement")
async def suggest_improvement(prompt_id: str, user=Depends(get_current_user)):
    """AI 개선 제안 (오프라인 분석)."""
    from app.services.domains.proposal.prompt_evolution import suggest_improvements

    result = await suggest_improvements(prompt_id)
    return ok(result)


@router.post("/{prompt_id}/create-candidate")
async def create_candidate_endpoint(
    prompt_id: str,
    body: CandidateRequest,
    user=Depends(get_current_user),
):
    """후보 프롬프트 등록."""
    from app.services.domains.proposal.prompt_evolution import create_candidate

    version = await create_candidate(prompt_id, body.text, body.reason)
    if version is None:
        return ok({"error": "등록 실패"})
    return ok({"version": version, "status": "candidate"})


# ════════════════════════════════════════════════════════
# Admin: 시뮬레이션 + 제안 이력 (패턴 경로)
# ════════════════════════════════════════════════════════


class SimulateRequest(BaseModel):
    """시뮬레이션 실행 요청."""
    prompt_text: Optional[str] = None
    data_source: str = "sample"
    data_source_id: Optional[str] = None
    custom_variables: Optional[dict] = None
    run_quality_check: bool = True


class CompareRequest(BaseModel):
    """A vs B 비교 시뮬레이션 요청."""
    version_a: Optional[int] = None
    text_a: Optional[str] = None
    version_b: Optional[int] = None
    text_b: Optional[str] = None
    data_source: str = "sample"
    data_source_id: Optional[str] = None
    run_quality_check: bool = True


class SuggestionFeedbackRequest(BaseModel):
    """AI 제안 피드백."""
    accepted_index: Optional[int] = None
    feedback: str = ""


@router.post("/{prompt_id}/simulate")
async def simulate_prompt(
    prompt_id: str,
    body: SimulateRequest,
    user=Depends(require_role("admin")),
):
    """프롬프트 시뮬레이션 실행."""
    from app.services.domains.proposal.prompt_simulator import (
        SimulationRequest, check_quota, run_simulation,
    )

    user_id = user.id
    allowed, remaining = await check_quota(user_id)
    if not allowed:
        from app.exceptions import RateLimitError
        raise RateLimitError("일일 시뮬레이션 한도 초과")

    req = SimulationRequest(
        prompt_text=body.prompt_text,
        data_source=body.data_source,
        data_source_id=body.data_source_id,
        custom_variables=body.custom_variables,
        run_quality_check=body.run_quality_check,
    )
    result = await run_simulation(prompt_id, req, user_id)
    return ok(result.model_dump())


@router.post("/{prompt_id}/simulate-compare")
async def simulate_compare(
    prompt_id: str,
    body: CompareRequest,
    user=Depends(require_role("admin")),
):
    """A vs B 비교 시뮬레이션."""
    from app.services.domains.proposal.prompt_simulator import check_quota, run_comparison

    user_id = user.id
    allowed, _ = await check_quota(user_id)
    if not allowed:
        from app.exceptions import RateLimitError
        raise RateLimitError("일일 시뮬레이션 한도 초과")

    return ok(await run_comparison(
        prompt_id,
        version_a=body.version_a, text_a=body.text_a,
        version_b=body.version_b, text_b=body.text_b,
        data_source=body.data_source,
        data_source_id=body.data_source_id,
        run_quality_check=body.run_quality_check,
        user_id=user_id,
    ))


@router.get("/{prompt_id}/simulations")
async def get_simulations(
    prompt_id: str,
    limit: int = Query(20, ge=1, le=100),
    user=Depends(require_role("admin")),
):
    """시뮬레이션 이력 조회."""
    from app.services.domains.proposal.prompt_simulator import get_simulation_history

    simulations = await get_simulation_history(prompt_id, limit)
    return ok({"simulations": simulations})


@router.get("/{prompt_id}/suggestions")
async def get_suggestion_history(
    prompt_id: str,
    user=Depends(require_role("admin")),
):
    """AI 개선 제안 이력 조회."""
    from app.utils.supabase_client import get_async_client

    try:
        client = await get_async_client()
        result = await (
            client.table("prompt_improvement_suggestions")
            .select("*")
            .eq("prompt_id", prompt_id)
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        return ok({"suggestions": result.data or []})
    except Exception:
        return ok({"suggestions": []})


@router.post("/{prompt_id}/suggestions/{suggestion_id}/feedback")
async def post_suggestion_feedback(
    prompt_id: str,
    suggestion_id: str,
    body: SuggestionFeedbackRequest,
    user=Depends(require_role("admin")),
):
    """AI 제안 수용/거부 피드백 기록."""
    from app.utils.supabase_client import get_async_client

    try:
        client = await get_async_client()
        await (
            client.table("prompt_improvement_suggestions")
            .update({
                "accepted_index": body.accepted_index,
                "feedback": body.feedback,
            })
            .eq("id", suggestion_id)
            .execute()
        )
        return ok(None, message="피드백 저장 완료")
    except Exception:
        return ok({"updated": False})
