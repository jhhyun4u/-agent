# llm-wiki Feature Design

**Project:** Tenopa Proposal AI Coworker  
**Feature:** Knowledge Management System (llm-wiki)  
**Level:** Dynamic  
**Architecture:** Option C — Pragmatic Balance  
**Phase:** DESIGN (v1.0)  
**Last Updated:** 2026-04-13  

---

## Context Anchor

| Aspect | Content |
|---|---|
| **WHY** | Organizational knowledge is an untapped competitive advantage. Centralizing it enables faster, better proposals and reduces rework from forgotten lessons. |
| **WHO** | Proposal writers (primary), knowledge managers (tagging/monitoring), team leads (coverage tracking). |
| **RISK** | Knowledge churn (outdated data), privacy breaches (team vs. org scope), embedding API failures breaking recommendations. |
| **SUCCESS** | <500ms search latency, >80% recommendation relevance, zero RLS breaches, 80%+ test coverage. |
| **SCOPE** | Knowledge ingestion + classification + semantic search + recommendations + health dashboard + multi-tenant RLS. |

---

## 1. Overview

### 1.1 Problem & Solution

**Problem:** Proposal writers spend 40% of time searching scattered organizational knowledge (past solutions, client data, market pricing, lessons learned). No semantic search or contextual recommendations exist.

**Solution:** Unified knowledge management system with semantic embeddings, auto-classification, vector search, and context-aware recommendations integrated into proposal workflow.

### 1.2 Scope & Boundaries

**In Scope:**
- Knowledge classification (auto-classify documents on ingestion into 4 types)
- Semantic search (pgvector + keyword hybrid)
- Contextual recommendations (proposal context → top 5 knowledge chunks)
- Knowledge lifecycle (deprecation + freshness scoring)
- Multi-tenant RLS (team/org boundaries)
- Health dashboard (KB metrics + search/recommendation analytics)

**Out of Scope:**
- Knowledge curation UI (manual tagging, categorization)
- Advanced ML recommendation tuning
- Knowledge versioning/branching
- Cross-org federation

---

## 2. Architecture Overview (Option C: Pragmatic Balance)

### 2.1 System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js + React)                   │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ SearchBar        │  │ Recommendations  │  │ Health       │  │
│  │ (pages/          │  │ Sidebar          │  │ Dashboard    │  │
│  │ knowledge)       │  │ (proposal editor)│  │ (pages/      │  │
│  └────────┬─────────┘  └────────┬─────────┘  │ knowledge/   │  │
│           │                     │            │ health)      │  │
└───────────┼─────────────────────┼────────────┴──────────────┘  │
            │                     │
            ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│              Backend APIs (FastAPI)                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ app/api/routes_knowledge.py                             │  │
│  │ - POST /api/knowledge/search                            │  │
│  │ - POST /api/knowledge/recommend                         │  │
│  │ - GET /api/knowledge/health                             │  │
│  │ - PUT /api/knowledge/{id}/deprecate                     │  │
│  │ - PUT /api/knowledge/{id}/share                         │  │
│  │                              (+ RLS via require_knowledge_access) │
│  └────────────────────┬─────────────────────────────────────┘  │
└───────────────────────┼──────────────────────────────────────┘  │
                        │
            ┌───────────┴────────────┬─────────────┐
            │                        │             │
            ▼                        ▼             ▼
    ┌──────────────────┐    ┌────────────────┐  ┌─────────────┐
    │ Knowledge        │    │ Document       │  │ Proposal    │
    │ Manager Service  │    │ Ingestion      │  │ Workflow    │
    │ (knowledge_      │    │ (existing)     │  │ (LangGraph) │
    │ manager.py)      │    │                │  │             │
    │                  │    │ Call:          │  │ Hooks into: │
    │ • Classifier     │    │ classifier()   │  │ recommend   │
    │ • Search         │    │ post-chunking  │  │ node        │
    │ • Recommendations│    └────────────────┘  └─────────────┘
    │ • Health metrics │
    └────────┬─────────┘
             │
    ┌────────▼────────────────────────────────────────┐
    │       Supabase PostgreSQL + pgvector           │
    │                                                 │
    │  ┌────────────────────────────────────────────┐ │
    │  │ Existing:                                  │ │
    │  │ - document_chunks (+ embeddings via      │ │
    │  │   pgvector extension)                     │ │
    │  │ - document (parent)                       │ │
    │  │                                            │ │
    │  │ New:                                       │ │
    │  │ - knowledge_metadata (classification)    │ │
    │  │ - knowledge_sharing_audit (RLS)          │ │
    │  │                                            │ │
    │  │ RLS Policies:                              │ │
    │  │ - Team knowledge (team_id match)          │ │
    │  │ - Org knowledge (shared = true)           │ │
    │  └────────────────────────────────────────────┘ │
    └─────────────────────────────────────────────────┘
