# KB 개선 Plan

| 항목 | 내용 |
|------|------|
| Feature | kb-enhancement |
| 버전 | v1.0 |
| 작성일 | 2026-03-24 |
| 상태 | Plan |

---

## 1. 배경 및 목적

현재 KB(Knowledge Base)는 6개 영역(역량, 콘텐츠, 발주기관, 경쟁사, 교훈, Q&A)과 2개 참조 테이블(노임단가, 시장가격)로 구성되어 있다. 기본 구조는 갖추어져 있으나, 실제 운영 시 다음 문제가 있다:

1. **자동 축적 부족**: 제안서 작성 과정에서 생성된 고품질 콘텐츠가 KB에 자동으로 쌓이지 않음
2. **검색 정확도**: 키워드 폴백 시 title만 검색, capabilities는 임베딩 미적용, 검색 결과 랭킹 단순
3. **활용 단절**: LangGraph 노드에서 KB 조회 시 단순 텍스트 나열, 섹션 추천이 형식적
4. **관리 비효율**: 프론트엔드에서 KB 건강도 파악 어려움, 일괄 작업 지원 부족

## 2. 현황 분석

### 2-1. 자동 축적 경로

| 트리거 | 현재 동작 | 문제점 |
|--------|----------|--------|
| 수주 결과 등록 | capabilities에 후보 등록 (draft) | **제안서 섹션 → content_library 자동 등록 없음** |
| 패찰 결과 등록 | competitors 자동 갱신 | 정상 |
| 교훈 등록 | 임베딩 생성 + lessons_learned 저장 | 정상 |
| Q&A 등록 | 4중 연동 (qa→content→embedding→lesson) | 정상 |
| **제안서 섹션 완성** | **없음** | 고품질 섹션이 KB에 축적되지 않음 |
| **리서치 결과** | **없음** | research_brief 데이터가 휘발됨 |
| **전략 수립 결과** | **없음** | SWOT, Win Theme 등이 축적되지 않음 |

### 2-2. 검색 품질

| 영역 | 시맨틱 검색 | 키워드 폴백 | 문제점 |
|------|:-----------:|:-----------:|--------|
| content | O (RPC) | title ILIKE | **body 검색 안 됨** |
| client | O (RPC) | client_name ILIKE | 정상 |
| competitor | O (RPC) | company_name ILIKE | 정상 |
| lesson | O (RPC) | 전체 조회 (limit) | **키워드 매칭 없음** |
| capability | **X** | description ILIKE | **임베딩 미적용** |
| qa | O (RPC) | question/answer ILIKE | 정상 |

### 2-3. LangGraph 활용

| 노드 | KB 활용 방식 | 개선점 |
|------|-------------|--------|
| go_no_go | query_kb_context → 텍스트 나열 | **유사 과거 사례 매칭 없음** |
| strategy_generate | KB + SWOT | **과거 동일 발주기관 전략 참조 없음** |
| plan_story | evidence_candidates | **content_library 유사 콘텐츠 미참조** |
| proposal_write_next | suggest_content_for_section | **추천 결과가 프롬프트에 미주입** |
| plan_price | labor_rates + market_price | 정상 (직접 DB 조회) |

### 2-4. 관리 UX

| 기능 | 현재 | 문제점 |
|------|------|--------|
| KB 건강도 대시보드 | 없음 | 영역별 데이터 건수, 임베딩 커버리지 파악 불가 |
| 일괄 임베딩 생성 | 없음 | 기존 데이터에 임베딩이 없으면 수동 1건씩 |
| 콘텐츠 품질 점수 갱신 | 수동 (API 호출) | 자동 배치 갱신 없음 |
| 중복 콘텐츠 탐지 | 없음 | 유사 콘텐츠 중복 등록 감지 불가 |

## 3. 변경 범위

### Phase A: 자동 축적 강화 (우선순위 HIGH)

#### A-1. 제안서 섹션 → content_library 자동 등록
**파일**: `app/graph/nodes/proposal_nodes.py`, `app/services/content_library.py`

- 제안서 섹션 작성 완료 시 `content_library`에 자동 등록 (draft)
- 조건: 섹션 content 500자 이상 + 자가진단 70점 이상
- 메타데이터: source_project_id, industry, section_type, tags (RFP 키워드 기반)
- 임베딩 자동 생성

