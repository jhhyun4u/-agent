"""⚠️ DEPRECATED: v3.1 Phase 기반 API 엔드포인트.

이 모듈은 LangGraph 기반 워크플로(routes_workflow.py, routes_proposal.py)로 대체되었습니다.
프론트엔드(frontend/lib/api.ts)가 /api/v3.1/* 엔드포인트를 아직 호출 중이므로 삭제 불가.
프론트엔드 마이그레이션 완료 후 삭제 예정.
"""

import logging
import os
import uuid
from typing import List, Optional

import json as _json

from fastapi import APIRouter, BackgroundTasks, Depends, Form, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import settings
from app.services.core.session_manager import session_manager
from app.models.phase_schemas import Phase1Artifact, Phase2Artifact, Phase3Artifact, Phase4Artifact
from app.services.legacy.phase_executor import PhaseExecutor
from app.services.domains.bidding.bid_calculator import BidCalculator, PersonnelInput, ProcurementMethod, parse_budget_string
from app.exceptions import (
    FileSizeExceededError, FileFormatError, FileNotFoundError_,
    InvalidRequestError, ConflictError, InternalServiceError, PropNotFoundError,
    ResourceNotFoundError,
)
from app.services.tools.template_service import get_available_templates, get_template_toc, clear_toc_cache
from app.api.deps import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v3.1", tags=["v3.1"])


async def _run_phases(proposal_id: str, rfp_content: str):
    """백그라운드에서 5-Phase 파이프라인 실행 (Phase 1부터)"""
    executor = PhaseExecutor(proposal_id, session_manager)
    try:
        final = await executor.execute_all(rfp_content)
        session_manager.update_session(proposal_id, {
            "docx_path": final.docx_path,
            "pptx_path": final.pptx_path,
            "hwpx_path": final.hwpx_path,
        })
        logger.info(f"Phase 실행 완료: {proposal_id} (score={final.quality_score})")
    except Exception as e:
        logger.error(f"Phase 실행 실패: {proposal_id} — {e}")


async def _run_phases_from(proposal_id: str, start_phase: int):
    """백그라운드에서 특정 Phase부터 파이프라인 재실행"""
    executor = PhaseExecutor(proposal_id, session_manager)
    try:
        final = await executor.execute_from_phase(start_phase)
        session_manager.update_session(proposal_id, {
            "docx_path": final.docx_path,
            "pptx_path": final.pptx_path,
            "hwpx_path": final.hwpx_path,
        })
        logger.info(f"Phase {start_phase}부터 재실행 완료: {proposal_id} (score={final.quality_score})")
    except Exception as e:
        logger.error(f"Phase {start_phase}부터 재실행 실패: {proposal_id} — {e}")


@router.post("/proposals/generate")
async def generate_proposal_v31(
    rfp_title: str = Form(...),
    client_name: str = Form(...),
    rfp_content: Optional[str] = Form(None),
    rfp_file: Optional[UploadFile] = File(None),
    express_mode: bool = Form(False),
    team_id: Optional[str] = Form(None),
    section_ids: Optional[str] = Form(None),  # JSON 배열 문자열 ex) '["uuid1","uuid2"]'
    form_template_id: Optional[str] = Form(None),
    current_user=Depends(get_current_user),
):
    """v3.4 제안서 세션 초기화"""
    proposal_id = str(uuid.uuid4())
    owner_id = current_user.id

    rfp_text = ""
    if rfp_file:
        # 파일 크기 검증
        content = await rfp_file.read()
        max_bytes = settings.max_file_size_mb * 1024 * 1024
        if len(content) > max_bytes:
            raise FileSizeExceededError(settings.max_file_size_mb, len(content) / (1024 * 1024))
        # 확장자 검증
        ext = os.path.splitext(rfp_file.filename or "")[1].lower()
        if ext not in settings.allowed_file_extensions:
            raise FileFormatError(ext, list(settings.allowed_file_extensions))
        rfp_text = content.decode("utf-8", errors="ignore")
    elif rfp_content:
        rfp_text = rfp_content
    else:
        raise InvalidRequestError("RFP 콘텐츠가 필요합니다.")

    # section_ids JSON 파싱
    parsed_section_ids: Optional[List[str]] = None
    if section_ids:
        try:
            parsed_section_ids = _json.loads(section_ids)
        except (ValueError, TypeError):
            parsed_section_ids = None

    try:
        session_manager.create_session(
            proposal_id=proposal_id,
            initial_data={
                "rfp_title": rfp_title,
                "client_name": client_name,
                "owner_id": owner_id,
                "team_id": team_id,
                "section_ids": parsed_section_ids,
                "form_template_id": form_template_id or None,
                "phases_completed": 0,
                "proposal_state": {
                    "rfp_title": rfp_title,
                    "client_name": client_name,
                    "rfp_content": rfp_text,
                    "express_mode": express_mode,
                },
            },
            session_type="v3.1",
        )
        logger.info(f"세션 생성: {proposal_id} | {rfp_title} | owner={owner_id}")
        return {
            "proposal_id": proposal_id,
            "status": "initialized",
            "message": "세션이 초기화되었습니다. /execute를 호출하여 생성을 시작하세요.",
            "rfp_title": rfp_title,
            "client_name": client_name,
        }
    except Exception as e:
        logger.error(f"세션 생성 오류: {proposal_id} — {e}")
        raise InternalServiceError("제안서 세션 생성 중 오류가 발생했습니다.")


