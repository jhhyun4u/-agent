# Scheduler-Integration 구현 가이드 (Do)

**버전**: v1.0
**작성일**: 2026-03-30
**상태**: IMPLEMENTATION
**참고**: Design v1.0 기반

---

## 🚀 구현 시작

**Design 문서**: ✅ 완료됨 (`docs/02-design/features/scheduler-integration.design.md`)

**구현 순서**: 5 Phases (1주일 예정)
- Phase 1: DB 마이그레이션 (1일)
- Phase 2: MigrationService (1-2일)
- Phase 3: APScheduler 통합 (1일)
- Phase 4: API 엔드포인트 (1day)
- Phase 5: E2E 테스트 (1-2day)

---

## Phase 1: 데이터베이스 마이그레이션 (1일)

### 1.1 신규 파일 생성

**파일**: `database/migrations/016_scheduler_integration.sql`

```sql
-- ============================================
-- Migration: Scheduler Integration Tables
-- Version: 1.0
-- Date: 2026-03-30
-- ============================================

-- 1. migration_batches 테이블
CREATE TABLE IF NOT EXISTS migration_batches (
    -- 기본 정보
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_name VARCHAR(255) NOT NULL,

    -- 상태
    status VARCHAR(20) NOT NULL DEFAULT 'pending',

    -- 시간 정보
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    scheduled_at TIMESTAMPTZ NOT NULL,

    -- 처리 통계
    total_documents INT NOT NULL DEFAULT 0,
    processed_documents INT NOT NULL DEFAULT 0,
    failed_documents INT NOT NULL DEFAULT 0,
    skipped_documents INT NOT NULL DEFAULT 0,

    -- 상세 정보
    source_system VARCHAR(100) NOT NULL DEFAULT 'intranet',
    batch_type VARCHAR(50) NOT NULL DEFAULT 'monthly',

    -- 에러 정보
    error_message TEXT,
    error_details JSONB,

    -- 메타데이터
    created_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- 제약조건
    CONSTRAINT status_valid CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'partial_failed'))
);

-- 인덱스
CREATE INDEX idx_migration_batches_status ON migration_batches(status);
CREATE INDEX idx_migration_batches_scheduled ON migration_batches(scheduled_at);
CREATE INDEX idx_migration_batches_created_by ON migration_batches(created_by);

-- 2. migration_schedule 테이블
CREATE TABLE IF NOT EXISTS migration_schedule (
    -- 기본 정보
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 스케줄 설정
    enabled BOOLEAN NOT NULL DEFAULT true,
    cron_expression VARCHAR(100) NOT NULL DEFAULT '0 0 1 * *',
    schedule_name VARCHAR(255) NOT NULL DEFAULT 'monthly_intranet_migration',
    schedule_type VARCHAR(50) NOT NULL DEFAULT 'cron',

    -- 실행 예정
    next_run_at TIMESTAMPTZ,
    last_run_at TIMESTAMPTZ,
    last_batch_id UUID REFERENCES migration_batches(id),

    -- 설정
    timeout_seconds INT DEFAULT 3600,
    max_retries INT DEFAULT 3,
    retry_delay_seconds INT DEFAULT 300,

    -- 알림 설정
    notify_on_success BOOLEAN DEFAULT false,
    notify_on_failure BOOLEAN DEFAULT true,
    notification_channels JSONB DEFAULT '["email", "teams"]'::jsonb,

    -- 메타데이터
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    updated_by UUID REFERENCES users(id),

    -- 제약조건
    CONSTRAINT schedule_type_valid CHECK (schedule_type IN ('cron', 'once', 'interval'))
);

-- 인덱스
CREATE INDEX idx_migration_schedule_enabled ON migration_schedule(enabled);
CREATE INDEX idx_migration_schedule_next_run ON migration_schedule(next_run_at);

-- 3. document_chunks 테이블 확장 (선택)
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS
    migration_batch_id UUID REFERENCES migration_batches(id);

CREATE INDEX IF NOT EXISTS idx_document_chunks_migration_batch
ON document_chunks(migration_batch_id);

-- 4. RLS 정책 (필수)
ALTER TABLE migration_batches ENABLE ROW LEVEL SECURITY;
ALTER TABLE migration_schedule ENABLE ROW LEVEL SECURITY;

-- RLS Policy for migration_batches (SELECT)
CREATE POLICY migration_batches_select
ON migration_batches
FOR SELECT
USING (
    -- 프로젝트 멤버는 조회 가능
    auth.uid() IN (
        SELECT user_id FROM project_members
        WHERE project_id IS NOT NULL
    )
    OR
    -- 시스템 관리자는 항상 조회 가능
    auth.uid() IN (
        SELECT id FROM users WHERE role = 'admin'
    )
);

-- RLS Policy for migration_batches (INSERT)
CREATE POLICY migration_batches_insert
ON migration_batches
FOR INSERT
WITH CHECK (
    -- 프로젝트 관리자만 삽입 가능
    auth.uid() IN (
        SELECT user_id FROM project_members
        WHERE role IN ('admin', 'manager')
    )
);

-- RLS Policy for migration_schedule (SELECT)
CREATE POLICY migration_schedule_select
ON migration_schedule
FOR SELECT
USING (true);  -- 모두 조회 가능

-- RLS Policy for migration_schedule (UPDATE)
CREATE POLICY migration_schedule_update
ON migration_schedule
FOR UPDATE
USING (
    -- 시스템 관리자만 수정 가능
    auth.uid() IN (
        SELECT id FROM users WHERE role = 'admin'
    )
);

-- 5. 초기 데이터 삽입
INSERT INTO migration_schedule (
    id, enabled, cron_expression, schedule_name,
    next_run_at, created_at, updated_at
)
VALUES (
    gen_random_uuid(),
    true,
    '0 0 1 * *',  -- 매달 1일 00:00
    'monthly_intranet_migration',
    NOW() + INTERVAL '1 month',
    NOW(),
    NOW()
)
ON CONFLICT DO NOTHING;
```

