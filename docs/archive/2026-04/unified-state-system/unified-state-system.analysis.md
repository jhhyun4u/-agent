# Unified State System - Gap Analysis Report

**Feature**: unified-state-system
**Phase**: Check (Gap Analysis)
**Analysis Date**: 2026-03-30
**Match Rate**: **52%** ❌ (Threshold: ≥90%)

---

## Executive Summary

The implementation demonstrates a **critical architectural divergence** from the design specification. While the implementation successfully creates database infrastructure (proposal_timelines table, timestamps) and API endpoints (GET /state-history), it uses an **incorrect ProposalStatus enum** that contradicts the core design intent.

**Root Issue**: The design specifies unification of 16 old granular statuses into 10 business-level statuses (waiting, in_progress, completed, submitted, presentation, closed, archived, on_hold, expired). The implementation instead **retains the old granular statuses** (initialized, searching, analyzing, strategizing, processing, submitted, presented, won, lost, no_go), defeating the unification goal.

---

## Score Breakdown by Phase

| Phase | Status | Coverage | Issues |
|-------|:------:|:--------:|:------:|
| **1: DB Schema** | ❌ FAIL | 40% | Missing ai_task_status table, win_result column, 4 timestamps, CHECK constraints, data migration script |
| **2: Backend Services** | ❌ FAIL | 55% | Wrong ProposalStatus enum values, missing WinResult enum, TimelineService/StateTransitionService consolidated incorrectly |
| **3: API/Schemas** | ⚠️ PARTIAL | 75% | Schemas defined and /state-history endpoint works, but EnhancedWorkflowStateResponse not wired to /state endpoint |
| **4: Tests** | ❌ FAIL | 0% | No unit or integration tests exist |
| **Overall** | ❌ FAIL | **52%** | Below 90% threshold |

---

## HIGH Severity Gaps (6 items)

### GAP-H1: ProposalStatus Enum — Architectural Misalignment ⚠️ CRITICAL

**Design Requirement**:
```python
class ProposalStatus(str, Enum):
    WAITING = "waiting"              # Not yet started
    IN_PROGRESS = "in_progress"      # Actively being worked
    COMPLETED = "completed"          # Drafting complete, awaiting decision
    SUBMITTED = "submitted"          # Submitted to client
    PRESENTATION = "presentation"    # In evaluation/presentation phase
    CLOSED = "closed"                # Closed (won/lost/abandoned)
    ARCHIVED = "archived"            # Historical record
    ON_HOLD = "on_hold"              # Paused temporarily
    EXPIRED = "expired"              # Deadline passed
```

**Implementation**:
```python
class ProposalStatus(str, Enum):
    INITIALIZED = "initialized"      # ❌ Not in design
    SEARCHING = "searching"          # ❌ Not in design
    ANALYZING = "analyzing"          # ❌ Not in design
    STRATEGIZING = "strategizing"    # ❌ Not in design
    PROCESSING = "processing"        # ❌ Not in design
    SUBMITTED = "submitted"          # ✅ Matches
    PRESENTED = "presented"          # ❌ Should be "presentation"
    WON = "won"                      # ❌ Not in design (should be win_result column)
    LOST = "lost"                    # ❌ Not in design (should be win_result column)
    NO_GO = "no_go"                  # ❌ Not in design (should be win_result column)
```

**Impact**: The entire state machine is built on wrong status values. Workflow transitions, database constraints, and API contracts will all mismatch the design.

**Recommendation**: Rewrite ProposalStatus enum to match design specification.

---

### GAP-H2: Missing ai_task_status Table (Layer 3 Separation)

**Design Requirement**:
- Create dedicated `ai_task_status` table for Layer 3 (AI Runtime State)
- Separate from proposals.status to allow independent AI task tracking
- Support states: running, complete, error, paused, no_response

**Implementation**:
- Only adds CHECK constraint to existing `ai_task_logs` table
- No dedicated Layer 3 table created
- No separation of concerns between proposal business status and AI task state

