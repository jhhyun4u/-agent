# PSM-16: Q&A 기록 검색 가능 저장

> **요구사항 ID**: PSM-16 (Must)
> **기능명**: psm-16-qa-search
> **버전**: v1.0
> **작성일**: 2026-03-18
> **상태**: Plan

---

## 1. 배경 및 목적

### 1-1. 배경
- PSM-16은 v1 요구사항 중 유일한 HIGH 잔여 갭 항목
- 현재 `presentation_qa` 테이블이 DB 스키마에 존재하나, 임베딩·콘텐츠 라이브러리 연결·검색 API가 없음
- 발표 현장 Q&A 기록이 체계적으로 축적·검색되지 않아, 다음 제안서 작성 시 활용 불가

### 1-2. 목적
발표 후 Q&A 기록을 **콘텐츠 라이브러리** 및 **교훈 아카이브**에 검색 가능하게 저장하여:
1. 과거 Q&A를 시맨틱 검색으로 빠르게 찾기
2. 유사 프로젝트 제안 시 예상 질문/답변 참고
3. 조직 지식 선순환 구조 완성

### 1-3. 요구사항 원문
> "Q&A 기록은 콘텐츠 라이브러리 및 교훈 아카이브에 검색 가능하게 저장" (Must)

---

## 2. 범위 (Scope)

### 2-1. In-Scope

| # | 항목 | 설명 |
|---|------|------|
| 1 | DB 마이그레이션 | `presentation_qa` 테이블에 `embedding`, `content_library_id` 컬럼 추가 + 인덱스 |
| 2 | Q&A 저장 서비스 | `save_qa_to_kb()` — Q&A → presentation_qa + content_library + 임베딩 + 교훈 아카이브 |
| 3 | Q&A CRUD API | POST/GET/PUT/DELETE `/api/proposals/{id}/qa` |
| 4 | Q&A 검색 API | GET `/api/kb/qa/search` — 키워드 + 시맨틱 검색 |
| 5 | 워크플로 연동 | 발표 완료 후 Q&A 입력 단계 (review_node interrupt 활용) |
| 6 | 프론트엔드 Q&A 관리 | 프로젝트 상세 내 Q&A 입력/편집 UI |
| 7 | KB Q&A 페이지 | `/kb/qa` — 조직 전체 Q&A 검색·브라우징 |

### 2-2. Out-of-Scope

| 항목 | 사유 |
|------|------|
| Q&A 자동 생성 (AI 예상 질문) | 별도 기능으로 분리 |
| 음성 녹취 → Q&A 변환 | 외부 서비스 의존, 별도 검토 |
| Q&A 기반 자동 학습/모델 파인튜닝 | LRN-05 범위 |

---

## 3. 기존 자산 분석

### 3-1. DB (이미 존재)
- `presentation_qa` 테이블: `id, proposal_id, question, answer, evaluator_reaction, memo, created_at`
- `content_library` 테이블: `type` 컬럼에 `qa_record` 이미 정의됨
- `lessons_learned` 테이블: 교훈 저장 (임베딩 포함)

### 3-2. 서비스 (확장 필요)
- `kb_updater.py`: 수주/패찰 KB 업데이트 존재 → Q&A KB 업데이트 추가
- `knowledge_search.py`: 통합 KB 검색 → Q&A 검색 쿼리 추가

### 3-3. 설계 초안 (아카이브)
- `docs/archive/2026-03/proposal-agent-v1/design/15a-gap-high-archive.md` §27-3에 `save_qa_to_kb()` 함수 스케치 존재

### 3-4. 프론트엔드 (신규 필요)
- KB 페이지 5개 존재 (content, clients, competitors, lessons, search) → `/kb/qa` 추가
- 프로젝트 상세에 Q&A 탭 없음 → 추가 필요

---

## 4. 구현 항목

### Phase A: DB 마이그레이션
- **A-1**: `presentation_qa` 테이블 확장
  - `embedding vector(1536)` 컬럼 추가
  - `content_library_id UUID REFERENCES content_library(id)` 컬럼 추가
  - `category TEXT DEFAULT 'general'` 컬럼 추가
  - `created_by UUID REFERENCES users(id)` 컬럼 추가
  - IVFFlat 인덱스: `idx_presentation_qa_embedding`
  - B-tree 인덱스: `idx_presentation_qa_proposal_id`, `idx_presentation_qa_category`

### Phase B: 백엔드 서비스 + API
- **B-1**: `app/services/qa_service.py` — Q&A KB 저장 서비스
  - `save_qa_to_kb(proposal_id, qa_records)` — 설계 초안 기반
  - `search_qa(query, org_id, filters)` — 키워드 + 시맨틱 하이브리드 검색
  - `get_proposal_qa(proposal_id)` — 프로젝트별 Q&A 조회
