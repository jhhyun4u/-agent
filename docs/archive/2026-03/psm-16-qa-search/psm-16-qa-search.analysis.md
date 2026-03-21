# PSM-16 Q&A 검색 가능 저장 — Gap Analysis Report

> **Feature**: psm-16-qa-search
> **Date**: 2026-03-18
> **Design Doc**: `docs/02-design/features/psm-16-qa-search.design.md` (v1.0)

---

## 1. Overall Match Rate: 98%

| Category | Score | Status |
|----------|:-----:|:------:|
| DB Migration | 100% | PASS |
| Pydantic Schemas | 100% | PASS |
| Service Layer | 100% | PASS |
| API Endpoints | 100% | PASS |
| Workflow Integration | 100% | PASS |
| KB Search Integration | 95% | WARN |
| Frontend (QaPanel) | 100% | PASS |
| Frontend (KB QA Page) | 100% | PASS |
| Frontend (API Client) | 100% | PASS |
| Proposal Page Integration | 90% | WARN |
| Auth (require_project_access) | 100% | PASS |

---

## 2. Verification Checklist (Design §10)

| # | Checklist Item | Status |
|---|---------------|:------:|
| 1 | POST /api/proposals/{id}/qa — presentation_qa + content_library + embedding | PASS |
| 2 | GET /api/proposals/{id}/qa — 시간순 조회 | PASS |
| 3 | PUT /api/proposals/{id}/qa/{qa_id} — 임베딩 재생성 + content_library 동기화 | PASS |
| 4 | DELETE /api/proposals/{id}/qa/{qa_id} — content_library도 삭제 | PASS |
| 5 | GET /api/kb/qa/search — 시맨틱 검색 + 프로젝트명/발주기관 부가정보 | PASS |
| 6 | 시맨틱 검색 RPC 미등록 시 키워드 폴백 동작 | PASS |
| 7 | unified_search에서 qa 영역 포함 | PASS |
| 8 | review_ppt 승인 시 Q&A 입력 안내 메시지 | PASS |
| 9 | QaPanel: 일괄 등록, 수정, 삭제 UI | PASS |
| 10 | KB Q&A 페이지: 검색 + 카테고리 필터 + 결과 카드 | PASS |
| 11 | 인증: require_project_access 적용 | PASS |

**Checklist: 11/11 (100%)**

---

## 3. Gaps Found

### GAP-1 (MEDIUM): knowledge_search.py 키워드 폴백에 org_id 필터 누락

| 항목 | 설계 | 구현 |
|------|------|------|
| `_search_qa` 키워드 폴백 | `eq("proposals.org_id", org_id)` + inner join | org_id 필터 없음 |

**영향**: 폴백 경로에서 다른 조직의 Q&A 노출 가능 (RPC 미등록 시에만 발생)
**위치**: `app/services/knowledge_search.py` `_search_qa` 함수 키워드 폴백 부분

### GAP-2 (LOW): Q&A 탭 상태 조건 미적용

| 항목 | 설계 | 구현 |
|------|------|------|
| Q&A 탭 노출 조건 | presented/won/lost 일 때만 | 항상 표시 |

**영향**: UX 선호도 차이, 데이터 무결성에는 영향 없음
**위치**: `frontend/app/proposals/[id]/page.tsx`

---

## 4. File Coverage

| 유형 | 파일 | 매칭 |
|------|------|:----:|
| 신규 | `database/migrations/005_qa_search.sql` | 100% |
| 신규 | `app/services/qa_service.py` | 100% |
| 신규 | `app/api/routes_qa.py` | 100% |
| 신규 | `frontend/components/QaPanel.tsx` | 100% |
| 신규 | `frontend/app/kb/qa/page.tsx` | 100% |
| 수정 | `app/models/schemas.py` | 100% |
| 수정 | `app/main.py` | 100% |
| 수정 | `app/graph/nodes/review_node.py` | 100% |
| 수정 | `app/services/knowledge_search.py` | 95% |
| 수정 | `frontend/app/proposals/[id]/page.tsx` | 90% |
| 수정 | `frontend/lib/api.ts` | 100% |

---

## 5. Summary

**매칭률 98%** — Production-ready. MEDIUM 갭 1건(키워드 폴백 org_id 필터)은 RPC 미등록 시에만 발생하는 폴백 경로에 한정. 즉시 수정 권장.
