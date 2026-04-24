"""WebSocket 라우트 (§26)

/api/ws/dashboard 엔드포인트: 클라이언트 연결, 채널 구독, 메시지 수신.
"""

import json
import logging

from fastapi import APIRouter, WebSocketException
from starlette.websockets import WebSocket

from app.models.ws_schemas import WsMessage, WsSubscribeMessage
from app.services.core.ws_manager import ws_manager
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

router = APIRouter()


async def _authenticate_ws(token: str | None) -> dict:
    """WebSocket 토큰 인증
    
    Returns:
        {user_id, org_id, team_id, division_id, role}
    
    Raises:
        WebSocketException: 인증 실패
    """
    if not token:
        raise WebSocketException(code=4001, reason="Unauthorized: no token")

    try:
        client = await get_async_client()
        response = await client.auth.get_user(token)
        user_auth = response.user
    except Exception:
        raise WebSocketException(code=4001, reason="Unauthorized: invalid token")

    if not user_auth:
        raise WebSocketException(code=4001, reason="Unauthorized: no user")

    # DB에서 프로필 조회
    try:
        profile = (
            await client.table("users")
            .select("id, email, name, role, org_id, team_id, division_id, status")
            .eq("id", str(user_auth.id))
            .single()
            .execute()
        )
        if not profile.data:
            raise WebSocketException(code=4001, reason="Unauthorized: no profile")

        return {
            "user_id": profile.data["id"],
            "org_id": profile.data["org_id"],
            "team_id": profile.data.get("team_id"),
            "division_id": profile.data.get("division_id"),
            "role": profile.data.get("role", "member"),
        }
    except WebSocketException:
        raise
    except Exception as e:
        logger.error(f"[WS] 프로필 조회 실패: {e}")
        raise WebSocketException(code=4001, reason="Unauthorized: profile lookup failed")


def _resolve_initial_channels(user_data: dict) -> set[str]:
    """사용자의 역할에 따라 초기 구독 채널 결정"""
    channels = set()
    role = user_data["role"]
    org_id = user_data["org_id"]
    team_id = user_data.get("team_id")
    division_id = user_data.get("division_id")

    # 팀 채널 (모든 역할이 구독)
    if team_id:
        channels.add(f"team:{team_id}")

    # 본부 채널 (director+)
    if division_id and role in ("director", "executive", "admin"):
        channels.add(f"division:{division_id}")

    # 전사 채널 (executive+)
    if role in ("executive", "admin"):
        channels.add(f"company:{org_id}")

    return channels


@router.websocket("/api/ws/dashboard")
async def websocket_dashboard(websocket: WebSocket):
    """대시보드 실시간 업데이트 WebSocket 엔드포인트
    
    클라이언트는 쿼리 파라미터로 JWT 토큰을 전달:
    ws://localhost:8000/api/ws/dashboard?token=<jwt>
    
    메시지 포맷:
    {
        "action": "subscribe" | "unsubscribe",
        "channel": "team:<id>" | "division:<id>" | "company:<id>"
    }
    """

    # 토큰 추출
    token = websocket.query_params.get("token")

    # 인증
    try:
        user_data = await _authenticate_ws(token)
    except WebSocketException as e:
        logger.warning(f"[WS] 인증 실패: {e.reason}")
        await websocket.close(code=e.code, reason=e.reason)
        return

    user_id = user_data["user_id"]

    # 초기 채널 결정
    initial_channels = _resolve_initial_channels(user_data)

    # 연결 등록
    connected = await ws_manager.connect(
        websocket,
        user_id=user_id,
        org_id=user_data["org_id"],
        team_id=user_data.get("team_id"),
        division_id=user_data.get("division_id"),
        role=user_data["role"],
        channels=initial_channels,
    )

    if not connected:
        # 동시 연결 제한으로 인해 close되었음
        return

    logger.info(f"[WS] WebSocket 연결: user={user_id}, channels={initial_channels}")

    try:
        while True:
            # 클라이언트 메시지 수신
            data = await websocket.receive_text()

            try:
                msg_dict = json.loads(data)
                sub_msg = WsSubscribeMessage(**msg_dict)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"[WS] 잘못된 메시지: {e}")
                error_msg = WsMessage(
                    type="error",
                    channel=f"user:{user_id}",
                    data={"code": "INVALID_MESSAGE", "message": str(e)},
                )
                try:
                    await websocket.send_text(error_msg.model_dump_json())
                except Exception:
                    pass
                continue

            # 채널 권한 확인 (간단한 검증: 사용자가 실제로 이 채널에 접근할 수 있는지)
            channel_type = sub_msg.channel.split(":")[0] if ":" in sub_msg.channel else None

            # 채널별 권한 확인
            authorized = False
            if channel_type == "team":
                # team 채널은 팀원이면 접근 가능
                authorized = user_data.get("team_id") is not None
            elif channel_type == "division":
                # division 채널은 director 이상만 접근 가능
                authorized = user_data["role"] in ("director", "executive", "admin")
            elif channel_type == "company":
                # company 채널은 executive 이상만 접근 가능
                authorized = user_data["role"] in ("executive", "admin")

            if not authorized:
                logger.warning(
                    f"[WS] 권한 없음: user={user_id}, channel={sub_msg.channel}, role={user_data['role']}"
                )
                error_msg = WsMessage(
                    type="error",
                    channel=f"user:{user_id}",
                    data={
                        "code": "UNAUTHORIZED_CHANNEL",
                        "message": f"채널 접근 권한 없음: {sub_msg.channel}",
                    },
                )
                try:
                    await websocket.send_text(error_msg.model_dump_json())
                except Exception:
                    pass
                continue

            # 구독/구독해제 처리
            if sub_msg.action == "subscribe":
                await ws_manager.subscribe(websocket, sub_msg.channel)
                logger.info(f"[WS] 구독: user={user_id}, channel={sub_msg.channel}")
            elif sub_msg.action == "unsubscribe":
                await ws_manager.unsubscribe(websocket, sub_msg.channel)
                logger.info(f"[WS] 구독해제: user={user_id}, channel={sub_msg.channel}")

    except Exception as e:
        logger.error(f"[WS] 연결 중 에러: user={user_id}, {e}", exc_info=True)
    finally:
        await ws_manager.disconnect(websocket)
        logger.info(f"[WS] 연결 종료: user={user_id}")