### 1.2 마이그레이션 실행

```bash
# Supabase CLI 설치 (아직 안 했으면)
npm install -g supabase

# 마이그레이션 파일 실행
supabase migration up --version 016_scheduler_integration

# 또는 직접 SQL 실행 (Supabase Dashboard)
# SQL Editor → 위 SQL 복사 → 실행
```

### 1.3 검증 체크리스트

- [ ] migration_batches 테이블 생성 확인
- [ ] migration_schedule 테이블 생성 확인
- [ ] 인덱스 3개 생성 확인
- [ ] RLS 정책 4개 활성화 확인
- [ ] 초기 데이터 (schedule) 1개 삽입 확인
- [ ] Supabase Dashboard에서 테이블 조회 가능 확인

```sql
-- 검증 쿼리
SELECT * FROM migration_batches LIMIT 1;
SELECT * FROM migration_schedule LIMIT 1;
SELECT * FROM information_schema.tables
WHERE table_name IN ('migration_batches', 'migration_schedule');
```

---

## Phase 2: MigrationService 구현 (1-2일)

### 2.1 Pydantic 스키마 작성

**파일**: `app/models/migration_schemas.py` (200줄)

```python
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from uuid import UUID

# ===== Request/Response 스키마 =====

class MigrationBatch(BaseModel):
    """배치 작업 기록"""
    id: UUID
    batch_name: str
    status: str  # pending|processing|completed|failed|partial_failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    scheduled_at: datetime
    total_documents: int
    processed_documents: int
    failed_documents: int
    skipped_documents: int
    batch_type: str
    source_system: str
    error_message: Optional[str] = None
    error_details: Optional[dict] = None
    created_by: UUID
    updated_at: datetime

    @property
    def duration_minutes(self) -> Optional[int]:
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() / 60)
        return None

    class Config:
        from_attributes = True

class MigrationSchedule(BaseModel):
    """스케줄 설정"""
    id: UUID
    enabled: bool
    cron_expression: str
    schedule_name: str
    schedule_type: str
    next_run_at: Optional[datetime] = None
    last_run_at: Optional[datetime] = None
    last_batch_id: Optional[UUID] = None
    timeout_seconds: int
    max_retries: int
    retry_delay_seconds: int
    notify_on_success: bool
    notify_on_failure: bool
    notification_channels: List[str]
    created_at: datetime
    updated_at: datetime
    updated_by: Optional[UUID] = None

    class Config:
        from_attributes = True

class MigrationTriggerRequest(BaseModel):
    """배치 즉시 시작 요청"""
    batch_type: str = "manual"
    include_failed_docs: bool = False
    document_limit: Optional[int] = None

class BatchListParams(BaseModel):
    """배치 목록 조회 파라미터"""
    status: Optional[str] = None
    limit: int = 20
    offset: int = 0
    sort_by: str = "scheduled_at"
    order: str = "desc"

class MigrationScheduleUpdate(BaseModel):
    """스케줄 업데이트 요청"""
    enabled: Optional[bool] = None
    cron_expression: Optional[str] = None
    timeout_seconds: Optional[int] = None
    max_retries: Optional[int] = None
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None

class BatchResult(BaseModel):
    """배치 처리 결과"""
    batch_id: UUID
    status: str
    processed: int
    failed: int
    errors: List[str] = []
    duration_seconds: Optional[int] = None
```

