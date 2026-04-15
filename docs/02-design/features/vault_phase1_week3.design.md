# Design: Vault AI Chat Phase 1 Week 3

**Feature**: vault_phase1_week3  
**Status**: Design (selected: Option B — Clean Architecture)  
**Created**: 2026-04-15  
**Architecture Selection**: Clean Architecture with Feature-Based Modularization

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

## 1. Overview

### 1.1 Architecture Decision

**Selected: Option B — Clean Architecture with Feature-Based Modularization**

The design separates concerns by feature category, creating:
- **Advanced Features Module** — Context + Regeneration + Citations
- **Performance Module** — Caching + Parallel Search + Bug Fixes
- **UX Module** — Suggestions + Sharing + Bookmarks

Each module has dedicated:
- Frontend components (in `frontend/components/Vault{Feature}*/`)
- Backend services (in `app/services/vault_*.py`)
- Database migrations (in `database/migrations/02X_*.sql`)
- Tests (in `tests/{unit,integration}/vault_*.test.ts`, `tests/services/test_vault_*.py`)

**Rationale**: Best separation of concerns, independent feature development, clear test boundaries, extensible for Phase 2+.

### 1.2 Module Map

```
Backend Services:
├── vault_context_manager.py (A.1 — context extraction)
├── vault_regeneration_service.py (A.2 — message regeneration + editing)
├── vault_citation_service.py (A.3 — citation parsing + source linking)
├── vault_cache_service.py (B.1 — already exists, extend for consistency)
├── vault_search_optimizer.py (B.2 — parallel search coordination)
├── vault_audit_logger.py (B.3 — audit log schema fixes)
├── vault_suggestion_engine.py (C.1 — search suggestions)
├── vault_sharing_service.py (C.2 — conversation sharing + public access)
└── vault_bookmarks_service.py (C.3 — bookmark CRUD + RLS)

Frontend Components:
├── components/Vault/Advanced/
│   ├── RegenerateButton.tsx (A.2)
│   ├── EditMessage.tsx (A.2)
│   └── CitationRenderer.tsx (A.3)
├── components/Vault/Performance/
│   └── (no new components, hooks-based optimization)
├── components/Vault/UX/
│   ├── SearchSuggestionDropdown.tsx (C.1)
│   ├── ShareConversationMenu.tsx (C.2)
│   └── BookmarkButton.tsx (C.3)
└── components/Vault/
    ├── VaultChat.tsx (enhanced with A.1-A.3)
    └── VaultSidebar.tsx (enhanced with C.2-C.3, bookmarks tab)

Database:
├── migrations/029_vault_query_cache.sql (B.1)
├── migrations/030_vault_conversation_sharing.sql (C.2)
└── migrations/031_vault_bookmarks.sql (C.3)
```

---

## 2. API Contract

### 2.1 New Endpoints

#### **A.1 Context Improvement** (internal, no new endpoint)
- Modifies: `POST /api/vault/chat` (adds context_hint parameter to routing)

#### **A.2 Regeneration/Editing**
```
POST /api/vault/messages/{message_id}/regenerate
Request: { conversation_id: string, variation?: float }
Response: { id: string, content: string, sources: Source[], confidence: number, timestamp: datetime }
```

#### **A.3 Citations** (internal, no new endpoint)
- Modifies: `POST /api/vault/chat` (system prompt enhancement)

#### **B.1 Caching** (internal, no new endpoint)
- Modifies: `/chat` endpoints (adds cache layer)

#### **B.2 Parallel Search** (internal, no new endpoint)
- Modifies: `_search_sections()` async call pattern

#### **B.3 Response Time Fixes** (internal, no new endpoint)
- Modifies: React polling loop + audit_logs schema

#### **C.1 Search Suggestions**
```
GET /api/vault/suggestions?q={query}&limit=5
Response: string[]  # [recent_query_1, document_title_1, recent_query_2, ...]
```

#### **C.2 Conversation Sharing**
```
PATCH /api/vault/conversations/{id}
Request: { title?: string }
Response: { id: string, title: string, updated_at: datetime }

POST /api/vault/conversations/{id}/share
Request: { is_public: boolean }
Response: { share_url: string, share_token: string }

GET /api/vault/shared/{share_token}
Response: { conversation: {...}, messages: Message[] }
```

