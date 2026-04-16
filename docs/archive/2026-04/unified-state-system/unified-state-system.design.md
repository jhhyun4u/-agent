# Unified State System Design (Phases 1-4)

## Architecture Overview

### Current State (Phase 0 Hotfix Complete)
- ✅ Database constraint violations fixed
- ✅ Code uses valid status values: "processing" and "abandoned"
- ⏳ Still need full migration to 3-layer architecture

### Target State (After Phase 4)
Three-layer state system replacing scattered state concepts:

```
Layer 1: proposals.status (Business Decision)
├─ initialized → searching → analyzing → strategizing → processing
├─ submitted → presented → won/lost
└─ no_go (abandoned)

Layer 2: proposals.current_phase (Workflow Execution)
├─ start, rfp_fetch, rfp_analyze, research_gather, go_no_go
├─ review_rfp, strategy_generate, plan_*, proposal_*, ppt_*
└─ submission_*, bid_plan, evaluation_nodes, etc.

Layer 3: ai_task_logs.status (AI Runtime State)
├─ running, complete, error, paused, no_response
└─ Per-task tracking (independent of proposal.status)
```

---

## Phase 1: Database Schema Migration (1-2 Days)

### 1.1 Timestamp Columns (proposals table)

**New Columns**:
```sql
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS (
    created_at          TIMESTAMPTZ DEFAULT now(),
    started_at          TIMESTAMPTZ,
    last_activity_at    TIMESTAMPTZ DEFAULT now(),
    completed_at        TIMESTAMPTZ
);
```

**Purpose**:
- `created_at`: When proposal was first initialized
- `started_at`: When workflow actually started (after initialization)
- `last_activity_at`: Updated on every state transition (for sorting/filtering)
- `completed_at`: When proposal reached terminal state (won/lost/no_go)

**Triggers** (automatic updates):
- Update `last_activity_at` on every proposals.update
- Set `started_at` when status first transitions from "initialized"
- Set `completed_at` when status reaches terminal state

### 1.2 Proposal Timeline Table

**New Table**: `proposal_timelines`

```sql
CREATE TABLE proposal_timelines (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id         UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,

    -- State Transition
    event_type          TEXT NOT NULL,  -- 'status_change', 'phase_change', 'approval', 'review'
    from_status         TEXT,           -- NULL for first entry
    to_status           TEXT,           -- Current status (null if not status event)
    from_phase          TEXT,           -- NULL for first entry
    to_phase            TEXT,           -- Current phase (null if not phase event)

    -- Actor & Comment
    triggered_by        UUID REFERENCES auth.users(id),  -- User who triggered
    actor_type          TEXT,           -- 'user', 'system', 'ai', 'workflow'
    trigger_reason      TEXT,           -- Why the transition happened
    notes               TEXT,           -- Comments/feedback

    -- Metadata
    metadata            JSONB,          -- Extra data (decision_comment, approver_role, etc.)
    created_at          TIMESTAMPTZ DEFAULT now(),

    -- Indexes
    INDEX idx_proposal_timelines_proposal_id (proposal_id),
    INDEX idx_proposal_timelines_created_at (created_at DESC),
    INDEX idx_proposal_timelines_event_type (event_type)
);
```

**Event Types**:
- `status_change`: proposals.status updated (e.g., initialized → processing)
- `phase_change`: proposals.current_phase updated (e.g., rfp_analyze → research_gather)
- `approval`: Approver decision (Go/No-Go)
- `review`: Human review checkpoint completed
- `ai_status`: AI task state change (paused, error, retry)

**Examples**:

Entry 1: Proposal created
```json
{
  "event_type": "status_change",
  "from_status": null,
  "to_status": "initialized",
  "triggered_by": "user_123",
  "actor_type": "user",
  "trigger_reason": "New proposal from G2B search",
  "metadata": { "bid_no": "2026-1234", "source": "g2b" }
}
```