```

### 2.2 Key Design Decisions

| Decision | Rationale | Implementation |
|---|---|---|
| **Reuse document_chunks** | Avoids duplicate embedding logic; pgvector already in place | Join knowledge_metadata with document_chunks on chunk_id |
| **Unified Knowledge Manager** | Single entry point; easier RLS enforcement; no cross-service messaging | `app/services/knowledge_manager.py` handles all knowledge ops |
| **Asyncio queue (not Celery)** | Simpler infrastructure; no ops overhead; fine for MVP | AsyncQueue for embedding retries; batch processing every 5min |
| **Supabase RLS (not app-level)** | DB-layer enforcement; zero privacy leaks possible | RLS policies on document_chunks + knowledge_metadata; verified in unit tests |
| **Hybrid search (pgvector + BM25)** | Semantic + keyword coverage; handles embedding failures gracefully | Primary: cosine_similarity on embeddings; Fallback: PostgreSQL FTS |

---

## 3. Data Model

### 3.1 New Tables

#### knowledge_metadata
**Purpose:** Classification + freshness scoring for knowledge chunks
```sql
CREATE TABLE knowledge_metadata (
  id UUID PRIMARY KEY,
  chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
  knowledge_type VARCHAR(50) NOT NULL, -- capability | client_intel | market_price | lesson_learned
  classification_confidence DECIMAL(3,2), -- 0.0-1.0 (LLM confidence)
  is_deprecated BOOLEAN DEFAULT false, -- Manually marked as stale
  freshness_score DECIMAL(3,2) DEFAULT 100, -- 0-100: auto-decay based on age
  last_updated_at TIMESTAMP DEFAULT now(),
  updated_by UUID, -- Knowledge manager ID
  multi_type_ids UUID[] DEFAULT NULL, -- For multi-type docs: other knowledge_metadata IDs
  created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_knowledge_metadata_chunk_id ON knowledge_metadata(chunk_id);
CREATE INDEX idx_knowledge_metadata_type ON knowledge_metadata(knowledge_type);
CREATE INDEX idx_knowledge_metadata_deprecated ON knowledge_metadata(is_deprecated);
```

#### knowledge_sharing_audit
**Purpose:** Track team → org knowledge sharing decisions
```sql
CREATE TABLE knowledge_sharing_audit (
  id UUID PRIMARY KEY,
  chunk_id UUID NOT NULL REFERENCES document_chunks(id) ON DELETE CASCADE,
  shared_by UUID NOT NULL REFERENCES auth.users(id),
  shared_from_team_id UUID NOT NULL,
  shared_to_org BOOLEAN DEFAULT true,
  shared_at TIMESTAMP DEFAULT now(),
  reason VARCHAR(500),
  created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_sharing_audit_chunk ON knowledge_sharing_audit(chunk_id);
CREATE INDEX idx_sharing_audit_team ON knowledge_sharing_audit(shared_from_team_id);
```

### 3.2 Schema Modifications

#### document_chunks (existing, modified)
- Add column: `is_knowledge_indexed BOOLEAN DEFAULT false` (tracks if classifier ran)
- Add trigger: After insert, enqueue classification job

### 3.3 RLS Policies

**Policy 1: Team Knowledge (Default)**
```sql
CREATE POLICY "team_knowledge_access" ON knowledge_metadata
  USING (
    -- User can see team's own knowledge
    EXISTS (
      SELECT 1 FROM document_chunks dc
      JOIN documents d ON dc.document_id = d.id
      WHERE dc.id = knowledge_metadata.chunk_id
        AND d.team_id = auth.jwt()->>'team_id'
    )
  );
```

**Policy 2: Org Knowledge (Shared)**
```sql
CREATE POLICY "org_knowledge_access" ON knowledge_metadata
  USING (
    -- User can see knowledge marked as shared org-wide
    EXISTS (
      SELECT 1 FROM knowledge_sharing_audit ksa
      WHERE ksa.chunk_id = knowledge_metadata.chunk_id
        AND ksa.shared_to_org = true
    )
    OR
    -- Original team can always see their own
    EXISTS (
      SELECT 1 FROM document_chunks dc
      JOIN documents d ON dc.document_id = d.id
      WHERE dc.id = knowledge_metadata.chunk_id
        AND d.team_id = auth.jwt()->>'team_id'
    )
  );
```

---

## 4. API Contract

### 4.1 Search Endpoint

```
POST /api/knowledge/search
Content-Type: application/json

Request:
{
  "query": "IoT platform architecture",
  "knowledge_types": ["capability", "lesson_learned"],  // Optional, multi-select
  "freshness_min": 50,  // Optional, 0-100
  "team_id": "team-001",  // Optional (default: current user's team)
  "limit": 10,
  "offset": 0
}

Response (200 OK):
{
  "items": [
    {
      "id": "chunk-123",
      "knowledge_type": "capability",
      "confidence_score": 0.92,
      "freshness_score": 85,
      "source_doc": "IoT Platform Case Study - Acme Corp",
      "source_author": "john.doe",
      "created_at": "2025-08-15T10:00:00Z",
      "content_preview": "Our IoT platform for Acme Corp included real-time sensor...",
      "embedding_similarity": 0.87
    }
  ],
  "total": 1,
  "limit": 10,
  "offset": 0
}

Error (400 Bad Request):
{
  "error": "INVALID_QUERY",
  "message": "Query must be at least 3 characters"
}

Error (401 Unauthorized):
{
  "error": "UNAUTHORIZED",
  "message": "User not authenticated"
}

Error (403 Forbidden):
{
  "error": "FORBIDDEN",
  "message": "No access to requested team knowledge"
}
```

### 4.2 Recommendation Endpoint

```
POST /api/knowledge/recommend
Content-Type: application/json

Request:
{
  "proposal_context": {
    "rfp_summary": "Build enterprise IoT platform with real-time analytics",
    "client_type": "manufacturing",
    "bid_amount": 500000,
    "selected_strategy": "architectural_innovation"
  },
  "limit": 5  // Top N recommendations
}

Response (200 OK):
{
  "items": [
    {
      "rank": 1,
      "chunk_id": "chunk-456",
      "knowledge_type": "capability",
      "confidence_score": 0.89,
      "source_doc": "Acme Corp IoT Case Study",
      "content_preview": "Successfully delivered IoT platform with 99.9% uptime...",
      "relevance_reason": "Similar architecture + manufacturing client",
      "freshness_score": 82
    }
  ],
  "context_matched": ["architecture", "manufacturing", "real_time"]
}

Error (503 Service Unavailable - Embedding Failure):
{
  "error": "EMBEDDING_UNAVAILABLE",
  "message": "Semantic search temporarily unavailable. Fallback: keyword-only search",
  "items": [
    {
      "rank": 1,
      "chunk_id": "chunk-789",
      "knowledge_type": "capability",
      "source_doc": "IoT Platform Guide",
      "content_preview": "...",
      "match_type": "keyword_fallback"
    }
  ]
}
```

### 4.3 Health Dashboard Endpoint

```
GET /api/knowledge/health?team_id=team-001

Response (200 OK):
{
  "kb_size": {
    "total_documents": 156,
    "total_chunks": 3240,
    "storage_bytes": 1250000
  },
  "coverage": {
    "capability": {
      "count": 1200,
      "percentage": 37
    },
    "client_intel": {
      "count": 980,
      "percentage": 30
    },
    "market_price": {
      "count": 650,
      "percentage": 20
    },
    "lesson_learned": {
      "count": 410,
      "percentage": 13
    }
  },
  "freshness": {
    "less_than_1yr": 2100,
    "between_1_2yr": 800,
    "more_than_2yr": 340,
    "deprecated": 45
  },
  "search_analytics": {
    "total_searches_last_30d": 1240,
    "zero_result_queries": 45,
    "top_queries": ["IoT platform", "manufacturing solutions", "pricing"]
  },
  "recommendation_feedback": {
    "thumbs_up": 1420,
    "thumbs_down": 280,
    "acceptance_rate": 0.84
  }
}
```

### 4.4 Deprecation Endpoint

```
PUT /api/knowledge/{chunk_id}/deprecate
Content-Type: application/json

Request:
{
  "is_deprecated": true,
  "reason": "Client information outdated (2021 data)"
}

Response (200 OK):
{
  "id": "chunk-123",
  "is_deprecated": true,
  "freshness_score": 15  // Auto-reduced
}

Requires: Knowledge Manager role
```

### 4.5 Sharing Endpoint

```
PUT /api/knowledge/{chunk_id}/share
Content-Type: application/json

Request:
{
  "shared_to_org": true,
  "reason": "Best practice solution applicable to all teams"
}

Response (200 OK):
{
  "id": "chunk-123",
  "shared_to_org": true,
  "shared_at": "2026-04-13T14:30:00Z",
  "audit_id": "audit-789"
}

Requires: Knowledge Manager role
```

---

## 5. Service Design

### 5.1 Knowledge Manager Service

**File:** `app/services/knowledge_manager.py`

```python
class KnowledgeManager:
    """Unified service for classification, search, recommendations, health metrics"""
    
    async def classify_chunk(
        self, 
        chunk_id: str, 
        content: str, 
        document_context: str
    ) -> ClassificationResult:
        """Auto-classify knowledge chunk using Claude API"""
        # 1. Call Claude with prompt: "Classify this knowledge chunk"
        # 2. Return: type + confidence + multi-type_ids if applicable
        # 3. Store in knowledge_metadata
        # 4. Log classification audit trail
        pass
    
    async def search(
        self,
        query: str,
        filters: SearchFilters,
        user_context: UserContext
    ) -> SearchResult:
        """Semantic + keyword hybrid search"""
        # 1. Validate RLS (user can access team/org knowledge?)
        # 2. Generate embedding for query (or skip if embedding unavailable)
        # 3. Search pgvector (cosine similarity >0.7)
        # 4. Fallback: PostgreSQL FTS if embedding fails
        # 5. Rank by embedding_similarity + freshness_score + freshness_penalty
        # 6. Apply filters (type, freshness, team)
        # 7. Return paginated results
        pass
    
    async def recommend(
        self,
        proposal_context: ProposalContext,
        user_context: UserContext,
        limit: int = 5
    ) -> RecommendationResult:
        """Context-aware recommendation engine"""
        # 1. Extract context dimensions: client_type, industry, strategy, etc.
        # 2. Build synthetic query from context
        # 3. Call search() internally with high similarity threshold
        # 4. Re-rank by context relevance + freshness
        # 5. Fallback to keyword search if embeddings unavailable
        # 6. Return with relevance_reason + confidence
        pass
    
    async def get_health_metrics(
        self,
        team_id: Optional[str] = None
    ) -> HealthMetrics:
        """Aggregate KB health metrics"""
        # 1. Count documents by type + freshness
        # 2. Calculate coverage percentages
        # 3. Fetch search analytics (last 30 days)
        # 4. Fetch recommendation feedback (acceptance rate)
        # 5. Cache result for 24 hours
        pass
    
    async def mark_deprecated(
        self,
        chunk_id: str,
        reason: str,
        user_id: str
    ) -> None:
        """Mark knowledge as deprecated"""
        # 1. Update knowledge_metadata.is_deprecated = true
        # 2. Set freshness_score = 15
        # 3. Log audit trail
        pass
    
    async def share_to_org(
        self,
        chunk_id: str,
        reason: str,
        user_id: str
    ) -> None:
        """Promote team knowledge → org-wide"""
        # 1. Verify user has knowledge_manager role
        # 2. Insert into knowledge_sharing_audit
        # 3. RLS policies automatically expose to all users
        pass
    
    async def retry_failed_embeddings(self) -> int:
        """Background job: Retry chunks missing embeddings"""
        # 1. Query: chunks with is_knowledge_indexed = false
        # 2. Batch embed (50 at a time, avoid rate limits)
        # 3. Update document_chunks.embedding_vector
        # 4. Mark is_knowledge_indexed = true
        # 5. Log success/failure counts
        # 6. Return count retried
        pass
```

### 5.2 Service Integration

**File:** `app/api/routes_knowledge.py`

```python
from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, require_knowledge_access
from app.services.knowledge_manager import KnowledgeManager

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])
knowledge_manager = KnowledgeManager()

