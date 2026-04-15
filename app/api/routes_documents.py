"""
문서 수집 및 처리 API (§8)

POST /api/documents/upload                     — 문서 업로드 및 처리 시작
GET  /api/documents                             — 문서 목록 조회 (필터 + 페이지네이션)
GET  /api/documents/{id}                        — 문서 상세 조회
POST /api/documents/{id}/process                — 문서 재처리 (실패한 문서)
GET  /api/documents/{id}/chunks                 — 문서의 청크 목록 조회
DELETE /api/documents/{id}                      — 문서 삭제
"""

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Optional, Literal

from fastapi import APIRouter, Depends, File, UploadFile, Query, Form, HTTPException, status

from app.api.deps import get_current_user
from app.config import settings
from app.models.auth_schemas import CurrentUser
from app.models.document_schemas import (
    DocumentResponse,
    DocumentListResponse,
    DocumentDetailResponse,
    ChunkListResponse,
    DocumentProcessResponse,
)
from app.services.document_ingestion import process_document, process_document_bounded
from app.utils.supabase_client import get_async_client

# 지원하는 파일 형식
SUPPORTED_FORMATS = {
    ".pdf": "application/pdf",
    ".hwp": "application/x-hwp",
    ".hwpx": "application/x-hwpx",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".doc": "application/msword",
}

router = APIRouter(prefix="/api/documents", tags=["documents"])
logger = logging.getLogger(__name__)

# Allowed document types (must match upload validation)
ALLOWED_DOC_TYPES = {"보고서", "제안서", "실적", "기타"}

# Magic bytes (file signature) validation
MAGIC_BYTES = {
    ".pdf": b"%PDF",
    ".docx": b"PK\x03\x04",  # ZIP archive
    ".hwpx": b"PK\x03\x04",  # ZIP archive
    ".pptx": b"PK\x03\x04",  # ZIP archive
    ".hwp": b"\xd0\xcf\x11\xe0",  # OLE2 (HWP is OLE2-based)
}


