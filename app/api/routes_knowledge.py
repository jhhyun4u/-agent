"""
Knowledge Management System API Routes (Module-5).

REST endpoints for:
- Knowledge classification (auto + manual)
- Semantic + keyword search
- Context-aware recommendations
- Knowledge lifecycle management
- Health metrics and analytics

Design Ref: §5 RLS Policies, §6 Knowledge Lifecycle
"""

import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import ValidationError

from app.api.deps import get_current_user, require_role, require_knowledge_access, CurrentUser
from app.models.knowledge_schemas import (
    ClassificationRequest,
    ClassificationResult,
    SearchRequest,
    SearchResponse,
    RecommendationRequest,
    RecommendationResponse,
    KnowledgeType,
    FlatHealthMetrics,
    KnowledgeFeedbackRequest,
    KnowledgeFeedbackResponse,
    DeprecationRequest,
    DeprecationResponse,
    SharingRequest,
    SharingResponse,
)
from app.services.domains.vault.knowledge_manager import get_knowledge_manager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


# ============================================================================
# CLASSIFICATION ENDPOINTS
# ============================================================================

@router.post(
    "/classify",
    response_model=ClassificationResult,
    summary="Auto-classify a knowledge chunk",
    description="Use Claude API to classify knowledge chunk with confidence score"
)
async def classify_knowledge(
    request: ClassificationRequest,
    current_user: CurrentUser = Depends(require_knowledge_access),
) -> ClassificationResult:
    """
    Auto-classify a knowledge chunk using Claude API.

    Returns ClassificationResult with:
    - knowledge_type: One of capability, client_intel, market_price, lesson_learned
    - classification_confidence: 0.0-1.0 score
    - is_multi_type: True if chunk spans multiple types
    - reasoning: Explanation of classification

    Plan SC-1: Classification accuracy ≥90%
    """
    try:
        manager = get_knowledge_manager()
        result = await manager.classify_chunk(
            chunk_id=request.chunk_id,
            content=request.content,
            document_context={
                "title": request.document_context
            } if request.document_context else None
        )
        return result

    except Exception as e:
        logger.error(f"Classification failed for chunk {request.chunk_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Classification failed: {str(e)}"
        )


# ============================================================================
# SEARCH ENDPOINTS
# ============================================================================

@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic + keyword hybrid search",
    description="Search knowledge base with pgvector embedding + BM25 fallback"
)
async def search_knowledge(
    request: SearchRequest,
    current_user: CurrentUser = Depends(require_knowledge_access),
) -> SearchResponse:
    """
    Semantic + keyword hybrid search for knowledge.

    Algorithm:
    1. Generate embedding for query
    2. Try pgvector cosine similarity search
    3. If no results → fallback to BM25 keyword search
    4. Apply filters (type, freshness, team)
    5. Return paginated results

    Plan SC-1: <500ms response time for 5000+ document KB

    Query params:
    - query: Search text (min 3 chars)
    - limit: Results per page (1-100, default 10)
    - offset: Pagination offset (default 0)
    - knowledge_types: Filter by type (optional, multi-select)
    - freshness_min: Min freshness score 0-100 (optional)
    """
    try:
        manager = get_knowledge_manager()
        response = await manager.search(
            request=request,
            user_team_id=current_user.team_id
        )
        return response

    except ValidationError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid search request: {e.errors()}"
        )
    except Exception as e:
        logger.error(f"Search failed for query '{request.query}': {e}")
        # Return empty results instead of raising
        return SearchResponse(
            items=[],
            total=0,
            limit=request.limit,
            offset=request.offset,
        )


# ============================================================================
# RECOMMENDATION ENDPOINTS
# ============================================================================