#### **C.3 Bookmarks**
```
GET /api/vault/bookmarks?type={type}&limit=20
Response: BookmarkResponse[]

POST /api/vault/bookmarks
Request: { type: "message"|"document"|"conversation", target_id: string, note?: string }
Response: BookmarkResponse

DELETE /api/vault/bookmarks/{id}
Response: { success: boolean }
```

### 2.2 Request/Response Schemas

All endpoints follow standard envelope:
```typescript
interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  meta?: { total?: number, page?: number, limit?: number }
}
```

---

## 3. Database Schema

### 3.1 New Tables (with RLS)

#### vault_query_cache (B.1)
```sql
CREATE TABLE vault_query_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  cache_key TEXT UNIQUE NOT NULL,      -- SHA256(query+sections+filters)
  sections TEXT[] NOT NULL,
  response_json JSONB NOT NULL,        -- List[SearchResult] serialized
  hit_count INT DEFAULT 0,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL
);
CREATE INDEX idx_vault_query_cache_key ON vault_query_cache(cache_key);
CREATE INDEX idx_vault_query_cache_expires ON vault_query_cache(expires_at);
```

#### vault_conversation_sharing (C.2)
```sql
ALTER TABLE vault_conversations ADD COLUMN (
  share_token TEXT UNIQUE DEFAULT NULL,
  is_public BOOLEAN DEFAULT FALSE,
  shared_at TIMESTAMPTZ DEFAULT NULL
);
CREATE INDEX idx_share_token ON vault_conversations(share_token) WHERE share_token IS NOT NULL;
```

#### vault_bookmarks (C.3)
```sql
CREATE TABLE vault_bookmarks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  bookmark_type TEXT NOT NULL CHECK (bookmark_type IN ('message', 'document', 'conversation')),
  target_id TEXT NOT NULL,
  note TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
CREATE UNIQUE INDEX ON vault_bookmarks(user_id, bookmark_type, target_id);
CREATE INDEX ON vault_bookmarks(user_id, created_at DESC);

ALTER TABLE vault_bookmarks ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Users own bookmarks" ON vault_bookmarks
  USING (user_id = auth.uid());
```

### 3.2 Schema Migrations

| Migration | Purpose | Impact |
|-----------|---------|--------|
| 029_vault_query_cache.sql | Create cache table + cleanup function | New table, index |
| 030_vault_conversation_sharing.sql | Add sharing columns + constraints | ALTER vault_conversations |
| 031_vault_bookmarks.sql | Create bookmarks table + RLS | New table, RLS policy |

### 3.3 Audit Log Fix (B.3)

Fix vault_audit_logs schema mismatch:
```python
# Before (WRONG): INSERT (sections: array, conversation_id)
# After (CORRECT): INSERT (section: string, user_id, action, timestamp)

# In _log_analytics():
section = sections[0] if sections else None  # Use first section
db.vault_audit_logs.insert({
    'section': section,
    'user_id': current_user.id,
    'action': 'search',
    'query': query,
    'timestamp': datetime.now()
})
```

---

## 4. Frontend Component Architecture

### 4.1 Component Hierarchy

```
VaultChat.tsx (enhanced)
├── parseCitations() → CitationRenderer (A.3)
├── hover menu:
│   ├── RegenerateButton (A.2) → handleRegenerate()
│   ├── EditMessage (A.2) → handleEditMessage()
│   └── BookmarkButton (C.3) → handleBookmark()
└── message list → each message:
    ├── content (A.3 citations)
    ├── sources with badge (A.3)
    └── source click → scrollToSource()

VaultSidebar.tsx (enhanced)
├── conversation list:
│   ├── title edit (C.2) → handleTitleEdit()
│   ├── hover menu:
│   │   ├── "공유" button (C.2) → ShareConversationMenu
│   │   └── "..." menu (export, delete)
│   └── ShareConversationMenu.tsx
│       ├── "공유 링크 생성" → POST /conversations/{id}/share
│       ├── Copy to clipboard
│       └── "내보내기" → GET /conversations/{id}/export
├── tabs:
│   ├── "대화" (conversation list)
│   └── "북마크" (bookmarks tab) → BookmarksList.tsx
└── BookmarksList.tsx (C.3)
    ├── GET /api/vault/bookmarks
    ├── filter by type (message/document/conversation)
    └── each bookmark → scroll to context

VaultSearchBar.tsx (connected)
├── input with debounced suggestions
├── SuggestionDropdown (C.1)
│   ├── GET /api/vault/suggestions?q={query}
│   ├── recent queries
│   ├── matching documents
│   └── click → input.value + handleSearch()
└── on Enter → VaultChat.handleSendMessage()
```

