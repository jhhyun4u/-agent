# typescript & **Phase 3: 프론트엔드 업데이트** (0.5일)
Cohesion: 0.53 | Nodes: 6

## Key Nodes
- **typescript** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\unified-state-system.plan.md) -- 4 connections
  - <- has_code_example <- [[31]]
  - <- has_code_example <- [[32]]
  - <- has_code_example <- [[33-ui]]
  - <- has_code_example <- [[34-api]]
- ****Phase 3: 프론트엔드 업데이트** (0.5일)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\unified-state-system.plan.md) -- 4 connections
  - -> contains -> [[31]]
  - -> contains -> [[32]]
  - -> contains -> [[33-ui]]
  - -> contains -> [[34-api]]
- **3.1 타입 정의 업데이트** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\unified-state-system.plan.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[phase-3-05]]
- **3.2 상태 배지 컴포넌트 업데이트** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\unified-state-system.plan.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[phase-3-05]]
- **3.3 필터 UI 업데이트** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\unified-state-system.plan.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[phase-3-05]]
- **3.4 API 타입 동기화** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\unified-state-system.plan.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[phase-3-05]]

## Internal Relationships
- 3.1 타입 정의 업데이트 -> has_code_example -> typescript [EXTRACTED]
- 3.2 상태 배지 컴포넌트 업데이트 -> has_code_example -> typescript [EXTRACTED]
- 3.3 필터 UI 업데이트 -> has_code_example -> typescript [EXTRACTED]
- 3.4 API 타입 동기화 -> has_code_example -> typescript [EXTRACTED]
- **Phase 3: 프론트엔드 업데이트** (0.5일) -> contains -> 3.1 타입 정의 업데이트 [EXTRACTED]
- **Phase 3: 프론트엔드 업데이트** (0.5일) -> contains -> 3.2 상태 배지 컴포넌트 업데이트 [EXTRACTED]
- **Phase 3: 프론트엔드 업데이트** (0.5일) -> contains -> 3.3 필터 UI 업데이트 [EXTRACTED]
- **Phase 3: 프론트엔드 업데이트** (0.5일) -> contains -> 3.4 API 타입 동기화 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 typescript, **Phase 3: 프론트엔드 업데이트** (0.5일), 3.1 타입 정의 업데이트를 중심으로 has_code_example 관계로 연결되어 있다. 주요 소스 파일은 unified-state-system.plan.md이다.

### Key Facts
- 목표 - TypeScript ProposalStatus 타입 업데이트 - 컴포넌트 props 타입 수정 - 상태 필터/배지 UI 업데이트 - API 응답 타입 동기화
- 목표 - TypeScript ProposalStatus 타입 업데이트 - 컴포넌트 props 타입 수정 - 상태 필터/배지 UI 업데이트 - API 응답 타입 동기화
- **파일**: `frontend/app/types/proposal.ts` (또는 기존 types 파일)
- **파일**: `frontend/app/components/ProposalStatusBadge.tsx`
- **파일**: `frontend/app/components/ProposalListFilters.tsx`
