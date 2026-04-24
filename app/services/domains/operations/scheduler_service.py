import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from supabase import AsyncClient as AsyncSupabaseClient

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, db_client: AsyncSupabaseClient, intranet_client: Optional[Any] = None):
        self.db = db_client
        self.intranet = intranet_client
        self.logger = logger
        self.scheduler = AsyncIOScheduler()
        self._jobs = {}

    async def initialize(self):
        try:
            schedules = await self._get_active_schedules()
            for schedule in schedules:
                await self.add_job(schedule)
            self.logger.info(f"Scheduler initialized with {len(schedules)} schedules")
        except Exception as e:
            self.logger.error(f"Scheduler init failed: {e}")

    async def add_schedule(self, name: str, cron_expression: str, source_type: str = "intranet", enabled: bool = True) -> str:
        schedule_id = str(uuid4())
        try:
            await self.db.table("migration_schedule").insert({
                "id": schedule_id,
                "schedule_name": name,
                "cron_expression": cron_expression,
                "source_type": source_type,
                "enabled": enabled,
                "created_at": datetime.now(timezone.utc).isoformat()
            }).execute()
            if enabled:
                await self.add_job({"id": schedule_id, "cron_expression": cron_expression})
            return schedule_id
        except Exception as e:
            self.logger.error(f"Failed to create schedule: {e}")
            raise

    async def trigger_migration_now(self, schedule_id: str) -> str:
        try:
            batch_id = await self._create_batch(schedule_id)
            await self._run_batch(batch_id)
            return batch_id
        except Exception as e:
            self.logger.error(f"Migration trigger failed: {e}")
            raise

    async def add_job(self, schedule: Dict[str, Any]):
        try:
            schedule_id = schedule.get("id")
            cron_expr = schedule.get("cron_expression")
            if not schedule_id or not cron_expr:
                return
            job = self.scheduler.add_job(
                self._batch_job_runner,
                trigger=CronTrigger.from_crontab(cron_expr),
                args=[schedule_id],
                id=schedule_id,
                replace_existing=True
            )
            self._jobs[schedule_id] = job
        except Exception as e:
            self.logger.error(f"Failed to add job: {e}")

    async def remove_job(self, schedule_id: str):
        try:
            if schedule_id in self._jobs:
                self._jobs[schedule_id].remove()
                del self._jobs[schedule_id]
        except Exception as e:
            self.logger.error(f"Failed to remove job: {e}")

    async def _batch_job_runner(self, schedule_id: str):
        try:
            batch_id = await self._create_batch(schedule_id)
            await self._run_batch(batch_id)
            await self._mark_schedule_run(schedule_id, batch_id)
        except Exception as e:
            self.logger.error(f"Batch job failed: {e}")

    async def _create_batch(self, schedule_id: str) -> str:
        batch_id = str(uuid4())
        try:
            await self.db.table("migration_batches").insert({
                "id": batch_id,
                "schedule_id": schedule_id,
                "batch_name": f"Batch-{batch_id[:8]}",
                "status": "pending",
                "scheduled_at": datetime.now(timezone.utc).isoformat(),
                "created_by": "system",
                "source_system": "intranet"
            }).execute()
            return batch_id
        except Exception as e:
            self.logger.error(f"Batch creation failed: {e}")
            raise

    async def _run_batch(self, batch_id: str):
        try:
            # Mark batch as processing
            await self.db.table("migration_batches").update({
                "status": "processing",
                "started_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", batch_id).execute()

            # Fetch documents to migrate
            documents = await self._fetch_documents_to_migrate()

            if not documents:
                self.logger.info(f"No documents to migrate for batch {batch_id}")
                await self.db.table("migration_batches").update({
                    "status": "completed",
                    "completed_at": datetime.now(timezone.utc).isoformat(),
                    "total_documents": 0,
                    "processed_documents": 0,
                    "failed_documents": 0
                }).eq("id", batch_id).execute()
                return

            # Process batch with ConcurrentBatchProcessor
            from app.services.domains.bidding.batch_processor import ConcurrentBatchProcessor
            processor = ConcurrentBatchProcessor(
                db_client=self.db,
                num_workers=5,
                max_retries=3
            )

            result = await processor.process_batch(documents, batch_id)
            processor.shutdown()

            # Update batch with results
            await self.db.table("migration_batches").update({
                "status": "completed" if result["status"] == "success" else "partial_failed",
                "completed_at": datetime.now(timezone.utc).isoformat(),
                "total_documents": len(documents),
                "processed_documents": result["processed"],
                "failed_documents": result["failed"]
            }).eq("id", batch_id).execute()

            self.logger.info(
                f"Batch {batch_id} completed: "
                f"{result['processed']} processed, {result['failed']} failed"
            )

        except Exception as e:
            self.logger.error(f"Batch execution failed: {e}", exc_info=True)
            await self.db.table("migration_batches").update({
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", batch_id).execute()

    async def _fetch_documents_to_migrate(self) -> List[Dict]:
        """Fetch documents modified since last migration"""
        try:
            # Get last successful migration timestamp
            result = await self.db.table("migration_batches").select(
                "completed_at"
            ).eq(
                "status", "completed"
            ).order(
                "completed_at", ascending=False
            ).limit(1).execute()

            sync_since = None
            if result.data and len(result.data) > 0:
                sync_since = result.data[0].get("completed_at")

            # TODO: Fetch from intranet API based on sync_since
            # For now, return empty list (Phase 6 implementation)
            # In production, call:
            # documents = await self.intranet.fetch_documents(modified_since=sync_since)

            self.logger.info(f"Fetching documents modified since: {sync_since}")
            return []  # TODO: Replace with actual intranet API call

        except Exception as e:
            self.logger.error(f"Failed to fetch documents: {e}", exc_info=True)
            return []

    async def _mark_schedule_run(self, schedule_id: str, batch_id: str):
        try:
            await self.db.table("migration_schedule").update({
                "last_run_at": datetime.now(timezone.utc).isoformat(),
                "last_batch_id": batch_id
            }).eq("id", schedule_id).execute()
        except Exception as e:
            self.logger.error(f"Mark schedule run failed: {e}")

    async def _get_active_schedules(self) -> List[Dict]:
        try:
            result = await self.db.table("migration_schedule").select("*").eq("enabled", True).execute()
            return result.data or []
        except Exception as e:
            self.logger.error(f"Get schedules failed: {e}")
            return []

    async def get_batch_status(self, batch_id: str) -> Optional[Dict]:
        try:
            result = await self.db.table("migration_batches").select("*").eq("id", batch_id).single().execute()
            return result.data
        except Exception as e:
            self.logger.error(f"Get batch status failed: {e}")
            return None

    async def get_schedules(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        try:
            result = await self.db.table("migration_schedule").select("*").range(offset, offset + limit - 1).execute()
            return result.data or []
        except Exception as e:
            self.logger.error(f"Get schedules failed: {e}")
            return []

    async def get_batches(self, limit: int = 50, offset: int = 0) -> List[Dict]:
        try:
            result = await self.db.table("migration_batches").select("*").range(offset, offset + limit - 1).execute()
            return result.data or []
        except Exception as e:
            self.logger.error(f"Get batches failed: {e}")
            return []

    async def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    async def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()


# ============================================
# Dependency Injection
# ============================================

async def get_scheduler_service(db_client=None) -> SchedulerService:
    """
    Dependency injection for SchedulerService

    Args:
        db_client: Optional Supabase async client (use default if not provided)

    Returns:
        SchedulerService instance
    """
    if db_client is None:
        from app.utils.supabase_client import get_async_client
        db_client = await get_async_client()

    return SchedulerService(db_client)
