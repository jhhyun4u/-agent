"""
상태 전환 검증 및 실행 (Phase 2: Unified State System)

ProposalStatus enum: 10개의 통합 비즈니스 상태 (Layer 1)
WinResult enum: 종료 세부 결과 (closed 상태에서만 사용)
Valid transitions: from_state → [to_states] 규칙 정의
StateValidator: 상태 전환 검증 + timeline 로깅
"""

from typing import Optional
from enum import Enum
from datetime import datetime, timezone
from app.utils.supabase_client import get_async_client

import logging

logger = logging.getLogger(__name__)


class ProposalStatus(str, Enum):
    """제안서 비즈니스 상태 (Layer 1: Business Status) — 10개 통합 상태"""
    INITIALIZED  = "initialized"   # 0. 제안서 초기 생성 (미사용된 상태, waiting과 동일하게 취급)
    WAITING      = "waiting"       # 1. 생성 후 대기 (PM/PL 미할당 또는 착수 전)
    IN_PROGRESS  = "in_progress"   # 2. AI 워크플로우 진행 중 (RFP분석~제안서 완성)
    COMPLETED    = "completed"     # 3. 내부 완성 (제출 전 검토 완료)
    SUBMITTED    = "submitted"     # 4. 고객/발주기관에 제출됨
    PRESENTATION = "presentation"  # 5. 발표/입찰 진행 중
    CLOSED       = "closed"        # 6. 최종 종료 (win_result로 세부 구분)
    ARCHIVED     = "archived"      # 7. 보관 (closed 후 30일 경과)
    ON_HOLD      = "on_hold"       # 8. 일시 보류 (재개 가능)
    EXPIRED      = "expired"       # 9. 마감일 초과 자동 만료


class WinResult(str, Enum):
    """종료 세부 결과 (closed 상태에서만 사용)"""
    WON       = "won"       # 수주
    LOST      = "lost"      # 패찰 (미수주)
    NO_GO     = "no_go"     # 미진행 결정
    ABANDONED = "abandoned" # 중도 포기
    CANCELLED = "cancelled" # 취소


