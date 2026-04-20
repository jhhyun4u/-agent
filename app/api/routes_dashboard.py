"""
대시보드 KPI API 라우트 (설계: 섹션 5)

3개 엔드포인트:
- GET /api/dashboard/metrics/{dashboard_type} — 실시간 KPI (캐시 5분)
- GET /api/dashboard/timeline/{dashboard_type} — 월별 이력 (캐시 10분)
- GET /api/dashboard/details/{dashboard_type} — 상세 드릴다운 (캐시 없음)

권한 검증: role 기반 RBAC (deps.py)
캐싱: Redis 기반 (cache_manager.py)
"""

import logging
from datetime import datetime
from typing import Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.deps import get_current_user, require_role
from app.models.auth_schemas import CurrentUser
from app.models.dashboard_schemas import (
    DashboardIndividualMetrics,
    DashboardTeamMetrics,
    DashboardDepartmentMetrics,
    DashboardExecutiveMetrics,
    DashboardTimelineResponse,
    DashboardDetailsResponse,
    MetricsResponse,
    ErrorResponse,
)
from app.services.dashboard_metrics_service import DashboardMetricsService
from app.services.cache_manager import get_cache_manager
from app.exceptions import TenopAPIError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


# ════════════════════════════════════════════════════════════════════
# 헬퍼 함수
# ════════════════════════════════════════════════════════════════════

def _validate_dashboard_access(
    dashboard_type: str,
    current_user: CurrentUser,
) -> tuple[str, Optional[str], Optional[str]]:
    """
    대시보드 접근 권한 검증

    Args:
        dashboard_type: 대시보드 유형 (individual/team/department/executive)
        current_user: 현재 사용자

    Returns:
        (대시보드_유형, 제약_ID, 제약_타입)
        - 개인: (individual, user_id, "user")
        - 팀: (team, team_id, "team")
        - 본부: (department, division_id, "division")
        - 경영진: (executive, org_id, "org")

    Raises:
        HTTPException: 접근 권한 없음
    """
    if dashboard_type == "individual":
        return dashboard_type, current_user.id, "user"

    elif dashboard_type == "team":
        if current_user.role not in ["lead", "director", "executive", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="팀 대시보드 접근 권한이 없습니다. (필요: 팀장/본부장/경영진)"
            )
        if not current_user.team_id:
            raise HTTPException(
                status_code=400,
                detail="팀에 속해있지 않습니다."
            )
        return dashboard_type, current_user.team_id, "team"

    elif dashboard_type == "department":
        if current_user.role not in ["director", "executive", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="본부 대시보드 접근 권한이 없습니다. (필요: 본부장/경영진)"
            )
        if not current_user.division_id:
            raise HTTPException(
                status_code=400,
                detail="본부에 속해있지 않습니다."
            )
        return dashboard_type, current_user.division_id, "division"

    elif dashboard_type == "executive":
        if current_user.role not in ["executive", "admin"]:
            raise HTTPException(
                status_code=403,
                detail="경영진 대시보드 접근 권한이 없습니다."
            )
        return dashboard_type, current_user.org_id, "org"

    else:
        raise HTTPException(
            status_code=400,
            detail=f"잘못된 대시보드 유형: {dashboard_type}"
        )


async def _get_metrics_with_cache(
    cache_key: str,
    dashboard_type: str,
    service: DashboardMetricsService,
    constraint_id: Optional[str],
) -> tuple[dict, bool]:
    """
    캐시를 활용하여 메트릭 조회

    Args:
        cache_key: 캐시 키
        dashboard_type: 대시보드 유형
        service: DashboardMetricsService 인스턴스
        constraint_id: 제약 ID (user_id, team_id, division_id, org_id)

    Returns:
        (메트릭_데이터, 캐시_히트_여부)
    """
    cache_mgr = get_cache_manager()

    # 1차: 캐시 조회
    cached_metrics = await cache_mgr.get(cache_key)
    if cached_metrics:
        logger.debug(f"💾 대시보드 캐시 HIT: {cache_key}")
        return cached_metrics, True

    # 2차: DB에서 메트릭 조회
    try:
        if dashboard_type == "individual":
            metrics = await service.get_individual_metrics(constraint_id)
        elif dashboard_type == "team":
            metrics = await service.get_team_metrics(constraint_id)
        elif dashboard_type == "department":
            metrics = await service.get_department_metrics(constraint_id)
        elif dashboard_type == "executive":
            metrics = await service.get_executive_metrics(constraint_id)
        else:
            raise TenopAPIError("GEN_001", f"미지원 대시보드 유형: {dashboard_type}")

        # 3차: 캐시 저장 (TTL: 5분)
        await cache_mgr.set(cache_key, metrics, ttl=300)
        logger.debug(f"📝 대시보드 캐시 저장: {cache_key}")

        return metrics, False

    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"메트릭 조회 오류: {e}")
        raise TenopAPIError("GEN_001", "메트릭 조회 실패", status_code=500)


