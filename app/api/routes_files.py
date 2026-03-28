"""
프로젝트 파일 관리 API (GAP-2 + GAP-6)

POST   /api/proposals/{id}/files              — 참고자료 업로드
GET    /api/proposals/{id}/files              — 프로젝트 파일 목록 (category 필터)
DELETE /api/proposals/{id}/files/{file_id}    — 파일 삭제 (업로더/소유자만)
GET    /api/proposals/{id}/files/{file_id}/url — 서명 URL 다운로드 (1시간)
"""

import logging
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from app.api.deps import get_current_user
from app.api.response import ok, ok_list
from app.models.auth_schemas import CurrentUser
from app.exceptions import (
    FileNotFoundError_,
    FileUploadError,
    OwnershipRequiredError,
    PropNotFoundError,
)
from app.config import settings
from app.utils.file_utils import UPLOAD_ALLOWED_EXTENSIONS, validate_upload
from app.middleware.rate_limit import limiter
from app.utils.supabase_client import get_async_client

# 전체 카테고리 통합 허용 확장자 (테스트·문서용)
ALLOWED_EXTENSIONS: frozenset[str] = frozenset().union(*UPLOAD_ALLOWED_EXTENSIONS.values())

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/proposals", tags=["files"])

BUCKET = settings.storage_bucket_proposals


@router.post("/{proposal_id}/files", status_code=201)
@limiter.limit("10/minute")
async def upload_project_file(
    request: Request,
    proposal_id: str,
    file: UploadFile = File(...),
    description: str = Form(""),
    user: CurrentUser = Depends(get_current_user),
):
    """프로젝트 참고자료 업로드."""
    client = await get_async_client()

    # 프로젝트 존재 + 접근 권한 확인
    prop = await client.table("proposals").select("id, owner_id, team_id").eq("id", proposal_id).maybe_single().execute()
    if not prop.data:
        raise PropNotFoundError(proposal_id)

    # 파일 읽기 + 통합 검증 (파일명 살균 + 확장자 + 크기)
    content = await file.read()
    filename, ext = validate_upload(file.filename, content, "project_file")

    file_id = str(uuid4())
    storage_path = f"{proposal_id}/references/{file_id}.{ext}"

    # Storage 업로드
    try:
        await client.storage.from_(BUCKET).upload(
            path=storage_path,
            file=content,
            file_options={"content-type": file.content_type or "application/octet-stream", "upsert": "true"},
        )
    except Exception as e:
        logger.error(f"파일 업로드 실패: {e}")
        raise FileUploadError("파일 저장소 업로드 실패: 잠시 후 다시 시도해주세요")

    # DB 기록
    await client.table("proposal_files").insert({
        "id": file_id,
        "proposal_id": proposal_id,
        "category": "reference",
        "filename": filename,
        "storage_path": storage_path,
        "file_type": ext,
        "file_size": len(content),
        "uploaded_by": user.id,
        "description": description or None,
    }).execute()

    return ok({"file_id": file_id, "filename": filename, "storage_path": storage_path})


@router.get("/{proposal_id}/files")
async def list_project_files(
    proposal_id: str,
    category: str | None = None,
    user: CurrentUser = Depends(get_current_user),
):
    """프로젝트 파일 목록 (category 필터 지원)."""
    client = await get_async_client()

    query = client.table("proposal_files").select(
        "id, proposal_id, category, filename, storage_path, file_type, file_size, uploaded_by, description, created_at"
    ).eq("proposal_id", proposal_id).order("created_at", desc=True)

    if category:
        query = query.eq("category", category)

    result = await query.execute()
    items = result.data or []
    return ok_list(items, total=len(items))


@router.delete("/{proposal_id}/files/{file_id}", status_code=204)
async def delete_project_file(
    proposal_id: str,
    file_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """파일 삭제 (업로더 또는 프로젝트 소유자만)."""
    client = await get_async_client()

    # 파일 조회
    file_res = await client.table("proposal_files").select(
        "id, storage_path, uploaded_by, category"
    ).eq("id", file_id).eq("proposal_id", proposal_id).maybe_single().execute()

    if not file_res.data:
        raise FileNotFoundError_()

    file_row = file_res.data

    # RFP 원본은 삭제 불가
    if file_row["category"] == "rfp":
        raise OwnershipRequiredError("RFP 원본 파일은 삭제할 수 없습니다")

    # 권한: 업로더 또는 프로젝트 소유자
    prop = await client.table("proposals").select("owner_id").eq("id", proposal_id).maybe_single().execute()
    user_id = user.id
    if file_row["uploaded_by"] != user_id and (prop.data or {}).get("owner_id") != user_id:
        raise OwnershipRequiredError("삭제 권한이 없습니다")

    # Storage 삭제 (best-effort)
    try:
        await client.storage.from_(BUCKET).remove([file_row["storage_path"]])
    except Exception as e:
        logger.warning(f"Storage 파일 삭제 실패 (무시): {e}")

    # DB 삭제
    await client.table("proposal_files").delete().eq("id", file_id).execute()


@router.get("/{proposal_id}/files/bundle")
async def download_files_bundle(
    proposal_id: str,
    category: str | None = None,
    user: CurrentUser = Depends(get_current_user),
):
    """참고자료 일괄 ZIP 다운로드 (#10, GAP-4 StreamingResponse)."""
    import io
    import zipfile
    from collections.abc import AsyncGenerator

    from fastapi.responses import StreamingResponse

    client = await get_async_client()

    query = client.table("proposal_files").select(
        "filename, storage_path, file_size"
    ).eq("proposal_id", proposal_id)
    if category:
        query = query.eq("category", category)
    result = await query.execute()
    file_rows = result.data or []

    if not file_rows:
        raise FileNotFoundError_("다운로드할 파일이 없습니다")

    async def generate_zip() -> AsyncGenerator[bytes, None]:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for row in file_rows:
                try:
                    data = await client.storage.from_(BUCKET).download(row["storage_path"])
                    zf.writestr(row["filename"], data)
                except Exception as e:
                    logger.warning(f"번들 다운로드 중 파일 스킵: {row['filename']} ({e})")
        yield buf.getvalue()

    return StreamingResponse(
        generate_zip(),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="files_{proposal_id[:8]}.zip"'},
    )


@router.get("/{proposal_id}/files/{file_id}/url")
async def get_file_download_url(
    proposal_id: str,
    file_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """서명 URL 다운로드 (1시간 유효)."""
    client = await get_async_client()

    file_res = await client.table("proposal_files").select(
        "storage_path, filename"
    ).eq("id", file_id).eq("proposal_id", proposal_id).maybe_single().execute()

    if not file_res.data:
        raise FileNotFoundError_()

    signed = await client.storage.from_(BUCKET).create_signed_url(
        file_res.data["storage_path"], expires_in=settings.signed_url_expiry_seconds
    )

    return ok({
        "url": signed.get("signedURL") or signed.get("signedUrl") or signed.get("data", {}).get("signedUrl", ""),
        "filename": file_res.data["filename"],
        "expires_in": settings.signed_url_expiry_seconds,
    })