@router.post("/search")
async def search_knowledge(
    request: SearchRequest,
    user: User = Depends(get_current_user),
    access: KnowledgeAccess = Depends(require_knowledge_access)
) -> SearchResponse:
    """Search organizational knowledge"""
    return await knowledge_manager.search(
        query=request.query,
        filters=request.get_filters(),
        user_context=UserContext(user_id=user.id, team_id=access.team_id)
    )

@router.post("/recommend")
async def get_recommendations(
    request: RecommendRequest,
    user: User = Depends(get_current_user),
    access: KnowledgeAccess = Depends(require_knowledge_access)
) -> RecommendationResponse:
    """Get context-aware recommendations for proposal"""
    return await knowledge_manager.recommend(
        proposal_context=request.proposal_context,
        user_context=UserContext(user_id=user.id, team_id=access.team_id),
        limit=request.limit
    )

@router.get("/health")
async def get_health_metrics(
    user: User = Depends(get_current_user)
) -> HealthMetrics:
    """Get KB health dashboard"""
    return await knowledge_manager.get_health_metrics(team_id=user.team_id)
```

### 5.3 Document Ingestion Integration

**File:** `app/services/document_ingestion.py` (modified)

```python
async def ingest_document(doc_path: str, ...):
    """Existing ingestion flow — add classifier call post-chunking"""
    
    chunks = await chunk_document(doc_path)
    
    # NEW: Classify each chunk
    for chunk in chunks:
        try:
            classification = await knowledge_manager.classify_chunk(
                chunk_id=chunk.id,
                content=chunk.content,
                document_context=doc_metadata
            )
            # Stored automatically in knowledge_metadata table
        except Exception as e:
            logger.warning(f"Classification failed for {chunk.id}: {e}")
            # Continue ingestion; retry later via background job
    
    return chunks
