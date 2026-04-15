# Plan: pricing-integration (Option A — 통합) & 3. 범위
Cohesion: 0.29 | Nodes: 7

## Key Nodes
- **Plan: pricing-integration (Option A — 통합)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pricing-integration.plan.md) -- 4 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
- **3. 범위** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pricing-integration.plan.md) -- 3 connections
  - -> contains -> [[in-scope]]
  - -> contains -> [[out-of-scope]]
  - <- contains <- [[plan-pricing-integration-option-a]]
- **1. 배경** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pricing-integration.plan.md) -- 1 connections
  - <- contains <- [[plan-pricing-integration-option-a]]
- **2. 목표** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pricing-integration.plan.md) -- 1 connections
  - <- contains <- [[plan-pricing-integration-option-a]]
- **4. 수용 기준** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pricing-integration.plan.md) -- 1 connections
  - <- contains <- [[plan-pricing-integration-option-a]]
- **In-Scope** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pricing-integration.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **Out-of-Scope** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\pricing-integration.plan.md) -- 1 connections
  - <- contains <- [[3]]

## Internal Relationships
- 3. 범위 -> contains -> In-Scope [EXTRACTED]
- 3. 범위 -> contains -> Out-of-Scope [EXTRACTED]
- Plan: pricing-integration (Option A — 통합) -> contains -> 1. 배경 [EXTRACTED]
- Plan: pricing-integration (Option A — 통합) -> contains -> 2. 목표 [EXTRACTED]
- Plan: pricing-integration (Option A — 통합) -> contains -> 3. 범위 [EXTRACTED]
- Plan: pricing-integration (Option A — 통합) -> contains -> 4. 수용 기준 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: pricing-integration (Option A — 통합), 3. 범위, 1. 배경를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 pricing-integration.plan.md이다.

### Key Facts
- > 독립 가격 시뮬레이터 제거 + 워크플로 STEP 2.5에 집중 + 빠른 견적 이관
- In-Scope 1. `/pricing`, `/pricing/history` 페이지 삭제 2. 사이드바에서 "가격 시뮬레이터" 메뉴 제거 3. `PricingSimulator.tsx` 컴포넌트 삭제 4. `/proposals/new`에 빠른 견적(quickEstimate) UI 추가 5. `BidPlanReviewPanel`에 기존 시뮬레이션 불러오기 유지 (Option C에서 구현)
- `/pricing` 독립 도구와 워크플로 STEP 2.5가 동일한 하위 컴포넌트를 공유하지만, 이용자가 두 곳에서 같은 작업을 반복하게 되는 UX 문제가 있음. 검토 결과 Option A(통합) 채택.
- - `/pricing` 독립 페이지 제거 → 네비게이션 단순화 - 사전 검토 니즈 → `/proposals/new`에서 "빠른 견적" 버튼으로 이관 - 워크플로 STEP 2.5에서 기존 시뮬레이션 이력 불러오기 유지
- - [x] `/pricing` 페이지 접근 불가 (404) - [x] 사이드바에 "가격 시뮬레이터" 메뉴 없음 - [x] `/proposals/new`에서 예산 있는 공고 → "빠른 견적" 버튼 → 추천가+수주확률 표시 - [x] STEP 2.5에서 기존 시뮬레이션 불러오기 정상 동작 - [x] TypeScript 빌드 에러 0건
