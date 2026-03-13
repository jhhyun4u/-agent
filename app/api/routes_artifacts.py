"""
산출물 + 다운로드 + Compliance Matrix API (§12-4)

GET  /api/proposals/{id}/artifacts/{step}          — 산출물 조회
GET  /api/proposals/{id}/download/docx             — DOCX 다운로드
GET  /api/proposals/{id}/download/pptx             — PPTX 다운로드
GET  /api/proposals/{id}/compliance                — Compliance Matrix
POST /api/proposals/{id}/compliance/check          — Compliance AI 체크 실행
"""

import logging

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.api.deps import get_current_user, require_project_access
from app.exceptions import PropNotFoundError

router = APIRouter(prefix="/api/proposals", tags=["artifacts"])
logger = logging.getLogger(__name__)


@router.get("/{proposal_id}/artifacts/{step}")
async def get_artifacts(
    proposal_id: str,
    step: str,
    user=Depends(get_current_user),
):
    """단계별 산출물 조회 (그래프 상태에서 추출)."""
    from app.api.routes_workflow import _get_graph

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    try:
        snapshot = await graph.aget_state(config)
        if not snapshot:
            raise PropNotFoundError(proposal_id)

        state = snapshot.values
        artifact_map = {
            "search": state.get("search_results"),
            "rfp_fetch": state.get("bid_detail"),
            "rfp_analyze": state.get("rfp_analysis"),
            "research": state.get("research_brief"),
            "go_no_go": state.get("go_no_go"),
            "strategy": state.get("strategy"),
            "plan": state.get("plan"),
            "proposal": state.get("proposal_sections"),
            "self_review": state.get("parallel_results", {}).get("_self_review_score"),
            "presentation_strategy": state.get("presentation_strategy"),
            "ppt": state.get("ppt_slides"),
        }

        artifact = artifact_map.get(step)
        if artifact is None:
            return {"step": step, "artifact": None, "message": "해당 단계 산출물 없음"}

        # Pydantic 모델 직렬화
        if hasattr(artifact, "model_dump"):
            data = artifact.model_dump()
        elif isinstance(artifact, list):
            data = [a.model_dump() if hasattr(a, "model_dump") else a for a in artifact]
        else:
            data = artifact

        return {"step": step, "artifact": data}
    except PropNotFoundError:
        raise
    except Exception as e:
        logger.error(f"산출물 조회 실패: {e}")
        return {"step": step, "artifact": None, "error": str(e)}


@router.get("/{proposal_id}/download/docx")
async def download_docx(
    proposal_id: str,
    user=Depends(get_current_user),
):
    """DOCX 다운로드 (중간 버전 포함)."""
    from app.api.routes_workflow import _get_graph
    from app.services.docx_builder import build_docx

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot:
        raise PropNotFoundError(proposal_id)

    state = snapshot.values
    sections = state.get("proposal_sections", [])
    rfp = state.get("rfp_analysis")
    proposal_name = state.get("project_name", "제안서")

    if not sections:
        return Response(
            content=b"",
            status_code=204,
            headers={"X-Message": "No sections available"},
        )

    docx_bytes = await build_docx(sections, rfp, proposal_name)

    filename = f"{proposal_name}_제안서.docx"
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{proposal_id}/download/pptx")
async def download_pptx(
    proposal_id: str,
    user=Depends(get_current_user),
):
    """PPTX 다운로드."""
    from app.api.routes_workflow import _get_graph
    from app.services.pptx_builder import build_pptx

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot:
        raise PropNotFoundError(proposal_id)

    state = snapshot.values
    slides = state.get("ppt_slides", [])
    proposal_name = state.get("project_name", "제안서")
    pres_strategy = state.get("presentation_strategy")

    if not slides:
        return Response(
            content=b"",
            status_code=204,
            headers={"X-Message": "No slides available"},
        )

    # Pydantic 모델 → dict 변환
    slide_dicts = [s.model_dump() if hasattr(s, "model_dump") else s for s in slides]
    pres_dict = pres_strategy.model_dump() if hasattr(pres_strategy, "model_dump") else pres_strategy

    pptx_bytes = await build_pptx(slide_dicts, proposal_name, pres_dict)

    filename = f"{proposal_name}_발표자료.pptx"
    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{proposal_id}/compliance")
async def get_compliance_matrix(
    proposal_id: str,
    user=Depends(get_current_user),
):
    """Compliance Matrix 현재 상태."""
    from app.api.routes_workflow import _get_graph

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot:
        raise PropNotFoundError(proposal_id)

    matrix = snapshot.values.get("compliance_matrix", [])
    data = [m.model_dump() if hasattr(m, "model_dump") else m for m in matrix]

    # 통계
    total = len(data)
    met = sum(1 for d in data if d.get("status") == "충족")
    unmet = sum(1 for d in data if d.get("status") == "미충족")
    unchecked = sum(1 for d in data if d.get("status") == "미확인")

    return {
        "items": data,
        "stats": {
            "total": total,
            "met": met,
            "unmet": unmet,
            "unchecked": unchecked,
            "compliance_rate": round(met / total * 100, 1) if total else 0,
        },
    }


@router.post("/{proposal_id}/compliance/check")
async def run_compliance_check(
    proposal_id: str,
    user=Depends(get_current_user),
):
    """Compliance Matrix AI 체크 실행."""
    from app.api.routes_workflow import _get_graph
    from app.services.compliance_tracker import ComplianceTracker

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot:
        raise PropNotFoundError(proposal_id)

    state = snapshot.values
    sections = state.get("proposal_sections", [])
    matrix = state.get("compliance_matrix", [])

    if not sections or not matrix:
        return {"message": "섹션 또는 Compliance Matrix가 없습니다.", "checked": 0}

    updated = await ComplianceTracker.check_compliance(sections, matrix)
    data = [m.model_dump() if hasattr(m, "model_dump") else m for m in updated]

    return {
        "items": data,
        "checked": len(data),
        "message": f"Compliance 체크 완료: {len(data)}개 항목",
    }
