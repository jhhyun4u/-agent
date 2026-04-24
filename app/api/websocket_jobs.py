"""
STEP 8: Job Queue WebSocket Streaming (Day 5 WebSocket endpoint)

Real-time job status updates via WebSocket.
Endpoint: WS /ws/jobs/{job_id}

Messages:
- JobStatusMessage: 상태 변경 (PENDING → RUNNING → SUCCESS/FAILED/CANCELLED)
- JobProgressMessage: 진행률 업데이트 (0-100%)
- JobCompletionMessage: 완료 + 결과
- JobErrorMessage: 에러 메시지
- JobHeartbeat: 30초마다 alive 신호

자동 종료: Job 완료 시 WebSocket 자동 종료.
권한: 자신의 job만 구독 가능.
"""

import asyncio
import json
import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, WebSocketException
from starlette.websockets import WebSocket

from app.models.auth_schemas import CurrentUser
from app.models.job_queue_schemas import JobStatus
from app.services.domains.bidding.job_queue_service import JobQueueService, JobNotFoundError
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================
# WebSocket Message Types
# ============================================


class JobStatusMessage:
    """Job 상태 변경 메시지"""

    def __init__(self, job_id: UUID, status: str):
        self.type = "status"
        self.job_id = str(job_id)
        self.status = status

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "job_id": self.job_id,
            "status": self.status,
        })


class JobProgressMessage:
    """Job 진행률 메시지"""

    def __init__(self, job_id: UUID, progress: float):
        self.type = "progress"
        self.job_id = str(job_id)
        self.progress = min(max(progress, 0.0), 100.0)  # 0-100% 범위

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "job_id": self.job_id,
            "progress": self.progress,
        })


class JobCompletionMessage:
    """Job 완료 메시지"""

    def __init__(self, job_id: UUID, result: dict, duration_seconds: float):
        self.type = "completed"
        self.job_id = str(job_id)
        self.result = result
        self.duration_seconds = duration_seconds

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "job_id": self.job_id,
            "result": self.result,
            "duration_seconds": self.duration_seconds,
        })


class JobErrorMessage:
    """Job 에러 메시지"""

    def __init__(self, job_id: UUID, error: str, retries: int = 0):
        self.type = "error"
        self.job_id = str(job_id)
        self.error = error
        self.retries = retries

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "job_id": self.job_id,
            "error": self.error,
            "retries": self.retries,
        })


class JobHeartbeat:
    """Heartbeat 메시지 (alive 신호)"""

    def __init__(self, job_id: UUID):
        self.type = "heartbeat"
        self.job_id = str(job_id)

    def to_json(self) -> str:
        return json.dumps({
            "type": self.type,
            "job_id": self.job_id,
        })


# ============================================
# Authentication
# ============================================


async def _authenticate_ws_token(token: Optional[str]) -> CurrentUser:
    """
    WebSocket 토큰 인증 및 사용자 정보 반환.

    Args:
        token: Authorization Bearer 토큰

    Returns:
        CurrentUser: {id, email, name, role, org_id}

    Raises:
        WebSocketException: 인증 실패
    """
    if not token:
        raise WebSocketException(code=4001, reason="Unauthorized: no token")

    try:
        client = await get_async_client()
        response = await client.auth.get_user(token)
        user_auth = response.user
    except Exception as e:
        logger.error(f"[WS] Auth token validation failed: {e}")
        raise WebSocketException(code=4001, reason="Unauthorized: invalid token")

    if not user_auth:
        raise WebSocketException(code=4001, reason="Unauthorized: no user found")

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

        return CurrentUser(
            id=UUID(profile.data["id"]),
            email=profile.data.get("email", ""),
            name=profile.data.get("name", ""),
            role=profile.data.get("role", "member"),
            org_id=UUID(profile.data["org_id"]) if profile.data.get("org_id") else None,
        )

    except WebSocketException:
        raise
    except Exception as e:
        logger.error(f"[WS] Profile lookup failed: {e}")
        raise WebSocketException(code=4001, reason="Unauthorized: profile lookup failed")


# ============================================
# WebSocket Endpoint
# ============================================


