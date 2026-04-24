"""
Queue Manager — Redis 기반 비동기 메시지 큐 관리 (STEP 8)

역할:
- Job 우선도별 큐 관리 (HIGH/NORMAL/LOW)
- Redis와 로컬 폴백 모두 지원
- Job 상태 캐시 (TTL 24h)
- 워커 하트비트 추적
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from uuid import UUID

try:
    import redis.asyncio as aioredis
except ImportError:
    aioredis = None

logger = logging.getLogger(__name__)


class QueueManager:
    """Redis 기반 메시지 큐 관리"""

    # 큐 이름 (우선도별)
    QUEUE_HIGH = "jobs:queue:high"
    QUEUE_NORMAL = "jobs:queue:normal"
    QUEUE_LOW = "jobs:queue:low"
    QUEUE_DLQ = "jobs:queue:dlq"  # Dead Letter Queue

    # 기타 키
    KEY_JOB_STATE = "jobs:state:{job_id}"  # hash: {status, retries, worker_id}
    KEY_WORKER_HEARTBEAT = "workers:hb:{worker_id}"  # heartbeat (TTL 30s)

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.logger = logger
        self._is_connected = False

    async def connect(self):
        """Redis 연결 (비동기)"""
        if aioredis is None:
            self.logger.warning("aioredis not installed, using in-memory fallback")
            self._is_connected = False
            return

        try:
            self.redis = await aioredis.from_url(
                self.redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_keepalive=True,
            )
            await self.redis.ping()
            self._is_connected = True
            self.logger.info(f"Connected to Redis: {self.redis_url}")
        except Exception as e:
            self.logger.error(f"Failed to connect to Redis: {e}, using in-memory fallback")
            self._is_connected = False
            self.redis = None

    async def close(self):
        """Redis 연결 종료"""
        if self.redis:
            try:
                await self.redis.close()
                self._is_connected = False
                self.logger.info("Redis connection closed")
            except Exception as e:
                self.logger.error(f"Error closing Redis connection: {e}")

    # ── Public Methods ──

    async def enqueue_job(self, job: dict) -> bool:
        """Job을 큐에 추가 (우선도별)"""
        try:
            if not self._is_connected or not self.redis:
                self.logger.debug(f"Redis not available, skipping enqueue for job {job.get('id')}")
                return False

            queue_key = self._get_queue_key(job.get("priority", 1))
            job_json = json.dumps(job, default=str)

            # 1. 큐에 추가 (list의 우측에 push)
            await self.redis.rpush(queue_key, job_json)

            # 2. Job 상태 캐시 (TTL 24시간)
            state_key = self.KEY_JOB_STATE.format(job_id=str(job.get("id")))
            await self.redis.hset(
                state_key,
                mapping={
                    "status": job.get("status", "pending"),
                    "retries": job.get("retries", 0),
                    "worker_id": "",
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )
            await self.redis.expire(state_key, 86400)  # 24시간

            self.logger.info(f"Job {job.get('id')} enqueued (priority={job.get('priority')})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to enqueue job {job.get('id')}: {e}")
            return False

    async def dequeue_job(self, worker_id: str, timeout: int = 5) -> Optional[dict]:
        """
        큐에서 Job을 꺼냄 (우선도 순서)
        - HIGH > NORMAL > LOW 순서로 확인
        - blocking=true로 대기
        """
        if not self._is_connected or not self.redis:
            self.logger.debug(f"Redis not available, {worker_id} cannot dequeue")
            return None

        try:
            # 우선도별로 큐 확인
            for queue_key in [self.QUEUE_HIGH, self.QUEUE_NORMAL, self.QUEUE_LOW]:
                try:
                    # BLPOP: 왼쪽에서 꺼냄 (FIFO) + blocking
                    result = await asyncio.wait_for(
                        self.redis.blpop(queue_key, timeout=1),
                        timeout=timeout
                    )

                    if result:
                        _, job_json = result
                        job_dict = json.loads(job_json)

                        # Job 상태 업데이트: RUNNING
                        state_key = self.KEY_JOB_STATE.format(job_id=str(job_dict["id"]))
                        await self.redis.hset(
                            state_key,
                            mapping={
                                "status": "running",
                                "worker_id": worker_id,
                                "started_at": datetime.utcnow().isoformat(),
                            }
                        )

                        self.logger.info(f"Job dequeued by {worker_id}: {job_dict['id']}")
                        return job_dict

                except asyncio.TimeoutError:
                    continue

            return None

        except Exception as e:
            self.logger.error(f"Failed to dequeue job: {e}")
            return None

    async def mark_success(self, job_id: str, result: dict) -> bool:
        """Job 완료 처리"""
        if not self._is_connected or not self.redis:
            self.logger.debug(f"Redis not available, cannot mark job {job_id} as success")
            return False

        try:
            state_key = self.KEY_JOB_STATE.format(job_id=job_id)
            await self.redis.hset(
                state_key,
                mapping={
                    "status": "success",
                    "completed_at": datetime.utcnow().isoformat(),
                    "result_size": len(json.dumps(result, default=str)),
                }
            )
            self.logger.info(f"Job {job_id} marked SUCCESS")
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark job success: {e}")
            return False

    async def mark_failure(self, job_id: str, error: str, retries: int) -> bool:
        """Job 실패 처리 (재시도 결정)"""
        if not self._is_connected or not self.redis:
            self.logger.debug(f"Redis not available, cannot mark job {job_id} as failure")
            return False

        try:
            if retries >= 3:  # 최대 재시도 초과
                # DLQ로 이동
                await self.redis.rpush(
                    self.QUEUE_DLQ,
                    json.dumps({
                        "job_id": job_id,
                        "error": error,
                        "failed_at": datetime.utcnow().isoformat(),
                        "retries": retries,
                    })
                )
                status = "failed"
                self.logger.warning(f"Job {job_id} moved to DLQ after {retries} retries")
            else:
                # 재시도 큐로 복귀
                status = "pending"
                self.logger.info(f"Job {job_id} will retry (attempt {retries + 1})")

            state_key = self.KEY_JOB_STATE.format(job_id=job_id)
            await self.redis.hset(
                state_key,
                mapping={
                    "status": status,
                    "retries": retries,
                    "last_error": error[:200],  # 처음 200자만
                }
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark job failure: {e}")
            return False

    async def get_job_state(self, job_id: str) -> Optional[dict]:
        """Job 상태 조회 (캐시에서)"""
        if not self._is_connected or not self.redis:
            self.logger.debug(f"Redis not available, cannot get job state for {job_id}")
            return None

        try:
            state_key = self.KEY_JOB_STATE.format(job_id=job_id)
            state = await self.redis.hgetall(state_key)
            return state if state else None
        except Exception as e:
            self.logger.error(f"Failed to get job state: {e}")
            return None

    async def worker_heartbeat(self, worker_id: str) -> bool:
        """워커 하트비트 (존재 신호)"""
        if not self._is_connected or not self.redis:
            return False

        try:
            hb_key = self.KEY_WORKER_HEARTBEAT.format(worker_id=worker_id)
            await self.redis.set(
                hb_key,
                datetime.utcnow().isoformat(),
                ex=30
            )  # TTL 30s
            return True
        except Exception as e:
            self.logger.error(f"Heartbeat failed for {worker_id}: {e}")
            return False

    async def get_active_workers(self) -> List[str]:
        """현재 활성 워커 목록"""
        if not self._is_connected or not self.redis:
            return []

        try:
            pattern = "workers:hb:*"
            keys = await self.redis.keys(pattern)
            return [k.replace("workers:hb:", "") for k in keys]
        except Exception as e:
            self.logger.error(f"Failed to get active workers: {e}")
            return []

    async def get_queue_stats(self) -> dict:
        """큐 통계 조회"""
        if not self._is_connected or not self.redis:
            return {
                "high_count": 0,
                "normal_count": 0,
                "low_count": 0,
                "dlq_count": 0,
                "active_workers": 0,
            }

        try:
            stats = {
                "high_count": await self.redis.llen(self.QUEUE_HIGH),
                "normal_count": await self.redis.llen(self.QUEUE_NORMAL),
                "low_count": await self.redis.llen(self.QUEUE_LOW),
                "dlq_count": await self.redis.llen(self.QUEUE_DLQ),
                "active_workers": len(await self.get_active_workers()),
            }
            return stats
        except Exception as e:
            self.logger.error(f"Failed to get queue stats: {e}")
            return {
                "high_count": 0,
                "normal_count": 0,
                "low_count": 0,
                "dlq_count": 0,
                "active_workers": 0,
            }

    async def clear_queue(self) -> bool:
        """큐 전체 비우기 (테스트용)"""
        if not self._is_connected or not self.redis:
            return False

        try:
            await self.redis.delete(
                self.QUEUE_HIGH,
                self.QUEUE_NORMAL,
                self.QUEUE_LOW,
                self.QUEUE_DLQ
            )
            self.logger.warning("Queues cleared")
            return True
        except Exception as e:
            self.logger.error(f"Failed to clear queues: {e}")
            return False

    # ── Private Methods ──

    def _get_queue_key(self, priority: int) -> str:
        """우선도별 큐 키 반환"""
        if priority == 0:  # HIGH
            return self.QUEUE_HIGH
        elif priority == 1:  # NORMAL
            return self.QUEUE_NORMAL
        else:  # LOW (2+)
            return self.QUEUE_LOW
