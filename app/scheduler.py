"""
APScheduler 스케줄러 초기화 및 관리

배치 마이그레이션 및 정기 작업 실행
"""

import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

logger = logging.getLogger(__name__)

# 전역 스케줄러 인스턴스
_scheduler: AsyncIOScheduler = None


def get_scheduler() -> AsyncIOScheduler:
    """스케줄러 인스턴스 반환"""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def init_scheduler():
    """스케줄러 초기화 및 작업 등록"""
    scheduler = get_scheduler()

    if scheduler.running:
        logger.info("Scheduler already running")
        return

    logger.info("Initializing scheduler...")

    # 작업 등록
    _register_jobs(scheduler)

    # 스케줄러 시작
    scheduler.start()
    logger.info("Scheduler started")


async def shutdown_scheduler():
    """스케줄러 종료"""
    scheduler = get_scheduler()
    if scheduler.running:
        scheduler.shutdown(wait=True)
        logger.info("Scheduler stopped")


def _register_jobs(scheduler: AsyncIOScheduler):
    """작업 등록"""
    from app.jobs.migration_jobs import run_scheduled_migration

    # 매월 첫째 날 자정에 실행 (0 0 1 * *)
    scheduler.add_job(
        run_scheduled_migration,
        trigger=CronTrigger(hour=0, minute=0, day=1),
        id="monthly_migration",
        name="Monthly intranet document migration",
        replace_existing=True,
        coalesce=True,
        max_instances=1,
    )

    logger.info("Registered job: monthly_migration (0 0 1 * *)")