@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    summary="Context-aware knowledge recommendations",
    description="Generate ranked recommendations based on proposal context"
)
async def recommend_knowledge(
    request: RecommendationRequest,
    current_user: CurrentUser = Depends(require_knowledge_access),
) -> RecommendationResponse:
    """
    Generate context-aware knowledge recommendations.

    Uses Claude API to rank knowledge by relevance to proposal context.

    Request body:
    - proposal_context: RFP summary, client type, bid amount, selected strategy
    - limit: Number of recommendations (1-20, default 5)

    Response:
    - items: Ranked recommendation items with relevance reasons
    - context_matched: Matching context dimensions
    - fallback_used: True if keyword search fallback was used

    Plan SC-2: Recommendation relevance >80% (user acceptance rate)
    """
    try:
        manager = get_knowledge_manager()
        response = await manager.recommend(
            proposal_context=request.proposal_context,
            user_team_id=current_user.team_id,
            limit=request.limit
        )
        return response

    except Exception as e:
        logger.error(f"Recommendation generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Recommendation generation failed: {str(e)}"
        )


# ============================================================================
# LIFECYCLE MANAGEMENT ENDPOINTS
# ============================================================================

@router.put(
    "/{chunk_id}/deprecate",
    response_model=DeprecationResponse,
    summary="Mark knowledge as deprecated",
    description="Soft-delete knowledge chunk with reason tracking"
)
async def deprecate_knowledge(
    chunk_id: UUID,
    request: DeprecationRequest,
    current_user: CurrentUser = Depends(require_knowledge_access),
    required_role: str = Depends(lambda: require_role(["knowledge_manager", "admin"]))
) -> DeprecationResponse:
    """
    Mark knowledge as deprecated (soft delete).

    Requires knowledge_manager or admin role.

    Design Ref: §6 Knowledge Lifecycle
    """
    try:
        manager = get_knowledge_manager()
        metadata = await manager.mark_deprecated(
            chunk_id=chunk_id,
            reason=request.reason,
            user_id=current_user.id
        )
        return DeprecationResponse(
            id=UUID(metadata["id"]),
            is_deprecated=metadata.get("is_deprecated", True),
            freshness_score=Decimal(str(metadata.get("freshness_score", 0))),
            updated_at=datetime.fromisoformat(metadata.get("last_updated_at", datetime.utcnow().isoformat()))
        )

    except Exception as e:
        logger.error(f"Deprecation failed for chunk {chunk_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Deprecation failed: {str(e)}"
        )


@router.put(
    "/{chunk_id}/share",
    response_model=SharingResponse,
    summary="Share knowledge org-wide",
    description="Promote team knowledge to organization-wide scope"
)
async def share_knowledge(
    chunk_id: UUID,
    request: SharingRequest,
    current_user: CurrentUser = Depends(require_knowledge_access),
    required_role: str = Depends(lambda: require_role(["knowledge_manager", "admin"]))
) -> SharingResponse:
    """
    Promote team knowledge to org-wide scope.

    Creates audit trail. Requires knowledge_manager or admin role.

    Design Ref: §5 RLS Policies, §6 Knowledge Lifecycle
    """
    try:
        manager = get_knowledge_manager()
        audit_id = await manager.share_to_org(
            chunk_id=chunk_id,
            reason=request.reason,
            shared_by=current_user.id,
            team_id=current_user.team_id
        )
        return SharingResponse(
            id=audit_id,
            shared_to_org=True,
            shared_at=datetime.utcnow(),
            audit_id=audit_id
        )

    except Exception as e:
        logger.error(f"Sharing failed for chunk {chunk_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Sharing failed: {str(e)}"
        )


# ============================================================================
# HEALTH & ANALYTICS ENDPOINTS
# ============================================================================

