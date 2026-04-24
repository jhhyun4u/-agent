from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel
from app.api.deps import get_current_user
from app.utils.supabase_client import get_async_client
from app.services.domains.operations.scheduler_service import SchedulerService

router = APIRouter(prefix="/api/scheduler", tags=["scheduler"])


@router.get("/health")
async def scheduler_health():
    """Scheduler service health check endpoint"""
    return {"status": "ok", "service": "scheduler"}


class ScheduleCreate(BaseModel):
    name: str
    cron_expression: str
    source_type: str = "intranet"
    enabled: bool = True

class ScheduleResponse(BaseModel):
    id: str
    schedule_name: str
    cron_expression: str
    enabled: bool
    next_run_at: Optional[str]
    last_run_at: Optional[str]

class BatchResponse(BaseModel):
    id: str
    batch_name: str
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    processed_documents: int
    failed_documents: int

@router.get("/schedules", response_model=List[ScheduleResponse])
async def list_schedules(current_user = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    client = await get_async_client()
    result = await client.table("migration_schedule").select("*").execute()
    return result.data or []

@router.post("/schedules", response_model=ScheduleResponse)
async def create_schedule(schedule: ScheduleCreate, current_user = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    client = await get_async_client()
    service = SchedulerService(client)

    schedule_id = await service.add_schedule(
        name=schedule.name,
        cron_expression=schedule.cron_expression,
        source_type=schedule.source_type,
        enabled=schedule.enabled
    )

    return ScheduleResponse(
        id=schedule_id,
        schedule_name=schedule.name,
        cron_expression=schedule.cron_expression,
        enabled=schedule.enabled,
        next_run_at=None,
        last_run_at=None
    )

@router.post("/schedules/{schedule_id}/trigger")
async def trigger_migration(schedule_id: str, current_user = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    client = await get_async_client()
    service = SchedulerService(client)
    
    batch_id = await service.trigger_migration_now(schedule_id)
    return {"batch_id": batch_id, "message": "Migration triggered"}

@router.get("/batches/{batch_id}", response_model=BatchResponse)
async def get_batch_status(batch_id: str, current_user = Depends(get_current_user)):
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    client = await get_async_client()
    service = SchedulerService(client)

    batch = await service.get_batch_status(batch_id)
    if not batch:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    return BatchResponse(
        id=batch.get("id"),
        batch_name=batch.get("batch_name"),
        status=batch.get("status"),
        started_at=batch.get("started_at"),
        completed_at=batch.get("completed_at"),
        processed_documents=batch.get("processed_documents", 0),
        failed_documents=batch.get("failed_documents", 0)
    )