#### A-2. 리서치 결과 축적
**파일**: `app/graph/nodes/research_gather.py`, `app/services/kb_updater.py`

- research_brief의 high/medium credibility 데이터 → `content_library`에 `research_data` 타입 저장
- 제안서 완료(수주/패찰) 시 연구 데이터 성과 카운터 갱신

#### A-3. 전략 결과 축적
**파일**: `app/graph/nodes/strategy_generate.py`, `app/services/kb_updater.py`

- 전략 수립 결과(SWOT, Win Theme, Ghost Theme, 포지셔닝 근거) → `content_library`에 `strategy_record` 타입 저장
- 발주기관 + 포지셔닝 조합으로 향후 유사 전략 참조 가능

### Phase B: 검색 품질 개선 (우선순위 HIGH)

#### B-1. capabilities 임베딩 적용
**파일**: `app/services/knowledge_search.py`, `database/migrations/`

- capabilities 테이블에 `embedding vector(1536)` 컬럼 추가
- `search_capabilities_by_embedding` RPC 함수 생성
- `_search_capabilities()` → 시맨틱 검색으로 전환

#### B-2. 키워드 폴백 개선
**파일**: `app/services/knowledge_search.py`

- content: `body` ILIKE 추가 (현재 `title`만 검색)
- lesson: `strategy_summary`, `effective_points`, `weak_points` ILIKE 추가
- 전체: 결과에 `match_type: "semantic" | "keyword"` 표시

#### B-3. 하이브리드 랭킹
**파일**: `app/services/knowledge_search.py`

- 시맨틱 유사도 + 품질 점수 + 신선도 가중 랭킹
- 공식: `final_score = similarity × 0.5 + quality_score × 0.3 + freshness × 0.2`
- content_library만 우선 적용 (품질 점수 있는 유일한 영역)

### Phase C: 활용도 강화 (우선순위 MEDIUM)

#### C-1. 유사 과거 사례 매칭 (Go/No-Go)
**파일**: `app/graph/nodes/go_no_go.py`, `app/graph/context_helpers.py`

- RFP 제목/키워드로 `lessons_learned` 시맨틱 검색 → 유사 과거 사례 top 3 추출
- 프롬프트에 "과거 유사 사례: [사례명] — 결과: 수주/패찰, 포지셔닝: X, 교훈: Y" 형태로 주입

#### C-2. 과거 전략 참조 (strategy_generate)
**파일**: `app/graph/nodes/strategy_generate.py`

- 동일 발주기관 과거 전략 레코드 조회 (A-3에서 축적한 strategy_record)
- "이전 전략과의 차이점" 분석 프롬프트 추가

#### C-3. 섹션 작성 시 유사 콘텐츠 주입 (proposal_write_next)
**파일**: `app/graph/nodes/proposal_nodes.py`

- `suggest_content_for_section()` 결과를 실제 프롬프트 `{reference_content}` 변수에 주입
- 최대 3개, 품질 점수 순, content[:300] 미리보기 포함

#### C-4. 스토리라인 작성 시 KB 참조 (plan_story)
**파일**: `app/graph/nodes/plan_nodes.py`

- content_library에서 유사 섹션 콘텐츠 검색 → evidence_candidates에 추가
- "과거 수주 제안서에서 효과적이었던 표현/구조" 참조

### Phase D: 관리 UX 개선 (우선순위 LOW)

#### D-1. KB 건강도 대시보드 API
**파일**: `app/api/routes_kb.py`

- `GET /api/kb/health` — 영역별 건수, 임베딩 커버리지(%), 평균 품질 점수, 최근 갱신일
- 응답 예: `{ "content": { "total": 150, "with_embedding": 142, "coverage": 94.7, "avg_quality": 65.2, "last_updated": "2026-03-20" }, ... }`

#### D-2. 일괄 임베딩 생성
**파일**: `app/api/routes_kb.py`, `app/services/embedding_service.py`

- `POST /api/kb/reindex` — 임베딩 없는 레코드에 대해 배치 생성
- 영역 선택 가능: `{ "areas": ["content", "capability"] }`
- 진행 상황 응답: `{ "total": 50, "processed": 30, "failed": 2 }`