```

---

## 6. Frontend Component Architecture

### 6.1 Component Tree

```
knowledge/
├── page.tsx (Main KB page)
│   └── KnowledgeSearchBar.tsx
│       ├── SearchInput (query)
│       ├── Filters (type, freshness, team)
│       └── SearchResults
│           └── SearchResultCard (source, confidence, content)
│
├── health/
│   └── page.tsx (Health Dashboard)
│       └── KnowledgeHealthDashboard.tsx
│           ├── KBSize (docs, chunks, storage)
│           ├── Coverage (pie chart by type)
│           ├── Freshness (distribution)
│           └── SearchAnalytics (top queries, zero-results)
│
proposals/[id]/
└── page.tsx (Existing proposal editor — modified)
    ├── ProposalEditor (existing)
    └── KnowledgeRecommendations.tsx (new sidebar)
        ├── RecommendationCard (source, relevance_reason, feedback buttons)
        └── LoadingState / ErrorState / EmptyState
```

### 6.2 Key Components

**KnowledgeSearchBar.tsx**
- Input: query, filters (type, freshness, team)
- API: POST /api/knowledge/search
- Display: Results with source + confidence + preview
- Error: Keyword-only fallback if embedding unavailable

**KnowledgeRecommendations.tsx**
- Sidebar component (during proposal writing)
- Input: Proposal context (extracted from form state)
- API: POST /api/knowledge/recommend
- Display: Top 5 recommendations with relevance reasons
- Feedback: Thumbs up/down (logs to analytics)

**KnowledgeHealthDashboard.tsx**
- Metrics visualization (charts + tables)
- API: GET /api/knowledge/health
- Display: KB size, coverage, freshness, search analytics

---

## 7. Test Strategy

### 7.1 Unit Tests

**File:** `tests/unit/test_knowledge_classifier.py`
- Classify single chunk (10 test cases × 4 types = 40 tests)
- Confidence scoring accuracy
- Multi-type detection
- Edge cases: empty content, special characters, non-English

**File:** `tests/unit/test_knowledge_search.py`
- Semantic search ranking (cosine similarity)
- Filter application (type, freshness, team)
- Keyword fallback (embedding unavailable)
- Pagination

**File:** `tests/unit/test_knowledge_rls.py`
- Team knowledge RLS (user X cannot see team Y knowledge)
- Org knowledge access (shared chunks visible to all)
- Deprecation visibility (still searchable)

### 7.2 Integration Tests

**File:** `tests/integration/test_knowledge_api.py`
- Search endpoint (request/response shape)
- Recommend endpoint (context matching)
- Health endpoint (aggregation)
- Deprecation (updates correctly)
- Sharing (audit trail recorded)
- Embedding failure graceful degradation

**File:** `tests/integration/test_document_ingestion_with_classification.py`
- Full flow: document upload → chunking → classification
- Classification stored in knowledge_metadata
- Async retry on failure

### 7.3 E2E Tests

**File:** `frontend/e2e/knowledge-search.spec.ts`
- Navigate to /knowledge
- Type search query
- Apply filters
- Verify results display + clicking shows detail
- Verify error state (embedding unavailable)

**File:** `frontend/e2e/knowledge-recommendation.spec.ts`
- Open proposal editor
- Fill RFP context
- Verify recommendations sidebar appears
- Click recommendation (copies content or links to source)
- Verify feedback buttons work

---

## 8. Implementation Guide

### 8.1 Module Map (Session Guide)

**Module-1: Data Layer (Week 1)**
- Files: `database/migrations/008_knowledge_tables.sql` + `app/models/knowledge_schemas.py`
- Tasks:
  1. Create knowledge_metadata + knowledge_sharing_audit tables
  2. Add RLS policies (team + org access)
  3. Add indexes (chunk_id, type, freshness)
  4. Define Pydantic schemas (Classification, Health, etc.)
- Deliverable: DB schema + RLS verified in unit tests

**Module-2: Classification Service (Week 1-2)**
- Files: `app/services/knowledge_manager.py` (classify_chunk method)
- Tasks:
  1. Implement classify_chunk() with Claude API call
  2. Extract classification prompt + parse response
  3. Store classification in knowledge_metadata
  4. Add confidence scoring logic
  5. Handle multi-type documents
- Deliverable: Classification service (tested with 40 unit tests)

**Module-3: Search Service (Week 2)**
- Files: `app/services/knowledge_manager.py` (search method)
- Tasks:
  1. Implement semantic search (pgvector cosine similarity)
  2. Implement keyword fallback (PostgreSQL FTS)
  3. Add filters (type, freshness, team, offset)
  4. Implement RLS enforcement (require_knowledge_access)
  5. Add result ranking (similarity + freshness + age)
- Deliverable: Search service (tested with 15 unit tests)

**Module-4: Recommendation Engine (Week 2-3)**
- Files: `app/services/knowledge_manager.py` (recommend method)
- Tasks:
  1. Parse proposal context (client_type, strategy, etc.)
  2. Build synthetic query from context
  3. Call search() internally with high similarity threshold
  4. Re-rank by context relevance
  5. Add relevance_reason generation
- Deliverable: Recommendation engine (tested with 10 unit tests)

**Module-5: API Routes & Endpoints (Week 3)**
- Files: `app/api/routes_knowledge.py` (5 endpoints)
- Tasks:
  1. Implement POST /api/knowledge/search
  2. Implement POST /api/knowledge/recommend
  3. Implement GET /api/knowledge/health
  4. Implement PUT /api/knowledge/{id}/deprecate
  5. Implement PUT /api/knowledge/{id}/share
  6. Add error handling (RLS, embedding failure, validation)
- Deliverable: All 5 API endpoints (tested with 20 integration tests)

**Module-6: Document Ingestion Integration (Week 3)**
- Files: `app/services/document_ingestion.py` (modified) + background queue
- Tasks:
  1. Add classification call post-chunking
  2. Implement async retry queue for failed embeddings
  3. Add background job: retry_failed_embeddings()
  4. Schedule job to run every 5 minutes
- Deliverable: Full ingestion → classification pipeline

**Module-7: Frontend Components (Week 4)**
- Files: `frontend/components/Knowledge*.tsx` (3 components)
- Tasks:
  1. Build KnowledgeSearchBar (input + filters + results)
  2. Build KnowledgeRecommendations (sidebar + feedback)
  3. Build KnowledgeHealthDashboard (charts + metrics)
- Deliverable: 3 components + styling (Tailwind + shadcn/ui)

**Module-8: Frontend Pages (Week 4)**
- Files: `frontend/app/(app)/knowledge/page.tsx` + health subpage
- Tasks:
  1. Create /knowledge page (search + results)
  2. Create /knowledge/health page (dashboard)
  3. Integrate recommendations sidebar in proposal editor
  4. Add loading/error/empty states
- Deliverable: Full UI flow

**Module-9: Testing (Week 5)**
- Files: All test files (unit + integration + E2E)
- Tasks:
  1. Write unit tests (classifier, search, RLS)
  2. Write integration tests (API endpoints, ingestion)
  3. Write E2E tests (Playwright workflows)
  4. Verify 80%+ coverage
- Deliverable: Comprehensive test suite (80%+ coverage)

### 8.2 Recommended Session Plan

**Session 1 (2-3 hours):** Module-1 (Data Layer)
- Create DB tables + RLS policies
- Write Pydantic schemas
- Run migration test

**Session 2 (3-4 hours):** Module-2 + Module-3 (Classification + Search)
- Implement classify_chunk() + search()
- Write 40 unit tests
- Verify correctness

**Session 3 (3-4 hours):** Module-4 + Module-5 (Recommendations + APIs)
- Implement recommend() + API routes
- Test embedding failure graceful degradation
- Integration tests (20 tests)

**Session 4 (3-4 hours):** Module-6 + Module-7 (Integration + Frontend)
- Wire up document_ingestion classifier
- Build 3 React components
- Verify styling + responsive design

**Session 5 (2-3 hours):** Module-8 + Module-9 (Pages + Testing)
- Build /knowledge pages
- Write E2E tests (Playwright)
- Verify 80%+ coverage

### 8.3 Implementation Checklist

- [ ] **Module-1:** DB migration + RLS verified
- [ ] **Module-2:** Classification service (40 unit tests)
- [ ] **Module-3:** Search service (15 unit tests)
- [ ] **Module-4:** Recommendation engine (10 unit tests)
- [ ] **Module-5:** API routes (5 endpoints, 20 integration tests)
- [ ] **Module-6:** Document ingestion integration + background job
- [ ] **Module-7:** Frontend components (3 components)
- [ ] **Module-8:** Frontend pages (/knowledge + /knowledge/health)
- [ ] **Module-9:** E2E tests (2 test files, 80%+ coverage)
- [ ] **Performance:** Search <500ms p95, recommend <1s p95
- [ ] **RLS Security:** Zero cross-team leaks (100% RLS test pass rate)
- [ ] **Compatibility:** No breaking changes to proposal API

---

## 9. Design Reference Comments

When implementing, use these comment patterns to link code back to design decisions:

```python
# Design Ref: §2.1 — Pragmatic Balance: Reuse document_chunks table
# for embeddings, single knowledge_manager service entry point
class KnowledgeManager:
    async def search(self, ...):
        # Plan SC-1: Search latency <500ms p95
        # Design: Use pgvector cosine_similarity, cache results
        pass

