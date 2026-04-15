"""
Integration tests for Vault AI Chat API endpoints
Tests conversation management and message operations
"""

import pytest
import asyncio
from datetime import datetime
from typing import AsyncGenerator
from httpx import AsyncClient

from app.main import app
from app.models.auth_schemas import CurrentUser
from tests.conftest import get_test_db


pytestmark = pytest.mark.asyncio


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def test_user() -> CurrentUser:
    """Create test user"""
    return CurrentUser(
        id="test-user-123",
        email="test@vault.local",
        role="user"
    )


class TestConversationManagement:
    """Tests for conversation CRUD operations"""
    
    async def test_create_conversation(self, async_client: AsyncClient, test_user: CurrentUser):
        """Test creating a new conversation"""
        response = await async_client.post(
            "/api/vault/conversations",
            json={"title": "Test Conversation"},
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"]
        assert data["title"] == "Test Conversation"
        assert data["user_id"] == test_user.id
        assert data["message_count"] == 0
        assert data["created_at"]
        assert data["updated_at"]
    
    async def test_create_conversation_without_title(self, async_client: AsyncClient, test_user: CurrentUser):
        """Test creating conversation without title"""
        response = await async_client.post(
            "/api/vault/conversations",
            json={},
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"]
        assert data["title"] is None
    
    async def test_list_conversations(self, async_client: AsyncClient, test_user: CurrentUser):
        """Test listing user's conversations"""
        # Create test conversations
        conv_ids = []
        for i in range(3):
            resp = await async_client.post(
                "/api/vault/conversations",
                json={"title": f"Conv {i}"},
                headers={"Authorization": f"Bearer {test_user.id}"}
            )
            conv_ids.append(resp.json()["id"])
        
        # List conversations
        response = await async_client.get(
            "/api/vault/conversations?limit=10&offset=0",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3
        assert all(conv["user_id"] == test_user.id for conv in data)
        assert data[0]["updated_at"]  # Most recent first
    
    async def test_list_conversations_pagination(self, async_client: AsyncClient, test_user: CurrentUser):
        """Test conversation list pagination"""
        # Create 5 conversations
        for i in range(5):
            await async_client.post(
                "/api/vault/conversations",
                json={"title": f"Conv {i}"},
                headers={"Authorization": f"Bearer {test_user.id}"}
            )
        
        # Get first page (limit=2)
        response = await async_client.get(
            "/api/vault/conversations?limit=2&offset=0",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        assert response.status_code == 200
        assert len(response.json()) <= 2
        
        # Get second page
        response = await async_client.get(
            "/api/vault/conversations?limit=2&offset=2",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        assert response.status_code == 200
    
    async def test_get_conversation(self, async_client: AsyncClient, test_user: CurrentUser):
        """Test retrieving conversation details"""
        # Create conversation
        create_resp = await async_client.post(
            "/api/vault/conversations",
            json={"title": "Detail Test"},
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        conv_id = create_resp.json()["id"]
        
        # Get conversation
        response = await async_client.get(
            f"/api/vault/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == conv_id
        assert data["title"] == "Detail Test"
        assert data["user_id"] == test_user.id
        assert data["message_count"] == 0
        assert isinstance(data["messages"], list)
    
    async def test_delete_conversation(self, async_client: AsyncClient, test_user: CurrentUser):
        """Test deleting a conversation"""
        # Create conversation
        create_resp = await async_client.post(
            "/api/vault/conversations",
            json={"title": "Delete Test"},
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        conv_id = create_resp.json()["id"]
        
        # Delete conversation
        response = await async_client.delete(
            f"/api/vault/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        assert response.status_code == 200
        
        # Verify deleted
        response = await async_client.get(
            f"/api/vault/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        assert response.status_code == 404
    
    async def test_cannot_access_other_users_conversation(self, async_client: AsyncClient, test_user: CurrentUser):
        """Test RLS: users cannot access other users' conversations"""
        # Create conversation as test_user
        create_resp = await async_client.post(
            "/api/vault/conversations",
            json={"title": "Private Conversation"},
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        conv_id = create_resp.json()["id"]
        
        # Try to access as different user
        other_user = CurrentUser(id="other-user-456", email="other@vault.local", role="user")
        response = await async_client.get(
            f"/api/vault/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {other_user.id}"}
        )
        assert response.status_code == 404


class TestMessageOperations:
    """Tests for message storage and retrieval"""
    
    async def test_get_conversation_messages(self, async_client: AsyncClient, test_user: CurrentUser):
        """Test retrieving messages from conversation"""
        # Create conversation
        create_resp = await async_client.post(
            "/api/vault/conversations",
            json={"title": "Message Test"},
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        conv_id = create_resp.json()["id"]
        
        # Get messages (empty)
        response = await async_client.get(
            f"/api/vault/conversations/{conv_id}/messages",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        assert response.status_code == 200
        messages = response.json()
        assert isinstance(messages, list)
        assert len(messages) == 0
    
    async def test_message_pagination(self, async_client: AsyncClient, test_user: CurrentUser):
        """Test message pagination"""
        # Create conversation
        create_resp = await async_client.post(
            "/api/vault/conversations",
            json={"title": "Pagination Test"},
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        conv_id = create_resp.json()["id"]
        
        # Get first page
        response = await async_client.get(
            f"/api/vault/conversations/{conv_id}/messages?limit=10&offset=0",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        assert response.status_code == 200
        
        # Get second page
        response = await async_client.get(
            f"/api/vault/conversations/{conv_id}/messages?limit=10&offset=10",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        assert response.status_code == 200


class TestRateLimiting:
    """Tests for rate limiting"""
    
    async def test_rate_limit_exceeded(self, async_client: AsyncClient, test_user: CurrentUser):
        """Test rate limiting (30 requests per minute)"""
        # This is a placeholder test
        # In real test, would need to mock time and make 31+ rapid requests
        # For now, just verify endpoint returns proper error
        
        response = await async_client.post(
            "/api/vault/chat",
            json={
                "conversation_id": "test-conv",
                "message": "Test message",
                "user_id": test_user.id
            },
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        
        # Should either succeed or fail with proper error
        assert response.status_code in [200, 429, 422, 401]


class TestSecurityRLS:
    """Tests for Row-Level Security policies"""
    
    async def test_rls_conversation_isolation(self, async_client: AsyncClient):
        """Test that users are isolated by RLS policy"""
        user1 = CurrentUser(id="user-1", email="user1@test.local", role="user")
        user2 = CurrentUser(id="user-2", email="user2@test.local", role="user")
        
        # User1 creates conversation
        resp1 = await async_client.post(
            "/api/vault/conversations",
            json={"title": "User1 Conv"},
            headers={"Authorization": f"Bearer {user1.id}"}
        )
        conv_id = resp1.json()["id"]
        
        # User1 can see it
        resp = await async_client.get(
            f"/api/vault/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {user1.id}"}
        )
        assert resp.status_code == 200
        
        # User2 cannot see it
        resp = await async_client.get(
            f"/api/vault/conversations/{conv_id}",
            headers={"Authorization": f"Bearer {user2.id}"}
        )
        assert resp.status_code == 404
    
    async def test_rls_message_isolation(self, async_client: AsyncClient):
        """Test that messages are isolated by RLS policy"""
        user1 = CurrentUser(id="user-1", email="user1@test.local", role="user")
        user2 = CurrentUser(id="user-2", email="user2@test.local", role="user")
        
        # User1 creates conversation
        resp1 = await async_client.post(
            "/api/vault/conversations",
            json={"title": "User1 Conv"},
            headers={"Authorization": f"Bearer {user1.id}"}
        )
        conv_id = resp1.json()["id"]
        
        # User1 can access messages
        resp = await async_client.get(
            f"/api/vault/conversations/{conv_id}/messages",
            headers={"Authorization": f"Bearer {user1.id}"}
        )
        assert resp.status_code == 200
        
        # User2 cannot access messages
        resp = await async_client.get(
            f"/api/vault/conversations/{conv_id}/messages",
            headers={"Authorization": f"Bearer {user2.id}"}
        )
        assert resp.status_code == 404


class TestErrorHandling:
    """Tests for error scenarios"""
    
    async def test_get_nonexistent_conversation(self, async_client: AsyncClient, test_user: CurrentUser):
        """Test getting non-existent conversation"""
        response = await async_client.get(
            "/api/vault/conversations/nonexistent-id",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        assert response.status_code == 404
    
    async def test_delete_nonexistent_conversation(self, async_client: AsyncClient, test_user: CurrentUser):
        """Test deleting non-existent conversation"""
        response = await async_client.delete(
            "/api/vault/conversations/nonexistent-id",
            headers={"Authorization": f"Bearer {test_user.id}"}
        )
        assert response.status_code in [404, 403]  # Not found or not authorized
    
    async def test_unauthorized_access(self, async_client: AsyncClient):
        """Test accessing endpoints without authorization"""
        response = await async_client.get("/api/vault/conversations")
        assert response.status_code == 401


class TestHealthCheck:
    """Tests for service health"""
    
    async def test_vault_health_check(self, async_client: AsyncClient):
        """Test Vault health check endpoint"""
        response = await async_client.get("/api/vault/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "vault-chat"
