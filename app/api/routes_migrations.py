"""
마이그레이션 API (Phase 4)

배치 조회, 스케줄 관리, 즉시 시작
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, require_role
from app.exceptions import (
    TenopAPIError,
    ResourceNotFoundError,
    InternalServiceError,
)
from app.models.auth_schemas import CurrentUser
from app.models.migration_schemas import (
    MigrationBatch,
    MigrationSchedule,
    MigrationTriggerRequest,
    MigrationScheduleUpdate,
    BatchListParams,
    BatchListResponse,
    MigrationTriggerResponse,
)
from app.services.migration_service import MigrationService
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/migrations", tags=["migrations"])


def _get_migration_service(db) -> MigrationService:
    """마이그레이션 서비스 팩토리 (notification_service는 M-5로 추후 주입)."""
    return MigrationService(db=db, notification_service=None)


@router.post("/trigger", response_model=MigrationTriggerResponse, status_code=status.HTTP_202_ACCEPTED)
async def trigger_migration(
    req: MigrationTriggerRequest,
    user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_role("admin", "executive")),
    db=Depends(get_async_client),
):
    """배치 마이그레이션 즉시 시작 (202 Accepted - 백그라운드 작업)

    권한: admin, executive 만 허용
    """
    try:
        migration_service = _get_migration_service(db)
        batch = await migration_service.create_batch_record(
            batch_type=req.batch_type,
            total_docs=0,
            created_by_id=UUID(user.id) if user.id else None
        )

        logger.info(f"마이그레이션 트리거: batch_id={batch.id}, type={req.batch_type}, user={user.id}")

        return MigrationTriggerResponse(
            batch_id=batch.id,
            batch_name=batch.batch_name,
            status="accepted",
            scheduled_at=batch.scheduled_at,
            estimated_duration_minutes=45,
            message="Migration batch started in background"
        )

    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"마이그레이션 시작 실패: {e}")
        raise InternalServiceError(f"마이그레이션 시작 실패: {str(e)}")


@router.get("/batches", response_model=BatchListResponse)
async def list_batches(
    params: BatchListParams = Depends(),
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
):
    """배치 목록 조회 (필터링, 정렬, 페이징)

    권한: admin, executive, director (읽기 허용)
    """
    try:
        migration_service = _get_migration_service(db)
        batches = await migration_service.get_batch_history(
            limit=params.limit,
            offset=params.offset,
            status=params.status,
            sort_by=params.sort_by,
            order=params.order,
        )

        total = len(batches) if batches else 0
        return BatchListResponse(
            total=total,
            limit=params.limit,
            offset=params.offset,
            batches=batches or []
        )

    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"배치 목록 조회 실패: {e}")
        raise InternalServiceError(f"배치 목록 조회 실패: {str(e)}")


@router.get("/batches/{batch_id}", response_model=MigrationBatch)
async def get_batch(
    batch_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
):
    """배치 상세 조회"""
    try:
        migration_service = _get_migration_service(db)
        batch = await migration_service.get_batch(batch_id)

        if not batch:
            raise ResourceNotFoundError("배치", str(batch_id))

        return batch

    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"배치 {batch_id} 조회 실패: {e}")
        raise InternalServiceError(f"배치 조회 실패: {str(e)}")


@router.get("/schedule", response_model=Optional[MigrationSchedule])
async def get_schedule(
    user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_role("admin", "executive")),
    db=Depends(get_async_client),
):
    """마이그레이션 스케줄 조회

    권한: admin, executive 만 조회 가능
    """
    try:
        migration_service = _get_migration_service(db)
        schedule = await migration_service.get_schedule()
        return schedule

    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"스케줄 조회 실패: {e}")
        raise InternalServiceError(f"스케줄 조회 실패: {str(e)}")


@router.put("/schedule/{schedule_id}", response_model=MigrationSchedule)
async def update_schedule(
    schedule_id: UUID,
    update: MigrationScheduleUpdate,
    user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_role("admin", "executive")),
    db=Depends(get_async_client),
):
    """마이그레이션 스케줄 업데이트

    권한: admin, executive 만 수정 가능
    """
    try:
        migration_service = _get_migration_service(db)
        updates = update.model_dump(exclude_none=True)
        schedule = await migration_service.update_schedule(schedule_id, **updates)

        if not schedule:
            raise ResourceNotFoundError("스케줄", str(schedule_id))

        logger.info(f"스케줄 업데이트: schedule_id={schedule_id}, fields={list(updates.keys())}, user={user.id}")
        return schedule

    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"스케줄 {schedule_id} 업데이트 실패: {e}")
        raise InternalServiceError(f"스케줄 업데이트 실패: {str(e)}")
