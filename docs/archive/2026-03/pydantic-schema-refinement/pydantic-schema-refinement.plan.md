# Plan: pydantic-schema-refinement

> 290개 API 엔드포인트의 요청/응답 Pydantic 스키마 정교화 — OpenAPI 자동 문서화 + 프론트엔드 타입 동기화 기반 확보

## 1. 배경

현재 290개 API 엔드포인트 중 **93%가 비정형 dict를 반환**하고 있으며, `response_model`을 사용하는 엔드포인트는 20건(7%)에 불과하다. 이로 인해:

- **OpenAPI(Swagger) 문서**: 응답 스키마가 비어 있어 프론트엔드 개발 시 추론에 의존
- **직렬화 미검증**: datetime, None, 민감 필드가 필터 없이 그대로 노출
- **계약 깨짐 무탐지**: 백엔드 필드명/타입 변경 시 프론트엔드가 런타임에야 발견
- **`user: dict`**: 인증 의존성이 dict → KeyError 위험, IDE 자동완성 불가

입력(Create) 모델은 비교적 양호하나, **출력(Response) 모델이 심각하게 부족**한 상태다.

### 현황 수치

| 항목 | 수치 |
|------|------|
| 전체 API 엔드포인트 | ~290개 |
| `response_model` 적용 | 20건 (7%) |
| `return {dict}` 비정형 응답 | 221건 (76%) |
| 정의된 Pydantic 모델 | ~60개 |
| 스키마 파일 수 | 6개 |

## 2. 목표

- **response_model 커버리지**: 7% → **80%+** (핵심 도메인 100%)
- **공통 패턴 모델화**: PaginatedResponse, StatusResponse 등 재사용 모델 도입
- **CurrentUser 타입 안전**: `dict` → Pydantic 모델로 전환, IDE 자동완성 지원
- **Literal 타입 정리**: 카테고리형 문자열을 공유 타입 모듈로 통합
- **Optional → `| None` 스타일 통일**: Python 3.11+ 컨벤션
- **OpenAPI 문서 품질**: 프론트엔드가 자동 생성된 타입으로 API 연동 가능

## 3. 범위

### In-Scope

#### Phase A — 기반 인프라 (공통 모델 + CurrentUser)
1. `app/models/common.py` 신규 — 공통 응답 모델
   - `StatusResponse` (status + message)
   - `PaginatedResponse[T]` (Generic, items + total + page + per_page)
   - `ItemsResponse[T]` (items + total, 페이지네이션 없는 버전)
   - `DeleteResponse` (deleted + id)
2. `app/models/types.py` 신규 — 공유 Literal 타입
   - `UserRole = Literal["member", "lead", "director", "executive", "admin"]`
   - `ProposalStatus = Literal["draft", "in_progress", "review", "approved", "submitted", "won", "lost", "void"]`
   - `ScopeType = Literal["team", "division", "org"]`
   - 기타 반복 사용되는 카테고리형 타입
3. `app/models/auth_schemas.py` 신규 — 인증 모델
   - `CurrentUser(BaseModel)` — id, email, name, role, org_id, team_id, division_id
   - `deps.py`의 `get_current_user` 반환 타입을 `CurrentUser`로 전환
4. `user_schemas.py` — `Optional` → `| None` 스타일 통일, `UserCreate.role` → Literal 전환

#### Phase B — 핵심 도메인 Response 모델 (높은 영향도)
5. `app/models/proposal_schemas.py` 신규 — 제안서 도메인
   - `ProposalListItem` (목록용 요약)
   - `ProposalDetail` (상세 조회)
   - `ProposalResultResponse`
   - `LessonResponse`
6. `app/models/workflow_schemas.py` 신규 — 워크플로 도메인
   - `WorkflowStateResponse`
   - `WorkflowHistoryItem`
   - `WorkflowStreamEvent`
   - `WorkflowResumeRequest` (현재 `dict`)
7. `app/models/artifact_schemas.py` 신규 — 산출물 도메인
   - `ArtifactResponse`
   - `ComplianceMatrixResponse`
   - `SectionRegenerateRequest`
   - `AiAssistResponse`
8. `app/models/notification_schemas.py` 신규 — 알림 도메인
   - `NotificationResponse`
   - `NotificationSettingsResponse`
9. `app/models/analytics_schemas.py` 신규 — 분석 도메인
   - `WinRateResponse`
   - `FailureReasonsResponse`
   - `PositioningWinRateResponse`
   - `MonthlyTrendsResponse`
   - `CompetitorAnalysisResponse`

