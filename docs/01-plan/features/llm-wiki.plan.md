# LLM-Wiki Implementation Plan

**Feature**: llm-wiki (Organizational Knowledge Management System)  
**Status**: PLAN Phase  
**Duration**: 4 weeks (2026-04-22 ~ 2026-05-20)  
**Phase Structure**: DO (2w) → CHECK (3d) → ACT (1w) → REPORT

---

## Objectives

1. **Semantic knowledge search** — 8 knowledge domains integrated (capabilities, customers, competitors, pricing, lessons learned, similar cases, outsourcers, documents)
2. **AI classification engine** — Auto-classify, tag, and recommend knowledge during proposal writing (target: 80%+ accuracy)
3. **Knowledge health dashboard** — Track quality, gaps, and utilization metrics
4. **Integration with proposal workflow** — Real-time contextual recommendations in STEP 2-4

---

## Architecture Overview

### Layer 1: Document Ingestion Pipeline
- Extend existing `document_ingestion.py` to collect from 8 sources:
  - Internal documentation (MSSQL legacy DB, Intranet)
  - Project archives (past proposals, win/loss analysis)
  - Knowledge bases (competitor intelligence, pricing databases)
  - Unstructured (emails, meeting notes via Teams API)

**Modules**:
- `services/knowledge_collector.py` — Source connectors (150 lines)
- `services/knowledge_preprocessor.py` — Normalization, dedup (100 lines)

### Layer 2: Classification & Tagging
- **Auto-classifier** — LLM-based multi-label classification into 8 domains
- **Entity extractor** — Extract customers, competitors, capabilities, pricing data
- **Relationship mapper** — Link related documents (similar cases, lessons learned)

**Modules**:
- `services/knowledge_classifier.py` — Classification engine (200 lines)
- `services/entity_extractor.py` — Entity recognition (150 lines)
- `services/knowledge_graph.py` — Graph construction & querying (180 lines)

### Layer 3: Vector Search & Retrieval
- Semantic search using Supabase `pgvector` (already integrated with vault)
- Hybrid search: keyword + semantic ranking
- Context-aware filtering by team/org/classification

**Modules**:
- `services/knowledge_searcher.py` — Hybrid search implementation (120 lines)
- `app/api/routes_knowledge.py` — REST API for search (80 lines)

### Layer 4: Contextual Recommendation Engine
- During proposal STEP 2/3/4, inject relevant knowledge recommendations
- Scoring: relevance + recency + team usage + accuracy
- Integrate with `graph/nodes/proposal_nodes.py`

**Modules**:
- `services/recommendation_engine.py` — Scoring & ranking (140 lines)
- `graph/nodes/knowledge_inject.py` — Proposal integration (60 lines)

### Layer 5: Knowledge Health & Metrics
- Track: documentation coverage, staleness, usage frequency, team engagement
- Dashboard views: org-level, team-level, domain-level
- Quality scorecards by domain

**Modules**:
- `services/knowledge_health_monitor.py` — Metrics collection (100 lines)
- `app/api/routes_knowledge_analytics.py` — Analytics API (70 lines)

---

## Database Schema Changes

**New Tables** (Supabase):

```sql
-- Knowledge documents (8 domains)
CREATE TABLE knowledge_docs (
  id UUID PRIMARY KEY,
  title TEXT,
  content TEXT,
  domain ENUM('capabilities','customers','competitors','pricing','lessons','similar_cases','outsourcers','documents'),
  source TEXT,
  team_id UUID REFERENCES teams(id),
  org_id UUID REFERENCES organizations(id),
  tags TEXT[],
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  embedding vector(1536) -- pgvector embedding
);

-- Entity extraction results
CREATE TABLE knowledge_entities (
  id UUID PRIMARY KEY,
  doc_id UUID REFERENCES knowledge_docs(id),
  entity_type TEXT, -- 'customer','competitor','capability','price'
  entity_value TEXT,
  confidence FLOAT,
  context TEXT
);

-- Knowledge usage tracking
CREATE TABLE knowledge_usage (
  id UUID PRIMARY KEY,
  doc_id UUID REFERENCES knowledge_docs(id),
  proposal_id UUID REFERENCES proposals(id),
  user_id UUID REFERENCES auth_users(id),
  context TEXT, -- which proposal section used this
  created_at TIMESTAMP
);

-- Health metrics
CREATE TABLE knowledge_metrics (
  org_id UUID REFERENCES organizations(id),
  domain TEXT,
  coverage_score FLOAT, -- % of capabilities documented
  staleness_days INT,
  usage_count INT,
  team_engagement FLOAT,
  month DATE,
  PRIMARY KEY (org_id, domain, month)
);
```

