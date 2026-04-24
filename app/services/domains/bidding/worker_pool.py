"""
Worker Pool — 5개 워커 스레드 관리 (STEP 8)

역할:
- 5개 워커 병렬 처리
- Redis 큐에서 Job dequeue
- JobExecutor로 실행
- 에러 처리 및 재시도
- Graceful shutdown
"""

import asyncio
import logging
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Optional, List, Callable
from uuid import UUID

logger = logging.getLogger(__name__)


class WorkerPool:
    """5개 워커 스레드 관리"""

    def __init__(
        self,
        job_service: "JobService",
        queue_manager: "QueueManager",
        job_executor: "JobExecutor",
        num_workers: int = 5,
    ):
        self.job_service = job_service
        self.queue = queue_manager
        self.executor = job_executor
        self.num_workers = num_workers

        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.workers: List[str] = []
        self.running = False
        self.logger = logger
        self._shutdown_event = asyncio.Event()

    async def start(self):
        """워커 풀 시작"""
        self.running = True
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.num_workers,
            thread_name_prefix="job-worker-"
        )

        # 각 워커를 스레드에서 실행
        loop = asyncio.get_event_loop()
        futures = []

        for i in range(self.num_workers):
            worker_id = f"worker-{i}"
            self.workers.append(worker_id)

            # asyncio.run_in_executor로 동기 워커를 async 환경에서 실행
            future = loop.run_in_executor(
                self.thread_pool,
                self._worker_loop,
                worker_id
            )
            futures.append(future)

        self.logger.info(f"Worker pool started with {self.num_workers} workers")
        return futures

    async def stop(self, timeout: int = 30):
        """워커 풀 종료 (graceful shutdown)"""
        self.running = False
        self.logger.info("Initiating graceful shutdown of worker pool...")

        # 진행 중인 작업 완료 대기 (최대 timeout초)
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True)

        self.logger.info("Worker pool stopped")

    def is_running(self) -> bool:
        """워커 풀이 실행 중인지 확인"""
        return self.running

    # ── Private Methods ──

    def _worker_loop(self, worker_id: str):
        """워커 메인 루프 (스레드에서 실행)"""
        self.logger.info(f"{worker_id} started")

        while self.running:
            try:
                # 큐에서 Job을 꺼냄 (blocking, timeout=5초)
                job_dict = asyncio.run(
                    self.queue.dequeue_job(worker_id, timeout=5)
                )

                if not job_dict:
                    continue

                job_id = str(job_dict.get("id"))

                # Job 실행
                self.logger.info(f"{worker_id} processing job {job_id}")

                try:
                    # 실제 작업 실행 (JobExecutor)
                    result = asyncio.run(
                        self.executor.execute(job_dict)
                    )

                    # 성공
                    asyncio.run(
                        self.job_service.mark_job_success(
                            UUID(job_id),
                            result
                        )
                    )
                    asyncio.run(
                        self.queue.mark_success(job_id, result)
                    )

                    self.logger.info(f"{worker_id} completed job {job_id}")

                except Exception as e:
                    # 실패 처리
                    self.logger.error(
                        f"{worker_id} job {job_id} failed: {str(e)}"
                    )

                    retries = job_dict.get("retries", 0)

                    # DB 상태 업데이트
                    asyncio.run(
                        self.job_service.mark_job_failed(
                            UUID(job_id),
                            str(e),
                            retries
                        )
                    )

                    # 재시도 결정
                    if retries < 3:
                        # 재시도 큐로 복귀 (우선도 감소)
                        job_dict["retries"] = retries + 1
                        job_dict["status"] = "pending"
                        # 재시도 job은 NORMAL 우선도로 설정
                        job_dict["priority"] = 1
                        asyncio.run(self.queue.enqueue_job(job_dict))
                        self.logger.info(f"Job {job_id} re-enqueued (attempt {retries + 2})")
                    else:
                        # DLQ로 이동 (큐 마니저에서 처리)
                        asyncio.run(
                            self.queue.mark_failure(job_id, str(e), retries)
                        )

                # 하트비트 업데이트
                asyncio.run(
                    self.queue.worker_heartbeat(worker_id)
                )

            except Exception as e:
                self.logger.error(f"{worker_id} critical error: {e}", exc_info=True)
                # 워커는 계속 돌음 (graceful recovery)

        self.logger.info(f"{worker_id} stopped")

    def _signal_handler(self, signum, frame):
        """SIGTERM/SIGINT 신호 처리"""
        self.logger.info(f"Signal {signum} received, shutting down...")
        self.running = False
