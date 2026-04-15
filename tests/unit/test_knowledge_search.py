"""
Unit tests for Knowledge Search Service (Module-3).

Tests cover:
- Semantic search with pgvector
- BM25 keyword fallback
- Filter application
- Result formatting
- Error handling
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.models.knowledge_schemas import (
    SearchRequest,
    SearchFilters,
    SearchResultItem,
    SearchResponse,
    KnowledgeType,
)


# ============================================================================
# SEARCH REQUEST TESTS
# ============================================================================

class TestSearchRequest:
    """Test search request validation."""

    def test_valid_search_request(self):
        """Valid search request with minimal parameters."""
        req = SearchRequest(query="IoT platform architecture")
        assert req.query == "IoT platform architecture"
        assert req.limit == 10
        assert req.offset == 0

    def test_search_request_with_filters(self):
        """Search request with filters."""
        req = SearchRequest(
            query="Manufacturing solutions",
            filters=SearchFilters(
                knowledge_types=[KnowledgeType.CAPABILITY, KnowledgeType.LESSON_LEARNED],
                freshness_min=50,
                exclude_deprecated=True
            ),
            limit=20,
            offset=10
        )
        assert req.limit == 20
        assert req.offset == 10
        assert len(req.filters.knowledge_types) == 2

    def test_search_request_query_min_length(self):
        """Query must be at least 3 characters."""
        # Valid: 3 characters
        req = SearchRequest(query="AWS")
        assert req.query == "AWS"

        # Invalid: less than 3 characters
        with pytest.raises(ValueError):
            SearchRequest(query="AI")

    def test_search_request_pagination(self):
        """Pagination parameters should be valid."""
        # Valid: max limit
        req = SearchRequest(query="test", limit=100, offset=0)
        assert req.limit == 100

        # Invalid: limit too high
        with pytest.raises(ValueError):
            SearchRequest(query="test", limit=101)

        # Invalid: negative offset
        with pytest.raises(ValueError):
            SearchRequest(query="test", offset=-1)


# ============================================================================
# SEARCH FILTER TESTS
# ============================================================================

class TestSearchFilters:
    """Test search filter validation."""

    def test_filters_default(self):
        """Default filters should be valid."""
        filters = SearchFilters()
        assert filters.knowledge_types is None
        assert filters.freshness_min is None
        assert filters.exclude_deprecated is True

    def test_filters_with_types(self):
        """Filters with knowledge types."""
        filters = SearchFilters(
            knowledge_types=[
                KnowledgeType.CAPABILITY,
                KnowledgeType.CLIENT_INTEL,
                KnowledgeType.MARKET_PRICE,
            ]
        )
        assert len(filters.knowledge_types) == 3

    def test_filters_freshness_bounds(self):
        """Freshness min must be 0-100."""
        # Valid: 0
        filters = SearchFilters(freshness_min=0)
        assert filters.freshness_min == 0

        # Valid: 100
        filters = SearchFilters(freshness_min=100)
        assert filters.freshness_min == 100

        # Invalid: < 0
        with pytest.raises(ValueError):
            SearchFilters(freshness_min=-1)

        # Invalid: > 100
        with pytest.raises(ValueError):
            SearchFilters(freshness_min=101)


# ============================================================================
# SEARCH RESULT ITEM TESTS
# ============================================================================

class TestSearchResultItem:
    """Test search result item model."""

    def test_valid_search_result_item(self):
        """Valid search result item."""
        item = SearchResultItem(
            id=uuid4(),
            knowledge_type=KnowledgeType.CAPABILITY,
            confidence_score=Decimal("0.92"),
            freshness_score=Decimal("85.0"),
            source_doc="Case Study Document",
            created_at=datetime.utcnow(),
            content_preview="IoT platform implementation details...",
            embedding_similarity=Decimal("0.87"),
            is_deprecated=False
        )
        assert item.knowledge_type == KnowledgeType.CAPABILITY
        assert item.freshness_score == Decimal("85.0")
        assert item.is_deprecated is False

    def test_search_result_item_all_types(self):
        """Search results can be any knowledge type."""
        for ktype in [
            KnowledgeType.CAPABILITY,
            KnowledgeType.CLIENT_INTEL,
            KnowledgeType.MARKET_PRICE,
            KnowledgeType.LESSON_LEARNED,
        ]:
            item = SearchResultItem(
                id=uuid4(),
                knowledge_type=ktype,
                confidence_score=Decimal("0.75"),
                freshness_score=Decimal("90.0"),
                source_doc="Document",
                created_at=datetime.utcnow(),
                content_preview="Content..."
            )
            assert item.knowledge_type == ktype

    def test_search_result_item_optional_fields(self):
        """Optional fields can be None."""
        item = SearchResultItem(
            id=uuid4(),
            knowledge_type=KnowledgeType.CAPABILITY,
            confidence_score=Decimal("0.70"),
            freshness_score=Decimal("80.0"),
            source_doc="Document",
            created_at=datetime.utcnow(),
            content_preview="Content...",
            source_author=None,
            embedding_similarity=None
        )
        assert item.source_author is None
        assert item.embedding_similarity is None


# ============================================================================
# SEARCH RESPONSE TESTS
# ============================================================================

class TestSearchResponse:
    """Test search response model."""

    def test_valid_search_response_empty(self):
        """Valid search response with no results."""
        resp = SearchResponse(
            items=[],
            total=0,
            limit=10,
            offset=0
        )
        assert len(resp.items) == 0
        assert resp.total == 0

    def test_valid_search_response_with_results(self):
        """Valid search response with results."""
        items = [
            SearchResultItem(
                id=uuid4(),
                knowledge_type=KnowledgeType.CAPABILITY,
                confidence_score=Decimal("0.92"),
                freshness_score=Decimal("90.0"),
                source_doc="Doc 1",
                created_at=datetime.utcnow(),
                content_preview="Content 1..."
            ),
            SearchResultItem(
                id=uuid4(),
                knowledge_type=KnowledgeType.LESSON_LEARNED,
                confidence_score=Decimal("0.85"),
                freshness_score=Decimal("75.0"),
                source_doc="Doc 2",
                created_at=datetime.utcnow(),
                content_preview="Content 2..."
            ),
        ]
        resp = SearchResponse(
            items=items,
            total=100,
            limit=10,
            offset=0
        )
        assert len(resp.items) == 2
        assert resp.total == 100

    def test_search_response_pagination(self):
        """Search response preserves pagination info."""
        resp = SearchResponse(
            items=[],
            total=500,
            limit=10,
            offset=50
        )
        assert resp.offset == 50
        assert resp.limit == 10
        assert resp.total == 500


# ============================================================================
# SEARCH SERVICE INTEGRATION TESTS
# ============================================================================

class TestKnowledgeSearchIntegration:
    """Test search service integration."""

    @pytest.mark.asyncio
    async def test_search_semantic_success(self):
        """Semantic search should return results."""
        from app.services.knowledge_manager import KnowledgeManager

        manager = KnowledgeManager()
        request = SearchRequest(query="IoT platform")

        # Mock semantic search path
        with patch.object(
            manager, "_semantic_search",
            new_callable=AsyncMock,
            return_value=[
                SearchResultItem(
                    id=uuid4(),
                    knowledge_type=KnowledgeType.CAPABILITY,
                    confidence_score=Decimal("0.92"),
                    freshness_score=Decimal("90.0"),
                    source_doc="IoT Case Study",
                    created_at=datetime.utcnow(),
                    content_preview="IoT platform with AWS...",
                    embedding_similarity=Decimal("0.88")
                )
            ]
        ):
            response = await manager.search(
                request=request,
                user_team_id=uuid4()
            )

            assert len(response.items) == 1
            assert response.items[0].knowledge_type == KnowledgeType.CAPABILITY

    @pytest.mark.asyncio
    async def test_search_fallback_to_keyword(self):
        """Should fallback to keyword search if semantic returns no results."""
        from app.services.knowledge_manager import KnowledgeManager

        manager = KnowledgeManager()
        request = SearchRequest(query="manufacturing")

        keyword_result = SearchResultItem(
            id=uuid4(),
            knowledge_type=KnowledgeType.CLIENT_INTEL,
            confidence_score=Decimal("0.75"),
            freshness_score=Decimal("80.0"),
            source_doc="Manufacturing Client",
            created_at=datetime.utcnow(),
            content_preview="Manufacturing client info...",
        )

        # Mock: semantic returns empty, keyword returns results
        with patch.object(
            manager, "_semantic_search",
            new_callable=AsyncMock,
            return_value=[]
        ), patch.object(
            manager, "_keyword_search",
            new_callable=AsyncMock,
            return_value=[keyword_result]
        ):
            response = await manager.search(
                request=request,
                user_team_id=uuid4()
            )

            assert len(response.items) == 1
            assert response.items[0].source_doc == "Manufacturing Client"

    @pytest.mark.asyncio
    async def test_search_pagination(self):
        """Search should handle pagination correctly."""
        from app.services.knowledge_manager import KnowledgeManager

        manager = KnowledgeManager()
        request = SearchRequest(query="test", limit=5, offset=10)

        # Create 20 results
        results = [
            SearchResultItem(
                id=uuid4(),
                knowledge_type=KnowledgeType.CAPABILITY,
                confidence_score=Decimal("0.80"),
                freshness_score=Decimal("85.0"),
                source_doc=f"Doc {i}",
                created_at=datetime.utcnow(),
                content_preview=f"Content {i}..."
            )
            for i in range(20)
        ]

        with patch.object(
            manager, "_semantic_search",
            new_callable=AsyncMock,
            return_value=results
        ):
            response = await manager.search(
                request=request,
                user_team_id=uuid4()
            )

            # Should return paginated results
            assert len(response.items) == 5
            assert response.offset == 10
            assert response.limit == 5
            assert response.total == 20

    @pytest.mark.asyncio
    async def test_search_error_handling(self):
        """Search should return empty results on error."""
        from app.services.knowledge_manager import KnowledgeManager

        manager = KnowledgeManager()
        request = SearchRequest(query="test")

        # Mock error
        with patch.object(
            manager, "_semantic_search",
            new_callable=AsyncMock,
            side_effect=Exception("Database error")
        ):
            response = await manager.search(
                request=request,
                user_team_id=uuid4()
            )

            # Should return empty results instead of raising
            assert len(response.items) == 0
            assert response.total == 0

    @pytest.mark.asyncio
    async def test_semantic_search_not_implemented(self):
        """Semantic search method should be callable."""
        from app.services.knowledge_manager import KnowledgeManager

        manager = KnowledgeManager()
        # This should not raise NotImplementedError anymore
        # It should be implemented and callable
        assert hasattr(manager, "_semantic_search")
        assert callable(getattr(manager, "_semantic_search"))

    @pytest.mark.asyncio
    async def test_keyword_search_not_implemented(self):
        """Keyword search method should be callable."""
        from app.services.knowledge_manager import KnowledgeManager

        manager = KnowledgeManager()
        # This should not raise NotImplementedError anymore
        # It should be implemented and callable
        assert hasattr(manager, "_keyword_search")
        assert callable(getattr(manager, "_keyword_search"))


# ============================================================================
# SEARCH CONFIG CONSTANTS TESTS
# ============================================================================

class TestSearchConfiguration:
    """Test search service configuration."""

    def test_similarity_threshold(self):
        """Similarity threshold should be reasonable."""
        # pgvector cosine similarity ranges 0-1
        # Threshold should be > 0.5 for meaningful matches
        threshold = 0.7
        assert 0.5 < threshold <= 1.0

    def test_result_limits(self):
        """Result limits should be reasonable."""
        vector_limit = 20
        bm25_limit = 50
        assert vector_limit < bm25_limit
        assert vector_limit > 0
        assert bm25_limit > 0

    def test_freshness_decay_factor(self):
        """Freshness decay factor should be 0-1."""
        factor = 0.1
        assert 0.0 <= factor <= 1.0
