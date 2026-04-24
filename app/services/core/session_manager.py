"""제안서 세션 관리 서비스 (메모리 + Supabase DB 영속화)"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from app.exceptions import SessionNotFoundError

logger = logging.getLogger(__name__)

# proposals 테이블에 저장할 필드 목록
_DB_FIELDS = {
    "rfp_title": "title",          # session key → DB 컬럼명
    "client_name": "notes",        # notes 컬럼에 보조 저장
    "status": "status",
    "current_phase": "current_phase",
    "phases_completed": "phases_completed",
    "failed_phase": "failed_phase",
    "docx_path": "storage_path_docx",
    "pptx_path": "storage_path_pptx",
}


def _to_db_payload(session: Dict[str, Any]) -> Dict[str, Any]:
    """세션 데이터 → proposals 테이블 업데이트 페이로드 변환"""
    payload: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
    for session_key, db_col in _DB_FIELDS.items():
        if session_key in session:
            val = session[session_key]
            # datetime은 ISO 문자열로
            if isinstance(val, datetime):
                val = val.isoformat()
            payload[db_col] = val
    return payload


def _from_db_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """proposals DB 행 → 세션 데이터 변환"""
    return {
        "proposal_id": row.get("id"),
        "rfp_title": row.get("title", ""),
        "status": row.get("status", "initialized"),
        "current_phase": row.get("current_phase"),
        "phases_completed": row.get("phases_completed", 0),
        "failed_phase": row.get("failed_phase"),
        "owner_id": row.get("owner_id"),
        "team_id": row.get("team_id"),
        "docx_path": row.get("storage_path_docx", ""),
        "pptx_path": row.get("storage_path_pptx", ""),
        "rfp_content": row.get("rfp_content", ""),
        "created_at": row.get("created_at") or datetime.now(timezone.utc),
        "updated_at": row.get("updated_at") or datetime.now(timezone.utc),
        "session_type": "v3.1",
        "proposal_state": {
            "rfp_title": row.get("title", ""),
            "rfp_content": row.get("rfp_content", ""),
        },
    }


class ProposalSessionManager:
    """제안서 세션 관리자 (메모리 캐시 + Supabase DB write-through)"""

    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    # ─────────────────────────────────────────────
    # 동기 메서드 (기존 인터페이스 유지)
    # phase_executor.py 등 내부에서 사용
    # ─────────────────────────────────────────────

    def create_session(
        self,
        proposal_id: str,
        initial_data: Dict[str, Any],
        session_type: str = "v3",
    ) -> Dict[str, Any]:
        """새 세션 생성 (메모리 + DB write-through)"""
        session_data = {
            **initial_data,
            "proposal_id": proposal_id,
            "session_type": session_type,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "status": "initialized",
        }
        self._sessions[proposal_id] = session_data
        logger.info(f"세션 생성: {proposal_id} (type={session_type})")

        # DB 비동기 저장 (fire-and-forget)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._db_create(proposal_id, session_data))
        except RuntimeError:
            pass  # 이벤트 루프 없으면 스킵

        return session_data

    async def acreate_session(
        self,
        proposal_id: str,
        initial_data: Dict[str, Any],
        session_type: str = "v3",
    ) -> Dict[str, Any]:
        """새 세션 생성 — DB INSERT 먼저 (ghost session 방지).

        설계 요구: DB INSERT 성공 후 인메모리 캐시에 추가.
        DB 실패 시 세션이 생성되지 않아 ghost session을 방지한다.
        """
        session_data = {
            **initial_data,
            "proposal_id": proposal_id,
            "session_type": session_type,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
            "status": "initialized",
        }

        # DB INSERT 먼저 (실패 시 예외 전파 → ghost session 방지)
        await self._db_create(proposal_id, session_data)

        # DB 성공 후 인메모리 캐시에 추가
        self._sessions[proposal_id] = session_data
        logger.info(f"세션 생성 (DB-first): {proposal_id} (type={session_type})")

        return session_data

    def get_session(self, proposal_id: str) -> Dict[str, Any]:
        """세션 조회 (메모리 전용, 빠른 읽기)"""
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
        """세션 업데이트 (메모리 + DB write-through)"""
        session = self.get_session(proposal_id)
        session.update(updates)
        session["updated_at"] = datetime.now(timezone.utc)

        # DB 비동기 업데이트 (fire-and-forget)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._db_update(proposal_id, session))
        except RuntimeError:
            pass

        logger.debug(f"세션 업데이트: {proposal_id} keys={list(updates.keys())}")
        return session

    def delete_session(self, proposal_id: str) -> None:
        """세션 삭제"""
        if proposal_id not in self._sessions:
            raise SessionNotFoundError(
                f"제안서를 찾을 수 없습니다: {proposal_id}",
                details={"proposal_id": proposal_id}
            )
        del self._sessions[proposal_id]
        logger.info(f"세션 삭제(메모리): {proposal_id}")

    def list_sessions(
        self,
        session_type: Optional[str] = None
    ) -> Dict[str, Dict[str, Any]]:
        """세션 목록 조회"""
        if session_type:
            return {
                pid: s for pid, s in self._sessions.items()
                if s.get("session_type") == session_type
            }
        return self._sessions.copy()

    def session_exists(self, proposal_id: str) -> bool:
        """메모리 기준 세션 존재 여부"""
        return proposal_id in self._sessions

    def get_session_count(self, session_type: Optional[str] = None) -> int:
        """세션 개수"""
        if session_type:
            return sum(1 for s in self._sessions.values() if s.get("session_type") == session_type)
        return len(self._sessions)

    # ─────────────────────────────────────────────
    # 비동기 메서드 (DB 폴백 포함)
    # routes_v31.py async 엔드포인트에서 사용
    # ─────────────────────────────────────────────

    async def aget_session(self, proposal_id: str) -> Dict[str, Any]:
        """세션 조회 — 메모리 우선, 없으면 DB에서 로드"""
        if proposal_id in self._sessions:
            return self._sessions[proposal_id]

        # DB 폴백
        session = await self._db_load_session(proposal_id)
        if session is None:
            raise SessionNotFoundError(
                f"제안서를 찾을 수 없습니다: {proposal_id}",
                details={"proposal_id": proposal_id}
            )
        # 메모리 캐시에 복원
        self._sessions[proposal_id] = session
        logger.info(f"DB에서 세션 복원: {proposal_id}")
        return session

    async def mark_expired_proposals(self) -> int:
        """PSM-05: 마감일이 지난 진행중 제안서를 expired로 자동 전환 (StateMachine 사용)."""
        try:
            from app.utils.supabase_client import get_async_client
            from app.state_machine import StateMachine
            from app.services.domains.proposal.state_validator import ProposalStatus

            client = await get_async_client()

            # deadline 컬럼 존재 확인
            try:
                await client.table("proposals").select("deadline").limit(0).execute()
            except Exception:
                logger.info("mark_expired_proposals: deadline 컬럼 미존재 — 스킵")
                return 0

            # 만료 가능 상태: initialized, waiting, in_progress
            expirable_statuses = [
                ProposalStatus.INITIALIZED.value,
                ProposalStatus.WAITING.value,
                ProposalStatus.IN_PROGRESS.value,
            ]

            now = datetime.now(timezone.utc).isoformat()

            # 만료된 제안서 조회
            result = await client.table("proposals").select("id").in_(
                "status", expirable_statuses
            ).lt("deadline", now).execute()

            expired_proposals = result.data or []
            count = 0

            if not expired_proposals:
                return 0

            # 각 제안서에 StateMachine.expire_proposal() 호출 (병렬 처리, 동시성 제한 Semaphore(10))
            async def _expire_single(proposal_id: str, semaphore: asyncio.Semaphore) -> bool:
                """단일 제안서 만료 처리"""
                async with semaphore:
                    try:
                        sm = StateMachine(proposal_id)
                        await sm.expire_proposal()
                        logger.info(f"[EXPIRED] proposal_id={proposal_id} 만료 처리 완료")
                        return True
                    except Exception as e:
                        logger.warning(f"[EXPIRED] proposal_id={proposal_id} 만료 처리 실패: {e}")
                        return False

            # Semaphore(10): 최대 10개 동시 작업 제한
            semaphore = asyncio.Semaphore(10)
            tasks = [
                _expire_single(row["id"], semaphore)
                for row in expired_proposals
                if row.get("id")
            ]

            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=False)
                count = sum(1 for r in results if r)
                if count:
                    logger.info(f"PSM-05: 마감 초과 제안서 {count}건 expired 전환 완료")

            return count
        except Exception as e:
            logger.warning(f"mark_expired_proposals 실패 (무시): {e}")
            return 0

    async def startup_load(self) -> int:
        """앱 시작 시 DB에서 활성 세션 로드 (processing/initialized 상태)"""
        try:
            from app.utils.supabase_client import get_async_client
            client = await get_async_client()
            result = await (
                client.table("proposals")
                .select("*")
                .in_("status", ["initialized", "processing"])
                .execute()
            )
            rows = result.data or []
            for row in rows:
                pid = row.get("id")
                if pid and pid not in self._sessions:
                    self._sessions[pid] = _from_db_row(row)
            logger.info(f"DB에서 세션 {len(rows)}개 복원 완료")
            return len(rows)
        except Exception as e:
            logger.warning(f"startup_load 실패 (무시): {e}")
            return 0

    # ─────────────────────────────────────────────
    # 내부 DB 헬퍼 (비동기)
    # ─────────────────────────────────────────────

    async def _db_create(self, proposal_id: str, session: Dict[str, Any]) -> None:
        """proposals 테이블에 신규 행 삽입.

        acreate_session에서 호출 시 예외가 전파되어 ghost session을 방지한다.
        create_session(동기)에서 fire-and-forget으로 호출 시 예외는 로그만 남긴다.
        """
        from app.utils.supabase_client import get_async_client

        payload = {
            "id": proposal_id,
            "title": session.get("rfp_title", "제목 없음"),
            "status": "initialized",
            "owner_id": session.get("owner_id"),
            "team_id": session.get("team_id"),
            "rfp_content": session.get("proposal_state", {}).get("rfp_content", ""),
            "current_phase": None,
            "phases_completed": 0,
        }
        if session.get("section_ids") is not None:
            payload["section_ids"] = session["section_ids"]
        if session.get("form_template_id") is not None:
            payload["form_template_id"] = session["form_template_id"]
        # owner_id가 없으면 삽입 스킵 (RLS 위반 방지)
        if not payload["owner_id"]:
            logger.debug(f"_db_create 스킵 (owner_id 없음): {proposal_id}")
            return
        try:
            client = await get_async_client()
            await client.table("proposals").insert(payload).execute()
            logger.debug(f"DB 세션 생성: {proposal_id}")
        except Exception as e:
            logger.warning(f"_db_create 실패: {e}")
            raise

    async def _db_update(self, proposal_id: str, session: Dict[str, Any]) -> None:
        """proposals 테이블 업데이트"""
        try:
            from app.utils.supabase_client import get_async_client
            client = await get_async_client()
            payload = _to_db_payload(session)
            await (
                client.table("proposals")
                .update(payload)
                .eq("id", proposal_id)
                .execute()
            )
        except Exception as e:
            logger.warning(f"_db_update 실패 (무시): {e}")

    async def _db_load_session(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """DB에서 단일 세션 로드"""
        try:
            from app.utils.supabase_client import get_async_client
            client = await get_async_client()
            result = await (
                client.table("proposals")
                .select("*")
                .eq("id", proposal_id)
                .single()
                .execute()
            )
            if result.data:
                return _from_db_row(result.data)
        except Exception as e:
            logger.warning(f"_db_load_session 실패 (무시): {e}")
        return None


# 전역 세션 매니저 인스턴스
session_manager = ProposalSessionManager()