@router.websocket("/ws/jobs/{job_id}")
async def websocket_job_stream(
    websocket: WebSocket,
    job_id: UUID,
    token: Optional[str] = Query(None),
):
    """
    Job 실시간 상태 스트리밍 WebSocket 엔드포인트.

    Path Parameters:
        job_id: 모니터링할 Job ID

    Query Parameters:
        token: Authorization Bearer 토큰

    Connection Flow:
        1. 토큰 인증
        2. Job 접근 권한 확인 (생성자 또는 admin)
        3. 상태 변경 메시지 실시간 전송
        4. 30초마다 heartbeat 전송
        5. Job 완료 시 자동 종료

    Message Format:
        {
            "type": "status|progress|completed|error|heartbeat",
            "job_id": "<uuid>",
            ...
        }

    Disconnect Conditions:
        - 클라이언트 연결 끊김
        - Job 완료 (SUCCESS/FAILED/CANCELLED)
        - 권한 검증 실패
        - 토큰 만료
    """
    try:
        # Step 1: 토큰 인증
        user = await _authenticate_ws_token(token)
        logger.info(f"[WS] User authenticated: {user.id}")

        # Step 2: WebSocket 연결 수락
        await websocket.accept()
        logger.info(f"[WS] Connection accepted for job {job_id}")

        # Step 3: Job 접근 권한 확인
        service = JobQueueService(db_client=await get_async_client())

        try:
            job = await service.get_job(job_id=job_id)
        except JobNotFoundError:
            error_msg = JobErrorMessage(
                job_id=job_id,
                error="Job not found",
            )
            await websocket.send_text(error_msg.to_json())
            await websocket.close(code=4004, reason="Job not found")
            return

        # 권한 확인: 생성자 또는 admin
        if job.created_by != user.id and user.role != "admin":
            error_msg = JobErrorMessage(
                job_id=job_id,
                error="Access denied",
            )
            await websocket.send_text(error_msg.to_json())
            await websocket.close(code=4003, reason="Access denied")
            return

        logger.info(f"[WS] Job access verified: {job_id} (user={user.id})")

        # Step 4: 초기 상태 전송
        status_msg = JobStatusMessage(job_id=job_id, status=job.status.value)
        await websocket.send_text(status_msg.to_json())

        progress = await service.get_job_progress(job_id=job_id)
        progress_msg = JobProgressMessage(job_id=job_id, progress=progress)
        await websocket.send_text(progress_msg.to_json())

        # Step 5: 상태 폴링 루프 (30초 heartbeat)
        last_status = job.status
        heartbeat_interval = 30  # seconds
        last_heartbeat = asyncio.get_event_loop().time()

        while True:
            try:
                # 현재 상태 조회
                current_job = await service.get_job(job_id=job_id)

                # 상태 변경 감지
                if current_job.status != last_status:
                    status_msg = JobStatusMessage(
                        job_id=job_id,
                        status=current_job.status.value,
                    )
                    await websocket.send_text(status_msg.to_json())
                    logger.info(f"[WS] Status changed: {job_id} → {current_job.status}")

                    last_status = current_job.status

                    # 완료 메시지 전송
                    if current_job.status == JobStatus.SUCCESS:
                        result = current_job.result or {}
                        completion_msg = JobCompletionMessage(
                            job_id=job_id,
                            result=result,
                            duration_seconds=current_job.duration_seconds or 0.0,
                        )
                        await websocket.send_text(completion_msg.to_json())
                        logger.info(f"[WS] Job completed: {job_id}")
                        await websocket.close(code=1000, reason="Job completed")
                        break

                    # 실패 또는 취소 메시지 전송
                    elif current_job.status in [JobStatus.FAILED, JobStatus.CANCELLED]:
                        error_msg = JobErrorMessage(
                            job_id=job_id,
                            error=current_job.error or f"Job {current_job.status.value}",
                            retries=current_job.retries,
                        )
                        await websocket.send_text(error_msg.to_json())
                        logger.info(f"[WS] Job {current_job.status.value}: {job_id}")
                        await websocket.close(
                            code=1000,
                            reason=f"Job {current_job.status.value}"
                        )
                        break

                # 진행률 업데이트
                current_progress = await service.get_job_progress(job_id=job_id)
                if current_progress > progress:
                    progress_msg = JobProgressMessage(
                        job_id=job_id,
                        progress=current_progress,
                    )
                    await websocket.send_text(progress_msg.to_json())
                    progress = current_progress

                # Heartbeat 전송 (30초마다)
                now = asyncio.get_event_loop().time()
                if now - last_heartbeat >= heartbeat_interval:
                    heartbeat_msg = JobHeartbeat(job_id=job_id)
                    await websocket.send_text(heartbeat_msg.to_json())
                    logger.debug(f"[WS] Heartbeat sent: {job_id}")
                    last_heartbeat = now

                # 폴링 대기 (1초)
                await asyncio.sleep(1)

            except asyncio.CancelledError:
                logger.info(f"[WS] Stream cancelled: {job_id}")
                break
            except Exception as e:
                logger.error(f"[WS] Streaming error for {job_id}: {e}")
                error_msg = JobErrorMessage(job_id=job_id, error=str(e))
                try:
                    await websocket.send_text(error_msg.to_json())
                except Exception:
                    pass
                break

    except WebSocketException as e:
        logger.warning(f"[WS] WebSocket exception: {e}")
        try:
            await websocket.close(code=e.code, reason=e.reason)
        except Exception:
            pass

    except Exception as e:
        logger.error(f"[WS] Unexpected error for job {job_id}: {e}", exc_info=True)
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except Exception:
            pass

    finally:
        logger.info(f"[WS] Connection closed: {job_id}")
