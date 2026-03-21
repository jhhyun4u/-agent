"""
제출서류 관리 API + 조직 공통 서류 API

제안서별 제출서류:
  GET    /api/proposals/{id}/submission-docs
  POST   /api/proposals/{id}/submission-docs/extract
  POST   /api/proposals/{id}/submission-docs
  PUT    /api/proposals/{id}/submission-docs/{doc_id}
  DELETE /api/proposals/{id}/submission-docs/{doc_id}
  POST   /api/proposals/{id}/submission-docs/{doc_id}/upload
  POST   /api/proposals/{id}/submission-docs/{doc_id}/verify
  GET    /api/proposals/{id}/submission-docs/readiness

조직 공통 서류:
  GET    /api/org/{org_id}/document-templates
  POST   /api/org/{org_id}/document-templates
  DELETE /api/org/{org_id}/document-templates/{id}
"""

import logging

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.api.deps import get_current_user, require_project_access, require_role
from app.models.stream_schemas import (
    OrgDocTemplateCreate,
    OrgDocTemplateResponse,
    ReadinessResponse,
    SubmissionDocCreate,
    SubmissionDocResponse,
    SubmissionDocUpdate,
)

router = APIRouter(tags=["submission-docs"])
logger = logging.getLogger(__name__)


# ── 제안서별 제출서류 ──