def validate_file_magic_bytes(file_content: bytes, file_ext: str) -> bool:
    """
    Validate file by magic bytes (file signature) to prevent spoofing.

    Args:
        file_content: File binary content
        file_ext: File extension (lowercase, includes dot)

    Returns:
        True if valid, raises HTTPException if invalid
    """
    if file_ext not in MAGIC_BYTES:
        # No magic bytes check for this format (accept it)
        return True

    expected_magic = MAGIC_BYTES[file_ext]
    if not file_content.startswith(expected_magic):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"파일 형식이 유효하지 않습니다. 파일이 손상되었거나 {file_ext} 파일이 아닙니다.",
        )

    return True


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(..., description="보고서|제안서|실적|기타"),
    doc_subtype: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),
    current_user: CurrentUser = Depends(get_current_user),
) -> DocumentResponse:
    """
    문서 파일 업로드 및 처리 시작

    - 파일을 Supabase Storage에 저장
    - intranet_documents 레코드 생성
    - 백그라운드에서 process_document() 비동기 호출
    - 즉시 응답 (상태는 클라이언트가 주기적으로 조회)
    """
    client = await get_async_client()

    # doc_type 검증
    if doc_type not in ALLOWED_DOC_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"잘못된 문서 타입입니다. 허용 값: {', '.join(ALLOWED_DOC_TYPES)}",
        )

    # 파일 형식 검증
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="파일명이 없습니다",
        )

    _, file_ext = os.path.splitext(file.filename)
    file_ext = file_ext.lower()

    if file_ext not in SUPPORTED_FORMATS:
        supported = ", ".join(SUPPORTED_FORMATS.keys())
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"지원하지 않는 파일 형식입니다. 지원 형식: {supported}",
        )

    try:
        # 파일 읽기 및 크기 검증
        file_content = await file.read()
        logger.debug(f"[{current_user.org_id}] 파일 읽기 완료: {file.filename} ({len(file_content)} bytes)")

        max_size_bytes = settings.intranet_max_file_size_mb * 1024 * 1024
        if len(file_content) > max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"파일이 너무 큽니다 (최대 {settings.intranet_max_file_size_mb}MB)",
            )

        # 매직 바이트 검증 (파일 형식 검증)
        logger.debug(f"[{current_user.org_id}] 매직 바이트 검증 시작: {file_ext}")
        validate_file_magic_bytes(file_content, file_ext)
        logger.debug(f"[{current_user.org_id}] 매직 바이트 검증 완료")

        # Supabase Storage에 저장
        bucket = settings.storage_bucket_intranet
        document_id = str(uuid.uuid4())
        storage_path = f"{current_user.org_id}/{document_id}/{file.filename}"

        logger.debug(f"[{current_user.org_id}] Storage 업로드 시작: {storage_path} (bucket: {bucket})")
        try:
            await client.storage.from_(bucket).upload(
                path=storage_path,
                file=file_content,
                file_options={"upsert": "true"},
            )
            logger.info(f"[{current_user.org_id}] Storage 업로드 완료: {storage_path}")
        except Exception as storage_err:
            logger.error(f"[{current_user.org_id}] Storage 업로드 실패: {storage_err}", exc_info=True)
            raise

        # intranet_documents 레코드 생성
        now = datetime.now(timezone.utc)
        doc_insert_data = {
            "id": document_id,
            "org_id": current_user.org_id,
            "filename": file.filename,
            "file_size_bytes": len(file_content),
            "doc_type": doc_type,
            "storage_path": storage_path,
            "processing_status": "extracting",
            "total_chars": 0,
            "chunk_count": 0,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }

        # Optional fields
        if doc_subtype:
            doc_insert_data["doc_subtype"] = doc_subtype

        # If project_id provided, add it (allows project-based organization)
        if project_id:
            doc_insert_data["project_id"] = project_id

        logger.debug(f"[{current_user.org_id}] DB 삽입 시작: {document_id}")
        try:
            doc_result = await client.table("intranet_documents").insert(doc_insert_data).execute()
            logger.debug(f"[{current_user.org_id}] DB 삽입 완료, 응답: {doc_result}")
        except Exception as db_err:
            logger.error(f"[{current_user.org_id}] DB 삽입 실패: {db_err}", exc_info=True)
            raise

        if not doc_result.data:
            logger.error(f"[{current_user.org_id}] doc_result.data가 비어있음: {doc_result}")
            raise Exception("문서 레코드 생성 실패")

        doc = doc_result.data[0]
        logger.info(f"[{current_user.org_id}] 문서 레코드 생성 완료: {doc['id']}")

        # 백그라운드: 비동기 처리 시작 (동시성 제한 적용)
        logger.debug(f"[{current_user.org_id}] 비동기 처리 태스크 생성 (동시성 제한: 최대 5개)")
        asyncio.create_task(process_document_bounded(document_id, current_user.org_id))

        return DocumentResponse(
            id=doc["id"],
            filename=doc["filename"],
            doc_type=doc["doc_type"],
            storage_path=doc["storage_path"],
            processing_status=doc["processing_status"],
            total_chars=doc["total_chars"],
            chunk_count=doc["chunk_count"],
            error_message=doc.get("error_message"),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
        )

    except HTTPException:
        raise
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        logger.error(f"[{current_user.org_id}] 문서 업로드 실패: {error_msg}", exc_info=True)
        # Return detailed error in dev mode for debugging
        detail = error_msg if settings.dev_mode else "문서 업로드 중 오류가 발생했습니다"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail,
        )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    status_filter: Optional[str] = Query(None, alias="status"),
    doc_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None, description="파일명 검색"),
    sort_by: Optional[Literal["created_at", "updated_at", "filename", "total_chars"]] = Query(
        "updated_at", description="정렬 기준"
    ),
    order: Optional[Literal["asc", "desc"]] = Query("desc", description="정렬 순서"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: CurrentUser = Depends(get_current_user),
) -> DocumentListResponse:
    """
    문서 목록 조회

    쿼리 파라미터:
    - status: extracting, chunking, embedding, completed, failed
    - doc_type: 보고서, 제안서, 실적, 기타
    - search: 파일명 검색 (포함 검색)
    - sort_by: created_at|updated_at|filename|total_chars (기본: updated_at)
    - order: asc|desc (기본: desc)
    - limit: 페이지당 항목 수 (기본 20, 최대 100)
    - offset: 페이지 시작 위치 (기본 0)
    """
    client = await get_async_client()

    try:
        # 검색 input 이스케이프 (한 번만 수행)
        escaped_search = None
        if search:
            escaped_search = search.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

        # 기본 쿼리
        query = (
            client.table("intranet_documents")
            .select("*")
            .eq("org_id", current_user.org_id)
        )

        # 필터 적용
        if status_filter:
            query = query.eq("processing_status", status_filter)
        if doc_type:
            query = query.eq("doc_type", doc_type)
        if escaped_search:
            # 파일명 포함 검색 (Supabase의 ilike 연산자 사용, 와일드카드 이스케이프)
            query = query.ilike("filename", f"%{escaped_search}%")

        # 정렬 적용
        query = query.order(sort_by, desc=(order == "desc"))

        # 페이지네이션
        query = query.range(offset, offset + limit - 1)

        result = await query.execute()

        # 전체 개수 조회 (필터 적용, 정렬 제외)
        count_query = (
            client.table("intranet_documents")
            .select("id")
            .eq("org_id", current_user.org_id)
        )
        if status_filter:
            count_query = count_query.eq("processing_status", status_filter)
        if doc_type:
            count_query = count_query.eq("doc_type", doc_type)
        if escaped_search:
            count_query = count_query.ilike("filename", f"%{escaped_search}%")

        count_result = await count_query.execute()
        total = len(count_result.data) if count_result.data else 0

        items = [
            DocumentResponse(
                id=doc["id"],
                filename=doc["filename"],
                doc_type=doc["doc_type"],
                storage_path=doc["storage_path"],
                processing_status=doc["processing_status"],
                total_chars=doc["total_chars"],
                chunk_count=doc["chunk_count"],
                error_message=doc.get("error_message"),
                created_at=doc["created_at"],
                updated_at=doc["updated_at"],
            )
            for doc in (result.data or [])
        ]

        return DocumentListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.error(f"[{current_user.org_id}] 문서 목록 조회 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 목록 조회 중 오류가 발생했습니다",
        )