### 4.2 State Management

**Hooks-based with Context where needed:**

```typescript
// hooks/useVaultChat.ts
const { messages, isStreaming, streamState, handleSendMessage, ... } = useVaultChat()

// hooks/useVaultCitations.ts (A.3)
const { parsedMessage, sources } = useVaultCitations(message)

// hooks/useBookmarks.ts (C.3)
const { bookmarks, isBookmarked, toggleBookmark } = useBookmarks(targetId, targetType)

// hooks/useShareConversation.ts (C.2)
const { shareToken, shareUrl, generateShareLink } = useShareConversation(conversationId)

// hooks/useSuggestions.ts (C.1)
const { suggestions, loading } = useSuggestions(query, 300)  // 300ms debounce

// hooks/useVaultChatStream.ts (B.3 fix)
// Modified to return Promise<VaultStreamState> instead of callback
const streamState = await startStream(params)
```

---

## 5. Backend Service Architecture

### 5.1 Service Interfaces

#### vault_context_manager.py (A.1)
```python
class VaultContextManager:
    @staticmethod
    def extract_context(messages: List[ChatMessage]) -> ContextSummary:
        """Extract topic hint + last 6 turns"""
        
    @staticmethod
    def build_user_message(message: str, context: List[ChatMessage]) -> str:
        """Inject context + topic hint into prompt"""
```

#### vault_regeneration_service.py (A.2)
```python
class VaultRegenerationService:
    @staticmethod
    async def regenerate_message(
        message_id: str, 
        conversation_id: str,
        variation: float = 0.1
    ) -> dict:
        """Load context, re-run chat pipeline, update DB"""
        
    @staticmethod
    async def edit_message(
        message_id: str,
        new_content: str
    ) -> dict:
        """Delete subsequent messages, re-run from edited point"""
```

#### vault_citation_service.py (A.3)
```python
class VaultCitationService:
    @staticmethod
    def parse_citations(text: str) -> Tuple[str, List[str]]:
        """Parse [출처 N] markers, return cleaned text + citation indices"""
        
    @staticmethod
    def inject_citation_instructions(system_prompt: str) -> str:
        """Enhance system prompt with citation format guide"""
```

#### vault_search_optimizer.py (B.2)
```python
class VaultSearchOptimizer:
    @staticmethod
    async def parallel_search(
        query: str,
        sections: List[str],
        filters: dict
    ) -> List[SearchResult]:
        """Use asyncio.gather() for concurrent section searches"""
```

#### vault_suggestion_engine.py (C.1)
```python
class VaultSuggestionEngine:
    @staticmethod
    async def get_suggestions(
        query: str,
        user_id: str,
        limit: int = 5
    ) -> List[str]:
        """Recent queries + document titles matching q"""
```

#### vault_sharing_service.py (C.2)
```python
class VaultSharingService:
    @staticmethod
    async def generate_share_token(conversation_id: str) -> str:
        """Create unique token, update DB"""
        
    @staticmethod
    async def get_shared_conversation(share_token: str) -> dict:
        """Fetch public conversation + messages"""
        
    @staticmethod
    async def export_conversation(conversation_id: str, format: str = "markdown") -> str:
        """Render messages as markdown/html"""
```

#### vault_bookmarks_service.py (C.3)
```python
class VaultBookmarksService:
    @staticmethod
    async def create_bookmark(
        user_id: str,
        bookmark_type: str,
        target_id: str,
        note: Optional[str] = None
    ) -> dict:
        """Insert bookmark, return response"""
        
    @staticmethod
    async def get_bookmarks(user_id: str, limit: int = 20) -> List[dict]:
        """Fetch user's bookmarks"""
        
    @staticmethod
    async def delete_bookmark(bookmark_id: str, user_id: str) -> bool:
        """Delete if user owns"""
```

### 5.2 API Endpoint Organization

**File: `app/api/routes_vault_chat.py` (enhanced)**

