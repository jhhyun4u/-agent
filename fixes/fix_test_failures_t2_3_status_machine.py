"""
Fix T2.3: Proposal Status State Machine Validation (3 failing tests)

Tests:
1. test_invalid_proposal_status_value
2. test_invalid_bid_no_status_update
3. test_get_status_excellent

Issue: Status transitions not validated against state machine
"""

# CURRENT ISSUE:
# Proposal statuses allow invalid transitions. For example:
# - CREATED → REJECTED → REVIEW (invalid, can't go backward)
# - COMPLETED → SUBMITTED (invalid, can't revert)

# VALID STATE MACHINE:
# CREATED → REVIEW → APPROVED → SUBMITTED → COMPLETED
#                  ↘ REJECTED (terminal)
#         ↘ REJECTED (terminal)

# FILE: app/models/proposal_schemas.py
# BEFORE: No status validation

# AFTER: Add status validator

code_fix = '''
from enum import Enum
from typing import Optional

class ProposalStatus(str, Enum):
    CREATED = "created"
    REVIEW = "review"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    REJECTED = "rejected"

# Valid state transitions
VALID_STATUS_TRANSITIONS = {
    ProposalStatus.CREATED: {ProposalStatus.REVIEW, ProposalStatus.REJECTED},
    ProposalStatus.REVIEW: {ProposalStatus.APPROVED, ProposalStatus.REJECTED},
    ProposalStatus.APPROVED: {ProposalStatus.SUBMITTED, ProposalStatus.REJECTED},
    ProposalStatus.SUBMITTED: {ProposalStatus.COMPLETED, ProposalStatus.REJECTED},
    ProposalStatus.COMPLETED: set(),  # Terminal state
    ProposalStatus.REJECTED: set(),   # Terminal state
}

def validate_status_transition(current: ProposalStatus, next: ProposalStatus) -> None:
    """Validate status transition is allowed."""
    if next not in VALID_STATUS_TRANSITIONS.get(current, set()):
        raise ValueError(
            f"Invalid status transition: {current.value} → {next.value}. "
            f"Valid next states: {[s.value for s in VALID_STATUS_TRANSITIONS[current]]}"
        )

class ProposalStatusUpdate(BaseModel):
    """Request to update proposal status."""
    current_status: ProposalStatus
    new_status: ProposalStatus
    reason: Optional[str] = None

    @validator("new_status", pre=False)
    def validate_transition(cls, v, values):
        if "current_status" in values:
            validate_status_transition(values["current_status"], v)
        return v
'''

# FILE: app/services/proposal_service.py
# BEFORE:
"""
async def update_status(self, proposal_id: str, new_status: str):
    proposal = await self.get_proposal(proposal_id)
    proposal.status = new_status  # No validation!
    await self.db.update(proposal)
"""

# AFTER:
"""
async def update_status(self, proposal_id: str, new_status: str):
    proposal = await self.get_proposal(proposal_id)
    current = ProposalStatus(proposal.status)
    next_status = ProposalStatus(new_status)

    # Validate transition
    validate_status_transition(current, next_status)

    proposal.status = new_status
    await self.db.update(proposal)
"""

# TESTS THAT WILL FIX:
tests_fixed = {
    "test_invalid_proposal_status_value": "Rejects invalid enum values",
    "test_invalid_bid_no_status_update": "Rejects invalid transition (e.g., REJECTED → SUBMITTED)",
    "test_get_status_excellent": "Validates status machine for excellence ratings"
}

print("""
Steps to fix status machine (T2.3):

1. Create app/models/proposal_status_validator.py:
   - Define ProposalStatus enum with 6 states
   - Define VALID_STATUS_TRANSITIONS dict
   - Add validate_status_transition() function

2. Update app/models/proposal_schemas.py:
   - Import ProposalStatus from new module
   - Add validator to ProposalStatusUpdate model
   - Validate transitions on model instantiation

3. Update app/services/proposal_service.py:
   - Import validate_status_transition
   - Add validation to update_status() method
   - Raise ValueError if transition invalid

4. Run tests: pytest -k "test_invalid_proposal_status_value or test_invalid_bid or test_get_status" -v
5. All 3 tests should pass
""")