@router.get("/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> DocumentDetailResponse:
    """
    문서 상세 조회

    extracted_text는 첫 1000자만 반환 (대용량 방지)
    """
    client = await get_async_client()

    try:
        result = await (
            client.table("intranet_documents")
            .select("*")
            .eq("id", document_id)
            .eq("org_id", current_user.org_id)
            .single()
            .execute()
        )

        doc = result.data
        extracted_text = doc.get("extracted_text")
        if extracted_text and len(extracted_text) > 1000:
            extracted_text = extracted_text[:1000]

        return DocumentDetailResponse(
            id=doc["id"],
            filename=doc["filename"],
            doc_type=doc["doc_type"],
            storage_path=doc["storage_path"],
            extracted_text=extracted_text,
            processing_status=doc["processing_status"],
            total_chars=doc["total_chars"],
            chunk_count=doc["chunk_count"],
            error_message=doc.get("error_message"),
            created_at=doc["created_at"],
            updated_at=doc["updated_at"],
        )

    except Exception as e:
        logger.error(f"[{current_user.org_id}] 문서 조회 실패 ({document_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="문서를 찾을 수 없습니다",
        )


@router.post("/{document_id}/process", response_model=DocumentProcessResponse)
async def reprocess_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> DocumentProcessResponse:
    """
    문서 재처리 (실패한 문서 재시도)

    - 진행 중인 문서는 재처리 불가 (race condition 방지)
    - error_message 초기화
    - processing_status: extracting으로 리셋
    - process_document() 비동기 호출
    """
    client = await get_async_client()

    try:
        # 문서 존재 확인
        doc_result = await (
            client.table("intranet_documents")
            .select("*")
            .eq("id", document_id)
            .eq("org_id", current_user.org_id)
            .single()
            .execute()
        )

        doc = doc_result.data

        # 진행 중인 상태 확인 (재처리 불가)
        current_status = doc.get("processing_status")
        if current_status in ("extracting", "chunking", "embedding"):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"문서가 현재 처리 중입니다 (상태: {current_status}). 처리 완료 후 재시도하세요.",
            )

        # 상태 리셋
        update_result = await (
            client.table("intranet_documents")
            .update({
                "processing_status": "extracting",
                "error_message": None,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            })
            .eq("id", document_id)
            .execute()
        )

        if not update_result.data:
            raise Exception("상태 업데이트 실패")

        # 백그라운드: 비동기 처리 시작 (동시성 제한 적용)
        asyncio.create_task(process_document_bounded(document_id, current_user.org_id))

        return DocumentProcessResponse(
            id=document_id,
            processing_status="extracting",
            message="재처리 시작됨",
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[{current_user.org_id}] 문서 재처리 실패 ({document_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 재처리 중 오류가 발생했습니다",
        )


@router.get("/{document_id}/chunks", response_model=ChunkListResponse)
async def get_document_chunks(
    document_id: str,
    chunk_type: Optional[str] = Query(None),
    sort_by: Optional[Literal["chunk_index", "created_at", "char_count"]] = Query(
        "chunk_index", description="정렬 기준"
    ),
    order: Optional[Literal["asc", "desc"]] = Query("asc", description="정렬 순서"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: CurrentUser = Depends(get_current_user),
) -> ChunkListResponse:
    """
    문서의 청크 목록 조회

    쿼리 파라미터:
    - chunk_type: title, heading, body, table, image
    - sort_by: chunk_index|created_at|char_count (기본: chunk_index)
    - order: asc|desc (기본: asc for chunk_index)
    - limit: 페이지당 항목 수 (기본 20, 최대 100)
    - offset: 페이지 시작 위치 (기본 0)
    """
    client = await get_async_client()

    try:
        # 문서 존재 확인
        await (
            client.table("intranet_documents")
            .select("id")
            .eq("id", document_id)
            .eq("org_id", current_user.org_id)
            .single()
            .execute()
        )

        # 청크 목록 조회
        query = (
            client.table("document_chunks")
            .select("*")
            .eq("document_id", document_id)
            .eq("org_id", current_user.org_id)
            .order(sort_by, desc=(order == "desc"))
        )

        if chunk_type:
            query = query.eq("chunk_type", chunk_type)

        query = query.range(offset, offset + limit - 1)
        result = await query.execute()

        # 전체 개수 조회
        count_query = (
            client.table("document_chunks")
            .select("id")
            .eq("document_id", document_id)
            .eq("org_id", current_user.org_id)
        )
        if chunk_type:
            count_query = count_query.eq("chunk_type", chunk_type)
        count_result = await count_query.execute()

        total = len(count_result.data) if count_result.data else 0

        from app.models.document_schemas import ChunkResponse

        items = [
            ChunkResponse(
                id=chunk["id"],
                chunk_index=chunk["chunk_index"],
                chunk_type=chunk["chunk_type"],
                section_title=chunk.get("section_title"),
                content=chunk["content"],
                char_count=chunk["char_count"],
                created_at=chunk["created_at"],
            )
            for chunk in (result.data or [])
        ]

        return ChunkListResponse(
            items=items,
            total=total,
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        logger.error(f"[{current_user.org_id}] 청크 목록 조회 실패 ({document_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="청크 목록 조회 중 오류가 발생했습니다",
        )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: str,
    current_user: CurrentUser = Depends(get_current_user),
) -> None:
    """
    문서 삭제

    - 문서 메타데이터 삭제
    - 관련 청크 자동 삭제 (ON DELETE CASCADE)
    - Supabase Storage 파일 삭제
    """
    client = await get_async_client()

    try:
        # 문서 존재 및 접근 권한 확인
        doc_result = await (
            client.table("intranet_documents")
            .select("storage_path")
            .eq("id", document_id)
            .eq("org_id", current_user.org_id)
            .single()
            .execute()
        )

        doc = doc_result.data
        storage_path = doc.get("storage_path")

        # Storage에서 파일 삭제
        if storage_path:
            try:
                bucket = settings.storage_bucket_intranet
                await client.storage.from_(bucket).remove([storage_path])
                logger.info(f"[{current_user.org_id}] Storage 파일 삭제: {storage_path}")
            except Exception as e:
                logger.warning(f"[{current_user.org_id}] Storage 파일 삭제 경고: {e}")
                # Storage 삭제 실패는 진행 계속 (DB 삭제는 수행)

        # DB에서 문서 레코드 삭제 (CASCADE로 청크도 자동 삭제)
        await (
            client.table("intranet_documents")
            .delete()
            .eq("id", document_id)
            .execute()
        )

        logger.info(f"[{current_user.org_id}] 문서 삭제 완료: {document_id}")

    except Exception as e:
        logger.error(f"[{current_user.org_id}] 문서 삭제 실패 ({document_id}): {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 삭제 중 오류가 발생했습니다",
        )
