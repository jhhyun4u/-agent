"""
제안서 상태 머신 (Phase 2: Unified State System)

StateMachine: StateValidator를 래핑한 비즈니스 친화적 상태 관리
- start_workflow()     → waiting → in_progress
- complete_proposal()  → in_progress → completed
- submit_proposal()    → completed → submitted
- mark_presentation()  → submitted → presentation
- close_proposal()     → * → closed  (win_result 필수)
- hold_proposal()      → * → on_hold
- resume_proposal()    → on_hold → waiting / in_progress
- archive_proposal()   → closed / expired → archived

각 메서드는 StateValidator.transition()을 호출하여 상태 전환을 실행합니다.
"""

from typing import Optional
from app.services.state_validator import StateValidator, ProposalStatus, WinResult
import logging

logger = logging.getLogger(__name__)


class StateMachine:
    """
    제안서 상태 머신 (비즈니스 레벨 상태 관리)

    BusinessStatus (Layer 1): proposals.status — 10개 통합 상태
    └─ waiting → in_progress → completed → submitted → presentation → closed
       on_hold ↔ waiting/in_progress/closed
       expired → archived
       closed → archived

    WorkflowPhase (Layer 2): proposals.current_phase
    └─ start, rfp_fetch, rfp_analyze, research_gather, go_no_go, ...

    AIRuntime (Layer 3): ai_task_status 테이블 (독립 관리)
    └─ running, complete, error, paused, no_response
    """

    def __init__(self, proposal_id: str):
        """Initialize state machine for a proposal

        Args:
            proposal_id: UUID of the proposal
        """
        self.proposal_id = proposal_id

    async def start_workflow(
        self,
        user_id: str,
        initial_phase: str = "rfp_analyze",
    ) -> dict:
        """워크플로우 착수: waiting → in_progress

        Args:
            user_id: 사용자 ID (착수자)
            initial_phase: 시작 phase (기본값: rfp_analyze)

        Returns:
            timeline entry dict
        """
        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.IN_PROGRESS.value,
            current_phase=initial_phase,
            user_id=user_id,
            actor_type="user",
            reason="사용자가 제안서 작업 착수",
        )

    async def complete_proposal(
        self,
        user_id: Optional[str] = None,
        notes: str = "",
    ) -> dict:
        """내부 완성: in_progress → completed

        Args:
            user_id: 완성 처리자 ID
            notes: 코멘트

        Returns:
            timeline entry dict
        """
        metadata = {"notes": notes} if notes else {}

        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.COMPLETED.value,
            current_phase="completed",
            user_id=user_id,
            actor_type="workflow" if not user_id else "user",
            reason="제안서 내부 완성",
            metadata=metadata,
        )

    async def submit_proposal(
        self,
        user_id: str,
        submission_type: str = "email",
    ) -> dict:
        """제안서 제출: completed → submitted

        Args:
            user_id: 제출자 ID
            submission_type: 제출 방식 (email, portal, hand_delivery 등)

        Returns:
            timeline entry dict
        """
        metadata = {
            "submission_type": submission_type,
        }

        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.SUBMITTED.value,
            current_phase="submitted",
            user_id=user_id,
            actor_type="user",
            reason="제안서 제출",
            metadata=metadata,
        )

    async def mark_presentation(
        self,
        user_id: str,
        presentation_date: Optional[str] = None,
    ) -> dict:
        """프레젠테이션/입찰 진행: submitted → presentation

        Args:
            user_id: 기록자 ID
            presentation_date: 프레젠테이션 날짜 (ISO format)

        Returns:
            timeline entry dict
        """
        metadata: dict = {}
        if presentation_date:
            metadata["presentation_date"] = presentation_date

        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.PRESENTATION.value,
            current_phase="presentation",
            user_id=user_id,
            actor_type="user",
            reason="프레젠테이션/입찰 진행 기록",
            metadata=metadata,
        )

    async def close_proposal(
        self,
        user_id: str,
        win_result: str,
        reason: str = "",
        notes: str = "",
        contract_amount: Optional[float] = None,
        contract_date: Optional[str] = None,
    ) -> dict:
        """최종 종료: * → closed  (win_result 필수)

        Args:
            user_id: 기록자 ID
            win_result: 종료 세부 결과 (WinResult enum 값: won/lost/no_go/abandoned/cancelled)
            reason: 종료 이유
            notes: 상세 정보 및 교훈
            contract_amount: 계약금액 (수주 시)
            contract_date: 계약일 (수주 시, ISO format)

        Returns:
            timeline entry dict
        """
        # win_result 사전 검증
        try:
            wr = WinResult(win_result)
        except ValueError as e:
            raise ValueError(
                f"알 수 없는 win_result: {win_result}. 허용: {[w.value for w in WinResult]}"
            ) from e

        metadata: dict = {
            "win_result": win_result,
            "notes": notes,
        }
        if contract_amount is not None:
            metadata["contract_amount"] = contract_amount
        if contract_date:
            metadata["contract_date"] = contract_date

        log_label = {
            WinResult.WON: "CONTRACT_WON",
            WinResult.LOST: "CONTRACT_LOST",
            WinResult.NO_GO: "NO_GO_DECISION",
            WinResult.ABANDONED: "ABANDONED",
            WinResult.CANCELLED: "CANCELLED",
        }.get(wr, "CLOSED")

        logger.info(f"[{log_label}] proposal_id={self.proposal_id}, win_result={win_result}")

        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.CLOSED.value,
            user_id=user_id,
            actor_type="user",
            reason=reason or f"종료: {win_result}",
            metadata=metadata,
            win_result=win_result,
        )

    async def hold_proposal(
        self,
        user_id: str,
        reason: str = "",
    ) -> dict:
        """일시 보류: * → on_hold

        Args:
            user_id: 보류 처리자 ID
            reason: 보류 사유

        Returns:
            timeline entry dict
        """
        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.ON_HOLD.value,
            user_id=user_id,
            actor_type="user",
            reason=reason or "일시 보류",
        )

    async def resume_proposal(
        self,
        user_id: str,
        to_status: str = "waiting",
    ) -> dict:
        """보류 해제: on_hold → waiting / in_progress

        Args:
            user_id: 재개 처리자 ID
            to_status: 재개 후 상태 ('waiting' 또는 'in_progress')

        Returns:
            timeline entry dict
        """
        if to_status not in (ProposalStatus.WAITING.value, ProposalStatus.IN_PROGRESS.value):
            raise ValueError(f"보류 해제 후 상태는 'waiting' 또는 'in_progress'만 가능합니다. (요청: {to_status})")

        return await StateValidator.transition(
            self.proposal_id,
            to_status,
            user_id=user_id,
            actor_type="user",
            reason="보류 해제 및 재개",
        )

    async def archive_proposal(
        self,
        user_id: Optional[str] = None,
        reason: str = "",
    ) -> dict:
        """보관: closed / expired → archived

        Args:
            user_id: 처리자 ID (없으면 시스템 자동 처리)
            reason: 보관 사유

        Returns:
            timeline entry dict
        """
        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.ARCHIVED.value,
            user_id=user_id,
            actor_type="system" if not user_id else "user",
            reason=reason or "보관 처리 (30일 경과 자동)",
        )

    async def expire_proposal(
        self,
        reason: str = "마감일 초과",
    ) -> dict:
        """만료: waiting / in_progress → expired (시스템 자동)

        Args:
            reason: 만료 사유

        Returns:
            timeline entry dict
        """
        return await StateValidator.transition(
            self.proposal_id,
            ProposalStatus.EXPIRED.value,
            actor_type="system",
            reason=reason,
        )

    async def transition(
        self,
        to_status: str,
        current_phase: Optional[str] = None,
        user_id: Optional[str] = None,
        reason: Optional[str] = None,
        metadata: Optional[dict] = None,
        win_result: Optional[str] = None,
    ) -> dict:
        """직접 상태 전환 (고급 사용)

        이 메서드는 위의 편의 메서드들로 처리되지 않는 경우에만 사용하세요.

        Args:
            to_status: 전환할 상태 (ProposalStatus 값)
            current_phase: 현재 phase
            user_id: 사용자 ID
            reason: 전환 이유
            metadata: 추가 메타데이터
            win_result: 종료 세부 결과 (closed 전환 시 사용)

        Returns:
            timeline entry dict
        """
        return await StateValidator.transition(
            self.proposal_id,
            to_status,
            current_phase=current_phase,
            user_id=user_id,
            actor_type="user" if user_id else "workflow",
            reason=reason or f"상태 전환: {to_status}",
            metadata=metadata,
            win_result=win_result,
        )
