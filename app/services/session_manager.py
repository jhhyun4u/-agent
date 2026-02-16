"""제안서 세션 관리 서비스"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from app.exceptions import SessionNotFoundError

logger = logging.getLogger(__name__)


class ProposalSessionManager:
    """제안서 세션 관리자 (메모리 기반)"""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(
        self,
        proposal_id: str,
        initial_data: Dict[str, Any],
        session_type: str = "v3",
    ) -> Dict[str, Any]:
        """
        새 세션 생성

        Args:
            proposal_id: 제안서 ID
            initial_data: 초기 데이터
            session_type: 세션 타입 (v3, v3.1, legacy)

        Returns:
            생성된 세션 데이터
        """
        session_data = {
            **initial_data,
            "proposal_id": proposal_id,
            "session_type": session_type,
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "status": "initialized",
        }

        self._sessions[proposal_id] = session_data
        logger.info(f"세션 생성: {proposal_id} (type={session_type})")

        return session_data

    def get_session(self, proposal_id: str) -> Dict[str, Any]:
        """
        세션 조회

        Args:
            proposal_id: 제안서 ID

        Returns:
            세션 데이터

        Raises:
            SessionNotFoundError: 세션을 찾을 수 없는 경우
        """
        session = self._sessions.get(proposal_id)
        if not session:
            raise SessionNotFoundError(
                f"제안서를 찾을 수 없습니다: {proposal_id}",
                details={"proposal_id": proposal_id}
            )
        return session

    def update_session(
        self,
        proposal_id: str,
        updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        세션 업데이트

        Args:
            proposal_id: 제안서 ID
            updates: 업데이트할 데이터

        Returns:
            업데이트된 세션 데이터

        Raises:
            SessionNotFoundError: 세션을 찾을 수 없는 경우
        """
        session = self.get_session(proposal_id)
        session.update(updates)
        session["updated_at"] = datetime.now()

        logger.info(f"세션 업데이트: {proposal_id}")
        return session

    def delete_session(self, proposal_id: str) -> None:
        """
        세션 삭제

        Args:
            proposal_id: 제안서 ID

        Raises:
            SessionNotFoundError: 세션을 찾을 수 없는 경우
        """
        if proposal_id not in self._sessions:
            raise SessionNotFoundError(
                f"제안서를 찾을 수 없습니다: {proposal_id}",
                details={"proposal_id": proposal_id}
            )

        del self._sessions[proposal_id]
        logger.info(f"세션 삭제: {proposal_id}")

    def list_sessions(
        self,
        session_type: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        세션 목록 조회

        Args:
            session_type: 세션 타입 필터 (선택)

        Returns:
            세션 딕셔너리
        """
        if session_type:
            return {
                pid: session
                for pid, session in self._sessions.items()
                if session.get("session_type") == session_type
            }
        return self._sessions.copy()

    def session_exists(self, proposal_id: str) -> bool:
        """
        세션 존재 여부 확인

        Args:
            proposal_id: 제안서 ID

        Returns:
            존재 여부
        """
        return proposal_id in self._sessions

    def get_session_count(self, session_type: Optional[str] = None) -> int:
        """
        세션 개수 조회

        Args:
            session_type: 세션 타입 필터 (선택)

        Returns:
            세션 개수
        """
        if session_type:
            return sum(
                1 for s in self._sessions.values()
                if s.get("session_type") == session_type
            )
        return len(self._sessions)


# 전역 세션 매니저 인스턴스
session_manager = ProposalSessionManager()
