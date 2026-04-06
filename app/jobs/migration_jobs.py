"""
마이그레이션 작업 (레거시 — scheduled_monitor.py로 통합됨)

run_scheduled_migration() 함수는 app/services/scheduled_monitor.py로 이전.
이 파일은 기존 테스트 호환성을 위해 보존되며, 실제 스케줄러 잡은
scheduled_monitor.setup_scheduler() 안의 'monthly_migration' 잡을 사용.
"""

import logging
from app.services.migration_service import MigrationService
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


async def run_scheduled_migration():
    """정기 마이그레이션 작업 (레거시 래퍼 — 실제 잡은 scheduled_monitor.py에서 실행).

    이 함수는 하위 호환성 유지용입니다.
    실제 스케줄러는 app/services/scheduled_monitor.setup_scheduler()에서 등록됩니다.
    """
    try:
        logger.info("정기 마이그레이션 잡 시작...")

        db = await get_async_client()
        migration_service = MigrationService(db=db, notification_service=None)

        batch = await migration_service.batch_import_intranet_documents(
            batch_type="monthly",
            include_failed=True
        )

        logger.info(
            f"정기 마이그레이션 완료: batch_id={batch.id if batch else 'N/A'}, "
            f"processed={batch.processed_documents if batch else 0}, "
            f"failed={batch.failed_documents if batch else 0}"
        )

    except Exception as e:
        logger.error(f"정기 마이그레이션 실패: {e}", exc_info=True)
