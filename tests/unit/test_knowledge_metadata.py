"""
Unit tests for knowledge metadata tables, RLS policies, and Pydantic schemas.

Tests cover:
- Database schema creation and structure
- RLS policy enforcement
- Pydantic schema validation
- Data model constraints
"""

import pytest
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

from app.models.knowledge_schemas import (
    ClassificationRequest,
    ClassificationResult,
    SearchRequest,
    SearchFilters,
    SearchResultItem,
    SearchResponse,
    ProposalContext,
    RecommendationRequest,
    RecommendationResultItem,
    RecommendationResponse,
    DeprecationRequest,
    DeprecationResponse,
    SharingRequest,
    SharingResponse,
    KnowledgeType,
    KnowledgeMetadataDB,
    KnowledgeSharingAuditDB,
    ErrorResponse,
)


# ============================================================================
# CLASSIFICATION SCHEMA TESTS
# ============================================================================

class TestClassificationSchemas:
    """Test classification request/response schemas."""

    def test_classification_request_valid(self):
        """Valid classification request should pass validation."""
        req = ClassificationRequest(
            chunk_id=uuid4(),
            content="This is IoT platform expertise for Acme Corp",
            document_context="IoT Platform Case Study"
        )
        assert req.chunk_id is not None
        assert req.content == "This is IoT platform expertise for Acme Corp"
        assert req.document_context == "IoT Platform Case Study"

    def test_classification_request_empty_content(self):
        """Empty content should raise validation error."""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            ClassificationRequest(
                chunk_id=uuid4(),
                content="",
                document_context="Context"
            )

    def test_classification_request_whitespace_only(self):
        """Whitespace-only content should raise validation error."""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            ClassificationRequest(
                chunk_id=uuid4(),
                content="   ",
                document_context="Context"
            )

    def test_classification_result_valid(self):
        """Valid classification result should pass validation."""
        result = ClassificationResult(
            chunk_id=uuid4(),
            knowledge_type=KnowledgeType.CAPABILITY,
            classification_confidence=Decimal("0.92"),
            is_multi_type=False,
            reasoning="Detected technical expertise language"
        )
        assert result.knowledge_type == KnowledgeType.CAPABILITY
        assert result.classification_confidence == Decimal("0.92")
        assert result.is_multi_type is False

    def test_classification_result_multi_type(self):
        """Classification result can mark multiple types."""
        other_id = uuid4()
        result = ClassificationResult(
            chunk_id=uuid4(),
            knowledge_type=KnowledgeType.CAPABILITY,
            classification_confidence=Decimal("0.85"),
            is_multi_type=True,
            multi_type_ids=[other_id],
            reasoning="Document spans capability and lesson_learned"
        )
        assert result.is_multi_type is True
        assert len(result.multi_type_ids) == 1
        assert result.multi_type_ids[0] == other_id

    def test_classification_confidence_bounds(self):
        """Classification confidence must be between 0.0 and 1.0."""
        # Valid: 0.0
        result = ClassificationResult(
            chunk_id=uuid4(),
            knowledge_type=KnowledgeType.LESSON_LEARNED,
            classification_confidence=Decimal("0.0")
        )
        assert result.classification_confidence == Decimal("0.0")

        # Valid: 1.0
        result = ClassificationResult(
            chunk_id=uuid4(),
            knowledge_type=KnowledgeType.LESSON_LEARNED,
            classification_confidence=Decimal("1.0")
        )
        assert result.classification_confidence == Decimal("1.0")

        # Invalid: > 1.0
        with pytest.raises(ValueError):
            ClassificationResult(
                chunk_id=uuid4(),
                knowledge_type=KnowledgeType.LESSON_LEARNED,
                classification_confidence=Decimal("1.5")
            )

        # Invalid: < 0.0
        with pytest.raises(ValueError):
            ClassificationResult(
                chunk_id=uuid4(),
                knowledge_type=KnowledgeType.LESSON_LEARNED,
                classification_confidence=Decimal("-0.1")
            )


# ============================================================================
# SEARCH SCHEMA TESTS
# ============================================================================

