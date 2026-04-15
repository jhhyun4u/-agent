"""
State transition validator for unified state system.

Ensures all proposal status transitions follow valid paths and logs transitions
to proposal_timelines table for audit trail.

Layer 1 (Business Status):
  - initialized, waiting, in_progress, completed, submitted, presentation, closed, archived, on_hold, expired

Layer 3 (AI Runtime Status):
  - running, paused, error, no_response, complete
"""

from typing import Optional, Set
from enum import Enum
from datetime import datetime
from app.utils.supabase_client import get_async_client
from app.exceptions import TenopAPIError


class ProposalStatus(str, Enum):
    """Valid proposal business statuses (Layer 1)"""
    INITIALIZED = "initialized"
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SUBMITTED = "submitted"
    PRESENTATION = "presentation"
    CLOSED = "closed"
    ARCHIVED = "archived"
    ON_HOLD = "on_hold"
    EXPIRED = "expired"


class WinResult(str, Enum):
    """Win/Loss/No-Go decision (Layer 1, child of CLOSED status)"""
    WON = "won"
    LOST = "lost"
    NO_GO = "no_go"
    ABANDONED = "abandoned"
    CANCELLED = "cancelled"


class AITaskStatus(str, Enum):
    """AI runtime status (Layer 3, independent of proposal.status)"""
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"
    NO_RESPONSE = "no_response"
    COMPLETE = "complete"


