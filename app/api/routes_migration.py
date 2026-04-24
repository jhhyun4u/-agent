"""
마이그레이션 스케줄 관리 API

엔드포인트:
- POST /api/migration/schedules - 스케줄 생성
- GET /api/migration/schedules - 스케줄 목록
- POST /api/migration/trigger/{schedule_id} - 즉시 실행
- GET /api/migration/batches - 배치 이력
- GET /api/migration/batches/{batch_id} - 배치 상세
- GET /api/migration/batches/{batch_id}/logs - 배치 로그
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.api.deps import get_current_user
from app.models.auth_schemas import CurrentUser
from app.services.domains.operations.scheduler_service import SchedulerService, get_scheduler_service
from app.utils.supabase_client import get_async_client

router = APIRouter(prefix="/api/migration", tags=["migration"])


# Pydantic Models
class CreateScheduleRequest:
    """스케줄 생성 요청"""

    def __init__(
        self, name: str, cron_expression: str, source_type: str, enabled: bool = True
    ):
        self.name = name
        self.cron_expression = cron_expression
        self.source_type = source_type
        self.enabled = enabled


class ScheduleResponse:
    """스케줄 응답"""

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


@router.post("/schedules")
async def create_schedule(
    name: str,
    cron_expression: str,
    source_type: str,
    enabled: bool = True,
    current_user: CurrentUser = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler_service),
) -> dict:
    """
    새 마이그레이션 스케줄 생성

    Args:
        name: 스케줄 이름
        cron_expression: Cron 표현식 (예: "0 0 1 * *")
        source_type: 소스 타입 (예: "intranet")
        enabled: 활성화 여부

    Returns:
        생성된 스케줄 정보
    """
    try:
        schedule_id = await scheduler.add_schedule(
            name=name,
            cron_expression=cron_expression,
            source_type=source_type,
            enabled=enabled,
        )

        return {
            "id": str(schedule_id),
            "name": name,
            "cron_expression": cron_expression,
            "source_type": source_type,
            "enabled": enabled,
            "message": "Schedule created successfully",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)
        )


@router.get("/schedules")
async def list_schedules(
    current_user: CurrentUser = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler_service),
) -> dict:
    """
    모든 마이그레이션 스케줄 조회

    Returns:
        스케줄 리스트
    """
    try:
        schedules = await scheduler.get_schedules()
        return {"total": len(schedules), "data": schedules}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/trigger/{schedule_id}")
async def trigger_migration(
    schedule_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler_service),
) -> dict:
    """
    즉시 마이그레이션 트리거

    Args:
        schedule_id: 스케줄 UUID

    Returns:
        생성된 배치 정보
    """
    try:
        schedule_uuid = UUID(schedule_id)
        batch_id = await scheduler.trigger_migration_now(schedule_uuid)

        return {
            "batch_id": str(batch_id),
            "status": "started",
            "message": "Migration started",
        }
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid schedule_id"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/batches")
async def list_batches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: CurrentUser = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler_service),
) -> dict:
    """
    배치 이력 조회 (페이지네이션)

    Args:
        limit: 조회 수
        offset: 오프셋

    Returns:
        배치 리스트
    """
    try:
        result = await scheduler.get_batches(limit=limit, offset=offset)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/batches/{batch_id}")
async def get_batch_detail(
    batch_id: str,
    current_user: CurrentUser = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler_service),
) -> dict:
    """
    배치 상세 정보 조회

    Args:
        batch_id: 배치 UUID

    Returns:
        배치 상세 정보
    """
    try:
        batch_uuid = UUID(batch_id)
        batch = await scheduler.get_batch_detail(batch_uuid)
        return batch
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid batch_id"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.get("/batches/{batch_id}/logs")
async def get_batch_logs(
    batch_id: str,
    status: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=1000),
    current_user: CurrentUser = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler_service),
) -> dict:
    """
    배치의 개별 문서 처리 로그 조회

    Args:
        batch_id: 배치 UUID
        status: 필터링할 상태 (success, failed, skipped)
        limit: 조회 수

    Returns:
        마이그레이션 로그 리스트
    """
    try:
        batch_uuid = UUID(batch_id)
        logs = await scheduler.get_batch_logs(
            batch_uuid, status=status, limit=limit
        )
        return {"batch_id": str(batch_uuid), "total": len(logs), "data": logs}
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid batch_id"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )
