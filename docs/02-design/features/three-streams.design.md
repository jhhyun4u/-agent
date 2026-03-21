# §34. 3-Stream 병행 업무 설계 (v1.0)

**작성일**: 2026-03-21
**상태**: 구현 완료 (Match Rate 98%)

---

## 1. 개요

Go/No-Go 결정 이후 3가지 업무가 병행 진행되는 구조:

| Stream | 성격 | 구현 방식 |
|--------|------|----------|
| Stream 1: 정성제안서 | AI-heavy | 기존 LangGraph StateGraph (28노드) |
| Stream 2: 비딩 가격 관리 | 의사결정-heavy | 독립 서비스 (`bidding_stream.py`) |
| Stream 3: 제출서류 준비 | 행정-heavy | 독립 서비스 (`submission_docs_service.py`) |

## 2. 아키텍처 결정: Option C Hybrid

| 근거 | 설명 |
|------|------|
| Stream 1 유지 | 기존 28노드 StateGraph 변경 불필요 |
| Stream 2/3 독립 | AI 노드 불필요 (CRUD+상태머신). LangGraph interrupt/checkpoint 불필요 |
| State 격리 | ProposalState 36필드에 추가 없음. 각 스트림 자체 DB 테이블 |
| 비동기 병행 | Stream 1 리뷰 게이트 대기 중에도 Stream 2/3 독립 진행 |

## 3. DB 스키마

### 3-1. `submission_documents` (Stream 3)

```
id UUID PK, proposal_id FK, doc_type, doc_category(5종), required_format(5종),
required_copies, source(rfp_extracted|manual|template_matched),
status(pending|assigned|in_progress|uploaded|verified|rejected|not_applicable|expired),
assignee_id FK, deadline, priority(high|medium|low), notes,
file_path, file_name, file_size, file_format, uploaded_by FK, uploaded_at,
verified_by FK, verified_at, rejection_reason,
sort_order, rfp_reference, created_at, updated_at
```

### 3-2. `stream_progress` (오케스트레이션)

```
id UUID PK, proposal_id FK, stream(proposal|bidding|documents),
status(not_started|in_progress|blocked|completed|error),
progress_pct(0-100), current_phase, blocked_reason,
started_at, completed_at, metadata JSONB, updated_at
UNIQUE(proposal_id, stream)
```

### 3-3. `org_document_templates` (조직 공통 서류)

```
id UUID PK, org_id FK, doc_type, doc_category, required_format,
file_path, file_name, file_size,
valid_from DATE, valid_until DATE, auto_include BOOLEAN,
uploaded_by FK, notes, created_at, updated_at
UNIQUE(org_id, doc_type)
```

### 3-4. `proposals` 확장

- `streams_ready` JSONB — `{"proposal":false,"bidding":false,"documents":false}`
- `submission_gate_status` TEXT — `pending` | `submitted`

## 4. 백엔드 서비스

### 4-1. `stream_orchestrator.py`

- `initialize_streams(proposal_id)` — Go 결정 시 3개 stream_progress 레코드 UPSERT
- `update_stream_progress()` — 진행률 갱신 + streams_ready 자동 동기화
- `get_streams_status()` — 3개 스트림 통합 조회 + convergence 판단
- `check_convergence()` — 최종 제출 가능 여부
- `mark_final_submission()` — 3개 모두 completed 확인 후 proposals 상태 갱신

### 4-2. `submission_docs_service.py`

- `extract_checklist_from_rfp()` — Claude API 1회 호출 → JSON 배열 추출 + org_document_templates 자동 병합 (유효기간 만료 시 expired 경고)
- CRUD: `get_checklist()`, `add_document()`, `update_document_status()`, `delete_document()`, `assign_document()`
- 파일: `upload_document()` (Supabase Storage), `validate_document()` (포맷 검증)
- 점검: `check_documents_ready()` — 미배정/미검증/만료 경고
- 조직: `get_org_templates()`, `upsert_org_template()`, `delete_org_template()`

### 4-3. `bidding_stream.py`

