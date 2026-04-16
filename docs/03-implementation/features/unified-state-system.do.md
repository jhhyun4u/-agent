# Unified State System - Do Phase (Implementation Guide)

## Overview
Implementation of unified state system in 4 sequential phases. This guide covers Phase 1 (Database Schema Migration) with references to Phases 2-4.

**Design Reference**: `docs/02-design/features/unified-state-system.design.md`

---

## Phase 1: Database Schema Migration (1-2 Days)

### 1.1 Create Migration SQL File

**File**: `database/migrations/012_unified_state_system.sql`

**Steps**:
1. Create new file in `database/migrations/`
2. Copy migration script from design document (section Phase 1)
3. Include rollback instructions in comments
4. Test migration on local database before deployment

**Checklist**:
- [ ] File created at `database/migrations/012_unified_state_system.sql`
- [ ] Contains timestamp column additions (created_at, started_at, last_activity_at, completed_at)
- [ ] Contains proposal_timelines table creation with indexes
- [ ] Contains ai_task_logs constraint verification
- [ ] Contains data migration for existing proposals
- [ ] Contains rollback comments
- [ ] Syntax validated (no SQL errors)

**Verification Command**:
```bash
# Run migration on local test database
psql -d tenopa_test -f database/migrations/012_unified_state_system.sql

# Verify tables exist
psql -d tenopa_test -c "
  SELECT table_name
  FROM information_schema.tables
  WHERE table_schema = 'public'
  AND table_name IN ('proposals', 'proposal_timelines', 'ai_task_logs');
"

# Verify columns exist
psql -d tenopa_test -c "
  SELECT column_name, data_type
  FROM information_schema.columns
  WHERE table_name = 'proposals'
  AND column_name IN ('created_at', 'started_at', 'last_activity_at', 'completed_at');
"
```

### 1.2 Create Rollback Script

**File**: `database/rollback_migration_012.sql`

**Content**:
```sql
-- ============================================
-- Rollback for Migration 012: Unified State System
-- ============================================

-- Drop new table
DROP TABLE IF EXISTS proposal_timelines CASCADE;

-- Remove timestamp columns
ALTER TABLE proposals
  DROP COLUMN IF EXISTS created_at,
  DROP COLUMN IF EXISTS started_at,
  DROP COLUMN IF EXISTS last_activity_at,
  DROP COLUMN IF EXISTS completed_at;

-- Remove ai_task_logs constraint if needed
ALTER TABLE ai_task_logs
  DROP CONSTRAINT IF EXISTS ai_task_logs_status_check;
```

**Checklist**:
- [ ] Rollback script created
- [ ] Tested on copy of production database
- [ ] Verified all changes are reversible
- [ ] Stored alongside migration (same directory)

### 1.3 Deploy Migration

**Before Deployment**:
1. Back up production database
2. Test migration on staging environment
3. Get approval from database administrator

**Deployment Steps**:
```bash
# 1. SSH to production server
ssh user@production-server

# 2. Navigate to project
cd /app/tenopa-proposer

# 3. Create backup
pg_dump -h localhost -U postgres -d tenopa > /backups/tenopa_$(date +%Y%m%d_%H%M%S).sql

# 4. Run migration
psql -h localhost -U postgres -d tenopa -f database/migrations/012_unified_state_system.sql

# 5. Verify success
psql -h localhost -U postgres -d tenopa -c "SELECT COUNT(*) FROM proposal_timelines;"

# 6. Commit migration record
psql -h localhost -U postgres -d tenopa -c "
  INSERT INTO schema_migrations (version, description, status)
  VALUES ('012', 'unified-state-system', 'success');
"
```

**Checklist**:
- [ ] Database backup created
- [ ] Migration run on production
- [ ] Tables and columns verified to exist
- [ ] No errors in migration log
- [ ] Existing data preserved (spot-check 5-10 proposals)

---

## Phase 2: Backend Code Refactoring (2 Days) — PENDING

### 2.1 Create State Validator Service

**File**: `app/services/state_validator.py`

Copy implementation from design document (section 2.1). This service:
- Defines valid proposal statuses (Enum)
- Validates state transitions
- Executes transitions with timeline logging

**Checklist**:
- [ ] File created with ProposalStatus enum
- [ ] VALID_TRANSITIONS dictionary defined
- [ ] validate_transition() method implemented
- [ ] transition() method implemented with timeline logging
- [ ] Docstrings added
- [ ] No linting errors (ruff check)
- [ ] Type hints correct (mypy check)

**Tests**:
```bash
cd /project/tenopa-proposer
uv run pytest tests/services/test_state_validator.py -v
```

### 2.2 Create State Machine Class

**File**: `app/state_machine.py`

Copy implementation from design document (section 2.2). This class:
- Wraps StateValidator
- Provides business-friendly methods (start_workflow, decide_go, decide_no_go, submit_proposal, etc.)