```python
# Existing endpoints (keep as-is)
@router.post("/chat")  # Enhanced: context_hint + caching + parallel search
@router.get("/conversations/{id}")

# New endpoints (A.2)
@router.post("/messages/{id}/regenerate")

# New endpoints (C.1)
@router.get("/suggestions")

# New endpoints (C.2)
@router.patch("/conversations/{id}")  # Title edit
@router.post("/conversations/{id}/share")
@router.get("/shared/{share_token}")
@router.get("/conversations/{id}/export")

# New endpoints (C.3)
@router.get("/bookmarks")
@router.post("/bookmarks")
@router.delete("/bookmarks/{id}")
```

---

## 6. Data Flow

### 6.1 Request Flow (Chat with all enhancements)

```
User Input (VaultChat)
  ↓
[B.3] useVaultChatStream.ts fix: stale closure → useRef + Promise-based polling
  ↓
POST /api/vault/chat
  ↓
[A.1] VaultContextManager.extract_context() → last 6 turns + topic hint
  ↓
[A.1] vault_router.route(query, context_hint) 
  ↓
[B.1] VaultCacheService.get_search(cache_key) → Check cache (30-min TTL)
  ↓
If cache miss:
  ├─[B.2] VaultSearchOptimizer.parallel_search() → asyncio.gather() for sections
  ├─[B.1] VaultCacheService.set_search() → Store result
  ├─[B.3] Fix vault_audit_logs.insert() → Correct schema
  └─Continue
  ↓
[A.3] VaultCitationService.inject_citation_instructions() + LLM call (streaming SSE)
  ↓
[A.3] parseCitations() in frontend → [출처 N] → <sup><a>[N]</a></sup>
  ↓
Render message with sources + hover buttons:
  ├─[A.2] RegenerateButton (regenerate_message endpoint)
  ├─[A.2] EditMessage (edit_message logic)
  └─[C.3] BookmarkButton (toggle bookmark)
```

### 6.2 Sidebar Flow (Sharing + Bookmarks)

```
VaultSidebar.tsx
  ├─ Conversation List:
  │   └─ Hover → ShareConversationMenu
  │       ├─ "공유" → POST /conversations/{id}/share → copy link
  │       ├─ "내보내기" → GET /conversations/{id}/export
  │       └─ share_token stored + is_public=TRUE
  │
  └─ Bookmarks Tab:
      ├─ GET /api/vault/bookmarks
      ├─ Display bookmarks by type
      ├─ Click → scroll to source
      └─ ⭐ toggle → POST/DELETE /bookmarks
```

### 6.3 Search Suggestions Flow

```
VaultSearchBar.tsx
  ├─ input.onChange → debounce 300ms
  ├─ GET /api/vault/suggestions?q={query}
  ├─ SuggestionDropdown displays:
  │   ├─ Recent queries (from vault_audit_logs)
  │   └─ Document titles (ILIKE '%q%')
  └─ Click → input.value = suggestion + handleSearch()
```

---

## 7. State Machines

### 7.1 Message Regeneration State

```
[Initial] → user clicks "재생성"
  ↓
[Regenerating] → POST /messages/{id}/regenerate in flight
  ↓ (success)
[Regenerated] → message updated in state, old content replaced
  ↓ (error)
[Error] → toast notification, revert to previous content
```

### 7.2 Bookmark Toggle State

```
[Unbookmarked] ←→ [Bookmarking]
  ↓ (success)
[Bookmarked] ←→ [Unbookmarking]
  ↓ (error)
[Error] → toast, revert
```

---

## 8. Test Plan

### 8.1 Unit Tests

**Backend:**
- `test_vault_context_manager.py` — Context extraction, topic detection
- `test_vault_citation_service.py` — Citation parsing regex, source linking
- `test_vault_cache_service.py` — Key generation, TTL, hit/miss
- `test_vault_search_optimizer.py` — Async gathering, timeout handling
- `test_vault_suggestion_engine.py` — Query matching, document title search

**Frontend:**
- `useVaultCitations.test.ts` — Parse [출처 N], render <sup>
- `useBookmarks.test.ts` — Toggle state, API calls
- `useShareConversation.test.ts` — Token generation, copy
- `useSuggestions.test.ts` — Debounce, API integration

### 8.2 Integration Tests

- `/chat` endpoint with caching + parallel search
- `/messages/{id}/regenerate` + message history updates
- `/conversations/{id}/share` + public access via share_token
- `/bookmarks` CRUD with RLS checks
- `/suggestions` with vault_audit_logs + vault_documents