@router.get("/proposals/{proposal_id}/status")
async def get_proposal_status_v31(proposal_id: str, current_user=Depends(get_current_user)):
    """제안서 진행 상태 조회"""
    session = await session_manager.aget_session(proposal_id)

    return {
        "proposal_id": proposal_id,
        "rfp_title": session.get("rfp_title", ""),
        "client_name": session.get("client_name", ""),
        "status": session.get("status", "unknown"),
        "current_phase": session.get("current_phase", "pending"),
        "phases_completed": session.get("phases_completed", 0),
        "created_at": (session.get("created_at") or "").isoformat() if hasattr(session.get("created_at"), "isoformat") else str(session.get("created_at", "")),
        "error": session.get("error", ""),
    }


@router.get("/proposals/{proposal_id}/result")
async def get_proposal_result_v31(proposal_id: str, current_user=Depends(get_current_user)):
    """제안서 최종 결과 조회"""
    session = await session_manager.aget_session(proposal_id)

    artifacts = {
        "phase_1_research": session.get("phase_artifact_1", {}),
        "phase_2_analysis": session.get("phase_artifact_2", {}),
        "phase_3_plan": session.get("phase_artifact_3", {}),
        "phase_4_implement": session.get("phase_artifact_4", {}),
        "phase_5_test": session.get("phase_artifact_5", {}),
    }

    return {
        "proposal_id": proposal_id,
        "status": session.get("status", "unknown"),
        "rfp_title": session.get("rfp_title", ""),
        "client_name": session.get("client_name", ""),
        "phases_completed": session.get("phases_completed", 0),
        "artifacts": artifacts,
        "quality_score": session.get("phase_artifact_5", {}).get("quality_score", 0),
        "docx_path": session.get("docx_path", ""),
        "pptx_path": session.get("pptx_path", ""),
        "hwpx_path": session.get("hwpx_path", ""),
        "executive_summary": session.get("phase_artifact_5", {}).get("executive_summary", ""),
    }


@router.post("/proposals/{proposal_id}/execute", status_code=202)
async def execute_proposal_phase_v31(
    proposal_id: str,
    background_tasks: BackgroundTasks,
    start_phase: int = 1,
    current_user=Depends(get_current_user),
):
    """5-Phase 파이프라인 비동기 실행 (즉시 202 반환, 백그라운드 실행)"""
    session = await session_manager.aget_session(proposal_id)

    current_status = session.get("status", "initialized")
    if current_status == "processing":
        raise ConflictError("이미 실행 중입니다.")
    if current_status == "completed":
        raise ConflictError("이미 완료된 제안서입니다.")

    if start_phase not in range(1, 6):
        raise InvalidRequestError("start_phase는 1~5여야 합니다.")

    rfp_content = session.get("proposal_state", {}).get("rfp_content", "")
    if not rfp_content:
        raise InvalidRequestError("RFP 콘텐츠가 없습니다.")

    if start_phase == 1:
        background_tasks.add_task(_run_phases, proposal_id, rfp_content)
    else:
        background_tasks.add_task(_run_phases_from, proposal_id, start_phase)

    return {
        "proposal_id": proposal_id,
        "status": "processing",
        "start_phase": start_phase,
        "message": f"Phase {start_phase}부터 파이프라인이 백그라운드에서 시작되었습니다. /status로 진행 상태를 확인하세요.",
    }


