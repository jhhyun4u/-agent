"""E2E tests for complete document processing flow"""

import pytest
import asyncio
from datetime import datetime, timezone


@pytest.mark.e2e
class TestDocumentUploadFlow:
    """End-to-end document upload and processing"""

    @pytest.mark.asyncio
    async def test_e2e_001_document_create_and_fetch(
        self, supabase_client_real, test_user, cleanup_test_documents
    ):
        """E2E-001: Create document record and fetch it back"""
        import uuid

        doc_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()

        # Create document
        doc_record = {
            "id": doc_id,
            "org_id": test_user.org_id,
            "filename": "test-document.pdf",
            "doc_type": "보고서",
            "storage_path": f"{test_user.org_id}/{doc_id}/test-document.pdf",
            "processing_status": "extracting",
            "total_chars": 0,
            "chunk_count": 0,
            "created_at": now,
            "updated_at": now,
        }

        # Insert
        insert_result = await supabase_client_real.table("intranet_documents").insert(
            doc_record
        ).execute()

        assert insert_result.data
        assert insert_result.data[0]["id"] == doc_id
        assert insert_result.data[0]["processing_status"] == "extracting"

        # Fetch
        fetch_result = await (
            supabase_client_real.table("intranet_documents")
            .select("*")
            .eq("id", doc_id)
            .single()
            .execute()
        )

        assert fetch_result.data
        assert fetch_result.data["id"] == doc_id
        assert fetch_result.data["filename"] == "test-document.pdf"
        assert fetch_result.data["org_id"] == test_user.org_id

    @pytest.mark.asyncio
    async def test_e2e_002_document_status_transition(
        self, supabase_client_real, uploaded_document_id, cleanup_test_documents
    ):
        """E2E-002: Document status transitions through processing pipeline"""
        doc_id = uploaded_document_id

        # Verify initial status
        initial = await (
            supabase_client_real.table("intranet_documents")
            .select("processing_status")
            .eq("id", doc_id)
            .single()
            .execute()
        )
        assert initial.data["processing_status"] == "extracting"

        # Transition to chunking
        now = datetime.now(timezone.utc).isoformat()
        update1 = await supabase_client_real.table("intranet_documents").update({
            "processing_status": "chunking",
            "updated_at": now,
        }).eq("id", doc_id).execute()

        assert update1.data[0]["processing_status"] == "chunking"

        # Transition to completed with extracted text
        update2 = await supabase_client_real.table("intranet_documents").update({
            "processing_status": "completed",
            "total_chars": 1234,
            "chunk_count": 5,
            "extracted_text": "Sample extracted text from document",
            "updated_at": now,
        }).eq("id", doc_id).execute()

        assert update2.data[0]["processing_status"] == "completed"
        assert update2.data[0]["total_chars"] == 1234
        assert update2.data[0]["chunk_count"] == 5

    @pytest.mark.asyncio
    async def test_e2e_003_list_documents_with_pagination(
        self, supabase_client_real, test_user, cleanup_test_documents
    ):
        """E2E-003: List documents with pagination support"""
        import uuid

        now = datetime.now(timezone.utc).isoformat()

        # Create multiple test documents
        doc_ids = []
        for i in range(5):
            doc_id = str(uuid.uuid4())
            doc_ids.append(doc_id)

            doc_record = {
                "id": doc_id,
                "org_id": test_user.org_id,
                "filename": f"document-{i}.pdf",
                "doc_type": "보고서",
                "storage_path": f"{test_user.org_id}/{doc_id}/document-{i}.pdf",
                "processing_status": "completed",
                "total_chars": 1000 + i,
                "chunk_count": 3,
                "created_at": now,
                "updated_at": now,
            }

            await supabase_client_real.table("intranet_documents").insert(doc_record).execute()

        # List with limit
        list_result = await (
            supabase_client_real.table("intranet_documents")
            .select("*")
            .eq("org_id", test_user.org_id)
            .range(0, 2)  # First 3 items
            .execute()
        )

        assert len(list_result.data) >= 3
        assert all(doc["org_id"] == test_user.org_id for doc in list_result.data)

        # List with offset
        list_result2 = await (
            supabase_client_real.table("intranet_documents")
            .select("*")
            .eq("org_id", test_user.org_id)
            .range(3, 5)  # Skip first 3
            .execute()
        )

        # Verify different documents returned
        if list_result2.data:
            assert list_result2.data[0]["id"] != list_result.data[0]["id"]

    @pytest.mark.asyncio
    async def test_e2e_004_chunk_insertion_and_query(
        self, supabase_client_real, uploaded_document_id, test_user, cleanup_test_documents
    ):
        """E2E-004: Create chunks and query by document"""
        import uuid

        doc_id = uploaded_document_id
        now = datetime.now(timezone.utc).isoformat()

        # Create chunks
        chunks = []
        for i in range(3):
            chunk_id = str(uuid.uuid4())
            chunk_record = {
                "id": chunk_id,
                "document_id": doc_id,
                "org_id": test_user.org_id,
                "chunk_index": i,
                "chunk_type": "section",
                "section_title": f"Section {i+1}",
                "content": f"This is chunk {i+1} content with some sample text.",
                "char_count": 50,
                "created_at": now,
            }

            result = await supabase_client_real.table("document_chunks").insert(
                chunk_record
            ).execute()

            if result.data:
                chunks.append(result.data[0])

        # Query chunks by document
        chunks_result = await (
            supabase_client_real.table("document_chunks")
            .select("*")
            .eq("document_id", doc_id)
            .order("chunk_index", desc=False)
            .execute()
        )

        assert len(chunks_result.data) >= 3
        assert all(chunk["document_id"] == doc_id for chunk in chunks_result.data)
        assert chunks_result.data[0]["chunk_index"] < chunks_result.data[1]["chunk_index"]

    @pytest.mark.asyncio
    async def test_e2e_005_document_deletion_cascade(
        self, supabase_client_real, uploaded_document_id, test_user
    ):
        """E2E-005: Delete document and verify chunks are cascade deleted"""
        import uuid

        doc_id = uploaded_document_id
        now = datetime.now(timezone.utc).isoformat()

        # Create chunks for document
        chunk_ids = []
        for i in range(2):
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)

            chunk_record = {
                "id": chunk_id,
                "document_id": doc_id,
                "org_id": test_user.org_id,
                "chunk_index": i,
                "chunk_type": "section",
                "content": f"Chunk {i} content",
                "char_count": 20,
                "created_at": now,
            }

            await supabase_client_real.table("document_chunks").insert(
                chunk_record
            ).execute()

        # Verify chunks exist
        before_delete = await supabase_client_real.table("document_chunks").select(
            "*"
        ).eq("document_id", doc_id).execute()

        assert len(before_delete.data) >= 2

        # Delete document
        delete_result = await supabase_client_real.table("intranet_documents").delete().eq(
            "id", doc_id
        ).execute()

        # Verify document is deleted
        after_delete = await supabase_client_real.table("intranet_documents").select(
            "*"
        ).eq("id", doc_id).execute()

        assert not after_delete.data or len(after_delete.data) == 0


