# 2. 구현 범위 & Frontend Design Gap 해소 계획서
Cohesion: 0.11 | Nodes: 19

## Key Nodes
- **2. 구현 범위** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 7 connections
  - -> contains -> [[phase-a-gono-go-13-4-85-95]]
  - -> contains -> [[phase-b-13-8-75-90]]
  - -> contains -> [[phase-c-13-6]]
  - -> contains -> [[phase-d-ui-31-3-75-85]]
  - -> contains -> [[phase-e-low]]
  - <- contains <- [[frontend-design-gap]]
  - <- contains <- [[4]]
- **Frontend Design Gap 해소 계획서** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 6 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5-not-scope]]
  - -> contains -> [[6]]
- **4. 수정 대상 파일** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 4 connections
  - -> contains -> [[2]]
  - -> contains -> [[4]]
  - <- contains <- [[frontend-design-gap]]
  - <- contains <- [[4]]
- **Phase A — Go/No-Go 패널 보강 (§13-4 충실도 85% → 95%)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 3 connections
  - -> contains -> [[a-1-gonogopanel-4]]
  - -> contains -> [[a-2]]
  - <- contains <- [[2]]
- **Phase B — 대시보드 역할별 위젯 (§13-8 충실도 75% → 90%)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 3 connections
  - -> contains -> [[b-1]]
  - -> contains -> [[b-2]]
  - <- contains <- [[2]]
- **Phase D — UI 인프라 보강 (§31-3 충실도 75% → 85%)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 3 connections
  - -> contains -> [[d-1-tiptap]]
  - -> contains -> [[d-2-tailwind-merge-clsx]]
  - <- contains <- [[2]]
- **Phase C — 포지셔닝 변경 영향 미리보기 (§13-6 미구현 → 구현)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 2 connections
  - -> contains -> [[c-1-positioningimpactmodal]]
  - <- contains <- [[2]]
- **1. 배경 및 목적** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 1 connections
  - <- contains <- [[frontend-design-gap]]
- **3. 구현 순서 및 의존성** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 1 connections
  - <- contains <- [[frontend-design-gap]]
- **5. 범위 외 (NOT Scope)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 1 connections
  - <- contains <- [[frontend-design-gap]]
- **6. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 1 connections
  - <- contains <- [[frontend-design-gap]]
- **A-1. GoNoGoPanel 4축 점수 표시** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 1 connections
  - <- contains <- [[phase-a-gono-go-13-4-85-95]]
- **A-2. 강점/리스크 분할 표시** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 1 connections
  - <- contains <- [[phase-a-gono-go-13-4-85-95]]
- **B-1. 팀장 위젯 — 결재 대기 + 마감 임박** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 1 connections
  - <- contains <- [[phase-b-13-8-75-90]]
- **B-2. 경영진 위젯 — 본부별 비교 테이블** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 1 connections
  - <- contains <- [[phase-b-13-8-75-90]]
- **C-1. PositioningImpactModal 신규 컴포넌트** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 1 connections
  - <- contains <- [[phase-c-13-6]]
- **D-1. Tiptap 확장 설치** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 1 connections
  - <- contains <- [[phase-d-ui-31-3-75-85]]
- **D-2. tailwind-merge + clsx 도입** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 1 connections
  - <- contains <- [[phase-d-ui-31-3-75-85]]
- **Phase E — LOW 우선순위 (선택적)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.plan.md) -- 1 connections
  - <- contains <- [[2]]

## Internal Relationships
- 2. 구현 범위 -> contains -> Phase A — Go/No-Go 패널 보강 (§13-4 충실도 85% → 95%) [EXTRACTED]
- 2. 구현 범위 -> contains -> Phase B — 대시보드 역할별 위젯 (§13-8 충실도 75% → 90%) [EXTRACTED]
- 2. 구현 범위 -> contains -> Phase C — 포지셔닝 변경 영향 미리보기 (§13-6 미구현 → 구현) [EXTRACTED]
- 2. 구현 범위 -> contains -> Phase D — UI 인프라 보강 (§31-3 충실도 75% → 85%) [EXTRACTED]
- 2. 구현 범위 -> contains -> Phase E — LOW 우선순위 (선택적) [EXTRACTED]
- 4. 수정 대상 파일 -> contains -> 2. 구현 범위 [EXTRACTED]
- 4. 수정 대상 파일 -> contains -> 4. 수정 대상 파일 [EXTRACTED]
- Frontend Design Gap 해소 계획서 -> contains -> 1. 배경 및 목적 [EXTRACTED]
- Frontend Design Gap 해소 계획서 -> contains -> 2. 구현 범위 [EXTRACTED]
- Frontend Design Gap 해소 계획서 -> contains -> 3. 구현 순서 및 의존성 [EXTRACTED]
- Frontend Design Gap 해소 계획서 -> contains -> 4. 수정 대상 파일 [EXTRACTED]
- Frontend Design Gap 해소 계획서 -> contains -> 5. 범위 외 (NOT Scope) [EXTRACTED]
- Frontend Design Gap 해소 계획서 -> contains -> 6. 성공 기준 [EXTRACTED]
- Phase A — Go/No-Go 패널 보강 (§13-4 충실도 85% → 95%) -> contains -> A-1. GoNoGoPanel 4축 점수 표시 [EXTRACTED]
- Phase A — Go/No-Go 패널 보강 (§13-4 충실도 85% → 95%) -> contains -> A-2. 강점/리스크 분할 표시 [EXTRACTED]
- Phase B — 대시보드 역할별 위젯 (§13-8 충실도 75% → 90%) -> contains -> B-1. 팀장 위젯 — 결재 대기 + 마감 임박 [EXTRACTED]
- Phase B — 대시보드 역할별 위젯 (§13-8 충실도 75% → 90%) -> contains -> B-2. 경영진 위젯 — 본부별 비교 테이블 [EXTRACTED]
- Phase C — 포지셔닝 변경 영향 미리보기 (§13-6 미구현 → 구현) -> contains -> C-1. PositioningImpactModal 신규 컴포넌트 [EXTRACTED]
- Phase D — UI 인프라 보강 (§31-3 충실도 75% → 85%) -> contains -> D-1. Tiptap 확장 설치 [EXTRACTED]
- Phase D — UI 인프라 보강 (§31-3 충실도 75% → 85%) -> contains -> D-2. tailwind-merge + clsx 도입 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 2. 구현 범위, Frontend Design Gap 해소 계획서, 4. 수정 대상 파일를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 frontend-design-gap.plan.md이다.

### Key Facts
- Phase A — Go/No-Go 패널 보강 (§13-4 충실도 85% → 95%)
- > 설계 문서(§13 프론트엔드 핵심 컴포넌트) 대비 미구현/차이 항목을 체계적으로 해소하여 설계 충실도를 94% → 98%+ 로 끌어올린다.
- 신규 파일 (2개) | 파일 | 용도 | |------|------| | `components/PositioningImpactModal.tsx` | 포지셔닝 변경 영향 미리보기 | | `lib/utils.ts` | cn() 유틸 (tailwind-merge + clsx) |
- **현재**: 포지셔닝 선택 + 의사결정 사유만 표시 **설계**: AI 수주 가능성 4축 점수(기술/실적/가격/경쟁) + 강점/리스크 분할 + 종합 점수 바
- **현재**: 단일 대시보드 + 스코프 토글 (개인/팀/본부/전체) **설계**: 팀장 전용 위젯(결재대기/마감임박), 경영진 전용 위젯(본부비교/포지셔닝별)
