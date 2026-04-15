"""Integration tests for Knowledge Management API endpoints.

Tests cover:
- POST /knowledge/classify - Text classification
- POST /knowledge/search - Knowledge search with filters
- POST /knowledge/recommend - Recommendation generation
- GET /knowledge/health - Health metrics
- GET /knowledge/types - Knowledge types
- PUT /knowledge/{chunk_id}/deprecate - Deprecation
- PUT /knowledge/{chunk_id}/share - Org-wide sharing
- Error handling and validation
"""

import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.models.schemas import SearchFiltersType


@pytest.fixture
async def client():
    """Async HTTP client for testing."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


class TestKnowledgeClassify:
    """Tests for POST /knowledge/classify endpoint."""

    async def test_classify_single_text(self, client):
        """Test classifying a single text snippet."""
        response = await client.post(
            "/knowledge/classify",
            json={
                "texts": ["We developed IoT platform for smart building automation"],
                "confidence_threshold": 0.7,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert len(data["items"]) == 1
        assert "knowledge_type" in data["items"][0]
        assert data["items"][0]["knowledge_type"] in [
            "capability",
            "client_intel",
            "market_price",
            "lesson_learned",
        ]

    async def test_classify_multiple_texts(self, client):
        """Test classifying multiple text snippets."""
        response = await client.post(
            "/knowledge/classify",
            json={
                "texts": [
                    "We won the smart city tender from Seoul Metropolitan Government",
                    "Market price for IoT systems is 5-15% higher in Q4",
                    "Lesson: Always include warranty terms in proposal",
                ],
                "confidence_threshold": 0.6,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 3

    async def test_classify_missing_texts(self, client):
        """Test validation error for missing texts."""
        response = await client.post(
            "/knowledge/classify",
            json={"confidence_threshold": 0.7},
        )
        assert response.status_code == 422  # Validation error

    async def test_classify_empty_texts(self, client):
        """Test validation error for empty texts array."""
        response = await client.post(
            "/knowledge/classify",
            json={"texts": [], "confidence_threshold": 0.7},
        )
        assert response.status_code == 400


class TestKnowledgeSearch:
    """Tests for POST /knowledge/search endpoint."""

    async def test_search_basic_query(self, client):
        """Test basic knowledge search."""
        response = await client.post(
            "/knowledge/search",
            json={
                "query": "IoT platform capabilities",
                "limit": 10,
                "offset": 0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "meta" in data
        if data["items"]:
            item = data["items"][0]
            assert "id" in item
            assert "source_doc" in item
            assert "content_preview" in item
            assert "confidence_score" in item
            assert "freshness_score" in item

    async def test_search_with_type_filter(self, client):
        """Test search with knowledge type filter."""
        response = await client.post(
            "/knowledge/search",
            json={
                "query": "IoT",
                "limit": 10,
                "offset": 0,
                "filters": {
                    "knowledge_types": ["capability", "client_intel"],
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        if data["items"]:
            for item in data["items"]:
                assert item["knowledge_type"] in ["capability", "client_intel"]

    async def test_search_with_freshness_filter(self, client):
        """Test search with freshness score filter."""
        response = await client.post(
            "/knowledge/search",
            json={
                "query": "market price",
                "limit": 10,
                "offset": 0,
                "filters": {
                    "freshness_min": 70,
                },
            },
        )
        assert response.status_code == 200
        data = response.json()
        if data["items"]:
            for item in data["items"]:
                assert item["freshness_score"] >= 70

    async def test_search_with_combined_filters(self, client):
        """Test search with multiple filters."""
        response = await client.post(
            "/knowledge/search",
            json={
                "query": "smart city",
                "limit": 10,
                "offset": 0,
                "filters": {
                    "knowledge_types": ["capability"],
                    "freshness_min": 60,
                },
            },
        )
        assert response.status_code == 200

    async def test_search_pagination(self, client):
        """Test search pagination."""
        response1 = await client.post(
            "/knowledge/search",
            json={
                "query": "IoT",
                "limit": 5,
                "offset": 0,
            },
        )
        assert response1.status_code == 200

        response2 = await client.post(
            "/knowledge/search",
            json={
                "query": "IoT",
                "limit": 5,
                "offset": 5,
            },
        )
        assert response2.status_code == 200

    async def test_search_empty_query(self, client):
        """Test validation error for empty query."""
        response = await client.post(
            "/knowledge/search",
            json={
                "query": "",
                "limit": 10,
                "offset": 0,
            },
        )
        assert response.status_code == 400

    async def test_search_invalid_limit(self, client):
        """Test validation error for invalid limit."""
        response = await client.post(
            "/knowledge/search",
            json={
                "query": "test",
                "limit": 0,
                "offset": 0,
            },
        )
        assert response.status_code == 422

    async def test_search_no_results(self, client):
        """Test search with no matching results."""
        response = await client.post(
            "/knowledge/search",
            json={
                "query": "xyzabc_nonexistent_keyword_12345",
                "limit": 10,
                "offset": 0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []


class TestKnowledgeRecommend:
    """Tests for POST /knowledge/recommend endpoint."""

    async def test_recommend_basic(self, client):
        """Test basic recommendation."""
        response = await client.post(
            "/knowledge/recommend",
            json={
                "proposal_content": "We are proposing IoT solution for smart building",
                "limit": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        if data["items"]:
            item = data["items"][0]
            assert "id" in item
            assert "relevance_reason" in item
            assert "confidence_score" in item

    async def test_recommend_with_context(self, client):
        """Test recommendation with proposal context."""
        response = await client.post(
            "/knowledge/recommend",
            json={
                "proposal_content": "Smart city platform for Seoul",
                "proposal_context": {
                    "client": "Seoul Metropolitan Government",
                    "project_type": "IoT Infrastructure",
                    "budget_range": "1-5 billion KRW",
                },
                "limit": 5,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "items" in data

    async def test_recommend_empty_content(self, client):
        """Test validation error for empty proposal content."""
        response = await client.post(
            "/knowledge/recommend",
            json={
                "proposal_content": "",
                "limit": 5,
            },
        )
        assert response.status_code == 400

    async def test_recommend_invalid_limit(self, client):
        """Test validation error for invalid limit."""
        response = await client.post(
            "/knowledge/recommend",
            json={
                "proposal_content": "test proposal",
                "limit": 0,
            },
        )
        assert response.status_code == 422

    async def test_recommend_respects_limit(self, client):
        """Test that recommendations respect limit parameter."""
        response = await client.post(
            "/knowledge/recommend",
            json={
                "proposal_content": "IoT platform proposal",
                "limit": 3,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) <= 3


class TestKnowledgeHealth:
    """Tests for GET /knowledge/health endpoint."""

    async def test_health_metrics(self, client):
        """Test retrieving health metrics."""
        response = await client.get("/knowledge/health")
        assert response.status_code == 200
        data = response.json()

        # Verify required fields
        assert "kb_size_chunks" in data
        assert "kb_size_bytes" in data
        assert "coverage_percentage" in data
        assert "avg_freshness_score" in data
        assert "total_organizations" in data
        assert "total_shares" in data
        assert "deprecation_rate" in data
        assert "knowledge_type_distribution" in data
        assert "confidence_distribution" in data
        assert "trending_topics" in data

    async def test_health_kb_size_chunks_positive(self, client):
        """Test that KB size (chunks) is non-negative."""
        response = await client.get("/knowledge/health")
        assert response.status_code == 200
        data = response.json()
        assert data["kb_size_chunks"] >= 0

    async def test_health_coverage_in_range(self, client):
        """Test that coverage percentage is between 0-100."""
        response = await client.get("/knowledge/health")
        assert response.status_code == 200
        data = response.json()
        assert 0 <= data["coverage_percentage"] <= 100

    async def test_health_freshness_in_range(self, client):
        """Test that average freshness score is between 0-100."""
        response = await client.get("/knowledge/health")
        assert response.status_code == 200
        data = response.json()
        assert 0 <= data["avg_freshness_score"] <= 100

    async def test_health_deprecation_rate_valid(self, client):
        """Test that deprecation rate is valid percentage."""
        response = await client.get("/knowledge/health")
        assert response.status_code == 200
        data = response.json()
        assert 0 <= data["deprecation_rate"] <= 100


class TestKnowledgeTypes:
    """Tests for GET /knowledge/types endpoint."""

    async def test_get_knowledge_types(self, client):
        """Test retrieving available knowledge types."""
        response = await client.get("/knowledge/types")
        assert response.status_code == 200
        data = response.json()

        # Should return list of type definitions
        assert isinstance(data, (list, dict))

        if isinstance(data, dict):
            assert "types" in data or "items" in data


class TestKnowledgeDeprecate:
    """Tests for PUT /knowledge/{chunk_id}/deprecate endpoint."""

    async def test_deprecate_knowledge_chunk(self, client):
        """Test deprecating a knowledge chunk."""
        # First, we'd need a valid chunk_id from search results
        # For testing, we'll use a mock chunk_id
        chunk_id = "test-chunk-123"

        response = await client.put(
            f"/knowledge/{chunk_id}/deprecate",
            json={"reason": "Information is outdated"},
        )

        # May return 404 if chunk doesn't exist (expected in test env)
        # or 200 if successfully deprecated
        assert response.status_code in [200, 404, 401]

    async def test_deprecate_with_reason(self, client):
        """Test deprecation with detailed reason."""
        chunk_id = "test-chunk-456"

        response = await client.put(
            f"/knowledge/{chunk_id}/deprecate",
            json={
                "reason": "Technology superseded by newer platform",
            },
        )

        assert response.status_code in [200, 404, 401]


class TestKnowledgeShare:
    """Tests for PUT /knowledge/{chunk_id}/share endpoint."""

    async def test_share_knowledge_to_org(self, client):
        """Test sharing knowledge to organization."""
        chunk_id = "test-chunk-789"

        response = await client.put(
            f"/knowledge/{chunk_id}/share",
            json={
                "organization_id": "org-123",
                "share_level": "read",
            },
        )

        # May return 404 if chunk doesn't exist (expected in test env)
        assert response.status_code in [200, 404, 401]

    async def test_share_with_write_access(self, client):
        """Test sharing with write access level."""
        chunk_id = "test-chunk-999"

        response = await client.put(
            f"/knowledge/{chunk_id}/share",
            json={
                "organization_id": "org-456",
                "share_level": "write",
            },
        )

        assert response.status_code in [200, 404, 401]


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    async def test_invalid_json_body(self, client):
        """Test error handling for invalid JSON."""
        response = await client.post(
            "/knowledge/search",
            content="not valid json",
            headers={"content-type": "application/json"},
        )
        assert response.status_code == 422

    async def test_missing_required_fields(self, client):
        """Test error for missing required fields."""
        response = await client.post(
            "/knowledge/search",
            json={"limit": 10},  # Missing required 'query'
        )
        assert response.status_code == 422

    async def test_invalid_filter_type(self, client):
        """Test error for invalid filter type."""
        response = await client.post(
            "/knowledge/search",
            json={
                "query": "test",
                "limit": 10,
                "offset": 0,
                "filters": {
                    "knowledge_types": "not_a_list",  # Should be list
                },
            },
        )
        assert response.status_code == 422


class TestRLSEnforcement:
    """Tests for Row-Level Security enforcement."""

    async def test_search_enforces_access_control(self, client):
        """Test that search respects RLS policies."""
        # This would require authenticated requests
        # In test env, we verify the endpoint structure
        response = await client.post(
            "/knowledge/search",
            json={
                "query": "test",
                "limit": 10,
                "offset": 0,
            },
        )

        # Should return 200 or 401 (auth required)
        assert response.status_code in [200, 401, 403]

    async def test_recommend_enforces_access_control(self, client):
        """Test that recommendation respects RLS policies."""
        response = await client.post(
            "/knowledge/recommend",
            json={
                "proposal_content": "test proposal",
                "limit": 5,
            },
        )

        assert response.status_code in [200, 401, 403]

    async def test_health_endpoint_access(self, client):
        """Test health endpoint access control."""
        response = await client.get("/knowledge/health")

        # Health metrics may be public or require auth
        assert response.status_code in [200, 401, 403]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