# ════════════════════════════════════════════════════════════════════
# 엔드포인트 1: GET /api/dashboard/metrics/{dashboard_type}
# ════════════════════════════════════════════════════════════════════

@router.get(
    "/metrics/{dashboard_type}",
    response_model=MetricsResponse,
    summary="대시보드 KPI 조회",
    description="실시간 KPI 메트릭 조회 (캐시 5분)",
    responses={
        400: {"model": ErrorResponse, "description": "파라미터 오류"},
        401: {"model": ErrorResponse, "description": "미인증"},
        403: {"model": ErrorResponse, "description": "접근 권한 없음"},
        500: {"model": ErrorResponse, "description": "서버 에러"},
    }
)
async def get_metrics(
    dashboard_type: Literal["individual", "team", "department", "executive"],
    period: str = Query("ytd", description="기간 (ytd/mtd/custom)"),
    custom_start_date: Optional[str] = Query(None, description="커스텀 시작 날짜 (YYYY-MM-DD)"),
    custom_end_date: Optional[str] = Query(None, description="커스텀 종료 날짜 (YYYY-MM-DD)"),
    current_user: CurrentUser = Depends(get_current_user),
) -> MetricsResponse:
    """
    대시보드 KPI 조회

    **대시보드 유형별 권한:**
    - individual: 모든 사용자 (자신의 데이터만)
    - team: 팀장, 본부장, 경영진
    - department: 본부장, 경영진
    - executive: 경영진만

    **응답 필드:**
    - metrics: 대시보드 유형에 따라 다른 스키마
    - cache_hit: 캐시에서 조회했는지 여부
    - cache_ttl_seconds: 남은 캐시 TTL (초)

    **캐싱:** Redis 5분
    """
    try:
        # 권한 검증
        _, constraint_id, constraint_type = _validate_dashboard_access(
            dashboard_type, current_user
        )

        # 캐시 키 생성
        cache_key = f"dashboard:metrics:{dashboard_type}:{constraint_id}:{period}"

        # 메트릭 조회 (캐시 활용)
        service = DashboardMetricsService()
        metrics, cache_hit = await _get_metrics_with_cache(
            cache_key, dashboard_type, service, constraint_id
        )

        return MetricsResponse(
            dashboard_type=dashboard_type,
            period=period,
            generated_at=datetime.utcnow(),
            cache_hit=cache_hit,
            cache_ttl_seconds=300,
            metrics=metrics,
        )

    except HTTPException:
        raise
    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"대시보드 메트릭 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="메트릭 조회 실패")


# ════════════════════════════════════════════════════════════════════
# 엔드포인트 2: GET /api/dashboard/timeline/{dashboard_type}
# ════════════════════════════════════════════════════════════════════

