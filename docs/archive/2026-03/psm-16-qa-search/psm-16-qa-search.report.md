# PSM-16: Q&A 기록 검색 가능 저장 — PDCA 완료 보고서

> **Feature**: psm-16-qa-search
> **요구사항 ID**: PSM-16 (Must)
> **Date**: 2026-03-18
> **Match Rate**: 98%
> **Status**: Completed

---

## 1. 요약

v1 요구사항 중 유일한 HIGH 잔여 갭이었던 PSM-16 "Q&A 기록은 콘텐츠 라이브러리 및 교훈 아카이브에 검색 가능하게 저장"을 완전 구현하였다. 발표 현장 Q&A가 presentation_qa + content_library + lessons_learned 3중 저장되어 시맨틱 검색으로 활용 가능하며, 프론트엔드 Q&A 관리 UI와 KB 검색 페이지를 통해 조직 지식 선순환 구조를 완성하였다.

---

## 2. PDCA 사이클 요약

| Phase | 산출물 | 날짜 |
|-------|--------|------|
| Plan | `docs/01-plan/features/psm-16-qa-search.plan.md` | 2026-03-18 |
| Design | `docs/02-design/features/psm-16-qa-search.design.md` | 2026-03-18 |
| Do | 신규 5파일 + 수정 6파일 = 11파일 | 2026-03-18 |
| Check | `docs/03-analysis/features/psm-16-qa-search.analysis.md` (98%) | 2026-03-18 |
| Report | 본 문서 | 2026-03-18 |

---

## 3. 구현 내역

### 3.1 백엔드 (신규 3 + 수정 4 = 7파일)

| 파일 | 유형 | 내용 |
|------|:----:|------|
| `database/migrations/005_qa_search.sql` | 신규 | presentation_qa 4컬럼 확장 + IVFFlat 인덱스 + `search_qa_by_embedding` RPC |
| `app/services/qa_service.py` | 신규 | save/get/update/delete/search — 4단계 KB 자동 연동 |
| `app/api/routes_qa.py` | 신규 | 5개 엔드포인트 (CRUD + 검색) |
| `app/models/schemas.py` | 수정 | QARecordCreate/Update/Response/SearchResult + QA_CATEGORIES |
| `app/main.py` | 수정 | qa_router 등록 |
| `app/services/knowledge_search.py` | 수정 | qa 영역 추가 + `_search_qa` 함수 (org_id 폴백 필터 포함) |
| `app/graph/nodes/review_node.py` | 수정 | PPT 리뷰 시 Q&A 입력 안내 메시지 |

### 3.2 프론트엔드 (신규 2 + 수정 2 = 4파일)

| 파일 | 유형 | 내용 |
|------|:----:|------|
| `frontend/components/QaPanel.tsx` | 신규 | Q&A 입력/수정/삭제 패널 (카테고리 드롭다운, 평가위원 반응) |
| `frontend/app/kb/qa/page.tsx` | 신규 | KB Q&A 시맨틱 검색 페이지 (유사도 바, 카테고리 필터) |
| `frontend/app/proposals/[id]/page.tsx` | 수정 | Q&A 탭 추가 |
| `frontend/lib/api.ts` | 수정 | qaApi 메서드 5개 + 4개 TypeScript 타입 |

### 3.3 코드 규모

| 구분 | 줄 수 |
|------|------:|
| 신규 코드 | ~680줄 |
| 수정 코드 | ~120줄 |
| SQL (마이그레이션) | ~60줄 |
| **합계** | **~860줄** |

---

## 4. API 엔드포인트

| Method | Path | 설명 |
|--------|------|------|
| POST | `/api/proposals/{id}/qa` | Q&A 일괄 등록 + KB 자동 연동 |
| GET | `/api/proposals/{id}/qa` | 프로젝트별 Q&A 조회 |
| PUT | `/api/proposals/{id}/qa/{qa_id}` | 개별 Q&A 수정 + 임베딩 재생성 |
| DELETE | `/api/proposals/{id}/qa/{qa_id}` | 개별 Q&A 삭제 + content_library 연동 삭제 |
| GET | `/api/kb/qa/search` | 조직 전체 Q&A 시맨틱 + 키워드 하이브리드 검색 |

