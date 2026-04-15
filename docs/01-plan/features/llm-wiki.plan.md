# llm-wiki Feature Plan

**Project:** Tenopa Proposal AI Coworker  
**Feature:** Knowledge Management System (llm-wiki)  
**Level:** Dynamic (Complex multi-service feature)  
**Phase:** PLAN (v1.0)  
**Last Updated:** 2026-04-11  

---

## Executive Summary

| Perspective | Description |
|---|---|
| **Problem** | Proposal writers spend 40% of time searching scattered organizational knowledge (past solutions, client data, market pricing, lessons). No semantic search or contextual recommendations exist. |
| **Solution** | Unified knowledge management system with semantic embeddings, auto-classification, vector search, and context-aware recommendations integrated into proposal workflow. |
| **Function & UX** | Search bar with 4 knowledge types + recommendations sidebar during proposal writing, showing source + confidence score. Classification automatic on ingestion. |
| **Core Value** | 40% time savings for proposal writers, 80%+ recommendation relevance, knowledge consolidation driving 15% proposal quality increase. |

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

## 1. Requirements

### 1.1 Functional Requirements

#### F1: Knowledge Classification System
- **Auto-classify documents on ingestion** into 4 types:
  - **capability** — Technical/domain expertise (e.g., "IoT platform experience")
  - **client_intelligence** — Client info, organizational structure, decision makers
  - **market_price_data** — Market rates, competitive pricing, salary benchmarks
  - **lesson_learned** — Post-project reflections, dos/don'ts, risks encountered
- LLM auto-classification with confidence score (0-100)
- Store classification metadata in `knowledge_metadata` table (new)
- Support multi-type documents: if document spans types, tag all applicable + add cross-reference

#### F2: Semantic Search Engine
- **Query by natural language** or keyword
- Return results ranked by semantic relevance (cosine similarity on embeddings)
- Filters:
  - Knowledge type (multi-select)
  - Knowledge age (freshness score: 0=stale, 100=recent)
  - Source (document_id, creator)
  - Team (if hierarchical permission selected)
- **Latency SLA**: <500ms for 5,000+ document KB
- Reuse `document_chunks` table + pgvector embeddings (80% backend ready)

#### F3: Contextual Recommendations
- **Recommendation API** (integration point with proposal writing workflow)
- Input: Proposal context (RFP summary, client type, bid amount, selected strategy)
- Output: Top 5 knowledge chunks ranked by relevance, each with:
  - Source: Document title + chunk #
  - Knowledge type + metadata
  - Confidence score (embedding similarity + classification confidence)
  - Creation date + author
- Use LangGraph hook in proposal workflow (recommendation node)
- Display in sidebar during proposal writing

#### F4: Knowledge Health Dashboard
- **Real-time metrics:**
  - KB size (total documents, chunks, storage used)
  - Knowledge coverage by type (% of 4 types)
  - Freshness distribution (how many <1yr old, >2yr old, deprecated)
  - Search usage (top queries, zero-result queries)
  - Recommendation accuracy (user acceptance rate: thumbs up/down)
- Accessible to knowledge managers + team leads
- Data refresh: every 24 hours (batch job)

#### F5: Multi-Tenant RLS & Sharing
- **Default: Team knowledge only** (same team_id = searchable)
- **Explicit sharing**: Knowledge manager can promote team knowledge → org-wide
- Supabase RLS policies enforce team/org boundaries
- Audit trail: log all sharing decisions (who shared, when, with whom)

#### F6: Knowledge Lifecycle
- **Hybrid model:**
  - Manual deprecation: Knowledge manager marks as "deprecated" (stays searchable, shown with "stale" badge)
  - Auto-freshness scoring: Documents >2yr old get freshness score <50 (reduces ranking but stays searchable)
  - No hard deletion: All knowledge archived in separate table (audit trail)

#### F7: Error Handling & Resilience
- **Embedding API failure:**
  - Document ingestion succeeds, queued for async embedding retry (task queue)
  - Fallback search: Use keyword/BM25 search for unembedded docs
  - UI notification: "Some recommendations unavailable, retrying..."
  - Recommendation endpoint returns partial results if embedding fails
- **Search/recommendation API errors:** Graceful degradation (keyword fallback)

### 1.2 Non-Functional Requirements

