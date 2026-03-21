# Gap Analysis: 3-Stream 병행 업무 (three-streams)

**분석일**: 2026-03-21
**설계 기준**: 인라인 구현 계획서 (Phase A~F)
**Match Rate**: **97%** (GAP-1 수정 후 **98%**)

---

## Overall Scores

| Category | Score | Status |
|----------|:-----:|:------:|
| Phase A: DB + Backend | 97% | ✅ |
| Phase B: Graph Integration | 100% | ✅ |
| Phase C: Frontend Infra | 100% | ✅ |
| Phase D: SubmissionDocsPanel | 88% | ✅ |
| Phase E: BiddingWorkspace | 100% | ✅ |
| Phase F: StreamDashboard | 100% | ✅ |
| **Overall** | **97%** | **✅** |

---

## RED — Missing/Bug (설계 O, 구현 X or 버그)

| # | 항목 | 위치 | 설명 | 심각도 |
|---|------|------|------|--------|
| GAP-1 | 스키마 클래스명 불일치 | `routes_submission_docs.py` → `stream_schemas.py` | `SubmissionDocResponse` import하지만 실제 클래스명은 `SubmissionDocumentResponse` → **런타임 ImportError** | **HIGH** |

## YELLOW — 추가 기능 (설계 X, 구현 O)

| # | 항목 | 위치 | 설명 |
|---|------|------|------|
| ADD-1 | `expired` 문서 상태 | `011_three_streams.sql` | 템플릿 유효기간 만료 체크 |
| ADD-2 | `template_matched` source | `011_three_streams.sql` | 자동매칭 vs RFP추출 구분 |
| ADD-3 | RLS + 인덱스 | `011_three_streams.sql` | 보안 + 성능 |
| ADD-4 | `orgTemplatesApi` 프론트엔드 | `api.ts` | 조직 공통서류 CRUD 클라이언트 |
| ADD-5 | StreamDashboard 30초 폴링 | `StreamDashboard.tsx` | UX 개선 |
| ADD-6 | `_sync_streams_ready()` 헬퍼 | `stream_orchestrator.py` | proposals.streams_ready 자동 동기화 |

## BLUE — 변경 사항 (설계 ≠ 구현)

| # | 항목 | 설계 | 구현 | 영향 |
|---|------|------|------|------|
| CHG-1 | Stream 1 완료 | END 후처리 | 별도 `stream1_complete_hook` 노드 → END | LOW (더 나은 설계) |
| CHG-2 | 담당자 배정 UI | 팀원 선택 드롭다운 | 상태 변경만 (사용자 선택 미구현) | LOW |

---

## Phase A 상세

### A-1. DB Migration

| 항목 | 설계 | 구현 | 상태 |
|------|------|------|:----:|
| `submission_documents` 테이블 | 전체 컬럼 | 전체 일치 + expired/template_matched 추가 | ✅ |
| `stream_progress` 테이블 | 전체 컬럼 + UNIQUE | 전체 일치 | ✅ |
| `org_document_templates` 테이블 | 전체 컬럼 + UNIQUE | 전체 일치 | ✅ |
| `proposals` 확장 | streams_ready + submission_gate_status | 일치 | ✅ |

### A-2. 백엔드 서비스

| 서비스 | 함수 수(설계) | 구현 | 상태 |
|--------|:------:|:----:|:----:|
| `stream_orchestrator.py` | 5 | 5 + 헬퍼 2 | ✅ |
| `submission_docs_service.py` | 9 | 12 (add_document, delete_document 등 추가) | ✅ |
| `bidding_stream.py` | 3 | 3 + 헬퍼 1 | ✅ |

### A-4. API 라우트

| 파일 | 엔드포인트(설계) | 구현 | 상태 |
|------|:------:|:----:|:----:|
| `routes_streams.py` | 3 | 3 | ✅ |
| `routes_submission_docs.py` | 11 | 11 | ✅ |
| `routes_bid_submission.py` 확장 | 2 | 2 | ✅ |

---

## Phase B 상세

