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
from typing import Optional, Literal

from fastapi import APIRouter, Depends, File, UploadFile, Query, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db, require_project_access
from app.config import settings
from app.exceptions import PropNotFoundError, TenopAPIError
from app.models.auth_schemas import CurrentUser
from app.models.document_schemas import (
    DocumentUploadRequest,
    DocumentResponse,
    DocumentListResponse,
    DocumentDetailResponse,
    ChunkListResponse,
    DocumentProcessResponse,
)
from app.services.document_ingestion import process_document
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


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(..., description="보고서|제안서|실적|기타"),
    doc_subtype: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_project_access),
) -> DocumentResponse:
    """
    문서 파일 업로드 및 처리 시작

    - 파일을 Supabase Storage에 저장
    - intranet_documents 레코드 생성
    - 백그라운드에서 process_document() 비동기 호출
    - 즉시 응답 (상태는 클라이언트가 주기적으로 조회)
    """
    import uuid
    from datetime import datetime
    import os

    client = await get_async_client()

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

    # 파일 크기 검증 (500MB)
    if file.size and file.size > 500 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="파일이 너무 큽니다 (최대 500MB)",
        )

    try:
        # 파일 읽기
        file_content = await file.read()

        # Supabase Storage에 저장
        bucket = settings.storage_bucket_intranet
        document_id = str(uuid.uuid4())
        storage_path = f"{current_user.org_id}/{document_id}/{file.filename}"

        await client.storage.from_(bucket).upload(
            path=storage_path,
            file=file_content,
            file_options={"upsert": "true"},
        )
        logger.info(f"[{current_user.org_id}] Storage 업로드 완료: {storage_path}")

        # intranet_documents 레코드 생성
        now = datetime.utcnow()
        doc_result = await client.table("intranet_documents").insert({
            "id": document_id,
            "org_id": current_user.org_id,
            "filename": file.filename,
            "doc_type": doc_type,
            "doc_subtype": doc_subtype,
            "storage_path": storage_path,
            "processing_status": "extracting",
            "total_chars": 0,
            "chunk_count": 0,
            "created_at": now.isoformat(),
            "updated_at": now.isoformat(),
        }).execute()

        if not doc_result.data:
            raise Exception("문서 레코드 생성 실패")

        doc = doc_result.data[0]

        # 백그라운드: 비동기 처리 시작
        asyncio.create_task(process_document(document_id, current_user.org_id))

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
        logger.error(f"[{current_user.org_id}] 문서 업로드 실패: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="문서 업로드 중 오류가 발생했습니다",
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
    _: None = Depends(require_project_access),
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
        if search:
            # 파일명 포함 검색 (Supabase의 ilike 연산자 사용)
            query = query.ilike("filename", f"%{search}%")

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
        if search:
            count_query = count_query.ilike("filename", f"%{search}%")

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
    _: None = Depends(require_project_access),
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
    _: None = Depends(require_project_access),
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
        from datetime import datetime
        update_result = await (
            client.table("intranet_documents")
            .update({
                "processing_status": "extracting",
                "error_message": None,
                "updated_at": datetime.utcnow().isoformat(),
            })
            .eq("id", document_id)
            .execute()
        )

        if not update_result.data:
            raise Exception("상태 업데이트 실패")

        # 백그라운드: 비동기 처리 시작
        asyncio.create_task(process_document(document_id, current_user.org_id))

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
    _: None = Depends(require_project_access),
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
    _: None = Depends(require_project_access),
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
