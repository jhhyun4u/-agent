"""
DB 마이그레이션 상태 API (설계 §4.4)

GET /api/migrations/status   — 현재 상태 + 전체 목록 (GAP-H3)
GET /api/migrations/history  — 실행 이력 (페이징) (GAP-H4)
GET /api/migrations/summary  — 통계 요약 (GAP-H5)

권한: admin만 허용 (설계 §7.1)
"""

import logging
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, require_role
from app.exceptions import InternalServiceError
from app.models.auth_schemas import CurrentUser
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/migrations", tags=["migration-status"])


# ─────────────────────────────────────────────
# Pydantic 응답 모델
# ─────────────────────────────────────────────

from pydantic import BaseModel, Field


class MigrationItem(BaseModel):
    """GET /api/migrations/status 내 개별 항목"""
    version: str
    name: str
    applied_at: Optional[datetime] = None
    status: str
    execution_time_ms: Optional[int] = None


class MigrationStatusResponse(BaseModel):
    """GET /api/migrations/status 응답 (설계 §4.4.1)"""
    status: str = Field(description="ok | degraded | unknown")
    total: int
    successful: int
    failed: int
    migrations: list[MigrationItem]


class MigrationHistoryItem(BaseModel):
    """GET /api/migrations/history 내 개별 항목"""
    id: int
    version: str
    name: str
    applied_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None
    status: str
    error_message: Optional[str] = None


class MigrationHistoryResponse(BaseModel):
    """GET /api/migrations/history 응답 (설계 §4.4.2)"""
    total: int
    limit: int
    offset: int
    data: list[MigrationHistoryItem]


class MigrationSummaryResponse(BaseModel):
    """GET /api/migrations/summary 응답 (설계 §4.4.3)"""
    total: int
    applied: int
    failed: int
    pending: int
    success_rate: str
    last_applied_at: Optional[datetime] = None


# ─────────────────────────────────────────────
# 엔드포인트
# ─────────────────────────────────────────────


@router.get(
    "/status",
    response_model=MigrationStatusResponse,
    summary="마이그레이션 현재 상태 조회",
)
async def get_migration_status(
    user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_role("admin")),
    db=Depends(get_async_client),
) -> MigrationStatusResponse:
    """migration_history 테이블 기반 전체 상태 반환 (설계 §4.4.1).

    권한: admin
    """
    try:
        res = await (
            db.table("migration_history")
            .select("version, name, applied_at, status, execution_time_ms")
            .order("version", desc=False)
            .execute()
        )
        rows: list[dict[str, Any]] = res.data or []

        successful = sum(1 for r in rows if r.get("status") == "success")
        failed = sum(1 for r in rows if r.get("status") == "failed")
        overall = "ok" if failed == 0 else "degraded"

        migrations = [
            MigrationItem(
                version=r["version"],
                name=r.get("name") or r["version"],
                applied_at=r.get("applied_at"),
                status=r.get("status", "unknown"),
                execution_time_ms=r.get("execution_time_ms"),
            )
            for r in rows
        ]

        return MigrationStatusResponse(
            status=overall,
            total=len(rows),
            successful=successful,
            failed=failed,
            migrations=migrations,
        )

    except Exception as e:
        logger.error(f"마이그레이션 상태 조회 실패: {e}")
        raise InternalServiceError(f"마이그레이션 상태 조회 실패: {str(e)}")


@router.get(
    "/history",
    response_model=MigrationHistoryResponse,
    summary="마이그레이션 실행 이력 조회",
)
async def get_migration_history(
    limit: int = Query(default=50, ge=1, le=200, description="페이지당 항목 수"),
    offset: int = Query(default=0, ge=0, description="시작 오프셋"),
    user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_role("admin")),
    db=Depends(get_async_client),
) -> MigrationHistoryResponse:
    """migration_history 테이블 전체 이력 반환 (설계 §4.4.2).

    - 최신순 정렬 (applied_at DESC)
    - limit/offset 페이징

    권한: admin
    """
    try:
        # 전체 건수 조회
        count_res = await (
            db.table("migration_history")
            .select("id", count="exact")
            .execute()
        )
        total: int = count_res.count or 0

        # 페이지 데이터 조회
        res = await (
            db.table("migration_history")
            .select("id, version, name, applied_at, execution_time_ms, status, error_message")
            .order("applied_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        rows: list[dict[str, Any]] = res.data or []

        data = [
            MigrationHistoryItem(
                id=r["id"],
                version=r["version"],
                name=r.get("name") or r["version"],
                applied_at=r.get("applied_at"),
                execution_time_ms=r.get("execution_time_ms"),
                status=r.get("status", "unknown"),
                error_message=r.get("error_message"),
            )
            for r in rows
        ]

        return MigrationHistoryResponse(
            total=total,
            limit=limit,
            offset=offset,
            data=data,
        )

    except Exception as e:
        logger.error(f"마이그레이션 이력 조회 실패: {e}")
        raise InternalServiceError(f"마이그레이션 이력 조회 실패: {str(e)}")


@router.get(
    "/summary",
    response_model=MigrationSummaryResponse,
    summary="마이그레이션 통계 요약",
)
async def get_migration_summary(
    user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_role("admin")),
    db=Depends(get_async_client),
) -> MigrationSummaryResponse:
    """migration_history 기반 성공/실패/대기 통계 반환 (설계 §4.4.3).

    pending은 migration_history에 없는 파일 수 기반이 아닌
    failed 레코드를 재시도 대기로 간주하는 단순 계산을 사용합니다
    (스크립트 실행 없이 API만으로 파일 시스템 접근 불가).

    권한: admin
    """
    try:
        res = await (
            db.table("migration_history")
            .select("status, applied_at")
            .execute()
        )
        rows: list[dict[str, Any]] = res.data or []

        total = len(rows)
        applied = sum(1 for r in rows if r.get("status") == "success")
        failed = sum(1 for r in rows if r.get("status") == "failed")
        # pending: failed는 재시도 대기로 집계 (파일 시스템 미접근)
        pending = failed

        success_rate = (
            f"{applied / total * 100:.1f}%" if total > 0 else "0.0%"
        )

        success_rows = [r for r in rows if r.get("status") == "success"]
        last_applied_at: Optional[datetime] = None
        if success_rows:
            # applied_at이 문자열일 수 있으므로 안전하게 파싱
            raw_times = [r.get("applied_at") for r in success_rows if r.get("applied_at")]
            if raw_times:
                parsed = []
                for t in raw_times:
                    if isinstance(t, datetime):
                        parsed.append(t)
                    else:
                        try:
                            parsed.append(datetime.fromisoformat(str(t).replace("Z", "+00:00")))
                        except ValueError:
                            pass
                if parsed:
                    last_applied_at = max(parsed)

        return MigrationSummaryResponse(
            total=total,
            applied=applied,
            failed=failed,
            pending=pending,
            success_rate=success_rate,
            last_applied_at=last_applied_at,
        )

    except Exception as e:
        logger.error(f"마이그레이션 요약 조회 실패: {e}")
        raise InternalServiceError(f"마이그레이션 요약 조회 실패: {str(e)}")
