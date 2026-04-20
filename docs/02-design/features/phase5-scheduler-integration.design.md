# Phase 5: Scheduler Integration - 상세 설계

**버전**: v1.0  
**작성일**: 2026-04-20  
**상태**: IMPLEMENTATION READY  

---

## 1. 모듈 설계

### 1.1 SchedulerService (`app/services/scheduler_service.py`)

**목적**: APScheduler와 Supabase 연동을 통한 정기 마이그레이션 관리

```python
class SchedulerService:
    """정기 문서 마이그레이션 스케줄러"""
    
    def __init__(
        self,
        db_client: AsyncSupabaseClient,
        intranet_client: IntranetClient,
        logger: logging.Logger
    ):
        self.db = db_client
        self.intranet = intranet_client
        self.logger = logger
        self.scheduler = AsyncScheduler()
        self._jobs = {}  # {schedule_id: APScheduler job}
    
    # Public Methods
    
    async def initialize(self):
        """서버 시작 시 모든 활성 스케줄 복구"""
        schedules = await self._get_active_schedules()
        for schedule in schedules:
            await self.add_job(schedule)
    
    async def add_schedule(
        self,
        name: str,
        cron_expression: str,  # "0 0 1 * *"
        source_type: str,       # "intranet"
        enabled: bool = True
    ) -> UUID:
        """새 스케줄 등록"""
        schedule_id = uuid4()
        await self.db.table("migration_schedules").insert({
            "id": schedule_id,
            "name": name,
            "cron_expression": cron_expression,
            "source_type": source_type,
            "enabled": enabled,
            "created_at": datetime.now(timezone.utc)
        })
        
        if enabled:
            await self.add_job({"id": schedule_id, ...})
        
        return schedule_id
    
    async def trigger_migration_now(self, schedule_id: UUID) -> UUID:
        """즉시 마이그레이션 트리거"""
        batch_id = await self._create_batch(schedule_id)
        await self._run_batch(batch_id)
        return batch_id
    
    async def add_job(self, schedule: dict):
        """APScheduler에 작업 등록"""
        job = self.scheduler.add_job(
            self._batch_job_runner,
            trigger=CronTrigger.from_crontab(schedule["cron_expression"]),
            args=[schedule["id"]],
            id=str(schedule["id"])
        )
        self._jobs[schedule["id"]] = job
    
    async def remove_job(self, schedule_id: UUID):
        """APScheduler에서 작업 제거"""
        if schedule_id in self._jobs:
            self._jobs[schedule_id].remove()
            del self._jobs[schedule_id]
    
    # Private Methods
    
    async def _batch_job_runner(self, schedule_id: UUID):
        """배치 작업 실행 (APScheduler 콜백)"""
        try:
            batch_id = await self._create_batch(schedule_id)
            await self._run_batch(batch_id)
            await self._mark_schedule_run(schedule_id)
        except Exception as e:
            self.logger.error(f"Batch job failed: {e}", exc_info=True)
    
    async def _create_batch(self, schedule_id: UUID) -> UUID:
        """배치 레코드 생성"""
        batch_id = uuid4()
        await self.db.table("migration_batches").insert({
            "id": batch_id,
            "schedule_id": schedule_id,
            "status": "pending",
            "total_documents": 0,
            "processed_documents": 0,
            "failed_documents": 0,
            "created_at": datetime.now(timezone.utc)
        })
        return batch_id
    
    async def _run_batch(self, batch_id: UUID):
        """배치 실행"""
        # Fetch documents to migrate
        documents = await self._fetch_documents_to_migrate()
        
        # Update batch with total count
        await self.db.table("migration_batches").update({
            "status": "running",
            "total_documents": len(documents),
            "started_at": datetime.now(timezone.utc)
        }).eq("id", batch_id)
        
        # Process batch
        processor = ConcurrentBatchProcessor(
            db_client=self.db,
            num_workers=5,
            max_retries=3
        )
        
        result = await processor.process_batch(documents, batch_id)
        
        # Finalize batch
        await self.db.table("migration_batches").update({
            "status": result["status"],  # "success" or "partial"
            "processed_documents": result["processed"],
            "failed_documents": result["failed"],
            "completed_at": datetime.now(timezone.utc),
            "duration_seconds": result["duration"]
        }).eq("id", batch_id)
    
    async def _fetch_documents_to_migrate(self) -> List[dict]:
        """마이그레이션할 문서 조회 (변경 감지)"""
        # Get last migration timestamp
        last_batch = await self.db.table("migration_batches")\
            .select("completed_at")\
            .order("completed_at", ascending=False)\
            .limit(1)\
            .single()
        
        sync_since = last_batch["completed_at"] if last_batch else None
        
        # Fetch modified documents from intranet
        documents = await self.intranet.fetch_documents(
            modified_since=sync_since
        )
        
        return documents
    
    async def _get_active_schedules(self) -> List[dict]:
        """활성 스케줄 조회"""
        result = await self.db.table("migration_schedules")\
            .select("*")\
            .eq("enabled", True)\
            .execute()
        return result.data
    
    async def _mark_schedule_run(self, schedule_id: UUID):
        """스케줄 마지막 실행 시간 갱신"""
        await self.db.table("migration_schedules").update({
            "last_run_at": datetime.now(timezone.utc),
            "next_run_at": self._calculate_next_run(schedule_id)
        }).eq("id", schedule_id)
```