@router.get(
    "/timeline/{dashboard_type}",
    response_model=DashboardTimelineResponse,
    summary="대시보드 월별 이력",
    description="월별 이력 조회 (캐시 10분)",
    responses={
        400: {"model": ErrorResponse, "description": "파라미터 오류"},
        401: {"model": ErrorResponse, "description": "미인증"},
        403: {"model": ErrorResponse, "description": "접근 권한 없음"},
        500: {"model": ErrorResponse, "description": "서버 에러"},
    }
)
async def get_timeline(
    dashboard_type: Literal["team", "department", "executive"],
    months: int = Query(12, ge=1, le=36, description="조회 개월 수 (1~36)"),
    metric: str = Query("win_rate", description="메트릭 (win_rate/total_amount/proposal_count)"),
    current_user: CurrentUser = Depends(get_current_user),
) -> DashboardTimelineResponse:
    """
    월별 이력 조회

    **응답 필드:**
    - data: 월별 데이터 포인트 배열
    - summary: 추이/평균/최고 월 등

    **캐싱:** Redis 10분
    """
    try:
        # 권한 검증 (team/department/executive만 가능)
        if dashboard_type == "individual":
            raise HTTPException(
                status_code=400,
                detail="타임라인은 team/department/executive만 지원합니다."
            )

        _, constraint_id, constraint_type = _validate_dashboard_access(
            dashboard_type, current_user
        )

        # 캐시 키 생성
        cache_key = f"dashboard:timeline:{dashboard_type}:{constraint_id}:{metric}:{months}"

        # 캐시 조회
        cache_mgr = get_cache_manager()
        cached_timeline = await cache_mgr.get(cache_key)
        if cached_timeline:
            logger.debug(f"💾 타임라인 캐시 HIT: {cache_key}")
            return DashboardTimelineResponse(**cached_timeline)

        # DB에서 타임라인 조회
        service = DashboardMetricsService()
        timeline_data = await service.fetch_timeline(
            dashboard_type, constraint_id, months, metric
        )

        # 캐시 저장 (TTL: 10분)
        await cache_mgr.set(cache_key, timeline_data, ttl=600)

        return DashboardTimelineResponse(**timeline_data)

    except HTTPException:
        raise
    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"타임라인 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="타임라인 조회 실패")


# ════════════════════════════════════════════════════════════════════
# 엔드포인트 3: GET /api/dashboard/details/{dashboard_type}
# ════════════════════════════════════════════════════════════════════

@router.get(
    "/details/{dashboard_type}",
    response_model=DashboardDetailsResponse,
    summary="대시보드 상세 드릴다운",
    description="상세 데이터 조회 (캐시 없음)",
    responses={
        400: {"model": ErrorResponse, "description": "파라미터 오류"},
        401: {"model": ErrorResponse, "description": "미인증"},
        403: {"model": ErrorResponse, "description": "접근 권한 없음"},
        500: {"model": ErrorResponse, "description": "서버 에러"},
    }
)
async def get_details(
    dashboard_type: Literal["team", "department", "executive"],
    filter_type: str = Query(..., description="필터 유형 (team/region/client/positioning)"),
    filter_value: Optional[str] = Query(None, description="필터 값 (팀ID/지역/기관명/positioning)"),
    sort_by: str = Query("win_rate", description="정렬 키 (win_rate/amount/date)"),
    sort_order: str = Query("desc", description="정렬 순서 (asc/desc)"),
    limit: int = Query(50, ge=1, le=500, description="조회 건수"),
    offset: int = Query(0, ge=0, description="오프셋"),
    current_user: CurrentUser = Depends(get_current_user),
) -> DashboardDetailsResponse:
    """
    상세 데이터 드릴다운

    **필터 유형:**
    - team: 팀별
    - region: 지역별
    - client: 기관별
    - positioning: 포지셔닝별

    **캐싱:** 없음 (실시간)
    """
    try:
        # 권한 검증
        _, constraint_id, constraint_type = _validate_dashboard_access(
            dashboard_type, current_user
        )

        # DB에서 상세 데이터 조회
        service = DashboardMetricsService()
        details_data = await service.fetch_details(
            dashboard_type=dashboard_type,
            constraint_id=constraint_id,
            filter_type=filter_type,
            filter_value=filter_value,
            sort_by=sort_by,
            sort_order=sort_order,
            limit=limit,
            offset=offset,
        )

        return DashboardDetailsResponse(**details_data)

    except HTTPException:
        raise
    except TenopAPIError:
        raise
    except Exception as e:
        logger.error(f"상세 데이터 조회 오류: {e}")
        raise HTTPException(status_code=500, detail="상세 데이터 조회 실패")


# ════════════════════════════════════════════════════════════════════
# Health Check
# ════════════════════════════════════════════════════════════════════

@router.get(
    "/health",
    summary="대시보드 헬스 체크",
    description="대시보드 서비스 상태 확인",
    tags=["health"]
)
async def health_check():
    """
    대시보드 서비스 헬스 체크

    Returns:
        {"status": "ok", "timestamp": "2026-04-20T10:00:00Z"}
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "service": "dashboard",
    }
