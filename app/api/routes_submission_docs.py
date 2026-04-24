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
  POST   /api/proposals/{id}/submission-docs/{doc_id}/confirm-original
  GET    /api/proposals/{id}/submission-docs/bundle
  GET    /api/proposals/{id}/submission-docs/readiness

조직 공통 서류:
  GET    /api/org/{org_id}/document-templates
  POST   /api/org/{org_id}/document-templates
  DELETE /api/org/{org_id}/document-templates/{id}
"""

import logging

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response

from app.api.deps import get_current_user, require_project_access, require_role
from app.api.response import ok, ok_list
from app.config import settings
from app.exceptions import (
    InvalidRequestError,
    ResourceNotFoundError,
)
from app.utils.file_utils import validate_upload
from app.models.auth_schemas import CurrentUser
from app.models.stream_schemas import (
    OrgDocTemplateCreate,
    SubmissionDocCreate,
    SubmissionDocUpdate,
)

router = APIRouter(prefix="/api", tags=["submission-docs"])
logger = logging.getLogger(__name__)


# ── 제안서별 제출서류 ──

@router.get("/proposals/{proposal_id}/submission-docs")
async def list_submission_docs(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """제출서류 체크리스트 조회."""
    from app.services.domains.bidding.submission_docs_service import get_checklist

    items = await get_checklist(proposal_id)
    return ok_list(items, total=len(items))


@router.post("/proposals/{proposal_id}/submission-docs/extract")
async def extract_submission_docs(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """AI로 RFP에서 제출서류 목록 추출."""
    from app.services.domains.bidding.submission_docs_service import extract_checklist_from_rfp
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
        raise InvalidRequestError("RFP 원문이 없습니다. RFP 분석을 먼저 실행하세요.")

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

    items = await extract_checklist_from_rfp(proposal_id, rfp_text, rfp_analysis)
    return ok_list(items, total=len(items))


@router.post("/proposals/{proposal_id}/submission-docs")
async def add_submission_doc(
    proposal_id: str,
    body: SubmissionDocCreate,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """수동 서류 추가."""
    from app.services.domains.bidding.submission_docs_service import add_document

    return ok(await add_document(proposal_id, body.model_dump(exclude_none=True)))


@router.put("/proposals/{proposal_id}/submission-docs/{doc_id}")
async def update_submission_doc(
    proposal_id: str,
    doc_id: str,
    body: SubmissionDocUpdate,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """상태/담당 변경."""
    from app.services.domains.bidding.submission_docs_service import update_document_status

    data = body.model_dump(exclude_none=True)
    if not data:
        raise InvalidRequestError("변경할 필드가 없습니다.")
    return ok(await update_document_status(doc_id, data, proposal_id=proposal_id))


@router.delete("/proposals/{proposal_id}/submission-docs/{doc_id}")
async def delete_submission_doc(
    proposal_id: str,
    doc_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """서류 삭제."""
    from app.services.domains.bidding.submission_docs_service import delete_document

    deleted = await delete_document(doc_id, proposal_id=proposal_id)
    if not deleted:
        raise ResourceNotFoundError("서류")
    return ok(None, message="삭제 완료")


@router.post("/proposals/{proposal_id}/submission-docs/{doc_id}/upload")
async def upload_submission_doc(
    proposal_id: str,
    doc_id: str,
    file: UploadFile = File(...),
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """파일 업로드 — Supabase Storage (크기/이름/타입 검증 포함)."""
    from app.services.domains.bidding.submission_docs_service import upload_document
    from app.utils.supabase_client import get_async_client

    # 통합 검증 (파일명 살균 + 확장자 + 크기 50MB)
    file_bytes = await file.read()
    safe_name, ext = validate_upload(file.filename, file_bytes, "submission", max_mb=50)

    client = await get_async_client()
    storage_path = f"submission-docs/{proposal_id}/{doc_id}/{safe_name}"

    try:
        await client.storage.from_(settings.storage_bucket_proposals).upload(
            storage_path, file_bytes,
            {"content-type": file.content_type or "application/octet-stream"},
        )
    except Exception:
        await client.storage.from_(settings.storage_bucket_proposals).update(
            storage_path, file_bytes,
            {"content-type": file.content_type or "application/octet-stream"},
        )

    result = await upload_document(
        doc_id=doc_id,
        file_path=storage_path,
        file_name=safe_name,
        file_size=len(file_bytes),
        file_format=ext.upper(),
        user_id=user.id,
        proposal_id=proposal_id,
    )
    return ok(result)


@router.post("/proposals/{proposal_id}/submission-docs/{doc_id}/verify")
async def verify_submission_doc(
    proposal_id: str,
    doc_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """검증 완료."""
    from app.services.domains.bidding.submission_docs_service import verify_document

    return ok(await verify_document(doc_id, user.id, proposal_id=proposal_id))


@router.post("/proposals/{proposal_id}/submission-docs/{doc_id}/confirm-original")
async def confirm_original(
    proposal_id: str,
    doc_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """원본 서류 준비 완료 확인 (파일 업로드 없이 verified 처리)."""
    from app.services.domains.bidding.submission_docs_service import confirm_original_document

    try:
        return ok(await confirm_original_document(doc_id, user.id, proposal_id=proposal_id))
    except ValueError as e:
        raise InvalidRequestError(str(e))


@router.get("/proposals/{proposal_id}/submission-docs/bundle")
async def download_copy_bundle(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """사본 서류 묶음 다운로드 (PDF 병합 또는 ZIP)."""
    from app.services.domains.bidding.submission_docs_service import build_copy_bundle

    try:
        data, content_type = await build_copy_bundle(proposal_id)
    except ValueError as e:
        raise InvalidRequestError(str(e))

    ext = "pdf" if "pdf" in content_type else "zip"
    filename = f"submission_copies_{proposal_id[:8]}.{ext}"
    return Response(
        content=data,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/proposals/{proposal_id}/submission-docs/readiness")
async def check_readiness(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    _access=Depends(require_project_access),
):
    """사전 제출 점검."""
    from app.services.domains.bidding.submission_docs_service import check_documents_ready

    return ok(await check_documents_ready(proposal_id))


# ── 조직 공통 서류 ──

@router.get("/org/{org_id}/document-templates")
async def list_org_templates(
    org_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """조직 공통 서류 목록."""
    from app.services.domains.bidding.submission_docs_service import get_org_templates

    items = await get_org_templates(org_id)
    return ok_list(items, total=len(items))


@router.post("/org/{org_id}/document-templates")
async def upsert_org_template(
    org_id: str,
    body: OrgDocTemplateCreate,
    user: CurrentUser = Depends(get_current_user),
    _role=Depends(require_role("lead", "director", "executive", "admin")),
):
    """공통 서류 등록/갱신."""
    from app.services.domains.bidding.submission_docs_service import upsert_org_template

    return ok(await upsert_org_template(org_id, body.model_dump(exclude_none=True), user.id))


@router.delete("/org/{org_id}/document-templates/{template_id}")
async def delete_org_template(
    org_id: str,
    template_id: str,
    user: CurrentUser = Depends(get_current_user),
    _role=Depends(require_role("lead", "director", "executive", "admin")),
):
    """공통 서류 삭제."""
    from app.services.domains.bidding.submission_docs_service import delete_org_template

    deleted = await delete_org_template(template_id)
    if not deleted:
        raise ResourceNotFoundError("템플릿")
    return ok(None, message="삭제 완료")
