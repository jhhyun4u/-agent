# Test Failure Analysis & Fix Plan

**Status**: DIAGNOSIS PHASE  
**Date**: 2026-04-21  
**Identified Issues**: 10 blocking tests  
**Fix Timeline**: 4-6 hours (parallel fixes)

---

## Failure Categories

### Category 1: Authorization Validation (5 failures)

**Tests Affected**:
1. `test_unauthorized_team_access` — Missing role check in GET /api/dashboard/*
2. `test_no_auth_header_returns_401` — Auth header validation
3. `test_websocket_unauthorized_access` — WebSocket auth check
4. `test_unauthorized_job_status` — Job queue access control
5. `test_forbidden_access_other_team` — Cross-team access control

**Root Cause**: `app/api/deps.py` `require_role()` decorator not validating role against endpoint permissions

**Fix Plan** (T2.1):
```python
# File: app/api/deps.py (line ~45)
# Current: Only checks if user has SOME role
# Fix: Also check if role is in endpoint's required_roles list

async def require_role(required_roles: list[str]):
    async def check_role(current_user: CurrentUser = Depends(get_current_user)):
        if current_user.role not in required_roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return check_role

# Usage in routes:
@router.get("/metrics/executive")
async def get_metrics(user = Depends(require_role(["admin", "director"]))):
    ...
```

**Files to Fix**:
- `app/api/deps.py` — Add role validation
- `app/api/routes_dashboard.py` — Add required_roles parameter to decorators
- `app/api/routes_jobs.py` — Apply same fix

**Expected Tests to Fix**: 5 authorization tests

---

### Category 2: Budget Filtering Logic (1 failure)

**Test**: `test_bid_with_budget_below_threshold`

**Root Cause**: Budget filter in `test_bid_to_proposal_workflow.py` expects proposals <$300K to be excluded, but filter is inverted

**Fix Plan** (T2.2):
```python
# File: app/services/bid_market_research.py (line ~120)
# Current: `where budget >= threshold`
# Fix: `where budget <= threshold` for "below threshold" queries

# Or fix the test expectation instead if logic is correct
# Read test first to understand intent
```

**Files to Fix**:
- `app/services/bid_market_research.py` — Review budget filtering
- OR fix test expectation in `tests/integration/test_bid_to_proposal_workflow.py`

**Expected Tests to Fix**: 1 bid workflow test

---

### Category 3: Status Machine Transitions (3 failures)

**Tests Affected**:
1. `test_invalid_proposal_status_value` — Invalid status enum
2. `test_invalid_bid_no_status_update` — Bid status not updating to "submitted"
3. `test_get_status_excellent` — Status harness validation

**Root Cause**: Proposal status state machine in `app/models/` doesn't validate enum transitions. Missing: CREATED→REVIEW→APPROVED→SUBMITTED→COMPLETED

**Fix Plan** (T2.3):
```python
# File: app/models/proposal_schemas.py (line ~85)
# Add status validator:

from enum import Enum

class ProposalStatus(str, Enum):
    CREATED = "created"
    REVIEW = "review"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    REJECTED = "rejected"

# Valid transitions:
VALID_TRANSITIONS = {
    "created": ["review", "rejected"],
    "review": ["approved", "rejected"],
    "approved": ["submitted", "rejected"],
    "submitted": ["completed", "rejected"],
    "completed": [],
    "rejected": []
}

def validate_status_transition(current: ProposalStatus, next: ProposalStatus):
    if next.value not in VALID_TRANSITIONS[current.value]:
        raise ValueError(f"Invalid transition: {current} → {next}")
```

**Files to Fix**:
- `app/models/proposal_schemas.py` — Add status validator
- `app/services/proposal_service.py` — Call validator on update_status()

**Expected Tests to Fix**: 3 status transition tests

---

### Category 4: Test Data Issues (1 failure)

**Test**: General test data setup missing/incomplete

**Root Cause**: Pytest fixtures in `tests/conftest.py` not initializing database state properly. Missing seeding for test user, org, team

**Fix Plan** (T2.4):
```python
# File: tests/conftest.py
# Add fixture:

@pytest.fixture(scope="session")
def setup_test_db():
    """Seed test database with minimal required data"""
    # Create test org, team, users
    test_org = create_test_org("test-org-001")
    test_team = create_test_team(test_org.id, "team-001")
    test_user = create_test_user(
        org_id=test_org.id,
        team_id=test_team.id,
        role="member"
    )
    yield {"org": test_org, "team": test_team, "user": test_user}
    # Cleanup
    delete_test_data(test_org.id)
```

**Files to Fix**:
- `tests/conftest.py` — Add database seeding fixture
- `tests/fixtures/db_fixtures.py` — Helper functions

**Expected Tests to Fix**: 1 general test data setup test

---

## Fix Execution Plan (Parallel)

### T2.1: Authorization Fixes (1h)
- Edit: `app/api/deps.py` (line 45-55)
- Edit: `app/api/routes_dashboard.py` (add `required_roles` to 6 endpoints)
- Test: 5 authorization tests should pass
- Parallel: Can start immediately

### T2.2: Budget Filtering Fix (20 min)
- Review: `tests/integration/test_bid_to_proposal_workflow.py` (understand intent)
- Edit: Either test expectation OR service logic
- Test: 1 bid workflow test should pass
- Parallel: Can start immediately (no dependencies)

### T2.3: Status Machine Fix (45 min)
- Create: `app/models/proposal_schemas.py` status validator class
- Edit: `app/services/proposal_service.py` to use validator
- Edit: All status update calls to validate transitions
- Test: 3 status transition tests should pass
- Parallel: Can start immediately

### T2.4: Test Data Seeding (30 min)
- Create: `tests/fixtures/db_fixtures.py` helper functions
- Edit: `tests/conftest.py` to use fixtures
- Test: Run full test suite to verify seeding works
- Parallel: Can start immediately

---

## Verification Steps

**After all fixes**:
```bash
# Run full test suite
cd /c/project/tenopa\ proposer
uv sync
uv run pytest -v --tb=short

# Expected result:
# PASSED: 14 dashboard tests
# PASSED: 5 authorization tests ✓
# PASSED: 1 budget test ✓
# PASSED: 3 status tests ✓
# PASSED: 1 data seeding test ✓
# FAILED: 0
```

**Commit & Push**:
```bash
git add -A
git commit -m "fix: resolve 10 blocking test failures

- Authorization: Add role validation to require_role() decorator
- Budget: Fix budget threshold filtering logic
- Status: Implement proposal status state machine validator
- Test data: Add database seeding fixtures

All 10 tests now passing."
git push origin main
```

---

## Risk Assessment

| Fix | Risk | Mitigation |
|-----|------|-----------|
| Authorization | Medium (changes auth logic) | Run full test suite + security review |
| Budget | Low (filtering logic isolated) | Review test intent first |
| Status | Medium (affects proposal workflow) | Add transition validator tests |
| Test data | Low (test-only changes) | Verify all tests pass |

**Overall Risk**: LOW-MEDIUM. Can be deployed together after verification.

