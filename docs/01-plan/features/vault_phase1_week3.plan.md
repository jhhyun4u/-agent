# Plan: Vault AI Chat Phase 1 Week 3

**Feature**: vault_phase1_week3  
**Status**: Planning  
**Created**: 2026-04-15  
**Last Updated**: 2026-04-15

---

## Executive Summary

| Perspective | Description |
|---|---|
| **Problem** | Week 2 Vault Phase 1 (4-layer with SSE streaming, advanced filters, analytics) completed with 22/22 tests passing. Week 3 needs 9 more features across 3 categories to enhance user experience, improve performance, and add advanced capabilities. |
| **Solution** | Implement 3 feature categories sequentially: (A) Advanced Features (context, regeneration, citations), (B) Performance (caching, parallel search), (C) UX (suggestions, sharing, bookmarks). Prioritizes backend stability before frontend complexity. |
| **Function & UX Effect** | Users gain real-time response regeneration, inline citations with source linking, search autocomplete, conversation sharing, and bookmarks. Backend gains 30-min search cache and parallel section queries reducing latency by ~40%. |
| **Core Value** | Iterative improvement from Week 2 foundation: faster search, better conversation context, professional citation system. Positions Vault AI Chat as feature-complete for Phase 1. |

---

## Context Anchor

| Dimension | Details |
|---|---|
| **WHY** | Phase 1 Week 2 achieved core streaming + filtering. Week 3 adds polish (citations, sharing) + performance (caching, parallelization) + UX (autocomplete, bookmarks) to complete Phase 1 milestone. |
| **WHO** | Vault users (internal proposal team) searching organization knowledge base. Proposal managers need fast context + reusable conversations. Secondary: Admin monitoring analytics. |
| **RISK** | Stale closure bug in React polling (60s timeout). Schema mismatch in audit_logs table (sections array vs section TEXT). Missing VaultSearchBar connection in layout. Scope creep: 9 features in 1 week requires parallel work. |
| **SUCCESS** | All 9 features implemented + tested (34+ E2E tests). Zero test regressions from Week 2. Match Rate ≥90%. Streaming response time <2s. Search cache hit rate >40%. |
| **SCOPE** | 9 features: 3 backend endpoints, 2 new services, 3 DB migrations, 2 frontend components, ~1500 lines of code. No schema breaking changes. Backward compatible with existing Vault API. |

---

## 1. Requirements

### High-Level Goals
- Complete Vault AI Chat Phase 1 with polished features
- Achieve 90%+ design-implementation alignment
- Maintain test coverage ≥80%
- Improve search latency by 30-40% via caching + parallelization

### Functional Requirements

#### Category A: Advanced Features
- **A.1 Context Improvement**: Extend user message context from 3 to 6 turns + extract conversation topic → improve routing accuracy
- **A.2 Regeneration/Editing**: POST /messages/{id}/regenerate endpoint + UI buttons (regenerate for assistant, edit for user messages)
- **A.3 Source Citations**: System prompt instructs model to mark claims with [출처 N] + frontend parser converts to clickable superscripts

#### Category B: Performance Optimization  
- **B.1 Caching**: DB-based query cache (vault_query_cache table, 30-min TTL for search, 1-hour for routing decisions)
- **B.2 Parallel Search**: Convert sequential section search loop to `asyncio.gather()` for 2-3 concurrent API calls
- **B.3 Response Time**: Fix stale closure bug in React polling (60s timeout), fix vault_audit_logs schema mismatch (sections array → section TEXT)

#### Category C: User Experience
- **C.1 Search Suggestions**: GET /suggestions endpoint returning recent queries + matching document titles + debounced autocomplete dropdown
- **C.2 Conversation Sharing**: share_token + is_public columns on vault_conversations, POST /conversations/{id}/share returns shareable URL, GET /shared/{token} for public access
- **C.3 Bookmarks**: vault_bookmarks table (message/document/conversation), UI buttons to toggle bookmarks, sidebar "Bookmarks" tab

### Non-Functional Requirements
- **Performance**: Search latency <800ms (cached) / <1.2s (fresh)
- **Reliability**: Zero new test failures, 100% backward compatibility
- **Accessibility**: All new UI elements keyboard-navigable, ARIA labels on hover buttons
- **Security**: RLS on bookmarks table, auth check on share endpoints, no secrets in error messages

---

## 2. Implementation Strategy

### Approach: Sequential Implementation by Category

**Rationale**: 
- Categories A & B have backend-heavy dependencies (schemas, services)
- Category C depends on stabilized backend from A & B
- Each category has independent features → lower merge conflict risk

### Phasing Plan

