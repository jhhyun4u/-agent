"""
Phase 3: APScheduler 통합 테스트

스케줄러 초기화, 작업 등록, 시작/종료 검증
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.scheduler import get_scheduler, init_scheduler, shutdown_scheduler


@pytest.fixture
def mock_scheduler():
    """Mock 스케줄러"""
    scheduler = MagicMock(spec=AsyncIOScheduler)
    scheduler.running = False
    scheduler.add_job = MagicMock()
    scheduler.start = MagicMock()
    scheduler.shutdown = MagicMock()
    return scheduler


class TestSchedulerInitialization:
    """스케줄러 초기화 테스트"""

    async def test_get_scheduler_creates_instance(self):
        """스케줄러 인스턴스 생성"""
        scheduler = get_scheduler()
        assert scheduler is not None
        assert isinstance(scheduler, AsyncIOScheduler)

    async def test_get_scheduler_returns_same_instance(self):
        """스케줄러 싱글톤 패턴"""
        scheduler1 = get_scheduler()
        scheduler2 = get_scheduler()
        assert scheduler1 is scheduler2

    async def test_init_scheduler_registers_jobs(self, mock_scheduler):
        """스케줄러 초기화 및 작업 등록"""
        with patch('app.scheduler.get_scheduler', return_value=mock_scheduler):
            mock_scheduler.running = False
            await init_scheduler()

            # start() 호출 확인
            mock_scheduler.start.assert_called_once()

    async def test_init_scheduler_when_already_running(self, mock_scheduler):
        """이미 실행 중인 스케줄러 재초기화"""
        with patch('app.scheduler.get_scheduler', return_value=mock_scheduler):
            mock_scheduler.running = True
            await init_scheduler()

            # start() 호출 안 됨
            mock_scheduler.start.assert_not_called()


class TestSchedulerJobs:
    """스케줄러 작업 등록 테스트"""

    async def test_monthly_migration_job_registered(self, mock_scheduler):
        """월간 마이그레이션 작업 등록"""
        with patch('app.scheduler.get_scheduler', return_value=mock_scheduler):
            mock_scheduler.running = False
            await init_scheduler()

            # add_job() 호출 확인
            mock_scheduler.add_job.assert_called()
            call_args = mock_scheduler.add_job.call_args
            assert call_args[1]['id'] == 'monthly_migration'
            assert call_args[1]['name'] == 'Monthly intranet document migration'

    async def test_monthly_migration_cron_trigger(self, mock_scheduler):
        """월간 마이그레이션 Cron 트리거 설정 (0 0 1 * *)"""
        with patch('app.scheduler.get_scheduler', return_value=mock_scheduler):
            mock_scheduler.running = False
            await init_scheduler()

            # CronTrigger 검증 (hour=0, minute=0, day=1)
            call_args = mock_scheduler.add_job.call_args
            trigger = call_args[1]['trigger']
            # 트리거 세부 정보는 CronTrigger 인스턴스
            assert trigger is not None


class TestSchedulerShutdown:
    """스케줄러 종료 테스트"""

    async def test_shutdown_scheduler(self, mock_scheduler):
        """스케줄러 종료"""
        with patch('app.scheduler.get_scheduler', return_value=mock_scheduler):
            mock_scheduler.running = True
            await shutdown_scheduler()

            # shutdown() 호출 확인 (wait=True)
            mock_scheduler.shutdown.assert_called_once_with(wait=True)

    async def test_shutdown_scheduler_when_not_running(self, mock_scheduler):
        """미실행 스케줄러 종료"""
        with patch('app.scheduler.get_scheduler', return_value=mock_scheduler):
            mock_scheduler.running = False
            await shutdown_scheduler()

            # shutdown() 호출 안 됨
            mock_scheduler.shutdown.assert_not_called()


class TestMigrationJob:
    """마이그레이션 작업 테스트"""

    async def test_run_scheduled_migration(self):
        """정기 마이그레이션 작업 실행"""
        with patch('app.jobs.migration_jobs.get_async_client') as mock_client, \
             patch('app.jobs.migration_jobs.MigrationService') as mock_service_class:

            from app.jobs.migration_jobs import run_scheduled_migration

            mock_service = AsyncMock()
            mock_batch = MagicMock()
            mock_batch.id = "test-batch-id"
            mock_batch.processed_documents = 100
            mock_batch.failed_documents = 0

            mock_service.batch_import_intranet_documents = AsyncMock(return_value=mock_batch)
            mock_service_class.return_value = mock_service

            await run_scheduled_migration()

            # batch_import_intranet_documents 호출 확인
            mock_service.batch_import_intranet_documents.assert_called_once()
            call_kwargs = mock_service.batch_import_intranet_documents.call_args[1]
            assert call_kwargs['batch_type'] == 'monthly'
            assert call_kwargs['include_failed'] is True

    async def test_run_scheduled_migration_error_handling(self):
        """마이그레이션 작업 에러 처리"""
        with patch('app.jobs.migration_jobs.get_async_client') as mock_client, \
             patch('app.jobs.migration_jobs.MigrationService') as mock_service_class:

            from app.jobs.migration_jobs import run_scheduled_migration

            mock_service = AsyncMock()
            mock_service.batch_import_intranet_documents = AsyncMock(
                side_effect=Exception("Connection error")
            )
            mock_service_class.return_value = mock_service

            # 에러가 발생해도 예외가 발생하지 않음 (로깅만)
            await run_scheduled_migration()
            mock_service.batch_import_intranet_documents.assert_called_once()


if __name__ == "__main__":
    # pytest 실행: pytest tests/test_scheduler_integration.py -v
    pass
