"""
STEP 8: Job Queue API 라우트 (Day 5 REST endpoints)

Job 생성 → 상태 추적 → 완료 알림 (7개 REST 엔드포인트)
- POST   /api/jobs                    (Job 생성)
- GET    /api/jobs/{job_id}           (상태 조회)
- GET    /api/jobs                    (목록 조회 + 필터링)
- PUT    /api/jobs/{job_id}/cancel    (취소)
- PUT    /api/jobs/{job_id}/retry     (재시도)
- DELETE /api/jobs/{job_id}           (삭제)
- GET    /api/jobs/stats              (통계, admin only)
"""

import logging
from typing import Optional, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from app.api.deps import get_current_user, require_role
from app.exceptions import TenopAPIError
from app.middleware.rate_limit import limiter
from app.models.auth_schemas import CurrentUser
from app.models.job_queue_schemas import (
    JobCreateRequest,
    JobStatus,
    JobStatusResponse,
    JobListResponse,
    JobCancelResponse,
    JobRetryResponse,
    JobType,
)
from app.services.job_queue_service import (
    JobQueueService,
    JobNotFoundError,
    InvalidJobStateError,
    JobCancelError,
    JobRetryError,
)
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/jobs", tags=["jobs"])


# ============================================
# Helper: Get Service Instance
# ============================================


async def _get_job_service() -> JobQueueService:
    """JobQueueService 인스턴스 반환"""
    client = await get_async_client()
    return JobQueueService(db_client=client)


# ============================================
# POST /api/jobs — Job 생성
# ============================================


@router.post("", response_model=JobStatusResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_job(
    request: Request,
    body: JobCreateRequest,
    user: CurrentUser = Depends(get_current_user),
) -> JobStatusResponse:
    """
    새로운 비동기 작업 생성.

    Args:
        proposal_id: 제안서 프로젝트 ID
        type: 작업 유형 (step4a_diagnosis, step4a_regenerate, step4b_pricing, 등)
        payload: 작업 입력 파라미터 dict
        priority: 우선도 (0=HIGH, 1=NORMAL, 2=LOW)
        max_retries: 최대 재시도 횟수 (1-10)

    Returns:
        JobStatusResponse: {id, status, progress, retries, duration_seconds, created_at, started_at}

    Raises:
        400: 유효하지 않은 요청 파라미터
        404: 제안서 프로젝트를 찾을 수 없음
        409: 상태 불일치
    """
    try:
        service = await _get_job_service()

        # Job 생성 (권한 검증은 service 계층에서 수행)
        job = await service.create_job(
            proposal_id=body.proposal_id,
            job_type=body.type,
            payload=body.payload,
            priority=body.priority,
            max_retries=body.max_retries,
            created_by=user.id,
            tags=body.tags,
        )

        logger.info(f"[JOB] Created: {job.id} (type={body.type}, user={user.id})")

        return JobStatusResponse(
            id=job.id,
            status=job.status,
            progress=0.0,
            retries=job.retries,
            max_retries=job.max_retries,
            duration_seconds=None,
            created_at=job.created_at,
            started_at=job.started_at,
            estimated_completion=None,
            queue_position=None,
        )

    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"[JOB] Create failed: {e}")
        raise TenopAPIError(
            error_code="JOB_CREATE_FAILED",
            message=str(e),
            status_code=500,
        )


# ============================================
# GET /api/jobs/stats — 큐 통계 (Admin Only)
# ============================================


@router.get("/stats", response_model=dict)
@limiter.limit("10/minute")
async def get_job_stats(
    request: Request,
    user: CurrentUser = Depends(get_current_user),
) -> dict:
    """
    Job 큐 통계 (Admin만 접근 가능).

    Returns:
        {
            pending: int,
            running: int,
            success: int,
            failed: int,
            cancelled: int,
            total: int,
            avg_duration_seconds: float,
            success_rate: float,  # 0.0~1.0
        }

    Raises:
        403: 접근 권한 없음 (admin only)
    """
    try:
        if user.role != "admin":
            raise TenopAPIError(
                error_code="ACCESS_DENIED",
                message="Admin access required to view job statistics",
                status_code=403,
            )

        service = await _get_job_service()
        stats = await service.get_queue_stats()

        return {
            "pending": stats.get("pending", 0),
            "running": stats.get("running", 0),
            "success": stats.get("success", 0),
            "failed": stats.get("failed", 0),
            "cancelled": stats.get("cancelled", 0),
            "total": stats.get("total", 0),
            "avg_duration_seconds": stats.get("avg_duration_seconds", 0.0),
            "success_rate": stats.get("success_rate", 0.0),
        }

    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"[JOB] Stats failed: {e}")
        raise TenopAPIError(
            error_code="JOB_STATS_FAILED",
            message=str(e),
            status_code=500,
        )


