"""Integration tests for document routes (I-*)"""

import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
from io import BytesIO



class TestUploadEndpoint:
    """Tests for POST /api/documents/upload (I-UPL-*)"""

    @pytest.mark.asyncio
    async def test_iupl_01_valid_upload(self, mock_current_user, mock_supabase_client):
        """I-UPL-01: Valid PDF upload succeeds with 201 response"""
        from app.main import app

        now = datetime.now(timezone.utc).isoformat()
        doc_data = {
            "id": "doc-001",
            "filename": "test.pdf",
            "file_size_bytes": 26,
            "doc_type": "보고서",
            "storage_path": "test-org-001/doc-001/test.pdf",
            "processing_status": "extracting",
            "total_chars": 0,
            "chunk_count": 0,
            "error_message": None,
            "created_at": now,
            "updated_at": now,
        }

        # Queue response: insert returns list with doc data
        mock_supabase_client._execute_responses.append([doc_data])
        mock_supabase_client.storage.from_.return_value.upload = AsyncMock(return_value=None)

        with patch("app.api.routes_documents.get_async_client", return_value=mock_supabase_client):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/documents/upload",
                    data={"doc_type": "보고서"},
                    files={"file": ("test.pdf", BytesIO(b"%PDF-1.4\nPDF content"), "application/pdf")}
                )

        assert response.status_code == 201
        data = response.json()
        assert data["id"] == "doc-001"
        assert data["filename"] == "test.pdf"

    @pytest.mark.asyncio
    async def test_iupl_02_invalid_doc_type(self, mock_current_user, mock_supabase_client):
        """I-UPL-02: Invalid doc_type returns 400"""
        from app.main import app

        with patch("app.api.routes_documents.get_async_client", return_value=mock_supabase_client):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/documents/upload",
                    data={"doc_type": "invalid"},
                    files={"file": ("test.pdf", BytesIO(b"content"), "application/pdf")}
                )

        assert response.status_code == 400
        assert "잘못된 문서 타입" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_iupl_03_unsupported_file_ext(self, mock_current_user, mock_supabase_client):
        """I-UPL-03: Unsupported file extension returns 415"""
        from app.main import app

        with patch("app.api.routes_documents.get_async_client", return_value=mock_supabase_client):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post(
                    "/api/documents/upload",
                    data={"doc_type": "보고서"},
                    files={"file": ("virus.exe", BytesIO(b"content"), "application/x-msdownload")}
                )

        assert response.status_code == 415


class TestListEndpoint:
    """Tests for GET /api/documents (I-LST-*)"""

    @pytest.mark.asyncio
    async def test_ilst_01_returns_paginated_list(self, mock_current_user, mock_supabase_client):
        """I-LST-01: Returns paginated list structure"""
        from app.main import app

        now = datetime.now(timezone.utc).isoformat()
        docs = [
            {
                "id": f"doc-{i}",
                "filename": f"file-{i}.pdf",
                "doc_type": "보고서",
                "storage_path": f"org/doc-{i}/file.pdf",
                "processing_status": "completed",
                "total_chars": 1000,
                "chunk_count": 5,
                "error_message": None,
                "created_at": now,
                "updated_at": now,
            }
            for i in range(3)
        ]

        # Queue responses: list, then count
        mock_supabase_client._execute_responses.append(docs)
        mock_supabase_client._execute_responses.append(docs)

        with patch("app.api.routes_documents.get_async_client", return_value=mock_supabase_client):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/documents")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_ilst_02_pagination_limit(self, mock_current_user, mock_supabase_client):
        """I-LST-02: limit parameter respected"""
        from app.main import app

        mock_supabase_client._execute_responses.append([])
        mock_supabase_client._execute_responses.append([])

        with patch("app.api.routes_documents.get_async_client", return_value=mock_supabase_client):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/documents?limit=50&offset=10")

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 50
        assert data["offset"] == 10


class TestDetailEndpoint:
    """Tests for GET /api/documents/{id} (I-DET-*)"""

    @pytest.mark.asyncio
    async def test_idet_01_extracted_text_truncation(self, mock_current_user, mock_supabase_client):
        """I-DET-01: extracted_text truncated at 1000 chars"""
        from app.main import app

        now = datetime.now(timezone.utc).isoformat()
        doc_data = {
            "id": "doc-001",
            "filename": "test.pdf",
            "doc_type": "보고서",
            "storage_path": "org/doc-001/test.pdf",
            "processing_status": "completed",
            "total_chars": 2000,
            "chunk_count": 5,
            "error_message": None,
            "extracted_text": "x" * 2000,
            "created_at": now,
            "updated_at": now,
        }

        mock_supabase_client._execute_responses.append(doc_data)

        with patch("app.api.routes_documents.get_async_client", return_value=mock_supabase_client):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/documents/doc-001")

        assert response.status_code == 200
        data = response.json()
        assert len(data["extracted_text"]) == 1000

    @pytest.mark.asyncio
    async def test_idet_02_document_not_found(self, mock_current_user, mock_supabase_client):
        """I-DET-02: Non-existent document returns 404"""
        from app.main import app

        # Mock will raise exception on execute
        async def raise_error(*args, **kwargs):
            raise Exception("No rows found")
        mock_supabase_client.table.return_value.execute = AsyncMock(side_effect=raise_error)

        with patch("app.api.routes_documents.get_async_client", return_value=mock_supabase_client):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/documents/nonexistent")

        assert response.status_code == 404


