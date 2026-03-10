"""발표 자료 생성 API (v3.1) — 평가항목 기반 PPTX 자동 생성"""

import asyncio
import logging
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import FileResponse

from app.exceptions import SessionNotFoundError
from app.middleware.auth import get_current_user
from app.models.phase_schemas import Phase2Artifact, Phase3Artifact, Phase4Artifact
from app.models.schemas import RFPData
from app.services.presentation_generator import generate_presentation_slides
from app.services.presentation_pptx_builder import build_presentation_pptx
from app.services.session_manager import session_manager
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v3.1", tags=["presentation"])

# ── 표준 템플릿 메타데이터 ─────────────────────────────────────────────────────

_STANDARD_TEMPLATES = [
    {
        "id": "government_blue",
        "name": "정부/공공기관 스타일",
        "description": "공공입찰 발표에 적합한 블루 계열 공식 스타일",
        "preview_color": "#1F497D",
        "slide_count_example": 8,
    },
    {
        "id": "corporate_modern",
        "name": "기업 현대적 스타일",
        "description": "깔끔한 모던 디자인, SI/컨설팅 발표에 적합",
        "preview_color": "#2E4057",
        "slide_count_example": 10,
    },
    {
        "id": "minimal_clean",
        "name": "심플/미니멀",
        "description": "텍스트 중심, 내용 전달에 집중하는 미니멀 스타일",
        "preview_color": "#444444",
        "slide_count_example": 8,
    },
]

_TEMPLATES_DIR = Path("app/templates/presentation")


# ── 헬퍼 ──────────────────────────────────────────────────────────────────────

def _resolve_template_path(
    mode: str,
    template_id: str,
    sample_storage_path: Optional[str],
) -> Optional[Path]:
    """template_mode → 실제 PPTX 파일 경로. 없으면 None (scratch fallback)"""
    if mode == "standard":
        path = _TEMPLATES_DIR / f"{template_id}.pptx"
        if path.exists():
            return path
        logger.warning(f"표준 템플릿 파일 없음: {path} — scratch로 fallback")
        return None

    if mode == "sample" and sample_storage_path:
        # Storage 경로에서 파일명 추출하여 로컬 캐시 경로 결정
        fname = Path(sample_storage_path).name
        local = Path(tempfile.gettempdir()) / f"sample_template_{fname}"
        return local if local.exists() else None

    return None  # scratch


async def _download_sample_template(storage_path: str) -> Optional[Path]:
    """Supabase Storage에서 샘플 PPTX 다운로드 후 로컬 경로 반환"""
    try:
        fname = Path(storage_path).name
        local_path = Path(tempfile.gettempdir()) / f"sample_template_{fname}"
        if local_path.exists():
            return local_path

        client = await get_async_client()
        bucket, *rest = storage_path.lstrip("/").split("/", 1)
        object_path = rest[0] if rest else storage_path

        data = await asyncio.to_thread(
            lambda: client.storage.from_(bucket).download(object_path)
        )
        local_path.parent.mkdir(parents=True, exist_ok=True)
        local_path.write_bytes(data)
        logger.info(f"샘플 템플릿 다운로드 완료: {local_path}")
        return local_path
    except Exception as e:
        logger.warning(f"샘플 템플릿 다운로드 실패: {e}")
        return None


async def _upload_presentation(proposal_id: str, local_path: str) -> str:
    """PPTX 파일을 Supabase Storage에 업로드하고 공개 URL 반환"""
    try:
        client = await get_async_client()
        bucket = "proposal-files"
        storage_path = f"{proposal_id}/presentation.pptx"
        content_type = "application/vnd.openxmlformats-officedocument.presentationml.presentation"

        file_bytes = await asyncio.to_thread(lambda: open(local_path, "rb").read())
        await client.storage.from_(bucket).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": content_type, "upsert": "true"},
        )
        url = client.storage.from_(bucket).get_public_url(storage_path)
        logger.info(f"발표 자료 Storage 업로드 완료: {storage_path}")
        return url
    except Exception as e:
        logger.warning(f"발표 자료 Storage 업로드 실패 (URL 없이 계속): {e}")
        return ""


# ── 백그라운드 실행 함수 ──────────────────────────────────────────────────────