### 2.2 MigrationService 구현

**파일**: `app/services/migration_service.py` (500줄)

핵심 메서드들 (자세한 코드는 Design 문서 참고):

```python
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID
import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.migration_schemas import MigrationBatch, MigrationSchedule
from app.services.document_ingestion import DocumentIngestionService
from app.services.notification_service import NotificationService
from app.database import get_db

logger = logging.getLogger(__name__)

class MigrationService:
    """배치 마이그레이션 오케스트레이션 서비스"""

    def __init__(
        self,
        db: AsyncSession,
        doc_service: DocumentIngestionService,
        notification_service: NotificationService
    ):
        self.db = db
        self.doc_service = doc_service
        self.notification = notification_service

    # ===== 주요 메서드 =====

    async def batch_import_intranet_documents(
        self,
        batch_type: str = "monthly",
        include_failed: bool = False
    ) -> MigrationBatch:
        """
        인트라넷 문서 배치 임포트 (메인 오케스트레이터)

        흐름:
        1. 배치 레코드 생성
        2. 변경 문서 감지
        3. 병렬 처리
        4. 완료 기록
        5. 알림 발송
        """
        batch = None
        try:
            # 1. 배치 시작
            batch = await self.create_batch_record(
                batch_type=batch_type,
                total_docs=0
            )
            logger.info(f"Batch started: {batch.id}")

            # 2. 변경 문서 감지
            since = batch.scheduled_at - timedelta(days=30)
            documents = await self.detect_changed_documents(since)

            if include_failed:
                # 이전 실패 문서도 포함
                failed_docs = await self._get_failed_documents(batch)
                documents.extend(failed_docs)

            logger.info(f"Found {len(documents)} documents to process")

            # 3. 배치 정보 업데이트
            await self.db.execute(
                "UPDATE migration_batches SET total_documents = $1 WHERE id = $2",
                len(documents), batch.id
            )

            # 4. 병렬 처리
            results = await self.process_batch_documents(batch.id, documents)

            # 5. 배치 완료
            status = "completed" if results.failed == 0 else "partial_failed"
            await self.complete_batch(
                batch_id=batch.id,
                status=status,
                processed=results.processed,
                failed=results.failed
            )

            # 6. 알림
            if results.failed > 0:
                await self.notification.send_notification(
                    channel="teams",
                    title=f"Migration Batch Completed with Errors",
                    details={
                        "batch_id": str(batch.id),
                        "processed": results.processed,
                        "failed": results.failed,
                        "errors": results.errors[:5]  # 처음 5개만
                    }
                )

            return batch

        except Exception as e:
            logger.error(f"Batch failed: {e}", exc_info=True)
            if batch:
                await self.complete_batch(
                    batch_id=batch.id,
                    status="failed",
                    error=str(e)
                )
            raise

    async def detect_changed_documents(
        self,
        since: datetime
    ) -> List[dict]:
        """
        마지막 마이그레이션 이후 신규/수정 문서 감지

        전략:
        - 인트라넷 API 또는 파일 시스템에서 modified_date > since 조회
        - 로컬 캐시와 비교 (변경 감지 최소화)
        """
        # TODO: 구현 - 인트라넷 API 연동
        # 예시: 인트라넷에서 modified_date > since인 문서 리스트 반환
        pass

    async def process_batch_documents(
        self,
        batch_id: UUID,
        documents: List[dict],
        max_parallel: int = 5
    ) -> BatchResult:
        """
        배치 내 문서들을 병렬로 처리

        특징:
        - 동시 처리 제한 (max_parallel=5)
        - 개별 문서 에러 격리
        - 진행 상황 로깅
        """
        processed = 0
        failed = 0
        errors = []

        # 배치를 작은 단위로 분할 (병렬도 제한)
        for i in range(0, len(documents), max_parallel):
            batch_chunk = documents[i:i+max_parallel]

            # 병렬 처리
            tasks = [
                self._process_single_document(batch_id, doc)
                for doc in batch_chunk
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 결과 집계
            for result in results:
                if isinstance(result, Exception):
                    failed += 1
                    errors.append(str(result))
                else:
                    processed += 1

            # 진행 상황 업데이트
            await self.update_batch_progress(batch_id, processed, failed)

        return BatchResult(
            batch_id=batch_id,
            status="completed",
            processed=processed,
            failed=failed,
            errors=errors
        )

    async def _process_single_document(
        self,
        batch_id: UUID,
        doc: dict,
        retry_count: int = 0
    ) -> dict:
        """
        단일 문서 처리 (document_ingestion 재사용)

        재시도: 지수 백오프 (5s, 10s, 20s...)
        """
        max_retries = 3
        base_delay = 5

        try:
            # document_ingestion.process_document() 호출
            result = await self.doc_service.process_document(
                file_path=doc['path'],
                project_id=doc['project_id'],
                batch_id=batch_id
            )
            return {"status": "success", "file": doc['path']}

        except Exception as e:
            if retry_count < max_retries:
                delay = base_delay * (2 ** retry_count)
                logger.warning(f"Retry {retry_count+1} after {delay}s: {doc['path']}")
                await asyncio.sleep(delay)
                return await self._process_single_document(
                    batch_id, doc, retry_count + 1
                )
            else:
                logger.error(f"Failed after {max_retries} retries: {doc['path']}")
                raise

    # ===== CRUD 메서드 =====

    async def create_batch_record(
        self,
        batch_type: str,
        total_docs: int
    ) -> MigrationBatch:
        """배치 시작 레코드 생성"""
        # TODO: DB INSERT
        pass

    async def update_batch_progress(
        self,
        batch_id: UUID,
        processed: int,
        failed: int = 0
    ) -> None:
        """배치 진행 상황 업데이트"""
        # TODO: DB UPDATE
        pass

    async def complete_batch(
        self,
        batch_id: UUID,
        status: str,
        processed: int = 0,
        failed: int = 0,
        error: str = None
    ) -> None:
        """배치 완료 처리"""
        # TODO: DB UPDATE
        pass

    async def get_batch_history(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str = None
    ) -> List[MigrationBatch]:
        """배치 히스토리 조회"""
        # TODO: DB SELECT with filtering
        pass

    # ===== 스케줄 관리 =====

    async def get_schedule(self) -> MigrationSchedule:
        """현재 스케줄 설정 조회"""
        # TODO: DB SELECT
        pass

    async def update_schedule(
        self,
        schedule_id: UUID,
        **kwargs
    ) -> MigrationSchedule:
        """스케줄 업데이트"""
        # TODO: DB UPDATE
        pass
```

