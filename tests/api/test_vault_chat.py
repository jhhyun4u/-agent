"""
Tests for Vault AI Chat API routes
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)


class TestVaultChatEndpoints:
    """Test Vault AI Chat endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/vault/health")
        assert response.status_code == 200
        assert response.json()["service"] == "vault-chat"
    
    @pytest.mark.asyncio
    async def test_chat_endpoint_requires_auth(self, client):
        """Test that chat endpoint requires authentication"""
        # Without auth token, should return 401
        response = client.post(
            "/api/vault/chat",
            json={
                "conversation_id": None,
                "message": "What are our completed projects?"
            }
        )
        assert response.status_code == 401
    
    def test_conversations_list_requires_auth(self, client):
        """Test that conversation list requires authentication"""
        response = client.get("/api/vault/conversations")
        assert response.status_code == 401
    
    def test_create_conversation_requires_auth(self, client):
        """Test that creating conversation requires authentication"""
        response = client.post(
            "/api/vault/conversations",
            json={"title": "Test Conversation"}
        )
        assert response.status_code == 401


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