| NFR | Target | Rationale |
|---|---|---|
| Search latency | <500ms p95 | Proposal writers need instant feedback |
| Recommendation API | <1s response time | Sidebar recommendation during typing |
| Embedding retry | 24h max | No knowledge goes unembedded >1 day |
| Storage | Supabase pgvector (included) | No external vector DB cost |
| Uptime | 99.5% | Knowledge system critical path |
| Test coverage | ≥80% | Integration + unit tests |
| RLS enforcement | 100% | Zero privacy breaches |

---

## 2. Success Criteria

| # | Criterion | Measurement | Target |
|---|---|---|---|
| **SC-1** | Search latency | p95 response time (5,000+ KB) | <500ms |
| **SC-2** | Recommendation relevance | User acceptance rate (thumbs up/down) | ≥80% |
| **SC-3** | Knowledge coverage | All 4 types represented | ≥1 doc per type per team |
| **SC-4** | RLS enforcement | Audit: zero cross-team/org searches | 100% (0 breaches) |
| **SC-5** | API contract alignment | Design vs. implementation code match | ≥95% match |
| **SC-6** | Test coverage | Unit + integration + E2E | ≥80% |

---

## 3. Implementation Scope

### 3.1 Backend Files (Python/FastAPI)

**New Services:**
- `app/services/knowledge_classifier.py` — LLM-based auto-classification
- `app/services/knowledge_recommendation.py` — Recommendation engine (proposal context → top 5 chunks)
- `app/services/knowledge_health.py` — Dashboard metrics aggregation

**New API Routes:**
- `app/api/routes_knowledge.py`:
  - `POST /api/knowledge/search` — Semantic search with filters
  - `POST /api/knowledge/recommend` — Contextual recommendations
  - `GET /api/knowledge/health` — Dashboard metrics
  - `PUT /api/knowledge/{id}/deprecate` — Mark knowledge as stale
  - `PUT /api/knowledge/{id}/share` — Promote team → org knowledge

**DB Migrations:**
- `database/migrations/008_knowledge_tables.sql`:
  - `knowledge_metadata` — Classification + freshness metadata
  - `knowledge_sharing_audit` — Sharing decisions audit trail
  - (Reuse `document_chunks` + pgvector for embeddings)

**Modify Existing:**
- `app/services/document_ingestion.py` — Call knowledge_classifier after document chunking
- `app/api/deps.py` — Add `require_knowledge_access` (team/org RLS check)
- `app/graph/nodes/proposal_nodes.py` — Add recommendation hook (Phase 4B: Recommendations)

### 3.2 Frontend Files (TypeScript/React)

**New Components:**
- `frontend/components/KnowledgeSearchBar.tsx` — Search input + filters + results
- `frontend/components/KnowledgeRecommendations.tsx` — Sidebar recommendations during proposal editing
- `frontend/components/KnowledgeHealthDashboard.tsx` — Metrics visualization

**New Pages:**
- `frontend/app/(app)/knowledge/page.tsx` — KB main page (search + browse)
- `frontend/app/(app)/knowledge/health/page.tsx` — Manager dashboard

**Modify Existing:**
- `frontend/lib/api.ts` — Add knowledge search + recommend endpoints
- `frontend/app/(app)/proposals/[id]/page.tsx` — Integrate recommendation sidebar

### 3.3 Tests

**New Test Files:**
- `tests/unit/test_knowledge_classifier.py` — Classification accuracy (10 test cases per type)
- `tests/unit/test_knowledge_search.py` — Search filtering + ranking (15 tests)
- `tests/integration/test_knowledge_api.py` — API contract + RLS enforcement (20 tests)
- `frontend/e2e/knowledge-search.spec.ts` — E2E search workflow (Playwright)
- `frontend/e2e/knowledge-recommendation.spec.ts` — E2E recommendations during proposal writing (Playwright)

**Modify Existing:**
- `tests/integration/test_routes_documents.py` — Add classification tests post-ingestion

---

## 4. Risks & Mitigation

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| **R1: Embedding API quota exceeded** | Recommendations fail, fallback to keyword search | Medium | Queue retries with exponential backoff; monitor API usage; alert at 80% quota |
| **R2: Knowledge churn (outdated data)** | Stale recommendations reduce trust | High | Hybrid freshness model (manual deprecation + auto-scoring); dashboard monitoring |
| **R3: RLS misconfiguration** | Team knowledge leaks across teams | Medium | Comprehensive RLS unit tests; audit trail logging; pen test before go-live |
| **R4: Search performance degrades** | Latency >500ms with large KB | Low | Index strategy (pgvector + BM25 hybrid); caching layer (Redis if needed) |
| **R5: Classification accuracy <80%** | Poor recommendations reduce adoption | Medium | Start with high-confidence predictions (>90%); prompt engineering review; user feedback loop |

