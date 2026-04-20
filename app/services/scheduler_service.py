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
            await self.db.table("migration_batches").update({
                "status": "processing",
                "started_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", batch_id).execute()
            await self.db.table("migration_batches").update({
                "status": "completed",
                "completed_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", batch_id).execute()
        except Exception as e:
            self.logger.error(f"Batch execution failed: {e}")
            await self.db.table("migration_batches").update({
                "status": "failed",
                "error_message": str(e),
                "completed_at": datetime.now(timezone.utc).isoformat()
            }).eq("id", batch_id).execute()
            raise

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

    async def start(self):
        if not self.scheduler.running:
            self.scheduler.start()

    async def stop(self):
        if self.scheduler.running:
            self.scheduler.shutdown()
