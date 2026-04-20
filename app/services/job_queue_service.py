"""
STEP 8: 비동기 Job Queue 시스템 - Service 계층

Job CRUD + 상태 관리 핵심 로직
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, List, Tuple
from uuid import UUID, uuid4

from app.exceptions import TenopAPIError
from app.models.job_queue_schemas import (
    Job,
    JobStatus,
    JobType,
    JobPriority,
    JobEventType,
    JobEvent,
)

logger = logging.getLogger(__name__)


# ============================================
# Custom Exceptions
# ============================================

class JobNotFoundError(TenopAPIError):
    """Job을 찾을 수 없음"""

    def __init__(self, message: str = "Job not found"):
        super().__init__(
            error_code="JOB_NOT_FOUND",
            message=message,
            status_code=404,
        )


class InvalidJobStateError(TenopAPIError):
    """Job 상태가 유효하지 않음"""

    def __init__(self, message: str = "Invalid job state for operation"):
        super().__init__(
            error_code="INVALID_JOB_STATE",
            message=message,
            status_code=409,
        )


class JobCancelError(TenopAPIError):
    """Job 취소 불가"""

    def __init__(self, message: str = "Cannot cancel job in current state"):
        super().__init__(
            error_code="JOB_CANCEL_FAILED",
            message=message,
            status_code=409,
        )


class JobRetryError(TenopAPIError):
    """Job 재시도 불가"""

    def __init__(self, message: str = "Job does not exist in DLQ or already completed"):
        super().__init__(
            error_code="JOB_RETRY_FAILED",
            message=message,
            status_code=404,
        )


# ============================================
# Job Queue Service
# ============================================

class JobQueueService:
    """
    Job CRUD + 상태 관리 서비스

    의존성:
    - db_client: Supabase 클라이언트 (비동기)
    - queue_manager: Redis 큐 관리자 (Day 3에서 추가)
    """

    def __init__(self, db_client):
        """
        Args:
            db_client: Supabase 비동기 클라이언트
        """
        self.db = db_client
        self.logger = logger

    # ========================================
    # CRUD Operations
    # ========================================

    async def create_job(
        self,
        proposal_id: UUID,
        job_type: JobType,
        payload: dict,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        created_by: UUID = None,
        tags: dict = None,
    ) -> Job:
        """
        새로운 Job 생성 및 큐에 등록

        Args:
            proposal_id: 제안서 ID
            job_type: 작업 타입 (STEP4A_DIAGNOSIS 등)
            payload: 작업 입력 파라미터
            priority: 우선도 (HIGH=0, NORMAL=1, LOW=2)
            max_retries: 최대 재시도 횟수
            created_by: 생성자 사용자 ID
            tags: 필터링용 태그

        Returns:
            생성된 Job 객체

        Raises:
            TenopAPIError: 생성 실패 시
        """
        job_id = uuid4()
        now = datetime.utcnow()

        # Job 객체 생성
        job = Job(
            id=job_id,
            proposal_id=proposal_id,
            step=self._extract_step(job_type),
            type=job_type,
            status=JobStatus.PENDING,
            priority=priority,
            payload=payload,
            max_retries=max_retries,
            retries=0,
            created_by=created_by,
            created_at=now,
            tags=tags or {},
        )

        try:
            # DB에 저장
            await self._save_to_db(job)
            self.logger.info(
                f"Job {job_id} created: type={job_type.value}, "
                f"priority={priority.value}, proposal_id={proposal_id}"
            )

            # Job 이벤트 기록
            await self._record_event(
                job_id,
                JobEventType.CREATED,
                {
                    "job_type": job_type.value,
                    "priority": priority.value,
                    "max_retries": max_retries,
                },
            )

            return job

        except Exception as e:
            self.logger.error(f"Failed to create job {job_id}: {e}")
            raise TenopAPIError(
                error_code="JOB_CREATE_FAILED",
                message=f"Failed to create job: {str(e)}",
                status_code=500,
            ) from e

    async def get_job(self, job_id: UUID) -> Optional[Job]:
        """
        Job 조회

        Args:
            job_id: Job ID

        Returns:
            Job 객체 또는 None

        Raises:
            TenopAPIError: 조회 실패 시
        """
        try:
            response = await self.db.table("jobs").select("*").eq("id", str(job_id)).single()

            if not response:
                return None

            return self._row_to_job(response)

        except Exception as e:
            self.logger.error(f"Failed to get job {job_id}: {e}")
            raise TenopAPIError(
                error_code="JOB_GET_FAILED",
                message=f"Failed to get job: {str(e)}",
                status_code=500,
            ) from e

    async def get_jobs(
        self,
        proposal_id: Optional[UUID] = None,
        status: Optional[JobStatus] = None,
        step: Optional[str] = None,
        created_by: Optional[UUID] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> Tuple[List[Job], int]:
        """
        Job 목록 조회 (필터링 + 페이징)

        Args:
            proposal_id: 제안서 ID (필터)
            status: Job 상태 (필터)
            step: STEP (필터)
            created_by: 생성자 (필터)
            limit: 페이지 크기
            offset: 오프셋

        Returns:
            (jobs 리스트, 총 개수) 튜플

        Raises:
            TenopAPIError: 조회 실패 시
        """
        try:
            query = self.db.table("jobs").select("*", count="exact")

            # 필터 적용
            if proposal_id:
                query = query.eq("proposal_id", str(proposal_id))
            if status:
                query = query.eq("status", status.value)
            if step:
                query = query.eq("step", step)
            if created_by:
                query = query.eq("created_by", str(created_by))

            # 정렬 및 페이징
            response = await query.order(
                "created_at", ascending=False
            ).range(offset, offset + limit - 1)

            jobs = [self._row_to_job(row) for row in response.data] if response.data else []
            total = response.count or 0

            return jobs, total

        except Exception as e:
            self.logger.error(f"Failed to get jobs list: {e}")
            raise TenopAPIError(
                error_code="JOB_LIST_FAILED",
                message=f"Failed to get jobs: {str(e)}",
                status_code=500,
            ) from e

    # ========================================
    # State Transitions
    # ========================================

    async def mark_job_running(self, job_id: UUID, worker_id: str) -> bool:
        """
        Job 상태를 RUNNING으로 변경

        Args:
            job_id: Job ID
            worker_id: 워커 ID (예: "worker-1")

        Returns:
            성공 여부

        Raises:
            TenopAPIError: 상태 변경 실패 시
        """
        try:
            now = datetime.utcnow()

            await self.db.table("jobs").update({
                "status": JobStatus.RUNNING.value,
                "started_at": now.isoformat(),
                "assigned_worker_id": worker_id,
            }).eq("id", str(job_id))

            # 이벤트 기록
            await self._record_event(
                job_id,
                JobEventType.STARTED,
                {"worker_id": worker_id},
            )

            self.logger.info(f"Job {job_id} marked as RUNNING (worker={worker_id})")
            return True

        except Exception as e:
            self.logger.error(f"Failed to mark job {job_id} as running: {e}")
            raise TenopAPIError(
                error_code="JOB_RUNNING_FAILED",
                message=f"Failed to update job status: {str(e)}",
                status_code=500,
            ) from e

    async def mark_job_success(self, job_id: UUID, result: dict) -> bool:
        """
        Job 상태를 SUCCESS로 변경

        Args:
            job_id: Job ID
            result: 작업 결과

        Returns:
            성공 여부

        Raises:
            TenopAPIError: 상태 변경 실패 시
        """
        try:
            # 먼저 job을 조회하여 duration 계산
            job = await self.get_job(job_id)
            if not job:
                raise JobNotFoundError()

            duration = None
            if job.started_at:
                duration = (datetime.utcnow() - job.started_at).total_seconds()

            now = datetime.utcnow()

            # Job 상태 업데이트
            await self.db.table("jobs").update({
                "status": JobStatus.SUCCESS.value,
                "result": result,
                "completed_at": now.isoformat(),
                "duration_seconds": duration,
            }).eq("id", str(job_id))

            # Job Result 기록
            await self._save_job_result(job_id, result)

            # 메트릭 기록
            await self._record_metric(
                job_id=job_id,
                step=job.step,
                job_type=job.type.value,
                status=JobStatus.SUCCESS.value,
                duration_seconds=duration,
            )

            # 이벤트 기록
            await self._record_event(
                job_id,
                JobEventType.COMPLETED,
                {"duration_seconds": duration},
            )

            self.logger.info(
                f"Job {job_id} marked as SUCCESS "
                f"(duration={duration:.2f}s if duration else 'unknown')"
            )
            return True

        except Exception as e:
            self.logger.error(f"Failed to mark job {job_id} as success: {e}")
            raise TenopAPIError(
                error_code="JOB_SUCCESS_FAILED",
                message=f"Failed to update job result: {str(e)}",
                status_code=500,
            ) from e

    async def mark_job_failed(
        self,
        job_id: UUID,
        error: str,
        attempt: int,
    ) -> bool:
        """
        Job 상태를 FAILED로 변경 (또는 재시도를 위해 PENDING 유지)

        Args:
            job_id: Job ID
            error: 에러 메시지
            attempt: 현재 시도 횟수

        Returns:
            성공 여부

        Raises:
            TenopAPIError: 상태 변경 실패 시
        """
        try:
            job = await self.get_job(job_id)
            if not job:
                raise JobNotFoundError()

            now = datetime.utcnow()

            if attempt >= job.max_retries:
                # 최대 재시도 초과 → FAILED로 변경
                await self.db.table("jobs").update({
                    "status": JobStatus.FAILED.value,
                    "error": error[:500],  # 처음 500자만 저장
                    "completed_at": now.isoformat(),
                    "retries": attempt,
                }).eq("id", str(job_id))

                # 메트릭 기록
                await self._record_metric(
                    job_id=job_id,
                    step=job.step,
                    job_type=job.type.value,
                    status=JobStatus.FAILED.value,
                    duration_seconds=None,
                )

                # 이벤트 기록
                await self._record_event(
                    job_id,
                    JobEventType.FAILED,
                    {"error": error, "attempt": attempt, "max_retries": job.max_retries},
                )

                self.logger.error(
                    f"Job {job_id} FAILED after {attempt} attempts: {error}"
                )
            else:
                # 재시도 가능 → retries만 증가
                await self.db.table("jobs").update({
                    "retries": attempt,
                    "error": error[:500],  # 마지막 에러만 저장
                }).eq("id", str(job_id))

                # 이벤트 기록
                await self._record_event(
                    job_id,
                    JobEventType.RETRIED,
                    {
                        "error": error,
                        "attempt": attempt,
                        "next_attempt": attempt + 1,
                    },
                )

                self.logger.info(
                    f"Job {job_id} will retry "
                    f"(attempt {attempt + 1}/{job.max_retries}): {error}"
                )

            return True

        except Exception as e:
            self.logger.error(f"Failed to mark job {job_id} as failed: {e}")
            raise TenopAPIError(
                error_code="JOB_FAILED_UPDATE_FAILED",
                message=f"Failed to update job failure status: {str(e)}",
                status_code=500,
            ) from e

    async def cancel_job(self, job_id: UUID) -> bool:
        """
        Job 취소 (PENDING 또는 RUNNING → CANCELLED)

        Args:
            job_id: Job ID

        Returns:
            성공 여부

        Raises:
            JobCancelError: 취소 불가능한 상태
            JobNotFoundError: Job을 찾을 수 없음
        """
        try:
            job = await self.get_job(job_id)
            if not job:
                raise JobNotFoundError()

            # SUCCESS, FAILED, CANCELLED 상태는 취소 불가
            if job.status in [JobStatus.SUCCESS, JobStatus.FAILED, JobStatus.CANCELLED]:
                raise JobCancelError(
                    message=f"Cannot cancel job in {job.status.value} state"
                )

            now = datetime.utcnow()

            await self.db.table("jobs").update({
                "status": JobStatus.CANCELLED.value,
                "completed_at": now.isoformat(),
            }).eq("id", str(job_id))

            # 이벤트 기록
            await self._record_event(
                job_id,
                JobEventType.CANCELLED,
                {"cancelled_at": now.isoformat()},
            )

            self.logger.info(f"Job {job_id} cancelled")
            return True

        except (JobNotFoundError, JobCancelError):
            raise
        except Exception as e:
            self.logger.error(f"Failed to cancel job {job_id}: {e}")
            raise TenopAPIError(
                error_code="JOB_CANCEL_FAILED",
                message=f"Failed to cancel job: {str(e)}",
                status_code=500,
            ) from e

    # ========================================
    # Private Helpers
    # ========================================

    async def _save_to_db(self, job: Job) -> None:
        """Job을 DB에 저장"""
        await self.db.table("jobs").insert({
            "id": str(job.id),
            "proposal_id": str(job.proposal_id),
            "step": job.step,
            "type": job.type.value,
            "status": job.status.value,
            "priority": job.priority.value,
            "payload": job.payload,
            "retries": job.retries,
            "max_retries": job.max_retries,
            "created_at": job.created_at.isoformat(),
            "created_by": str(job.created_by),
            "tags": job.tags,
        })

    async def _save_job_result(self, job_id: UUID, result: dict) -> None:
        """Job 결과를 job_results 테이블에 저장"""
        try:
            await self.db.table("job_results").insert({
                "job_id": str(job_id),
                "result_data": result,
                "saved_at": datetime.utcnow().isoformat(),
            })
        except Exception as e:
            self.logger.warning(f"Failed to save job result for {job_id}: {e}")

    async def _record_metric(
        self,
        job_id: UUID,
        step: str,
        job_type: str,
        status: str,
        duration_seconds: Optional[float] = None,
        memory_mb: Optional[float] = None,
        cpu_percent: Optional[float] = None,
        worker_id: Optional[str] = None,
    ) -> None:
        """Job 성과 메트릭 기록"""
        try:
            await self.db.table("job_metrics").insert({
                "job_id": str(job_id),
                "step": step,
                "type": job_type,
                "status": status,
                "duration_seconds": duration_seconds,
                "memory_mb": memory_mb,
                "cpu_percent": cpu_percent,
                "worker_id": worker_id,
                "recorded_at": datetime.utcnow().isoformat(),
            })
        except Exception as e:
            self.logger.warning(f"Failed to record metric for job {job_id}: {e}")

    async def _record_event(
        self,
        job_id: UUID,
        event_type: JobEventType,
        details: dict = None,
    ) -> None:
        """Job 이벤트 기록"""
        try:
            await self.db.table("job_events").insert({
                "job_id": str(job_id),
                "event_type": event_type.value,
                "details": details or {},
                "occurred_at": datetime.utcnow().isoformat(),
            })
        except Exception as e:
            self.logger.warning(f"Failed to record event for job {job_id}: {e}")

    def _row_to_job(self, row: dict) -> Job:
        """DB 행을 Job 객체로 변환"""
        return Job(
            id=UUID(row["id"]),
            proposal_id=UUID(row["proposal_id"]),
            step=row["step"],
            type=JobType(row["type"]),
            status=JobStatus(row["status"]),
            priority=JobPriority(row["priority"]),
            payload=row.get("payload") or {},
            result=row.get("result"),
            error=row.get("error"),
            retries=row.get("retries", 0),
            max_retries=row.get("max_retries", 3),
            created_at=self._parse_datetime(row["created_at"]),
            started_at=self._parse_datetime(row.get("started_at")),
            completed_at=self._parse_datetime(row.get("completed_at")),
            duration_seconds=row.get("duration_seconds"),
            created_by=UUID(row["created_by"]),
            assigned_worker_id=row.get("assigned_worker_id"),
            tags=row.get("tags") or {},
            updated_at=self._parse_datetime(row.get("updated_at")),
        )

    @staticmethod
    def _extract_step(job_type: JobType) -> str:
        """JobType에서 STEP 추출 (예: STEP4A_DIAGNOSIS → "4a")"""
        type_str = job_type.value  # "step4a_diagnosis"
        parts = type_str.split("_")
        if parts[0].startswith("step"):
            return parts[0][4:]  # "4a"
        return "unknown"

    @staticmethod
    def _parse_datetime(value) -> Optional[datetime]:
        """문자열을 datetime으로 파싱"""
        if not value:
            return None
        if isinstance(value, datetime):
            return value
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None


__all__ = [
    "JobQueueService",
    "JobNotFoundError",
    "InvalidJobStateError",
    "JobCancelError",
    "JobRetryError",
]