**Impact**: Cannot independently track AI task state per the 3-layer architecture design.

---

### GAP-H3: Missing Timestamp Columns (4 of 8)

**Design Requirement**: 8 timestamps
- created_at ✅
- started_at ✅
- last_activity_at ✅
- **submitted_at** ❌
- **presentation_started_at** ❌
- **closed_at** ❌
- **archived_at** ❌
- **expired_at** ❌
- completed_at ✅

**Implementation**: Only 4 of 8 timestamps added.

**Impact**: Cannot track precise state transition times for terminal states.

---

### GAP-H4: Missing win_result Column + WinResult Enum

**Design Requirement**:
```python
class WinResult(str, Enum):
    WON = "won"
    LOST = "lost"
    NO_GO = "no_go"
    ABANDONED = "abandoned"
    CANCELLED = "cancelled"
```

- proposals.win_result column (VARCHAR, nullable)
- WIN_RESULT CHECK constraint
- Used only when status = "closed"

**Implementation**: Not implemented. Win outcome tracked as status values (won, lost, no_go).

**Impact**: Cannot separate business status (closed) from win outcome (won/lost/no_go/abandoned). Conflates two concerns.

---

### GAP-H5: Missing Data Migration Script

**Design Requirement**:
- `scripts/migrate_states_018.py` to migrate 16 old statuses → 10 new ones
- Mapping logic for each old status to new status
- Data validation and rollback capability

**Implementation**: Not implemented.

**Impact**: Cannot deploy to production without data loss or inconsistency.

---

### GAP-H6: Missing Database CHECK Constraints

**Design Requirement**:
```sql
ALTER TABLE proposals ADD CONSTRAINT proposals_status_check
  CHECK (status IN ('waiting', 'in_progress', 'completed', 'submitted',
                    'presentation', 'closed', 'archived', 'on_hold', 'expired'));

ALTER TABLE proposals ADD CONSTRAINT proposals_win_result_check
  CHECK (win_result IS NULL OR win_result IN ('won', 'lost', 'no_go', 'abandoned', 'cancelled'));
```

**Implementation**: No CHECK constraints added to database.

**Impact**: Invalid status values can be inserted at database level.

---

## MEDIUM Severity Gaps (6 items)

### GAP-M1: Phase 0 Critical Bug Resolution Unclear

The original Phase 0 hotfix addressed a bug where code tried to set status="running" which violated CHECK constraints. The design unifies this, but it's unclear if this is properly resolved in the final state model.

---

### GAP-M2: TimelineService Not Implemented as Designed

**Design**: Dedicated `TimelineService` class with methods:
- `record_status_change(proposal_id, from_status, to_status, ...)`
- `record_phase_change(proposal_id, from_phase, to_phase, ...)`
- `record_review_comment(proposal_id, reviewer_id, comment, ...)`
- `get_timeline(proposal_id, limit, offset)`

**Implementation**: StateValidator.transition() handles timeline logging inline. No separate TimelineService.

**Impact**: Timeline functionality scattered across StateValidator; less maintainable.

---

### GAP-M3: StateTransitionService Architecture

**Design**: Single `StateTransitionService` class providing:
- `validate_transition(from_status, to_status)`
- `execute_transition(proposal_id, to_status, user_id, ...)`
- Centralized timestamp handling
- Event publishing

**Implementation**: Split into StateValidator + StateMachine. Missing win_result parameter, timestamp coverage limited.

---

### GAP-M4: Missing Enums

**Design**: Three enums required
- ProposalStatus ✅ (but wrong values)
- **WinResult** ❌
- **AITaskStatus** ❌

**Implementation**: Only ProposalStatus exists.

---

### GAP-M5: proposal_timelines Schema Mismatch

