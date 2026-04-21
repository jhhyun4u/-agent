"""
Proposal Status State Machine Validator

Valid transitions:
  CREATED → REVIEW → APPROVED → SUBMITTED → COMPLETED
        ↘ REJECTED (terminal at any point)
"""

from enum import Enum
from typing import Set


class ProposalStatus(str, Enum):
    """Proposal workflow status enum."""
    CREATED = "created"
    REVIEW = "review"
    APPROVED = "approved"
    SUBMITTED = "submitted"
    COMPLETED = "completed"
    REJECTED = "rejected"


# Valid state transitions: current_state -> set(valid_next_states)
VALID_STATUS_TRANSITIONS: dict[ProposalStatus, Set[ProposalStatus]] = {
    ProposalStatus.CREATED: {ProposalStatus.REVIEW, ProposalStatus.REJECTED},
    ProposalStatus.REVIEW: {ProposalStatus.APPROVED, ProposalStatus.REJECTED},
    ProposalStatus.APPROVED: {ProposalStatus.SUBMITTED, ProposalStatus.REJECTED},
    ProposalStatus.SUBMITTED: {ProposalStatus.COMPLETED, ProposalStatus.REJECTED},
    ProposalStatus.COMPLETED: set(),  # Terminal state
    ProposalStatus.REJECTED: set(),   # Terminal state
}


def validate_status_transition(current: str | ProposalStatus, next_status: str | ProposalStatus) -> None:
    """
    Validate status transition is allowed.

    Args:
        current: Current status
        next_status: Desired next status

    Raises:
        ValueError: If transition is invalid
    """
    current_enum = ProposalStatus(current) if isinstance(current, str) else current
    next_enum = ProposalStatus(next_status) if isinstance(next_status, str) else next_status

    valid_next = VALID_STATUS_TRANSITIONS.get(current_enum, set())

    if next_enum not in valid_next:
        valid_names = [s.value for s in valid_next]
        raise ValueError(
            f"Invalid status transition: {current_enum.value} → {next_enum.value}. "
            f"Valid next states: {valid_names if valid_names else '(terminal state)'}"
        )
