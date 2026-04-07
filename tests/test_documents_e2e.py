"""
Document ingestion E2E tests (integration with real server).

Run with: uv run pytest tests/test_documents_e2e.py -v -s
"""

import os
import pytest
import requests
import time
from dotenv import load_dotenv
from supabase import create_client

# Load env
load_dotenv()

# Test configuration
API_BASE_URL = "http://localhost:8000"
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

# Initialize Supabase client for verification
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


@pytest.fixture
def test_pdf_file():
    """Create a PDF file with sufficient text for processing."""
    # Use reportlab to create a proper PDF with text
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        import io

        buffer = io.BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)

        # Add substantial text content (> 50 characters required for processing)
        text = "This is a test document for E2E testing. " * 10  # Repeat to ensure sufficient length
        y = 750
        for line in text.split(" "):
            if y < 50:
                c.showPage()
                y = 750
            c.drawString(100, y, line)
            y -= 15

        c.save()
        buffer.seek(0)
        return buffer
    except ImportError:
        # Fallback to simple text if reportlab not available
        import io
        pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< >>
stream
BT
/F1 12 Tf
100 700 Td
(This is a test document for E2E testing. This is a test document for E2E testing.) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000214 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
312
%%EOF
"""
        return io.BytesIO(pdf_content)


class TestDocumentUploadE2E:
    """End-to-end tests for document upload feature."""

    def test_upload_creates_document_record(self, test_pdf_file):
        """Test that upload creates a document record in the database."""
        response = requests.post(
            f"{API_BASE_URL}/api/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
            data={"doc_type": "보고서"},
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 201, f"Expected 201, got {response.status_code}: {response.text}"
        data = response.json()

        # Verify response structure
        assert "id" in data
        assert data["filename"] == "test.pdf"
        assert data["doc_type"] == "보고서"
        assert data["processing_status"] == "extracting"

        # Verify document exists in database
        doc_id = data["id"]
        result = supabase.table("intranet_documents").select("*").eq("id", doc_id).single().execute()
        assert result.data is not None
        assert result.data["filename"] == "test.pdf"

    def test_upload_stores_file_in_storage(self, test_pdf_file):
        """Test that uploaded file is stored in Supabase Storage."""
        response = requests.post(
            f"{API_BASE_URL}/api/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
            data={"doc_type": "보고서"},
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 201
        data = response.json()
        storage_path = data["storage_path"]

        # Verify file exists in storage
        try:
            file_data = supabase.storage.from_("intranet-documents").download(storage_path)
            assert len(file_data) > 0  # File exists and has content
        except Exception as e:
            pytest.fail(f"File not found in storage: {e}")

    def test_upload_triggers_async_processing(self, test_pdf_file):
        """Test that async processing starts after upload."""
        response = requests.post(
            f"{API_BASE_URL}/api/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
            data={"doc_type": "보고서"},
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 201
        data = response.json()
        doc_id = data["id"]
        initial_status = data["processing_status"]
        assert initial_status == "extracting"

        # Wait for processing
        max_wait = 15  # seconds
        elapsed = 0
        doc = None
        while elapsed < max_wait:
            result = supabase.table("intranet_documents").select("*").eq("id", doc_id).single().execute()
            doc = result.data

            if doc["processing_status"] in ["completed", "failed"]:
                break

            time.sleep(1)
            elapsed += 1

        # Verify processing completed or at least started
        assert doc is not None, "Document not found"
        assert doc["processing_status"] in ["completed", "failed"], f"Expected completed/failed, got {doc['processing_status']} after {elapsed}s: {doc.get('error_message')}"
        if doc["processing_status"] == "completed":
            assert doc["chunk_count"] > 0, "Expected chunks to be created"

    def test_upload_creates_chunks(self, test_pdf_file):
        """Test that processing creates document chunks."""
        response = requests.post(
            f"{API_BASE_URL}/api/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
            data={"doc_type": "보고서"},
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 201
        doc_id = response.json()["id"]

        # Wait for processing to complete
        max_wait = 15  # seconds
        elapsed = 0
        while elapsed < max_wait:
            doc_result = supabase.table("intranet_documents").select("*").eq("id", doc_id).single().execute()
            doc = doc_result.data

            if doc["processing_status"] in ["completed", "failed"]:
                break

            time.sleep(1)
            elapsed += 1

        # Verify chunks exist
        chunks_result = supabase.table("document_chunks").select("*").eq("document_id", doc_id).execute()
        assert len(chunks_result.data) > 0, f"Expected chunks to be created, got 0. Document status: {doc['processing_status']}, error: {doc.get('error_message')}"

        # Verify chunk structure
        chunk = chunks_result.data[0]
        assert "id" in chunk
        assert "content" in chunk
        assert "embedding" in chunk
        assert len(chunk["embedding"]) == 3073  # Claude embedding dimension


class TestDocumentListE2E:
    """End-to-end tests for document list feature."""

    def test_list_documents_returns_documents(self, test_pdf_file):
        """Test that list endpoint returns documents."""
        # Upload a document first
        upload_response = requests.post(
            f"{API_BASE_URL}/api/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
            data={"doc_type": "보고서"},
            headers={"Authorization": "Bearer test-token"}
        )
        assert upload_response.status_code == 201

        # List documents
        response = requests.get(
            f"{API_BASE_URL}/api/documents",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data  # Response key is "items", not "documents"
        assert len(data["items"]) > 0

    def test_list_documents_pagination(self, test_pdf_file):
        """Test pagination in list endpoint."""
        response = requests.get(
            f"{API_BASE_URL}/api/documents?limit=5&offset=0",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data


class TestDocumentDetailE2E:
    """End-to-end tests for document detail feature."""

    def test_get_document_detail(self, test_pdf_file):
        """Test retrieving document detail."""
        # Upload a document
        upload_response = requests.post(
            f"{API_BASE_URL}/api/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
            data={"doc_type": "보고서"},
            headers={"Authorization": "Bearer test-token"}
        )
        assert upload_response.status_code == 201
        doc_id = upload_response.json()["id"]

        # Get detail
        response = requests.get(
            f"{API_BASE_URL}/api/documents/{doc_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == doc_id
        assert data["filename"] == "test.pdf"


class TestDocumentDeleteE2E:
    """End-to-end tests for document delete feature."""

    def test_delete_document(self, test_pdf_file):
        """Test deleting a document."""
        # Upload a document
        upload_response = requests.post(
            f"{API_BASE_URL}/api/documents/upload",
            files={"file": ("test.pdf", test_pdf_file, "application/pdf")},
            data={"doc_type": "보고서"},
            headers={"Authorization": "Bearer test-token"}
        )
        assert upload_response.status_code == 201
        doc_id = upload_response.json()["id"]

        # Delete
        response = requests.delete(
            f"{API_BASE_URL}/api/documents/{doc_id}",
            headers={"Authorization": "Bearer test-token"}
        )

        assert response.status_code == 204
        assert response.text == ""  # No content in 204 response


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