class StateValidator:
    """Validates and logs proposal state transitions."""

    # Valid state machine transitions: from_status → {allowed_to_status}
    VALID_TRANSITIONS = {
        ProposalStatus.INITIALIZED: {
            ProposalStatus.WAITING,
            ProposalStatus.IN_PROGRESS,
            ProposalStatus.ON_HOLD,
            ProposalStatus.EXPIRED,
        },
        ProposalStatus.WAITING: {
            ProposalStatus.IN_PROGRESS,
            ProposalStatus.ON_HOLD,
            ProposalStatus.EXPIRED,
        },
        ProposalStatus.IN_PROGRESS: {
            ProposalStatus.COMPLETED,
            ProposalStatus.ON_HOLD,
            ProposalStatus.EXPIRED,
        },
        ProposalStatus.COMPLETED: {
            ProposalStatus.SUBMITTED,
            ProposalStatus.ON_HOLD,
            ProposalStatus.EXPIRED,
        },
        ProposalStatus.SUBMITTED: {
            ProposalStatus.PRESENTATION,
            ProposalStatus.ON_HOLD,
            ProposalStatus.EXPIRED,
        },
        ProposalStatus.PRESENTATION: {
            ProposalStatus.CLOSED,
            ProposalStatus.ON_HOLD,
            ProposalStatus.EXPIRED,
        },
        ProposalStatus.CLOSED: set(),           # Terminal
        ProposalStatus.ARCHIVED: set(),         # Terminal
        ProposalStatus.ON_HOLD: {
            ProposalStatus.WAITING,
            ProposalStatus.IN_PROGRESS,
            ProposalStatus.EXPIRED,
        },
        ProposalStatus.EXPIRED: set(),          # Terminal
    }

    @staticmethod
    def is_terminal_state(status: ProposalStatus) -> bool:
        """Check if status is terminal (no further transitions allowed)."""
        return len(StateValidator.VALID_TRANSITIONS.get(status, set())) == 0

    @staticmethod
    def get_allowed_transitions(status: ProposalStatus) -> Set[ProposalStatus]:
        """Get set of allowed next statuses."""
        return StateValidator.VALID_TRANSITIONS.get(status, set())

    @staticmethod
    async def validate_transition(
        proposal_id: str,
        from_status: str,
        to_status: str,
    ) -> None:
        """
        Validate if transition is allowed.

        Args:
            proposal_id: Proposal UUID
            from_status: Current status
            to_status: Desired next status

        Raises:
            TenopAPIError: If transition is invalid
        """
        # Normalize to enum
        try:
            from_enum = ProposalStatus(from_status)
            to_enum = ProposalStatus(to_status)
        except ValueError as e:
            raise TenopAPIError(
                code="invalid_status",
                message=f"Invalid status value(s): from={from_status}, to={to_status}",
            ) from e

        # Check if transition is allowed
        allowed = StateValidator.get_allowed_transitions(from_enum)
        if to_enum not in allowed:
            raise TenopAPIError(
                code="invalid_transition",
                message=f"Invalid transition: {from_status} → {to_status}. "
                        f"Allowed: {[s.value for s in allowed]}",
            )

    @staticmethod
    async def transition(
        proposal_id: str,
        to_status: ProposalStatus,
        current_phase: Optional[str] = None,
        user_id: Optional[str] = None,
        actor_type: str = "workflow",
        reason: Optional[str] = None,
        metadata: Optional[dict] = None,
        win_result: Optional[str] = None,
    ) -> dict:
        """
        Execute state transition with timeline logging.

        Args:
            proposal_id: Proposal UUID
            to_status: New status
            current_phase: LangGraph node name
            user_id: User who triggered transition (optional)
            actor_type: 'user', 'workflow', 'system', 'ai', 'cron'
            reason: Reason for transition
            metadata: Additional JSONB data
            win_result: If to_status is CLOSED, must specify win result

        Returns:
            Timeline entry dict

        Raises:
            TenopAPIError: If validation fails
        """
        client = await get_async_client()

        # Get current status
        try:
            prop = await client.table("proposals").select("status").eq("id", proposal_id).single().execute()
            from_status = prop.data["status"]
        except Exception as e:
            raise TenopAPIError(
                code="proposal_not_found",
                message=f"Proposal {proposal_id} not found",
            ) from e

        # Validate transition
        await StateValidator.validate_transition(proposal_id, from_status, to_status.value)

        # Build update dict
        update_data = {
            "status": to_status.value,
            "last_activity_at": datetime.utcnow().isoformat(),
        }

        # Set timestamps based on status
        if from_status == ProposalStatus.INITIALIZED.value and to_status != ProposalStatus.INITIALIZED:
            update_data["started_at"] = datetime.utcnow().isoformat()

        if to_status == ProposalStatus.SUBMITTED:
            update_data["submitted_at"] = datetime.utcnow().isoformat()

        if to_status == ProposalStatus.PRESENTATION:
            update_data["presentation_started_at"] = datetime.utcnow().isoformat()

        if to_status == ProposalStatus.CLOSED:
            update_data["closed_at"] = datetime.utcnow().isoformat()
            if win_result:
                update_data["win_result"] = win_result

        if to_status == ProposalStatus.ARCHIVED:
            update_data["archived_at"] = datetime.utcnow().isoformat()

        if to_status == ProposalStatus.EXPIRED:
            update_data["expired_at"] = datetime.utcnow().isoformat()

        if current_phase:
            update_data["current_phase"] = current_phase

        # Update proposal
        try:
            await client.table("proposals").update(update_data).eq("id", proposal_id).execute()
        except Exception as e:
            raise TenopAPIError(
                code="proposal_update_failed",
                message=f"Failed to update proposal {proposal_id}",
            ) from e

        # Log to timeline
        timeline_entry = {
            "proposal_id": proposal_id,
            "event_type": "status_change",
            "from_status": from_status,
            "to_status": to_status.value,
            "to_phase": current_phase,
            "triggered_by": user_id,
            "actor_type": actor_type,
            "trigger_reason": reason,
            "notes": None,
            "metadata": metadata or {},
        }

        try:
            result = await client.table("proposal_timelines").insert(timeline_entry).execute()
            return result.data[0] if result.data else {}
        except Exception as e:
            # Log to timeline is best-effort; don't fail the transition
            import logging
            logging.warning(f"Failed to log timeline entry for proposal {proposal_id}: {e}")
            return {}

    @staticmethod
    async def update_ai_task_status(
        proposal_id: str,
        ai_status: AITaskStatus,
        current_node: Optional[str] = None,
        error_message: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Update AI task runtime status (Layer 3).

        Independent of proposal.status. Multiple AI tasks can run while
        proposal.status remains 'in_progress'.

        Args:
            proposal_id: Proposal UUID
            ai_status: Current AI task status
            current_node: LangGraph node being executed
            error_message: Error details if status is ERROR
            session_id: LangGraph thread/session ID

        Returns:
            Updated ai_task_status record
        """
        client = await get_async_client()

        update_data = {
            "status": ai_status.value,
            "last_heartbeat": datetime.utcnow().isoformat(),
        }

        if current_node:
            update_data["current_node"] = current_node

        if error_message:
            update_data["error_message"] = error_message

        if ai_status in (AITaskStatus.COMPLETE, AITaskStatus.ERROR):
            update_data["ended_at"] = datetime.utcnow().isoformat()

        if session_id:
            update_data["session_id"] = session_id

        try:
            # Get or create latest ai_task_status
            existing = await client.table("ai_task_status").select("id").eq(
                "proposal_id", proposal_id
            ).order("started_at", desc=True).limit(1).execute()

            if existing.data:
                # Update existing
                result = await client.table("ai_task_status").update(
                    update_data
                ).eq("id", existing.data[0]["id"]).execute()
            else:
                # Create new
                insert_data = {
                    "proposal_id": proposal_id,
                    **update_data,
                }
                result = await client.table("ai_task_status").insert(insert_data).execute()

            return result.data[0] if result.data else {}

        except Exception as e:
            import logging
            logging.error(f"Failed to update AI task status for {proposal_id}: {e}")
            return {}
