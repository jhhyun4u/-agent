"""Unit tests for data validation (D-*)"""

import pytest
from pydantic import ValidationError


class TestDocTypeValidation:
    """Tests for doc_type validation (D-DOC-*)"""

    @pytest.mark.parametrize("valid_type", ["보고서", "제안서", "실적", "기타"])
    def test_ddoc_accepted_types(self, valid_type):
        """D-DOC-01/02/03/04: All valid doc_type values accepted"""
        from app.models.document_schemas import DocumentUploadRequest
        req = DocumentUploadRequest(doc_type=valid_type)
        assert req.doc_type == valid_type

    def test_ddoc_05_invalid_with_number(self):
        """D-DOC-05: Invalid type rejected"""
        from app.models.document_schemas import DocumentUploadRequest
        with pytest.raises(ValidationError):
            DocumentUploadRequest(doc_type="보고서2")

    def test_ddoc_06_empty_string(self):
        """D-DOC-06: Empty string is rejected"""
        from app.models.document_schemas import DocumentUploadRequest
        with pytest.raises(ValidationError):
            DocumentUploadRequest(doc_type="")


class TestFileExtensionValidation:
    """Tests for file extension validation"""

    def test_valid_extensions(self):
        """Test all valid intranet_doc extensions"""
        from app.utils.file_utils import validate_extension
        for ext in ["pdf", "hwp", "hwpx", "docx", "doc", "txt"]:
            assert validate_extension(f"file.{ext}", "intranet_doc") == ext

    def test_invalid_extension(self):
        """Test invalid extension raises error"""
        from app.utils.file_utils import validate_extension, FileFormatError
        with pytest.raises(FileFormatError):
            validate_extension("virus.exe", "intranet_doc")


class TestChunkingDataValidation:
    """Tests for chunking boundary data validation"""

    def test_chunk_exact_max_size(self):
        """Section exactly max_chunk_chars creates chunk"""
        from app.services.document_chunker import chunk_document
        text = "제1장\n" + "x" * 2995
        result = chunk_document(text, "보고서")
        assert len(result) >= 1

    def test_chunk_over_max_size_split(self):
        """Section over max_chunk_chars splits into multiple"""
        from app.services.document_chunker import _chunk_by_window
        text = "제1장\n" + "x" * 3100
        result = _chunk_by_window(text, window=2000)
        assert len(result) >= 2

    def test_chunk_overlap_behavior(self):
        """Overlapping windows preserve boundary content"""
        from app.services.document_chunker import _chunk_by_window
        text = "ABCDEFGHIJ" * 100
        chunks = _chunk_by_window(text, window=300, overlap=50)
        assert len(chunks) >= 2
        for chunk in chunks:
            assert chunk.char_count > 0

    def test_chunk_min_chars_boundary(self):
        """Section at min_chars boundary included"""
        from app.services.document_chunker import _chunk_by_headings
        text = "제1장\n" + "x" * 196
        result = _chunk_by_headings(text, min_chars=200)
        assert len(result) >= 1


class TestTextLengthValidation:
    """Tests for text length boundaries"""

    def test_extracted_text_1000_chars(self):
        """1000-char text returned as-is"""
        from app.models.document_schemas import DocumentDetailResponse
        from datetime import datetime, timezone

        text = "x" * 1000
        doc = DocumentDetailResponse(
            id="id",
            filename="f.pdf",
            doc_type="보고서",
            storage_path="p",
            processing_status="completed",
            total_chars=1000,
            chunk_count=0,
            error_message=None,
            extracted_text=text,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert len(doc.extracted_text) == 1000

    def test_extracted_text_none(self):
        """extracted_text=None is valid"""
        from app.models.document_schemas import DocumentDetailResponse
        from datetime import datetime, timezone

        doc = DocumentDetailResponse(
            id="id",
            filename="f.pdf",
            doc_type="보고서",
            storage_path="p",
            processing_status="extracting",
            total_chars=0,
            chunk_count=0,
            error_message=None,
            extracted_text=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        assert doc.extracted_text is None


class TestPaginationValidation:
    """Tests for pagination parameter validation"""

    def test_valid_pagination(self):
        """Valid pagination parameters accepted"""
        from app.models.document_schemas import DocumentListResponse

        resp = DocumentListResponse(items=[], total=0, limit=20, offset=0)
        assert resp.limit == 20
        assert resp.offset == 0

    def test_max_limit(self):
        """limit=100 (max) accepted"""
        from app.models.document_schemas import DocumentListResponse

        resp = DocumentListResponse(items=[], total=0, limit=100, offset=0)
        assert resp.limit == 100
