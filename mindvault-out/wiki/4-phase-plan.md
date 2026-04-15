# 4. 구현 순서 (Phase 단위) & Plan: 프론트엔드 핵심 컴포넌트
Cohesion: 0.10 | Nodes: 21

## Key Nodes
- **4. 구현 순서 (Phase 단위)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 7 connections
  - -> contains -> [[phase-a-api]]
  - -> contains -> [[phase-b-phasegraph-workflowpanel-c1-c2]]
  - -> contains -> [[phase-c-evaluationview-c3]]
  - -> contains -> [[phase-d-analyticspage-c4]]
  - -> contains -> [[phase-e-proposaleditor-c5]]
  - -> contains -> [[phase-f-kb-c6]]
  - <- contains <- [[plan]]
- **Plan: 프론트엔드 핵심 컴포넌트** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 7 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4-phase]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
- **2. 범위** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 4 connections
  - -> contains -> [[2-1-in-scope-plan]]
  - -> contains -> [[2-2-out-of-scope-plan]]
  - -> contains -> [[2-3]]
  - <- contains <- [[plan]]
- **3. 기술 결정** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 4 connections
  - -> contains -> [[3-1]]
  - -> contains -> [[3-2]]
  - -> contains -> [[3-3-api]]
  - <- contains <- [[plan]]
- **3-3. API 클라이언트 확장** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[3]]
- **typescript** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 1 connections
  - <- has_code_example <- [[3-3-api]]
- **1. 목표** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **2-1. In Scope (이번 Plan)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **2-2. Out of Scope (이번 Plan 제외)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **2-3. 사전 조건** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **3-1. 신규 의존성** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **3-2. 컴포넌트 구조** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **5. 검증 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **6. 리스크** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **7. 추정 규모** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **Phase A: 인프라 + API 클라이언트 (선행)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 1 connections
  - <- contains <- [[4-phase]]
- **Phase B: PhaseGraph + WorkflowPanel (C1, C2)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 1 connections
  - <- contains <- [[4-phase]]
- **Phase C: EvaluationView (C3)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 1 connections
  - <- contains <- [[4-phase]]
- **Phase D: AnalyticsPage (C4)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 1 connections
  - <- contains <- [[4-phase]]
- **Phase E: ProposalEditor (C5)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 1 connections
  - <- contains <- [[4-phase]]
- **Phase F: KB 관리 (C6)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-core-components\frontend-core-components.plan.md) -- 1 connections
  - <- contains <- [[4-phase]]

## Internal Relationships
- 2. 범위 -> contains -> 2-1. In Scope (이번 Plan) [EXTRACTED]
- 2. 범위 -> contains -> 2-2. Out of Scope (이번 Plan 제외) [EXTRACTED]
- 2. 범위 -> contains -> 2-3. 사전 조건 [EXTRACTED]
- 3. 기술 결정 -> contains -> 3-1. 신규 의존성 [EXTRACTED]
- 3. 기술 결정 -> contains -> 3-2. 컴포넌트 구조 [EXTRACTED]
- 3. 기술 결정 -> contains -> 3-3. API 클라이언트 확장 [EXTRACTED]
- 3-3. API 클라이언트 확장 -> has_code_example -> typescript [EXTRACTED]
- 4. 구현 순서 (Phase 단위) -> contains -> Phase A: 인프라 + API 클라이언트 (선행) [EXTRACTED]
- 4. 구현 순서 (Phase 단위) -> contains -> Phase B: PhaseGraph + WorkflowPanel (C1, C2) [EXTRACTED]
- 4. 구현 순서 (Phase 단위) -> contains -> Phase C: EvaluationView (C3) [EXTRACTED]
- 4. 구현 순서 (Phase 단위) -> contains -> Phase D: AnalyticsPage (C4) [EXTRACTED]
- 4. 구현 순서 (Phase 단위) -> contains -> Phase E: ProposalEditor (C5) [EXTRACTED]
- 4. 구현 순서 (Phase 단위) -> contains -> Phase F: KB 관리 (C6) [EXTRACTED]
- Plan: 프론트엔드 핵심 컴포넌트 -> contains -> 1. 목표 [EXTRACTED]
- Plan: 프론트엔드 핵심 컴포넌트 -> contains -> 2. 범위 [EXTRACTED]
- Plan: 프론트엔드 핵심 컴포넌트 -> contains -> 3. 기술 결정 [EXTRACTED]
- Plan: 프론트엔드 핵심 컴포넌트 -> contains -> 4. 구현 순서 (Phase 단위) [EXTRACTED]
- Plan: 프론트엔드 핵심 컴포넌트 -> contains -> 5. 검증 기준 [EXTRACTED]
- Plan: 프론트엔드 핵심 컴포넌트 -> contains -> 6. 리스크 [EXTRACTED]
- Plan: 프론트엔드 핵심 컴포넌트 -> contains -> 7. 추정 규모 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 4. 구현 순서 (Phase 단위), Plan: 프론트엔드 핵심 컴포넌트, 2. 범위를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 frontend-core-components.plan.md이다.

### Key Facts
- Phase A: 인프라 + API 클라이언트 (선행) 1. `npm install` 의존성 추가 2. `lib/api.ts` 확장 (workflow, artifacts, analytics 메서드) 3. TypeScript 타입 정의 (WorkflowState, EvaluationResult, AnalyticsData 등)
- > **Feature**: frontend-core-components > **Date**: 2026-03-16 > **Status**: Plan > **Design Reference**: `docs/02-design/features/proposal-agent-v1/09-frontend.md` (§13)
- 2-1. In Scope (이번 Plan)
- `lib/api.ts`에 추가할 메서드:
- ```typescript // Workflow workflow: { start(id: string, state?: object): Promise<...>, getState(id: string): Promise<...>, resume(id: string, data: object): Promise<...>, getTokenUsage(id: string): Promise<...>, stream(id: string): EventSource, }, // Artifacts artifacts: { get(id: string, step:…