@router.get(
    "/health",
    response_model=FlatHealthMetrics,
    summary="Knowledge base health metrics",
    description="Aggregate KB size, coverage, freshness, analytics (flat shape for dashboard)"
)
async def get_kb_health(
    team_id: Optional[UUID] = Query(None, description="Filter to team (defaults to current user's team)"),
    current_user: CurrentUser = Depends(require_knowledge_access),
) -> FlatHealthMetrics:
    """
    Get knowledge base health metrics in flat shape for the frontend dashboard.

    Returns a flat FlatHealthMetrics response matching KnowledgeHealthDashboard.tsx:
    - kb_size_chunks, kb_size_bytes
    - coverage_percentage
    - avg_freshness_score
    - total_organizations, total_shares
    - deprecation_rate
    - knowledge_type_distribution
    - confidence_distribution
    - trending_topics

    Design Ref: §4.3, §5.1
    """
    try:
        manager = get_knowledge_manager()
        target_team = team_id or current_user.team_id
        metrics = await manager.get_flat_health_metrics(team_id=target_team)
        return metrics

    except NotImplementedError:
        logger.warning("Health metrics not yet implemented")
        raise HTTPException(
            status_code=501,
            detail="Health metrics endpoint not yet implemented"
        )
    except Exception as e:
        logger.error(f"Failed to retrieve health metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve health metrics: {str(e)}"
        )


# ============================================================================
# FEEDBACK ENDPOINTS
# ============================================================================

@router.post(
    "/{chunk_id}/feedback",
    response_model=KnowledgeFeedbackResponse,
    summary="Submit recommendation feedback",
    description="Log thumbs-up or thumbs-down feedback for a knowledge recommendation"
)
async def submit_recommendation_feedback(
    chunk_id: UUID,
    request: KnowledgeFeedbackRequest,
    current_user: CurrentUser = Depends(require_knowledge_access),
) -> KnowledgeFeedbackResponse:
    """
    Submit feedback (positive/negative) for a recommended knowledge chunk.

    Logs feedback to knowledge_feedback_log for analytics.
    Feedback is used to improve recommendation relevance over time.

    Request body:
    - feedback_type: 'positive' (thumbs up) or 'negative' (thumbs down)
    - proposal_context: Optional context for richer analytics

    Design Ref: §4.3 Recommendation Feedback Analytics
    """
    try:
        manager = get_knowledge_manager()
        result = await manager.record_feedback(
            chunk_id=chunk_id,
            feedback_type=request.feedback_type,
            user_id=current_user.id,
            proposal_context=request.proposal_context,
        )
        return KnowledgeFeedbackResponse(
            chunk_id=chunk_id,
            feedback_type=result["feedback_type"],
            recorded=result["recorded"],
        )

    except Exception as e:
        logger.error(f"Feedback submission failed for chunk {chunk_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Feedback submission failed: {str(e)}"
        )


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

@router.get(
    "/types",
    response_model=dict,
    summary="Get available knowledge types",
    description="List valid classification types with descriptions"
)
async def get_knowledge_types(
    current_user: CurrentUser = Depends(get_current_user),
) -> dict:
    """
    Get available knowledge types with descriptions and examples.

    Returns:
    ```json
    {
      "types": [
        {
          "value": "capability",
          "description": "Technical expertise and domain knowledge",
          "examples": ["IoT platform development experience", "Kubernetes patterns"]
        },
        ...
      ]
    }
    ```
    """
    return {
        "types": [
            {
                "value": KnowledgeType.CAPABILITY.value,
                "description": "Technical expertise and domain knowledge",
                "examples": [
                    "IoT platform development experience",
                    "Real-time data processing implementation",
                    "Kubernetes orchestration patterns"
                ]
            },
            {
                "value": KnowledgeType.CLIENT_INTEL.value,
                "description": "Client organization and decision-making information",
                "examples": [
                    "Client organizational structure",
                    "Decision approval process and timeline",
                    "Past procurement behavior"
                ]
            },
            {
                "value": KnowledgeType.MARKET_PRICE.value,
                "description": "Market pricing and competitive intelligence",
                "examples": [
                    "Average winning bid rates for similar projects",
                    "Market pricing for comparable services",
                    "Competitor win/loss analysis"
                ]
            },
            {
                "value": KnowledgeType.LESSON_LEARNED.value,
                "description": "Project lessons, risks, and improvement insights",
                "examples": [
                    "Success factors from past projects",
                    "Root cause analysis of failures",
                    "Risk mitigation strategies"
                ]
            }
        ]
    }
