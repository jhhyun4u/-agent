"""
프롬프트 진화 API (Phase B + D)

고정 경로를 패턴 경로보다 먼저 등록하여 라우트 충돌 방지.

── 고정 경로 (GET) ──
GET  /api/prompts/dashboard                    — 대시보드 집계
GET  /api/prompts/section-heatmap              — 섹션 유형별 히트맵
GET  /api/prompts/list                         — 전체 목록

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
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.deps import get_current_user

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

    return {
        "prompts": prompts.data or [],
        "effectiveness": effectiveness,
        "edit_stats": edit_stats,
        "running_experiments": experiments,
        "total_prompts": len(prompts.data or []),
    }


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

    return {"heatmap": sorted(result, key=lambda x: x["usage_count"], reverse=True)}


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
    return {"prompts": result.data or []}


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
    from app.services.human_edit_tracker import record_action

    await record_action(
        proposal_id=body.proposal_id,
        section_id=body.section_id,
        action=body.action,
        original=body.original,
        edited=body.edited,
        user_id=user.get("id"),
    )
    return {"recorded": True}


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
    from app.services.prompt_evolution import start_experiment

    exp_id = await start_experiment(
        prompt_id=body.prompt_id,
        candidate_version=body.candidate_version,
        traffic_pct=body.traffic_pct,
        experiment_name=body.experiment_name,
        min_samples=body.min_samples,
    )
    if not exp_id:
        return {"error": "실험 시작 실패"}
    return {"experiment_id": exp_id, "status": "running"}


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
    return {"experiments": result.data or []}


@router.post("/experiments/{experiment_id}/evaluate")
async def evaluate_experiment_endpoint(
    experiment_id: str,
    user=Depends(get_current_user),
):
    """실험 결과 평가."""
    from app.services.prompt_evolution import evaluate_experiment

    result = await evaluate_experiment(experiment_id)
    return result


@router.post("/experiments/{experiment_id}/promote")
async def promote_endpoint(
    experiment_id: str,
    user=Depends(get_current_user),
):
    """후보 승격."""
    from app.services.prompt_evolution import promote_candidate

    result = await promote_candidate(experiment_id)
    return result


@router.post("/experiments/{experiment_id}/rollback")
async def rollback_endpoint(
    experiment_id: str,
    user=Depends(get_current_user),
):
    """실험 롤백."""
    from app.services.prompt_evolution import rollback_experiment

    result = await rollback_experiment(experiment_id)
    return result


# ════════════════════════════════════════════════════════
# 패턴 경로 (/{prompt_id}/... — 반드시 고정 경로 뒤에 배치)
# ════════════════════════════════════════════════════════


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

    return {
        "prompt_id": prompt_id,
        "active_version": active,
        "versions": versions,
        "total_versions": len(versions),
    }


@router.get("/{prompt_id}/effectiveness")
async def get_effectiveness(
    prompt_id: str,
    version: Optional[int] = None,
    user=Depends(get_current_user),
):
    """프롬프트 성과 메트릭."""
    from app.services.prompt_tracker import compute_effectiveness

    metrics = await compute_effectiveness(prompt_id, version)
    return metrics


class CandidateRequest(BaseModel):
    """후보 프롬프트 등록 요청."""
    text: str
    reason: str


@router.post("/{prompt_id}/suggest-improvement")
async def suggest_improvement(prompt_id: str, user=Depends(get_current_user)):
    """AI 개선 제안 (오프라인 분석)."""
    from app.services.prompt_evolution import suggest_improvements

    result = await suggest_improvements(prompt_id)
    return result


@router.post("/{prompt_id}/create-candidate")
async def create_candidate_endpoint(
    prompt_id: str,
    body: CandidateRequest,
    user=Depends(get_current_user),
):
    """후보 프롬프트 등록."""
    from app.services.prompt_evolution import create_candidate

    version = await create_candidate(prompt_id, body.text, body.reason)
    if version is None:
        return {"error": "등록 실패"}
    return {"version": version, "status": "candidate"}