#### D-3. 중복 콘텐츠 탐지
**파일**: `app/services/content_library.py`, `app/api/routes_kb.py`

- `GET /api/kb/content/duplicates?threshold=0.9` — 코사인 유사도 90% 이상 콘텐츠 쌍 검출
- 프론트엔드에서 병합/삭제 선택 가능

#### D-4. 프론트엔드 KB 건강도 위젯
**파일**: `frontend/app/(app)/kb/search/page.tsx` 또는 `dashboard/page.tsx`

- 영역별 데이터 건수 + 임베딩 커버리지 바 차트
- 품질 점수 분포 히스토그램
- 최근 KB 갱신 이력

## 4. 수정 대상 파일

### Phase A (자동 축적)
| # | 파일 | 변경 | 라인 추정 |
|---|------|------|----------|
| A-1 | `app/graph/nodes/proposal_nodes.py` | 섹션 완료 시 content_library 등록 호출 | +25 |
| A-1 | `app/services/content_library.py` | `auto_register_section()` 신규 | +40 |
| A-2 | `app/graph/nodes/research_gather.py` | 리서치 결과 KB 저장 호출 | +10 |
| A-2 | `app/services/kb_updater.py` | `save_research_to_kb()` 신규 | +35 |
| A-3 | `app/graph/nodes/strategy_generate.py` | 전략 결과 KB 저장 호출 | +10 |
| A-3 | `app/services/kb_updater.py` | `save_strategy_to_kb()` 신규 | +30 |

### Phase B (검색 개선)
| # | 파일 | 변경 | 라인 추정 |
|---|------|------|----------|
| B-1 | `database/migrations/012_kb_enhancement.sql` | capabilities embedding + RPC | +40 |
| B-1 | `app/services/knowledge_search.py` | `_search_capabilities()` 시맨틱 전환 | +15 (수정) |
| B-2 | `app/services/knowledge_search.py` | 키워드 폴백 body/strategy_summary 추가 | +15 (수정) |
| B-3 | `app/services/knowledge_search.py` | 하이브리드 랭킹 함수 | +30 |

### Phase C (활용 강화)
| # | 파일 | 변경 | 라인 추정 |
|---|------|------|----------|
| C-1 | `app/graph/context_helpers.py` | `find_similar_cases()` 신규 | +25 |
| C-1 | `app/graph/nodes/go_no_go.py` | 유사 사례 프롬프트 주입 | +10 |
| C-2 | `app/graph/nodes/strategy_generate.py` | 과거 전략 레코드 조회 + 프롬프트 | +15 |
| C-3 | `app/graph/nodes/proposal_nodes.py` | suggest 결과 프롬프트 주입 | +15 |
| C-4 | `app/graph/nodes/plan_nodes.py` | 유사 콘텐츠 검색 + evidence 추가 | +15 |

### Phase D (관리 UX)
| # | 파일 | 변경 | 라인 추정 |
|---|------|------|----------|
| D-1 | `app/api/routes_kb.py` | `GET /api/kb/health` | +50 |
| D-2 | `app/api/routes_kb.py` | `POST /api/kb/reindex` | +40 |
| D-2 | `app/services/embedding_service.py` | `batch_reindex()` 신규 | +35 |
| D-3 | `app/services/content_library.py` | `find_duplicates()` 신규 | +30 |
| D-3 | `app/api/routes_kb.py` | `GET /api/kb/content/duplicates` | +15 |
| D-4 | `frontend/lib/api.ts` | KB health 타입 + API | +15 |
| D-4 | `frontend/app/(app)/kb/search/page.tsx` | 건강도 위젯 | +60 |

**총 추정**: ~620줄 (A: 150, B: 100, C: 80, D: 290)

## 5. 구현 순서

```
Phase A — 자동 축적 (우선)
  Step 1: content_library.py — auto_register_section()
  Step 2: proposal_nodes.py — 섹션 완료 시 자동 등록 호출
  Step 3: kb_updater.py — save_research_to_kb(), save_strategy_to_kb()
  Step 4: research_gather.py, strategy_generate.py — KB 저장 호출

Phase B — 검색 개선
  Step 5: 012_kb_enhancement.sql — capabilities embedding + RPC
  Step 6: knowledge_search.py — 시맨틱 전환 + 폴백 개선 + 랭킹

Phase C — 활용 강화
  Step 7: context_helpers.py — find_similar_cases()
  Step 8: go_no_go.py, strategy_generate.py — 유사 사례/전략 주입
  Step 9: proposal_nodes.py, plan_nodes.py — 콘텐츠 추천 주입

Phase D — 관리 UX
  Step 10: routes_kb.py — health, reindex, duplicates API
  Step 11: embedding_service.py — batch_reindex()
  Step 12: 프론트엔드 — 건강도 위젯
```