@router.get("/proposals/{proposal_id}/download/{file_type}")
async def download_document(proposal_id: str, file_type: str, current_user=Depends(get_current_user)):
    """
    DOCX/PPTX 다운로드

    우선순위:
    1. Supabase Storage 서명 URL 리다이렉트 (업로드 완료된 경우)
    2. 로컬 파일 직접 반환 (Storage 미업로드 또는 개발 환경)
    """
    import os
    from fastapi.responses import RedirectResponse
    from app.utils.supabase_client import get_async_client

    if file_type not in ("docx", "pptx", "hwpx"):
        raise InvalidRequestError("file_type은 docx, pptx, hwpx 중 하나여야 합니다.")
    session = await session_manager.aget_session(proposal_id)

    # 1. Storage 서명 URL 시도
    storage_path = session.get(f"{file_type}_storage_path", "")
    if storage_path:
        try:
            client = await get_async_client()
            signed = await client.storage.from_(settings.storage_bucket_proposals).create_signed_url(
                storage_path, expires_in=300  # 5분 유효
            )
            url = signed.get("signedURL") or signed.get("signed_url", "")
            if url:
                return RedirectResponse(url=url)
        except Exception as e:
            logger.warning(f"Storage 서명 URL 생성 실패, 로컬 폴백: {e}")

    # 2. 로컬 파일 폴백
    path = session.get(f"{file_type}_path", "")
    if not path:
        raise FileNotFoundError_("파일이 아직 생성되지 않았습니다.")
    if not os.path.exists(path):
        raise FileNotFoundError_("파일을 찾을 수 없습니다.")
    return FileResponse(path, filename=f"proposal_{proposal_id}.{file_type}")


class PersonnelRequest(BaseModel):
    role: str
    grade: str
    person_months: float
    labor_type: str = "SW"


class BidCalculateRequest(BaseModel):
    personnel: List[PersonnelRequest]
    procurement_method: str = "종합평가"
    budget: Optional[str] = None
    price_weight: int = 20
    competitor_count: int = 5


@router.post("/bid/calculate")
async def calculate_bid(req: BidCalculateRequest, current_user=Depends(get_current_user)):
    """낙찰가 계산 (인건비 기준 원가 산출 + 입찰 전략)"""
    method_map = {
        "최저가": ProcurementMethod.LOWEST_PRICE,
        "적격심사": ProcurementMethod.ADEQUATE_REVIEW,
        "종합평가": ProcurementMethod.COMPREHENSIVE,
        "수의계약": ProcurementMethod.NEGOTIATED,
    }
    method = method_map.get(req.procurement_method, ProcurementMethod.COMPREHENSIVE)
    budget_int = parse_budget_string(req.budget)

    personnel = [
        PersonnelInput(role=p.role, grade=p.grade, person_months=p.person_months, labor_type=p.labor_type)
        for p in req.personnel
    ]

    calc = BidCalculator()
    cost = calc.calculate_cost(personnel)
    result = calc.optimize_bid(
        cost, method, budget=budget_int,
        price_weight=req.price_weight,
        competitor_count=req.competitor_count,
    )
    return calc.to_dict(result)

@router.get("/templates")
async def list_templates(current_user=Depends(get_current_user)):
    """사용 가능한 제안서 템플릿 목록 반환"""
    templates = get_available_templates()
    return {"templates": templates, "count": len(templates)}


@router.get("/templates/toc")
async def get_default_toc(filename: str = None, current_user=Depends(get_current_user)):
    """템플릿 기반 기본 목차 반환 (RFP 목차 없을 때 사용되는 기본값 미리보기)"""
    toc = await get_template_toc(prefer_filename=filename)
    return {"table_of_contents": toc, "count": len(toc)}


@router.post("/templates/cache/clear")
async def clear_template_cache(current_user=Depends(get_current_user)):
    """템플릿 TOC 캐시 초기화 (템플릿 파일 변경 후 사용)"""
    clear_toc_cache()
    return {"message": "템플릿 TOC 캐시가 초기화되었습니다."}


# ── Phase 개별 실행 ──────────────────────────────────────────

_PHASE_LABELS = {
    1: "phase_1_research",
    2: "phase_2_analysis",
    3: "phase_3_plan",
    4: "phase_4_implement",
    5: "phase_5_test",
}


