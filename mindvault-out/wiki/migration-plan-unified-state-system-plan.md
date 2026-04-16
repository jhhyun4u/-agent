# Migration Plan & Unified State System Plan
Cohesion: 0.13 | Nodes: 19

## Key Nodes
- **Migration Plan** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 6 connections
  - -> contains -> [[phase-0-critical-bug-fix-completed]]
  - -> contains -> [[phase-1-database-schema-migration-pending]]
  - -> contains -> [[phase-2-backend-code-refactoring-pending]]
  - -> contains -> [[phase-3-api-and-service-updates-pending]]
  - -> contains -> [[phase-4-testing-and-deployment-pending]]
  - <- contains <- [[unified-state-system-plan]]
- **Unified State System Plan** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 6 connections
  - -> contains -> [[overview]]
  - -> contains -> [[problem-statement]]
  - -> contains -> [[solution-3-layer-architecture]]
  - -> contains -> [[migration-plan]]
  - -> contains -> [[current-status]]
  - -> contains -> [[references]]
- **Changes:** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 5 connections
  - <- contains <- [[phase-0-critical-bug-fix-completed]]
  - <- contains <- [[phase-1-database-schema-migration-pending]]
  - <- contains <- [[phase-2-backend-code-refactoring-pending]]
  - <- contains <- [[phase-3-api-and-service-updates-pending]]
  - <- contains <- [[phase-4-testing-and-deployment-pending]]
- **Phase 0: CRITICAL BUG FIX (COMPLETED ✅)** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 4 connections
  - -> contains -> [[changes]]
  - -> contains -> [[files-modified]]
  - -> contains -> [[verification]]
  - <- contains <- [[migration-plan]]
- **Solution: 3-Layer Architecture** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 4 connections
  - -> contains -> [[layer-1-business-status-proposalsstatus]]
  - -> contains -> [[layer-2-workflow-phase-proposalscurrentphase]]
  - -> contains -> [[layer-3-ai-runtime-state-aitasklogsstatus]]
  - <- contains <- [[unified-state-system-plan]]
- **Phase 1: Database Schema Migration (PENDING)** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 2 connections
  - -> contains -> [[changes]]
  - <- contains <- [[migration-plan]]
- **Phase 2: Backend Code Refactoring (PENDING)** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 2 connections
  - -> contains -> [[changes]]
  - <- contains <- [[migration-plan]]
- **Phase 3: API and Service Updates (PENDING)** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 2 connections
  - -> contains -> [[changes]]
  - <- contains <- [[migration-plan]]
- **Phase 4: Testing and Deployment (PENDING)** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 2 connections
  - -> contains -> [[changes]]
  - <- contains <- [[migration-plan]]
- **Problem Statement** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 2 connections
  - -> contains -> [[current-issues]]
  - <- contains <- [[unified-state-system-plan]]
- **Current Issues** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 1 connections
  - <- contains <- [[problem-statement]]
- **Current Status** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 1 connections
  - <- contains <- [[unified-state-system-plan]]
- **Files Modified:** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 1 connections
  - <- contains <- [[phase-0-critical-bug-fix-completed]]
- **Layer 1: Business Status (proposals.status)** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 1 connections
  - <- contains <- [[solution-3-layer-architecture]]
- **Layer 2: Workflow Phase (proposals.current_phase)** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 1 connections
  - <- contains <- [[solution-3-layer-architecture]]
- **Layer 3: AI Runtime State (ai_task_logs.status)** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 1 connections
  - <- contains <- [[solution-3-layer-architecture]]
- **Overview** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 1 connections
  - <- contains <- [[unified-state-system-plan]]
- **References** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 1 connections
  - <- contains <- [[unified-state-system-plan]]
- **Verification:** (C:\project\tenopa proposer\docs\archive\2026-04\unified-state-system\unified-state-system.plan.md) -- 1 connections
  - <- contains <- [[phase-0-critical-bug-fix-completed]]

## Internal Relationships
- Migration Plan -> contains -> Phase 0: CRITICAL BUG FIX (COMPLETED ✅) [EXTRACTED]
- Migration Plan -> contains -> Phase 1: Database Schema Migration (PENDING) [EXTRACTED]
- Migration Plan -> contains -> Phase 2: Backend Code Refactoring (PENDING) [EXTRACTED]
- Migration Plan -> contains -> Phase 3: API and Service Updates (PENDING) [EXTRACTED]
- Migration Plan -> contains -> Phase 4: Testing and Deployment (PENDING) [EXTRACTED]
- Phase 0: CRITICAL BUG FIX (COMPLETED ✅) -> contains -> Changes: [EXTRACTED]
- Phase 0: CRITICAL BUG FIX (COMPLETED ✅) -> contains -> Files Modified: [EXTRACTED]
- Phase 0: CRITICAL BUG FIX (COMPLETED ✅) -> contains -> Verification: [EXTRACTED]
- Phase 1: Database Schema Migration (PENDING) -> contains -> Changes: [EXTRACTED]
- Phase 2: Backend Code Refactoring (PENDING) -> contains -> Changes: [EXTRACTED]
- Phase 3: API and Service Updates (PENDING) -> contains -> Changes: [EXTRACTED]
- Phase 4: Testing and Deployment (PENDING) -> contains -> Changes: [EXTRACTED]
- Problem Statement -> contains -> Current Issues [EXTRACTED]
- Solution: 3-Layer Architecture -> contains -> Layer 1: Business Status (proposals.status) [EXTRACTED]
- Solution: 3-Layer Architecture -> contains -> Layer 2: Workflow Phase (proposals.current_phase) [EXTRACTED]
- Solution: 3-Layer Architecture -> contains -> Layer 3: AI Runtime State (ai_task_logs.status) [EXTRACTED]
- Unified State System Plan -> contains -> Overview [EXTRACTED]
- Unified State System Plan -> contains -> Problem Statement [EXTRACTED]
- Unified State System Plan -> contains -> Solution: 3-Layer Architecture [EXTRACTED]
- Unified State System Plan -> contains -> Migration Plan [EXTRACTED]
- Unified State System Plan -> contains -> Current Status [EXTRACTED]
- Unified State System Plan -> contains -> References [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Migration Plan, Unified State System Plan, Changes:를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 unified-state-system.plan.md이다.

### Key Facts
- Phase 0: CRITICAL BUG FIX (COMPLETED ✅) **Priority**: 1 Day **Impact**: Prevents 500 errors in production workflow endpoints
- Overview Migration from 16 scattered proposal states to 10 business-oriented states with a 3-layer architecture. This addresses critical database constraint violations and provides a clearer, more maintainable state model for the proposal workflow.
- Files Modified: - `app/api/routes_workflow.py` (2 edits) - `app/api/routes_proposal.py` (1 edit)
- Changes: 1. ✅ `routes_workflow.py` line 153: `"running"` → `"processing"` 2. ✅ `routes_workflow.py` line 148: Check for active states tuple instead of exact `"running"` 3. ✅ `routes_workflow.py` line 298: `"cancelled"` → `"abandoned"` 4. ✅ `routes_proposal.py` line 378: Check for active states…
- Layer 1: Business Status (proposals.status) Tracks the actual business outcome/decision point.