### 8.3 E2E Tests (Playwright)

1. **A.2 Regeneration**: Send message → hover → click regenerate → new response appears
2. **A.3 Citations**: Response with [출처 1] → click → scroll to source #1
3. **C.1 Suggestions**: Type "AI" in search → dropdown shows 5 suggestions → click → search executes
4. **C.2 Sharing**: Conversation hover → click "공유" → copy link → open in incognito → see public conversation
5. **C.3 Bookmarks**: Click ⭐ on message → sidebar Bookmarks tab shows it → click → scroll to message
6. **B.1 Caching**: Same search 2x → 2nd is faster + vault_query_cache has row
7. **B.2 Parallel**: Monitor network tab → all section searches in parallel (not sequential)
8. **B.3 Streaming**: Stream completes in <2s (not 60s timeout)

### 8.4 Coverage Target

- Unit: 85%+
- Integration: 90%+
- E2E: 7/8 critical flows (100%)

---

## 9. Error Handling

### 9.1 API Errors

```python
# All endpoints return ApiResponse with error field
{
  "success": false,
  "error": "User not authenticated",
  "data": null
}

# HTTP status codes:
- 400 Bad Request — validation error (Zod)
- 401 Unauthorized — missing auth
- 403 Forbidden — RLS violation (bookmarks)
- 404 Not Found — conversation/message not found
- 500 Internal Server Error — unexpected (logged + team notified)
```

### 9.2 Frontend Error Handling

```typescript
try {
  await regenerateMessage(messageId)
} catch (error) {
  toast({
    title: "재생성 실패",
    description: error.message,
    variant: "destructive"
  })
  // Revert optimistic UI change
}
```

---

## 10. Performance Optimization

### 10.1 Caching Strategy

- **Search results**: 30-minute TTL (vault_query_cache)
- **Routing decisions**: 1-hour TTL
- **User suggestions**: Cached in component state (until next session)
- **Cache invalidation**: Manual via admin endpoint (future) or TTL expiry

### 10.2 Frontend Optimization

- **Debounced suggestions**: 300ms → reduce API calls
- **Memoized components**: RegenerateButton, CitationRenderer (prevent re-renders)
- **Lazy-loaded bookmarks**: Load only when tab opened
- **Image optimization**: Source badges use CSS badge pseudo-element (no extra img)

### 10.3 Database Optimization

- Indices on: cache_key, expires_at, share_token, user_id+created_at
- RLS policies on bookmarks (avoid full table scans)
- Auto-cleanup function: DELETE vault_query_cache WHERE expires_at < NOW() (hourly)

---

## 11. Implementation Guide

### 11.1 Phased Implementation

| Phase | Features | Duration | Deliverable | Estimated LOC |
|-------|----------|----------|-------------|---------------|
| **Phase 1** | B.3 (bugs) → A.1 (context) → B.2 (parallel) | 1 session | Bug fixes + improved routing | ~300 |
| **Phase 2** | A.3 (citations) → B.1 (caching) → A.2 (regeneration) | 1.5 sessions | Citations + cache + regenerate | ~500 |
| **Phase 3** | Frontend: citations + regenerate/edit buttons | 0.5 session | Enhanced UX | ~200 |
| **Phase 4** | C.1 (suggestions) → C.2 (sharing) → C.3 (bookmarks) | 1.5 sessions | Complete UX features | ~400 |

**Total: ~1400 LOC, 4.5 sessions (approximately 5-6 work days)**

### 11.2 Dependency Order

```
1. B.3 (audit_log fix + stale closure fix) — blocks everything
   ↓
2. A.1 (context manager) → B.2 (parallel search) — independent, parallel-safe
   ↓
3. B.1 (cache service) + A.3 (citations) — independent
   ↓
4. A.2 (regeneration) — depends on A.1 context
   ↓
5. Frontend A components (citations, regenerate buttons)
   ↓
6. C.1 (suggestions) — independent
   ↓
7. C.2 (sharing) → C.3 (bookmarks) — independent
   ↓
8. Frontend C components (suggestions, sharing, bookmarks)
   ↓
9. Integration + E2E testing
```

### 11.3 Session Guide

**Recommended session split for parallel work:**

