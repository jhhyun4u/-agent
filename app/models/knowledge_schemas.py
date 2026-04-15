"""
Knowledge Management System (llm-wiki) Pydantic Schemas.

Defines request/response models for:
- Classification results
- Search operations
- Recommendations
- Health metrics
- Knowledge lifecycle management
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ============================================================================
# ENUMS: Knowledge Types and Roles
# ============================================================================

class KnowledgeType(str, Enum):
    """Classification types for knowledge chunks."""
    CAPABILITY = "capability"
    CLIENT_INTEL = "client_intel"
    MARKET_PRICE = "market_price"
    LESSON_LEARNED = "lesson_learned"


# ============================================================================
# CLASSIFICATION SCHEMAS
# ============================================================================

class ClassificationRequest(BaseModel):
    """Request to classify a knowledge chunk."""
    chunk_id: UUID = Field(..., description="Document chunk to classify")
    content: str = Field(..., description="Chunk content for classification")
    document_context: Optional[str] = Field(
        None,
        description="Parent document context (title, summary) for better classification"
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Ensure content is not empty."""
        if not v or len(v.strip()) == 0:
            raise ValueError("Content cannot be empty")
        return v


class ClassificationResult(BaseModel):
    """Result of knowledge classification."""
    chunk_id: UUID
    knowledge_type: KnowledgeType
    classification_confidence: Decimal = Field(
        ...,
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="LLM confidence score (0.0-1.0)"
    )
    is_multi_type: bool = Field(
        default=False,
        description="True if chunk spans multiple knowledge types"
    )
    multi_type_ids: Optional[List[UUID]] = Field(
        default=None,
        description="IDs of related classification results if multi-type"
    )
    reasoning: Optional[str] = Field(
        None,
        description="Explanation of classification decision"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# SEARCH SCHEMAS
# ============================================================================

class SearchFilters(BaseModel):
    """Filter options for knowledge search."""
    knowledge_types: Optional[List[KnowledgeType]] = Field(
        None,
        description="Filter by knowledge types (multi-select)"
    )
    freshness_min: Optional[int] = Field(
        None,
        ge=0,
        le=100,
        description="Minimum freshness score (0-100)"
    )
    team_id: Optional[UUID] = Field(
        None,
        description="Filter to specific team (defaults to current user's team)"
    )
    exclude_deprecated: bool = Field(
        default=True,
        description="Exclude deprecated knowledge"
    )


class SearchRequest(BaseModel):
    """Request for semantic knowledge search."""
    query: str = Field(..., min_length=3, description="Search query")
    filters: Optional[SearchFilters] = Field(default_factory=SearchFilters)
    limit: int = Field(default=10, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @field_validator("query")
    @classmethod
    def validate_query(cls, v: str) -> str:
        """Ensure query is at least 3 characters."""
        v = v.strip()
        if len(v) < 3:
            raise ValueError("Query must be at least 3 characters")
        return v


class SearchResultItem(BaseModel):
    """Individual search result item."""
    id: UUID = Field(..., description="Chunk ID")
    knowledge_type: KnowledgeType
    confidence_score: Decimal = Field(
        ...,
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Classification confidence"
    )
    freshness_score: Decimal = Field(
        ...,
        ge=Decimal("0.0"),
        le=Decimal("100.0"),
        description="Freshness score (0-100)"
    )
    source_doc: str = Field(..., description="Parent document title")
    source_author: Optional[str] = Field(None, description="Document author/creator")
    created_at: datetime
    content_preview: str = Field(..., description="First 200 chars of chunk content")
    embedding_similarity: Optional[Decimal] = Field(
        None,
        description="Cosine similarity score if semantic search used"
    )
    is_deprecated: bool = Field(default=False)


class SearchResponse(BaseModel):
    """Response from knowledge search."""
    items: List[SearchResultItem]
    total: int = Field(..., description="Total matching results")
    limit: int
    offset: int


# ============================================================================
# RECOMMENDATION SCHEMAS
# ============================================================================

class ProposalContext(BaseModel):
    """Context from proposal for knowledge recommendations."""
    rfp_summary: str = Field(
        ...,
        description="Summary of RFP/bid opportunity"
    )
    client_type: Optional[str] = Field(
        None,
        description="Type of client (e.g., manufacturing, healthcare)"
    )
    bid_amount: Optional[int] = Field(
        None,
        description="Bid amount in currency units"
    )
    selected_strategy: Optional[str] = Field(
        None,
        description="Selected proposal strategy"
    )
    additional_context: Optional[str] = Field(
        None,
        description="Any other relevant context"
    )


class RecommendationRequest(BaseModel):
    """Request for context-aware knowledge recommendations."""
    proposal_context: ProposalContext
    limit: int = Field(default=5, ge=1, le=20)


class RecommendationResultItem(BaseModel):
    """Individual recommendation result."""
    rank: int = Field(..., ge=1)
    chunk_id: UUID
    knowledge_type: KnowledgeType
    confidence_score: Decimal = Field(
        ...,
        ge=Decimal("0.0"),
        le=Decimal("1.0")
    )
    source_doc: str
    content_preview: str
    relevance_reason: str = Field(
        ...,
        description="Explanation of why this knowledge is relevant"
    )
    freshness_score: Decimal = Field(
        ...,
        ge=Decimal("0.0"),
        le=Decimal("100.0")
    )
    match_type: Optional[str] = Field(
        default="semantic",
        description="'semantic' for embedding match, 'keyword_fallback' for BM25"
    )


class RecommendationResponse(BaseModel):
    """Response from recommendation engine."""
    items: List[RecommendationResultItem]
    context_matched: List[str] = Field(
        ...,
        description="Context dimensions that matched (e.g., ['architecture', 'manufacturing'])"
    )
    fallback_used: bool = Field(
        default=False,
        description="True if keyword fallback was used due to embedding failure"
    )


# ============================================================================
# HEALTH DASHBOARD SCHEMAS
# ============================================================================

class KnowledgeBaseSize(BaseModel):
    """Knowledge base size metrics."""
    total_documents: int
    total_chunks: int
    storage_bytes: int


class CoverageItem(BaseModel):
    """Coverage metric for one knowledge type."""
    count: int
    percentage: int


class CoverageMetrics(BaseModel):
    """Knowledge type coverage."""
    capability: CoverageItem
    client_intel: CoverageItem
    market_price: CoverageItem
    lesson_learned: CoverageItem


class FreshnessMetrics(BaseModel):
    """Document freshness distribution."""
    less_than_1yr: int
    between_1_2yr: int
    more_than_2yr: int
    deprecated: int


class SearchAnalytics(BaseModel):
    """Search activity analytics."""
    total_searches_last_30d: int
    zero_result_queries: int
    top_queries: List[str]


class RecommendationFeedback(BaseModel):
    """User feedback on recommendations."""
    thumbs_up: int
    thumbs_down: int
    acceptance_rate: Decimal = Field(
        ...,
        ge=Decimal("0.0"),
        le=Decimal("1.0"),
        description="Ratio of thumbs-up to total feedback"
    )


class HealthMetrics(BaseModel):
    """Complete health metrics for knowledge base."""
    kb_size: KnowledgeBaseSize
    coverage: CoverageMetrics
    freshness: FreshnessMetrics
    search_analytics: SearchAnalytics
    recommendation_feedback: RecommendationFeedback
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FlatHealthMetrics(BaseModel):
    """
    Flat health metrics response for frontend KnowledgeHealthDashboard.

    Transforms nested HealthMetrics into the flat shape expected by the
    frontend HealthMetrics interface in KnowledgeHealthDashboard.tsx.
    """
    # KB size fields (from kb_size.*)
    kb_size_chunks: int = Field(..., description="Total knowledge chunks")
    kb_size_bytes: int = Field(default=0, description="Total storage bytes")

    # Coverage field (aggregate percentage across all types)
    coverage_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Overall classification coverage percentage"
    )

    # Freshness aggregate
    avg_freshness_score: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Average freshness score (0-100)"
    )

    # Organization sharing stats
    total_organizations: int = Field(default=0, description="Number of distinct orgs")
    total_shares: int = Field(default=0, description="Total org-wide shares")

    # Deprecation rate
    deprecation_rate: float = Field(
        default=0.0,
        ge=0.0,
        description="Percentage of knowledge marked deprecated"
    )

    # Distribution data for charts
    knowledge_type_distribution: dict = Field(
        default_factory=dict,
        description="Count per knowledge type: {capability: N, ...}"
    )
    confidence_distribution: dict = Field(
        default_factory=lambda: {"high": 0, "medium": 0, "low": 0},
        description="Count per confidence tier: {high, medium, low}"
    )

    # Trending topics (from usage logs or stub)
    trending_topics: List[dict] = Field(
        default_factory=list,
        description="List of {topic: str, occurrences: int}"
    )

    timestamp: datetime = Field(default_factory=datetime.utcnow)


