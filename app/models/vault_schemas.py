"""
Vault AI Chat - Pydantic schemas for request/response validation
Phase 1 implementation
"""

from typing import List, Dict, Optional, Literal, Any
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum


# ============================================================================
# Enums
# ============================================================================

class VaultSection(str, Enum):
    """Vault sections"""
    COMPLETED_PROJECTS = "completed_projects"
    COMPANY_INTERNAL = "company_internal"
    CREDENTIALS = "credentials"
    GOVERNMENT_GUIDELINES = "government_guidelines"
    COMPETITORS = "competitors"
    SUCCESS_CASES = "success_cases"
    CLIENTS_DB = "clients_db"
    RESEARCH_MATERIALS = "research_materials"


class QueryType(str, Enum):
    """Types of queries"""
    PROJECT_SEARCH = "project_search"
    BUDGET_ESTIMATE = "budget_estimate"
    TEAM_PERFORMANCE = "team_performance"
    CLIENT_HISTORY = "client_history"
    SKILL_CHECK = "skill_check"
    MARKET_RESEARCH = "market_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    MULTI_SECTION = "multi_section_synthesis"
    OTHER = "other"


class MessageRole(str, Enum):
    """Chat message roles"""
    USER = "user"
    ASSISTANT = "assistant"


# ============================================================================
# Request/Response Models
# ============================================================================

class VaultChatRequest(BaseModel):
    """Request for Vault AI Chat endpoint"""
    
    message: str = Field(..., description="User query message", min_length=1, max_length=2000)
    conversation_id: Optional[str] = Field(None, description="Existing conversation ID (for context)")
    scope: Optional[List[VaultSection]] = Field(None, description="Which sections to search")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters (date, team, etc.)")
    
    class Config:
        use_enum_values = True


class RoutingDecision(BaseModel):
    """Result of query routing/intent detection"""
    
    sections: List[VaultSection]
    query_type: QueryType
    confidence: float = Field(..., ge=0, le=1)
    filters: Dict[str, Any] = Field(default_factory=dict)
    reasoning: Optional[str] = None


class DocumentSource(BaseModel):
    """Reference to a source document"""

    document_id: str
    section: VaultSection
    title: str
    snippet: Optional[str] = None
    confidence: Optional[float] = None
    url_path: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class ChatMessage(BaseModel):
    """Single message in conversation"""
    
    id: Optional[str] = None
    role: MessageRole
    content: str
    sources: Optional[List[DocumentSource]] = None
    confidence: Optional[float] = None
    created_at: Optional[datetime] = None


class VaultChatResponse(BaseModel):
    """Response from Vault AI Chat endpoint"""
    
    response: str = Field(..., description="AI response text")
    confidence: float = Field(..., ge=0, le=1, description="Confidence in response (0-1)")
    sources: List[DocumentSource] = Field(default_factory=list, description="Source documents")
    validation_passed: bool = Field(True, description="Whether response passed 3-point validation")
    warnings: List[str] = Field(default_factory=list)
    message_id: Optional[str] = None
    
    class Config:
        use_enum_values = True


# ============================================================================
# Conversation Models
# ============================================================================

class ConversationCreate(BaseModel):
    """Create new conversation"""
    title: Optional[str] = None


class ConversationDetail(BaseModel):
    """Conversation with full message history"""
    
    id: str
    user_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    message_count: int
    messages: List[ChatMessage] = Field(default_factory=list)


class ConversationSummary(BaseModel):
    """Summary of conversation (for list view)"""
    
    id: str
    user_id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_message: Optional[str] = None
    message_count: int


# ============================================================================
# Document/Section Models
# ============================================================================

class VaultDocument(BaseModel):
    """Vault document (for any section)"""
    
    id: str
    section: VaultSection
    title: str
    content: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    embedding_id: Optional[str] = None
    
    class Config:
        use_enum_values = True