Entry 2: Workflow started
```json
{
  "event_type": "status_change",
  "from_status": "initialized",
  "to_status": "analyzing",
  "from_phase": "start",
  "to_phase": "rfp_analyze",
  "triggered_by": "user_123",
  "actor_type": "workflow",
  "trigger_reason": "User clicked 'Start Proposal'",
  "metadata": { "workflow_run_id": "abc123" }
}
```

Entry 3: Go/No-Go Decision
```json
{
  "event_type": "approval",
  "to_status": "strategizing",
  "from_phase": "go_no_go",
  "to_phase": "strategy_generate",
  "triggered_by": "user_123",
  "actor_type": "user",
  "trigger_reason": "Go decision",
  "notes": "Strong market fit, high win probability",
  "metadata": {
    "decision": "go",
    "approver_role": "lead",
    "approval_type": "go_no_go"
  }
}
```

### 1.3 AI Task Status Enhancement

**Verify ai_task_logs Table**:
```sql
-- Already exists in schema_v3.4.sql, verify status values:
-- status IN ('running', 'complete', 'error', 'paused', 'no_response')

-- Add CHECK constraint if missing:
ALTER TABLE ai_task_logs
ADD CONSTRAINT ai_task_logs_status_check
CHECK (status IN ('running', 'complete', 'error', 'paused', 'no_response'));
```

**Relationship**: Each row in ai_task_logs represents an async AI task independent of proposal.status. The proposal.status remains "processing" while multiple ai_task_logs entries track individual AI operations.

### 1.4 Migration Script

**File**: `database/migrations/012_unified_state_system.sql`

```sql
-- ============================================
-- Migration 012: Unified State System
-- Adds timestamp tracking and proposal timeline
-- ============================================

-- Phase 1a: Add timestamp columns
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS started_at TIMESTAMPTZ;
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMPTZ DEFAULT now();
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS completed_at TIMESTAMPTZ;

-- Phase 1b: Create proposal_timelines table
CREATE TABLE IF NOT EXISTS proposal_timelines (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id         UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    event_type          TEXT NOT NULL,
    from_status         TEXT,
    to_status           TEXT,
    from_phase          TEXT,
    to_phase            TEXT,
    triggered_by        UUID REFERENCES auth.users(id),
    actor_type          TEXT,
    trigger_reason      TEXT,
    notes               TEXT,
    metadata            JSONB,
    created_at          TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_proposal_timelines_proposal_id ON proposal_timelines(proposal_id);
CREATE INDEX idx_proposal_timelines_created_at ON proposal_timelines(created_at DESC);
CREATE INDEX idx_proposal_timelines_event_type ON proposal_timelines(event_type);

-- Phase 1c: Migrate existing proposals to populate created_at
UPDATE proposals SET created_at = COALESCE(created_at, now()) WHERE created_at IS NULL;

-- Phase 1d: Log initial state for all existing proposals
INSERT INTO proposal_timelines (proposal_id, event_type, to_status, to_phase, actor_type, created_at)
SELECT id, 'status_change', status, current_phase, 'system', now()
FROM proposals
ON CONFLICT DO NOTHING;

-- Phase 1e: Verify ai_task_logs has proper constraint
ALTER TABLE ai_task_logs ADD CONSTRAINT ai_task_logs_status_check
CHECK (status IN ('running', 'complete', 'error', 'paused', 'no_response'));
```

**Rollback Plan**:
```sql
DROP TABLE IF EXISTS proposal_timelines;
ALTER TABLE proposals DROP COLUMN IF EXISTS created_at, started_at, last_activity_at, completed_at;
```

---

## Phase 2: Backend Code Refactoring (2 Days)

### 2.1 State Transition Validator

**New File**: `app/services/state_validator.py`