class KnowledgeFeedbackRequest(BaseModel):
    """Request to submit feedback on a recommendation."""
    feedback_type: str = Field(
        ...,
        pattern="^(positive|negative)$",
        description="Feedback type: 'positive' or 'negative'"
    )
    proposal_context: Optional[dict] = Field(
        None,
        description="Optional proposal context for analytics"
    )


class KnowledgeFeedbackResponse(BaseModel):
    """Response after submitting recommendation feedback."""
    chunk_id: UUID
    feedback_type: str
    recorded: bool = Field(default=True)
    recorded_at: datetime = Field(default_factory=datetime.utcnow)


# ============================================================================
# LIFECYCLE MANAGEMENT SCHEMAS
# ============================================================================

class DeprecationRequest(BaseModel):
    """Request to deprecate knowledge."""
    is_deprecated: bool
    reason: Optional[str] = Field(None, max_length=500)


class DeprecationResponse(BaseModel):
    """Response after deprecation action."""
    id: UUID
    is_deprecated: bool
    freshness_score: Decimal = Field(
        ...,
        ge=Decimal("0.0"),
        le=Decimal("100.0")
    )
    updated_at: datetime


class SharingRequest(BaseModel):
    """Request to share knowledge org-wide."""
    shared_to_org: bool
    reason: Optional[str] = Field(None, max_length=500)