| Field | Design | Implementation | Status |
|-------|:------:|:---------------:|:------:|
| triggered_by | VARCHAR(50) | UUID | ❌ Type mismatch |
| triggered_by_user_id | UUID | N/A | ❌ Missing |
| event_data | JSONB | metadata (JSONB) | ⚠️ Different name |
| trigger_reason | VARCHAR | trigger_reason (TEXT) | ✅ |
| event_type | TEXT + CHECK | TEXT (no CHECK) | ⚠️ No constraint |
| notes | VARCHAR | notes (TEXT) | ✅ |

**Impact**: Column names don't match design; type differences may cause API issues.

---

### GAP-M6: Zero Test Coverage

**Design Phase 4**: 3+ unit test files + integration tests for state transitions

**Implementation**: No test files created.

**Impact**: Cannot verify state machine logic, transitions, or database constraints.

---

## LOW Severity Gaps (3 items)

### GAP-L1: EnhancedWorkflowStateResponse Not Wired to API

**Design**: GET /api/proposals/{id}/state returns EnhancedWorkflowStateResponse with all 3 layers

**Implementation**: Schema defined but commented out in routes_workflow.py. Old /state endpoint still returns legacy response.

**Impact**: 3-layer state not exposed via API.

---

### GAP-L2: Frontend Phase Not Started

Expected — not in scope for backend-only implementation.

---

### GAP-L3: PM/PL Assignment Columns Missing

**Design**: proposals.project_manager_id, proposals.project_leader_id columns

**Implementation**: Not implemented.

---

## What Works Well ✅

| Component | Status | Notes |
|-----------|:------:|:-----:|
| proposal_timelines table | ✅ | Created with 3 indexes (proposal_id, created_at DESC, event_type) |
| Timestamp columns | ✅ | 4 of 8 added (created_at, started_at, last_activity_at, completed_at) |
| StateValidator class | ✅ | Valid transition map and validation logic work |
| StateMachine methods | ✅ | Business-level convenience methods (start_workflow, decide_go, etc.) implemented |
| Pydantic schemas | ✅ | TimelineEntry, StateHistoryResponse, EnhancedWorkflowStateResponse defined |
| /state-history endpoint | ✅ | Pagination, filtering, error handling all work |
| Rollback script | ✅ | Safe migration rollback exists |
| Code quality | ✅ | ruff ✅, Python syntax ✅ |

---

## Decision Matrix

### Current Path (Implementation)
- **Pros**: Quick; some infrastructure (timeline table) in place
- **Cons**: Wrong enum values; defeats unification goal; data migration needed; HIGH priority issues

### Design-Aligned Path
- **Pros**: Achieves intended unification; cleaner architecture; win_result separation of concerns
- **Cons**: Requires significant refactoring; 4-6 HIGH severity fixes needed; data migration complex

### Recommendation

**PROCEED WITH ACT PHASE** (`/pdca iterate unified-state-system`) to fix HIGH severity gaps:

1. ✅ Rewrite ProposalStatus enum (10 unified values)
2. ✅ Add WinResult enum
3. ✅ Create ai_task_status table
4. ✅ Add missing 4 timestamps
5. ✅ Add CHECK constraints
6. ✅ Create data migration script
7. ✅ Update StateValidator/StateMachine for win_result
8. ✅ Write unit tests

**Estimated Fix Time**: 6-8 hours (Phases 1-2 refactoring + tests)

---

## Implementation Files Analyzed

- ✅ docs/01-plan/features/unified-state-system.plan.md
- ✅ docs/02-design/features/unified-state-system.design.md
- ✅ database/migrations/019_unified_state_system.sql
- ✅ database/rollback_migration_019.sql
- ✅ app/services/state_validator.py
- ✅ app/state_machine.py
- ✅ app/models/workflow_schemas.py
- ✅ app/api/routes_workflow.py (lines 392-450)

---

## Next Steps

**Immediate**: Run `/pdca iterate unified-state-system` to proceed with Act phase auto-fixes.

**Or**: Review implementation direction with stakeholders before proceeding (Design alignment vs. implementation pragmatism).

---

**Status**: READY FOR ACT PHASE
**Priority**: HIGH (Architectural mismatch requires resolution)
**Match Rate**: 52% (Below 90% threshold)