---

## 5. Dependencies & Integration Points

### 5.1 Upstream Dependencies
- **document_ingestion** (Phase C, 95% complete) — Provides document_chunks + embeddings table structure
- **Supabase pgvector** — Embedding storage + cosine similarity search (included in PostgreSQL)
- **Claude API** — Classification LLM + recommendation ranking

### 5.2 Integration Points
- **Proposal workflow (LangGraph)** — Recommendation node hooks into proposal_nodes.py (Phase 4B)
- **Supabase RLS** — Team/org boundaries enforced at DB layer (auth claims)
- **Document ingestion pipeline** — Auto-classification triggered post-chunking (modify document_ingestion.py)

### 5.3 Compatibility
- **Python 3.11+** — FastAPI async patterns
- **Supabase SDK** — Async client with RLS support
- **Next.js 15+** — React 19 component patterns
- **Backward compatibility** — No breaking changes to existing proposal/document APIs

---

## 6. Design Decisions (Locked)

| Decision | Rationale | Alternative Rejected |
|---|---|---|
| **D1: Auto-classification only** (no manual tags) | Faster ingestion, consistent taxonomy, LLM confidence score + user acceptance feedback for tuning | Manual-only (slower) / Hybrid (complexity) |
| **D2: Hybrid freshness model** | Balances knowledge preservation (no hard deletion) with trust (deprecated flagging + age scoring) | Hard deletion / TTL-only / No deprecation |
| **D3: Hierarchical sharing** (team default + explicit org sharing) | Protects team IP while enabling org-wide knowledge growth | Team-only (missed reuse) / Org-wide default (RLS complexity) |
| **D4: Keyword fallback on embedding failure** | Graceful degradation ensures search always works, no user-facing errors | Fail hard / Queue indefinitely (frustration) |
| **D5: Show source + confidence on recommendations** | Transparency builds trust; users understand why recommendation was suggested | Hide source (black box) / Confidence only (no traceability) |

---

## 7. Success Metrics & Monitoring

### Phase Metrics
- **Adoption:** % of proposal writers using search ≥50% within 30d
- **Engagement:** Avg. searches/recommendations per proposal ≥2
- **Recommendation feedback:** Thumbs up/down ratio ≥80% acceptance
- **KB growth:** >100 new docs/month across org

### Quality Metrics
- Search latency p95 <500ms
- Classification accuracy >85% (post-ingestion user feedback)
- RLS pass rate 100% (audit tests)
- Test coverage ≥80%

---

## 8. Implementation Phases (Session Guide)

### Phase 1: Foundation (Weeks 1-2)
- Database tables (knowledge_metadata, sharing_audit)
- Knowledge classifier service (LLM + confidence)
- Document ingestion integration (post-chunking classification)

### Phase 2: Search & API (Weeks 2-3)
- Knowledge search service (pgvector + BM25 hybrid)
- Search API + filtering
- RLS policies + audit logging

### Phase 3: Recommendations (Weeks 3-4)
- Recommendation engine (proposal context matching)
- Recommendation API + fallback
- Proposal workflow integration (LangGraph hook)

### Phase 4: UI & Dashboard (Weeks 4-5)
- Search bar component + results
- Recommendations sidebar
- Health dashboard (metrics page)

### Phase 5: Testing & Deployment (Weeks 5-6)
- Unit + integration tests (80%+ coverage)
- E2E tests (Playwright)
- Performance tuning + caching (if needed)
- Go-live + monitoring

---

## 9. Open Questions (For Design Phase)

1. Should recommendation results be cached? (Tradeoff: relevance vs. latency)
2. How many search results to return? (Pagination vs. top-N?)
3. Recommendation sidebar size limit? (Best practices from similar systems?)
4. Should team leads see KB health metrics for other teams? (Privacy vs. transparency)

---

## Appendix: Related Documentation

- **PRD:** (To be created from PM phase)
- **Design:** `docs/02-design/features/llm-wiki.design.md` (Next phase)
- **Document Ingestion (Phase C):** `docs/archive/2026-04/document_ingestion/`
- **Supabase RLS guide:** https://supabase.com/docs/guides/auth/row-level-security
- **pgvector docs:** https://github.com/pgvector/pgvector
