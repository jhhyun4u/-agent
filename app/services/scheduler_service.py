"""
정기 문서 마이그레이션 스케줄러 서비스

기능:
- APScheduler를 사용한 정기 스케줄 관리
- 배치 작업 생성 및 실행
- 변경 감지 기반 선택적 마이그레이션
- 배치 진행률 추적
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from postgrest import AsyncPostgrestClient

logger = logging.getLogger(__name__)


class SchedulerService:
    """정기 문서 마이그레이션 스케줄러"""

    def __init__(self, db_client: AsyncPostgrestClient):
        """
        초기화

        Args:
            db_client: Supabase PostgreSQL 클라이언트
        """
        self.db = db_client
        self.scheduler = AsyncIOScheduler()
        self._jobs = {}  # {schedule_id: APScheduler job}
        self._batch_processor = None

    async def initialize(self):
        """
        서버 시작 시 모든 활성 스케줄 복구 및 시작

        이전에 생성된 스케줄을 데이터베이스에서 조회하여
        APScheduler에 등록합니다.
        """
        try:
            schedules = await self._get_active_schedules()
            for schedule in schedules:
                await self.add_job(schedule)

            if not self.scheduler.running:
                self.scheduler.start()
                logger.info(f"Scheduler initialized with {len(schedules)} active jobs")
        except Exception as e:
            logger.error(f"Failed to initialize scheduler: {e}", exc_info=True)
            raise

    async def add_schedule(
        self,
        name: str,
        cron_expression: str,
        source_type: str,
        enabled: bool = True,
    ) -> UUID:
        """
        새 마이그레이션 스케줄 등록

        Args:
            name: 스케줄 이름
            cron_expression: Cron 표현식 (예: "0 0 1 * *" = 매달 1일 자정)
            source_type: 소스 타입 (예: "intranet")
            enabled: 활성화 여부

        Returns:
            생성된 스케줄 UUID
        """
        schedule_id = uuid4()

        data = {
            "id": str(schedule_id),
            "name": name,
            "cron_expression": cron_expression,
            "source_type": source_type,
            "enabled": enabled,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

        await self.db.table("migration_schedules").insert(data).execute()

        if enabled:
            schedule_dict = {
                "id": schedule_id,
                "name": name,
                "cron_expression": cron_expression,
                "source_type": source_type,
            }
            await self.add_job(schedule_dict)

        logger.info(f"Schedule created: {name} ({schedule_id})")
        return schedule_id

    async def trigger_migration_now(self, schedule_id: UUID) -> UUID:
        """
        즉시 마이그레이션 트리거

        Args:
            schedule_id: 스케줄 UUID

        Returns:
            생성된 배치 UUID
        """
        batch_id = await self._create_batch(schedule_id)
        await self._run_batch(batch_id, schedule_id)
        return batch_id

    async def add_job(self, schedule: dict):
        """
        APScheduler에 배치 작업 등록

        Args:
            schedule: 스케줄 정보 딕셔너리
        """
        schedule_id = schedule["id"]
        cron_expr = schedule["cron_expression"]

        try:
            job = self.scheduler.add_job(
                self._batch_job_runner,
                trigger=CronTrigger.from_crontab(cron_expr),
                args=[schedule_id],
                id=str(schedule_id),
                replace_existing=True,
            )
            self._jobs[schedule_id] = job
            logger.info(f"Job added: {schedule['name']} with cron: {cron_expr}")
        except Exception as e:
            logger.error(f"Failed to add job {schedule_id}: {e}", exc_info=True)
            raise

    async def remove_job(self, schedule_id: UUID):
        """
        APScheduler에서 배치 작업 제거

        Args:
            schedule_id: 스케줄 UUID
        """
        if schedule_id in self._jobs:
            self._jobs[schedule_id].remove()
            del self._jobs[schedule_id]
            logger.info(f"Job removed: {schedule_id}")

    async def get_schedules(self) -> List[Dict[str, Any]]:
        """
        모든 스케줄 조회

        Returns:
            스케줄 정보 리스트
        """
        result = (
            await self.db.table("migration_schedules")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return result.data

    async def get_batches(
        self, limit: int = 20, offset: int = 0
    ) -> Dict[str, Any]:
        """
        배치 이력 조회 (페이지네이션)

        Args:
            limit: 조회 수
            offset: 오프셋

        Returns:
            배치 정보 및 메타데이터
        """
        # Get total count
        count_result = (
            await self.db.table("migration_batches")
            .select("id", count="exact")
            .execute()
        )
        total = count_result.count or 0

        # Get paginated data
        result = (
            await self.db.table("migration_batches")
            .select("*")
            .order("created_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )

        return {"total": total, "limit": limit, "offset": offset, "data": result.data}

    async def get_batch_detail(self, batch_id: UUID) -> Dict[str, Any]:
        """
        배치 상세 정보 조회

        Args:
            batch_id: 배치 UUID

        Returns:
            배치 정보
        """
        result = (
            await self.db.table("migration_batches")
            .select("*")
            .eq("id", str(batch_id))
            .single()
            .execute()
        )
        return result.data

    async def get_batch_logs(
        self, batch_id: UUID, status: Optional[str] = None, limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        배치의 개별 문서 처리 로그 조회

        Args:
            batch_id: 배치 UUID
            status: 필터링할 상태 (옵션)
            limit: 조회 수

        Returns:
            마이그레이션 로그 리스트
        """
        query = self.db.table("migration_logs").select("*").eq("batch_id", str(batch_id))

        if status:
            query = query.eq("status", status)

        result = await query.order("processed_at", desc=True).limit(limit).execute()

        return result.data

    # Private Methods

    async def _batch_job_runner(self, schedule_id: UUID):
        """
        배치 작업 실행 (APScheduler 콜백)

        Args:
            schedule_id: 스케줄 UUID
        """
        try:
            logger.info(f"Starting batch job for schedule: {schedule_id}")
            batch_id = await self._create_batch(schedule_id)
            await self._run_batch(batch_id, schedule_id)
            await self._mark_schedule_run(schedule_id)
            logger.info(f"Batch job completed: {batch_id}")
        except Exception as e:
            logger.error(f"Batch job failed for schedule {schedule_id}: {e}", exc_info=True)
            await self._update_batch_status(batch_id, "failed", str(e))

    async def _create_batch(self, schedule_id: UUID) -> UUID:
        """
        배치 레코드 생성

        Args:
            schedule_id: 스케줄 UUID

        Returns:
            생성된 배치 UUID
        """
        batch_id = uuid4()
        data = {
            "id": str(batch_id),
            "schedule_id": str(schedule_id),
            "status": "pending",
            "total_documents": 0,
            "processed_documents": 0,
            "failed_documents": 0,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.db.table("migration_batches").insert(data).execute()
        return batch_id

    async def _run_batch(self, batch_id: UUID, schedule_id: UUID):
        """
        배치 실행

        Args:
            batch_id: 배치 UUID
            schedule_id: 스케줄 UUID
        """
        from app.services.batch_processor import ConcurrentBatchProcessor

        try:
            # Mark batch as running
            await self.db.table("migration_batches").update(
                {
                    "status": "running",
                    "started_at": datetime.now(timezone.utc).isoformat(),
                }
            ).eq("id", str(batch_id)).execute()

            # Fetch documents to migrate
            documents = await self._fetch_documents_to_migrate(schedule_id)

            # Update batch with total count
            await self.db.table("migration_batches").update(
                {"total_documents": len(documents)}
            ).eq("id", str(batch_id)).execute()

            # Process batch
            processor = ConcurrentBatchProcessor(db_client=self.db, num_workers=5, max_retries=3)
            result = await processor.process_batch(documents, batch_id)

            # Update batch status
            final_status = "success" if result["failed"] == 0 else "partial"
            await self.db.table("migration_batches").update(
                {
                    "status": final_status,
                    "processed_documents": result["processed"],
                    "failed_documents": result["failed"],
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "duration_seconds": result["duration"],
                }
            ).eq("id", str(batch_id)).execute()

            logger.info(
                f"Batch {batch_id} completed: {result['processed']} processed, "
                f"{result['failed']} failed ({result['duration']}s)"
            )

        except Exception as e:
            logger.error(f"Batch {batch_id} failed: {e}", exc_info=True)
            await self._update_batch_status(batch_id, "failed", str(e))

    async def _fetch_documents_to_migrate(self, schedule_id: UUID) -> List[Dict[str, Any]]:
        """
        마이그레이션할 문서 조회 (변경 감지 기반)

        Args:
            schedule_id: 스케줄 UUID

        Returns:
            문서 리스트
        """
        # Get last successful batch
        last_batch_result = (
            await self.db.table("migration_batches")
            .select("completed_at")
            .eq("schedule_id", str(schedule_id))
            .eq("status", "success")
            .order("completed_at", desc=True)
            .limit(1)
            .execute()
        )

        sync_since = None
        if last_batch_result.data:
            sync_since = last_batch_result.data[0]["completed_at"]

        # For now, return empty list (actual implementation would fetch from intranet)
        # This is a placeholder for the real document fetch logic
        logger.info(f"Fetching documents modified since: {sync_since}")

        return []

    async def _get_active_schedules(self) -> List[Dict[str, Any]]:
        """
        활성 스케줄 조회

        Returns:
            활성 스케줄 리스트
        """
        result = (
            await self.db.table("migration_schedules")
            .select("*")
            .eq("enabled", True)
            .execute()
        )
        return result.data

    async def _mark_schedule_run(self, schedule_id: UUID):
        """
        스케줄 마지막 실행 시간 갱신

        Args:
            schedule_id: 스케줄 UUID
        """
        now = datetime.now(timezone.utc).isoformat()
        await self.db.table("migration_schedules").update(
            {"last_run_at": now, "updated_at": now}
        ).eq("id", str(schedule_id)).execute()

    async def _update_batch_status(self, batch_id: UUID, status: str, error_message: str = None):
        """
        배치 상태 업데이트

        Args:
            batch_id: 배치 UUID
            status: 새로운 상태
            error_message: 에러 메시지 (옵션)
        """
        update_data = {
            "status": status,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        if error_message:
            update_data["error_message"] = error_message

        await self.db.table("migration_batches").update(update_data).eq(
            "id", str(batch_id)
        ).execute()


async def get_scheduler_service(db_client: AsyncPostgrestClient) -> SchedulerService:
    """의존성 주입: SchedulerService"""
    return SchedulerService(db_client)