**Checklist**:
- [ ] File created with StateMachine class
- [ ] All business methods implemented (start_workflow, decide_*, submit_*, etc.)
- [ ] Docstrings added
- [ ] No linting errors (ruff check)
- [ ] Type hints correct (mypy check)

### 2.3 Update Workflow Nodes

**Files to Update**:
1. `app/graph/nodes/gate_nodes.py`
2. `app/graph/nodes/go_no_go.py`
3. `app/graph/nodes/review_node.py`
4. Any other node that calls `client.table("proposals").update({"status": ...})`

**Pattern**:

**Before**:
```python
await client.table("proposals").update({
    "status": "processing",
    "current_phase": "strategy_generate"
}).eq("id", proposal_id).execute()
```

**After**:
```python
from app.state_machine import StateMachine
from app.services.state_validator import ProposalStatus

sm = StateMachine(proposal_id)
await sm.transition(
    ProposalStatus.STRATEGIZING,
    current_phase="strategy_generate",
    user_id=state.get("user_id"),
    actor_type="workflow",
    reason="Transitioned to strategy generation phase"
)
```

**Grep Command to Find All Occurrences**:
```bash
cd /project/tenopa-proposer
grep -r 'table("proposals").update.*status' app/graph/ app/api/
```

**Checklist**:
- [ ] All direct status update calls found (grep search)
- [ ] All converted to state_machine.transition()
- [ ] All workflow nodes tested individually
- [ ] Full workflow tested end-to-end
- [ ] No regressions (existing tests pass)

---

## Phase 3: API and Service Updates (2 Days) — PENDING

### 3.1 Enhance Workflow State Endpoint

**File**: `app/api/routes_workflow.py`

**Update**: GET `/api/proposals/{id}/state` endpoint

**Changes**:
1. Import StateValidator, StateMachine
2. Modify response to include all 3 layers:
   - business_status (from proposals.status)
   - workflow_phase (from proposals.current_phase)
   - ai_status (from ai_task_logs)
   - timestamps (created_at, started_at, last_activity_at, completed_at)
   - recent_transitions (from proposal_timelines)

**Checklist**:
- [ ] Endpoint returns business_status
- [ ] Endpoint returns workflow_phase
- [ ] Endpoint returns ai_status (latest task)
- [ ] Endpoint returns all 4 timestamps
- [ ] Endpoint returns 5 most recent transitions
- [ ] Pydantic response model created
- [ ] Tests updated to verify new fields

### 3.2 Add State History Endpoint

**File**: `app/api/routes_workflow.py`

**New Endpoint**: GET `/api/proposals/{id}/state-history`

**Parameters**:
- `limit` (default: 50)
- `offset` (default: 0)
- `event_type` (optional filter)

**Response**: Timeline entries from proposal_timelines table

**Checklist**:
- [ ] Endpoint created
- [ ] Pagination implemented (limit/offset)
- [ ] Filtering by event_type implemented
- [ ] Pydantic response model created
- [ ] Tests added

### 3.3 Update Notification Service

**File**: `app/services/notification_service.py`

**Changes**:
- Subscribe to proposal status changes
- Send notifications on terminal state changes (won, lost, no_go)
- Include full state information in notifications

**Checklist**:
- [ ] Notification trigger added for status changes
- [ ] Terminal state notifications implemented
- [ ] Teams card content includes business_status
- [ ] In-app notifications updated

---

## Phase 4: Testing and Deployment (1 Day) — PENDING

### 4.1 Unit Tests

**File**: `tests/services/test_state_validator.py`

Copy test structure from design document (section 4.1).

**Test Cases**:
- Valid transitions pass
- Invalid transitions raise ValueError
- Timeline entries created on transition
- started_at set on first transition
- completed_at set on terminal states
- All state enums are valid

**Run Tests**:
```bash
cd /project/tenopa-proposer
uv run pytest tests/services/test_state_validator.py -v
uv run pytest tests/services/test_state_machine.py -v
```

**Checklist**:
- [ ] All tests pass
- [ ] Coverage > 90%
- [ ] Edge cases covered

### 4.2 Integration Tests

**File**: `tests/api/test_workflow_state.py`

Copy test structure from design document (section 4.2).

**Test Cases**:
- GET /state returns all 3 layers
- GET /state-history pagination works
- Workflow progression through states
- Each state change is logged in timeline
- Terminal states set completed_at

**Run Tests**:
```bash
cd /project/tenopa-proposer
uv run pytest tests/api/test_workflow_state.py -v
```

**Checklist**:
- [ ] All tests pass
- [ ] No regressions in existing endpoints
- [ ] Full workflow tested

### 4.3 Pre-Deployment Verification

**Checklist**:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Code passes ruff (style)
- [ ] Code passes mypy (types)
- [ ] Database migration tested on staging
- [ ] Rollback script tested
- [ ] Production backup procedure documented

**Commands**:
```bash
cd /project/tenopa-proposer

# Style check
uv run ruff check app/

# Type check
uv run mypy app/ --no-error-summary

# All tests
uv run pytest tests/ -v

# Test migration
psql -d tenopa_test -f database/migrations/012_unified_state_system.sql
```