### 2.3 검증 체크리스트

- [ ] migration_schemas.py 작성 (6개 모델)
- [ ] MigrationService 클래스 구현 (14개 메서드)
- [ ] Unit 테스트 작성 (10개 테스트)
  - [ ] test_detect_changed_documents
  - [ ] test_process_batch_partial_failure
  - [ ] test_batch_record_creation
  - [ ] test_exponential_backoff_retry
  - [ ] 등등
- [ ] requirements.txt 업데이트: sqlalchemy>=2.0, asyncpg>=0.28

---

## Phase 3: APScheduler 통합 (1일)

### 3.1 스케줄러 파일 생성

**파일**: `app/scheduler.py` (150줄)

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime
from typing import Optional

from app.services.migration_service import MigrationService

logger = logging.getLogger(__name__)

class MigrationScheduler:
    """APScheduler를 이용한 마이그레이션 스케줄 관리"""

    def __init__(self, migration_service: MigrationService):
        self.migration_service = migration_service
        self.scheduler: Optional[AsyncIOScheduler] = None

    async def initialize(self):
        """백그라운드 스케줄러 초기화"""
        self.scheduler = AsyncIOScheduler()

        # DB에서 스케줄 설정 로드
        schedule = await self.migration_service.get_schedule()

        if schedule.enabled:
            # 크론 표현식 파싱
            cron_kwargs = self._parse_cron(schedule.cron_expression)

            # 작업 추가
            self.scheduler.add_job(
                self._scheduled_batch_import,
                CronTrigger(**cron_kwargs),
                id='migration_monthly',
                name='Monthly Intranet Migration',
                misfire_grace_time=60,  # 1분 오차 허용
                coalesce=True,
                max_instances=1
            )
            logger.info(f"Migration job scheduled: {schedule.cron_expression}")
        else:
            logger.info("Migration scheduler is disabled")

        self.scheduler.start()

    async def _scheduled_batch_import(self):
        """스케줄된 배치 실행"""
        try:
            logger.info("Starting scheduled migration batch")
            batch = await self.migration_service.batch_import_intranet_documents(
                batch_type="monthly"
            )
            logger.info(f"Scheduled migration completed: {batch.id}")
        except Exception as e:
            logger.error(f"Scheduled migration failed: {e}", exc_info=True)
            # 에러 알림은 migration_service에서 처리

    def _parse_cron(self, cron_expr: str) -> dict:
        """
        크론 표현식 → APScheduler 파라미터 변환

        예시:
        "0 0 1 * *" → {'minute': 0, 'hour': 0, 'day': 1}
        "0 */6 * * *" → {'minute': 0, 'hour': '*/6'}
        """
        parts = cron_expr.split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {cron_expr}")

        minute, hour, day, month, dow = parts

        return {
            'minute': minute,
            'hour': hour,
            'day': day,
            'month': month,
            'day_of_week': dow
        }

    def shutdown(self):
        """스케줄러 종료"""
        if self.scheduler and self.scheduler.running:
            logger.info("Shutting down migration scheduler")
            self.scheduler.shutdown()