@router.post("/proposals/{proposal_id}/phase/{phase_num}")
async def run_single_phase(proposal_id: str, phase_num: int, current_user=Depends(get_current_user)):
    """Phase 1~5 개별 실행 (동기). 이전 Phase 아티팩트는 세션에서 자동 로드.

    흐름:
      POST /generate  →  POST /phase/1  →  POST /phase/2  →  ...  →  POST /phase/5
    """
    if phase_num not in range(1, 6):
        raise InvalidRequestError("phase_num은 1~5여야 합니다.")

    session = await session_manager.aget_session(proposal_id)

    if session.get("status") == "processing":
        raise ConflictError("이미 실행 중입니다.")

    phases_completed = session.get("phases_completed", 0)
    if phase_num > 1 and phases_completed < phase_num - 1:
        raise InvalidRequestError(
            f"Phase {phase_num - 1}을 먼저 실행해야 합니다. 현재 완료: Phase {phases_completed}",
        )

    rfp_content = session.get("proposal_state", {}).get("rfp_content", "")
    if not rfp_content:
        raise InvalidRequestError("RFP 콘텐츠가 없습니다.")

    executor = PhaseExecutor(proposal_id, session_manager)

    def _load(artifact_cls, key):
        data = session.get(key, {})
        return artifact_cls(**{k: v for k, v in data.items() if k in artifact_cls.model_fields})

    try:
        if phase_num == 1:
            artifact = await executor.phase1_research(rfp_content)
        elif phase_num == 2:
            a1 = _load(Phase1Artifact, "phase_artifact_1")
            artifact = await executor.phase2_analysis(a1)
        elif phase_num == 3:
            a2 = _load(Phase2Artifact, "phase_artifact_2")
            artifact = await executor.phase3_plan(a2)
        elif phase_num == 4:
            a1 = _load(Phase1Artifact, "phase_artifact_1")
            a3 = _load(Phase3Artifact, "phase_artifact_3")
            artifact = await executor.phase4_implement(a3, a1)
        else:  # phase_num == 5
            a2 = _load(Phase2Artifact, "phase_artifact_2")
            a4 = _load(Phase4Artifact, "phase_artifact_4")
            artifact = await executor.phase5_test(a4, a2)
            session_manager.update_session(proposal_id, {
                "status": "completed",
                "docx_path": artifact.docx_path,
                "pptx_path": artifact.pptx_path,
                "hwpx_path": artifact.hwpx_path,
            })
            import asyncio as _asyncio
            _asyncio.create_task(executor._upload_to_storage(
                docx_path=artifact.docx_path or "",
                pptx_path=artifact.pptx_path or "",
                hwpx_path=artifact.hwpx_path or "",
            ))

        updated = session_manager.get_session(proposal_id)
        next_phase = phase_num + 1 if phase_num < 5 else None
        msg = (
            f"Phase {phase_num} 완료. Phase {next_phase}을 실행하세요."
            if next_phase else
            "모든 Phase 완료. /result에서 최종 결과를 확인하세요."
        )
        return {
            "proposal_id": proposal_id,
            "phase": phase_num,
            "phase_label": _PHASE_LABELS[phase_num],
            "phases_completed": updated.get("phases_completed", phase_num),
            "next_phase": next_phase,
            "message": msg,
            "artifact_summary": artifact.summary if hasattr(artifact, "summary") else "",
        }

    except Exception as e:
        session_manager.update_session(proposal_id, {"status": "failed", "error": str(e)})
        logger.error(f"[{proposal_id}] Phase {phase_num} 실패: {e}")
        raise InternalServiceError(f"Phase {phase_num} 실행 중 오류가 발생했습니다.")


@router.get("/proposals/{proposal_id}/versions")
async def get_proposal_versions(proposal_id: str, current_user=Depends(get_current_user)):
    """제안서 버전 목록 조회 (같은 패밀리의 모든 버전)"""
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()

    # 루트 찾기: parent_id가 NULL인 조상까지 올라감
    current_id = proposal_id
    while True:
        resp = client.table("proposals").select("id, parent_id").eq("id", current_id).single().execute()
        if not resp.data:
            raise PropNotFoundError(current_id)
        if resp.data.get("parent_id") is None:
            root_id = current_id
            break
        current_id = resp.data["parent_id"]

    # 루트 자신 + 루트의 직접/간접 자식 모두 조회
    # (parent_id = root_id 조건은 직계 자식만 포함하므로, 전체 패밀리를 위해 재귀 없이
    #  root_id를 공유하는 방식으로 단순화: root 포함하고 parent_id 체인 전체 수집)
    all_ids: list[str] = [root_id]
    queue: list[str] = [root_id]
    while queue:
        parent_batch = queue
        queue = []
        children_resp = (
            client.table("proposals")
            .select("id")
            .in_("parent_id", parent_batch)
            .execute()
        )
        for row in (children_resp.data or []):
            cid = row["id"]
            if cid not in all_ids:
                all_ids.append(cid)
                queue.append(cid)

    versions_resp = (
        client.table("proposals")
        .select("id, title, version, status, created_at, phases_completed")
        .in_("id", all_ids)
        .order("version", desc=False)
        .execute()
    )
    return {"versions": versions_resp.data or []}