```
Session 1 (1.5 days):
├─ Eng A: B.3 bug fixes (audit_log schema + stale closure)
├─ Eng B: A.1 context manager (parallel)
└─ Eng C: Setup database migrations (029-031), service interfaces

Session 2 (1 day):
├─ Eng A: B.2 parallel search optimizer + A.3 citation service
├─ Eng B: B.1 cache service enhancement + A.2 regeneration service
└─ Eng C: API endpoints (routes_vault_chat.py enhancements)

Session 3 (0.5 day):
├─ Eng A: Frontend A components (citations, regenerate buttons)
├─ Eng B: Frontend UX enhancements (VaultChat.tsx updates)
└─ Eng C: Unit tests for all services

Session 4 (1.5 days):
├─ Eng A: C.1 suggestion engine + C.2 sharing service
├─ Eng B: C.3 bookmarks service + RLS policies
├─ Eng C: Frontend C components (suggestions, sharing, bookmarks)
└─ All: Integration + E2E tests, bug fixes

Session 5 (0.5 day):
├─ All: Final QA, performance tuning, documentation
└─ Ship: Merge to main, deploy to staging
```

**Module-scoped implementation:**
```bash
# If working in sessions:
/pdca do vault_phase1_week3 --scope module-1    # B.3 bugs
/pdca do vault_phase1_week3 --scope module-2    # A.1 + B.2 + B.1 + A.3
/pdca do vault_phase1_week3 --scope module-3    # A.2 + Frontend A
/pdca do vault_phase1_week3 --scope module-4    # C.1 + C.2 + C.3 + Frontend C
/pdca do vault_phase1_week3 --scope module-5    # Testing + QA
```

---

## 12. Success Criteria Validation

| SC# | Criterion | Design Ref | How to Verify |
|-----|-----------|-----------|---|
| SC-1 | All 9 features implemented per spec | §11.1 phases | Code review + checklist |
| SC-2 | 34+ existing E2E tests passing (Week 2) | §8.3 | `pytest tests/integration/test_vault_phase1_week2.py` |
| SC-3 | New feature tests (34+) written + passing | §8.2-8.3 | `pytest tests/integration/test_vault_phase1_week3.py` |
| SC-4 | Design-implementation match ≥90% | §1.1 option B rationale | gap-detector analysis |
| SC-5 | Search cache hit rate >40% | §10.1 | Monitor vault_query_cache.hit_count |
| SC-6 | Streaming response time <2s | §6.1, §10.3 | Latency measurement in E2E test |
| SC-7 | Stale closure bug fixed (React poll) | §4.2, §6.1, §11.2 | E2E test: stream completes <2s |
| SC-8 | vault_audit_logs schema issue resolved | §3.3, §5.2 | No insert errors, all logs created |

---

## 13. Risk Mitigation

| Risk | Probability | Mitigation |
|-----|------------|-----------|
| Parallel work conflicts (merge) | Medium | Use feature branches, early integration testing |
| Cache invalidation issues | Low | Add manual invalidation endpoint, TTL testing |
| RLS policy bugs (bookmarks) | Low | Test each RLS policy independently |
| React hooks optimization failures | Low | Profile with React DevTools, use memo strategically |
| Database migration errors | Low | Test on staging, use transaction rollback |

---

## 14. Rollback Plan

| Feature | Rollback Steps |
|---------|---|
| B.3 (Bugs) | Keep (no breaking changes, only fixes) |
| A.1 (Context) | Revert context_hint parameter, use default context |
| A.2 (Regeneration) | DELETE /messages/{id}/regenerate endpoint, remove buttons |
| A.3 (Citations) | Remove system prompt injection, hide [출처 N] as plain text |
| B.1 (Caching) | Revert migration 029, remove cache.get() / cache.set() calls |
| B.2 (Parallel) | Revert to sequential `for section in sections:` loop |
| C.1 (Suggestions) | DELETE /suggestions endpoint, hide dropdown |
| C.2 (Sharing) | Revert migration 030, remove sharing UI |
| C.3 (Bookmarks) | Revert migration 031, remove bookmarks UI + RLS |

---

## 15. Documentation Plan

- Update API docs: 5 new endpoints + schemas
- Add inline comments: `// Design Ref: §{section} — {decision}`
- Vault Phase 1 Week 3 completion report (post-Check phase)
- Team wiki: Feature flag toggles (if needed for gradual rollout)

---

**Approval Sign-off**:  
✅ Option B (Clean Architecture) selected  
Ready for Do phase following PDCA cycle.