```

### 3.2 main.py 수정

```python
# app/main.py

from contextlib import asynccontextmanager
from app.scheduler import MigrationScheduler
from app.services.migration_service import MigrationService

# ... 기존 코드 ...

# 전역 변수
migration_scheduler: Optional[MigrationScheduler] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan 이벤트"""
    # Startup
    global migration_scheduler

    # DB, 서비스 초기화
    migration_service = MigrationService(
        db=get_db(),
        doc_service=DocumentIngestionService(),
        notification_service=NotificationService()
    )

    # 스케줄러 초기화
    migration_scheduler = MigrationScheduler(migration_service)
    await migration_scheduler.initialize()

    logger.info("Migration scheduler started")

    yield  # 애플리케이션 실행

    # Shutdown
    migration_scheduler.shutdown()
    logger.info("Migration scheduler stopped")

# FastAPI 앱 생성
app = FastAPI(
    title="Tenopa Proposer API",
    lifespan=lifespan
)

# ... 라우터 등록 등 기존 코드 ...
```

### 3.3 검증 체크리스트

- [ ] app/scheduler.py 작성
- [ ] main.py lifespan 추가
- [ ] requirements.txt 업데이트: `apscheduler>=3.10.0`
- [ ] 로컬 테스트: 서버 시작 시 "Migration scheduler started" 로그 확인
- [ ] 로컬 테스트: cron 파싱 정상 작동 확인

```bash
# requirements.txt에 추가
apscheduler>=3.10.0
```

---

## Phase 4: API 엔드포인트 (1day)

### 4.1 라우터 파일 생성

**파일**: `app/api/routes_migrations.py` (300줄)

```python
from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.api.deps import get_current_user, require_project_access
from app.models.migration_schemas import (
    MigrationBatch, MigrationSchedule, MigrationTriggerRequest,
    BatchListParams, MigrationScheduleUpdate
)
from app.services.migration_service import MigrationService

router = APIRouter(
    prefix="/api/migrations",
    tags=["migrations"]
)

# ===== 배치 작업 관련 =====

@router.get("/batches", response_model=dict)
async def list_batches(
    status: str = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """배치 히스토리 조회"""
    service = MigrationService(db, doc_service, notification_service)

    batches = await service.get_batch_history(
        limit=limit,
        offset=offset,
        status=status
    )

    return {
        "total": len(batches),
        "limit": limit,
        "offset": offset,
        "batches": batches
    }

@router.post("/trigger", response_model=dict, status_code=202)
async def trigger_migration(
    request: MigrationTriggerRequest,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """즉시 배치 시작 (비동기)"""
    # 권한 확인: 관리자만 가능
    if current_user.role not in ["admin", "manager"]:
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = MigrationService(db, doc_service, notification_service)

    # 백그라운드에서 실행
    import asyncio
    asyncio.create_task(
        service.batch_import_intranet_documents(
            batch_type=request.batch_type,
            include_failed=request.include_failed_docs
        )
    )

    return {
        "status": "accepted",
        "message": "Migration batch started in background",
        "batch_type": request.batch_type
    }

@router.get("/{batch_id}", response_model=MigrationBatch)
async def get_batch_detail(
    batch_id: UUID,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """배치 상세 조회"""
    service = MigrationService(db, doc_service, notification_service)

    batch = await service.get_batch(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")

    return batch

# ===== 스케줄 관리 =====

@router.get("/schedule", response_model=MigrationSchedule)
async def get_schedule(
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """현재 스케줄 설정 조회"""
    service = MigrationService(db, doc_service, notification_service)
    return await service.get_schedule()

@router.put("/schedule/{schedule_id}", response_model=MigrationSchedule)
async def update_schedule(
    schedule_id: UUID,
    request: MigrationScheduleUpdate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """스케줄 설정 업데이트 (관리자만)"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    service = MigrationService(db, doc_service, notification_service)
    return await service.update_schedule(schedule_id, **request.dict(exclude_unset=True))
