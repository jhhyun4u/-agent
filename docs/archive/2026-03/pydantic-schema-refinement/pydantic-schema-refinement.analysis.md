# pydantic-schema-refinement 설계-구현 갭 분석

> **설계 문서**: `docs/02-design/features/pydantic-schema-refinement.design.md`
> **분석일**: 2026-03-26
> **종합 일치율**: **94%** (90% 품질 게이트 통과)

## 1. 전체 요약

| 카테고리 | 항목 수 | MATCH | PARTIAL | MISS | 점수 |
|----------|:-------:|:-----:|:-------:|:----:|:----:|
| Phase A - 기반 인프라 | 11 | 11 | 0 | 0 | 100% |
| Phase B - 도메인 Response 모델 | 7 | 6 | 1 | 0 | 93% |
| Phase C - 라우트 적용 | 9 | 7 | 2 | 0 | 89% |
| **종합** | **27** | **24** | **3** | **0** | **94%** |

## 2. GAP 목록

| # | 항목 | 심각도 | 설명 |
|---|------|:------:|------|
| GAP-1 | SectionLockResponse | MEDIUM | `workflow_schemas.py`에 클래스 미정의. `lock_section` 라우트가 raw dict 반환 |
| GAP-2 | workflow response_model 4건 | MEDIUM | lock, locks, ai-status, ai-logs에 response_model 미적용 |
| GAP-3 | GET result response_model | LOW | `routes_performance.py`에 `ProposalResultResponse` response_model 미적용 |

## 3. EXTRA 목록 (비파괴적 추가)

| # | 항목 | 위치 | 설명 |
|---|------|------|------|
| EXT-1 | ProjectRole Literal | types.py | `Literal["member", "section_lead"]` 공유 타입 |
| EXT-2 | auth 추가 필드 | auth_schemas.py | `must_change_password`, `deactivated_at` |
| EXT-3 | model_config from_attributes | auth_schemas.py | ORM 호환 |
| EXT-4 | extra="ignore" | proposal_schemas.py | DB 스키마 변경 안전성 |
| EXT-5 | QA_CATEGORIES 별칭 | schemas.py | 하위 호환 유지 |

## 4. Phase별 상세

### Phase A (100%) — 11/11 MATCH
- `types.py`: 13종 Literal 타입 완전 일치
- `common.py`: 4개 Generic 모델 완전 일치
- `auth_schemas.py`: `CurrentUser` + `AuthMessageResponse` 완전 구현
- `deps.py`: `get_current_user() -> CurrentUser` 전환 완료, 속성 접근 전환 완료
- `user_schemas.py`: `Optional` → `| None` 통일, `UserRole` Literal 적용
- `schemas.py`: `QACategory`, `EvaluatorReaction` 참조 전환 + datetime 강화
- `bid_schemas.py`: `RecommendationsData` 정형화 완료
- `phase_schemas.py` + `pricing/models.py`: `datetime.now(UTC)` 통일

### Phase B (93%) — 6 MATCH, 1 PARTIAL
- `proposal_schemas.py`: 5 클래스 ✅
- `workflow_schemas.py`: 14/15 클래스 ✅ (GAP-1: `SectionLockResponse` 누락)
- `artifact_schemas.py`: 8 클래스 ✅
- `notification_schemas.py`: 3 클래스 ✅
- `analytics_schemas.py`: 14 클래스 ✅
- `performance_schemas.py`: 10 클래스 ✅
- `admin_schemas.py`: 13 클래스 ✅

### Phase C (89%) — 7 MATCH, 2 PARTIAL
- `response_model` 총 60건 적용 (핵심 8개 라우트)
- `CurrentUser` 타입 힌트: `user["key"]` 0건, `user: dict` 0건 (in-scope)
- GAP-2: workflow 4 EP 미적용
- GAP-3: performance 1 EP 미적용

## 5. 권장 조치

### 즉시 (GAP-1+2 통합, ~30분)
`workflow_schemas.py`에 `SectionLockResponse` 추가 + `routes_workflow.py` 4 EP에 response_model 적용

### 후속 (GAP-3, ~5분)
`routes_performance.py` GET result에 `response_model=ProposalResultResponse` 추가

### 문서 동기화
설계 문서에 EXTRA 5건 역반영

## 6. 결론

GAP 3건 수정 시 **97%+** 달성 가능. 모든 GAP이 `response_model` 미적용 수준이며, 실제 API 반환 데이터 구조는 정상 동작 중.
