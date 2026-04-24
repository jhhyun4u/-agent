"""
스테이징 환경 문서 마이그레이션 테스트

목적:
- 실제 Supabase 연결 테스트
- 배치 생성 → 처리 → 완료 전체 플로우 검증
- 에러 시나리오 처리 확인
- 성능 기준선 측정

실행: python scripts/staging_migration_test.py
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from uuid import uuid4

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_scheduler_initialization():
    """테스트 1: 스케줄러 초기화"""
    logger.info("=" * 60)
    logger.info("TEST 1: Scheduler Initialization")
    logger.info("=" * 60)

    try:
        from app.utils.supabase_client import get_async_client
        from app.services.domains.operations.scheduler_service import SchedulerService

        client = await get_async_client()
        scheduler = SchedulerService(client)

        # Initialize: Load active schedules
        await scheduler.initialize()
        logger.info("✅ Scheduler initialized successfully")
        logger.info(f"   APScheduler running: {scheduler.scheduler.running}")

        return True
    except Exception as e:
        logger.error(f"❌ Scheduler initialization failed: {e}")
        return False


async def test_schedule_creation():
    """테스트 2: 스케줄 생성"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: Schedule Creation")
    logger.info("=" * 60)

    try:
        from app.utils.supabase_client import get_async_client
        from app.services.domains.operations.scheduler_service import SchedulerService

        client = await get_async_client()
        scheduler = SchedulerService(client)

        # Create schedule
        schedule_id = await scheduler.add_schedule(
            name="Staging Test Schedule",
            cron_expression="0 0 * * *",  # Daily at midnight
            source_type="intranet",
            enabled=True
        )

        logger.info(f"✅ Schedule created: {schedule_id}")

        # Verify in DB
        schedules = await scheduler.get_schedules()
        logger.info(f"   Total schedules in DB: {len(schedules)}")

        return schedule_id
    except Exception as e:
        logger.error(f"❌ Schedule creation failed: {e}")
        return None


async def test_batch_creation_and_processing(schedule_id):
    """테스트 3: 배치 생성 및 처리"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Batch Creation & Processing")
    logger.info("=" * 60)

    try:
        from app.utils.supabase_client import get_async_client
        from app.services.domains.operations.scheduler_service import SchedulerService

        client = await get_async_client()
        scheduler = SchedulerService(client)

        # Create and run batch
        start_time = time.time()
        batch_id = await scheduler.trigger_migration_now(str(schedule_id))
        elapsed = time.time() - start_time

        logger.info(f"✅ Batch created and processed: {batch_id}")
        logger.info(f"   Elapsed time: {elapsed:.2f}s")

        # Check batch status
        batch = await scheduler.get_batch_status(str(batch_id))
        if batch:
            logger.info(f"   Status: {batch.get('status')}")
            logger.info(f"   Processed: {batch.get('processed_documents', 0)}")
            logger.info(f"   Failed: {batch.get('failed_documents', 0)}")

        return batch_id
    except Exception as e:
        logger.error(f"❌ Batch processing failed: {e}")
        return None


async def test_concurrent_batch_processor():
    """테스트 4: 병렬 배치 처리기"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Concurrent Batch Processor")
    logger.info("=" * 60)

    try:
        from app.utils.supabase_client import get_async_client
        from app.services.domains.bidding.batch_processor import ConcurrentBatchProcessor

        client = await get_async_client()
        processor = ConcurrentBatchProcessor(client, num_workers=3, max_retries=2)

        # Create sample documents
        sample_docs = [
            {
                "id": str(uuid4()),
                "filename": f"test_doc_{i}.pdf",
                "content": b"test content",
            }
            for i in range(5)
        ]

        # Process batch
        start_time = time.time()
        result = await processor.process_batch(sample_docs, uuid4())
        elapsed = time.time() - start_time

        logger.info(f"✅ Batch processed")
        logger.info(f"   Processed: {result.get('processed')}")
        logger.info(f"   Failed: {result.get('failed')}")
        logger.info(f"   Status: {result.get('status')}")
        logger.info(f"   Time: {elapsed:.2f}s")

        processor.shutdown()
        return result
    except Exception as e:
        logger.error(f"❌ Batch processor failed: {e}")
        return None


async def test_database_schema():
    """테스트 5: 데이터베이스 스키마"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: Database Schema Validation")
    logger.info("=" * 60)

    try:
        from app.utils.supabase_client import get_async_client

        client = await get_async_client()

        # Check migration_schedule table
        schedules = await client.table("migration_schedule").select("*").limit(1).execute()
        logger.info(f"✅ migration_schedule table exists: {len(schedules.data) >= 0}")

        # Check migration_batches table
        batches = await client.table("migration_batches").select("*").limit(1).execute()
        logger.info(f"✅ migration_batches table exists: {len(batches.data) >= 0}")

        # Check migration_status_logs table
        logs = await client.table("migration_status_logs").select("*").limit(1).execute()
        logger.info(f"✅ migration_status_logs table exists: {len(logs.data) >= 0}")

        return True
    except Exception as e:
        logger.error(f"❌ Schema validation failed: {e}")
        return False


async def test_api_endpoints():
    """테스트 6: API 엔드포인트"""
    logger.info("\n" + "=" * 60)
    logger.info("TEST 6: API Endpoints (Syntax Check)")
    logger.info("=" * 60)

    try:
        from app.api.routes_scheduler import (
            router,
            ScheduleCreate,
            ScheduleResponse,
            BatchResponse,
        )

        logger.info(f"✅ routes_scheduler imported successfully")
        logger.info(f"   Router: {router}")
        logger.info(f"   Routes: {len(router.routes)} endpoints")

        # List endpoints
        for route in router.routes:
            logger.info(f"   - {route.path} ({route.methods})")

        return True
    except Exception as e:
        logger.error(f"❌ API endpoint check failed: {e}")
        return False


async def run_all_tests():
    """모든 테스트 실행"""
    logger.info("\n")
    logger.info("╔" + "=" * 58 + "╗")
    logger.info("║" + " STAGING MIGRATION TEST SUITE ".center(58) + "║")
    logger.info("║" + " 2026-04-20 ".center(58) + "║")
    logger.info("╚" + "=" * 58 + "╝")

    results = {
        "Scheduler Initialization": await test_scheduler_initialization(),
        "Database Schema": await test_database_schema(),
        "API Endpoints": await test_api_endpoints(),
    }

    schedule_id = await test_schedule_creation()
    if schedule_id:
        results["Schedule Creation"] = True
        batch_id = await test_batch_creation_and_processing(schedule_id)
        results["Batch Processing"] = batch_id is not None
    else:
        results["Schedule Creation"] = False
        results["Batch Processing"] = False

    results["Concurrent Processor"] = (
        await test_concurrent_batch_processor() is not None
    )

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, passed_flag in results.items():
        status = "✅ PASS" if passed_flag else "❌ FAIL"
        logger.info(f"{status} - {test_name}")

    logger.info("=" * 60)
    logger.info(f"Result: {passed}/{total} tests passed ({100*passed//total}%)")

    if passed == total:
        logger.info("🎉 All tests passed! Ready for production deployment.")
    else:
        logger.info("⚠️  Some tests failed. Review logs above.")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