| Phase | Features | Duration | Deliverable |
|-------|----------|----------|-------------|
| **Phase 1** | B.3 (bug fixes) → A.1 (context) → B.2 (parallelization) | 2 sessions | Stable backend, improved routing + search speed |
| **Phase 2** | A.3 (citations) → B.1 (caching) → A.2 (regeneration) | 2 sessions | Citations + cache service + regeneration endpoint |
| **Phase 3** | Frontend: citation parser, regenerate/edit buttons, hover UX | 1 session | Frontend UI for A.2 + A.3 |
| **Phase 4** | C.1 (suggestions) → C.2 (sharing) → C.3 (bookmarks) | 2 sessions | Complete UX features |

### Key Implementation Files

**Backend**:
- `app/api/routes_vault_chat.py` — 5 new endpoints, cache integration
- `app/models/vault_schemas.py` — 4 new Pydantic models
- `app/services/vault_cache_service.py` — NEW, caching logic
- `app/services/vault_query_router.py` — context_hint parameter

**Database**:
- `database/migrations/029_vault_query_cache.sql` — NEW
- `database/migrations/030_vault_conversation_sharing.sql` — NEW
- `database/migrations/031_vault_bookmarks.sql` — NEW

**Frontend**:
- `frontend/components/VaultChat.tsx` — citation parser, hover buttons, regenerate/edit handlers
- `frontend/components/VaultSearchBar.tsx` — suggestions dropdown
- `frontend/components/VaultSidebar.tsx` — conversation title edit, sharing, bookmarks tab

---

## 3. Assumptions & Constraints

### Assumptions
- Week 2 tests (22/22) remain passing after Week 3 changes
- Redis not available → DB-based caching using existing `g2b_cache` pattern
- VaultSearchBar.tsx UI is complete (just needs connection + suggestions logic)
- Claude Sonnet API available with streaming support

### Constraints
- No breaking changes to existing Vault API endpoints
- RLS policies must be applied to vault_bookmarks table
- Streaming must not exceed 60s timeout (fix stale closure bug first)
- New migrations must be idempotent (safe to re-run)

---

## 4. Success Criteria

| # | Criterion | How to Verify |
|---|-----------|---|
| SC-1 | All 9 features implemented per spec | Code review + feature checklist |
| SC-2 | 34+ existing E2E tests still passing | `uv run pytest tests/integration/test_vault_phase1_week2.py` |
| SC-3 | New feature tests written + passing | `uv run pytest tests/integration/test_vault_phase1_week3.py` |
| SC-4 | Design-implementation match ≥90% | gap-detector analysis |
| SC-5 | Search cache hit rate >40% (if tested) | Monitor vault_query_cache table |
| SC-6 | Streaming response time <2s | End-to-end latency measurement |
| SC-7 | Stale closure bug fixed (React poll loop) | Manual test: stream completes <2s, not 60s timeout |
| SC-8 | vault_audit_logs schema issue resolved | No insert errors, all logging rows created successfully |

---

## 5. Risks & Mitigation

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| Stale closure bug is broader than detected | Medium | High | Fix early in Phase 1, write test case to prevent regression |
| Schema mismatch causes production data loss | Low | Critical | Test migrations on staging before merging, use transaction rollback |
| Scope creep (9 features in 1 week) | High | Medium | Strict feature cutoff at EOD, defer nice-to-haves to Week 4 |
| React polling loop still hangs after fix | Low | High | Implement Promise-based alternative, add timeout safety net |
| Caching invalidates stale data unexpectedly | Low | Medium | Add manual invalidation endpoint, test TTL expiration edge cases |

---

## 6. Testing Strategy

### Unit Tests
- Cache service: `test_vault_cache_service.py` (key generation, TTL, hit/miss)
- Routing decision with context_hint
- Citation parser regex matching

### Integration Tests
- Full /chat flow with caching enabled
- /messages/{id}/regenerate endpoint with DB updates
- /conversations/{id}/share, GET /shared/{token}
- Bookmarks CRUD operations

### E2E Tests
- Complete conversation: send → regenerate → edit → bookmark → share
- Search autocomplete: debounce + dropdown interaction
- Citation click → source scroll + highlight

---

## 7. Rollback Plan

| Feature | Rollback Steps |
|---|---|
| B.1 (Caching) | Revert 029 migration, remove VaultCacheService calls from /chat endpoints |
| B.2 (Parallel) | Revert asyncio.gather loop back to sequential `for` loop |
| A.2 (Regenerate) | Revert POST /messages/{id}/regenerate endpoint, remove hover buttons from VaultChat |
| C.2 (Sharing) | Revert 030 migration, remove share endpoints |
| C.3 (Bookmarks) | Revert 031 migration, remove bookmark endpoints + UI |

---

## 8. Documentation Plan

- Update API docs: 5 new endpoints + cache behavior
- Add code comments: Design Ref in each feature (e.g., `// Design Ref: §B.1 — cache integration`)
- Vault Phase 1 Week 3 completion report (after Check phase)

---

**Approval Sign-off**:  
Ready for Design phase following PDCA cycle.