# ============================================
# GET /api/jobs/{job_id} — Job 상태 조회
# ============================================


@router.get("/{job_id}", response_model=JobStatusResponse)
@limiter.limit("60/minute")
async def get_job_status(
    request: Request,
    job_id: UUID,
    user: CurrentUser = Depends(get_current_user),
) -> JobStatusResponse:
    """
    Job의 현재 상태 조회.

    권한: 생성자 또는 admin만 조회 가능

    Returns:
        JobStatusResponse: 상태, 진행률, 재시도 횟수, 타이밍

    Raises:
        404: Job을 찾을 수 없음
        403: 접근 권한 없음
    """
    try:
        service = await _get_job_service()
        job = await service.get_job(job_id=job_id)

        # 권한 확인: 생성자 또는 admin
        if str(job.created_by) != user.id and user.role != "admin":
            raise TenopAPIError(
                error_code="ACCESS_DENIED",
                message="You do not have permission to view this job",
                status_code=403,
            )

        # 진행률 계산
        progress = await service.get_job_progress(job_id=job_id)

        # 예상 완료 시간 계산
        estimated_completion = None
        if job.status == JobStatus.RUNNING:
            estimated_completion = await service.estimate_completion(job_id=job_id)

        # 큐 위치 조회
        queue_position = None
        if job.status == JobStatus.PENDING:
            queue_position = await service.get_queue_position(job_id=job_id)

        return JobStatusResponse(
            id=job.id,
            status=job.status,
            progress=progress,
            retries=job.retries,
            max_retries=job.max_retries,
            duration_seconds=job.duration_seconds,
            created_at=job.created_at,
            started_at=job.started_at,
            estimated_completion=estimated_completion,
            queue_position=queue_position,
        )

    except JobNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")
    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"[JOB] Get status failed for {job_id}: {e}")
        raise TenopAPIError(
            error_code="JOB_GET_FAILED",
            message=str(e),
            status_code=500,
        )


# ============================================
# GET /api/jobs — Job 목록 (필터링 + 페이지네이션)
# ============================================


@router.get("", response_model=JobListResponse)
@limiter.limit("60/minute")
async def list_jobs(
    request: Request,
    status_filter: Optional[str] = Query(None, alias="status"),
    job_type: Optional[str] = Query(None, alias="type"),
    proposal_id: Optional[UUID] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    user: CurrentUser = Depends(get_current_user),
) -> JobListResponse:
    """
    Job 목록 조회 (필터링 + 페이지네이션).

    Query Parameters:
        status: 상태 필터 (pending, running, success, failed, cancelled)
        type: 작업 유형 필터
        proposal_id: 제안서 프로젝트 ID
        limit: 페이지 크기 (1-100, 기본값 20)
        offset: 오프셋 (기본값 0)

    권한: 생성자 또는 admin만 조회 가능

    Returns:
        JobListResponse: {total, page, limit, items: [JobStatusResponse]}
    """
    try:
        service = await _get_job_service()

        # admin이 아니면 자신의 job만 조회
        created_by = None if user.role == "admin" else user.id

        # 목록 조회
        total, items = await service.list_jobs(
            created_by=created_by,
            proposal_id=proposal_id,
            status=status_filter,
            job_type=job_type,
            limit=limit,
            offset=offset,
        )

        # 진행률 계산
        response_items = []
        for job in items:
            progress = await service.get_job_progress(job_id=job.id)
            response_items.append(
                JobStatusResponse(
                    id=job.id,
                    status=job.status,
                    progress=progress,
                    retries=job.retries,
                    max_retries=job.max_retries,
                    duration_seconds=job.duration_seconds,
                    created_at=job.created_at,
                    started_at=job.started_at,
                    estimated_completion=None,
                    queue_position=None,
                )
            )

        page = (offset // limit) + 1 if limit > 0 else 1

        return JobListResponse(
            total=total,
            page=page,
            limit=limit,
            items=response_items,
        )

    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"[JOB] List failed: {e}")
        raise TenopAPIError(
            error_code="JOB_LIST_FAILED",
            message=str(e),
            status_code=500,
        )


# ============================================
# PUT /api/jobs/{job_id}/cancel — Job 취소
# ============================================