```python
from typing import Optional
from enum import Enum
from datetime import datetime
from app.utils.supabase_client import get_async_client

class ProposalStatus(str, Enum):
    """Valid proposal business statuses"""
    INITIALIZED = "initialized"
    SEARCHING = "searching"
    ANALYZING = "analyzing"
    STRATEGIZING = "strategizing"
    PROCESSING = "processing"
    SUBMITTED = "submitted"
    PRESENTED = "presented"
    WON = "won"
    LOST = "lost"
    NO_GO = "no_go"

class StateValidator:
    """Validates and executes state transitions"""

    # Valid transitions: from_state → [to_states]
    VALID_TRANSITIONS = {
        ProposalStatus.INITIALIZED: [ProposalStatus.SEARCHING, ProposalStatus.ANALYZING, ProposalStatus.NO_GO],
        ProposalStatus.SEARCHING: [ProposalStatus.ANALYZING, ProposalStatus.NO_GO],
        ProposalStatus.ANALYZING: [ProposalStatus.STRATEGIZING, ProposalStatus.NO_GO],
        ProposalStatus.STRATEGIZING: [ProposalStatus.PROCESSING, ProposalStatus.NO_GO],
        ProposalStatus.PROCESSING: [ProposalStatus.SUBMITTED, ProposalStatus.NO_GO],
        ProposalStatus.SUBMITTED: [ProposalStatus.PRESENTED],
        ProposalStatus.PRESENTED: [ProposalStatus.WON, ProposalStatus.LOST],
        ProposalStatus.WON: [],           # Terminal
        ProposalStatus.LOST: [],          # Terminal
        ProposalStatus.NO_GO: [],         # Terminal
    }

    @staticmethod
    async def validate_transition(
        proposal_id: str,
        from_status: ProposalStatus,
        to_status: ProposalStatus,
        actor_type: str = "workflow",  # 'user', 'workflow', 'system'
        reason: Optional[str] = None
    ) -> bool:
        """Validate if transition is allowed"""
        if from_status not in StateValidator.VALID_TRANSITIONS:
            raise ValueError(f"Unknown status: {from_status}")

        allowed = StateValidator.VALID_TRANSITIONS[from_status]
        if to_status not in allowed:
            raise ValueError(
                f"Invalid transition: {from_status} → {to_status}. "
                f"Allowed: {allowed}"
            )
        return True

    @staticmethod
    async def transition(
        proposal_id: str,
        to_status: ProposalStatus,
        current_phase: Optional[str] = None,
        user_id: Optional[str] = None,
        actor_type: str = "workflow",
        reason: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Execute state transition with timeline logging"""
        client = await get_async_client()

        # Get current status
        prop = await client.table("proposals").select("status").eq("id", proposal_id).single().execute()
        from_status = prop.data["status"]

        # Validate
        await StateValidator.validate_transition(
            proposal_id, from_status, to_status, actor_type, reason
        )

        # Update proposal
        update_data = {"status": to_status, "last_activity_at": datetime.utcnow().isoformat()}
        if current_phase:
            update_data["current_phase"] = current_phase

        # Set started_at on first transition from initialized
        if from_status == "initialized" and to_status != "initialized":
            update_data["started_at"] = datetime.utcnow().isoformat()

        # Set completed_at for terminal states
        if to_status in ("won", "lost", "no_go"):
            update_data["completed_at"] = datetime.utcnow().isoformat()

        await client.table("proposals").update(update_data).eq("id", proposal_id).execute()

        # Log to timeline
        timeline_entry = {
            "proposal_id": proposal_id,
            "event_type": "status_change",
            "from_status": from_status,
            "to_status": to_status,
            "from_phase": None,  # Will be filled by phase change
            "to_phase": current_phase,
            "triggered_by": user_id,
            "actor_type": actor_type,
            "trigger_reason": reason,
            "metadata": metadata or {}
        }

        result = await client.table("proposal_timelines").insert(timeline_entry).execute()
        return result.data[0] if result.data else {}
```

### 2.2 State Machine Class

**New File**: `app/state_machine.py`