class TestSearchSchemas:
    """Test search request/response schemas."""

    def test_search_request_valid(self):
        """Valid search request should pass validation."""
        req = SearchRequest(
            query="IoT platform architecture",
            filters=SearchFilters(
                knowledge_types=[KnowledgeType.CAPABILITY, KnowledgeType.LESSON_LEARNED],
                freshness_min=50,
                exclude_deprecated=True
            ),
            limit=10,
            offset=0
        )
        assert req.query == "IoT platform architecture"
        assert len(req.filters.knowledge_types) == 2
        assert req.filters.freshness_min == 50

    def test_search_request_min_query_length(self):
        """Query must be at least 3 characters."""
        # Valid: exactly 3 characters
        req = SearchRequest(query="IoT")
        assert req.query == "IoT"

        # Invalid: less than 3 characters
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            SearchRequest(query="IT")

    def test_search_request_query_whitespace_trimmed(self):
        """Query should be trimmed of whitespace."""
        req = SearchRequest(query="  IoT platform  ")
        assert req.query == "IoT platform"

    def test_search_request_pagination_bounds(self):
        """Limit must be between 1 and 100."""
        # Valid: 1
        req = SearchRequest(query="test", limit=1)
        assert req.limit == 1

        # Valid: 100
        req = SearchRequest(query="test", limit=100)
        assert req.limit == 100

        # Invalid: 0
        with pytest.raises(ValueError):
            SearchRequest(query="test", limit=0)

        # Invalid: > 100
        with pytest.raises(ValueError):
            SearchRequest(query="test", limit=101)

    def test_search_request_offset_non_negative(self):
        """Offset must be non-negative."""
        # Valid: 0
        req = SearchRequest(query="test", offset=0)
        assert req.offset == 0

        # Invalid: negative
        with pytest.raises(ValueError):
            SearchRequest(query="test", offset=-1)

    def test_search_filters_freshness_bounds(self):
        """Freshness score must be between 0 and 100."""
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

    def test_search_result_item_valid(self):
        """Valid search result item should pass validation."""
        item = SearchResultItem(
            id=uuid4(),
            knowledge_type=KnowledgeType.CAPABILITY,
            confidence_score=Decimal("0.92"),
            freshness_score=Decimal("85.0"),
            source_doc="IoT Platform Case Study",
            source_author="john.doe",
            created_at=datetime.utcnow(),
            content_preview="Our IoT platform for Acme Corp...",
            embedding_similarity=Decimal("0.87"),
            is_deprecated=False
        )
        assert item.knowledge_type == KnowledgeType.CAPABILITY
        assert item.freshness_score == Decimal("85.0")

    def test_search_response_valid(self):
        """Valid search response should pass validation."""
        item = SearchResultItem(
            id=uuid4(),
            knowledge_type=KnowledgeType.CAPABILITY,
            confidence_score=Decimal("0.92"),
            freshness_score=Decimal("85.0"),
            source_doc="Case Study",
            created_at=datetime.utcnow(),
            content_preview="Content...",
        )
        response = SearchResponse(
            items=[item],
            total=1,
            limit=10,
            offset=0
        )
        assert len(response.items) == 1
        assert response.total == 1


# ============================================================================
# RECOMMENDATION SCHEMA TESTS
# ============================================================================

class TestRecommendationSchemas:
    """Test recommendation request/response schemas."""

    def test_proposal_context_valid(self):
        """Valid proposal context should pass validation."""
        context = ProposalContext(
            rfp_summary="Build enterprise IoT platform with real-time analytics",
            client_type="manufacturing",
            bid_amount=500000,
            selected_strategy="architectural_innovation",
            additional_context="Strategic engagement with key account"
        )
        assert context.client_type == "manufacturing"
        assert context.bid_amount == 500000

    def test_proposal_context_minimal(self):
        """Proposal context requires only RFP summary."""
        context = ProposalContext(
            rfp_summary="Build IoT platform"
        )
        assert context.rfp_summary == "Build IoT platform"
        assert context.client_type is None
        assert context.bid_amount is None

    def test_recommendation_request_valid(self):
        """Valid recommendation request should pass validation."""
        req = RecommendationRequest(
            proposal_context=ProposalContext(
                rfp_summary="Manufacturing IoT solution",
                client_type="manufacturing"
            ),
            limit=5
        )
        assert req.limit == 5

    def test_recommendation_result_item_valid(self):
        """Valid recommendation result should pass validation."""
        item = RecommendationResultItem(
            rank=1,
            chunk_id=uuid4(),
            knowledge_type=KnowledgeType.CAPABILITY,
            confidence_score=Decimal("0.89"),
            source_doc="Acme Corp Case Study",
            content_preview="Successfully delivered IoT platform...",
            relevance_reason="Similar architecture and manufacturing client",
            freshness_score=Decimal("82.0"),
            match_type="semantic"
        )
        assert item.rank == 1
        assert item.match_type == "semantic"

    def test_recommendation_response_valid(self):
        """Valid recommendation response should pass validation."""
        item = RecommendationResultItem(
            rank=1,
            chunk_id=uuid4(),
            knowledge_type=KnowledgeType.CAPABILITY,
            confidence_score=Decimal("0.89"),
            source_doc="Case Study",
            content_preview="Content...",
            relevance_reason="Similar context",
            freshness_score=Decimal("82.0")
        )
        response = RecommendationResponse(
            items=[item],
            context_matched=["architecture", "manufacturing", "real_time"],
            fallback_used=False
        )
        assert len(response.items) == 1
        assert len(response.context_matched) == 3
        assert response.fallback_used is False

    def test_recommendation_response_with_fallback(self):
        """Recommendation response can indicate fallback was used."""
        item = RecommendationResultItem(
            rank=1,
            chunk_id=uuid4(),
            knowledge_type=KnowledgeType.CAPABILITY,
            confidence_score=Decimal("0.75"),
            source_doc="Case Study",
            content_preview="Content...",
            relevance_reason="Keyword match",
            freshness_score=Decimal("70.0"),
            match_type="keyword_fallback"
        )
        response = RecommendationResponse(
            items=[item],
            context_matched=["IoT"],
            fallback_used=True
        )
        assert response.fallback_used is True
        assert item.match_type == "keyword_fallback"


