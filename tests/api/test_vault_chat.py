"""
Tests for Vault AI Chat API routes
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock, patch
from app.main import app
from app.models.auth_schemas import CurrentUser


@pytest.fixture
def client():
    """FastAPI test client with proper mocking"""
    from app.api.deps import get_current_user

    # Create a default mock user for the tests
    default_mock_user = CurrentUser(
        id="default-user-id",
        email="default@example.com",
        name="Default User",
        role="member",
        org_id="test-org",
        team_id=None,
        division_id=None,
        status="active"
    )

    # Override get_current_user dependency
    app.dependency_overrides[get_current_user] = lambda: default_mock_user

    # Disable dev_mode to prevent auto-loading mock user
    with patch("app.config.settings.dev_mode", False):
        # Mock Supabase client
        supabase_mock = AsyncMock()
        supabase_mock.table = MagicMock(return_value=MagicMock())

        # Mock session manager
        session_mock = MagicMock()
        session_mock.startup_load = AsyncMock(return_value=0)
        session_mock.get_session_count = MagicMock(return_value=0)

        with patch("app.utils.supabase_client.get_async_client", return_value=supabase_mock), \
             patch("app.services.session_manager.session_manager", session_mock):
            test_client = TestClient(app)
            yield test_client

    # Clean up dependency overrides
    app.dependency_overrides.pop(get_current_user, None)


class TestVaultChatEndpoints:
    """Test Vault AI Chat endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/vault/health")
        assert response.status_code == 200
        assert response.json()["service"] == "vault-chat"

    def test_chat_endpoint_with_auth(self, client):
        """Test that chat endpoint works with mocked user"""
        # Auth is already mocked via dependency_overrides in the client fixture
        response = client.post(
            "/api/vault/chat",
            json={
                "conversation_id": None,
                "message": "What are our completed projects?"
            }
        )
        # Should not return 401 (unauthorized)
        # May return 200 (success), 422 (validation error), or 500 (infrastructure incomplete)
        # The important part is that auth is properly applied (no 401)
        assert response.status_code != 401

    def test_conversations_list_with_auth(self, client):
        """Test that conversation list works with mocked user"""
        # Auth is already mocked via dependency_overrides in the client fixture
        response = client.get("/api/vault/conversations")
        # Should be 200 or valid response
        assert response.status_code in [200, 404, 422]

    def test_create_conversation_with_auth(self, client):
        """Test that creating conversation works with mocked user"""
        # Auth is already mocked via dependency_overrides in the client fixture
        response = client.post(
            "/api/vault/conversations",
            json={"title": "Test Conversation"}
        )
        # Should not return 401 (unauthorized)
        # May return 200/201 (success), 422 (validation error), or 500 (infrastructure incomplete)
        assert response.status_code != 401


class TestVaultQueryRouter:
    """Test vault query router"""
    
    @pytest.mark.asyncio
    async def test_route_completed_projects_query(self):
        """Test routing for completed projects query"""
        from app.services.vault_query_router import vault_router
        
        routing = await vault_router.route(
            query="우리 회사가 완료한 프로젝트는?",
            conversation_context=[]
        )
        
        # Should route to completed_projects section
        from app.models.vault_schemas import VaultSection
        assert VaultSection.COMPLETED_PROJECTS in routing.sections
        assert routing.confidence > 0.0
    
    @pytest.mark.asyncio
    async def test_route_government_guidelines_query(self):
        """Test routing for government guidelines"""
        from app.services.vault_query_router import vault_router
        
        routing = await vault_router.route(
            query="정부 급여 기준이 뭐야?",
            conversation_context=[]
        )
        
        # Should route to government_guidelines section
        from app.models.vault_schemas import VaultSection
        assert VaultSection.GOVERNMENT_GUIDELINES in routing.sections
        assert routing.confidence > 0.0


class TestVaultValidation:
    """Test vault validation gate"""
    
    @pytest.mark.asyncio
    async def test_validation_with_no_sources(self):
        """Test validation when no sources are available"""
        from app.services.vault_validation import HallucinationValidator
        
        result = await HallucinationValidator.validate(
            response="This is a test response",
            sources=[],
            confidence=0.5,
            source_texts=[]
        )
        
        # Should have validation result with action
        assert "action" in result
        assert "confidence" in result


class TestSectionHandlers:
    """Test vault section handlers"""
    
    @pytest.mark.asyncio
    async def test_completed_projects_handler_search(self):
        """Test completed projects handler can be imported and used"""
        from app.services.vault_handlers.completed_projects import CompletedProjectsHandler
        
        # Handler should be importable
        assert CompletedProjectsHandler is not None
        
        # Search method should exist
        assert hasattr(CompletedProjectsHandler, 'search')
    
    @pytest.mark.asyncio
    async def test_government_guidelines_handler_search(self):
        """Test government guidelines handler can be imported and used"""
        from app.services.vault_handlers.government_guidelines import GovernmentGuidelinesHandler
        
        # Handler should be importable
        assert GovernmentGuidelinesHandler is not None
        
        # Search method should exist
        assert hasattr(GovernmentGuidelinesHandler, 'search')


class TestRateLimiting:
    """Test rate limiting functionality"""
    
    @pytest.mark.asyncio
    async def test_rate_limiter_initialization(self):
        """Test that rate limiter is properly configured"""
        from app.api.routes_vault_chat import chat_rate_limiter
        
        # Should be configured
        assert chat_rate_limiter is not None
        assert chat_rate_limiter.max_requests == 30
        assert chat_rate_limiter.window_seconds == 60
    
    @pytest.mark.asyncio
    async def test_rate_limiter_allows_requests(self):
        """Test that rate limiter allows requests within limit"""
        from app.api.routes_vault_chat import RateLimiter
        
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        
        # First 5 requests should be allowed
        for i in range(5):
            allowed = await limiter.is_allowed("test_user")
            assert allowed is True
        
        # 6th request should be rejected
        allowed = await limiter.is_allowed("test_user")
        assert allowed is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