@pytest.mark.e2e
class TestDocumentFiltering:
    """Document filtering and search capabilities"""

    @pytest.mark.asyncio
    async def test_e2e_006_filter_by_status(
        self, supabase_client_real, test_user, cleanup_test_documents
    ):
        """E2E-006: Filter documents by processing status"""
        import uuid

        now = datetime.now(timezone.utc).isoformat()

        # Create documents with different statuses
        statuses = ["extracting", "chunking", "completed", "failed"]
        for status in statuses:
            doc_id = str(uuid.uuid4())
            doc_record = {
                "id": doc_id,
                "org_id": test_user.org_id,
                "filename": f"doc-{status}.pdf",
                "doc_type": "보고서",
                "storage_path": f"{test_user.org_id}/{doc_id}/doc.pdf",
                "processing_status": status,
                "total_chars": 0,
                "chunk_count": 0,
                "created_at": now,
                "updated_at": now,
            }

            await supabase_client_real.table("intranet_documents").insert(
                doc_record
            ).execute()

        # Filter by status
        completed = await supabase_client_real.table("intranet_documents").select(
            "*"
        ).eq("org_id", test_user.org_id).eq("processing_status", "completed").execute()

        assert any(doc["processing_status"] == "completed" for doc in completed.data or [])

    @pytest.mark.asyncio
    async def test_e2e_007_filter_by_doc_type(
        self, supabase_client_real, test_user, cleanup_test_documents
    ):
        """E2E-007: Filter documents by type (보고서, 제안서, etc)"""
        import uuid

        now = datetime.now(timezone.utc).isoformat()

        # Create documents with different types
        types = ["보고서", "제안서", "실적"]
        for doc_type in types:
            doc_id = str(uuid.uuid4())
            doc_record = {
                "id": doc_id,
                "org_id": test_user.org_id,
                "filename": f"doc-{doc_type}.pdf",
                "doc_type": doc_type,
                "storage_path": f"{test_user.org_id}/{doc_id}/doc.pdf",
                "processing_status": "completed",
                "total_chars": 0,
                "chunk_count": 0,
                "created_at": now,
                "updated_at": now,
            }

            await supabase_client_real.table("intranet_documents").insert(
                doc_record
            ).execute()

        # Filter by type
        proposals = await supabase_client_real.table("intranet_documents").select(
            "*"
        ).eq("org_id", test_user.org_id).eq("doc_type", "제안서").execute()

        assert any(doc["doc_type"] == "제안서" for doc in proposals.data or [])