| 항목 | 설계 | 구현 | 상태 |
|------|------|------|:----:|
| Go 결정 → `initialize_streams()` | 비동기 호출 | `_fire_stream_initialization()` asyncio.create_task | ✅ |
| Go 결정 → `extract_checklist_from_rfp()` | 백그라운드 | 같은 task 내 실행 | ✅ |
| review_ppt approved → Stream 1 completed | END 후처리 | `stream1_complete_hook` 노드 경유 | ✅ |
| document_only → Stream 1 completed | END 후처리 | `stream1_complete_hook` 노드 경유 | ✅ |
| `/start` 응답에 streams_status | 포함 | `_get_streams_status_safe()` | ✅ |
| `/state` 응답에 streams_status | 포함 | `_get_streams_status_safe()` | ✅ |

---

## Phase C~F 상세

### C: Frontend Infra

| 항목 | 구현 | 상태 |
|------|------|:----:|
| StreamProgressHeader.tsx | 87줄, 3-스트림 미니바 + 클릭→탭 | ✅ |
| StreamTabBar.tsx | 83줄, 4탭 + 상태뱃지 | ✅ |
| 페이지 탭 기반 재구성 | 4탭 조건부 렌더링 | ✅ |
| API 타입 13개 | StreamProgress, SubmissionDocument 등 | ✅ |
| API 클라이언트 3개 | streamsApi, submissionDocsApi, orgTemplatesApi | ✅ |

### D: SubmissionDocsPanel

| 기능 | 구현 | 상태 |
|------|------|:----:|
| 체크리스트 테이블 7컬럼 | ✅ | ✅ |
| AI 추출 | ✅ | ✅ |
| 수동 추가 폼 | ✅ | ✅ |
| 드래그앤드롭 업로드 | ✅ | ✅ |
| 검증 완료 버튼 | ✅ | ✅ |
| N/A 처리 | ✅ | ✅ |
| 사전 점검 표시 | ✅ | ✅ |
| **담당자 선택 드롭다운** | 미구현(상태변경만) | ⚠️ LOW |

### E: BiddingWorkspace

| 기능 | 구현 | 상태 |
|------|------|:----:|
| 확정가 + 낙찰률 | ✅ | ✅ |
| 시나리오 비교 카드 | ✅ | ✅ |
| 가격 이력 타임라인 | ✅ | ✅ |
| 가격 조정 폼 (사유 필수) | ✅ | ✅ |
| 투찰 상태 트래커 | ✅ | ✅ |

### F: StreamDashboard

| 기능 | 구현 | 상태 |
|------|------|:----:|
| 3-스트림 진행률 카드 | ✅ | ✅ |
| 의존성 시각화 | ✅ | ✅ |
| 최종 제출 게이트 | ✅ (3 completed → 활성) | ✅ |
| 마감 카운트다운 | ✅ | ✅ |

---

## 합류 규칙 검증

| Stream | 설계 조건 | 구현 | 상태 |
|--------|----------|------|:----:|
| Stream 1 | review_ppt approved OR document_only | `stream1_complete_hook` 양쪽 경로 | ✅ |
| Stream 2 | bid_submission_status = "verified" | 기존 bid_handoff + stream progress | ✅ |
| Stream 3 | 모든 docs (N/A 제외) verified | `check_documents_ready()` | ✅ |
| 최종 게이트 | 3 completed + lead+ 역할 | `mark_final_submission()` + `require_role()` | ✅ |

---

## 권장 조치

| 우선순위 | 항목 | 파일 | 설명 |
|----------|------|------|------|
| **HIGH** | GAP-1 수정 | `stream_schemas.py` | `SubmissionDocResponse` 별칭 추가 |
| MEDIUM | CHG-2 | `SubmissionDocsPanel.tsx` | 팀원 선택 드롭다운 추가 |

---

## Match Rate 산출

| 카테고리 | 항목 수 | 일치 | 비율 |
|----------|:-------:|:----:|:----:|
| A: DB + Backend | 45 | 44 | 98% |
| B: Graph Integration | 6 | 6 | 100% |
| C: Frontend Infra | 12 | 12 | 100% |
| D: SubmissionDocsPanel | 8 | 7 | 88% |
| E: BiddingWorkspace | 6 | 6 | 100% |
| F: StreamDashboard | 4 | 4 | 100% |
| **합계** | **81** | **79** | **97%** |

---

*분석 버전: 1.0 | 2026-03-21*