```

### 4.2 main.py 라우터 등록

```python
# app/main.py

from app.api import routes_migrations

app.include_router(routes_migrations.router)
```

### 4.3 검증 체크리스트

- [ ] routes_migrations.py 작성 (5개 엔드포인트)
- [ ] main.py에 라우터 등록
- [ ] 로컬 테스트: GET /api/migrations/batches 응답 확인
- [ ] 로컬 테스트: POST /api/migrations/trigger 202 응답 확인
- [ ] 로컬 테스트: PUT /api/migrations/schedule/{id} 업데이트 확인
- [ ] 인증 검증: 권한 없는 사용자는 403 응답 확인

---

## Phase 5: E2E 테스트 (1-2day)

### 5.1 테스트 파일 작성

**파일**: `tests/test_migration_service.py` (300줄)
**파일**: `tests/test_routes_migrations.py` (250줄)
**파일**: `tests/test_e2e_scheduler.py` (200줄)

```python
# tests/test_e2e_scheduler.py (예시)

import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

class TestSchedulerE2E:

    async def test_monthly_cron_execution(self, migration_service):
        """매달 1일 00:00 자동 실행 테스트"""
        # 스케줄 확인
        schedule = await migration_service.get_schedule()
        assert schedule.cron_expression == "0 0 1 * *"
        assert schedule.enabled is True

        # 다음 실행시간 계산
        next_run = await migration_service._calculate_next_run(
            schedule.cron_expression
        )
        assert next_run.hour == 0
        assert next_run.minute == 0
        assert next_run.day == 1

    async def test_manual_trigger_flow(self, client, current_user):
        """수동 트리거 전체 흐름"""
        # 1. 트리거 요청
        response = await client.post(
            "/api/migrations/trigger",
            json={"batch_type": "manual"}
        )
        assert response.status_code == 202

        # 2. 배치 생성 확인
        batches = await client.get("/api/migrations/batches")
        assert len(batches.json()["batches"]) > 0

        # 3. 배치 상태 확인
        batch = batches.json()["batches"][0]
        assert batch["status"] in ["pending", "processing", "completed"]

    async def test_failed_batch_retry_flow(self, migration_service, mock_doc_service):
        """실패 배치 재시도 흐름"""
        # 1. 첫 번째 배치 실행 (실패)
        with patch.object(mock_doc_service, 'process_document', side_effect=Exception("Test error")):
            batch1 = await migration_service.batch_import_intranet_documents()
            assert batch1.status == "failed"

        # 2. 재시도
        batch2 = await migration_service.retry_failed_batch(batch1.id)
        assert batch2.status in ["processing", "completed"]

    async def test_scheduler_graceful_shutdown(self, scheduler):
        """스케줄러 우아한 종료"""
        assert scheduler.scheduler.running is True

        scheduler.shutdown()

        assert scheduler.scheduler.running is False

    async def test_notification_on_completion(self, migration_service, mock_notification):
        """완료 후 알림 발송"""
        with patch.object(mock_notification, 'send_notification') as mock_send:
            batch = await migration_service.batch_import_intranet_documents()

            # 알림 발송 확인
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert "batch_id" in call_args.kwargs["details"]
```

### 5.2 검증 체크리스트

- [ ] Unit 테스트 10개 작성 + 통과
- [ ] Integration 테스트 8개 작성 + 통과
- [ ] E2E 테스트 5개 작성 + 통과
- [ ] 커버리지: 90% 이상
- [ ] 모든 테스트 실행: `pytest tests/ -v`

```bash
# 테스트 실행
pytest tests/test_migration_service.py -v
pytest tests/test_routes_migrations.py -v
pytest tests/test_e2e_scheduler.py -v

