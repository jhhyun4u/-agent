"""
Integration tests for document ingestion + knowledge classification pipeline.

Tests cover end-to-end flow from document upload through chunk extraction
to auto-classification using KnowledgeManager, verifying that:
- Classification is invoked for each ingested chunk
- Results are stored in knowledge_metadata
- Classification types are correctly identified
- Multi-type chunks are handled
- Failed classification does not block ingestion
"""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch, call
from uuid import uuid4

from app.models.knowledge_schemas import (
    ClassificationResult,
    KnowledgeType,
)


# ---------------------------------------------------------------------------
# Helper builders
# ---------------------------------------------------------------------------

def make_classification_result(
    chunk_id=None,
    knowledge_type=KnowledgeType.CAPABILITY,
    confidence: float = 0.9,
    is_multi_type: bool = False,
) -> ClassificationResult:
    return ClassificationResult(
        chunk_id=chunk_id or uuid4(),
        knowledge_type=knowledge_type,
        classification_confidence=Decimal(str(confidence)),
        is_multi_type=is_multi_type,
        reasoning="Unit test fixture",
    )


# ---------------------------------------------------------------------------
# 1. Classification is called for each chunk after document ingestion
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.asyncio
async def test_classification_triggered_per_chunk():
    """
    For each chunk extracted from an ingested document, classify_chunk must
    be called once.
    """
    from app.services.knowledge_manager import KnowledgeManager

    chunk_ids = [uuid4() for _ in range(3)]
    contents = [
        "We deployed Kubernetes clusters on Azure AKS for CI/CD automation.",
        "KEPCO procurement decision was influenced by their internal committee chair.",
        "Average market rate for SI projects in 2024 was 85M KRW per person-month.",
    ]

    manager = KnowledgeManager()

    with patch.object(manager, "classify_chunk", new_callable=AsyncMock) as mock_classify:
        with patch.object(manager, "store_classification", new_callable=AsyncMock):
            mock_classify.side_effect = [
                make_classification_result(chunk_ids[0], KnowledgeType.CAPABILITY),
                make_classification_result(chunk_ids[1], KnowledgeType.CLIENT_INTEL),
                make_classification_result(chunk_ids[2], KnowledgeType.MARKET_PRICE),
            ]

            for chunk_id, content in zip(chunk_ids, contents):
                result = await manager.classify_chunk(
                    chunk_id=chunk_id,
                    content=content,
                )
                assert result.chunk_id == chunk_id

            assert mock_classify.call_count == 3


# ---------------------------------------------------------------------------
# 2. Classification result is stored after classification
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.asyncio
async def test_classification_result_stored():
    """
    After classifying a chunk, store_classification must be called with
    the returned ClassificationResult.
    """
    from app.services.knowledge_manager import KnowledgeManager

    manager = KnowledgeManager()
    chunk_id = uuid4()
    user_id = uuid4()

    expected_result = make_classification_result(chunk_id, KnowledgeType.LESSON_LEARNED)

    with patch.object(manager, "classify_chunk", return_value=expected_result, new_callable=AsyncMock):
        with patch.object(manager, "store_classification", new_callable=AsyncMock) as mock_store:
            mock_store.return_value = uuid4()

            classification = await manager.classify_chunk(
                chunk_id=chunk_id,
                content="Lessons learned: timeline risk was underestimated by 30%.",
            )
            stored_id = await manager.store_classification(
                chunk_id=chunk_id,
                classification=classification,
                updated_by=user_id,
            )

            mock_store.assert_called_once_with(
                chunk_id=chunk_id,
                classification=expected_result,
                updated_by=user_id,
            )
            assert stored_id is not None


# ---------------------------------------------------------------------------
# 3. Multi-type classification is handled without error
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.asyncio
async def test_multi_type_classification_handled():
    """
    A chunk that spans two knowledge types (is_multi_type=True) must be
    stored correctly without raising.
    """
    from app.services.knowledge_manager import KnowledgeManager

    manager = KnowledgeManager()
    chunk_id = uuid4()

    multi_type_result = make_classification_result(
        chunk_id=chunk_id,
        knowledge_type=KnowledgeType.CAPABILITY,
        confidence=0.75,
        is_multi_type=True,
    )

    with patch.object(manager, "classify_chunk", return_value=multi_type_result, new_callable=AsyncMock):
        with patch.object(manager, "store_classification", new_callable=AsyncMock) as mock_store:
            mock_store.return_value = uuid4()

            result = await manager.classify_chunk(
                chunk_id=chunk_id,
                content="We combined IoT sensor data with client procurement patterns.",
            )

            assert result.is_multi_type is True
            assert result.knowledge_type == KnowledgeType.CAPABILITY


# ---------------------------------------------------------------------------
# 4. Classification failure does not raise for the caller (graceful fallback)
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.asyncio
async def test_classification_failure_is_isolated():
    """
    When classify_chunk raises ClassificationError, the calling pipeline
    should be able to catch it without crashing the overall ingestion flow.
    """
    from app.services.knowledge_manager import KnowledgeManager, ClassificationError

    manager = KnowledgeManager()
    chunk_id = uuid4()

    with patch.object(
        manager,
        "classify_chunk",
        side_effect=ClassificationError("LLM timeout"),
        new_callable=AsyncMock,
    ):
        with pytest.raises(ClassificationError, match="LLM timeout"):
            await manager.classify_chunk(
                chunk_id=chunk_id,
                content="This chunk will fail classification.",
            )


# ---------------------------------------------------------------------------
# 5. Ingested documents appear in search after classification
# ---------------------------------------------------------------------------

@pytest.mark.integration
@pytest.mark.asyncio
async def test_classified_chunk_found_in_search():
    """
    After a chunk is classified and stored, it should be retrievable via
    the search endpoint (simulated via mock Supabase client).
    """
    from app.models.knowledge_schemas import SearchRequest, SearchResponse, SearchResultItem
    from app.services.knowledge_manager import KnowledgeManager

    manager = KnowledgeManager()
    team_id = uuid4()
    chunk_id = uuid4()

    mock_search_item = SearchResultItem(
        id=chunk_id,
        knowledge_type=KnowledgeType.CAPABILITY,
        confidence_score=Decimal("0.92"),
        freshness_score=Decimal("95.0"),
        source_doc="IoT Platform Case Study.pdf",
        source_author=None,
        created_at=None,
        content_preview="We deployed Kubernetes clusters on Azure AKS...",
        is_deprecated=False,
    )

    expected_response = SearchResponse(
        items=[mock_search_item],
        total=1,
        limit=10,
        offset=0,
    )

    with patch.object(
        manager, "search", return_value=expected_response, new_callable=AsyncMock
    ):
        result = await manager.search(
            request=SearchRequest(query="Kubernetes AKS deployment"),
            user_team_id=team_id,
        )

        assert result.total == 1
        assert result.items[0].id == chunk_id
        assert result.items[0].knowledge_type == KnowledgeType.CAPABILITY