- `get_bidding_workspace()` — 확정가 + 시나리오 + 이력 + 시장요약 통합
- `update_bid_price_post_workflow()` — 사유 필수 가격 조정 + bid_price_history 기록
- `get_market_tracking_summary()` — pricing_simulations에서 최신 결과 조회

## 5. API 엔드포인트 (16개)

### 5-1. 스트림 오케스트레이션 (3개)

| Method | Path | 설명 |
|--------|------|------|
| GET | `/api/proposals/{id}/streams` | 3개 스트림 통합 상태 |
| GET | `/api/proposals/{id}/streams/{stream}` | 단일 스트림 상세 |
| POST | `/api/proposals/{id}/streams/final-submit` | 최종 제출 (lead+) |

### 5-2. 제출서류 (8개) + 조직 공통 서류 (3개)

| Method | Path | 설명 |
|--------|------|------|
| GET | `.../submission-docs` | 체크리스트 |
| POST | `.../submission-docs/extract` | AI 추출 |
| POST | `.../submission-docs` | 수동 추가 |
| PUT | `.../submission-docs/{doc_id}` | 상태/담당 변경 |
| DELETE | `.../submission-docs/{doc_id}` | 삭제 |
| POST | `.../submission-docs/{doc_id}/upload` | 파일 업로드 |
| POST | `.../submission-docs/{doc_id}/verify` | 검증 완료 |
| GET | `.../submission-docs/readiness` | 사전 점검 |
| GET | `/api/org/{org_id}/document-templates` | 공통 서류 목록 |
| POST | `/api/org/{org_id}/document-templates` | 등록/갱신 |
| DELETE | `/api/org/{org_id}/document-templates/{id}` | 삭제 |

### 5-3. 비딩 확장 (2개)

| Method | Path | 설명 |
|--------|------|------|
| PUT | `.../bid-submission/adjust` | 가격 조정 |
| GET | `.../bidding-workspace` | 통합 대시보드 |

## 6. 그래프 통합 (최소 변경)

- **Go 결정 훅**: `review_node.py` → `_fire_stream_initialization()` (asyncio.create_task)
  - `initialize_streams()` + `extract_checklist_from_rfp()` 백그라운드 실행
- **Stream 1 완료 훅**: `graph.py` → `stream1_complete_hook` 노드
  - `review_ppt` approved, `document_only` 양쪽 경로에서 END 전 경유
- **워크플로 응답**: `/start`, `/state`, `/resume`에 `streams_status` 포함

## 7. 프론트엔드 UI

### 7-1. 인프라 컴포넌트

| 컴포넌트 | 역할 |
|----------|------|
| `StreamProgressHeader.tsx` | 3-스트림 미니 진행바 (헤더 상시 노출) |
| `StreamTabBar.tsx` | 4탭 전환 + 상태 뱃지 |

### 7-2. 탭별 컨텐츠

| 탭 | 컴포넌트 | 기능 |
|---|----------|------|
| 정성제안서 | 기존 DetailCenterPanel | 워크플로 UI 그대로 |
| 비딩관리 | `BiddingWorkspace.tsx` | 확정가 + 시나리오 + 이력 + 조정폼 + 투찰상태 |
| 제출서류 | `SubmissionDocsPanel.tsx` | 체크리스트 + AI추출 + 업로드 + 검증 + 사전점검 |
| 통합현황 | `StreamDashboard.tsx` | 3-스트림 카드 + 의존성 + 최종제출 게이트 |

## 8. 합류 규칙

| Stream | 완료 조건 |
|--------|----------|
| Stream 1 | `review_ppt` approved 또는 `document_only` END |
| Stream 2 | `bid_submission_status` = "verified" |
| Stream 3 | 모든 docs (N/A 제외) status = "verified" |

**최종 제출 게이트**: 3개 스트림 모두 completed + lead 이상 역할

---

*Migration: `database/migrations/011_three_streams.sql`*
*분석: `docs/03-analysis/features/three-streams.analysis.md` (98%)*
*보고서: `docs/04-report/features/three-streams.report.md`*