@router.get(
    "/api/proposals/{proposal_id}/submission-docs",
    response_model=list[SubmissionDocResponse],
)
async def list_submission_docs(
    proposal_id: str,
    user=Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """제출서류 체크리스트 조회."""
    from app.services.submission_docs_service import get_checklist

    return await get_checklist(proposal_id)


@router.post(
    "/api/proposals/{proposal_id}/submission-docs/extract",
    response_model=list[SubmissionDocResponse],
)
async def extract_submission_docs(
    proposal_id: str,
    user=Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """AI로 RFP에서 제출서류 목록 추출."""
    from app.services.submission_docs_service import extract_checklist_from_rfp
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()

    # RFP 원문 + 분석 결과 가져오기
    prop = await (
        client.table("proposals")
        .select("rfp_raw_text")
        .eq("id", proposal_id)
        .single()
        .execute()
    )
    rfp_text = (prop.data or {}).get("rfp_raw_text", "")
    if not rfp_text:
        raise HTTPException(status_code=400, detail="RFP 원문이 없습니다. RFP 분석을 먼저 실행하세요.")

    # 분석 결과 (artifacts)
    art = await (
        client.table("artifacts")
        .select("content")
        .eq("proposal_id", proposal_id)
        .eq("step", "rfp_analyze")
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    rfp_analysis = {}
    if art.data:
        import json
        content = art.data[0].get("content", "")
        if isinstance(content, str):
            try:
                rfp_analysis = json.loads(content)
            except (json.JSONDecodeError, TypeError):
                pass
        elif isinstance(content, dict):
            rfp_analysis = content

    return await extract_checklist_from_rfp(proposal_id, rfp_text, rfp_analysis)


@router.post(
    "/api/proposals/{proposal_id}/submission-docs",
    response_model=SubmissionDocResponse,
)
async def add_submission_doc(
    proposal_id: str,
    body: SubmissionDocCreate,
    user=Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """수동 서류 추가."""
    from app.services.submission_docs_service import add_document

    return await add_document(proposal_id, body.model_dump(exclude_none=True))


@router.put(
    "/api/proposals/{proposal_id}/submission-docs/{doc_id}",
    response_model=SubmissionDocResponse,
)
async def update_submission_doc(
    proposal_id: str,
    doc_id: str,
    body: SubmissionDocUpdate,
    user=Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """상태/담당 변경."""
    from app.services.submission_docs_service import update_document_status

    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="변경할 필드가 없습니다.")
    return await update_document_status(doc_id, data, proposal_id=proposal_id)


@router.delete("/api/proposals/{proposal_id}/submission-docs/{doc_id}")
async def delete_submission_doc(
    proposal_id: str,
    doc_id: str,
    user=Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """서류 삭제."""
    from app.services.submission_docs_service import delete_document

    deleted = await delete_document(doc_id, proposal_id=proposal_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="서류를 찾을 수 없습니다.")
    return {"deleted": True}


_MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB
_ALLOWED_EXTENSIONS = frozenset({
    "pdf", "hwp", "hwpx", "doc", "docx", "xls", "xlsx",
    "ppt", "pptx", "jpg", "jpeg", "png", "zip", "txt",
})


@router.post("/api/proposals/{proposal_id}/submission-docs/{doc_id}/upload")
async def upload_submission_doc(
    proposal_id: str,
    doc_id: str,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """파일 업로드 — Supabase Storage (크기/이름/타입 검증 포함)."""
    import os
    from app.services.submission_docs_service import upload_document
    from app.utils.supabase_client import get_async_client

    # 파일명 보안: 경로 탐색 방지 + sanitize
    raw_name = file.filename or "upload"
    safe_name = os.path.basename(raw_name).strip()
    if not safe_name or safe_name.startswith("."):
        raise HTTPException(status_code=400, detail="잘못된 파일명입니다.")

    # 확장자 검증
    ext = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"허용되지 않는 파일 형식입니다: .{ext}. 허용: {', '.join(sorted(_ALLOWED_EXTENSIONS))}",
        )

    # 크기 제한 (스트리밍 읽기)
    file_bytes = await file.read()
    if len(file_bytes) > _MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"파일 크기가 제한(50MB)을 초과합니다: {len(file_bytes) / 1024 / 1024:.1f}MB",
        )

    client = await get_async_client()
    storage_path = f"submission-docs/{proposal_id}/{doc_id}/{safe_name}"

    try:
        await client.storage.from_("proposal-files").upload(
            storage_path, file_bytes,
            {"content-type": file.content_type or "application/octet-stream"},
        )
    except Exception:
        await client.storage.from_("proposal-files").update(
            storage_path, file_bytes,
            {"content-type": file.content_type or "application/octet-stream"},
        )

    result = await upload_document(
        doc_id=doc_id,
        file_path=storage_path,
        file_name=safe_name,
        file_size=len(file_bytes),
        file_format=ext.upper(),
        user_id=user["id"],
        proposal_id=proposal_id,
    )
    return result


@router.post("/api/proposals/{proposal_id}/submission-docs/{doc_id}/verify")
async def verify_submission_doc(
    proposal_id: str,
    doc_id: str,
    user=Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """검증 완료."""
    from app.services.submission_docs_service import verify_document

    return await verify_document(doc_id, user["id"], proposal_id=proposal_id)


@router.get(
    "/api/proposals/{proposal_id}/submission-docs/readiness",
    response_model=ReadinessResponse,
)
async def check_readiness(
    proposal_id: str,
    user=Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """사전 제출 점검."""
    from app.services.submission_docs_service import check_documents_ready

    return await check_documents_ready(proposal_id)


# ── 조직 공통 서류 ──

@router.get(
    "/api/org/{org_id}/document-templates",
    response_model=list[OrgDocTemplateResponse],
)
async def list_org_templates(
    org_id: str,
    user=Depends(get_current_user),
):
    """조직 공통 서류 목록."""
    from app.services.submission_docs_service import get_org_templates

    return await get_org_templates(org_id)


@router.post(
    "/api/org/{org_id}/document-templates",
    response_model=OrgDocTemplateResponse,
)
async def upsert_org_template(
    org_id: str,
    body: OrgDocTemplateCreate,
    user=Depends(get_current_user),
    _role=Depends(require_role("lead", "director", "executive", "admin")),
):
    """공통 서류 등록/갱신."""
    from app.services.submission_docs_service import upsert_org_template

    return await upsert_org_template(org_id, body.model_dump(exclude_none=True), user["id"])


@router.delete("/api/org/{org_id}/document-templates/{template_id}")
async def delete_org_template(
    org_id: str,
    template_id: str,
    user=Depends(get_current_user),
    _role=Depends(require_role("lead", "director", "executive", "admin")),
):
    """공통 서류 삭제."""
    from app.services.submission_docs_service import delete_org_template

    deleted = await delete_org_template(template_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="템플릿을 찾을 수 없습니다.")
    return {"deleted": True}