class TestReprocessEndpoint:
    """Tests for POST /api/documents/{id}/process (I-RPR-*)"""

    @pytest.mark.asyncio
    async def test_irpr_01_reprocess_failed_doc(self, mock_current_user, mock_supabase_client):
        """I-RPR-01: Failed document can be reprocessed"""
        from app.main import app

        now = datetime.now(timezone.utc).isoformat()
        doc_data = {
            "id": "doc-001",
            "org_id": "test-org-001",
            "filename": "test.pdf",
            "doc_type": "보고서",
            "storage_path": "org/doc-001/test.pdf",
            "processing_status": "failed",
            "total_chars": 0,
            "chunk_count": 0,
            "error_message": "Previous error",
            "created_at": now,
            "updated_at": now,
        }

        # Queue responses: fetch, then update
        mock_supabase_client._execute_responses.append(doc_data)
        mock_supabase_client._execute_responses.append([doc_data])

        with patch("app.api.routes_documents.get_async_client", return_value=mock_supabase_client):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/documents/doc-001/process")

        assert response.status_code == 200
        data = response.json()
        assert data["processing_status"] == "extracting"

    @pytest.mark.asyncio
    async def test_irpr_02_in_progress_conflict(self, mock_current_user, mock_supabase_client):
        """I-RPR-02: In-progress document returns 409"""
        from app.main import app

        now = datetime.now(timezone.utc).isoformat()
        doc_data = {
            "id": "doc-001",
            "org_id": "test-org-001",
            "filename": "test.pdf",
            "doc_type": "보고서",
            "processing_status": "extracting",  # In progress
            "created_at": now,
            "updated_at": now,
        }

        mock_supabase_client._execute_responses.append(doc_data)

        with patch("app.api.routes_documents.get_async_client", return_value=mock_supabase_client):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.post("/api/documents/doc-001/process")

        assert response.status_code == 409
        assert "처리 중입니다" in response.json()["detail"]


class TestChunksEndpoint:
    """Tests for GET /api/documents/{id}/chunks (I-CHK-*)"""

    @pytest.mark.asyncio
    async def test_ichk_01_returns_chunk_list(self, mock_current_user, mock_supabase_client):
        """I-CHK-01: Returns chunks for document"""
        from app.main import app

        now = datetime.now(timezone.utc).isoformat()
        chunks = [
            {
                "id": f"chunk-{i}",
                "document_id": "doc-001",
                "chunk_index": i,
                "chunk_type": "section",
                "section_title": f"Section {i}",
                "content": f"content {i}",
                "char_count": 100,
                "created_at": now,
            }
            for i in range(5)
        ]

        # Queue responses: doc check, chunks list, count
        mock_supabase_client._execute_responses.append({"id": "doc-001"})
        mock_supabase_client._execute_responses.append(chunks)
        mock_supabase_client._execute_responses.append(chunks)

        with patch("app.api.routes_documents.get_async_client", return_value=mock_supabase_client):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/documents/doc-001/chunks")

        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 5

    @pytest.mark.asyncio
    async def test_ichk_02_chunk_type_filter(self, mock_current_user, mock_supabase_client):
        """I-CHK-02: chunk_type filter applied"""
        from app.main import app

        now = datetime.now(timezone.utc).isoformat()
        chunks = [
            {
                "id": "c1",
                "document_id": "doc-001",
                "chunk_index": 0,
                "chunk_type": "section",
                "section_title": None,
                "content": "content",
                "char_count": 100,
                "created_at": now,
            },
        ]

        # Queue responses: doc check, filtered chunks, count
        mock_supabase_client._execute_responses.append({"id": "doc-001"})
        mock_supabase_client._execute_responses.append(chunks)
        mock_supabase_client._execute_responses.append(chunks)

        with patch("app.api.routes_documents.get_async_client", return_value=mock_supabase_client):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.get("/api/documents/doc-001/chunks?chunk_type=section")

        assert response.status_code == 200
        data = response.json()
        assert all(c["chunk_type"] == "section" for c in data["items"])


class TestDeleteEndpoint:
    """Tests for DELETE /api/documents/{id} (I-DEL-*)"""

    @pytest.mark.asyncio
    async def test_idel_01_valid_delete(self, mock_current_user, mock_supabase_client):
        """I-DEL-01: Valid delete returns 204"""
        from app.main import app

        doc_data = {
            "id": "doc-001",
            "storage_path": "test-org-001/doc-001/test.pdf",
        }

        # Queue responses: fetch, then delete
        mock_supabase_client._execute_responses.append(doc_data)
        mock_supabase_client._execute_responses.append(None)
        mock_supabase_client.storage.from_.return_value.remove = AsyncMock(return_value=None)

        with patch("app.api.routes_documents.get_async_client", return_value=mock_supabase_client):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.delete("/api/documents/doc-001")

        assert response.status_code == 204

    @pytest.mark.asyncio
    async def test_idel_02_storage_error_doesnt_block(self, mock_current_user, mock_supabase_client):
        """I-DEL-02: Storage error doesn't block DB delete"""
        from app.main import app

        doc_data = {
            "id": "doc-001",
            "storage_path": "test-org-001/doc-001/test.pdf",
        }

        # Queue responses: fetch, then delete
        mock_supabase_client._execute_responses.append(doc_data)
        mock_supabase_client._execute_responses.append(None)
        # Storage removal fails
        mock_supabase_client.storage.from_.return_value.remove = AsyncMock(
            side_effect=Exception("Storage error")
        )

        with patch("app.api.routes_documents.get_async_client", return_value=mock_supabase_client):
            async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
                response = await client.delete("/api/documents/doc-001")

        # Should still succeed despite storage error
        assert response.status_code == 204