### 1.2 ConcurrentBatchProcessor (`app/services/batch_processor.py`)

**목적**: 대량 문서 병렬 처리 및 재시도 로직

```python
class ConcurrentBatchProcessor:
    """병렬 배치 문서 처리기"""
    
    def __init__(
        self,
        db_client: AsyncSupabaseClient,
        num_workers: int = 5,
        max_retries: int = 3,
        logger: logging.Logger = None
    ):
        self.db = db_client
        self.num_workers = num_workers
        self.max_retries = max_retries
        self.logger = logger or logging.getLogger(__name__)
        self.executor = ThreadPoolExecutor(max_workers=num_workers)
    
    async def process_batch(
        self,
        documents: List[dict],
        batch_id: UUID
    ) -> dict:
        """문서 배치 병렬 처리"""
        start_time = time.time()
        results = {
            "processed": 0,
            "failed": 0,
            "duration": 0,
            "status": "success"
        }
        
        # Create task queue
        tasks = [
            self._process_with_retry(doc, batch_id)
            for doc in documents
        ]
        
        # Run tasks concurrently
        outcomes = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Aggregate results
        for outcome in outcomes:
            if isinstance(outcome, Exception):
                results["failed"] += 1
                results["status"] = "partial"
                self.logger.error(f"Processing failed: {outcome}")
            elif outcome["success"]:
                results["processed"] += 1
            else:
                results["failed"] += 1
                results["status"] = "partial"
        
        results["duration"] = int(time.time() - start_time)
        return results
    
    async def _process_with_retry(
        self,
        document: dict,
        batch_id: UUID
    ) -> dict:
        """재시도 로직을 포함한 문서 처리"""
        for attempt in range(1, self.max_retries + 1):
            try:
                result = await self._process_single_document(document)
                
                # Log success
                await self._log_migration(batch_id, document, "success", None)
                
                return {"success": True, "document_id": document["id"]}
                
            except Exception as e:
                self.logger.warning(
                    f"Attempt {attempt}/{self.max_retries} failed: {e}"
                )
                
                if attempt == self.max_retries:
                    # Final failure
                    await self._log_migration(
                        batch_id, document, "failed", str(e)
                    )
                    return {
                        "success": False,
                        "document_id": document["id"],
                        "error": str(e)
                    }
                
                # Exponential backoff
                await asyncio.sleep(2 ** (attempt - 1))
        
        return {"success": False}
    
    async def _process_single_document(self, document: dict) -> dict:
        """개별 문서 처리"""
        # Use existing document_ingestion pipeline
        from app.services.document_ingestion import process_document_bounded
        
        result = await process_document_bounded(
            file_content=document["content"],
            filename=document["filename"],
            org_id=document["org_id"],
            doc_type=document.get("doc_type", "기타"),
            metadata={
                "source": "intranet_migration",
                "batch_id": document.get("batch_id")
            }
        )
        
        return result
    
    async def _log_migration(
        self,
        batch_id: UUID,
        document: dict,
        status: str,
        error: Optional[str]
    ):
        """마이그레이션 로그 기록"""
        await self.db.table("migration_logs").insert({
            "id": uuid4(),
            "batch_id": batch_id,
            "source_document_id": document["id"],
            "document_name": document["filename"],
            "status": status,
            "error_message": error,
            "retry_count": document.get("retry_count", 0),
            "processed_at": datetime.now(timezone.utc)
        })
```