async def _run_presentation(
    proposal_id: str,
    template_mode: str = "standard",
    template_id: str = "government_blue",
    sample_storage_path: Optional[str] = None,
):
    """발표 자료 PPTX 생성 백그라운드 태스크"""
    try:
        session = await session_manager.aget_session(proposal_id)

        # Artifact 로드
        phase2 = Phase2Artifact(**session["phase_artifact_2"])
        phase3 = Phase3Artifact(**session["phase_artifact_3"])
        phase4 = Phase4Artifact(**session["phase_artifact_4"])
        rfp_raw = session.get("phase_artifact_1", {}).get("rfp_data")
        rfp_data = RFPData(**rfp_raw) if rfp_raw else None

        # 슬라이드 JSON 생성 (Claude API)
        slides_json = await generate_presentation_slides(phase2, phase3, phase4, rfp_data)

        # 샘플 모드: Storage에서 다운로드
        if template_mode == "sample" and sample_storage_path:
            await _download_sample_template(sample_storage_path)

        template_path = _resolve_template_path(template_mode, template_id, sample_storage_path)

        # PPTX 빌드
        output_path = Path(tempfile.gettempdir()) / proposal_id / "presentation.pptx"
        project_name = rfp_data.project_name if rfp_data else ""
        build_presentation_pptx(slides_json, output_path, project_name, template_path)

        # Supabase Storage 업로드
        pptx_url = await _upload_presentation(proposal_id, str(output_path))

        # 세션 업데이트
        session_manager.update_session(proposal_id, {
            "presentation_status": "done",
            "presentation_pptx_path": str(output_path),
            "presentation_pptx_url": pptx_url,
            "presentation_eval_coverage": slides_json.get("eval_coverage", {}),
            "presentation_template_mode": template_mode,
            "presentation_template_id": template_id,
        })
        logger.info(f"발표 자료 생성 완료: {proposal_id} ({slides_json.get('total_slides', '?')}장)")

    except Exception as e:
        logger.error(f"발표 자료 생성 실패: {proposal_id} — {e}")
        try:
            session_manager.update_session(proposal_id, {
                "presentation_status": "error",
                "presentation_error": str(e)[:500],
            })
        except Exception:
            pass


# ── 엔드포인트 ────────────────────────────────────────────────────────────────

@router.get("/presentation/templates")
async def list_presentation_templates(
    current_user=Depends(get_current_user),
):
    """표준 발표 자료 템플릿 목록 조회"""
    templates_with_availability = []
    for t in _STANDARD_TEMPLATES:
        path = _TEMPLATES_DIR / f"{t['id']}.pptx"
        templates_with_availability.append({**t, "available": path.exists()})
    return {"templates": templates_with_availability}


@router.post("/proposals/{proposal_id}/presentation")
async def generate_presentation(
    proposal_id: str,
    background_tasks: BackgroundTasks,
    template_mode: str = "standard",
    template_id: str = "government_blue",
    sample_storage_path: Optional[str] = None,
    current_user=Depends(get_current_user),
):
    """발표 자료 PPTX 생성 요청 (백그라운드 실행)"""
    try:
        session = await session_manager.aget_session(proposal_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="제안서를 찾을 수 없습니다")

    if session.get("phases_completed", 0) < 5:
        raise HTTPException(status_code=400, detail="제안서 생성이 완료되지 않았습니다")

    if session.get("presentation_status") == "processing":
        raise HTTPException(status_code=409, detail="발표 자료를 생성 중입니다")

    # standard 모드 유효성 검증
    if template_mode == "standard":
        valid_ids = {t["id"] for t in _STANDARD_TEMPLATES}
        if template_id not in valid_ids:
            raise HTTPException(
                status_code=400,
                detail=f"존재하지 않는 템플릿입니다: {template_id}. 사용 가능: {sorted(valid_ids)}",
            )

    # sample 모드 유효성 검증
    if template_mode == "sample" and not sample_storage_path:
        raise HTTPException(
            status_code=400,
            detail="sample 모드에는 sample_storage_path가 필요합니다",
        )

    session_manager.update_session(proposal_id, {"presentation_status": "processing"})

    background_tasks.add_task(
        _run_presentation,
        proposal_id,
        template_mode,
        template_id,
        sample_storage_path,
    )

    return {
        "proposal_id": proposal_id,
        "status": "processing",
        "template_mode": template_mode,
        "template_id": template_id,
        "message": "발표 자료 생성을 시작합니다",
    }


@router.get("/proposals/{proposal_id}/presentation/status")
async def get_presentation_status(
    proposal_id: str,
    current_user=Depends(get_current_user),
):
    """발표 자료 생성 진행 상태 조회"""
    try:
        session = await session_manager.aget_session(proposal_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="제안서를 찾을 수 없습니다")

    return {
        "proposal_id": proposal_id,
        "status": session.get("presentation_status", "idle"),
        "pptx_url": session.get("presentation_pptx_url", ""),
        "eval_coverage": session.get("presentation_eval_coverage", {}),
        "template_mode": session.get("presentation_template_mode", ""),
        "template_id": session.get("presentation_template_id", ""),
        "error": session.get("presentation_error", ""),
    }


@router.get("/proposals/{proposal_id}/presentation/download")
async def download_presentation(
    proposal_id: str,
    current_user=Depends(get_current_user),
):
    """생성된 발표 자료 PPTX 파일 다운로드"""
    try:
        session = await session_manager.aget_session(proposal_id)
    except SessionNotFoundError:
        raise HTTPException(status_code=404, detail="제안서를 찾을 수 없습니다")

    pptx_path = session.get("presentation_pptx_path", "")
    if not pptx_path or not Path(pptx_path).exists():
        raise HTTPException(status_code=404, detail="발표 자료가 아직 생성되지 않았습니다")

    rfp_title = session.get("rfp_title", "presentation")
    safe_name = "".join(c for c in rfp_title if c.isalnum() or c in " _-")[:50]
    filename = f"{safe_name}_발표자료.pptx"

    return FileResponse(
        path=pptx_path,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=filename,
    )