---

## 5. 데이터 흐름

```
사용자 Q&A 입력
  ↓
POST /api/proposals/{id}/qa
  ↓
┌──────────────────────────────────────────┐
│ 1. presentation_qa INSERT               │
│ 2. content_library INSERT (qa_record)    │
│ 3. presentation_qa.embedding 생성        │
│    content_library.embedding 생성        │
│ 4. lessons_learned INSERT (qa_insight)   │
│    lessons_learned.embedding 생성        │
└──────────────────────────────────────────┘
  ↓
통합 KB 검색 (unified_search) 자동 포함
  ↓
/kb/qa 페이지에서 시맨틱 검색 가능
```

---

## 6. 갭 분석 결과

**Match Rate: 98%** (52개 항목 중 50개 일치, Checklist 11/11 통과)

| # | Gap | 심각도 | 상태 |
|---|-----|:------:|:----:|
| GAP-1 | knowledge_search.py 키워드 폴백 org_id 필터 누락 | MEDIUM | **수정 완료** |
| GAP-2 | Q&A 탭 상태 조건 미적용 (항상 표시) | LOW | 의도적 허용 |

- GAP-1은 Check 단계에서 즉시 수정 (`proposals!inner(org_id)` 조인 추가)
- GAP-2는 Q&A를 발표 전에도 사전 준비용으로 입력할 수 있어 오히려 유용

---

## 7. 핵심 기술 결정

| 결정 | 근거 |
|------|------|
| pgvector IVFFlat (lists=10) | 소규모 데이터셋에 적합, content_library와 동일 패턴 |
| 하이브리드 검색 (시맨틱 + 키워드 폴백) | RPC 미등록 시에도 동작, 정확도 향상 |
| content_library 이중 저장 | 통합 KB 검색에 자동 포함, 별도 조회 불필요 |
| 워크플로 외부 등록 방식 | 발표 후 수동 입력이 자연스러움, LangGraph 노드 불필요 |
| lessons_learned 자동 요약 | 교훈 아카이브 요구사항 충족, 벡터 검색 연동 |

---

## 8. 요구사항 해소 상황

### 8.1 본 기능으로 해소

| ID | 요구사항 | 상태 |
|----|----------|:----:|
| **PSM-16** | Q&A 기록 검색 가능 저장 | **완료** |

### 8.2 프로젝트 전체 잔여 갭 (PSM-16 해소 후)

| 등급 | 건수 | 항목 |
|------|:----:|------|
| HIGH | **0건** | PSM-16 해소로 HIGH 잔여 없음 |
| LOW | 1건 | AGT-04 (잔여 시간 추정 알고리즘) |
| 설계-구현 차이 | 2건 | #4 EVALUATOR (LOW), #7 COMMON_SYSTEM_RULES (MEDIUM) |
| Partial | 8건 | ULM-05, OB-09, CLG-03, CLI-07, LRN-05, PSM-13, ART-10, NFR-21 |

---

## 9. 결론

PSM-16 구현으로 **v1 요구사항의 HIGH 잔여 갭이 0건**이 되었다. 발표 Q&A → 콘텐츠 라이브러리 → 교훈 아카이브 → 시맨틱 검색의 전체 파이프라인이 완성되어, 조직 지식 선순환 구조의 마지막 퍼즐이 채워졌다.

전체 프로젝트 매칭률: 99% → **100% (HIGH 기준)**

---

*PSM-16 PDCA 사이클 완료 (2026-03-18). Plan → Design → Do → Check(98%) → Report. 단일 세션 내 전체 사이클 완료.*
