"""
AI 작업 상태 관리 서비스 (§22)

노드 실행 상태 추적, 하트비트 모니터링, SSE 이벤트 발행.
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Literal

from app.config import settings
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

HEARTBEAT_TIMEOUT = settings.heartbeat_timeout_seconds  # (AGT-08)

StatusType = Literal[
    "running", "complete", "error", "paused", "no_response", "waiting_approval"
]


class AiStatusManager:
    """제안서별 AI 작업 상태 추적.

    메모리 기반 (서버 재시작 시 초기화). DB에는 완료/오류 시 기록.
    """

    def __init__(self) -> None:
        self._statuses: dict[str, dict[str, Any]] = {}
        self._listeners: list = []

    def start_task(
        self,
        proposal_id: str,
        step: str,
        sub_tasks: list[str] | None = None,
    ) -> dict[str, Any]:
        """새 AI 작업 시작 등록."""
        now = time.time()
        sub_task_map = {}
        for st in (sub_tasks or []):
            sub_task_map[st] = {
                "status": "pending",
                "started_at": None,
                "completed_at": None,
                "duration_ms": None,
            }

        status = {
            "status": "running",
            "step": step,
            "sub_tasks": sub_task_map,
            "progress_pct": 0,
            "started_at": now,
            "last_heartbeat": now,
            "error": None,
        }
        self._statuses[proposal_id] = status
        logger.info(f"AI 작업 시작: {proposal_id}/{step}")
        self._emit_status_change(proposal_id, "running")
        return status

    def update_sub_task(
        self,
        proposal_id: str,
        sub_task: str,
        status: StatusType,
    ) -> dict[str, Any] | None:
        """서브태스크 상태 업데이트 + 진행률 자동 재계산."""
        task = self._statuses.get(proposal_id)
        if not task:
            return None

        if sub_task in task["sub_tasks"]:
            st = task["sub_tasks"][sub_task]
            now = time.time()

            if status == "running" and st["started_at"] is None:
                st["started_at"] = now
            elif status in ("complete", "error"):
                st["completed_at"] = now
                if st["started_at"]:
                    st["duration_ms"] = int((now - st["started_at"]) * 1000)

            st["status"] = status

        # 진행률 재계산
        self._recalculate_progress(proposal_id)
        task["last_heartbeat"] = time.time()
        return task

    def heartbeat(self, proposal_id: str) -> bool:
        """하트비트 갱신. 존재하면 True."""
        task = self._statuses.get(proposal_id)
        if not task:
            return False
        task["last_heartbeat"] = time.time()
        return True

    def check_heartbeat(self, proposal_id: str) -> bool:
        """하트비트 타임아웃 확인. True = 정상, False = 무응답."""
        task = self._statuses.get(proposal_id)
        if not task:
            return False
        elapsed = time.time() - task["last_heartbeat"]
        if elapsed > HEARTBEAT_TIMEOUT:
            task["status"] = "no_response"
            logger.warning(
                f"AI 무응답 감지: {proposal_id} ({elapsed:.0f}초 초과)"
            )
            return False
        return True

    def complete_task(self, proposal_id: str) -> dict[str, Any] | None:
        """작업 정상 완료."""
        task = self._statuses.get(proposal_id)
        if not task:
            return None
        task["status"] = "complete"
        task["progress_pct"] = 100
        logger.info(f"AI 작업 완료: {proposal_id}/{task['step']}")
        self._emit_status_change(proposal_id, "complete")
        return task

    def fail_task(
        self, proposal_id: str, error_message: str
    ) -> dict[str, Any] | None:
        """작업 오류 처리."""
        task = self._statuses.get(proposal_id)
        if not task:
            return None
        task["status"] = "error"
        task["error"] = error_message
        logger.error(f"AI 작업 오류: {proposal_id}/{task['step']}: {error_message}")
        self._emit_status_change(proposal_id, "error")
        return task

    def pause_task(self, proposal_id: str) -> dict[str, Any] | None:
        """작업 일시정지 (사용자 승인 대기)."""
        task = self._statuses.get(proposal_id)
        if not task:
            return None
        task["status"] = "waiting_approval"
        return task

    def abort_task(self, proposal_id: str) -> dict[str, Any] | None:
        """작업 중단 — 상태를 'paused'로 전환하고 완료된 서브태스크 보존."""
        task = self._statuses.get(proposal_id)
        if not task:
            return None
        task["status"] = "paused"
        # 미완료 서브태스크 중단 표시 (complete/error는 보존)
        for st in task["sub_tasks"].values():
            if st["status"] in ("running", "pending"):
                st["status"] = "paused"
        logger.info(f"AI 작업 중단(paused): {proposal_id}/{task['step']}")
        self._emit_status_change(proposal_id, "paused")
        return task

    def get_composite_status(self, proposal_id: str) -> dict[str, Any]:
        """제안서의 전체 AI 상태 조회."""
        task = self._statuses.get(proposal_id)
        if not task:
            return {"status": "idle", "step": None, "progress_pct": 0}

        # 하트비트 점검
        self.check_heartbeat(proposal_id)

        elapsed_ms = int((time.time() - task["started_at"]) * 1000)
        return {
            "status": task["status"],
            "step": task["step"],
            "sub_tasks": task["sub_tasks"],
            "progress_pct": task["progress_pct"],
            "elapsed_ms": elapsed_ms,
            "error": task["error"],
        }

    def _recalculate_progress(self, proposal_id: str) -> None:
        """서브태스크 완료 비율로 진행률 재계산.

        설계(SS22) 기준: "complete" 상태만 완료로 계산. "error"는 미완료로 처리.
        """
        task = self._statuses.get(proposal_id)
        if not task or not task["sub_tasks"]:
            return
        total = len(task["sub_tasks"])
        done = sum(
            1
            for st in task["sub_tasks"].values()
            if st["status"] == "complete"
        )
        task["progress_pct"] = int(done / total * 100) if total > 0 else 0

    def _emit_status_change(self, proposal_id: str, new_status: str) -> None:
        """상태 변경 이벤트 발행 (SSE 연동 또는 콜백).

        등록된 리스너에 상태 변경을 알린다.
        """
        for listener in self._listeners:
            try:
                listener(proposal_id, new_status)
            except Exception as e:
                logger.warning(f"상태 변경 리스너 오류: {e}")

    def add_listener(self, callback) -> None:
        """상태 변경 리스너 등록."""
        self._listeners.append(callback)

    def remove_listener(self, callback) -> None:
        """상태 변경 리스너 제거."""
        if callback in self._listeners:
            self._listeners.remove(callback)

    async def persist_log(
        self,
        proposal_id: str,
        step: str,
        status: StatusType,
        duration_ms: int = 0,
        input_tokens: int = 0,
        output_tokens: int = 0,
        model: str = "",
        error_message: str = "",
    ) -> None:
        """ai_task_logs 테이블에 상태 기록."""
        try:
            client = await get_async_client()
            row: dict[str, Any] = {
                "proposal_id": proposal_id,
                "step": step,
                "status": status,
                "duration_ms": duration_ms,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "model": model,
            }
            if error_message:
                row["error_message"] = error_message
            if status in ("complete", "error"):
                row["completed_at"] = datetime.now(timezone.utc).isoformat()

            await client.table("ai_task_logs").insert(row).execute()
        except Exception as e:
            logger.warning(f"ai_task_log 기록 실패: {e}")


# 싱글턴
ai_status_manager = AiStatusManager()