---

## Implementation Sprints

### Sprint 1: Ingestion & Classification (2026-04-22 ~ 2026-04-29)

**Tasks**:
- T1.1: Build document collector (MSSQL + Intranet sources)
- T1.2: Implement knowledge classifier (domain accuracy baseline)
- T1.3: Set up pgvector embeddings (batch encoding)
- T1.4: Create knowledge_docs table + migrations

**Success Criteria**:
- 1,000+ documents classified (>=80% accuracy)
- Embedding pipeline working
- CI/CD tests: 16/16 passing

**Blockers**: None identified

---

### Sprint 2: Search & Integration (2026-05-01 ~ 2026-05-08)

**Tasks**:
- T2.1: Implement hybrid search API (keyword + semantic)
- T2.2: Build recommendation engine (relevance scoring)
- T2.3: Integrate with proposal STEP 2/3 workflow
- T2.4: Dashboard analytics endpoints

**Success Criteria**:
- Search latency <500ms (p95)
- Recommendation adoption >25% in staging
- 12/12 integration tests passing

**Blockers**: Recommendation accuracy baseline (T1 dependency)

---

### Sprint 3: Health Monitoring & Optimization (2026-05-09 ~ 2026-05-20)

**Tasks**:
- T3.1: Knowledge health dashboard
- T3.2: Reranking engine (improve top-5 accuracy)
- T3.3: Performance tuning (parallel embedding, caching)
- T3.4: Team access controls (RLS) + audit logging

**Success Criteria**:
- Health dashboard live
- Semantic search accuracy >85%
- Response time SLA met
- Production-ready (8/8 security tests passing)

---

## Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Classification accuracy | >=80% | Confusion matrix on 100 docs |
| Search relevance | >=85% | NDCG@5 on query benchmark |
| Recommendation adoption | >=30% | % of recommendations used in proposals |
| Time saved per proposal | 40% reduction | Baseline: 2-4 hours → target: 1-2 hours |
| Knowledge coverage | >=90% | % of org capabilities documented |
| Team engagement | >=60% | % of teams using knowledge search |

---

## Risks & Mitigations

| Risk | Severity | Mitigation |
|------|----------|-----------|
| Low classification accuracy | High | Start with high-confidence docs, iterative tuning |
| Stale documents in index | High | Metadata validation + staleness monitoring |
| Integration complexity with proposal flow | Medium | Modular design, feature flags for gradual rollout |
| Performance at scale (10k+ docs) | Medium | Caching strategy + async indexing |

---

## Dependencies

- ✅ document_ingestion.py (existing — reuse pipeline)
- ✅ Supabase pgvector (already integrated with vault)
- ✅ Claude API (existing — use for classification)
- ❌ Knowledge graph DB (new — PostgreSQL extension)
- ❌ Embedding service (new or leverage existing)

---

## Effort Estimate

| Phase | Component | Lines | Hours | Resource |
|-------|-----------|-------|-------|----------|
| DO | Collector + Classifier | 450 | 24 | Backend |
| DO | Search + Recommendation | 320 | 20 | Backend |
| DO | Integration + Health | 210 | 16 | Backend |
| DO | **Tests + Docs** | **280** | **18** | **QA + Docs** |
| **DO Total** | | **1,260** | **78** | **Full team** |
| CHECK | Integration testing | — | 12 | QA |
| ACT | Optimization + fixes | — | 16 | Backend |
| REPORT | Metrics & learnings | — | 4 | PM |

**Total**: ~110 hours over 4 weeks (1 FTE)