#### Phase C — 라우트 적용 (response_model 바인딩)
10. 각 `routes_*.py`에 `response_model` 적용
    - 우선순위: proposal → workflow → artifacts → notification → analytics → admin → 나머지
11. 인라인 `return {dict}` → 모델 인스턴스 반환으로 전환
12. Query 파라미터 모델화 (반복 패턴 3회 이상 사용 그룹)

### Out-of-Scope
- 레거시 `routes_v31.py` — 제거 예정이므로 스키마화 불필요
- `routes_prompt_evolution.py` — 내부 관리 도구, 후순위
- 프론트엔드 타입 자동 생성 도구(openapi-typescript 등) 도입 — 별도 피처
- DB 스키마 변경 — 이번 작업은 API 레이어만 대상
- 테스트 코드 — 스키마 변경에 따른 테스트 수정은 포함하되 신규 테스트 작성은 별도

## 4. 수용 기준

### Phase A (기반 인프라)
- [ ] `CurrentUser` 모델 도입, `deps.py` 반환 타입 전환
- [ ] `common.py`의 `PaginatedResponse[T]`, `StatusResponse` 최소 5곳에서 사용
- [ ] `types.py`의 Literal 타입이 `user_schemas.py`, `schemas.py`에 적용
- [ ] `Optional` → `| None` 통일 (`user_schemas.py`)
- [ ] 기존 테스트 통과 (Breaking change 없음)

### Phase B (Response 모델)
- [ ] 핵심 5 도메인(proposal, workflow, artifact, notification, analytics) Response 모델 정의
- [ ] 각 모델에 `model_config = ConfigDict(from_attributes=True)` 설정 (ORM 호환)
- [ ] `RecommendationsResponse.data: dict` → 정형 필드로 전환

### Phase C (라우트 적용)
- [ ] `response_model` 커버리지 80%+ (핵심 도메인 100%)
- [ ] `return {dict}` 221건 → 50건 이하
- [ ] OpenAPI `/docs`에서 모든 핵심 엔드포인트 응답 스키마 확인 가능
- [ ] TypeScript 빌드 에러 0건 (프론트엔드 영향 없음)

## 5. 구현 순서

```
Phase A (기반 인프라)          Phase B (Response 모델)         Phase C (라우트 적용)
┌─────────────────┐          ┌─────────────────┐           ┌─────────────────┐
│ A-1. common.py  │          │ B-1. proposal    │           │ C-1. proposal   │
│ A-2. types.py   │─────────▶│ B-2. workflow    │──────────▶│ C-2. workflow   │
│ A-3. auth       │          │ B-3. artifact    │           │ C-3. artifact   │
│ A-4. user 통일  │          │ B-4. notification│           │ C-4. notification│
└─────────────────┘          │ B-5. analytics   │           │ C-5. analytics  │
                             │ B-6. bid 보완    │           │ C-6. 나머지     │
                             └─────────────────┘           └─────────────────┘
```

**예상 신규/수정 파일:**
- 신규: ~8개 (`common.py`, `types.py`, `auth_schemas.py`, `proposal_schemas.py`, `workflow_schemas.py`, `artifact_schemas.py`, `notification_schemas.py`, `analytics_schemas.py`)
- 수정: ~25개 (`deps.py` + `routes_*.py` 20+개 + 기존 스키마 3개)

## 6. 리스크 및 대응

| 리스크 | 영향 | 대응 |
|--------|------|------|
| `response_model` 적용 시 기존 dict 키와 불일치 | 프론트엔드 500 에러 | Phase별 점진 적용, 프론트 빌드 검증 병행 |
| `CurrentUser` 전환 시 dict 접근 코드 잔존 | 런타임 AttributeError | grep로 `user["` / `user.get(` 패턴 전수 조사 후 전환 |
| `response_model`의 직렬화 성능 오버헤드 | 응답 지연 | 대량 목록 API만 선별 벤치마크 |
| 기존 `bid_schemas.py` 모델과 신규 모델 중복 | 혼란 | 기존 모델 유지, 신규는 별도 네임스페이스 |

## 7. 의존성

- 선행 필요: 없음 (API 레이어만 변경)
- 후행 가능: `openapi-typescript` 도입 (이번 작업 완료 후)
- 프론트엔드: `api.ts` 타입은 현재 수동 정의 → 이번 작업으로 OpenAPI 기반 자동화 준비 완료
