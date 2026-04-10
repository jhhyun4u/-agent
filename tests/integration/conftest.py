"""Integration test fixtures for API endpoints"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone

from app.main import app
from app.api.deps import get_current_user
from app.models.auth_schemas import CurrentUser


# Test user
TEST_USER = CurrentUser(
    id="test-user-001",
    email="test@example.com",
    name="Test User",
    role="member",
    org_id="test-org-001",
)


@pytest.fixture
def mock_current_user():
    """Override get_current_user and require_project_access dependencies"""
    from app.api.deps import require_project_access

    def override_get_current_user():
        return TEST_USER

    def override_require_project_access():
        """require_project_access is a dependency that validates org membership"""
        return None

    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[require_project_access] = override_require_project_access
    yield TEST_USER
    app.dependency_overrides.clear()


class MockResponse:
    """Mock response object with .data attribute"""
    def __init__(self, data):
        self.data = data


def create_execute_mock(*responses):
    """Create an async mock execute that returns MockResponse objects"""
    responses_list = [MockResponse(r) for r in responses]

    async def mock_execute(*args, **kwargs):
        if not responses_list:
            return MockResponse(None)
        return responses_list.pop(0)

    return AsyncMock(side_effect=mock_execute)


def create_chainable_mock(execute_responses=None):
    """Create a mock that supports method chaining for Supabase queries"""
    mock = MagicMock()

    # All these methods return self for chaining
    mock.select = MagicMock(return_value=mock)
    mock.insert = MagicMock(return_value=mock)
    mock.update = MagicMock(return_value=mock)
    mock.delete = MagicMock(return_value=mock)
    mock.eq = MagicMock(return_value=mock)
    mock.single = MagicMock(return_value=mock)
    mock.order = MagicMock(return_value=mock)
    mock.ilike = MagicMock(return_value=mock)
    mock.range = MagicMock(return_value=mock)

    # execute is async and returns MockResponse
    if execute_responses:
        mock.execute = create_execute_mock(*execute_responses)
    else:
        async def async_execute(*args, **kwargs):
            return MockResponse(None)
        mock.execute = AsyncMock(side_effect=async_execute)

    return mock


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase async client"""
    client = AsyncMock()

    # Mock storage
    client.storage = AsyncMock()
    storage_from = AsyncMock()
    client.storage.from_ = MagicMock(return_value=storage_from)
    storage_from.upload = AsyncMock(return_value=None)
    storage_from.download = AsyncMock(return_value=b"mock file content")
    storage_from.remove = AsyncMock(return_value=None)

    # Response queue for execute() calls
    execute_responses = []

    # Create a reusable table mock
    table_mock = MagicMock()
    table_mock.select = MagicMock(return_value=table_mock)
    table_mock.insert = MagicMock(return_value=table_mock)
    table_mock.update = MagicMock(return_value=table_mock)
    table_mock.delete = MagicMock(return_value=table_mock)
    table_mock.eq = MagicMock(return_value=table_mock)
    table_mock.single = MagicMock(return_value=table_mock)
    table_mock.order = MagicMock(return_value=table_mock)
    table_mock.ilike = MagicMock(return_value=table_mock)
    table_mock.range = MagicMock(return_value=table_mock)

    # Set up execute as an async mock that returns queued responses
    async def mock_execute(*args, **kwargs):
        if execute_responses:
            response_data = execute_responses.pop(0)
            return MockResponse(response_data)
        return MockResponse(None)

    table_mock.execute = AsyncMock(side_effect=mock_execute)

    # Always return the same table mock
    client.table = MagicMock(return_value=table_mock)
    # Expose the queue so tests can configure responses
    client._execute_responses = execute_responses

    return client


@pytest.fixture
def sample_document_response():
    """Sample document response from DB"""
    now = datetime.now(timezone.utc).isoformat()
    return {
        "id": "doc-001",
        "org_id": "test-org-001",
        "filename": "test.pdf",
        "doc_type": "보고서",
        "doc_subtype": None,
        "storage_path": "test-org-001/doc-001/test.pdf",
        "processing_status": "extracting",
        "total_chars": 0,
        "chunk_count": 0,
        "error_message": None,
        "extracted_text": None,
        "created_at": now,
        "updated_at": now,
    }