---

## Implementation Order

### Week 1: Phase 1 (Database)
- **Mon-Tue**: Create migration script, test locally
- **Wed**: Deploy to staging
- **Thu**: Deploy to production (with backup)
- **Fri**: Verify, monitor logs

### Week 2: Phase 2 (Backend Services)
- **Mon-Tue**: Create StateValidator and StateMachine
- **Wed-Thu**: Update all workflow nodes
- **Fri**: Full workflow testing

### Week 3: Phase 3 (API)
- **Mon-Tue**: Enhance /state endpoint, add /state-history
- **Wed**: Update notification service
- **Thu-Fri**: Integration testing

### Week 4: Phase 4 (Testing & Deployment)
- **Mon-Tue**: Unit and integration tests
- **Wed-Thu**: Performance testing, documentation
- **Fri**: Production rollout

---

## Key Files Summary

### Files to Create
```
database/migrations/012_unified_state_system.sql
database/rollback_migration_012.sql
app/services/state_validator.py
app/state_machine.py
tests/services/test_state_validator.py
tests/services/test_state_machine.py
tests/api/test_workflow_state.py
```

### Files to Modify
```
app/api/routes_workflow.py               (enhance /state, add /state-history)
app/graph/nodes/gate_nodes.py            (use state_machine for transitions)
app/graph/nodes/go_no_go.py              (use state_machine for decisions)
app/graph/nodes/review_node.py           (use state_machine for reviews)
app/services/notification_service.py     (subscribe to status changes)
tests/api/test_workflow.py               (add state-related tests)
```

### No Changes Needed
```
app/graph/state.py                       (state structure unchanged)
app/graph/graph.py                       (graph structure unchanged)
app/config.py                            (config unchanged)
```

---

## Dependencies

### New Packages
None — uses existing `supabase-py`, `pydantic`, `typing`

### Existing Packages
- `fastapi` — API routes
- `pydantic` — Data validation
- `supabase` — Database access
- `pytest` — Testing

---

## Success Criteria per Phase

### Phase 1 ✅ (After Completion)
- [ ] proposal_timelines table exists with correct indexes
- [ ] Timestamp columns added to proposals
- [ ] Migration runs without errors
- [ ] Rollback script tested and verified
- [ ] Data integrity check: no lost proposals or timestamps

### Phase 2 ✅ (After Completion)
- [ ] StateValidator and StateMachine classes created
- [ ] All workflow nodes use state_machine for transitions
- [ ] No direct `proposals.update(status=...)` calls remain
- [ ] All existing workflow tests pass
- [ ] New unit tests added and passing

### Phase 3 ✅ (After Completion)
- [ ] GET /state returns all 3 layers correctly
- [ ] GET /state-history returns paginated timeline
- [ ] Notifications trigger on status changes
- [ ] API response includes recent transitions
- [ ] All new API tests passing

### Phase 4 ✅ (After Completion)
- [ ] Unit test coverage > 90%
- [ ] Integration tests covering all state transitions
- [ ] Full regression testing passed
- [ ] Production deployment completed safely
- [ ] Monitoring confirms no errors

---

## Rollback Procedure (If Issues Found)

**Database Rollback** (Phase 1):
```bash
psql -h localhost -U postgres -d tenopa -f database/rollback_migration_012.sql
```

**Code Rollback** (Phases 2-4):
```bash
git revert <commit-hash-of-last-phase>
```

**Monitoring After Rollback**:
- Verify workflow endpoints still work
- Check proposal creation/deletion still functional
- Monitor error logs for any constraint violations

---

## Testing Commands Reference

```bash
# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/services/test_state_validator.py -v

# Run with coverage
uv run pytest tests/ --cov=app --cov-report=html

# Style check
uv run ruff check app/

# Type check
uv run mypy app/ --no-error-summary

# Lint and auto-fix
uv run ruff check app/ --fix

# Database migration test
psql -d tenopa_test -f database/migrations/012_unified_state_system.sql
```

---

## Estimated Effort

| Phase | Duration | Effort | Risk |
|-------|----------|--------|------|
| 1 (Database) | 1-2 days | 8h | Low |
| 2 (Backend) | 2 days | 16h | Medium |
| 3 (API) | 2 days | 14h | Low |
| 4 (Testing) | 1 day | 8h | Low |
| **Total** | **6-7 days** | **46h** | **Medium** |

---

## Communication Checklist

- [ ] Database admin notified of migration
- [ ] Team informed of upcoming changes
- [ ] Rollback procedure documented and shared
- [ ] Monitoring alerts configured
- [ ] Deployment window scheduled
- [ ] Support team briefed on new state structure

---

## Next Steps After Phase 1

1. ✅ Complete Phase 1 (database migration)
2. Monitor for any database issues (24 hours)
3. Begin Phase 2 (backend refactoring)
4. Coordinate with team on Phase 2 timeline
5. Plan Phase 3 API launch (with feature flag if needed)

