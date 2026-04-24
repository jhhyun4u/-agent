"""
Job Service — Job CRUD + 상태 관리 (STEP 8)

역할:
- Job 생성 및 큐 등록
- Job 상태 조회 및 변경
- Job 취소
- 재시도 처리
"""

import logging
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from uuid import UUID, uuid4

from app.models.job_queue_schemas import Job, JobStatus, JobType, JobPriority

logger = logging.getLogger(__name__)


class JobService:
    """Job CRUD + 상태 관리"""

    def __init__(self, db_client, queue_manager):
        """
        Args:
            db_client: Supabase 클라이언트 (async)
            queue_manager: QueueManager 인스턴스
        """
        self.db = db_client
        self.queue = queue_manager
        self.logger = logger

    # ── CRUD ──

    async def create_job(
        self,
        proposal_id: UUID,
        job_type: str,
        payload: dict,
        priority: int = 1,
        created_by: UUID = None,
        max_retries: int = 3,
    ) -> Job:
        """새로운 Job 생성 및 큐에 등록"""
        job_id = uuid4()

        # 작업 STEP 추출 (e.g., "step4a_diagnosis" → "4a")
        step = self._extract_step(job_type)

        job = Job(
            id=job_id,
            proposal_id=proposal_id,
            step=step,
            type=JobType(job_type),
            status=JobStatus.PENDING,
            priority=JobPriority(priority),
            payload=payload,
            created_by=created_by,
            created_at=datetime.now(timezone.utc),
            retries=0,
            max_retries=max_retries,
        )

        # 1. DB에 저장
        await self._save_to_db(job)

        # 2. 큐에 추가
        success = await self.queue.enqueue_job(job.model_dump(mode="json"))

        if not success:
            self.logger.error(f"Failed to enqueue job {job_id}, but DB save succeeded")
            # DB는 저장되었으므로 나중에 수동 복구 가능

        return job

    async def get_job(self, job_id: UUID) -> Optional[Job]:
        """Job 조회"""
        try:
            response = await self.db.table("jobs").select("*").eq("id", str(job_id)).single()
            if response:
                return self._row_to_job(response)
            return None
        except Exception as e:
            self.logger.error(f"Failed to get job {job_id}: {e}")
            return None

    async def get_jobs(
        self,
        proposal_id: UUID = None,
        status: str = None,
        step: str = None,
        limit: int = 20,
        offset: int = 0,
        order_by: str = "created_at",
        order_direction: str = "desc",
    ) -> Tuple[List[Job], int]:
        """Job 목록 조회 (필터링)"""
        try:
            query = self.db.table("jobs").select("*", count="exact")

            if proposal_id:
                query = query.eq("proposal_id", str(proposal_id))
            if status:
                query = query.eq("status", status)
            if step:
                query = query.eq("step", step)

            response = await query.order(
                order_by,
                ascending=(order_direction == "asc")
            ).range(offset, offset + limit - 1)

            jobs = [self._row_to_job(row) for row in response.data]
            total = response.count or 0

            return jobs, total
        except Exception as e:
            self.logger.error(f"Failed to get jobs: {e}")
            return [], 0

    # ── 상태 전환 ──

    async def mark_job_running(self, job_id: UUID, worker_id: str) -> bool:
        """Job 상태를 RUNNING으로 변경"""
        try:
            await self.db.table("jobs").update({
                "status": "running",
                "started_at": datetime.now(timezone.utc).isoformat(),
                "assigned_worker_id": worker_id,
            }).eq("id", str(job_id))

            self.logger.info(f"Job {job_id} marked as RUNNING by {worker_id}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark job as running: {e}")
            return False

    async def mark_job_success(self, job_id: UUID, result: dict) -> bool:
        """Job 상태를 SUCCESS로 변경"""
        try:
            job = await self.get_job(job_id)
            if not job or not job.started_at:
                self.logger.error(f"Cannot calculate duration for job {job_id}")
                duration = None
            else:
                duration = (
                    datetime.now(timezone.utc) - job.started_at
                ).total_seconds()

            await self.db.table("jobs").update({
                "status": "success",
                "result": result,
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "duration_seconds": duration,
            }).eq("id", str(job_id))

            # 성과 메트릭 기록
            await self._record_metric(job_id, "success", duration or 0)

            self.logger.info(f"Job {job_id} marked as SUCCESS")
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark job as success: {e}")
            return False

    async def mark_job_failed(self, job_id: UUID, error: str, attempt: int) -> bool:
        """Job 상태를 FAILED로 변경 (또는 PENDING with retries++)"""
        try:
            if attempt >= 3:
                # 최대 재시도 초과
                duration = await self._calculate_duration(job_id)
                await self.db.table("jobs").update({
                    "status": "failed",
                    "error": error[:500],  # 처음 500자만 저장
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "retries": attempt,
                    "duration_seconds": duration,
                }).eq("id", str(job_id))

                await self._record_metric(job_id, "failed", duration or 0)

                self.logger.error(f"Job {job_id} FAILED after {attempt} attempts")
            else:
                # 재시도 가능
                await self.db.table("jobs").update({
                    "retries": attempt,
                    "error": error[:500],  # 마지막 에러만 저장
                }).eq("id", str(job_id))

                self.logger.info(f"Job {job_id} will retry (attempt {attempt + 1})")

            return True
        except Exception as e:
            self.logger.error(f"Failed to mark job as failed: {e}")
            return False

    async def cancel_job(self, job_id: UUID) -> bool:
        """Job 취소 (PENDING 또는 RUNNING → CANCELLED)"""
        try:
            job = await self.get_job(job_id)
            if not job:
                return False

            if job.status in [JobStatus.SUCCESS, JobStatus.FAILED]:
                self.logger.warning(f"Cannot cancel job {job_id} in state {job.status}")
                return False

            await self.db.table("jobs").update({
                "status": "cancelled",
                "completed_at": datetime.now(timezone.utc).isoformat(),
            }).eq("id", str(job_id))

            self.logger.info(f"Job {job_id} cancelled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel job: {e}")
            return False

    # ── Private Helpers ──

    async def _save_to_db(self, job: Job):
        """Job을 DB에 저장"""
        try:
            await self.db.table("jobs").insert({
                "id": str(job.id),
                "proposal_id": str(job.proposal_id),
                "step": job.step,
                "type": job.type.value,
                "status": job.status.value,
                "priority": job.priority.value,
                "payload": job.payload,
                "created_at": job.created_at.isoformat(),
                "created_by": str(job.created_by) if job.created_by else None,
                "retries": job.retries,
                "max_retries": job.max_retries,
            })
            self.logger.info(f"Job {job.id} saved to DB")
        except Exception as e:
            self.logger.error(f"Failed to save job to DB: {e}")
            raise

    async def _calculate_duration(self, job_id: UUID) -> Optional[float]:
        """Job 처리 시간 계산 (started_at -> completed_at)"""
        try:
            job = await self.get_job(job_id)
            if job and job.started_at and job.completed_at:
                return (job.completed_at - job.started_at).total_seconds()
            return None
        except Exception as e:
            self.logger.error(f"Failed to calculate duration: {e}")
            return None

    async def _record_metric(self, job_id: UUID, status: str, duration: float):
        """성과 메트릭 기록 (job_metrics 테이블)"""
        try:
            job = await self.get_job(job_id)
            if not job:
                return

            await self.db.table("job_metrics").insert({
                "job_id": str(job_id),
                "step": job.step,
                "type": job.type.value,
                "status": status,
                "duration_seconds": duration,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            })
            self.logger.info(f"Metric recorded for job {job_id}")
        except Exception as e:
            self.logger.error(f"Failed to record metric: {e}")

    def _row_to_job(self, row: dict) -> Job:
        """DB 행을 Job 모델로 변환"""
        return Job(
            id=UUID(row["id"]),
            proposal_id=UUID(row["proposal_id"]),
            step=row["step"],
            type=JobType(row["type"]),
            status=JobStatus(row["status"]),
            priority=JobPriority(row["priority"]),
            payload=row.get("payload", {}),
            result=row.get("result"),
            error=row.get("error"),
            retries=row.get("retries", 0),
            max_retries=row.get("max_retries", 3),
            created_at=datetime.fromisoformat(row["created_at"]) if isinstance(row["created_at"], str) else row["created_at"],
            started_at=datetime.fromisoformat(row["started_at"]) if isinstance(row.get("started_at"), str) else row.get("started_at"),
            completed_at=datetime.fromisoformat(row["completed_at"]) if isinstance(row.get("completed_at"), str) else row.get("completed_at"),
            duration_seconds=row.get("duration_seconds"),
            created_by=UUID(row["created_by"]) if row.get("created_by") else None,
            assigned_worker_id=row.get("assigned_worker_id"),
            tags=row.get("tags", {}),
            updated_at=datetime.fromisoformat(row["updated_at"]) if isinstance(row.get("updated_at"), str) else row.get("updated_at"),
        )

    @staticmethod
    def _extract_step(job_type: str) -> str:
        """작업 타입에서 STEP 추출 (e.g., 'step4a_diagnosis' → '4a')"""
        parts = job_type.split("_")
        if parts[0].startswith("step"):
            return parts[0][4:]  # Remove "step" prefix
        return "unknown"