## 6. 기술 고려사항

### 자동 등록 품질 필터

- 섹션 500자 미만 → 스킵 (단순 항목)
- 자가진단 70점 미만 → 스킵 (저품질)
- 동일 제안서의 rewrite → 최신만 유지 (upsert)

### 임베딩 비용

- 현재: 요청 시 1건씩 생성 (OpenAI text-embedding-3-small)
- Phase A 추가: 제안서당 ~10개 섹션 × 1 임베딩 = ~10회 추가
- Phase D reindex: 배치 100건 단위, rate limit 준수
- **비용 영향**: 미미 (embedding-3-small $0.00002/1K tokens)

### 토큰 예산 영향

- Phase C 프롬프트 주입: 유사 콘텐츠 3개 × 300자 = ~900자 ≈ ~300 tokens 추가
- 유사 사례 3개 × 200자 = ~600자 ≈ ~200 tokens 추가
- **총 ~500 tokens 추가**: 현재 예산 ~114K 대비 무시 가능

### 데이터 무결성

- 자동 등록은 모두 `draft` 상태 → 사용자 승인 전까지 검색에 미포함
- 리서치/전략 데이터는 `content_type` 구분 → 기존 섹션 블록과 분리

## 7. 검증 계획

| # | Phase | 검증 | 기대 결과 |
|---|-------|------|----------|
| V1 | A | 제안서 섹션 완료 후 content_library 조회 | 500자+ 섹션이 draft로 등록 |
| V2 | A | research_gather 완료 후 KB 조회 | high/medium 데이터 저장됨 |
| V3 | A | strategy_generate 완료 후 KB 조회 | strategy_record 타입 저장됨 |
| V4 | B | capabilities 시맨틱 검색 | 키워드 매칭보다 정확한 결과 |
| V5 | B | 키워드 폴백으로 body 검색 | RPC 없이도 body 내용 검색 가능 |
| V6 | B | 하이브리드 랭킹 | 품질 높은 콘텐츠가 상위 노출 |
| V7 | C | Go/No-Go에서 유사 사례 확인 | 프롬프트에 과거 사례 3건 포함 |
| V8 | C | proposal_write_next에서 추천 콘텐츠 | 프롬프트에 reference_content 주입 |
| V9 | D | `GET /api/kb/health` | 영역별 건수+커버리지 반환 |
| V10 | D | `POST /api/kb/reindex` | 임베딩 없는 레코드 배치 생성 |
| V11 | D | TypeScript 빌드 | 에러 0건 |

## 8. 리스크

| 리스크 | 대응 |
|--------|------|
| 자동 등록으로 KB 오염 (저품질 콘텐츠) | draft 상태 + 품질 필터 (500자+, 70점+) |
| 임베딩 재인덱싱 시 OpenAI 비용 증가 | 배치 100건 단위, 일일 한도 설정 |
| 프롬프트 주입으로 토큰 예산 초과 | 유사 콘텐츠 3개, 300자 제한 → ~500 tokens |
| capabilities 임베딩 마이그레이션 | NULL 허용 + 배치 reindex로 점진 적용 |
| 중복 탐지 False Positive | threshold 0.9 보수적 설정, 사용자 확인 후 병합 |

## 9. 우선순위 요약

| Phase | 우선순위 | 임팩트 | 난이도 | 비고 |
|-------|:-------:|:------:|:------:|------|
| A. 자동 축적 | **HIGH** | 높음 | 중 | 핵심 선순환 루프 완성 |
| B. 검색 개선 | **HIGH** | 높음 | 중 | 활용 강화의 전제 조건 |
| C. 활용 강화 | MEDIUM | 중 | 낮 | A+B 완료 후 효과 극대화 |
| D. 관리 UX | LOW | 중 | 중 | 운영 안정화 단계 |