```python
from enum import Enum
from app.services.state_validator import StateValidator, ProposalStatus

class StateMachine:
    """
    Proposal state machine with phase tracking.
    Separates business status (Layer 1) from workflow phase (Layer 2).
    """

    def __init__(self, proposal_id: str):
        self.proposal_id = proposal_id

    async def start_workflow(self, user_id: str):
        """Transition from initialized → first active state"""
        await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.ANALYZING,
            current_phase="rfp_analyze",
            user_id=user_id,
            actor_type="user",
            reason="Workflow started by user"
        )

    async def decide_go(self, user_id: str, notes: str = ""):
        """Go/No-Go: Go decision"""
        await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.STRATEGIZING,
            current_phase="strategy_generate",
            user_id=user_id,
            actor_type="user",
            reason="Go decision",
            metadata={"decision": "go", "notes": notes}
        )

    async def decide_no_go(self, user_id: str, reason: str = ""):
        """Go/No-Go: No-Go decision"""
        await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.NO_GO,
            user_id=user_id,
            actor_type="user",
            reason="No-Go decision",
            metadata={"decision": "no_go", "reason": reason}
        )

    async def submit_proposal(self, user_id: str):
        """Transition to submitted"""
        await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.SUBMITTED,
            current_phase="submit",
            user_id=user_id,
            actor_type="user",
            reason="Proposal submitted"
        )

    async def mark_presented(self, user_id: str):
        """Transition to presented"""
        await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.PRESENTED,
            current_phase="presented",
            user_id=user_id,
            actor_type="user",
            reason="Proposal presented"
        )

    async def record_win(self, user_id: str, metadata: dict = None):
        """Record winning contract"""
        await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.WON,
            user_id=user_id,
            actor_type="user",
            reason="Contract won",
            metadata=metadata or {}
        )

    async def record_loss(self, user_id: str, reason: str = "", metadata: dict = None):
        """Record lost bid"""
        await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.LOST,
            user_id=user_id,
            actor_type="user",
            reason=reason or "Contract lost",
            metadata=metadata or {}
        )
```

### 2.3 Update Workflow Nodes

**Strategy**: Replace direct `proposals.update({"status": ...})` with state machine calls.

**Files to Update**:
1. `app/graph/nodes/gate_nodes.py` (passthrough, fork gates)
2. `app/graph/nodes/go_no_go.py` (decision point)
3. `app/graph/nodes/review_node.py` (review gates)
4. Any node that calls `client.table("proposals").update(...)`

**Pattern**:

Before:
```python
await client.table("proposals").update({
    "status": "processing",
    "current_phase": "strategy_generate"
}).eq("id", proposal_id).execute()
```

After:
```python
from app.state_machine import StateMachine

sm = StateMachine(proposal_id)
await sm.transition(
    ProposalStatus.STRATEGIZING,
    current_phase="strategy_generate",
    user_id=state.get("user_id"),
    actor_type="workflow"
)
```

---

## Phase 3: API and Service Updates (2 Days)

### 3.1 Enhanced Workflow State Endpoint

**Updated**: `GET /api/proposals/{id}/state`

**Current Response**:
```json
{
  "proposal_id": "abc-123",
  "status": "processing",
  "current_phase": "proposal_write_next"
}
```

**New Response** (all 3 layers):
```json
{
  "proposal_id": "abc-123",
  "business_status": "processing",
  "workflow_phase": "proposal_write_next",
  "ai_status": {
    "task_id": "task-456",
    "status": "running",
    "current_step": "section_2",
    "progress": "Generating Impacts & Benefits section..."
  },
  "timestamps": {
    "created_at": "2026-03-30T10:00:00Z",
    "started_at": "2026-03-30T10:05:00Z",
    "last_activity_at": "2026-03-30T11:30:00Z",
    "completed_at": null
  },
  "recent_transitions": [
    {
      "event_type": "status_change",
      "from_status": "analyzing",
      "to_status": "processing",
      "to_phase": "proposal_write_next",
      "at": "2026-03-30T10:30:00Z",
      "reason": "Go decision",
      "triggered_by": "user_123"
    }
  ]
}
```

