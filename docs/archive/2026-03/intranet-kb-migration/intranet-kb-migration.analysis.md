# intranet-kb-migration Gap Analysis (v3)

> **Feature**: intranet-kb-migration
> **Plan Document**: v2.0 (`docs/01-plan/features/intranet-kb-migration.plan.md`)
> **Analysis Date**: 2026-03-27
> **Previous**: v3 (97%, archived) | **Current**: v4 (100%, GAP-1 + GAP-2 resolved)

---

## Overall Match Rate: 100%

| Category | Score | Status |
|----------|:-----:|:------:|
| Phase 1: DB + Migration | 100% | PASS |
| Phase 2: Scoring DB Conversion | 100% | PASS |
| Phase 3: Document Pipeline + Search | 100% | PASS |
| Phase 4: LangGraph Integration | N/A | Intentional Skip |
| Misc (config, routes, main) | 100% | PASS |
| Monthly Sync (Plan 외 추가 기능) | 100% | Added Feature |
| **Overall (Plan 대비)** | **100%** | **PASS** |

---

## Detailed Comparison

### Phase 1: DB Schema + Migration Script (7/8 PASS, 1 PARTIAL)

| # | Plan Item | Implementation | Status |
|---|-----------|----------------|--------|
| 1 | intranet_projects table (20+ columns, embedding, UNIQUE) | `017_intranet_documents.sql:7-57` | PASS |
| 2 | intranet_documents table (file_slot, CHECK) | `017_intranet_documents.sql:67-97` | PASS |
| 3 | document_chunks table (embedding, IVFFlat) | `017_intranet_documents.sql:105-127` | PASS |
| 4 | content_library ALTER (source_document_id) | `017_intranet_documents.sql:131-132` | PASS |
| 5 | search_document_chunks_by_embedding RPC | `017_intranet_documents.sql:136-177` | PASS |
| 6 | search_projects_by_embedding RPC | `017_intranet_documents.sql:181-212` | PASS |
| 7 | RLS (user + service, 3 tables) | `017_intranet_documents.sql:216-241` | PASS |
| 8 | migrate_intranet.py (pymssql, TDS7.0, cp949, 10 slots) | `scripts/migrate_intranet.py` (443 lines) | PASS |

**Item 1 (intranet_projects) — PASS:**
- 20+ metadata columns: PASS
- capability_id, client_intel_id FK: PASS
- market_price_id FK: PASS (v4 resolved, `017_intranet_documents.sql:49`)
- embedding vector(1536) + 4 indexes: PASS

**Item 8 (migrate_intranet.py) — Beyond Plan:**
- --incremental, --triggered-by, upsert, sync log API (Added Feature)

### Phase 2: Scoring DB Conversion (3/3 PASS)

| # | Plan Item | Implementation | Status |
|---|-----------|----------------|--------|
| 10 | 5-axis scoring (vector30+keyword20+client25+dept15+budget10) | `bid_scoring_service.py` | PASS |
| 11 | build_profile_from_db() | `bid_scoring_service.py` | PASS |
| 12 | load_profile() DB-first / JSON fallback | `scripts/bid_scoring.py` | PASS |

### Phase 3: Document Pipeline + Search (4/5 PASS, 1 PARTIAL)

| # | Plan Item | Implementation | Status |
|---|-----------|----------------|--------|
| 13 | 4-type chunking | `document_chunker.py` | PASS |
| 14 | process_document pipeline | `document_ingestion.py:26-114` | PASS |
| 15 | import_project (meta + embedding + KB seed) | `document_ingestion.py:143-238` | PASS |
| 16 | PPTX/XLSX extractor | `file_utils.py:146-278` | PASS |
| 17 | intranet_doc + intranet_project search areas | `knowledge_search.py:36-37,316-380` | PASS |

### Phase 4: LangGraph Integration (Intentional Skip)

research_gather, strategy_generate, context_helpers 확장은 Plan에서 별도 Phase로 분리. 향후 구현 예정.

### Misc (5/5 PASS)

| # | Plan Item | Implementation | Status |
|---|-----------|----------------|--------|
| 9 | migrate_intranet.env.example | `scripts/migrate_intranet.env.example` | PASS |
| 18 | config.py settings | `app/config.py:88-92` | PASS |
| 19 | main.py router registration | `app/main.py:203-204` | PASS |
| 20 | intranet_doc file category | `file_utils.py:277-279` | PASS |
| 21 | API endpoints (7 core + 3 sync = 10) | `routes_intranet.py` | PASS |

---

## Gaps (0 items — all resolved in v4)

### ~~GAP-1: market_price_id FK Missing~~ — RESOLVED

- **Fix applied**: `017_intranet_documents.sql:49` — `market_price_id UUID REFERENCES market_price_data(id)` 추가

### ~~GAP-2: market_price_data KB Seed Not Implemented~~ — RESOLVED

- **Fix applied**: `document_ingestion.py:320-350` — `_seed_market_price_data()` 구현 + `import_project()` 에서 호출

---

## Added Features (Plan 외, 10 items) — Monthly Auto-Sync

| # | Feature | File | Description |
|---|---------|------|-------------|
| A1 | intranet_sync_log table | `018_intranet_sync_log.sql` | 동기화 실행 이력 (type, status, statistics, host) |
| A2 | Incremental sync (upsert) | `migrate_intranet.py`, `document_ingestion.py`, `routes_intranet.py` | 기존 레코드 업데이트 |
| A3 | Sync start API | `routes_intranet.py` POST `/sync/start` | 동기화 시작 기록 |
| A4 | Sync complete API | `routes_intranet.py` POST `/sync/{id}/complete` | 통계 포함 완료 기록 |
| A5 | Sync status API | `routes_intranet.py` GET `/sync/status` | 대시보드용 조회 |
| A6 | Monthly sync check | `scheduled_monitor.py` `check_monthly_intranet_sync()` | 미실행 조직 탐지 |
| A7 | APScheduler job | `scheduled_monitor.py` CronTrigger(day=5, hour=9) | 매월 5일 09:00 KST |
| A8 | Windows Task Scheduler | `setup_monthly_sync.bat` | 매월 1일 09:00 자동 실행 |
| A9 | --triggered-by argument | `migrate_intranet.py` | manual/scheduler/api 구분 |
| A10 | Sync log RLS | `018_intranet_sync_log.sql` | user SELECT + service_role ALL |

---

## Score Calculation

```
Plan Requirements (Phase 4 intentional skip 제외): 21 items
  PASS:    21 items
  PARTIAL:  0 items (GAP-1, GAP-2 both resolved in v4)

Match Rate = 21/21 = 100%

Added Features: 10 items — all well-implemented
```

---

## Observations

| # | 내용 | 영향 |
|---|------|------|
| OBS-1 | Plan: 파일명 `016_*`, 실제: `017_*` (016 번호 선점) | None |
| OBS-2 | Plan: "8 endpoints", 실제: 7 core + 3 sync = 10 | Plan 초과 |
| OBS-3 | BAT 1일 실행, APScheduler 5일 검증 — 상호 보완 설계 | Good pattern |

---

## Recommended Actions

1. ~~GAP-1+2 수정~~ → **완료** (v4, 100% 달성)
2. **Plan v2.1 업데이트**: Section 5 "Monthly Auto-Sync" 추가 (A1~A10 반영)
3. **(Optional)** `/pdca report` 완료 보고서 생성
