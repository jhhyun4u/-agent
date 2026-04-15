# 2. 프론트엔드 & 1. 백엔드 API
Cohesion: 0.18 | Nodes: 11

## Key Nodes
- **2. 프론트엔드** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\pricing-integration.design.md) -- 4 connections
  - -> contains -> [[2-1-pricingsimulatortsx]]
  - -> contains -> [[2-2-bidplanreviewpaneltsx]]
  - -> contains -> [[2-3-apits]]
  - <- contains <- [[design-pricing-integration]]
- **1. 백엔드 API** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\pricing-integration.design.md) -- 3 connections
  - -> contains -> [[1-1-post-pricingsimulationssimulationidapplyproposalid]]
  - -> contains -> [[1-2-get-proposalsproposalidcontext]]
  - <- contains <- [[design-pricing-integration]]
- **Design: pricing-integration** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\pricing-integration.design.md) -- 3 connections
  - -> contains -> [[1-api]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
- **1-1. POST /pricing/simulations/{simulation_id}/apply/{proposal_id}** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\pricing-integration.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[1-api]]
- **2-3. api.ts 추가 메서드** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\pricing-integration.design.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[2]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\pricing-integration.design.md) -- 1 connections
  - <- has_code_example <- [[1-1-post-pricingsimulationssimulationidapplyproposalid]]
- **typescript** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\pricing-integration.design.md) -- 1 connections
  - <- has_code_example <- [[2-3-apits]]
- **1-2. GET /proposals/{proposal_id}/context (기존 활용)** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\pricing-integration.design.md) -- 1 connections
  - <- contains <- [[1-api]]
- **2-1. PricingSimulator.tsx 변경** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\pricing-integration.design.md) -- 1 connections
  - <- contains <- [[2]]
- **2-2. BidPlanReviewPanel.tsx 변경** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\pricing-integration.design.md) -- 1 connections
  - <- contains <- [[2]]
- **3. 구현 순서** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\pricing-integration.design.md) -- 1 connections
  - <- contains <- [[design-pricing-integration]]

## Internal Relationships
- 1-1. POST /pricing/simulations/{simulation_id}/apply/{proposal_id} -> has_code_example -> python [EXTRACTED]
- 1. 백엔드 API -> contains -> 1-1. POST /pricing/simulations/{simulation_id}/apply/{proposal_id} [EXTRACTED]
- 1. 백엔드 API -> contains -> 1-2. GET /proposals/{proposal_id}/context (기존 활용) [EXTRACTED]
- 2. 프론트엔드 -> contains -> 2-1. PricingSimulator.tsx 변경 [EXTRACTED]
- 2. 프론트엔드 -> contains -> 2-2. BidPlanReviewPanel.tsx 변경 [EXTRACTED]
- 2. 프론트엔드 -> contains -> 2-3. api.ts 추가 메서드 [EXTRACTED]
- 2-3. api.ts 추가 메서드 -> has_code_example -> typescript [EXTRACTED]
- Design: pricing-integration -> contains -> 1. 백엔드 API [EXTRACTED]
- Design: pricing-integration -> contains -> 2. 프론트엔드 [EXTRACTED]
- Design: pricing-integration -> contains -> 3. 구현 순서 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 2. 프론트엔드, 1. 백엔드 API, Design: pricing-integration를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 pricing-integration.design.md이다.

### Key Facts
- 2-1. PricingSimulator.tsx 변경
- 1-1. POST /pricing/simulations/{simulation_id}/apply/{proposal_id}
- > Plan: `docs/01-plan/features/pricing-integration.plan.md`
- 시뮬레이션 결과를 프로젝트 bid_plan 상태에 적용.
- ```typescript pricingApi.applyToProposal(simulationId: string, proposalId: string) → POST /pricing/simulations/{simulationId}/apply/{proposalId} ```