@router.post("/proposals/{proposal_id}/new-version", status_code=201)
async def create_new_version(proposal_id: str, current_user=Depends(get_current_user)):
    """기존 제안서 기반으로 새 버전 생성 (실행은 /execute로 별도 호출)"""
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()

    # 소스 제안서 조회
    src_resp = (
        client.table("proposals")
        .select("id, rfp_title, client_name, owner_id, team_id, section_ids, parent_id, version")
        .eq("id", proposal_id)
        .single()
        .execute()
    )
    if not src_resp.data:
        raise PropNotFoundError(proposal_id)
    src = src_resp.data

    # 루트 ID 결정
    root_id = proposal_id if src.get("parent_id") is None else src["parent_id"]

    # 같은 패밀리 최대 version 조회
    family_resp = (
        client.table("proposals")
        .select("version")
        .or_(f"id.eq.{root_id},parent_id.eq.{root_id}")
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    max_version = (family_resp.data[0]["version"] if family_resp.data else src.get("version", 1)) or 1
    new_version_num = max_version + 1

    # rfp_content는 세션에서 복사
    rfp_content = ""
    try:
        session = await session_manager.aget_session(proposal_id)
        rfp_content = session.get("proposal_state", {}).get("rfp_content", "")
    except Exception:
        pass

    new_id = str(uuid.uuid4())

    # DB에 새 행 삽입
    insert_data = {
        "id": new_id,
        "rfp_title": src.get("rfp_title", ""),
        "client_name": src.get("client_name", ""),
        "owner_id": src.get("owner_id", current_user.id),
        "team_id": src.get("team_id"),
        "section_ids": src.get("section_ids"),
        "parent_id": proposal_id,
        "version": new_version_num,
        "status": "initialized",
        "phases_completed": 0,
    }
    ins_resp = client.table("proposals").insert(insert_data).execute()
    if not ins_resp.data:
        raise InternalServiceError("새 버전 생성에 실패했습니다.")

    # 세션 초기화 (rfp_content 포함)
    try:
        session_manager.create_session(
            proposal_id=new_id,
            initial_data={
                "rfp_title": src.get("rfp_title", ""),
                "client_name": src.get("client_name", ""),
                "owner_id": src.get("owner_id", current_user.id),
                "team_id": src.get("team_id"),
                "phases_completed": 0,
                "proposal_state": {
                    "rfp_title": src.get("rfp_title", ""),
                    "client_name": src.get("client_name", ""),
                    "rfp_content": rfp_content,
                    "express_mode": False,
                },
            },
            session_type="v3.1",
        )
    except Exception as e:
        logger.warning(f"새 버전 세션 생성 실패 (DB 행은 생성됨): {e}")

    logger.info(f"새 버전 생성: {new_id} (version={new_version_num}, parent={proposal_id})")
    return {"proposal_id": new_id, "version": new_version_num, "status": "initialized"}


@router.get("/proposals/{proposal_id}/phase/{phase_num}")
async def get_phase_artifact(proposal_id: str, phase_num: int, current_user=Depends(get_current_user)):
    """특정 Phase 아티팩트 조회"""
    if phase_num not in range(1, 6):
        raise InvalidRequestError("phase_num은 1~5여야 합니다.")
    session = await session_manager.aget_session(proposal_id)

    key = f"phase_artifact_{phase_num}"
    artifact = session.get(key)
    if not artifact:
        raise ResourceNotFoundError(
            f"Phase {phase_num} 아티팩트",
        )
    return {
        "proposal_id": proposal_id,
        "phase": phase_num,
        "phase_label": _PHASE_LABELS[phase_num],
        "artifact": artifact,
    }