**Implementation**:
```python
@router.get("/{proposal_id}/state", response_model=EnhancedWorkflowStateResponse)
async def get_enhanced_state(proposal_id: str, ...):
    client = await get_async_client()

    # Layer 1: Business status
    prop = await client.table("proposals").select(
        "id,status,current_phase,created_at,started_at,last_activity_at,completed_at"
    ).eq("id", proposal_id).single().execute()

    # Layer 2: Current phase (already in proposal)
    # Layer 3: AI status
    ai_status = await client.table("ai_task_logs").select(
        "id,status,step,metadata"
    ).eq("proposal_id", proposal_id).order("created_at", desc=True).limit(1).single().execute()

    # Timeline: recent transitions
    timeline = await client.table("proposal_timelines").select(
        "event_type,from_status,to_status,to_phase,created_at,trigger_reason,triggered_by"
    ).eq("proposal_id", proposal_id).order("created_at", desc=True).limit(5).execute()

    return {
        "proposal_id": proposal_id,
        "business_status": prop.data["status"],
        "workflow_phase": prop.data["current_phase"],
        "ai_status": ...,
        "timestamps": {...},
        "recent_transitions": timeline.data
    }
```

### 3.2 New State History Endpoint

**New Endpoint**: `GET /api/proposals/{id}/state-history`

**Query Parameters**:
- `limit` (default: 50) — Number of entries
- `offset` (default: 0) — Pagination
- `event_type` (optional) — Filter by event type

**Response**:
```json
{
  "proposal_id": "abc-123",
  "total_events": 42,
  "history": [
    {
      "id": "event-1",
      "event_type": "status_change",
      "from_status": "processing",
      "to_status": "submitted",
      "to_phase": "submit",
      "at": "2026-03-30T14:30:00Z",
      "reason": "Proposal submitted to client",
      "actor_type": "user",
      "triggered_by": "user_123",
      "notes": "Final version",
      "metadata": {}
    }
  ]
}
```

### 3.3 Updated Notifications

**When to Notify**:
- Status changes to terminal states (won, lost, no_go)
- Major workflow phase transitions
- Go/No-Go decisions

**Notification Content**:
```json
{
  "type": "proposal_status_change",
  "proposal_id": "abc-123",
  "business_status": "won",
  "title": "Proposal Won! 🎉",
  "message": "Project 'Healthcare AI' was awarded",
  "action_url": "/proposals/abc-123"
}
```

---

## Phase 4: Testing and Deployment (1 Day)

### 4.1 Unit Tests

**File**: `tests/services/test_state_validator.py`

```python
async def test_valid_transition():
    """Valid transition should succeed"""
    assert await StateValidator.validate_transition(
        "prop-123",
        ProposalStatus.ANALYZING,
        ProposalStatus.STRATEGIZING
    )

async def test_invalid_transition():
    """Invalid transition should raise error"""
    with pytest.raises(ValueError):
        await StateValidator.validate_transition(
            "prop-123",
            ProposalStatus.WON,
            ProposalStatus.PROCESSING
        )

async def test_transition_creates_timeline():
    """Transition should create timeline entry"""
    result = await StateValidator.transition(
        "prop-123",
        ProposalStatus.PROCESSING,
        reason="Test transition"
    )
    assert result["proposal_id"] == "prop-123"
    assert result["event_type"] == "status_change"

async def test_sets_started_at():
    """First transition from initialized should set started_at"""
    # Setup: proposal in initialized state
    # Action: transition to analyzing
    # Assert: started_at is set
```

### 4.2 Integration Tests

**File**: `tests/api/test_workflow_state.py`

