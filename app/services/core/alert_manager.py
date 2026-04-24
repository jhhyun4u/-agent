"""
자가검증 알림 매니저

- Teams Webhook 알림 발송
- DB health_check_logs 로깅
- 중복 알림 억제 (같은 check_id fail이 suppress_minutes 이내 반복 시 스킵)
"""

import logging
from datetime import datetime, timezone

from app.config import settings
from app.services.core.health_checker import HealthResult
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

_STATUS_ICON = {"pass": "🟢", "warn": "🟡", "fail": "🔴", "fixed": "🟢"}


class AlertManager:
    """검증 결과 → 알림 + DB 로깅 + 중복 억제"""

    def __init__(self):
        self._recent_fails: dict[str, datetime] = {}

    async def handle_results(self, results: list[HealthResult]) -> None:
        """결과 목록 처리: 모두 DB 로깅 + fail/fixed만 알림"""
        for r in results:
            await self._log_to_db(r)
            if r.status in ("fail", "fixed"):
                await self._maybe_alert(r)

    async def _log_to_db(self, r: HealthResult) -> None:
        try:
            client = await get_async_client()
            await client.table("health_check_logs").insert({
                "check_id": r.check_id,
                "category": r.category,
                "status": r.status,
                "message": r.message,
                "detail": r.detail,
                "auto_recovered": r.auto_recovered,
                "duration_ms": r.duration_ms,
            }).execute()
        except Exception as e:
            logger.warning(f"헬스체크 로그 저장 실패: {e}")

    async def _maybe_alert(self, r: HealthResult) -> None:
        now = datetime.now(timezone.utc)
        suppress_seconds = settings.health_suppress_minutes * 60

        # fixed는 항상 알림 (복구 확인)
        if r.status == "fixed":
            await self._send_teams_alert(r)
            self._recent_fails.pop(r.check_id, None)
            return

        # fail 중복 억제
        last = self._recent_fails.get(r.check_id)
        if last and (now - last).total_seconds() < suppress_seconds:
            logger.info(f"[Health] {r.check_id} fail 중복 억제 (마지막: {last.isoformat()})")
            return

        self._recent_fails[r.check_id] = now
        await self._send_teams_alert(r)

    async def _send_teams_alert(self, r: HealthResult) -> None:
        icon = _STATUS_ICON.get(r.status, "⚪")
        title = f"{icon} [{r.status.upper()}] {r.check_id}: 자가검증"
        body = r.message
        if r.auto_recovered:
            body += "\n자동 복구: ✅"
        if r.detail:
            detail_str = ", ".join(f"{k}={v}" for k, v in r.detail.items())
            body += f"\n상세: {detail_str}"

        try:
            from app.services.core.notification_service import send_teams_notification
            await send_teams_notification(team_id="", title=title, body=body)
        except Exception as e:
            logger.warning(f"[Health] Teams 알림 전송 실패: {e}")