# Design Ref: §3.3 — RLS Policies: DB-layer enforcement
# All knowledge queries must pass require_knowledge_access
@router.post("/search")
async def search_knowledge(
    access: KnowledgeAccess = Depends(require_knowledge_access)
) -> SearchResponse:
    # Plan SC-4: RLS enforcement (zero breaches)
    pass
```

---

## 10. Risks & Mitigation (Detailed)

| Risk | Severity | Mitigation |
|---|---|---|
| **Embedding API quota exceeded** | Medium | Monitor API usage; queue retries with exponential backoff; fallback to keyword-only search |
| **Knowledge churn (stale data)** | High | Hybrid freshness model; knowledge managers can deprecate; dashboard shows freshness distribution |
| **RLS misconfiguration** | High | Comprehensive RLS unit tests (10 tests); audit trail logging; pen test before production |
| **Search latency >500ms** | Medium | pgvector index strategy; partial caching (24h); optional Redis if needed post-MVP |
| **Classification accuracy <80%** | Medium | Start with high-confidence predictions (>90%); user feedback loop; prompt tuning |

---

## 11. Open Questions (Resolved for Design)

1. **Should recommendation results be cached?** ✅ Resolved: No caching in MVP (high freshness priority); can add Redis in Module-4 if needed
2. **How many search results?** ✅ Resolved: Pagination (limit=10, default); top 5 for recommendations
3. **Recommendation sidebar size?** ✅ Resolved: 5 recommendations max (balance detail vs. distraction)
4. **Should team leads see other teams' KB health?** ✅ Resolved: No in MVP (privacy first); team managers see their own metrics

---

## Appendix: Related Documents

- **Plan:** `docs/01-plan/features/llm-wiki.plan.md` (Requirements, Success Criteria)
- **Document Ingestion:** `docs/archive/2026-04/document_ingestion/` (Baseline embeddings)
- **Supabase RLS:** https://supabase.com/docs/guides/auth/row-level-security
- **pgvector:** https://github.com/pgvector/pgvector
- **LangGraph Proposal Integration:** `app/graph/nodes/proposal_nodes.py`
