"""E2E test fixtures for real Supabase integration"""

import pytest
import os
from datetime import datetime, timezone
from dotenv import load_dotenv

from app.models.auth_schemas import CurrentUser
from app.utils.supabase_client import get_async_client

# Load .env for E2E tests
load_dotenv()


@pytest.fixture(scope="session")
def e2e_config():
    """E2E test configuration from environment"""
    return {
        "supabase_url": os.getenv("SUPABASE_URL", ""),
        "supabase_key": os.getenv("SUPABASE_KEY", ""),
        "supabase_service_role_key": os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
        "skip_if_not_configured": not (
            os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        ),
    }


@pytest.fixture(scope="function")
async def supabase_client_real(e2e_config):
    """Real Supabase async client for E2E tests

    NOTE: Tests using this fixture require valid Supabase credentials in .env
    To skip E2E tests: unset SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY
    """
    if e2e_config["skip_if_not_configured"]:
        pytest.skip("Supabase credentials not configured for E2E tests")

    client = await get_async_client()
    yield client
    # No cleanup needed - client connection is managed by app


@pytest.fixture
def test_user():
    """Test user for E2E operations"""
    return CurrentUser(
        id="test-e2e-user-001",
        email="e2e-test@example.com",
        name="E2E Test User",
        role="member",
        org_id="test-e2e-org-001",
    )


@pytest.fixture(scope="function")
async def test_org_setup(supabase_client_real):
    """Create test org record (if needed for RLS)"""
    org_data = {
        "id": "test-e2e-org-001",
        "name": "E2E Test Organization",
        "plan": "trial",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    try:
        # Upsert test org (handle if table doesn't exist)
        result = await supabase_client_real.table("organizations").upsert(org_data).execute()
        yield result
    except Exception as e:
        # Skip if table structure doesn't support this
        pytest.skip(f"Cannot set up test org: {e}")


@pytest.fixture(scope="function")
async def cleanup_test_documents(supabase_client_real):
    """Cleanup fixture to remove test documents after tests"""
    yield

    # Cleanup: delete all test documents
    try:
        await supabase_client_real.table("intranet_documents").delete().eq(
            "org_id", "test-e2e-org-001"
        ).execute()
    except Exception as e:
        print(f"Warning: Could not clean up test documents: {e}")


@pytest.fixture(scope="function")
async def test_document_data(test_user):
    """Sample document data for upload tests"""
    return {
        "filename": "test-e2e-document.pdf",
        "doc_type": "보고서",
        "doc_subtype": None,
        "file_content": b"%PDF-1.4\n%test pdf content",
    }


@pytest.fixture(scope="function")
async def uploaded_document_id(supabase_client_real, test_user, test_document_data):
    """Upload a test document and return its ID"""
    import uuid

    doc_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    # Insert document record
    doc_record = {
        "id": doc_id,
        "org_id": test_user.org_id,
        "filename": test_document_data["filename"],
        "doc_type": test_document_data["doc_type"],
        "doc_subtype": test_document_data["doc_subtype"],
        "storage_path": f"{test_user.org_id}/{doc_id}/{test_document_data['filename']}",
        "processing_status": "extracting",
        "total_chars": 0,
        "chunk_count": 0,
        "created_at": now,
        "updated_at": now,
    }

    result = await supabase_client_real.table("intranet_documents").insert(doc_record).execute()

    if result.data:
        yield doc_id
        # Cleanup
        try:
            await supabase_client_real.table("intranet_documents").delete().eq(
                "id", doc_id
            ).execute()
        except Exception as e:
            print(f"Warning: Could not clean up document {doc_id}: {e}")
    else:
        pytest.skip("Could not create test document")