# 커버리지 확인
pytest tests/ --cov=app --cov-report=html
```

---

## 최종 체크리스트

### ✅ 구현 완료 확인

- [ ] Phase 1: DB 마이그레이션 완료
- [ ] Phase 2: MigrationService + 스키마 완료
- [ ] Phase 3: APScheduler 통합 완료
- [ ] Phase 4: API 엔드포인트 완료
- [ ] Phase 5: E2E 테스트 완료

### ✅ 코드 품질 확인

- [ ] ruff check: 0개 경고
- [ ] mypy check: 0개 에러
- [ ] test coverage: 90% 이상
- [ ] performance: 1시간 내 처리 완료

### ✅ 배포 준비

- [ ] requirements.txt 업데이트
- [ ] .env 설정 확인
- [ ] Supabase 마이그레이션 검증
- [ ] 스테이징 환경 테스트
- [ ] 본운영 배포 체크리스트 작성

---

## 다음 단계

### Check Phase (Gap 분석)
```bash
/pdca analyze scheduler-integration
```

→ Design vs 구현 코드 비교 (목표: 90% 이상 매치)

### 진행 추적
```bash
/pdca status
```

---

## 참고 자료

- **Design 문서**: `docs/02-design/features/scheduler-integration.design.md`
- **Plan 문서**: `docs/01-plan/features/scheduler-integration.plan.md`
- **프로젝트 구조**: `-agent-master/`

---

**Happy Coding! 🚀**

구현 중 막히는 부분이 있으면 언제든 물어봐주세요!
