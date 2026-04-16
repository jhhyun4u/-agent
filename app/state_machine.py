"""
Proposal state machine with business-level methods.

Wraps StateValidator to provide convenient methods for common transitions:
- start_workflow() → in_progress
- decide_go() → in_progress (from analyzing)
- decide_no_go() → on_hold or closed
- submit() → submitted
- present() → presentation
- record_win() → closed (won)
- record_loss() → closed (lost)

This separates business logic (Layer 1: status) from workflow execution (Layer 2: phase)
and AI runtime state (Layer 3: ai_task_status).
"""

from typing import Optional
from app.services.state_validator import StateValidator, ProposalStatus, WinResult


class StateMachine:
    """
    Business-level state machine for proposals.

    Usage:
        sm = ProposalStateMachine(proposal_id)
        await sm.start_workflow(user_id="user-123")
        await sm.decide_go(user_id="user-123", notes="Strong fit")
        await sm.submit(user_id="user-123")
        await sm.record_win(user_id="user-123", contract_value=1000000)
    """

    def __init__(self, proposal_id: str):
        self.proposal_id = proposal_id

    async def start_workflow(
        self,
        user_id: str,
        phase: str = "rfp_analyze",
    ) -> dict:
        """
        Start proposal workflow (initialized → in_progress).

        Args:
            user_id: User starting the workflow
            phase: Initial workflow phase (default: rfp_analyze)

        Returns:
            Timeline entry
        """
        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.IN_PROGRESS,
            current_phase=phase,
            user_id=user_id,
            actor_type="user",
            reason="Workflow started by user",
        )

    async def decide_go(
        self,
        user_id: str,
        phase: str = "strategy_generate",
        notes: str = "",
    ) -> dict:
        """
        Go/No-Go decision: Go (in_progress → in_progress with phase change).

        Actually marks as ready for strategy generation.

        Args:
            user_id: User making the decision
            phase: Next workflow phase (default: strategy_generate)
            notes: Decision notes

        Returns:
            Timeline entry
        """
        metadata = {}
        if notes:
            metadata["decision"] = "go"
            metadata["notes"] = notes

        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.IN_PROGRESS,
            current_phase=phase,
            user_id=user_id,
            actor_type="user",
            reason="Go decision",
            metadata=metadata,
        )

    async def decide_no_go(
        self,
        user_id: str,
        reason: str = "",
    ) -> dict:
        """
        Go/No-Go decision: No-Go (in_progress → on_hold).

        Can be resumed later if conditions change.

        Args:
            user_id: User making the decision
            reason: Reason for no-go

        Returns:
            Timeline entry
        """
        metadata = {
            "decision": "no_go",
        }
        if reason:
            metadata["reason"] = reason

        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.ON_HOLD,
            user_id=user_id,
            actor_type="user",
            reason="No-Go decision",
            metadata=metadata,
        )

    async def submit(
        self,
        user_id: str,
    ) -> dict:
        """
        Submit proposal to client/issuing authority (completed → submitted).

        Args:
            user_id: User submitting

        Returns:
            Timeline entry
        """
        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.SUBMITTED,
            current_phase="submit",
            user_id=user_id,
            actor_type="user",
            reason="Proposal submitted to client",
        )

    async def present(
        self,
        user_id: str,
    ) -> dict:
        """
        Mark proposal presentation/bidding as active (submitted → presentation).

        Args:
            user_id: User marking as presented

        Returns:
            Timeline entry
        """
        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.PRESENTATION,
            current_phase="presentation",
            user_id=user_id,
            actor_type="user",
            reason="Proposal presented to client",
        )

    async def record_win(
        self,
        user_id: str,
        contract_value: Optional[float] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Record winning contract (presentation → closed with win_result='won').

        Args:
            user_id: User recording the win
            contract_value: Contract value in currency
            metadata: Additional data (contract_id, award_date, etc.)

        Returns:
            Timeline entry
        """
        record_metadata = metadata or {}
        if contract_value is not None:
            record_metadata["contract_value"] = contract_value

        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.CLOSED,
            user_id=user_id,
            actor_type="user",
            reason="Contract won",
            metadata=record_metadata,
            win_result=WinResult.WON.value,
        )

    async def record_loss(
        self,
        user_id: str,
        loss_reason: str = "",
        metadata: Optional[dict] = None,
    ) -> dict:
        """
        Record lost bid (presentation → closed with win_result='lost').

        Args:
            user_id: User recording the loss
            loss_reason: Why was it lost
            metadata: Additional data (competitor_name, score, etc.)

        Returns:
            Timeline entry
        """
        record_metadata = metadata or {}
        if loss_reason:
            record_metadata["loss_reason"] = loss_reason

        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.CLOSED,
            user_id=user_id,
            actor_type="user",
            reason=loss_reason or "Contract lost",
            metadata=record_metadata,
            win_result=WinResult.LOST.value,
        )

    async def abandon(
        self,
        user_id: str,
        reason: str = "",
    ) -> dict:
        """
        Abandon proposal (any state → closed with win_result='abandoned').

        Used when internal decision is made not to pursue.

        Args:
            user_id: User abandoning
            reason: Why abandoned

        Returns:
            Timeline entry
        """
        metadata = {}
        if reason:
            metadata["reason"] = reason

        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.CLOSED,
            user_id=user_id,
            actor_type="user",
            reason=reason or "Proposal abandoned",
            metadata=metadata,
            win_result=WinResult.ABANDONED.value,
        )

    async def hold(
        self,
        user_id: str,
        reason: str = "",
    ) -> dict:
        """
        Pause proposal (any active state → on_hold).

        Can be resumed with resume().

        Args:
            user_id: User holding
            reason: Why held

        Returns:
            Timeline entry
        """
        metadata = {}
        if reason:
            metadata["reason"] = reason

        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.ON_HOLD,
            user_id=user_id,
            actor_type="user",
            reason=reason or "Proposal held",
            metadata=metadata,
        )

    async def resume(
        self,
        user_id: str,
        phase: Optional[str] = None,
    ) -> dict:
        """
        Resume held proposal (on_hold → waiting or in_progress).

        Args:
            user_id: User resuming
            phase: Resume to this phase (if any)

        Returns:
            Timeline entry
        """
        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.WAITING,
            current_phase=phase,
            user_id=user_id,
            actor_type="user",
            reason="Proposal resumed",
        )

    async def archive(
        self,
        user_id: Optional[str] = None,
    ) -> dict:
        """
        Archive closed proposal (closed → archived).

        Typically done 30 days after closure for record keeping.

        Args:
            user_id: User archiving (optional, defaults to 'system')

        Returns:
            Timeline entry
        """
        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.ARCHIVED,
            user_id=user_id,
            actor_type="system" if not user_id else "user",
            reason="Proposal archived",
        )

    async def mark_expired(
        self,
    ) -> dict:
        """
        Mark proposal as expired (any open state → expired).

        Automatically triggered when RFP deadline passes.

        Returns:
            Timeline entry
        """
        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.EXPIRED,
            actor_type="cron",
            reason="RFP deadline passed",
        )
