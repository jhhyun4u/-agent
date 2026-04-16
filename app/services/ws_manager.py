"""WebSocket Connection Manager (§26)

다중 클라이언트 연결을 관리하고 채널별 브로드캐스트를 수행.
"""

import asyncio
import logging
from datetime import datetime
from typing import Callable

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from app.config import settings
from app.models.ws_schemas import WsConnectionMeta, WsMessage

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 연결 관리자
    
    - 채널별 클라이언트 등록/해제
    - 사용자당 동시 연결 제한
    - 채널별 브로드캐스트
    - 하트비트 및 좀비 연결 정리
    """
    
    def __init__(self):
        # 채널 → {WebSocket 인스턴스 집합}
        self._connections: dict[str, set[WebSocket]] = {}
        
        # 사용자 ID → {WebSocket 인스턴스 집합} (동시 연결 수 제한용)
        self._user_connections: dict[str, set[WebSocket]] = {}
        
        # WebSocket id(ws) → 메타데이터
        self._ws_meta: dict[int, WsConnectionMeta] = {}
        
        # 재진입 방지용 락
        self._lock = asyncio.Lock()
        
        # 하트비트 태스크
        self._heartbeat_task: asyncio.Task | None = None
    
    async def connect(
        self,
        ws: WebSocket,
        user_id: str,
        org_id: str,
        team_id: str | None,
        division_id: str | None,
        role: str,
        channels: set[str],
    ) -> bool:
        """클라이언트를 연결하고 채널에 등록
        
        Returns:
            True: 연결 성공
            False: 동시 연결 제한으로 거부됨
        """
        await ws.accept()
        
        async with self._lock:
            # 사용자당 연결 수 확인
            user_conns = self._user_connections.get(user_id, set())
            if len(user_conns) >= settings.ws_max_connections_per_user:
                logger.warning(
                    f"[WS] 사용자 {user_id}의 동시 연결 초과 ({len(user_conns)} >= {settings.ws_max_connections_per_user}). 연결 거부."
                )
                await ws.close(code=4029, reason="Too many connections")
                return False
            
            # 메타데이터 저장
            meta = WsConnectionMeta(
                user_id=user_id,
                org_id=org_id,
                team_id=team_id,
                division_id=division_id,
                role=role,
                channels=channels,
            )
            ws_id = id(ws)
            self._ws_meta[ws_id] = meta
            
            # 사용자 연결 추가
            if user_id not in self._user_connections:
                self._user_connections[user_id] = set()
            self._user_connections[user_id].add(ws)
            
            # 채널에 등록
            for channel in channels:
                if channel not in self._connections:
                    self._connections[channel] = set()
                self._connections[channel].add(ws)
            
            logger.info(
                f"[WS] 연결 성공: user={user_id}, channels={channels}, "
                f"user_conns={len(self._user_connections[user_id])}, "
                f"total_conns={sum(len(c) for c in self._connections.values())}"
            )
            return True
    
    async def disconnect(self, ws: WebSocket) -> None:
        """클라이언트를 모든 채널에서 제거"""
        async with self._lock:
            ws_id = id(ws)
            meta = self._ws_meta.pop(ws_id, None)
            
            if not meta:
                return
            
            # 채널에서 제거
            for channel in meta.channels:
                if channel in self._connections:
                    self._connections[channel].discard(ws)
                    # 채널이 비어있으면 삭제
                    if not self._connections[channel]:
                        del self._connections[channel]
            
            # 사용자 연결에서 제거
            user_id = meta.user_id
            if user_id in self._user_connections:
                self._user_connections[user_id].discard(ws)
                if not self._user_connections[user_id]:
                    del self._user_connections[user_id]
            
            logger.info(f"[WS] 연결 해제: user={user_id}")
    
    async def subscribe(self, ws: WebSocket, channel: str) -> bool:
        """클라이언트를 새로운 채널에 구독"""
        async with self._lock:
            ws_id = id(ws)
            meta = self._ws_meta.get(ws_id)
            
            if not meta:
                return False
            
            # 이미 구독 중이면 무시
            if channel in meta.channels:
                return True
            
            # 채널에 추가
            if channel not in self._connections:
                self._connections[channel] = set()
            self._connections[channel].add(ws)
            meta.channels.add(channel)
            
            logger.info(f"[WS] 구독: user={meta.user_id}, channel={channel}")
            return True
    
    async def unsubscribe(self, ws: WebSocket, channel: str) -> bool:
        """클라이언트를 채널에서 구독 해제"""
        async with self._lock:
            ws_id = id(ws)
            meta = self._ws_meta.get(ws_id)
            
            if not meta or channel not in meta.channels:
                return False
            
            # 채널에서 제거
            meta.channels.discard(channel)
            if channel in self._connections:
                self._connections[channel].discard(ws)
                if not self._connections[channel]:
                    del self._connections[channel]
            
            logger.info(f"[WS] 구독 해제: user={meta.user_id}, channel={channel}")
            return True
    
    async def broadcast(self, channel: str, message: WsMessage) -> int:
        """채널의 모든 클라이언트에게 메시지 브로드캐스트
        
        Returns:
            성공한 발송 수
        """
        if channel not in self._connections:
            return 0
        
        connections = self._connections[channel].copy()
        success_count = 0
        dead_connections = []
        
        msg_json = message.model_dump_json()
        
        for ws in connections:
            try:
                # 연결 상태 확인
                if ws.client_state != WebSocketState.CONNECTED:
                    dead_connections.append(ws)
                    continue
                
                await ws.send_text(msg_json)
                success_count += 1
            except Exception as e:
                logger.debug(f"[WS] 메시지 발송 실패 (channel={channel}): {e}")
                dead_connections.append(ws)
        
        # 좀비 연결 정리
        if dead_connections:
            async with self._lock:
                for ws in dead_connections:
                    await self.disconnect(ws)
        
        return success_count
    
    async def broadcast_to_user(self, user_id: str, message: WsMessage) -> int:
        """특정 사용자의 모든 연결에 직접 메시지 발송 (채널 관계없음)
        
        Returns:
            성공한 발송 수
        """
        if user_id not in self._user_connections:
            return 0
        
        connections = self._user_connections[user_id].copy()
        success_count = 0
        dead_connections = []
        
        msg_json = message.model_dump_json()
        
        for ws in connections:
            try:
                if ws.client_state != WebSocketState.CONNECTED:
                    dead_connections.append(ws)
                    continue
                
                await ws.send_text(msg_json)
                success_count += 1
            except Exception as e:
                logger.debug(f"[WS] 사용자 메시지 발송 실패 (user={user_id}): {e}")
                dead_connections.append(ws)
        
        # 좀비 연결 정리
        if dead_connections:
            async with self._lock:
                for ws in dead_connections:
                    await self.disconnect(ws)
        
        return success_count
    
    async def send_heartbeat(self) -> None:
        """모든 연결에 하트비트 발송"""
        heartbeat = WsMessage(
            type="heartbeat",
            channel="*",
            data={},
        )
        
        # 모든 채널의 연결에 발송
        all_channels = list(self._connections.keys())
        for channel in all_channels:
            await self.broadcast(channel, heartbeat)
    
    async def heartbeat_loop(self) -> None:
        """주기적 하트비트 루프 (서버 라이프사이클에서 실행)"""
        interval = settings.ws_heartbeat_interval_seconds
        logger.info(f"[WS] 하트비트 루프 시작 (간격={interval}초)")
        
        try:
            while True:
                await asyncio.sleep(interval)
                try:
                    await self.send_heartbeat()
                except Exception as e:
                    logger.error(f"[WS] 하트비트 발송 중 에러: {e}")
        except asyncio.CancelledError:
            logger.info("[WS] 하트비트 루프 종료")
            raise
    
    def get_stats(self) -> dict:
        """연결 통계 반환 (health check용)"""
        total_conns = sum(len(c) for c in self._connections.values())
        return {
            "total_connections": total_conns,
            "channels": len(self._connections),
            "users": len(self._user_connections),
            "channel_details": {
                ch: len(conns)
                for ch, conns in self._connections.items()
            },
        }


# 글로벌 인스턴스
ws_manager = ConnectionManager()
