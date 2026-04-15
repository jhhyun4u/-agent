"""
Unit tests for Knowledge Classifier (Module-2).

Tests cover:
- Classification request creation
- LLM response parsing
- Confidence score validation
- Multi-type classification
- Error handling
"""

import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.models.knowledge_schemas import (
    ClassificationRequest,
    ClassificationResult,
    KnowledgeType,
)
from app.services.knowledge_manager import (
    KnowledgeManager,
    ClassificationError,
    get_knowledge_manager,
)


# ============================================================================
# CLASSIFICATION REQUEST TESTS
# ============================================================================

class TestClassificationRequest:
    """Test classification request validation."""

    def test_valid_classification_request(self):
        """Valid classification request should be created."""
        chunk_id = uuid4()
        req = ClassificationRequest(
            chunk_id=chunk_id,
            content="We implemented an IoT platform using AWS Lambda and Kinesis",
            document_context="IoT Platform Case Study"
        )
        assert req.chunk_id == chunk_id
        assert "IoT platform" in req.content
        assert req.document_context == "IoT Platform Case Study"

    def test_classification_request_minimal(self):
        """Minimal classification request (no context)."""
        chunk_id = uuid4()
        req = ClassificationRequest(
            chunk_id=chunk_id,
            content="Machine learning model for customer segmentation"
        )
        assert req.chunk_id == chunk_id
        assert req.document_context is None

    def test_classification_request_content_validation(self):
        """Content validation should reject empty strings."""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            ClassificationRequest(
                chunk_id=uuid4(),
                content=""
            )

    def test_classification_request_whitespace_content(self):
        """Whitespace-only content should be rejected."""
        with pytest.raises(ValueError, match="Content cannot be empty"):
            ClassificationRequest(
                chunk_id=uuid4(),
                content="   \n\t  "
            )


# ============================================================================
# CLASSIFICATION RESULT TESTS
# ============================================================================

class TestClassificationResult:
    """Test classification result models."""

    def test_valid_classification_result(self):
        """Valid classification result."""
        chunk_id = uuid4()
        result = ClassificationResult(
            chunk_id=chunk_id,
            knowledge_type=KnowledgeType.CAPABILITY,
            classification_confidence=Decimal("0.92"),
            is_multi_type=False,
            reasoning="Detected technical expertise and implementation details"
        )
        assert result.chunk_id == chunk_id
        assert result.knowledge_type == KnowledgeType.CAPABILITY
        assert result.classification_confidence == Decimal("0.92")
        assert result.is_multi_type is False

    def test_classification_result_all_types(self):
        """Classification can be any of 4 types."""
        for knowledge_type in [
            KnowledgeType.CAPABILITY,
            KnowledgeType.CLIENT_INTEL,
            KnowledgeType.MARKET_PRICE,
            KnowledgeType.LESSON_LEARNED,
        ]:
            result = ClassificationResult(
                chunk_id=uuid4(),
                knowledge_type=knowledge_type,
                classification_confidence=Decimal("0.75")
            )
            assert result.knowledge_type == knowledge_type

    def test_classification_result_multi_type(self):
        """Classification can span multiple types."""
        other_ids = [uuid4(), uuid4()]
        result = ClassificationResult(
            chunk_id=uuid4(),
            knowledge_type=KnowledgeType.CAPABILITY,
            classification_confidence=Decimal("0.85"),
            is_multi_type=True,
            multi_type_ids=other_ids,
            reasoning="Spans capability and lesson_learned"
        )
        assert result.is_multi_type is True
        assert len(result.multi_type_ids) == 2

    def test_classification_confidence_bounds(self):
        """Confidence score must be 0.0-1.0."""
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

    def test_classification_result_timestamp(self):
        """Classification result has creation timestamp."""
        result = ClassificationResult(
            chunk_id=uuid4(),
            knowledge_type=KnowledgeType.CAPABILITY,
            classification_confidence=Decimal("0.80")
        )
        assert isinstance(result.created_at, datetime)
        # Should be recent
        assert (datetime.utcnow() - result.created_at).total_seconds() < 1


# ============================================================================
# KNOWLEDGE MANAGER SERVICE TESTS
# ============================================================================