---

## 2. API 엔드포인트 설계

### 2.1 라우터: `app/api/routes_migration.py`

```python
router = APIRouter(prefix="/api/migration", tags=["migration"])

@router.post("/schedules")
async def create_schedule(
    schedule: CreateScheduleRequest,
    current_user: CurrentUser = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler_service)
) -> ScheduleResponse:
    """새 마이그레이션 스케줄 생성"""
    schedule_id = await scheduler.add_schedule(
        name=schedule.name,
        cron_expression=schedule.cron_expression,
        source_type=schedule.source_type,
        enabled=schedule.enabled
    )
    return ScheduleResponse(id=schedule_id)

@router.get("/schedules")
async def list_schedules(
    current_user: CurrentUser = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler_service)
) -> List[ScheduleResponse]:
    """모든 마이그레이션 스케줄 조회"""
    pass

@router.post("/trigger/{schedule_id}")
async def trigger_migration(
    schedule_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    scheduler: SchedulerService = Depends(get_scheduler_service)
) -> BatchResponse:
    """즉시 마이그레이션 트리거"""
    batch_id = await scheduler.trigger_migration_now(schedule_id)
    return BatchResponse(id=batch_id, status="running")

@router.get("/batches")
async def list_batches(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSupabaseClient = Depends(get_async_client)
) -> PaginatedBatchResponse:
    """배치 이력 조회 (페이지네이션)"""
    pass

@router.get("/batches/{batch_id}")
async def get_batch_detail(
    batch_id: UUID,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSupabaseClient = Depends(get_async_client)
) -> BatchDetailResponse:
    """배치 상세 정보 조회"""
    pass

@router.get("/batches/{batch_id}/logs")
async def get_batch_logs(
    batch_id: UUID,
    status: Optional[str] = Query(None),  # "success", "failed"
    limit: int = Query(100, ge=1, le=1000),
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSupabaseClient = Depends(get_async_client)
) -> PaginatedMigrationLogResponse:
    """배치의 개별 문서 처리 로그"""
    pass
```

### 2.2 Pydantic 스키마

```python
# app/models/migration_schemas.py

class CreateScheduleRequest(BaseModel):
    name: str
    cron_expression: str  # "0 0 1 * *"
    source_type: str
    enabled: bool = True

class ScheduleResponse(BaseModel):
    id: UUID
    name: str
    cron_expression: str
    source_type: str
    enabled: bool
    last_run_at: Optional[datetime]
    next_run_at: Optional[datetime]
    created_at: datetime

class BatchResponse(BaseModel):
    id: UUID
    schedule_id: UUID
    status: str  # "pending", "running", "success", "partial", "failed"
    total_documents: int
    processed_documents: int
    failed_documents: int
    started_at: datetime
    completed_at: Optional[datetime]

class BatchDetailResponse(BatchResponse):
    error_message: Optional[str]
    duration_seconds: Optional[int]

class MigrationLogResponse(BaseModel):
    id: UUID
    batch_id: UUID
    source_document_id: str
    document_name: str
    status: str
    error_message: Optional[str]
    retry_count: int
    processed_at: datetime

class PaginatedBatchResponse(BaseModel):
    total: int
    limit: int
    offset: int
    data: List[BatchResponse]
```

---

## 3. 데이터베이스 스키마

### 3.1 마이그레이션 스케줄

```sql
CREATE TABLE migration_schedules (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    cron_expression VARCHAR(50) NOT NULL,  -- e.g., "0 0 1 * *"
    source_type VARCHAR(50) NOT NULL,      -- "intranet", etc.
    enabled BOOLEAN NOT NULL DEFAULT true,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    
    CONSTRAINT valid_cron CHECK (cron_expression ~ '^\d+ \d+ \d+ \d+ \d+$')
);

CREATE INDEX idx_migration_schedules_enabled ON migration_schedules(enabled);
```

### 3.2 마이그레이션 배치

