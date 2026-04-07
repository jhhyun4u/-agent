"""문서 수집 및 처리 관련 Pydantic 스키마"""

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class DocumentUploadRequest(BaseModel):
    """문서 업로드 요청"""

    doc_type: Literal["보고서", "제안서", "실적", "기타"]
    doc_subtype: Optional[str] = None
    project_id: Optional[str] = None


class DocumentResponse(BaseModel):
    """문서 조회 응답"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    doc_type: Literal["보고서", "제안서", "실적", "기타"]
    storage_path: str
    processing_status: Literal["extracting", "chunking", "embedding", "completed", "failed"] = Field(
        description="문서 처리 상태"
    )
    total_chars: int = 0
    chunk_count: int = 0
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DocumentListResponse(BaseModel):
    """문서 목록 응답"""

    items: list[DocumentResponse]
    total: int
    limit: int
    offset: int


class DocumentDetailResponse(DocumentResponse):
    """문서 상세 응답 (extracted_text 포함)"""

    extracted_text: Optional[str] = Field(
        None, description="첫 1000자만 반환 (대용량 방지)"
    )


class ChunkResponse(BaseModel):
    """청크 조회 응답"""

    model_config = ConfigDict(from_attributes=True)

    id: str
    chunk_index: int
    chunk_type: Literal["section", "slide", "article", "window"] = Field(
        description="청크 타입"
    )
    section_title: Optional[str] = None
    content: str
    char_count: int
    created_at: datetime


class ChunkListResponse(BaseModel):
    """청크 목록 응답"""

    items: list[ChunkResponse]
    total: int
    limit: int
    offset: int


class DocumentProcessRequest(BaseModel):
    """문서 재처리 요청"""

    pass  # 별도 파라미터 없음


class DocumentProcessResponse(BaseModel):
    """문서 재처리 응답"""

    id: str
    processing_status: Literal["extracting", "chunking", "embedding", "completed", "failed"]
    message: str