```python
async def test_workflow_state_returns_all_layers():
    """GET /state should return all 3 layers"""
    response = await client.get(f"/proposals/{PROPOSAL_ID}/state")
    assert response.status_code == 200
    body = response.json()

    assert "business_status" in body
    assert "workflow_phase" in body
    assert "ai_status" in body
    assert "timestamps" in body
    assert "recent_transitions" in body

async def test_state_history_pagination():
    """State history should support pagination"""
    response = await client.get(
        f"/proposals/{PROPOSAL_ID}/state-history?limit=10&offset=0"
    )
    assert response.status_code == 200
    body = response.json()
    assert len(body["history"]) <= 10

async def test_proposal_workflow_progression():
    """Workflow should progress through states correctly"""
    # Start with initialized
    # Trigger analyze
    # Trigger go decision
    # Trigger submit
    # Verify each state transition is logged
```

### 4.3 Rollback Plan

**If Critical Issues Found**:

1. **Database**: Run rollback migration (drop new tables, remove columns)
2. **Code**: Revert to previous commit (routes_workflow.py hotfix still in place)
3. **State**: Timeline entries will be orphaned but won't break workflow

**Rollback Commands**:
```bash
# Revert migration
psql -f database/rollback_migration_012.sql

# Revert code
git revert <commit-hash>

# Redeploy hotfix version
git checkout <phase-0-commit>
```

---

## Implementation Dependencies

### Import Graph
```
state_machine.py
  ├─ state_validator.py
  │  └─ supabase_client
  └─ enums (ProposalStatus)

routes_workflow.py (updated)
  ├─ state_machine.py
  └─ ai_status_manager.py

graph/nodes/ (updated)
  ├─ state_machine.py
  └─ supabase_client

notification_service.py (updated)
  ├─ state_machine.py
  └─ teams webhook
```

### Files to Create
1. `app/services/state_validator.py` (new)
2. `app/state_machine.py` (new)
3. `database/migrations/012_unified_state_system.sql` (new)
4. `database/rollback_migration_012.sql` (new)

### Files to Update
1. `app/api/routes_workflow.py` (add state history endpoint, enhance state endpoint)
2. `app/graph/nodes/gate_nodes.py` (use state_machine for transitions)
3. `app/graph/nodes/go_no_go.py` (use state_machine for decision)
4. `app/services/notification_service.py` (subscribe to status changes)
5. `tests/` (add new tests)

### Database Changes
- ✅ Phase 1: Create proposal_timelines table
- ✅ Phase 1: Add timestamp columns to proposals
- ✅ Phase 1: Verify ai_task_logs constraints

---

## Success Criteria

### Phase 1 (Database)
- ✅ proposal_timelines table created with proper indexes
- ✅ Timestamp columns added to proposals
- ✅ Migration script runs without errors
- ✅ Existing data populated correctly
- ✅ Rollback script tested

### Phase 2 (Backend)
- ✅ StateValidator validates all transitions correctly
- ✅ StateMachine executes transitions with timeline logging
- ✅ All workflow nodes use state_machine for transitions
- ✅ No direct `proposals.update(status=...)` calls remain in graph

### Phase 3 (API)
- ✅ GET /state returns all 3 layers
- ✅ GET /state-history returns paginated timeline
- ✅ Notifications triggered on status changes
- ✅ All endpoints return consistent state information

### Phase 4 (Testing)
- ✅ Unit tests for state transitions (10+ tests)
- ✅ Integration tests for workflow progression
- ✅ All existing workflow endpoints still work
- ✅ No regressions in proposal creation/deletion
- ✅ Deployment checklist completed

---

## Remaining Design Questions

1. **Force Transitions**: Should admins be able to force invalid transitions for cleanup?
2. **AI Status Sync**: Should proposal.status auto-update based on ai_task_logs status?
3. **Notification Throttling**: Should we throttle notifications if many transitions occur rapidly?
4. **Analytics**: Should we add status transition analytics to the dashboard?

---

## References

- **Plan**: `docs/01-plan/features/unified-state-system.plan.md`
- **Schema**: `database/schema_v3.4.sql` (current)
- **Workflow**: `app/graph/graph.py` (40 nodes)
- **Current Services**: `app/services/ai_status_manager.py`, `app/services/notification_service.py`
- **Existing Timeline Pattern**: None (new pattern)
