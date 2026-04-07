"""
스트림 오케스트레이션 API

GET  /api/proposals/{id}/streams              — 3개 스트림 통합 상태
GET  /api/proposals/{id}/streams/{stream}     — 단일 스트림 상세
POST /api/proposals/{id}/streams/final-submit — 최종 제출 게이트
"""

import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user, require_project_access, require_role
from app.models.stream_schemas import (
    FinalSubmitRequest,
    FinalSubmitResponse,
    StreamProgressResponse,
)

router = APIRouter(prefix="/api/proposals", tags=["streams"])
logger = logging.getLogger(__name__)


@router.get("/{proposal_id}/streams")
async def get_streams(
    proposal_id: str,
    user=Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """3개 스트림 통합 상태 조회."""
    from app.services.stream_orchestrator import get_streams_status

    return await get_streams_status(proposal_id)


@router.get("/{proposal_id}/streams/{stream}")
async def get_single_stream(
    proposal_id: str,
    stream: str,
    user=Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """단일 스트림 상세 조회."""
    from app.services.stream_orchestrator import get_streams_status

    result = await get_streams_status(proposal_id)
    for s in result["streams"]:
        if s["stream"] == stream:
            return s

    return StreamProgressResponse(
        stream=stream,
        status="not_started",
        progress_pct=0,
    )


@router.post("/{proposal_id}/streams/final-submit")
async def final_submit(
    proposal_id: str,
    body: FinalSubmitRequest,
    user=Depends(get_current_user),
    _access=Depends(require_project_access),
    _role=Depends(require_role("lead", "director", "executive", "admin")),
):
    """최종 제출 게이트 — 3개 스트림 모두 completed + lead 이상."""
    from app.services.stream_orchestrator import mark_final_submission

    result = await mark_final_submission(proposal_id, user.id)
    return FinalSubmitResponse(**result)