class SharingResponse(BaseModel):
    """Response after sharing action."""
    id: UUID
    shared_to_org: bool
    shared_at: datetime
    audit_id: UUID


class SharingAuditRecord(BaseModel):
    """Audit record for knowledge sharing."""
    id: UUID
    chunk_id: UUID
    shared_by: UUID
    shared_from_team_id: UUID
    shared_to_org: bool
    shared_at: datetime
    reason: Optional[str]
    created_at: datetime


# ============================================================================
# DATABASE MODELS (for ORM operations)
# ============================================================================

class KnowledgeMetadataDB(BaseModel):
    """Database model for knowledge_metadata table."""
    id: UUID
    chunk_id: UUID
    knowledge_type: KnowledgeType
    classification_confidence: Decimal
    is_deprecated: bool
    freshness_score: Decimal
    last_updated_at: datetime
    updated_by: Optional[UUID]
    multi_type_ids: Optional[List[UUID]]
    created_at: datetime

    class Config:
        from_attributes = True


class KnowledgeSharingAuditDB(BaseModel):
    """Database model for knowledge_sharing_audit table."""
    id: UUID
    chunk_id: UUID
    shared_by: UUID
    shared_from_team_id: UUID
    shared_to_org: bool
    shared_at: datetime
    reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============================================================================
# ERROR RESPONSE SCHEMAS
# ============================================================================

class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")


class EmbeddingUnavailableResponse(SearchResponse):
    """Search response when embeddings are temporarily unavailable."""
    fallback_used: bool = Field(default=True)
    error: Optional[str] = Field(
        default="EMBEDDING_UNAVAILABLE",
        description="Error code indicating embedding service issue"
    )
    error_message: Optional[str] = Field(
        default="Semantic search temporarily unavailable. Results use keyword search fallback.",
        description="Explanation of fallback behavior"
    )