- **B-2**: `app/api/routes_qa.py` — Q&A API 엔드포인트
  - `POST /api/proposals/{id}/qa` — Q&A 일괄 등록
  - `GET /api/proposals/{id}/qa` — 프로젝트별 Q&A 조회
  - `PUT /api/proposals/{id}/qa/{qa_id}` — 개별 Q&A 수정
  - `DELETE /api/proposals/{id}/qa/{qa_id}` — 개별 Q&A 삭제
  - `GET /api/kb/qa/search` — 조직 전체 Q&A 검색 (query, category, limit)
- **B-3**: `app/models/schemas.py` 확장 — QARecordCreate, QARecordUpdate, QASearchResult Pydantic 모델

### Phase C: 워크플로 연동
- **C-1**: `proposal_nodes.py` 또는 `review_node.py`에서 발표 완료 후 Q&A 입력 interrupt 추가
  - 기존 `review_proposal` 리뷰 후 또는 별도 `qa_input_gate` 노드
  - 사용자가 Q&A 입력 → resume 시 `save_qa_to_kb()` 호출

### Phase D: 프론트엔드
- **D-1**: Q&A 입력/관리 UI (`frontend/components/QaPanel.tsx`)
  - 프로젝트 상세 페이지(`/proposals/[id]`)에 Q&A 탭 추가
  - 질문/답변/카테고리/평가위원 반응 입력 폼
  - 기존 Q&A 목록 표시 + 수정/삭제
- **D-2**: KB Q&A 검색 페이지 (`frontend/app/kb/qa/page.tsx`)
  - 검색바 (키워드 + 시맨틱)
  - 카테고리 필터, 프로젝트 필터
  - Q&A 카드 목록 (질문, 답변 요약, 출처 프로젝트, 날짜)

---

## 5. 구현 순서

```
Phase A (DB) → Phase B (서비스+API) → Phase C (워크플로) → Phase D (프론트엔드)
```

| 순서 | 항목 | 의존성 | 예상 규모 |
|:----:|------|--------|----------|
| 1 | A-1: DB 마이그레이션 | 없음 | SQL 1파일 |
| 2 | B-3: Pydantic 스키마 | 없음 | ~30줄 |
| 3 | B-1: qa_service.py | A-1, B-3 | ~120줄 |
| 4 | B-2: routes_qa.py | B-1 | ~100줄 |
| 5 | C-1: 워크플로 연동 | B-1 | ~30줄 수정 |
| 6 | D-1: QaPanel.tsx | B-2 | ~200줄 |
| 7 | D-2: KB Q&A 페이지 | B-2 | ~150줄 |

**총 예상**: 신규 ~630줄 + 기존 파일 수정 ~50줄

---

## 6. 기술 결정

| 결정 | 근거 |
|------|------|
| 시맨틱 검색에 pgvector 사용 | 기존 content_library와 동일 패턴 |
| 하이브리드 검색 (키워드 + 벡터) | 정확도 향상, knowledge_search.py 패턴 참고 |
| content_library에 qa_record로 이중 저장 | 통합 KB 검색에 자동 포함 |
| lessons_learned에 Q&A 요약 자동 등록 | 교훈 아카이브 요구사항 충족 |
| 워크플로 interrupt 방식 | 기존 review_node 패턴과 일관 |

---

## 7. 리스크

| 리스크 | 영향 | 대응 |
|--------|------|------|
| 임베딩 API 호출 비용 | Q&A 건수만큼 API 호출 | 일괄 임베딩 처리, 캐싱 |
| presentation_qa 기존 데이터 마이그레이션 | 기존 데이터에 embedding 없음 | 마이그레이션 스크립트로 일괄 처리 (optional) |
| 카테고리 분류 일관성 | 사용자 입력 의존 | 카테고리 선택지 제한 (드롭다운) |

---

## 8. 성공 기준

- [ ] Q&A 기록 CRUD API 정상 동작
- [ ] Q&A 저장 시 content_library + lessons_learned 자동 등록
- [ ] 시맨틱 검색으로 유사 Q&A 조회 가능
- [ ] 프론트엔드에서 Q&A 입력·검색 UI 동작
- [ ] 기존 KB 통합 검색(`/kb/search`)에서 Q&A 결과 포함

---

## 9. 관련 요구사항

| ID | 요구사항 | 관계 |
|----|----------|------|
| PSM-16 | Q&A 기록 검색 가능 저장 | **본 기능** |
| CLG-03 | 콘텐츠 수정 시 버전 관리 | content_library 연동 시 적용 |
| CL-09 | 완료 제안서 자동 수집 | KB 업데이트 패턴 공유 |
| LRN-05 | 교훈 기반 학습 | Q&A → 교훈 아카이브 연동 |
