# Plan: pydantic-schema-refinement & 4. 수용 기준
Cohesion: 0.12 | Nodes: 16

## Key Nodes
- **Plan: pydantic-schema-refinement** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.plan.md) -- 7 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
- **4. 수용 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.plan.md) -- 4 connections
  - -> contains -> [[phase-a]]
  - -> contains -> [[phase-b-response]]
  - -> contains -> [[phase-c]]
  - <- contains <- [[plan-pydantic-schema-refinement]]
- **In-Scope** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.plan.md) -- 4 connections
  - -> contains -> [[phase-a-currentuser]]
  - -> contains -> [[phase-b-response]]
  - -> contains -> [[phase-c-responsemodel]]
  - <- contains <- [[3]]
- **3. 범위** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.plan.md) -- 3 connections
  - -> contains -> [[in-scope]]
  - -> contains -> [[out-of-scope]]
  - <- contains <- [[plan-pydantic-schema-refinement]]
- **1. 배경** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.plan.md) -- 1 connections
  - <- contains <- [[plan-pydantic-schema-refinement]]
- **2. 목표** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.plan.md) -- 1 connections
  - <- contains <- [[plan-pydantic-schema-refinement]]
- **5. 구현 순서** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.plan.md) -- 1 connections
  - <- contains <- [[plan-pydantic-schema-refinement]]
- **6. 리스크 및 대응** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.plan.md) -- 1 connections
  - <- contains <- [[plan-pydantic-schema-refinement]]
- **7. 의존성** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.plan.md) -- 1 connections
  - <- contains <- [[plan-pydantic-schema-refinement]]
- **Out-of-Scope** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **Phase A (기반 인프라)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **Phase A — 기반 인프라 (공통 모델 + CurrentUser)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.plan.md) -- 1 connections
  - <- contains <- [[in-scope]]
- **Phase B — 핵심 도메인 Response 모델 (높은 영향도)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.plan.md) -- 1 connections
  - <- contains <- [[in-scope]]
- **Phase B (Response 모델)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **Phase C (라우트 적용)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **Phase C — 라우트 적용 (response_model 바인딩)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.plan.md) -- 1 connections
  - <- contains <- [[in-scope]]

## Internal Relationships
- 3. 범위 -> contains -> In-Scope [EXTRACTED]
- 3. 범위 -> contains -> Out-of-Scope [EXTRACTED]
- 4. 수용 기준 -> contains -> Phase A (기반 인프라) [EXTRACTED]
- 4. 수용 기준 -> contains -> Phase B (Response 모델) [EXTRACTED]
- 4. 수용 기준 -> contains -> Phase C (라우트 적용) [EXTRACTED]
- In-Scope -> contains -> Phase A — 기반 인프라 (공통 모델 + CurrentUser) [EXTRACTED]
- In-Scope -> contains -> Phase B — 핵심 도메인 Response 모델 (높은 영향도) [EXTRACTED]
- In-Scope -> contains -> Phase C — 라우트 적용 (response_model 바인딩) [EXTRACTED]
- Plan: pydantic-schema-refinement -> contains -> 1. 배경 [EXTRACTED]
- Plan: pydantic-schema-refinement -> contains -> 2. 목표 [EXTRACTED]
- Plan: pydantic-schema-refinement -> contains -> 3. 범위 [EXTRACTED]
- Plan: pydantic-schema-refinement -> contains -> 4. 수용 기준 [EXTRACTED]
- Plan: pydantic-schema-refinement -> contains -> 5. 구현 순서 [EXTRACTED]
- Plan: pydantic-schema-refinement -> contains -> 6. 리스크 및 대응 [EXTRACTED]
- Plan: pydantic-schema-refinement -> contains -> 7. 의존성 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: pydantic-schema-refinement, 4. 수용 기준, In-Scope를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 pydantic-schema-refinement.plan.md이다.

### Key Facts
- > 290개 API 엔드포인트의 요청/응답 Pydantic 스키마 정교화 — OpenAPI 자동 문서화 + 프론트엔드 타입 동기화 기반 확보
- Phase A (기반 인프라) - [ ] `CurrentUser` 모델 도입, `deps.py` 반환 타입 전환 - [ ] `common.py`의 `PaginatedResponse[T]`, `StatusResponse` 최소 5곳에서 사용 - [ ] `types.py`의 Literal 타입이 `user_schemas.py`, `schemas.py`에 적용 - [ ] `Optional` → `| None` 통일 (`user_schemas.py`) - [ ] 기존 테스트 통과 (Breaking change 없음)
- Phase A — 기반 인프라 (공통 모델 + CurrentUser) 1. `app/models/common.py` 신규 — 공통 응답 모델 - `StatusResponse` (status + message) - `PaginatedResponse[T]` (Generic, items + total + page + per_page) - `ItemsResponse[T]` (items + total, 페이지네이션 없는 버전) - `DeleteResponse` (deleted + id) 2. `app/models/types.py` 신규 —…
- 현재 290개 API 엔드포인트 중 **93%가 비정형 dict를 반환**하고 있으며, `response_model`을 사용하는 엔드포인트는 20건(7%)에 불과하다. 이로 인해:
- - **response_model 커버리지**: 7% → **80%+** (핵심 도메인 100%) - **공통 패턴 모델화**: PaginatedResponse, StatusResponse 등 재사용 모델 도입 - **CurrentUser 타입 안전**: `dict` → Pydantic 모델로 전환, IDE 자동완성 지원 - **Literal 타입 정리**: 카테고리형 문자열을 공유 타입 모듈로 통합 - **Optional → `| None` 스타일 통일**: Python 3.11+ 컨벤션 - **OpenAPI 문서 품질**:…