class StateValidator:
    """상태 전환 검증 및 실행 + timeline 로깅"""

    # 유효한 상태 전환: from_state → [to_states]
    VALID_TRANSITIONS: dict[ProposalStatus, list[ProposalStatus]] = {
        ProposalStatus.INITIALIZED:  [ProposalStatus.WAITING, ProposalStatus.IN_PROGRESS, ProposalStatus.CLOSED, ProposalStatus.EXPIRED, ProposalStatus.ON_HOLD],  # 기존 데이터 호환
        ProposalStatus.WAITING:      [ProposalStatus.IN_PROGRESS, ProposalStatus.CLOSED, ProposalStatus.EXPIRED, ProposalStatus.ON_HOLD],
        ProposalStatus.IN_PROGRESS:  [ProposalStatus.COMPLETED, ProposalStatus.CLOSED, ProposalStatus.ON_HOLD, ProposalStatus.EXPIRED],
        ProposalStatus.COMPLETED:    [ProposalStatus.SUBMITTED, ProposalStatus.CLOSED, ProposalStatus.ON_HOLD],
        ProposalStatus.SUBMITTED:    [ProposalStatus.PRESENTATION, ProposalStatus.CLOSED],
        ProposalStatus.PRESENTATION: [ProposalStatus.CLOSED],
        ProposalStatus.CLOSED:       [ProposalStatus.ARCHIVED],
        ProposalStatus.ARCHIVED:     [],          # Terminal state
        ProposalStatus.ON_HOLD:      [ProposalStatus.WAITING, ProposalStatus.IN_PROGRESS, ProposalStatus.CLOSED],
        ProposalStatus.EXPIRED:      [ProposalStatus.ARCHIVED],  # 만료 후 보관
    }

    @staticmethod
    async def validate_transition(
        proposal_id: str,
        from_status: str,
        to_status: str,
        actor_type: str = "workflow",
        reason: Optional[str] = None
    ) -> bool:
        """상태 전환이 유효한지 검증

        Args:
            proposal_id: 제안서 ID
            from_status: 현재 상태
            to_status: 전환할 상태
            actor_type: 전환을 트리거한 주체 ('user', 'workflow', 'system')
            reason: 전환 이유

        Returns:
            True if valid, raises ValueError if invalid

        Raises:
            ValueError: 알 수 없는 상태 또는 유효하지 않은 전환
        """
        # 알려진 상태 확인
        try:
            from_state = ProposalStatus(from_status)
            to_state = ProposalStatus(to_status)
        except ValueError as e:
            raise ValueError(f"알 수 없는 상태: {from_status} 또는 {to_status}") from e

        # 유효한 전환 확인
        allowed = StateValidator.VALID_TRANSITIONS.get(from_state, [])
        if to_state not in allowed:
            raise ValueError(
                f"유효하지 않은 전환: {from_status} → {to_status}. "
                f"허용된 상태: {[s.value for s in allowed]}"
            )

        return True

    @staticmethod
    async def transition(
        proposal_id: str,
        to_status: str,
        current_phase: Optional[str] = None,
        user_id: Optional[str] = None,
        actor_type: str = "workflow",
        reason: Optional[str] = None,
        metadata: Optional[dict] = None,
        win_result: Optional[str] = None,
    ) -> dict:
        """상태 전환 실행 + timeline 로깅

        Args:
            proposal_id: 제안서 ID
            to_status: 전환할 대상 상태 (ProposalStatus 값)
            current_phase: 현재 LangGraph phase (workflow phase)
            user_id: 전환을 트리거한 사용자 ID
            actor_type: 전환 주체 ('user', 'workflow', 'system', 'ai')
            reason: 전환 이유 (timeline에 기록됨)
            metadata: 추가 메타데이터 (JSONB)
            win_result: 종료 세부 결과 — closed 전환 시 필수 (WinResult 값)

        Returns:
            timeline entry dict

        Raises:
            ValueError: 유효하지 않은 상태 전환 또는 win_result 누락
        """
        client = await get_async_client()

        # 현재 상태 조회
        try:
            prop = await client.table("proposals").select("status, current_phase").eq("id", proposal_id).single().execute()
        except Exception as e:
            logger.error(f"제안서 조회 실패 (proposal_id={proposal_id}): {e}")
            raise ValueError(f"제안서를 찾을 수 없음: {proposal_id}") from e

        from_status = prop.data["status"]
        from_phase = prop.data.get("current_phase")

        # 상태 전환 검증
        await StateValidator.validate_transition(
            proposal_id, from_status, to_status, actor_type, reason
        )

        # closed 전환 시 win_result 유효성 검증
        if to_status == ProposalStatus.CLOSED.value:
            if win_result is None:
                raise ValueError("closed 상태로 전환할 때 win_result는 필수입니다. 허용값: won, lost, no_go, abandoned, cancelled")
            try:
                WinResult(win_result)
            except ValueError as e:
                raise ValueError(f"알 수 없는 win_result 값: {win_result}. 허용: {[w.value for w in WinResult]}") from e

        # proposals 테이블 업데이트
        try:
            now = datetime.now(timezone.utc).isoformat()
            update_data: dict = {
                "status": to_status,
                "last_activity_at": now,
            }

            # current_phase 설정
            if current_phase:
                update_data["current_phase"] = current_phase

            # win_result 설정 (closed 전환 시)
            if to_status == ProposalStatus.CLOSED.value and win_result is not None:
                update_data["win_result"] = win_result

            # 단계별 타임스탬프 자동 설정
            if to_status == ProposalStatus.IN_PROGRESS.value:
                update_data["started_at"] = now

            if to_status == ProposalStatus.COMPLETED.value:
                update_data["completed_at"] = now

            if to_status == ProposalStatus.SUBMITTED.value:
                update_data["submitted_at"] = now

            if to_status == ProposalStatus.PRESENTATION.value:
                update_data["presentation_started_at"] = now

            if to_status == ProposalStatus.CLOSED.value:
                update_data["closed_at"] = now

            if to_status == ProposalStatus.ARCHIVED.value:
                update_data["archived_at"] = now

            if to_status == ProposalStatus.EXPIRED.value:
                update_data["expired_at"] = now

            await client.table("proposals").update(update_data).eq("id", proposal_id).execute()
            logger.info(f"[STATE_CHANGE] {proposal_id}: {from_status} → {to_status}" + (f" (win_result={win_result})" if win_result else ""))
        except Exception as e:
            logger.error(f"제안서 상태 업데이트 실패 (proposal_id={proposal_id}): {e}")
            raise

        # proposal_timelines 테이블에 기록
        try:
            timeline_entry = {
                "proposal_id": proposal_id,
                "event_type": "status_change",
                "from_status": from_status,
                "to_status": to_status,
                "from_phase": from_phase,
                "to_phase": current_phase,
                "triggered_by": user_id,
                "actor_type": actor_type,
                "trigger_reason": reason,
                "metadata": {**(metadata or {}), **({"win_result": win_result} if win_result else {})},
            }

            result = await client.table("proposal_timelines").insert(timeline_entry).execute()
            logger.info(f"[TIMELINE_LOG] proposal_id={proposal_id}, event={timeline_entry['event_type']}")
            return result.data[0] if result.data else timeline_entry
        except Exception as e:
            logger.error(f"Timeline 로깅 실패 (proposal_id={proposal_id}): {e}")
            # Timeline 실패는 치명적이지 않으므로, 로그만 기록하고 계속 진행
            return timeline_entry

    @staticmethod
    async def get_valid_next_states(current_status: str) -> list[str]:
        """현재 상태에서 전환 가능한 다음 상태들 조회

        Args:
            current_status: 현재 상태값

        Returns:
            [다음_상태1, 다음_상태2, ...] 또는 빈 리스트 (terminal state)
        """
        try:
            status = ProposalStatus(current_status)
            allowed = StateValidator.VALID_TRANSITIONS.get(status, [])
            return [s.value for s in allowed]
        except ValueError:
            return []
