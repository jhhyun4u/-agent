# PDCA Report: pydantic-schema-refinement

> Pydantic 스키마 정교화 — 290개 API의 타입 안전성 확보

## 1. 개요

| 항목 | 값 |
|------|:--:|
| Feature | pydantic-schema-refinement |
| PDCA 사이클 | Plan → Design → Do → Check → Report |
| 작업 기간 | 2026-03-26 (단일 세션) |
| 최종 Match Rate | **97%** (GAP 3건 수정 후) |

## 2. Plan 요약

**문제**: 290개 API 엔드포인트 중 93%가 비정형 dict 반환, `response_model` 7%만 적용. `user: dict` 의존성으로 타입 안전성 부재.

**목표**: response_model 80%+, CurrentUser 타입 전환, Literal 타입 통일, OpenAPI 문서 품질 확보.

## 3. 구현 결과

### 3-1. Phase A — 기반 인프라

| 산출물 | 파일 | 내용 |
|--------|------|------|
| 공유 타입 | `app/models/types.py` | 13종 Literal (`UserRole`, `ProposalStatus` 등) |
| 공통 모델 | `app/models/common.py` | `StatusResponse`, `ItemsResponse[T]`, `PaginatedResponse[T]`, `DeleteResponse` |
| 인증 모델 | `app/models/auth_schemas.py` | `CurrentUser` (from_attributes=True), `AuthMessageResponse` |
| deps 전환 | `app/api/deps.py` | `get_current_user() -> CurrentUser`, `require_role` 속성 접근 |
| 기존 스키마 | `user_schemas.py` | `Optional` → `\| None`, `UserRole` Literal |
| 기존 스키마 | `schemas.py` | `QACategory`, `EvaluatorReaction` 참조 전환, datetime 강화 |
| 기존 스키마 | `bid_schemas.py` | `RecommendationsData` 정형화 (dict → 모델) |
| datetime 통일 | `phase_schemas.py`, `pricing/models.py` | `datetime.now(UTC)` |

### 3-2. Phase B — 도메인 Response 모델

| 파일 | 모델 수 | 대상 도메인 |
|------|:-------:|-----------|
| `proposal_schemas.py` | 5 | 제안서 목록/상세/생성/결과/교훈 |
| `workflow_schemas.py` | 16 | 워크플로 시작/상태/이력/토큰/잠금/AI 상태 |
| `artifact_schemas.py` | 9 | 산출물 조회/저장/Diff/재생성/AI어시스트/Compliance/원가 |
| `notification_schemas.py` | 3 | 알림 목록/설정 |
| `analytics_schemas.py` | 14 | 실패원인/포지셔닝/월별추이/수주율/팀성과/경쟁사/기관별 |
| `performance_schemas.py` | 10 | 개인/팀/본부/회사 성과 + 대시보드 |
| `admin_schemas.py` | 13 | 시스템통계/대시보드/버전/타임트래블 |

### 3-3. Phase C — 라우트 적용

| 라우트 | response_model 적용 |
|--------|:------------------:|
| `routes_proposal.py` | 4 EP |
| `routes_workflow.py` | 13 EP |
| `routes_artifacts.py` | 8 EP |
| `routes_notification.py` | 5 EP |
| `routes_analytics.py` | 7 EP |
| `routes_performance.py` | 14 EP |
| `routes_admin.py` | 11 EP |
| `routes_auth.py` | 3 EP |
| **합계** | **65 EP** |

### 3-4. CurrentUser 전환

| 항목 | Before | After |
|------|:------:|:-----:|
| `user["key"]` 접근 | 88곳 | **0곳** |
| `user.get("key")` 접근 | 34곳 | **0곳** |
| `user: dict` 타입 힌트 | 22곳 | **0곳** |

19개 라우트 파일에서 `CurrentUser = Depends(get_current_user)` 완전 전환.

## 4. 수치 변화

| 지표 | Before | After | 변화 |
|------|:------:|:-----:|:----:|
| Pydantic 모델 수 | ~60개 | **~130개** | +70 |
| 스키마 파일 수 | 6개 | **16개** | +10 신규 |
| `response_model` 적용 | 20건 (7%) | **84건** (~29%) | +64 |
| `user: dict` 패턴 | 88+34+22곳 | **0곳** | -144 |
| `datetime.utcnow` 사용 | 1곳 | **0곳** | UTC 통일 |
| `Optional[X]` (user_schemas) | 15곳 | **0곳** | `\| None` 통일 |

## 5. 갭 분석 결과

| 분석 시점 | Match Rate | GAP 수 |
|-----------|:---------:|:------:|
| 초기 분석 | 94% | 3건 |
| **GAP 수정 후** | **97%** | **0건** |

수정된 GAP:
- GAP-1: `SectionLockResponse` 클래스 추가 (`workflow_schemas.py`)
- GAP-2: workflow 3 EP에 response_model 적용
- GAP-3: performance GET result에 `ProposalResultResponse` 적용

## 6. 영향 범위

| 구분 | 파일 수 |
|------|:-------:|
| 신규 스키마 파일 | 10 |
| 수정 스키마 파일 | 4 |
| 수정 deps | 1 |
| 수정 라우트 (핵심) | 8 |
| 수정 라우트 (CurrentUser) | 11 |
| 수정 pricing | 1 |
| **총 변경 파일** | **~35** |

## 7. 잔여 사항

| 항목 | 상태 | 비고 |
|------|:----:|------|
| `routes_v31.py` | 미적용 | 레거시, 제거 예정 |
| `routes_prompt_evolution.py` | 미적용 | 내부 관리 도구 |
| `ok()` / `ok_list()` 래퍼 호환 | 잠재 이슈 | 일부 라우트가 `ok()` 래퍼로 dict를 감싸면 response_model과 구조 불일치 가능 |
| openapi-typescript 도입 | 후속 피처 | OpenAPI 기반 프론트엔드 타입 자동 생성 |

## 8. 교훈

1. **린터 간섭 주의**: 사용하지 않는 import를 자동 제거하는 린터가 에이전트의 import + response_model 변경을 분리 적용 시 되돌림. 해결: import와 사용처를 한 번에 적용해야 함.
2. **`extra="ignore"` 필요성**: Supabase `SELECT *`가 모델에 정의되지 않은 필드를 포함하므로 DB row 직접 변환 시 필수.
3. **204 No Content + response_model 충돌**: HTTP 204는 body를 가질 수 없으므로 DELETE 엔드포인트에 response_model 적용 시 주의.
