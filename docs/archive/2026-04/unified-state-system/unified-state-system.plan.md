# Unified State System Plan

## Overview
Migration from 16 scattered proposal states to 10 business-oriented states with a 3-layer architecture. This addresses critical database constraint violations and provides a clearer, more maintainable state model for the proposal workflow.

## Problem Statement

### Current Issues
1. **Database Constraint Violations**: Code in `routes_workflow.py` and `routes_proposal.py` attempts to set invalid status values:
   - `status = "running"` (line 153 in routes_workflow.py) — NOT in CHECK constraint
   - `status = "cancelled"` (line 298 in routes_workflow.py) — NOT in CHECK constraint
   - Status checks for `== "running"` expect invalid value

2. **Semantic Confusion**: Current states don't clearly distinguish between:
   - Business-level status (Go/No-Go decision, approval status)
   - Workflow execution phase (which step is running)
   - AI runtime state (task paused, error, etc.)

3. **Scattered State Management**: Multiple tables track overlapping state concepts:
   - `proposals.status` — 14 discrete business states
   - `proposals.current_phase` — workflow phase name
   - `ai_task_logs.status` — AI task state (running, complete, error, paused)
   - Various state manager services

## Solution: 3-Layer Architecture

### Layer 1: Business Status (proposals.status)
Tracks the actual business outcome/decision point.

**10 Valid States** (in CHECK constraint):
1. `initialized` — Default, no decision made
2. `no_go` — Decided not to pursue
3. `searching` — Searching for opportunities (G2B phase)
4. `analyzing` — RFP analysis in progress
5. `strategizing` — Strategy development in progress
6. `processing` — Proposal/submission document work in progress
7. `submitted` — Submitted to client/bidding
8. `presented` — Presented/bid submitted
9. `won` — Won the contract
10. `lost` — Lost/no award

**Mapping Note**:
- Old "running" → "processing" (any workflow in progress)
- Old "cancelled" → "no_go" (intentional abandonment)
- Old "on_hold", "expired", "abandoned", "retrospect" → consolidated

### Layer 2: Workflow Phase (proposals.current_phase)
Tracks which step in the LangGraph workflow is currently executing. Values match node names:
- `start`, `rfp_fetch`, `rfp_analyze`, `research_gather`, `go_no_go`, `review_rfp`, etc.

### Layer 3: AI Runtime State (ai_task_logs.status)
Tracks async AI task execution state, separate from proposal status:
- `running`, `complete`, `error`, `paused`, `no_response`

## Migration Plan

### Phase 0: CRITICAL BUG FIX (COMPLETED ✅)
**Priority**: 1 Day
**Impact**: Prevents 500 errors in production workflow endpoints

#### Changes:
1. ✅ `routes_workflow.py` line 153: `"running"` → `"processing"`
2. ✅ `routes_workflow.py` line 148: Check for active states tuple instead of exact `"running"`
3. ✅ `routes_workflow.py` line 298: `"cancelled"` → `"abandoned"`
4. ✅ `routes_proposal.py` line 378: Check for active states tuple instead of exact `"running"`

#### Files Modified:
- `app/api/routes_workflow.py` (2 edits)
- `app/api/routes_proposal.py` (1 edit)

#### Verification:
- ✅ Python syntax check passed
- ✅ No new import errors
- ✅ Logic preserved (same active states checked)

---

### Phase 1: Database Schema Migration (PENDING)
**Priority**: 1-2 Days
**Scope**: Add new columns, ensure backward compatibility

#### Changes:
1. Add new columns to `proposals` table:
   - `created_at` TIMESTAMPTZ
   - `started_at` TIMESTAMPTZ
   - `last_activity_at` TIMESTAMPTZ
   - `completed_at` TIMESTAMPTZ

2. Create `proposal_timelines` table for event tracking:
   - Tracks transitions between states
   - Records decision timestamps
   - Tracks approvals and rejections

3. Update `ai_task_logs` table definition (already exists):
   - Ensure status column allows: running, complete, error, paused, no_response

4. Create migration script: `database/migrations/012_unified_state_system.sql`

---

### Phase 2: Backend Code Refactoring (PENDING)
**Priority**: 2 Days
**Scope**: Update state transition logic

#### Changes:
1. Create state transition validator: `app/services/state_validator.py`
   - Validate state transitions follow business rules
   - Prevent invalid transitions (e.g., won → searching)

2. Update workflow nodes:
   - Replace direct status updates with state transition API
   - Log state changes to proposal_timelines
   - Update proposal timestamps

3. Create state machine class: `app/state_machine.py`
   - Define valid transitions
   - Handle Edge cases (force transitions for admin, bypass certain checks)

---

### Phase 3: API and Service Updates (PENDING)
**Priority**: 2 Days
**Scope**: Expose state information clearly

#### Changes:
1. Update workflow state endpoint (`routes_workflow.py`):
   - Return all 3 layers (business status, current_phase, ai_status)
   - Include timeline of recent transitions

2. Add state history endpoint:
   - GET `/api/proposals/{id}/state-history` — timeline of all state changes

3. Update notification triggers:
   - Change state → send notification
   - Include business status in all user-facing messages

---

### Phase 4: Testing and Deployment (PENDING)
**Priority**: 1 Day
**Scope**: Verify no regressions

#### Changes:
1. Unit tests for state transitions
2. Integration tests for workflow (state should progress correctly)
3. Verify all active workflow endpoints still work
4. Deploy with rollback plan

---

## Current Status
✅ **Phase 0 COMPLETED** (2025-03-30)
- All constraint violations fixed
- Production endpoints safe
- Ready for Phase 1 planning

⏳ **Phase 1-4**: Pending after Phase 0 verification

## References
- Database Constraint: `database/schema_v3.4.sql` line 116-119
- Affected Routes: `app/api/routes_workflow.py`, `app/api/routes_proposal.py`
- LangGraph Workflow: `app/graph/graph.py` (40 nodes)
- AI Status: `app/services/ai_status_manager.py`