```sql
CREATE TABLE migration_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    schedule_id UUID NOT NULL REFERENCES migration_schedules(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL,  -- "pending", "running", "success", "partial", "failed"
    total_documents INT NOT NULL DEFAULT 0,
    processed_documents INT NOT NULL DEFAULT 0,
    failed_documents INT NOT NULL DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_seconds INT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'running', 'success', 'partial', 'failed')),
    CONSTRAINT valid_counts CHECK (
        total_documents >= 0 AND
        processed_documents >= 0 AND
        failed_documents >= 0 AND
        processed_documents + failed_documents <= total_documents
    )
);

CREATE INDEX idx_migration_batches_schedule ON migration_batches(schedule_id);
CREATE INDEX idx_migration_batches_status ON migration_batches(status);
CREATE INDEX idx_migration_batches_created ON migration_batches(created_at DESC);
```

### 3.3 마이그레이션 로그

```sql
CREATE TABLE migration_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_id UUID NOT NULL REFERENCES migration_batches(id) ON DELETE CASCADE,
    source_document_id VARCHAR(100) NOT NULL,
    document_name VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,  -- "success", "failed", "skipped"
    error_message TEXT,
    retry_count INT NOT NULL DEFAULT 0,
    processed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT now(),
    
    CONSTRAINT valid_status CHECK (status IN ('success', 'failed', 'skipped'))
);

CREATE INDEX idx_migration_logs_batch ON migration_logs(batch_id);
CREATE INDEX idx_migration_logs_status ON migration_logs(status);
CREATE INDEX idx_migration_logs_document ON migration_logs(source_document_id);
```

### 3.4 RLS 정책

```sql
-- 자신의 조직 스케줄만 볼 수 있음
ALTER TABLE migration_schedules ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users can view schedules in their org" ON migration_schedules
    FOR SELECT USING (
        org_id = (SELECT org_id FROM auth.users WHERE id = auth.uid())
    );

CREATE POLICY "admins can manage schedules" ON migration_schedules
    FOR ALL USING (
        has_role('admin') -- Custom function
    );
```

---

## 4. 에러 처리 & 모니터링

### 4.1 에러 시나리오

| 시나리오 | 처리 방법 | 재시도 |
|---------|---------|--------|
| 문서 처리 실패 | 배치 계속 진행 | ✅ 3회 |
| DB 연결 오류 | 지수 백오프 | ✅ 3회 |
| 스케줄 실행 실패 | 로그 + Slack 알림 | ❌ |
| 부분 실패 (>50%) | 상태: "partial" | ❌ |

### 4.2 모니터링 메트릭

```python
# Prometheus 메트릭
- migration_batches_total (배치 총 개수)
- migration_documents_processed (처리된 문서 수)
- migration_documents_failed (실패한 문서 수)
- migration_batch_duration_seconds (배치 소요 시간)
- migration_retry_count (재시도 횟수)
```

---

## 5. 테스트 계획

### 5.1 단위 테스트 (12개)

```python
# test_scheduler_service.py
- test_add_schedule_creates_record
- test_trigger_migration_now_creates_batch
- test_fetch_documents_with_change_detection
- test_mark_schedule_run_updates_timestamp

# test_batch_processor.py
- test_process_batch_parallel_execution
- test_process_with_retry_success_on_second_attempt
- test_process_with_retry_fails_after_max_retries
- test_batch_aggregates_results_correctly

# test_change_detection.py
- test_identifies_new_documents
- test_identifies_modified_documents
- test_skips_unchanged_documents
- test_handles_missing_sync_timestamp
```

### 5.2 통합 테스트 (12개)

```python
# test_e2e_migration.py
- test_full_batch_execution_flow
- test_batch_with_mixed_success_failure
- test_scheduler_triggers_batch_at_cron_time
- test_api_trigger_endpoint_works

# test_database_migration.py
- test_migration_script_creates_all_tables
- test_rls_policies_enforced
- test_indices_created_correctly
- test_migration_idempotent

# test_error_scenarios.py
- test_handles_document_processing_error
- test_handles_db_connection_error
- test_handles_storage_error
- test_rollback_on_critical_failure
```

---

## 6. 배포 전 체크리스트

- [ ] 모든 24개 테스트 통과
- [ ] 코드 커버리지 ≥ 80%
- [ ] 성능 테스트: 1000 docs < 300초
- [ ] 보안 스캔: secrets, SQL injection 확인
- [ ] 데이터베이스 마이그레이션 테스트
- [ ] RLS 정책 검증
- [ ] API 명세 검증 (OpenAPI)
- [ ] 운영 가이드 작성
- [ ] 팀 교육 완료

---

**작성일**: 2026-04-20  
**상태**: READY FOR IMPLEMENTATION ✅
