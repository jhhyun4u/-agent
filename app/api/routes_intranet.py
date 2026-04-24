"""인트라넷 KB 마이그레이션 API.

마이그레이션 스크립트 및 프론트엔드에서 호출하는 엔드포인트.
동기화 로그 추적 API 포함 (매월 자동 동기화 지원).
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, Query, UploadFile

from app.api.deps import get_current_user, require_role
from app.config import settings
from app.exceptions import InvalidRequestError, ResourceNotFoundError
from app.services.domains.proposal.document_ingestion import (
    compute_file_hash,
    import_project,
    process_document,
)
from app.utils.file_utils import validate_upload
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/kb/intranet", tags=["인트라넷 KB"])


# ── 프로젝트 임포트 (마이그레이션 스크립트용) ──


@router.post("/import-project")
async def import_project_endpoint(
    body: dict,
    upsert: bool = Query(False, description="True면 기존 레코드 업데이트 (증분 동기화)"),
    user=Depends(require_role("admin")),
):
    """인트라넷 프로젝트 메타데이터 임포트 + KB 자동 시드."""
    if not body.get("project_name"):
        raise InvalidRequestError("project_name은 필수입니다.")
    if "legacy_idx" not in body:
        raise InvalidRequestError("legacy_idx는 필수입니다.")

    result = await import_project(user.org_id, body, upsert=upsert)
    return result


# ── 파일 업로드 (마이그레이션 스크립트용) ──


@router.post("/upload-file")
async def upload_file_endpoint(
    project_id: str = Query(...),
    file_slot: str = Query(...),
    doc_type: str = Query(...),
    doc_subtype: str = Query(""),
    file: UploadFile = ...,
    background_tasks: BackgroundTasks = BackgroundTasks(),
    user=Depends(require_role("lead", "admin")),
):
    """인트라넷 문서 파일 업로드 + 비동기 처리 시작."""
    client = await get_async_client()

    # 프로젝트 존재 확인
    proj = await (
        client.table("intranet_projects")
        .select("id, org_id")
        .eq("id", project_id)
        .eq("org_id", user.org_id)
        .execute()
    )
    if not proj.data:
        raise ResourceNotFoundError("프로젝트를 찾을 수 없습니다.")

    # 파일 검증
    content = await file.read()
    safe_name, ext = validate_upload(
        file.filename, content, "intranet_doc",
        max_mb=getattr(settings, "intranet_max_file_size_mb", 100),
    )

    # 중복 체크
    file_hash = compute_file_hash(content)
    existing = await (
        client.table("intranet_documents")
        .select("id")
        .eq("project_id", project_id)
        .eq("file_slot", file_slot)
        .execute()
    )
    if existing.data:
        return {"id": existing.data[0]["id"], "action": "skipped", "reason": "slot_exists"}

    # Supabase Storage 업로드
    bucket = getattr(settings, "storage_bucket_intranet", "intranet-documents")
    storage_path = f"{user.org_id}/{project_id}/{file_slot}_{safe_name}"

    try:
        await client.storage.from_(bucket).upload(storage_path, content)
    except Exception as e:
        logger.warning(f"스토리지 업로드 실패 (계속 진행): {e}")
        storage_path = None

    # DB 레코드 생성
    doc_row = {
        "project_id": project_id,
        "org_id": user.org_id,
        "file_slot": file_slot,
        "doc_type": doc_type,
        "doc_subtype": doc_subtype or None,
        "filename": safe_name,
        "file_type": ext,
        "file_size": len(content),
        "storage_path": storage_path,
        "source_hash": file_hash,
        "processing_status": "pending",
    }
    result = await client.table("intranet_documents").insert(doc_row).execute()
    doc_id = result.data[0]["id"]

    # 프로젝트 파일 카운트 업데이트
    count_result = await (
        client.table("intranet_documents")
        .select("id", count="exact")
        .eq("project_id", project_id)
        .execute()
    )
    await (
        client.table("intranet_projects")
        .update({"file_count": count_result.count or 0, "migration_status": "files_uploading"})
        .eq("id", project_id)
        .execute()
    )

    # 비동기 처리 시작
    background_tasks.add_task(process_document, doc_id, user.org_id)

    return {"id": doc_id, "action": "created", "processing": "started"}


# ── 조회 API (프론트엔드용) ──


@router.get("/projects")
async def list_projects(
    status: str | None = None,
    client_name: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user=Depends(get_current_user),
):
    """임포트된 인트라넷 프로젝트 목록."""
    client = await get_async_client()
    query = (
        client.table("intranet_projects")
        .select("id, project_name, client_name, department, budget_krw, keywords, "
                "start_date, end_date, status, team, migration_status, file_count, created_at",
                count="exact")
        .eq("org_id", user.org_id)
        .order("created_at", desc=True)
    )

    if status:
        query = query.eq("status", status)
    if client_name:
        query = query.ilike("client_name", f"%{client_name}%")

    offset = (page - 1) * page_size
    query = query.range(offset, offset + page_size - 1)
    result = await query.execute()

    return {"data": result.data or [], "count": result.count or 0, "page": page}


@router.get("/projects/{project_id}")
async def get_project_detail(
    project_id: str,
    user=Depends(get_current_user),
):
    """프로젝트 상세 + 문서 목록."""
    client = await get_async_client()

    proj = await (
        client.table("intranet_projects")
        .select("*")
        .eq("id", project_id)
        .eq("org_id", user.org_id)
        .single()
        .execute()
    )
    if not proj.data:
        raise ResourceNotFoundError("프로젝트를 찾을 수 없습니다.")

    docs = await (
        client.table("intranet_documents")
        .select("id, file_slot, doc_type, doc_subtype, filename, file_type, "
                "file_size, processing_status, chunk_count, total_chars, error_message, created_at")
        .eq("project_id", project_id)
        .order("file_slot")
        .execute()
    )

    return {"project": proj.data, "documents": docs.data or []}


@router.get("/documents/{document_id}")
async def get_document_detail(
    document_id: str,
    user=Depends(get_current_user),
):
    """문서 상세 + 청크 목록."""
    client = await get_async_client()

    doc = await (
        client.table("intranet_documents")
        .select("*")
        .eq("id", document_id)
        .eq("org_id", user.org_id)
        .single()
        .execute()
    )
    if not doc.data:
        raise ResourceNotFoundError("문서를 찾을 수 없습니다.")

    chunks = await (
        client.table("document_chunks")
        .select("id, chunk_index, chunk_type, section_title, char_count")
        .eq("document_id", document_id)
        .order("chunk_index")
        .execute()
    )

    return {"document": doc.data, "chunks": chunks.data or []}


@router.post("/documents/{document_id}/reprocess")
async def reprocess_document(
    document_id: str,
    background_tasks: BackgroundTasks,
    user=Depends(require_role("lead", "admin")),
):
    """문서 재추출 + 재청킹 + 재임베딩."""
    client = await get_async_client()

    doc = await (
        client.table("intranet_documents")
        .select("id, org_id")
        .eq("id", document_id)
        .eq("org_id", user.org_id)
        .single()
        .execute()
    )
    if not doc.data:
        raise ResourceNotFoundError("문서를 찾을 수 없습니다.")

    # 텍스트 초기화 → 재추출 유도
    await (
        client.table("intranet_documents")
        .update({"extracted_text": None, "processing_status": "pending"})
        .eq("id", document_id)
        .execute()
    )

    background_tasks.add_task(process_document, document_id, user.org_id)
    return {"status": "reprocessing"}


@router.get("/stats")
async def get_migration_stats(user=Depends(get_current_user)):
    """마이그레이션 통계."""
    client = await get_async_client()
    org_id = user.org_id

    projects = await (
        client.table("intranet_projects")
        .select("status, migration_status", count="exact")
        .eq("org_id", org_id)
        .execute()
    )

    docs = await (
        client.table("intranet_documents")
        .select("doc_type, processing_status", count="exact")
        .eq("org_id", org_id)
        .execute()
    )

    chunks = await (
        client.table("document_chunks")
        .select("id", count="exact")
        .eq("org_id", org_id)
        .execute()
    )

    # 집계
    project_by_status: dict[str, int] = {}
    for p in projects.data or []:
        s = p.get("status") or "unknown"
        project_by_status[s] = project_by_status.get(s, 0) + 1

    doc_by_type: dict[str, int] = {}
    doc_by_processing: dict[str, int] = {}
    for d in docs.data or []:
        dt = d.get("doc_type") or "other"
        doc_by_type[dt] = doc_by_type.get(dt, 0) + 1
        ps = d.get("processing_status") or "unknown"
        doc_by_processing[ps] = doc_by_processing.get(ps, 0) + 1

    return {
        "total_projects": projects.count or 0,
        "total_documents": docs.count or 0,
        "total_chunks": chunks.count or 0,
        "projects_by_status": project_by_status,
        "documents_by_type": doc_by_type,
        "documents_by_processing": doc_by_processing,
    }


# ── 동기화 로그 API (매월 자동 동기화 추적) ──


@router.post("/sync/start")
async def sync_start(
    body: dict,
    user=Depends(require_role("admin")),
):
    """동기화 시작 기록. 사내 PC 마이그레이션 스크립트가 호출."""
    client = await get_async_client()

    row = {
        "org_id": user.org_id,
        "sync_type": body.get("sync_type", "incremental"),
        "status": "running",
        "source_host": body.get("source_host", ""),
        "triggered_by": body.get("triggered_by", "scheduler"),
    }
    result = await client.table("intranet_sync_log").insert(row).execute()
    sync_id = result.data[0]["id"]

    logger.info(f"인트라넷 동기화 시작: {sync_id} (type={row['sync_type']}, by={row['triggered_by']})")
    return {"sync_id": sync_id, "status": "running"}


@router.post("/sync/{sync_id}/complete")
async def sync_complete(
    sync_id: str,
    body: dict,
    user=Depends(require_role("admin")),
):
    """동기화 완료/실패 기록. 사내 PC 마이그레이션 스크립트가 호출."""
    client = await get_async_client()

    # 소속 조직 검증
    existing = await (
        client.table("intranet_sync_log")
        .select("id")
        .eq("id", sync_id)
        .eq("org_id", user.org_id)
        .execute()
    )
    if not existing.data:
        raise ResourceNotFoundError("동기화 로그를 찾을 수 없습니다.")

    update = {
        "status": body.get("status", "completed"),
        "projects_found": body.get("projects_found", 0),
        "projects_created": body.get("projects_created", 0),
        "projects_updated": body.get("projects_updated", 0),
        "projects_skipped": body.get("projects_skipped", 0),
        "files_uploaded": body.get("files_uploaded", 0),
        "files_failed": body.get("files_failed", 0),
        "error_message": body.get("error_message"),
        "completed_at": datetime.now(timezone.utc).isoformat(),
    }
    await client.table("intranet_sync_log").update(update).eq("id", sync_id).execute()

    logger.info(
        f"인트라넷 동기화 완료: {sync_id} "
        f"(created={update['projects_created']}, updated={update['projects_updated']})"
    )
    return {"sync_id": sync_id, **update}


@router.get("/sync/status")
async def sync_status(user=Depends(get_current_user)):
    """최근 동기화 상태 조회. 프론트엔드 대시보드용."""
    client = await get_async_client()

    # 최근 5건 이력
    logs = await (
        client.table("intranet_sync_log")
        .select("*")
        .eq("org_id", user.org_id)
        .order("started_at", desc=True)
        .limit(5)
        .execute()
    )

    # 이번 달 동기화 여부
    now = datetime.now(timezone.utc)
    month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    this_month = await (
        client.table("intranet_sync_log")
        .select("id", count="exact")
        .eq("org_id", user.org_id)
        .eq("status", "completed")
        .gte("started_at", month_start.isoformat())
        .execute()
    )

    last_completed = None
    for log in logs.data or []:
        if log.get("status") == "completed":
            last_completed = log.get("completed_at") or log.get("started_at")
            break

    return {
        "synced_this_month": (this_month.count or 0) > 0,
        "last_completed": last_completed,
        "recent_logs": logs.data or [],
    }