@router.put("/{job_id}/cancel", response_model=JobCancelResponse)
@limiter.limit("30/minute")
async def cancel_job(
    request: Request,
    job_id: UUID,
    user: CurrentUser = Depends(get_current_user),
) -> JobCancelResponse:
    """
    Job 취소 (PENDING 또는 RUNNING 상태만 가능).

    권한: 생성자 또는 admin만 취소 가능

    Returns:
        JobCancelResponse: {cancelled, job_id, message}

    Raises:
        404: Job을 찾을 수 없음
        409: 상태 불일치 (이미 완료됨)
        403: 접근 권한 없음
    """
    try:
        service = await _get_job_service()
        job = await service.get_job(job_id=job_id)

        # 권한 확인
        if str(job.created_by) != user.id and user.role != "admin":
            raise TenopAPIError(
                error_code="ACCESS_DENIED",
                message="You do not have permission to cancel this job",
                status_code=403,
            )

        # 상태 확인: PENDING 또는 RUNNING만 취소 가능
        if job.status not in [JobStatus.PENDING, JobStatus.RUNNING]:
            raise JobCancelError(
                message=f"Cannot cancel job in state '{job.status}'. Only PENDING or RUNNING jobs can be cancelled."
            )

        # 취소 실행
        cancelled = await service.cancel_job(job_id=job_id)

        logger.info(f"[JOB] Cancelled: {job_id} (user={user.id})")

        return JobCancelResponse(
            cancelled=cancelled,
            job_id=job_id,
            message="Job cancelled successfully" if cancelled else "Failed to cancel job",
        )

    except JobNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")
    except JobCancelError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"[JOB] Cancel failed for {job_id}: {e}")
        raise TenopAPIError(
            error_code="JOB_CANCEL_FAILED",
            message=str(e),
            status_code=500,
        )


# ============================================
# PUT /api/jobs/{job_id}/retry — Job 재시도
# ============================================


@router.put("/{job_id}/retry", response_model=JobRetryResponse)
@limiter.limit("20/minute")
async def retry_job(
    request: Request,
    job_id: UUID,
    user: CurrentUser = Depends(get_current_user),
) -> JobRetryResponse:
    """
    Job 재시도 (FAILED 상태만 가능, max_retries 이하).

    권한: 생성자 또는 admin만 재시도 가능

    Returns:
        JobRetryResponse: {job_id, status, retry_attempt}

    Raises:
        404: Job을 찾을 수 없음
        409: 상태 불일치 또는 재시도 한계 초과
        403: 접근 권한 없음
    """
    try:
        service = await _get_job_service()
        job = await service.get_job(job_id=job_id)

        # 권한 확인
        if str(job.created_by) != user.id and user.role != "admin":
            raise TenopAPIError(
                error_code="ACCESS_DENIED",
                message="You do not have permission to retry this job",
                status_code=403,
            )

        # 상태 확인: FAILED만 재시도 가능
        if job.status != JobStatus.FAILED:
            raise JobRetryError(
                message=f"Cannot retry job in state '{job.status}'. Only FAILED jobs can be retried."
            )

        # 재시도 한계 확인
        if job.retries >= job.max_retries:
            raise JobRetryError(
                message=f"Maximum retries ({job.max_retries}) exceeded for job {job_id}"
            )

        # 재시도 실행
        retry_attempt = await service.retry_job(job_id=job_id)

        logger.info(f"[JOB] Retried: {job_id} (attempt={retry_attempt}, user={user.id})")

        return JobRetryResponse(
            job_id=job_id,
            status=JobStatus.PENDING,
            retry_attempt=retry_attempt,
        )

    except JobNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")
    except JobRetryError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"[JOB] Retry failed for {job_id}: {e}")
        raise TenopAPIError(
            error_code="JOB_RETRY_FAILED",
            message=str(e),
            status_code=500,
        )


# ============================================
# DELETE /api/jobs/{job_id} — Job 삭제
# ============================================


@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_job(
    request: Request,
    job_id: UUID,
    user: CurrentUser = Depends(get_current_user),
) -> None:
    """
    Job 삭제 (SUCCESS, FAILED, CANCELLED 상태만 가능).

    권한: 생성자 또는 admin만 삭제 가능

    Raises:
        404: Job을 찾을 수 없음
        409: 상태 불일치 (진행 중인 job)
        403: 접근 권한 없음
    """
    try:
        service = await _get_job_service()
        job = await service.get_job(job_id=job_id)

        # 권한 확인
        if str(job.created_by) != user.id and user.role != "admin":
            raise TenopAPIError(
                error_code="ACCESS_DENIED",
                message="You do not have permission to delete this job",
                status_code=403,
            )

        # 상태 확인: 완료된 job만 삭제 가능
        if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
            raise InvalidJobStateError(
                message=f"Cannot delete job in state '{job.status}'. Only completed jobs can be deleted."
            )

        # 삭제 실행
        await service.delete_job(job_id=job_id)

        logger.info(f"[JOB] Deleted: {job_id} (user={user.id})")

    except JobNotFoundError:
        raise HTTPException(status_code=404, detail="Job not found")
    except InvalidJobStateError as e:
        raise HTTPException(status_code=409, detail=e.message)
    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"[JOB] Delete failed for {job_id}: {e}")
        raise TenopAPIError(
            error_code="JOB_DELETE_FAILED",
            message=str(e),
            status_code=500,
        )


