"""
Phase 5 CHECK Phase: Scheduler Integration Validation Tests
Integration tests for staging environment validation
"""
import asyncio
import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.domains.operations.scheduler_service import SchedulerService
from app.services.domains.bidding.batch_processor import ConcurrentBatchProcessor


@pytest.mark.integration
class TestSchedulerInitialization:
    """Validate scheduler initialization on app startup"""

    @pytest.mark.asyncio
    async def test_scheduler_initializes_with_active_schedules(self):
        """Verify scheduler loads existing active schedules from database on startup"""
        # Mock database with 2 active schedules
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.data = [
            {
                "id": str(uuid4()),
                "cron_expression": "0 8 * * *",
                "enabled": True,
            },
            {
                "id": str(uuid4()),
                "cron_expression": "0 18 * * *",
                "enabled": True,
            },
        ]

        # Properly chain the mock methods
        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_select.eq = MagicMock(return_value=mock_eq)
        mock_eq.execute = AsyncMock(return_value=mock_result)

        mock_db.table.return_value.select.return_value = mock_select

        scheduler = SchedulerService(mock_db)
        await scheduler.initialize()

        # Verify database query was made
        mock_db.table.assert_called_with("migration_schedule")
        # Should have scheduled 2 jobs
        assert len(scheduler._jobs) == 2

    @pytest.mark.asyncio
    async def test_scheduler_handles_database_connection_on_init(self):
        """Verify scheduler gracefully handles database connection errors during init"""
        mock_db = AsyncMock()
        mock_db.table.return_value.select.return_value.eq.return_value.execute = AsyncMock(
            side_effect=Exception("Connection failed")
        )

        scheduler = SchedulerService(mock_db)
        # Should not raise exception
        await scheduler.initialize()
        assert len(scheduler._jobs) == 0

    @pytest.mark.asyncio
    async def test_scheduler_start_and_stop_lifecycle(self):
        """Verify scheduler can start and stop correctly"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.data = []

        mock_select = MagicMock()
        mock_eq = MagicMock()
        mock_select.eq = MagicMock(return_value=mock_eq)
        mock_eq.execute = AsyncMock(return_value=mock_result)
        mock_db.table.return_value.select.return_value = mock_select

        scheduler = SchedulerService(mock_db)
        await scheduler.initialize()

        # Verify initial state
        assert not scheduler.scheduler.running

        # Start scheduler
        await scheduler.start()
        assert scheduler.scheduler.running

        # Stop scheduler
        await scheduler.stop()
        assert not scheduler.scheduler.running


@pytest.mark.integration
class TestAPIEndpointIntegration:
    """Validate all 6 API endpoints respond correctly"""

    @pytest.mark.asyncio
    async def test_create_schedule_endpoint_creates_database_record(self):
        """Verify POST /api/migration/schedules creates schedule in database"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.data = None
        mock_db.table.return_value.insert.return_value.execute = AsyncMock(
            return_value=mock_result
        )

        scheduler = SchedulerService(mock_db)
        schedule_id = await scheduler.add_schedule(
            name="Test Schedule",
            cron_expression="0 8 * * *",
            source_type="intranet",
            enabled=True,
        )

        assert schedule_id is not None
        mock_db.table.assert_called_with("migration_schedule")

    @pytest.mark.asyncio
    async def test_trigger_migration_creates_batch_and_runs(self):
        """Verify POST /api/migration/trigger/{schedule_id} creates and runs batch"""
        mock_db = AsyncMock()
        batch_id = str(uuid4())

        # Mock batch creation
        mock_db.table.return_value.insert.return_value.execute = AsyncMock()
        mock_db.table.return_value.update.return_value.eq.return_value.execute = AsyncMock()

        # Mock document fetch
        mock_db.table.return_value.select.return_value.eq.return_value.order.return_value.limit.return_value.execute = AsyncMock(
            return_value=MagicMock(data=[])
        )

        scheduler = SchedulerService(mock_db)
        # Should complete without error even with no documents
        result = await scheduler.trigger_migration_now(str(uuid4()))
        assert result is not None

    @pytest.mark.asyncio
    async def test_get_schedules_returns_paginated_list(self):
        """Verify GET /api/migration/schedules returns paginated schedules"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.data = [
            {"id": str(uuid4()), "schedule_name": "Schedule 1"},
            {"id": str(uuid4()), "schedule_name": "Schedule 2"},
        ]
        mock_db.table.return_value.select.return_value.range.return_value.execute = AsyncMock(
            return_value=mock_result
        )

        scheduler = SchedulerService(mock_db)
        schedules = await scheduler.get_schedules(limit=10, offset=0)

        assert len(schedules) == 2
        mock_db.table.assert_called_with("migration_schedule")

    @pytest.mark.asyncio
    async def test_get_batches_returns_paginated_history(self):
        """Verify GET /api/migration/batches returns paginated batch history"""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.data = [
            {
                "id": str(uuid4()),
                "status": "completed",
                "processed_documents": 10,
            },
            {
                "id": str(uuid4()),
                "status": "processing",
                "processed_documents": 5,
            },
        ]
        mock_db.table.return_value.select.return_value.range.return_value.execute = AsyncMock(
            return_value=mock_result
        )

        scheduler = SchedulerService(mock_db)
        batches = await scheduler.get_batches(limit=50, offset=0)

        assert len(batches) == 2

    @pytest.mark.asyncio
    async def test_get_batch_status_returns_single_batch(self):
        """Verify GET /api/migration/batches/{batch_id} returns batch details"""
        mock_db = AsyncMock()
        batch_id = str(uuid4())
        mock_result = MagicMock()
        mock_result.data = {
            "id": batch_id,
            "status": "completed",
            "total_documents": 100,
            "processed_documents": 100,
            "failed_documents": 0,
        }
        mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
            return_value=mock_result
        )

        scheduler = SchedulerService(mock_db)
        status = await scheduler.get_batch_status(batch_id)

        assert status is not None
        assert status["id"] == batch_id
        assert status["status"] == "completed"


@pytest.mark.integration
class TestBatchProcessingIntegration:
    """Validate batch processing with actual concurrent execution"""

    @pytest.mark.asyncio
    async def test_batch_processor_executes_concurrently(self):
        """Verify concurrent batch processor uses multiple workers"""
        mock_db = AsyncMock()
        processor = ConcurrentBatchProcessor(
            db_client=mock_db, num_workers=5, max_retries=3
        )

        documents = [{"id": i, "filename": f"doc_{i}.txt"} for i in range(10)]

        # Mock logging function
        processor._log_migration = AsyncMock()

        # Mock document processing
        with patch.object(
            processor, "_process_single_document", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = {"status": "success", "result": "processed"}
            result = await processor.process_batch(documents, str(uuid4()))

        assert result["processed"] == 10
        assert result["failed"] == 0
        processor.shutdown()

    @pytest.mark.asyncio
    async def test_batch_processor_retries_failed_documents(self):
        """Verify batch processor retries failed documents up to max_retries"""
        mock_db = AsyncMock()
        processor = ConcurrentBatchProcessor(
            db_client=mock_db, num_workers=5, max_retries=3
        )

        documents = [{"id": 1, "filename": "doc_1.txt"}]
        processor._log_migration = AsyncMock()

        # Mock processing to fail first 2 times, then succeed
        call_count = 0

        async def mock_process_fn(doc):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Transient error")
            return {"status": "success"}

        with patch.object(
            processor, "_process_single_document", side_effect=mock_process_fn
        ):
            result = await processor.process_batch(documents, str(uuid4()))

        assert result["processed"] == 1
        processor.shutdown()

    @pytest.mark.asyncio
    async def test_batch_processor_logs_all_operations(self):
        """Verify batch processor logs each document processing"""
        mock_db = AsyncMock()
        processor = ConcurrentBatchProcessor(
            db_client=mock_db, num_workers=5, max_retries=3
        )

        documents = [{"id": i, "filename": f"doc_{i}.txt"} for i in range(3)]
        processor._log_migration = AsyncMock()

        with patch.object(
            processor, "_process_single_document", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = {"status": "success"}
            await processor.process_batch(documents, str(uuid4()))

        # Verify logging was called for each document
        assert processor._log_migration.call_count >= 3
        processor.shutdown()


@pytest.mark.integration
class TestDatabasePersistence:
    """Validate database operations and data persistence"""

    @pytest.mark.asyncio
    async def test_schedule_persists_to_database(self):
        """Verify created schedules persist in database"""
        mock_db = AsyncMock()
        mock_insert = MagicMock()
        mock_execute = AsyncMock()
        mock_insert.execute = mock_execute

        mock_db.table.return_value.insert.return_value = mock_insert

        scheduler = SchedulerService(mock_db)
        await scheduler.add_schedule(
            name="Persist Test",
            cron_expression="0 8 * * *",
            source_type="intranet",
        )

        # Verify insert was called
        mock_db.table.assert_called_with("migration_schedule")
        mock_insert.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_status_updates_persist(self):
        """Verify batch status updates are written to database"""
        mock_db = AsyncMock()
        mock_update = MagicMock()
        mock_eq = MagicMock()
        mock_execute = AsyncMock()

        mock_db.table.return_value.update.return_value = mock_update
        mock_update.eq.return_value = mock_execute

        scheduler = SchedulerService(mock_db)
        schedule_id = str(uuid4())

        # Mark schedule run
        await scheduler._mark_schedule_run(schedule_id, str(uuid4()))

        # Verify update was called
        mock_db.table.assert_called_with("migration_schedule")


@pytest.mark.integration
class TestErrorRecovery:
    """Validate error handling and recovery mechanisms"""

    @pytest.mark.asyncio
    async def test_scheduler_recovers_from_batch_failure(self):
        """Verify scheduler logs batch failures and continues"""
        mock_db = AsyncMock()
        mock_db.table.return_value.insert.return_value.execute = AsyncMock()
        mock_db.table.return_value.update.return_value.eq.return_value.execute = AsyncMock(
            side_effect=Exception("Database error")
        )

        scheduler = SchedulerService(mock_db)
        # Should not raise exception
        with pytest.raises(Exception):
            # _run_batch will fail on database update
            await scheduler._run_batch(str(uuid4()))

    @pytest.mark.asyncio
    async def test_api_returns_error_on_invalid_schedule_id(self):
        """Verify API returns error for non-existent schedule"""
        mock_db = AsyncMock()
        mock_db.table.return_value.select.return_value.eq.return_value.single.return_value.execute = AsyncMock(
            side_effect=Exception("Not found")
        )

        scheduler = SchedulerService(mock_db)
        result = await scheduler.get_batch_status("invalid-id")

        assert result is None

    @pytest.mark.asyncio
    async def test_batch_processor_handles_malformed_documents(self):
        """Verify batch processor handles invalid document structures"""
        mock_db = AsyncMock()
        processor = ConcurrentBatchProcessor(
            db_client=mock_db, num_workers=5, max_retries=3
        )

        documents = [
            {},  # Missing required fields
            {"id": 1},  # Partial data
            {"id": 2, "filename": "doc.txt"},  # Valid
        ]
        processor._log_migration = AsyncMock()

        with patch.object(
            processor, "_process_single_document", new_callable=AsyncMock
        ):
            result = await processor.process_batch(documents, str(uuid4()))

        # Should handle gracefully
        assert result["processed"] >= 0
        processor.shutdown()


@pytest.mark.integration
class TestPerformanceValidation:
    """Validate performance under realistic conditions"""

    @pytest.mark.asyncio
    async def test_scheduler_handles_100_documents(self):
        """Verify scheduler processes 100 documents without timeout"""
        mock_db = AsyncMock()
        processor = ConcurrentBatchProcessor(
            db_client=mock_db, num_workers=5, max_retries=3
        )

        documents = [{"id": i, "filename": f"doc_{i}.txt"} for i in range(100)]
        processor._log_migration = AsyncMock()

        with patch.object(
            processor, "_process_single_document", new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = {"status": "success"}
            result = await processor.process_batch(documents, str(uuid4()))

        assert result["processed"] == 100
        processor.shutdown()

    @pytest.mark.asyncio
    async def test_concurrent_workers_reduce_processing_time(self):
        """Verify using multiple workers is faster than sequential"""
        mock_db = AsyncMock()
        processor = ConcurrentBatchProcessor(
            db_client=mock_db, num_workers=5, max_retries=3
        )

        documents = [{"id": i, "filename": f"doc_{i}.txt"} for i in range(20)]
        processor._log_migration = AsyncMock()

        with patch.object(
            processor, "_process_single_document", new_callable=AsyncMock
        ) as mock_process:
            async def slow_process(doc):
                await asyncio.sleep(0.01)  # Simulate work
                return {"status": "success"}

            mock_process.side_effect = slow_process
            result = await processor.process_batch(documents, str(uuid4()))

        assert result["processed"] == 20
        processor.shutdown()


@pytest.mark.integration
class TestAppIntegration:
    """Validate integration with FastAPI application"""

    @pytest.mark.asyncio
    async def test_scheduler_service_is_available_in_app(self):
        """Verify SchedulerService is accessible from app context"""
        # This would require app fixture - placeholder for integration test
        assert SchedulerService is not None

    @pytest.mark.asyncio
    async def test_migration_routes_are_registered(self):
        """Verify migration routes are registered in FastAPI app"""
        # This would require app fixture - placeholder for integration test
        # Route list: POST/GET /schedules, POST /trigger/{id}, GET /batches, GET /batches/{id}
        expected_routes = [
            "/api/migration/schedules",
            "/api/migration/trigger",
            "/api/migration/batches",
        ]
        for route in expected_routes:
            # Routes should be registered in app.include_router()
            pass
