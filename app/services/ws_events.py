"""WebSocket 이벤트 발행자 (§26)

다른 서비스에서 호출하는 fire-and-forget 브로드캐스트 함수들.
"""

import logging

from app.models.ws_schemas import (
    WsMessage,
    ProposalStatusUpdate,
    MonthlyTrendsUpdate,
    TeamPerformanceUpdate,
    NotificationPayload,
)
from app.services.ws_manager import ws_manager

logger = logging.getLogger(__name__)


async def broadcast_proposal_status(
    proposal_id: str,
    old_status: str | None,
    new_status: str,
    title: str | None,
    team_id: str | None,
    division_id: str | None,
    org_id: str,
) -> None:
    """제안서 상태 변경 브로드캐스트
    
    팀/본부/전사 범위별로 스코프에 맞게 발송.
    """
    try:
        data = ProposalStatusUpdate(
            proposal_id=proposal_id,
            old_status=old_status,
            new_status=new_status,
            title=title,
        )

        # 팀 범위 (이 제안서의 팀멤버)
        if team_id:
            team_msg = WsMessage(
                type="proposal_status",
                channel=f"team:{team_id}",
                data=data.model_dump(),
            )
            await ws_manager.broadcast(f"team:{team_id}", team_msg)

        # 본부 범위
        if division_id:
            div_msg = WsMessage(
                type="proposal_status",
                channel=f"division:{division_id}",
                data=data.model_dump(),
            )
            await ws_manager.broadcast(f"division:{division_id}", div_msg)

        # 전사 범위
        company_msg = WsMessage(
            type="proposal_status",
            channel=f"company:{org_id}",
            data=data.model_dump(),
        )
        await ws_manager.broadcast(f"company:{org_id}", company_msg)

        logger.debug(
            f"[WS] 제안서 상태 변경 브로드캐스트: {proposal_id} "
            f"({old_status} → {new_status})"
        )
    except Exception as e:
        logger.error(f"[WS] 제안서 상태 브로드캐스트 실패: {e}")


async def broadcast_result_update(
    team_id: str | None,
    division_id: str | None,
    org_id: str,
) -> None:
    """결과 기록 후 분석 데이터 갱신 신호
    
    클라이언트는 이 신호를 받으면 analytics/stats를 다시 로드.
    """
    try:
        data = MonthlyTrendsUpdate(
            team_id=team_id,
            division_id=division_id,
            org_id=org_id,
        )

        # 팀 범위
        if team_id:
            team_msg = WsMessage(
                type="monthly_trends",
                channel=f"team:{team_id}",
                data=data.model_dump(),
            )
            await ws_manager.broadcast(f"team:{team_id}", team_msg)

        # 본부 범위
        if division_id:
            div_msg = WsMessage(
                type="monthly_trends",
                channel=f"division:{division_id}",
                data=data.model_dump(),
            )
            await ws_manager.broadcast(f"division:{division_id}", div_msg)

        # 전사 범위
        company_msg = WsMessage(
            type="monthly_trends",
            channel=f"company:{org_id}",
            data=data.model_dump(),
        )
        await ws_manager.broadcast(f"company:{org_id}", company_msg)

        logger.debug("[WS] 결과 업데이트 신호 브로드캐스트")
    except Exception as e:
        logger.error(f"[WS] 결과 업데이트 브로드캐스트 실패: {e}")


async def broadcast_team_performance(
    team_id: str,
    division_id: str | None,
    org_id: str,
    performance_data: dict,
) -> None:
    """팀 성과 지표 업데이트"""
    try:
        data = TeamPerformanceUpdate(
            team_id=team_id,
            total=performance_data.get("total", 0),
            won=performance_data.get("won", 0),
            lost=performance_data.get("lost", 0),
            win_rate=performance_data.get("win_rate", 0.0),
        )

        # 팀 범위
        team_msg = WsMessage(
            type="team_performance",
            channel=f"team:{team_id}",
            data=data.model_dump(),
        )
        await ws_manager.broadcast(f"team:{team_id}", team_msg)

        # 본부 범위 (본부장이 팀별 성과를 본다)
        if division_id:
            div_msg = WsMessage(
                type="team_performance",
                channel=f"division:{division_id}",
                data=data.model_dump(),
            )
            await ws_manager.broadcast(f"division:{division_id}", div_msg)

        # 전사 범위
        company_msg = WsMessage(
            type="team_performance",
            channel=f"company:{org_id}",
            data=data.model_dump(),
        )
        await ws_manager.broadcast(f"company:{org_id}", company_msg)

        logger.debug(f"[WS] 팀 성과 업데이트: {team_id}")
    except Exception as e:
        logger.error(f"[WS] 팀 성과 브로드캐스트 실패: {e}")


async def broadcast_notification(
    user_id: str,
    notification_id: str,
    notification_type: str,
    title: str,
    message: str,
    link: str | None = None,
) -> None:
    """특정 사용자에게 알림 발송 (채널 무관, 직접 전달)"""
    try:
        data = NotificationPayload(
            notification_id=notification_id,
            user_id=user_id,
            type=notification_type,
            title=title,
            message=message,
            link=link,
        )

        msg = WsMessage(
            type="notification",
            channel=f"user:{user_id}",
            data=data.model_dump(),
        )

        await ws_manager.broadcast_to_user(user_id, msg)
        logger.debug(f"[WS] 알림 발송: {user_id} ({notification_type})")
    except Exception as e:
        logger.error(f"[WS] 알림 브로드캐스트 실패: {e}")


async def broadcast_error(
    channel: str,
    code: str,
    message: str,
    details: dict | None = None,
) -> None:
    """채널에 에러 메시지 발송"""
    try:
        msg = WsMessage(
            type="error",
            channel=channel,
            data={
                "code": code,
                "message": message,
                "details": details or {},
            },
        )

        await ws_manager.broadcast(channel, msg)
        logger.warning(f"[WS] 에러 메시지 발송: {channel} ({code})")
    except Exception as e:
        logger.error(f"[WS] 에러 브로드캐스트 실패: {e}")
