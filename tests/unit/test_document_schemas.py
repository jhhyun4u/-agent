"""Unit tests for document schemas (U-SCH-*)"""

import pytest
from datetime import datetime, timezone
from pydantic import ValidationError
from app.models.document_schemas import (
    DocumentUploadRequest,
    DocumentResponse,
    DocumentDetailResponse,
    ChunkResponse,
    DocumentListResponse,
    ChunkListResponse,
)


class TestDocumentUploadRequest:
    """Tests for upload request validation"""

    def test_usch_01_valid_보고서(self):
        """U-SCH-01: Valid doc_type='보고서' accepted"""
        req = DocumentUploadRequest(doc_type="보고서")
        assert req.doc_type == "보고서"

    def test_usch_01_valid_제안서(self):
        """U-SCH-01: Valid doc_type='제안서' accepted"""
        req = DocumentUploadRequest(doc_type="제안서")
        assert req.doc_type == "제안서"

    def test_usch_01_valid_실적(self):
        """U-SCH-01: Valid doc_type='실적' accepted"""
        req = DocumentUploadRequest(doc_type="실적")
        assert req.doc_type == "실적"

    def test_usch_01_valid_기타(self):
        """U-SCH-01: Valid doc_type='기타' accepted"""
        req = DocumentUploadRequest(doc_type="기타")
        assert req.doc_type == "기타"

    def test_usch_02_invalid_doc_type(self):
        """U-SCH-02: Invalid doc_type rejected"""
        with pytest.raises(ValidationError):
            DocumentUploadRequest(doc_type="invalid_type")

    def test_usch_02_empty_doc_type(self):
        """U-SCH-02: Empty doc_type rejected"""
        with pytest.raises(ValidationError):
            DocumentUploadRequest(doc_type="")

    def test_usch_02_missing_doc_type(self):
        """U-SCH-02: Missing doc_type rejected"""
        with pytest.raises(ValidationError):
            DocumentUploadRequest()


class TestDocumentResponse:
    """Tests for document response schema"""

    def test_usch_03_full_response(self):
        """U-SCH-03: Full DocumentResponse validates"""
        doc = DocumentResponse(
            id="test-id",
            filename="test.pdf",
            doc_type="보고서",
            storage_path="org/id/file.pdf",
            processing_status="completed",
            total_chars=1000,
            chunk_count=5,
            error_message=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert doc.id == "test-id"
        assert doc.error_message is None

    def test_usch_03_optional_error_message(self):
        """U-SCH-03: error_message=None is valid"""
        doc = DocumentResponse(
            id="test-id",
            filename="test.pdf",
            doc_type="보고서",
            storage_path="org/id/file.pdf",
            processing_status="failed",
            total_chars=0,
            chunk_count=0,
            error_message=None,  # Explicitly None
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert doc.error_message is None

    def test_usch_03_error_message_present(self):
        """U-SCH-03: error_message with text is valid"""
        doc = DocumentResponse(
            id="test-id",
            filename="test.pdf",
            doc_type="보고서",
            storage_path="org/id/file.pdf",
            processing_status="failed",
            total_chars=0,
            chunk_count=0,
            error_message="파일 읽기 실패",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert doc.error_message == "파일 읽기 실패"


class TestDocumentDetailResponse:
    """Tests for detail response with extracted_text"""

    def test_usch_04_extracted_text_optional(self):
        """U-SCH-04: extracted_text is optional"""
        doc = DocumentDetailResponse(
            id="test-id",
            filename="test.pdf",
            doc_type="보고서",
            storage_path="org/id/file.pdf",
            processing_status="completed",
            total_chars=1000,
            chunk_count=5,
            error_message=None,
            extracted_text=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert doc.extracted_text is None

    def test_usch_04_extracted_text_with_content(self):
        """U-SCH-04: extracted_text with content is valid"""
        text = "This is extracted text"
        doc = DocumentDetailResponse(
            id="test-id",
            filename="test.pdf",
            doc_type="보고서",
            storage_path="org/id/file.pdf",
            processing_status="completed",
            total_chars=1000,
            chunk_count=5,
            error_message=None,
            extracted_text=text,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert doc.extracted_text == text


class TestChunkResponse:
    """Tests for chunk response schema"""

    def test_usch_05_chunk_optional_section_title(self):
        """U-SCH-05: section_title=None is valid"""
        chunk = ChunkResponse(
            id="chunk-1",
            chunk_index=0,
            chunk_type="window",
            section_title=None,
            content="content",
            char_count=7,
            created_at=datetime.now(timezone.utc),
        )
        assert chunk.section_title is None

    def test_usch_05_chunk_with_section_title(self):
        """U-SCH-05: section_title with text is valid"""
        chunk = ChunkResponse(
            id="chunk-1",
            chunk_index=0,
            chunk_type="section",
            section_title="제1장",
            content="content",
            char_count=7,
            created_at=datetime.now(timezone.utc),
        )
        assert chunk.section_title == "제1장"


class TestListResponses:
    """Tests for list response schemas"""

    def test_usch_06_document_list_structure(self):
        """U-SCH-06: DocumentListResponse has correct structure"""
        now = datetime.now(timezone.utc)
        items = [
            DocumentResponse(
                id=f"doc-{i}",
                filename=f"file-{i}.pdf",
                doc_type="보고서",
                storage_path=f"org/doc-{i}/file.pdf",
                processing_status="completed",
                total_chars=1000,
                chunk_count=5,
                error_message=None,
                created_at=now,
                updated_at=now,
            )
            for i in range(3)
        ]
        
        list_resp = DocumentListResponse(items=items, total=3, limit=20, offset=0)
        assert len(list_resp.items) == 3
        assert list_resp.total == 3
        assert list_resp.limit == 20
        assert list_resp.offset == 0

    def test_usch_06_chunk_list_structure(self):
        """U-SCH-06: ChunkListResponse has correct structure"""
        now = datetime.now(timezone.utc)
        items = [
            ChunkResponse(
                id=f"chunk-{i}",
                chunk_index=i,
                chunk_type="section",
                section_title=f"Section {i}",
                content=f"content {i}",
                char_count=10,
                created_at=now,
            )
            for i in range(5)
        ]
        
        list_resp = ChunkListResponse(items=items, total=5, limit=20, offset=0)
        assert len(list_resp.items) == 5
        assert list_resp.total == 5