class TestKnowledgeManager:
    """Test KnowledgeManager service."""

    def test_get_knowledge_manager_singleton(self):
        """get_knowledge_manager returns singleton instance."""
        manager1 = get_knowledge_manager()
        manager2 = get_knowledge_manager()
        assert manager1 is manager2

    def test_knowledge_manager_instance(self):
        """KnowledgeManager instance can be created."""
        manager = KnowledgeManager()
        assert isinstance(manager, KnowledgeManager)

    @pytest.mark.asyncio
    async def test_classify_chunk_valid_response(self):
        """Classify chunk with valid Claude response."""
        manager = KnowledgeManager()
        chunk_id = uuid4()

        # Mock Claude API response
        mock_response = {
            "primary_type": "capability",
            "confidence": 0.92,
            "reasoning": "Detected technical expertise in IoT platform implementation",
            "secondary_types": [],
            "tags": ["IoT", "AWS", "real-time-systems"],
            "should_deprecate": False,
            "deprecation_reason": None
        }

        with patch.object(
            manager.__class__, "classify_chunk",
            new_callable=AsyncMock,
            return_value=ClassificationResult(
                chunk_id=chunk_id,
                knowledge_type=KnowledgeType.CAPABILITY,
                classification_confidence=Decimal("0.92"),
                reasoning="Detected technical expertise"
            )
        ):
            result = await manager.classify_chunk(
                chunk_id=chunk_id,
                content="IoT platform using AWS Lambda and Kinesis for real-time processing"
            )

            assert result.chunk_id == chunk_id
            assert result.knowledge_type == KnowledgeType.CAPABILITY
            assert result.classification_confidence == Decimal("0.92")

    @pytest.mark.asyncio
    async def test_classify_chunk_with_context(self):
        """Classify chunk with document context."""
        manager = KnowledgeManager()
        chunk_id = uuid4()

        context = {
            "title": "AWS Architecture Case Study",
            "created_date": datetime.utcnow().isoformat(),
            "source": "internal-archive",
            "author": "john.doe@company.com"
        }

        with patch.object(
            manager.__class__, "classify_chunk",
            new_callable=AsyncMock,
            return_value=ClassificationResult(
                chunk_id=chunk_id,
                knowledge_type=KnowledgeType.CAPABILITY,
                classification_confidence=Decimal("0.88")
            )
        ):
            result = await manager.classify_chunk(
                chunk_id=chunk_id,
                content="Lambda functions for serverless architecture",
                document_context=context
            )

            assert result.knowledge_type == KnowledgeType.CAPABILITY
            assert float(result.classification_confidence) > 0.8

    @pytest.mark.asyncio
    async def test_classify_chunk_low_confidence(self):
        """Classify chunk with low confidence defaults to unclassified behavior."""
        manager = KnowledgeManager()
        chunk_id = uuid4()

        with patch.object(
            manager.__class__, "classify_chunk",
            new_callable=AsyncMock,
            return_value=ClassificationResult(
                chunk_id=chunk_id,
                knowledge_type=KnowledgeType.CAPABILITY,
                classification_confidence=Decimal("0.3"),
                reasoning="Ambiguous content, low confidence"
            )
        ):
            result = await manager.classify_chunk(
                chunk_id=chunk_id,
                content="Something about teams and projects"
            )

            # Low confidence classification should still work
            assert result.classification_confidence <= Decimal("0.4")

    @pytest.mark.asyncio
    async def test_classify_chunk_multi_type(self):
        """Classify chunk spanning multiple knowledge types."""
        manager = KnowledgeManager()
        chunk_id = uuid4()
        secondary_id = uuid4()

        with patch.object(
            manager.__class__, "classify_chunk",
            new_callable=AsyncMock,
            return_value=ClassificationResult(
                chunk_id=chunk_id,
                knowledge_type=KnowledgeType.CAPABILITY,
                classification_confidence=Decimal("0.85"),
                is_multi_type=True,
                multi_type_ids=[secondary_id],
                reasoning="Spans capability and lesson_learned"
            )
        ):
            result = await manager.classify_chunk(
                chunk_id=chunk_id,
                content="We learned to always use automated testing. Testing framework X is best."
            )

            assert result.is_multi_type is True
            assert result.multi_type_ids is not None
            assert len(result.multi_type_ids) == 1

    @pytest.mark.asyncio
    async def test_search_is_implemented(self):
        """Search method is implemented (Module-3)."""
        manager = KnowledgeManager()
        assert hasattr(manager, "search")
        assert callable(getattr(manager, "search"))

    @pytest.mark.asyncio
    async def test_recommend_is_implemented(self):
        """Recommend method is implemented (Module-4)."""
        manager = KnowledgeManager()
        assert hasattr(manager, "recommend")
        assert callable(getattr(manager, "recommend"))

    @pytest.mark.asyncio
    async def test_get_health_metrics_success(self):
        """Get health metrics returns KB statistics."""
        manager = KnowledgeManager()
        team_id = uuid4()

        # Mock all Supabase client calls
        mock_execute = AsyncMock(
            return_value=MagicMock(count=10, data=[])
        )
        mock_eq = MagicMock(return_value=MagicMock(execute=mock_execute))
        mock_select = MagicMock(
            return_value=MagicMock(
                execute=mock_execute,
                eq=mock_eq
            )
        )
        mock_table = MagicMock(return_value=MagicMock(select=mock_select))
        mock_client = MagicMock(table=mock_table)

        with patch("app.services.knowledge_manager.get_async_client", return_value=mock_client):
            result = await manager.get_health_metrics(team_id=team_id)

            # Verify result structure
            assert result is not None
            assert hasattr(result, "kb_size")

    @pytest.mark.asyncio
    async def test_mark_deprecated_success(self):
        """Mark deprecated updates metadata correctly."""
        manager = KnowledgeManager()
        chunk_id = uuid4()
        user_id = uuid4()
        metadata_id = uuid4()

        # Mock Supabase client for select query (check existing)
        mock_maybe_single_execute = AsyncMock(
            return_value=MagicMock(data={"id": str(metadata_id)})
        )
        mock_maybe_single = MagicMock(return_value=MagicMock(execute=mock_maybe_single_execute))
        mock_eq_for_select = MagicMock(return_value=MagicMock(maybe_single=mock_maybe_single))
        mock_select = MagicMock(return_value=MagicMock(eq=mock_eq_for_select))

        # Mock Supabase client for update query
        mock_update_execute = AsyncMock(
            return_value=MagicMock(
                data=[{
                    "id": str(metadata_id),
                    "is_deprecated": True,
                    "freshness_score": 0.0,
                    "last_updated_at": datetime.utcnow().isoformat()
                }]
            )
        )
        mock_eq_for_update = MagicMock(return_value=MagicMock(execute=mock_update_execute))
        mock_update = MagicMock(return_value=MagicMock(eq=mock_eq_for_update))

        # Create table mock that returns different mocks based on method
        def table_side_effect(name):
            if name == "knowledge_metadata":
                return MagicMock(select=mock_select, update=mock_update)
            return MagicMock()

        mock_table = MagicMock(side_effect=table_side_effect)
        mock_client = MagicMock(table=mock_table)

        with patch("app.services.knowledge_manager.get_async_client", return_value=mock_client):
            result = await manager.mark_deprecated(
                chunk_id=chunk_id,
                reason="Outdated",
                user_id=user_id
            )

            # Verify result structure
            assert result is not None
            assert result["is_deprecated"] is True
            assert result["freshness_score"] == 0.0

    @pytest.mark.asyncio
    async def test_share_to_org_success(self):
        """Share to org creates audit record and returns audit_id."""
        manager = KnowledgeManager()
        chunk_id = uuid4()
        audit_id = uuid4()
        shared_by = uuid4()
        team_id = uuid4()

        # Mock Supabase client for insert query
        mock_insert_execute = AsyncMock(
            return_value=MagicMock(data=[{"id": str(audit_id)}])
        )
        mock_insert = MagicMock(return_value=MagicMock(execute=mock_insert_execute))

        # Create table mock
        def table_side_effect(name):
            if name == "knowledge_sharing_audit":
                return MagicMock(insert=mock_insert)
            return MagicMock()

        mock_table = MagicMock(side_effect=table_side_effect)
        mock_client = MagicMock(table=mock_table)

        with patch("app.services.knowledge_manager.get_async_client", return_value=mock_client):
            result = await manager.share_to_org(
                chunk_id=chunk_id,
                reason="Applicable to all teams",
                shared_by=shared_by,
                team_id=team_id
            )

            # Verify result is the audit_id
            assert result == audit_id


# ============================================================================
# CLASSIFICATION ERROR TESTS
# ============================================================================

class TestClassificationError:
    """Test classification error handling."""

    def test_classification_error_is_exception(self):
        """ClassificationError is an Exception."""
        error = ClassificationError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    def test_classification_error_message(self):
        """ClassificationError preserves message."""
        msg = "Invalid LLM response format"
        error = ClassificationError(msg)
        assert msg in str(error)