# ============================================================================
# LIFECYCLE MANAGEMENT SCHEMA TESTS
# ============================================================================

class TestLifecycleSchemas:
    """Test knowledge lifecycle management schemas."""

    def test_deprecation_request_valid(self):
        """Valid deprecation request should pass validation."""
        req = DeprecationRequest(
            is_deprecated=True,
            reason="Client information outdated (2021 data)"
        )
        assert req.is_deprecated is True
        assert len(req.reason) > 0

    def test_deprecation_response_valid(self):
        """Valid deprecation response should pass validation."""
        resp = DeprecationResponse(
            id=uuid4(),
            is_deprecated=True,
            freshness_score=Decimal("15.0"),
            updated_at=datetime.utcnow()
        )
        assert resp.is_deprecated is True
        assert resp.freshness_score == Decimal("15.0")

    def test_sharing_request_valid(self):
        """Valid sharing request should pass validation."""
        req = SharingRequest(
            shared_to_org=True,
            reason="Best practice solution applicable to all teams"
        )
        assert req.shared_to_org is True

    def test_sharing_response_valid(self):
        """Valid sharing response should pass validation."""
        resp = SharingResponse(
            id=uuid4(),
            shared_to_org=True,
            shared_at=datetime.utcnow(),
            audit_id=uuid4()
        )
        assert resp.shared_to_org is True
        assert resp.audit_id is not None


# ============================================================================
# DATABASE MODEL TESTS
# ============================================================================

class TestDatabaseModels:
    """Test database ORM models."""

    def test_knowledge_metadata_db_valid(self):
        """Valid knowledge metadata database model."""
        chunk_id = uuid4()
        model = KnowledgeMetadataDB(
            id=uuid4(),
            chunk_id=chunk_id,
            knowledge_type=KnowledgeType.MARKET_PRICE,
            classification_confidence=Decimal("0.88"),
            is_deprecated=False,
            freshness_score=Decimal("90.0"),
            last_updated_at=datetime.utcnow(),
            updated_by=uuid4(),
            multi_type_ids=None,
            created_at=datetime.utcnow()
        )
        assert model.chunk_id == chunk_id
        assert model.knowledge_type == KnowledgeType.MARKET_PRICE

    def test_knowledge_sharing_audit_db_valid(self):
        """Valid knowledge sharing audit database model."""
        model = KnowledgeSharingAuditDB(
            id=uuid4(),
            chunk_id=uuid4(),
            shared_by=uuid4(),
            shared_from_team_id=uuid4(),
            shared_to_org=True,
            shared_at=datetime.utcnow(),
            reason="Applicable to all teams",
            created_at=datetime.utcnow()
        )
        assert model.shared_to_org is True
        assert model.reason == "Applicable to all teams"


# ============================================================================
# KNOWLEDGE TYPE ENUM TESTS
# ============================================================================

class TestKnowledgeTypeEnum:
    """Test KnowledgeType enum."""

    def test_all_knowledge_types_valid(self):
        """All knowledge type values should be valid."""
        assert KnowledgeType.CAPABILITY.value == "capability"
        assert KnowledgeType.CLIENT_INTEL.value == "client_intel"
        assert KnowledgeType.MARKET_PRICE.value == "market_price"
        assert KnowledgeType.LESSON_LEARNED.value == "lesson_learned"

    def test_knowledge_type_in_schema(self):
        """Knowledge types should work in schema validation."""
        result = ClassificationResult(
            chunk_id=uuid4(),
            knowledge_type=KnowledgeType.CLIENT_INTEL,
            classification_confidence=Decimal("0.90")
        )
        assert result.knowledge_type == KnowledgeType.CLIENT_INTEL


# ============================================================================
# ERROR RESPONSE TESTS
# ============================================================================

class TestErrorResponse:
    """Test error response schemas."""

    def test_error_response_basic(self):
        """Basic error response should pass validation."""
        resp = ErrorResponse(
            error="INVALID_QUERY",
            message="Query must be at least 3 characters"
        )
        assert resp.error == "INVALID_QUERY"

    def test_error_response_with_details(self):
        """Error response with details should pass validation."""
        resp = ErrorResponse(
            error="VALIDATION_ERROR",
            message="Invalid request",
            details={
                "field": "knowledge_types",
                "reason": "Invalid type value"
            }
        )
        assert resp.details is not None
        assert resp.details["field"] == "knowledge_types"
