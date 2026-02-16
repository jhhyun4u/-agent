"""레거시 API 엔드포인트 (v2.0 호환성)"""

import logging
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile

from app.models.schemas import ProjectInput
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["legacy"])

OUTPUT_DIR = Path(settings.output_dir)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/proposals/from-rfp")
async def create_proposal_from_rfp(file: UploadFile):
    """RFP 파일 업로드 기반 제안서 생성 (레거시)"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="파일이 필요합니다.")

    suffix = Path(file.filename).suffix.lower()
    if suffix not in (".pdf", ".docx"):
        raise HTTPException(
            status_code=400, detail=f"지원하지 않는 파일 형식입니다: {suffix}"
        )

    proposal_id = str(uuid.uuid4())[:8]
    temp_path = OUTPUT_DIR / f"temp_{proposal_id}{suffix}"

    try:
        with open(temp_path, "wb") as f:
            f.write(await file.read())

        # v3.0으로 리다이렉트
        return {
            "proposal_id": proposal_id,
            "message": "v3.0 엔드포인트를 사용해주세요.",
            "legacy_notice": "이 엔드포인트는 더 이상 지원되지 않습니다.",
            "new_endpoint": "/api/v3/proposals/start",
        }

    finally:
        temp_path.unlink(missing_ok=True)


@router.post("/proposals/from-input")
async def create_proposal_from_input(project: ProjectInput):
    """직접 입력 기반 제안서 생성 (레거시)"""
    return {
        "message": "v3.0 엔드포인트를 사용해주세요.",
        "legacy_notice": "이 엔드포인트는 더 이상 지원되지 않습니다.",
        "new_endpoint": "/api/v3/proposals/start",
    }


@router.get("/proposals/{proposal_id}/download")
async def download_proposal(proposal_id: str, format: str = "docx"):
    """생성된 제안서 다운로드 (레거시)"""
    raise HTTPException(
        status_code=410,
        detail="이 엔드포인트는 더 이상 지원되지 않습니다. v3.0 엔드포인트를 사용해주세요."
    )
