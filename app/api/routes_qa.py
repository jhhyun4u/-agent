"""
Q&A 기록 CRUD + 검색 API (PSM-16)

POST   /api/proposals/{id}/qa          — Q&A 일괄 등록
GET    /api/proposals/{id}/qa          — 프로젝트별 Q&A 조회
PUT    /api/proposals/{id}/qa/{qa_id}  — 개별 Q&A 수정
DELETE /api/proposals/{id}/qa/{qa_id}  — 개별 Q&A 삭제
GET    /api/kb/qa/search               — 조직 전체 Q&A 검색
"""

import logging

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, require_project_access
from app.models.auth_schemas import CurrentUser
from app.models.schemas import QARecordCreate, QARecordUpdate
from app.services.qa_service import (
    delete_qa_record,
    get_proposal_qa,
    save_qa_records,
    search_qa,
    update_qa_record,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["qa"])


@router.post("/api/proposals/{proposal_id}/qa", status_code=201)
async def create_qa_records(
    proposal_id: str,
    records: list[QARecordCreate],
    user: CurrentUser = Depends(get_current_user),
):
    """Q&A 기록 일괄 등록 + KB 자동 연동."""
    _ = await require_project_access(proposal_id, user)
    qa_dicts = [r.model_dump() for r in records]
    saved = await save_qa_records(proposal_id, qa_dicts, created_by=user.id)
    return {"data": saved, "count": len(saved)}


@router.get("/api/proposals/{proposal_id}/qa")
async def list_qa_records(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """프로젝트별 Q&A 기록 조회."""
    _ = await require_project_access(proposal_id, user)
    records = await get_proposal_qa(proposal_id)
    return {"data": records, "count": len(records)}


@router.put("/api/proposals/{proposal_id}/qa/{qa_id}")
async def update_qa(
    proposal_id: str,
    qa_id: str,
    body: QARecordUpdate,
    user: CurrentUser = Depends(get_current_user),
):
    """개별 Q&A 기록 수정."""
    _ = await require_project_access(proposal_id, user)
    updated = await update_qa_record(qa_id, body.model_dump(exclude_unset=True))
    return {"data": updated}


@router.delete("/api/proposals/{proposal_id}/qa/{qa_id}", status_code=204)
async def remove_qa(
    proposal_id: str,
    qa_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """개별 Q&A 기록 삭제."""
    _ = await require_project_access(proposal_id, user)
    await delete_qa_record(qa_id)


@router.get("/api/kb/qa/search")
async def search_qa_records(
    query: str = Query(..., min_length=1),
    category: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    user: CurrentUser = Depends(get_current_user),
):
    """조직 전체 Q&A 검색 (시맨틱 + 키워드 하이브리드)."""
    org_id = user.org_id
    results = await search_qa(query, org_id, category=category, limit=limit)
    return {"data": results, "count": len(results)}
