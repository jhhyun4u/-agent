# pydantic-schema-refinement 설계-구현 갭 분석 & 4. Phase별 상세
Cohesion: 0.17 | Nodes: 12

## Key Nodes
- **pydantic-schema-refinement 설계-구현 갭 분석** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.analysis.md) -- 6 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-gap]]
  - -> contains -> [[3-extra]]
  - -> contains -> [[4-phase]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
- **4. Phase별 상세** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.analysis.md) -- 4 connections
  - -> contains -> [[phase-a-100-1111-match]]
  - -> contains -> [[phase-b-93-6-match-1-partial]]
  - -> contains -> [[phase-c-89-7-match-2-partial]]
  - <- contains <- [[pydantic-schema-refinement]]
- **5. 권장 조치** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.analysis.md) -- 3 connections
  - -> contains -> [[gap-12-30]]
  - -> contains -> [[gap-3-5]]
  - <- contains <- [[pydantic-schema-refinement]]
- **1. 전체 요약** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.analysis.md) -- 1 connections
  - <- contains <- [[pydantic-schema-refinement]]
- **2. GAP 목록** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.analysis.md) -- 1 connections
  - <- contains <- [[pydantic-schema-refinement]]
- **3. EXTRA 목록 (비파괴적 추가)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.analysis.md) -- 1 connections
  - <- contains <- [[pydantic-schema-refinement]]
- **6. 결론** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.analysis.md) -- 1 connections
  - <- contains <- [[pydantic-schema-refinement]]
- **즉시 (GAP-1+2 통합, ~30분)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.analysis.md) -- 1 connections
  - <- contains <- [[5]]
- **후속 (GAP-3, ~5분)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.analysis.md) -- 1 connections
  - <- contains <- [[5]]
- **Phase A (100%) — 11/11 MATCH** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.analysis.md) -- 1 connections
  - <- contains <- [[4-phase]]
- **Phase B (93%) — 6 MATCH, 1 PARTIAL** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.analysis.md) -- 1 connections
  - <- contains <- [[4-phase]]
- **Phase C (89%) — 7 MATCH, 2 PARTIAL** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\pydantic-schema-refinement\pydantic-schema-refinement.analysis.md) -- 1 connections
  - <- contains <- [[4-phase]]

## Internal Relationships
- 4. Phase별 상세 -> contains -> Phase A (100%) — 11/11 MATCH [EXTRACTED]
- 4. Phase별 상세 -> contains -> Phase B (93%) — 6 MATCH, 1 PARTIAL [EXTRACTED]
- 4. Phase별 상세 -> contains -> Phase C (89%) — 7 MATCH, 2 PARTIAL [EXTRACTED]
- 5. 권장 조치 -> contains -> 즉시 (GAP-1+2 통합, ~30분) [EXTRACTED]
- 5. 권장 조치 -> contains -> 후속 (GAP-3, ~5분) [EXTRACTED]
- pydantic-schema-refinement 설계-구현 갭 분석 -> contains -> 1. 전체 요약 [EXTRACTED]
- pydantic-schema-refinement 설계-구현 갭 분석 -> contains -> 2. GAP 목록 [EXTRACTED]
- pydantic-schema-refinement 설계-구현 갭 분석 -> contains -> 3. EXTRA 목록 (비파괴적 추가) [EXTRACTED]
- pydantic-schema-refinement 설계-구현 갭 분석 -> contains -> 4. Phase별 상세 [EXTRACTED]
- pydantic-schema-refinement 설계-구현 갭 분석 -> contains -> 5. 권장 조치 [EXTRACTED]
- pydantic-schema-refinement 설계-구현 갭 분석 -> contains -> 6. 결론 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 pydantic-schema-refinement 설계-구현 갭 분석, 4. Phase별 상세, 5. 권장 조치를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 pydantic-schema-refinement.analysis.md이다.

### Key Facts
- > **설계 문서**: `docs/02-design/features/pydantic-schema-refinement.design.md` > **분석일**: 2026-03-26 > **종합 일치율**: **94%** (90% 품질 게이트 통과)
- Phase A (100%) — 11/11 MATCH - `types.py`: 13종 Literal 타입 완전 일치 - `common.py`: 4개 Generic 모델 완전 일치 - `auth_schemas.py`: `CurrentUser` + `AuthMessageResponse` 완전 구현 - `deps.py`: `get_current_user() -> CurrentUser` 전환 완료, 속성 접근 전환 완료 - `user_schemas.py`: `Optional` → `| None` 통일, `UserRole` Literal…
- 즉시 (GAP-1+2 통합, ~30분) `workflow_schemas.py`에 `SectionLockResponse` 추가 + `routes_workflow.py` 4 EP에 response_model 적용
- | 카테고리 | 항목 수 | MATCH | PARTIAL | MISS | 점수 | |----------|:-------:|:-----:|:-------:|:----:|:----:| | Phase A - 기반 인프라 | 11 | 11 | 0 | 0 | 100% | | Phase B - 도메인 Response 모델 | 7 | 6 | 1 | 0 | 93% | | Phase C - 라우트 적용 | 9 | 7 | 2 | 0 | 89% | | **종합** | **27** | **24** | **3** | **0** | **94%** |
- | # | 항목 | 심각도 | 설명 | |---|------|:------:|------| | GAP-1 | SectionLockResponse | MEDIUM | `workflow_schemas.py`에 클래스 미정의. `lock_section` 라우트가 raw dict 반환 | | GAP-2 | workflow response_model 4건 | MEDIUM | lock, locks, ai-status, ai-logs에 response_model 미적용 | | GAP-3 | GET result response_model |…