class ProjectMeta(BaseModel):
    """Metadata for completed project"""
    
    proposal_id: str
    client: str
    budget: Optional[float] = None
    currency: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration_months: Optional[int] = None
    team_size: Optional[int] = None
    team_members: List[str] = Field(default_factory=list)
    status: Literal["won", "lost", "no_go", "abandoned"]
    key_outcomes: Optional[List[str]] = None


class GovernmentGuideline(BaseModel):
    """Government guideline document"""
    
    guideline_id: str
    category: str
    title: str
    content: str
    effective_date: Optional[str] = None
    expiration_date: Optional[str] = None
    salary_rates: Optional[Dict[str, float]] = None  # role -> daily rate


# ============================================================================
# Search & Filter Models
# ============================================================================

class SearchFilter(BaseModel):
    """Filters for section search"""

    date_from: Optional[str] = None
    date_to: Optional[str] = None
    client: Optional[str] = None
    team_member: Optional[str] = None
    budget_min: Optional[float] = None
    budget_max: Optional[float] = None
    status: Optional[List[str]] = None
    keywords: Optional[List[str]] = None
    category: Optional[str] = None

    # Advanced metadata filters
    industry: Optional[str] = None
    tech_stack: Optional[List[str]] = None  # OR condition - any tech stack match
    team_size_min: Optional[int] = None
    team_size_max: Optional[int] = None
    duration_months_min: Optional[int] = None
    duration_months_max: Optional[int] = None


class SearchResult(BaseModel):
    """Single search result"""
    
    document: VaultDocument
    relevance_score: float = Field(..., ge=0, le=1)
    match_type: Literal["exact", "semantic", "metadata"]
    preview: Optional[str] = None


class SearchResults(BaseModel):
    """Batch search results"""
    
    section: VaultSection
    query: str
    results: List[SearchResult]
    total_count: int
    has_more: bool


# ============================================================================
# Streaming Models (SSE)
# ============================================================================

class VaultChatStreamToken(BaseModel):
    """SSE token event - streamed response text chunk"""

    event: str = "token"
    text: str


class VaultChatStreamSources(BaseModel):
    """SSE sources event - initial sources before token stream"""

    event: str = "sources"
    sources: List[DocumentSource]


class VaultChatStreamDone(BaseModel):
    """SSE done event - completion with final metadata"""

    event: str = "done"
    confidence: float = Field(..., ge=0, le=1)
    validation_passed: bool
    warnings: List[str] = Field(default_factory=list)
    message_id: Optional[str] = None


class VaultChatStreamError(BaseModel):
    """SSE error event - error during streaming"""

    event: str = "error"
    message: str
    code: Optional[str] = None


# ============================================================================
# Validation Models
# ============================================================================

class ValidationReport(BaseModel):
    """Validation report for response"""
    
    passed: bool
    confidence: float = Field(..., ge=0, le=1)
    source_coherence_score: float
    fact_alignment_score: float
    contradictions: List[str] = Field(default_factory=list)
    citations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class Contradiction(BaseModel):
    """Detected contradiction in response"""
    
    claim: str
    source_statement: str
    severity: Literal["critical", "major", "minor"]


# ============================================================================
# Export/Download Models
# ============================================================================

class ExportRequest(BaseModel):
    """Request to export documents"""
    
    document_ids: List[str]
    format: Literal["pdf", "word", "markdown"] = "pdf"
    include_metadata: bool = True


class ExportResponse(BaseModel):
    """Response for export request"""
    
    file_url: str
    file_name: str
    file_size: int
    format: str
    created_at: datetime


# ============================================================================
# Analytics Models
# ============================================================================

class ChatMetrics(BaseModel):
    """Metrics for chat session"""
    
    total_messages: int
    average_response_time_ms: float
    sources_cited: int
    validation_pass_rate: float
    low_confidence_count: int


class VaultStats(BaseModel):
    """Overall Vault statistics"""
    
    total_documents: int
    total_conversations: int
    total_messages: int
    sections_breakdown: Dict[VaultSection, int]
    avg_response_confidence: float
    avg_response_time_ms: float
    hallucination_rate: float
