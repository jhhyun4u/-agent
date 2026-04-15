"""
Unit tests for Knowledge Recommendations (Module-4).

Tests cover:
- Recommendation request creation
- Recommendation result validation
- Context-aware ranking
- Fallback behavior
- Error handling
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.models.knowledge_schemas import (
    ProposalContext,
    RecommendationRequest,
    RecommendationResultItem,
    RecommendationResponse,
    KnowledgeType,
    SearchResponse,
    SearchResultItem,
)
from app.services.knowledge_manager import KnowledgeManager


# ============================================================================
# PROPOSAL CONTEXT TESTS
# ============================================================================

class TestProposalContext:
    """Test proposal context models."""

    def test_valid_proposal_context_minimal(self):
        """Minimal proposal context with only RFP summary."""
        context = ProposalContext(
            rfp_summary="IoT platform implementation for manufacturing client"
        )
        assert context.rfp_summary == "IoT platform implementation for manufacturing client"
        assert context.client_type is None
        assert context.bid_amount is None
        assert context.selected_strategy is None

    def test_valid_proposal_context_full(self):
        """Full proposal context with all fields."""
        context = ProposalContext(
            rfp_summary="Large-scale IoT platform for automotive manufacturer",
            client_type="automotive_manufacturing",
            bid_amount=5000000,
            selected_strategy="differentiation",
            additional_context="Client prefers cloud-native architecture"
        )
        assert context.rfp_summary == "Large-scale IoT platform for automotive manufacturer"
        assert context.client_type == "automotive_manufacturing"
        assert context.bid_amount == 5000000
        assert context.selected_strategy == "differentiation"
        assert context.additional_context == "Client prefers cloud-native architecture"


# ============================================================================
# RECOMMENDATION REQUEST TESTS
# ============================================================================

class TestRecommendationRequest:
    """Test recommendation request validation."""

    def test_valid_recommendation_request_default_limit(self):
        """Default limit should be 5."""
        context = ProposalContext(rfp_summary="Manufacturing IoT platform")
        req = RecommendationRequest(proposal_context=context)
        assert req.limit == 5

    def test_valid_recommendation_request_custom_limit(self):
        """Custom limit should be respected."""
        context = ProposalContext(rfp_summary="Manufacturing IoT platform")
        req = RecommendationRequest(proposal_context=context, limit=10)
        assert req.limit == 10

    def test_recommendation_request_limit_bounds(self):
        """Limit must be between 1 and 20."""
        context = ProposalContext(rfp_summary="Test RFP")

        # Valid: min
        req = RecommendationRequest(proposal_context=context, limit=1)
        assert req.limit == 1

        # Valid: max
        req = RecommendationRequest(proposal_context=context, limit=20)
        assert req.limit == 20

        # Invalid: too high
        with pytest.raises(ValueError):
            RecommendationRequest(proposal_context=context, limit=21)

        # Invalid: zero
        with pytest.raises(ValueError):
            RecommendationRequest(proposal_context=context, limit=0)


# ============================================================================
# RECOMMENDATION RESULT ITEM TESTS
# ============================================================================

class TestRecommendationResultItem:
    """Test recommendation result item model."""

    def test_valid_recommendation_item(self):
        """Valid recommendation item."""
        item = RecommendationResultItem(
            rank=1,
            chunk_id=uuid4(),
            knowledge_type=KnowledgeType.CAPABILITY,
            confidence_score=Decimal("0.85"),
            source_doc="IoT Architecture Case Study",
            content_preview="Implementation details of IoT platform...",
            relevance_reason="Directly matches required architecture pattern",
            freshness_score=Decimal("90.0"),
            match_type="semantic"
        )
        assert item.rank == 1
        assert item.knowledge_type == KnowledgeType.CAPABILITY
        assert item.relevance_reason == "Directly matches required architecture pattern"

    def test_recommendation_item_all_types(self):
        """Recommendations can be any knowledge type."""
        for ktype in [
            KnowledgeType.CAPABILITY,
            KnowledgeType.CLIENT_INTEL,
            KnowledgeType.MARKET_PRICE,
            KnowledgeType.LESSON_LEARNED,
        ]:
            item = RecommendationResultItem(
                rank=1,
                chunk_id=uuid4(),
                knowledge_type=ktype,
                confidence_score=Decimal("0.75"),
                source_doc="Document",
                content_preview="Content...",
                relevance_reason="Relevant",
                freshness_score=Decimal("80.0"),
            )
            assert item.knowledge_type == ktype

    def test_recommendation_item_rank_bounds(self):
        """Rank must be >= 1."""
        # Valid: 1
        item = RecommendationResultItem(
            rank=1,
            chunk_id=uuid4(),
            knowledge_type=KnowledgeType.CAPABILITY,
            confidence_score=Decimal("0.70"),
            source_doc="Doc",
            content_preview="Content",
            relevance_reason="Reason",
            freshness_score=Decimal("85.0"),
        )
        assert item.rank == 1

        # Valid: high rank
        item = RecommendationResultItem(
            rank=100,
            chunk_id=uuid4(),
            knowledge_type=KnowledgeType.CAPABILITY,
            confidence_score=Decimal("0.70"),
            source_doc="Doc",
            content_preview="Content",
            relevance_reason="Reason",
            freshness_score=Decimal("85.0"),
        )
        assert item.rank == 100


# ============================================================================
# RECOMMENDATION RESPONSE TESTS
# ============================================================================

class TestRecommendationResponse:
    """Test recommendation response model."""

    def test_valid_recommendation_response_empty(self):
        """Valid response with no recommendations."""
        resp = RecommendationResponse(
            items=[],
            context_matched=[],
            fallback_used=False
        )
        assert len(resp.items) == 0
        assert len(resp.context_matched) == 0
        assert resp.fallback_used is False

    def test_valid_recommendation_response_with_items(self):
        """Valid response with recommendations."""
        items = [
            RecommendationResultItem(
                rank=1,
                chunk_id=uuid4(),
                knowledge_type=KnowledgeType.CAPABILITY,
                confidence_score=Decimal("0.92"),
                source_doc="IoT Case Study",
                content_preview="Implementation details...",
                relevance_reason="Matches architecture needs",
                freshness_score=Decimal("90.0"),
            ),
            RecommendationResultItem(
                rank=2,
                chunk_id=uuid4(),
                knowledge_type=KnowledgeType.CLIENT_INTEL,
                confidence_score=Decimal("0.80"),
                source_doc="Client Profile",
                content_preview="Client information...",
                relevance_reason="Relevant to client type",
                freshness_score=Decimal("85.0"),
            ),
        ]
        resp = RecommendationResponse(
            items=items,
            context_matched=["architecture", "manufacturing"],
            fallback_used=False
        )
        assert len(resp.items) == 2
        assert resp.context_matched == ["architecture", "manufacturing"]


# ============================================================================
# KNOWLEDGE MANAGER RECOMMENDATION TESTS
# ============================================================================

class TestKnowledgeManagerRecommendations:
    """Test KnowledgeManager recommendation functionality."""

    @pytest.mark.asyncio
    async def test_recommend_success(self):
        """Recommendation engine generates ranked results."""
        manager = KnowledgeManager()
        proposal_context = ProposalContext(
            rfp_summary="Large-scale IoT platform for automotive manufacturer",
            client_type="automotive",
            bid_amount=5000000,
            selected_strategy="differentiation"
        )

        mock_search_results = SearchResponse(
            items=[
                SearchResultItem(
                    id=uuid4(),
                    knowledge_type=KnowledgeType.CAPABILITY,
                    confidence_score=Decimal("0.88"),
                    freshness_score=Decimal("92.0"),
                    source_doc="IoT Platform Architecture",
                    created_at=datetime.utcnow(),
                    content_preview="IoT architecture with AWS...",
                    embedding_similarity=Decimal("0.85"),
                ),
                SearchResultItem(
                    id=uuid4(),
                    knowledge_type=KnowledgeType.CLIENT_INTEL,
                    confidence_score=Decimal("0.75"),
                    freshness_score=Decimal("80.0"),
                    source_doc="Automotive Client Profiles",
                    created_at=datetime.utcnow(),
                    content_preview="Automotive industry profiles...",
                ),
            ],
            total=2,
            limit=20,
            offset=0
        )

        mock_claude_response = [
            {
                "chunk_id": str(mock_search_results.items[0].id),
                "relevance_score": 95,
                "match_reason": "Directly matches IoT architecture requirements",
                "matching_dimensions": ["architecture", "technology"]
            },
            {
                "chunk_id": str(mock_search_results.items[1].id),
                "relevance_score": 80,
                "match_reason": "Relevant to automotive client segment",
                "matching_dimensions": ["client_type", "industry"]
            }
        ]

        with patch.object(
            manager, "search",
            new_callable=AsyncMock,
            return_value=mock_search_results
        ), patch("app.services.knowledge_manager.claude_generate",
            new_callable=AsyncMock,
            return_value=mock_claude_response
        ):
            response = await manager.recommend(
                proposal_context=proposal_context,
                user_team_id=uuid4(),
                limit=5
            )

            assert len(response.items) == 2
            assert response.items[0].rank == 1
            assert response.items[1].rank == 2
            assert "architecture" in response.context_matched
            assert "client_type" in response.context_matched

    @pytest.mark.asyncio
    async def test_recommend_no_candidates(self):
        """Recommendation with no search candidates."""
        manager = KnowledgeManager()
        proposal_context = ProposalContext(
            rfp_summary="Very specific niche technology"
        )

        mock_search_results = SearchResponse(
            items=[],
            total=0,
            limit=20,
            offset=0
        )

        with patch.object(
            manager, "search",
            new_callable=AsyncMock,
            return_value=mock_search_results
        ):
            response = await manager.recommend(
                proposal_context=proposal_context,
                user_team_id=uuid4(),
                limit=5
            )

            assert len(response.items) == 0
            assert len(response.context_matched) == 0

    @pytest.mark.asyncio
    async def test_recommend_limit_respected(self):
        """Recommendation should respect limit parameter."""
        manager = KnowledgeManager()
        proposal_context = ProposalContext(
            rfp_summary="IoT platform"
        )

        # Create 10 mock search results
        mock_items = [
            SearchResultItem(
                id=uuid4(),
                knowledge_type=KnowledgeType.CAPABILITY,
                confidence_score=Decimal("0.85"),
                freshness_score=Decimal("90.0"),
                source_doc=f"Item {i}",
                created_at=datetime.utcnow(),
                content_preview=f"Content {i}...",
            )
            for i in range(10)
        ]

        mock_search_results = SearchResponse(
            items=mock_items,
            total=10,
            limit=20,
            offset=0
        )

        # Mock Claude response with all items ranked
        mock_claude_response = [
            {
                "chunk_id": str(item.id),
                "relevance_score": 80 + (9 - i),
                "match_reason": f"Match reason {i}",
                "matching_dimensions": ["dimension1"]
            }
            for i, item in enumerate(mock_items)
        ]

        with patch.object(
            manager, "search",
            new_callable=AsyncMock,
            return_value=mock_search_results
        ), patch("app.services.knowledge_manager.claude_generate",
            new_callable=AsyncMock,
            return_value=mock_claude_response
        ):
            response = await manager.recommend(
                proposal_context=proposal_context,
                user_team_id=uuid4(),
                limit=5
            )

            # Should return at most 5 items
            assert len(response.items) <= 5

    @pytest.mark.asyncio
    async def test_recommend_graceful_error_handling(self):
        """Recommendation should handle Claude errors gracefully."""
        manager = KnowledgeManager()
        proposal_context = ProposalContext(
            rfp_summary="IoT platform"
        )

        mock_search_results = SearchResponse(
            items=[
                SearchResultItem(
                    id=uuid4(),
                    knowledge_type=KnowledgeType.CAPABILITY,
                    confidence_score=Decimal("0.85"),
                    freshness_score=Decimal("90.0"),
                    source_doc="Item 1",
                    created_at=datetime.utcnow(),
                    content_preview="Content...",
                )
            ],
            total=1,
            limit=20,
            offset=0
        )

        with patch.object(
            manager, "search",
            new_callable=AsyncMock,
            return_value=mock_search_results
        ), patch("app.services.knowledge_manager.claude_generate",
            new_callable=AsyncMock,
            side_effect=Exception("Claude API error")
        ):
            response = await manager.recommend(
                proposal_context=proposal_context,
                user_team_id=uuid4(),
                limit=5
            )

            # Should return empty response on catastrophic error
            assert len(response.items) == 0
            # fallback_used only set to True when JSON parsing fails and we retry search
            # On other errors, we return empty without fallback
            assert response.fallback_used is False

    @pytest.mark.asyncio
    async def test_recommend_filtering_low_relevance(self):
        """Recommendations below 30% relevance should be excluded."""
        manager = KnowledgeManager()
        proposal_context = ProposalContext(
            rfp_summary="Specific proposal"
        )

        mock_search_results = SearchResponse(
            items=[
                SearchResultItem(
                    id=uuid4(),
                    knowledge_type=KnowledgeType.CAPABILITY,
                    confidence_score=Decimal("0.85"),
                    freshness_score=Decimal("90.0"),
                    source_doc="High relevance item",
                    created_at=datetime.utcnow(),
                    content_preview="Highly relevant...",
                ),
                SearchResultItem(
                    id=uuid4(),
                    knowledge_type=KnowledgeType.CAPABILITY,
                    confidence_score=Decimal("0.70"),
                    freshness_score=Decimal("80.0"),
                    source_doc="Low relevance item",
                    created_at=datetime.utcnow(),
                    content_preview="Low relevance...",
                ),
            ],
            total=2,
            limit=20,
            offset=0
        )

        mock_claude_response = [
            {
                "chunk_id": str(mock_search_results.items[0].id),
                "relevance_score": 85,
                "match_reason": "Highly relevant",
                "matching_dimensions": ["core_need"]
            },
            {
                "chunk_id": str(mock_search_results.items[1].id),
                "relevance_score": 15,  # Below threshold
                "match_reason": "Minimally relevant",
                "matching_dimensions": []
            }
        ]

        with patch.object(
            manager, "search",
            new_callable=AsyncMock,
            return_value=mock_search_results
        ), patch("app.services.knowledge_manager.claude_generate",
            new_callable=AsyncMock,
            return_value=mock_claude_response
        ):
            response = await manager.recommend(
                proposal_context=proposal_context,
                user_team_id=uuid4(),
                limit=5
            )

            # Should only include high-relevance item
            assert len(response.items) == 1
            assert response.items[0].relevance_reason == "Highly relevant"


# ============================================================================
# CONTEXT MATCHING TESTS
# ============================================================================

class TestContextMatching:
    """Test context dimension matching in recommendations."""

    @pytest.mark.asyncio
    async def test_context_matching_aggregation(self):
        """Matching dimensions should be aggregated."""
        manager = KnowledgeManager()
        proposal_context = ProposalContext(
            rfp_summary="Manufacturing IoT platform"
        )

        mock_search_results = SearchResponse(
            items=[
                SearchResultItem(
                    id=uuid4(),
                    knowledge_type=KnowledgeType.CAPABILITY,
                    confidence_score=Decimal("0.85"),
                    freshness_score=Decimal("90.0"),
                    source_doc="IoT",
                    created_at=datetime.utcnow(),
                    content_preview="IoT...",
                ),
                SearchResultItem(
                    id=uuid4(),
                    knowledge_type=KnowledgeType.CLIENT_INTEL,
                    confidence_score=Decimal("0.75"),
                    freshness_score=Decimal("80.0"),
                    source_doc="Manufacturing",
                    created_at=datetime.utcnow(),
                    content_preview="Manufacturing...",
                ),
            ],
            total=2,
            limit=20,
            offset=0
        )

        mock_claude_response = [
            {
                "chunk_id": str(mock_search_results.items[0].id),
                "relevance_score": 90,
                "match_reason": "IoT technology",
                "matching_dimensions": ["technology", "architecture"]
            },
            {
                "chunk_id": str(mock_search_results.items[1].id),
                "relevance_score": 85,
                "match_reason": "Manufacturing client",
                "matching_dimensions": ["industry", "client_type"]
            }
        ]

        with patch.object(
            manager, "search",
            new_callable=AsyncMock,
            return_value=mock_search_results
        ), patch("app.services.knowledge_manager.claude_generate",
            new_callable=AsyncMock,
            return_value=mock_claude_response
        ):
            response = await manager.recommend(
                proposal_context=proposal_context,
                user_team_id=uuid4(),
                limit=5
            )

            # Should aggregate all unique dimensions
            assert "technology" in response.context_matched
            assert "architecture" in response.context_matched
            assert "industry" in response.context_matched
            assert "client_type" in response.context_matched
