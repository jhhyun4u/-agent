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
from app.exceptions import PropNotFoundError
from app.middleware.rate_limit import limiter
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/proposals", tags=["files"])

ALLOWED_EXTENSIONS = {"pdf", "docx", "hwp", "hwpx", "xlsx", "pptx", "png", "jpg", "jpeg"}
BUCKET = "proposal-files"


@router.post("/{proposal_id}/files", status_code=201)
@limiter.limit("10/minute")
async def upload_project_file(
    request: Request,
    proposal_id: str,
    file: UploadFile = File(...),
    description: str = Form(""),
    user=Depends(get_current_user),
):
    """프로젝트 참고자료 업로드."""
    client = await get_async_client()

    # 프로젝트 존재 + 접근 권한 확인
    prop = await client.table("proposals").select("id, owner_id, team_id").eq("id", proposal_id).maybe_single().execute()
    if not prop.data:
        raise PropNotFoundError(proposal_id)

    # M-4: 파일명 살균 (path traversal 방지)
    import re
    raw_filename = file.filename or "untitled"
    filename = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '_', raw_filename.replace("..", "").strip())
    if not filename or filename in (".", ".."):
        filename = "untitled"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_EXTENSIONS:
        from fastapi import HTTPException
        raise HTTPException(400, f"허용되지 않는 파일 형식: .{ext} (허용: {', '.join(sorted(ALLOWED_EXTENSIONS))})")

    # H-4: 파일 크기 검증
    from app.config import settings
    content = await file.read()
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        from fastapi import HTTPException
        raise HTTPException(413, f"파일 크기 초과: {len(content) // (1024*1024)}MB (최대 {settings.max_file_size_mb}MB)")

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
        from fastapi import HTTPException
        raise HTTPException(500, "파일 업로드 실패")

    # DB 기록
    await client.table("proposal_files").insert({
        "id": file_id,
        "proposal_id": proposal_id,
        "category": "reference",
        "filename": filename,
        "storage_path": storage_path,
        "file_type": ext,
        "file_size": len(content),
        "uploaded_by": user.get("id"),
        "description": description or None,
    }).execute()

    return {"file_id": file_id, "filename": filename, "storage_path": storage_path}


@router.get("/{proposal_id}/files")
async def list_project_files(
    proposal_id: str,
    category: str | None = None,
    user=Depends(get_current_user),
):
    """프로젝트 파일 목록 (category 필터 지원)."""
    client = await get_async_client()

    query = client.table("proposal_files").select(
        "id, proposal_id, category, filename, storage_path, file_type, file_size, uploaded_by, description, created_at"
    ).eq("proposal_id", proposal_id).order("created_at", desc=True)

    if category:
        query = query.eq("category", category)

    result = await query.execute()
    return {"files": result.data or []}


@router.delete("/{proposal_id}/files/{file_id}", status_code=204)
async def delete_project_file(
    proposal_id: str,
    file_id: str,
    user=Depends(get_current_user),
):
    """파일 삭제 (업로더 또는 프로젝트 소유자만)."""
    client = await get_async_client()

    # 파일 조회
    file_res = await client.table("proposal_files").select(
        "id, storage_path, uploaded_by, category"
    ).eq("id", file_id).eq("proposal_id", proposal_id).maybe_single().execute()

    if not file_res.data:
        from fastapi import HTTPException
        raise HTTPException(404, "파일을 찾을 수 없습니다")

    file_row = file_res.data

    # RFP 원본은 삭제 불가
    if file_row["category"] == "rfp":
        from fastapi import HTTPException
        raise HTTPException(403, "RFP 원본 파일은 삭제할 수 없습니다")

    # 권한: 업로더 또는 프로젝트 소유자
    prop = await client.table("proposals").select("owner_id").eq("id", proposal_id).maybe_single().execute()
    user_id = user.get("id")
    if file_row["uploaded_by"] != user_id and (prop.data or {}).get("owner_id") != user_id:
        from fastapi import HTTPException
        raise HTTPException(403, "삭제 권한이 없습니다")

    # Storage 삭제 (best-effort)
    try:
        await client.storage.from_(BUCKET).remove([file_row["storage_path"]])
    except Exception as e:
        logger.warning(f"Storage 파일 삭제 실패 (무시): {e}")

    # DB 삭제
    await client.table("proposal_files").delete().eq("id", file_id).execute()


@router.get("/{proposal_id}/files/{file_id}/url")
async def get_file_download_url(
    proposal_id: str,
    file_id: str,
    user=Depends(get_current_user),
):
    """서명 URL 다운로드 (1시간 유효)."""
    client = await get_async_client()

    file_res = await client.table("proposal_files").select(
        "storage_path, filename"
    ).eq("id", file_id).eq("proposal_id", proposal_id).maybe_single().execute()

    if not file_res.data:
        from fastapi import HTTPException
        raise HTTPException(404, "파일을 찾을 수 없습니다")

    signed = await client.storage.from_(BUCKET).create_signed_url(
        file_res.data["storage_path"], expires_in=3600
    )

    return {
        "url": signed.get("signedURL") or signed.get("signedUrl") or signed.get("data", {}).get("signedUrl", ""),
        "filename": file_res.data["filename"],
        "expires_in": 3600,
    }
