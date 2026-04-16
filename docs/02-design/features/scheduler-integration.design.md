# 정기적 문서 마이그레이션 스케줄러 통합 설계 (Design)

**버전**: v1.0
**작성일**: 2026-03-30
**상태**: DESIGN
**참고**: Plan v1.0 기반

---

## 1. 아키텍처 설계

### 1.1 전체 시스템 흐름

```
┌──────────────────────────────────────────────────────────┐
│                    APScheduler (v3.10+)                  │
│          CronTrigger: "0 0 1 * *" (매달 1일 00:00)        │
└─────────────────────────┬────────────────────────────────┘
                          │
                          ↓
┌──────────────────────────────────────────────────────────┐
│               FastAPI Application (main.py)              │
├──────────────────────────────────────────────────────────┤
│  - BackgroundScheduler 초기화                             │
│  - Lifespan events (startup/shutdown)                    │
│  - Job callbacks (error handling)                        │
└─────────────────────────┬────────────────────────────────┘
                          │
        ┌─────────────────┴──────────────────┐
        │                                    │
        ↓                                    ↓
┌─────────────────────────────┐  ┌──────────────────────────┐
│   MigrationService           │  │  API Layer               │
│  (app/services/)             │  │  (routes_migrations.py)  │
├─────────────────────────────┤  ├──────────────────────────┤
│ batch_import_documents()     │  │ GET /migrations/batches  │
│ ├─ get_changed_documents()   │  │ POST /migrations/trigger │
│ ├─ create_batch_record()     │  │ GET /migrations/schedule │
│ ├─ process_batch()           │  │ GET /migrations/{id}     │
│ ├─ update_batch_status()     │  │ PUT /migrations/{id}/     │
│ └─ notify_on_error()         │  │     restart              │
└─────────────────────────────┘  └──────────────────────────┘
        │
        ↓
┌─────────────────────────────┐
│ Document Ingestion Service  │
│  (app/services/)            │
├─────────────────────────────┤
│ process_document()          │
│ extract_text()              │
│ chunk_document()            │
│ embed_chunks()              │
└─────────────────────────────┘
        │
        ↓
┌──────────────────────────────┐
│   Database (Supabase)        │
├──────────────────────────────┤
│ - migration_batches          │
│ - migration_schedule         │
│ - document_chunks (기존)     │
│ - documents (기존)           │
└──────────────────────────────┘
```

### 1.2 컴포넌트 상세 역할

| 컴포넌트 | 책임 | 파일 |
|---------|------|------|
| **APScheduler** | 크론 트리거, 작업 스케줄링 | `app/scheduler.py` (신규) |
| **MigrationService** | 배치 처리 오케스트레이션 | `app/services/migration_service.py` (신규) |
| **DocIngestionService** | 문서 처리 (기존 함수 재사용) | `app/services/document_ingestion.py` (수정) |
| **API Layer** | REST 엔드포인트 + 스키마 | `app/api/routes_migrations.py` (신규) |
| **DB Schema** | 배치 로그, 스케줄 설정 | `database/migrations/` (신규) |
| **Notification** | 에러/완료 알림 | `app/services/notification_service.py` (기존 확장) |

---

## 2. 데이터베이스 설계

### 2.1 신규 테이블: migration_batches

**목적**: 각 배치 작업 실행 기록 추적

```sql
CREATE TABLE migration_batches (
    -- 기본 정보
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_name VARCHAR(255) NOT NULL,  -- e.g., "2026-03-01_monthly"

    -- 상태
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- Values: pending → processing → completed | failed | partial_failed

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
    batch_type VARCHAR(50) NOT NULL DEFAULT 'monthly',  -- monthly | manual | incremental

    -- 에러 정보
    error_message TEXT,
    error_details JSONB,  -- {failed_docs: [{file, error}], warnings: [...]}

    -- 메타데이터
    created_by UUID NOT NULL REFERENCES users(id),
    updated_at TIMESTAMPTZ DEFAULT now(),

    -- 인덱스
    CONSTRAINT status_valid CHECK (status IN ('pending', 'processing', 'completed', 'failed', 'partial_failed')),
    INDEX idx_migration_batches_status (status),
    INDEX idx_migration_batches_scheduled (scheduled_at),
    INDEX idx_migration_batches_created_by (created_by)
);
```

### 2.2 신규 테이블: migration_schedule

**목적**: 스케줄 설정 및 다음 실행 예정시간 저장

```sql
CREATE TABLE migration_schedule (
    -- 기본 정보
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- 스케줄 설정
    enabled BOOLEAN NOT NULL DEFAULT true,
    cron_expression VARCHAR(100) NOT NULL DEFAULT '0 0 1 * *',  -- 매달 1일 00:00
    schedule_name VARCHAR(255) NOT NULL DEFAULT 'monthly_intranet_migration',
    schedule_type VARCHAR(50) NOT NULL DEFAULT 'cron',  -- cron | once | interval

    -- 실행 예정
    next_run_at TIMESTAMPTZ,
    last_run_at TIMESTAMPTZ,
    last_batch_id UUID REFERENCES migration_batches(id),

    -- 설정
    timeout_seconds INT DEFAULT 3600,  -- 1시간
    max_retries INT DEFAULT 3,
    retry_delay_seconds INT DEFAULT 300,  -- 5분

    -- 알림 설정
    notify_on_success BOOLEAN DEFAULT false,
    notify_on_failure BOOLEAN DEFAULT true,
    notification_channels JSONB DEFAULT '["email", "teams"]'::jsonb,

    -- 메타데이터
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    updated_by UUID REFERENCES users(id),

    INDEX idx_migration_schedule_enabled (enabled),
    INDEX idx_migration_schedule_next_run (next_run_at)
);
```

### 2.3 기존 테이블 확장

**document_chunks 테이블에 추가 컬럼** (선택사항):
```sql
ALTER TABLE document_chunks ADD COLUMN IF NOT EXISTS
    migration_batch_id UUID REFERENCES migration_batches(id);

CREATE INDEX idx_document_chunks_migration_batch
ON document_chunks(migration_batch_id);
```

---

## 3. API 설계

### 3.1 배치 작업 조회: GET /api/migrations/batches

**엔드포인트**: `GET /api/migrations/batches`

**쿼리 파라미터**:
```python
class BatchListParams(BaseModel):
    status: Optional[str] = None  # pending|processing|completed|failed
    limit: int = 20
    offset: int = 0
    sort_by: str = "scheduled_at"  # scheduled_at|started_at|created_by
    order: str = "desc"  # asc|desc
```

**응답** (200 OK):
```json
{
  "total": 42,
  "limit": 20,
  "offset": 0,
  "batches": [
    {
      "id": "uuid-1",
      "batch_name": "2026-03-01_monthly",
      "status": "completed",
      "started_at": "2026-03-01T00:00:00Z",
      "completed_at": "2026-03-01T01:23:45Z",
      "total_documents": 156,
      "processed_documents": 156,
      "failed_documents": 0,
      "skipped_documents": 0,
      "batch_type": "monthly",
      "created_by": "user-uuid",
      "duration_minutes": 83
    }
  ]
}
```

**에러** (400, 401, 500):
```json
{
  "detail": "Unauthorized",
  "error_code": "AUTH_001"
}
```

---

### 3.2 즉시 배치 시작: POST /api/migrations/trigger

**엔드포인트**: `POST /api/migrations/trigger`

**요청 본문**:
```python
class MigrationTriggerRequest(BaseModel):
    batch_type: str = "manual"  # manual | incremental
    include_failed_docs: bool = False  # 이전 실패 문서 재처리
    document_limit: Optional[int] = None  # 최대 처리 문서 수
```

**응답** (202 Accepted):
```json
{
  "batch_id": "uuid-xxx",
  "batch_name": "2026-03-30T14:30:00_manual",
  "status": "pending",
  "scheduled_at": "2026-03-30T14:30:00Z",
  "estimated_duration_minutes": 45
}
```

**백그라운드 처리**:
- 즉시 배치 레코드 생성 (status: pending)
- 백그라운드 태스크 시작 (MigrationService.batch_import_documents)
- 클라이언트는 polling 또는 WebSocket으로 상태 확인

---

### 3.3 스케줄 설정 조회: GET /api/migrations/schedule

**엔드포인트**: `GET /api/migrations/schedule`

**응답** (200 OK):
```json
{
  "id": "schedule-uuid",
  "enabled": true,
  "cron_expression": "0 0 1 * *",
  "schedule_name": "monthly_intranet_migration",
  "next_run_at": "2026-04-01T00:00:00Z",
  "last_run_at": "2026-03-01T00:15:23Z",
  "last_batch_id": "batch-uuid-xxx",
  "timeout_seconds": 3600,
  "max_retries": 3,
  "retry_delay_seconds": 300,
  "notify_on_success": false,
  "notify_on_failure": true,
  "notification_channels": ["email", "teams"]
}
```

---

### 3.4 스케줄 업데이트: PUT /api/migrations/schedule

**엔드포인트**: `PUT /api/migrations/schedule/{id}`

**요청 본문**:
```python
class MigrationScheduleUpdate(BaseModel):
    enabled: Optional[bool] = None
    cron_expression: Optional[str] = None
    timeout_seconds: Optional[int] = None
    max_retries: Optional[int] = None
    notify_on_success: Optional[bool] = None
    notify_on_failure: Optional[bool] = None
```

**응답** (200 OK): 업데이트된 schedule 객체

---

### 3.5 배치 상세 조회: GET /api/migrations/{batch_id}

**응답** (200 OK):
```json
{
  "id": "batch-uuid",
  "batch_name": "2026-03-01_monthly",
  "status": "partial_failed",
  "started_at": "2026-03-01T00:00:00Z",
  "completed_at": "2026-03-01T01:23:45Z",
  "total_documents": 156,
  "processed_documents": 154,
  "failed_documents": 2,
  "skipped_documents": 0,
  "error_details": {
    "failed_docs": [
      {
        "filename": "report_2026_03.pdf",
        "error": "Corrupted PDF file",
        "error_code": "DOC_001"
      }
    ],
    "warnings": [
      "1 file skipped due to size limit (>100MB)"
    ]
  },
  "batch_type": "monthly",
  "created_by": "user-uuid",
  "duration_minutes": 83
}
```

---

## 4. 서비스 구현 설계

### 4.1 MigrationService 클래스 구조

```python
# app/services/migration_service.py

class MigrationService:
    """배치 마이그레이션 오케스트레이션"""

    def __init__(self, db_client, doc_service, notification_service):
        self.db = db_client
        self.doc_service = doc_service  # DocumentIngestionService
        self.notification = notification_service

    # ===== 주요 메서드 =====

    async def batch_import_intranet_documents(
        self,
        batch_type: str = "monthly",
        include_failed: bool = False
    ) -> MigrationBatch:
        """
        인트라넷에서 신규/수정 문서 배치 임포트

        흐름:
        1. 배치 레코드 생성 (status: pending)
        2. 인트라넷 변경 문서 감지
        3. 각 문서 처리 (document_ingestion 재사용)
        4. 배치 완료 기록
        5. 에러 시 알림 발송
        """

    async def detect_changed_documents(
        self,
        since: datetime
    ) -> List[IntranetDocument]:
        """
        마지막 마이그레이션 이후 신규/수정 문서 감지

        전략:
        - 인트라넷 API로 modified_date > since인 문서 조회
        - 또는 파일 시스템 mtime 비교
        - 로컬 캐시와 비교 (변경 감지 최소화)
        """

    async def process_batch_documents(
        self,
        batch_id: UUID,
        documents: List[IntranetDocument],
        max_parallel: int = 5
    ) -> BatchResult:
        """
        배치 내 문서들을 병렬로 처리

        특징:
        - 동시 처리 제한 (max_parallel=5)
        - 개별 문서 에러 격리 (한 파일 실패 시 다음 진행)
        - 진행 상황 logging
        """

    async def _process_single_document(
        self,
        batch_id: UUID,
        doc: IntranetDocument,
        retry_count: int = 0
    ) -> DocumentProcessResult:
        """
        단일 문서 처리 (document_ingestion 재사용)

        1. document_ingestion.process_document() 호출
        2. migration_batch_id 업데이트
        3. 에러 시 재시도 로직
        """

    async def create_batch_record(
        self,
        batch_type: str,
        total_docs: int
    ) -> MigrationBatch:
        """배치 시작 레코드 생성"""

    async def update_batch_progress(
        self,
        batch_id: UUID,
        processed: int,
        failed: int = 0,
        errors: List[str] = None
    ) -> None:
        """배치 진행 상황 업데이트"""

    async def complete_batch(
        self,
        batch_id: UUID,
        status: str,
        error_details: dict = None
    ) -> None:
        """배치 완료 처리 및 알림"""

    async def get_batch_history(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str = None
    ) -> List[MigrationBatch]:
        """배치 히스토리 조회"""

    async def retry_failed_batch(
        self,
        batch_id: UUID
    ) -> MigrationBatch:
        """이전 실패 배치 재실행"""

    # ===== 스케줄 관리 =====

    async def get_schedule(self) -> MigrationSchedule:
        """현재 스케줄 설정 조회"""

    async def update_schedule(
        self,
        cron_expression: str = None,
        **kwargs
    ) -> MigrationSchedule:
        """스케줄 설정 업데이트"""

    # ===== 헬퍼 메서드 =====

    async def _notify_on_error(
        self,
        batch_id: UUID,
        error: Exception
    ) -> None:
        """에러 발생 시 관리자 알림"""

    async def _calculate_next_run(
        self,
        cron_expr: str
    ) -> datetime:
        """다음 실행 예정시간 계산"""
```

### 4.2 APScheduler 통합 (scheduler.py)

```python
# app/scheduler.py

class MigrationScheduler:
    """APScheduler를 이용한 스케줄 관리"""

    def __init__(self, migration_service, db_client):
        self.migration_service = migration_service
        self.db = db_client
        self.scheduler = None

    def initialize(self):
        """백그라운드 스케줄러 초기화"""
        self.scheduler = BackgroundScheduler()

        # 현재 DB에서 스케줄 설정 로드
        schedule = self.migration_service.get_schedule()

        if schedule.enabled:
            self.scheduler.add_job(
                self._scheduled_batch_import,
                'cron',
                id='migration_monthly',
                **self._parse_cron(schedule.cron_expression),
                misfire_grace_time=60,
                coalesce=True,
                max_instances=1
            )

        self.scheduler.start()

    async def _scheduled_batch_import(self):
        """스케줄된 배치 실행"""
        try:
            batch = await self.migration_service.batch_import_intranet_documents(
                batch_type="monthly"
            )
            logging.info(f"Scheduled migration completed: {batch.id}")
        except Exception as e:
            logging.error(f"Scheduled migration failed: {e}")
            # 에러 알림은 migration_service에서 처리

    def shutdown(self):
        """스케줄러 종료"""
        if self.scheduler:
            self.scheduler.shutdown()

    def _parse_cron(self, cron_expr: str) -> dict:
        """크론 표현식 → APScheduler 파라미터 변환"""
        # "0 0 1 * *" → {'hour': 0, 'minute': 0, 'day_of_month': 1}
```

---

## 5. 구현 체크리스트

### Phase 1: 데이터베이스 마이그레이션 (1일)

- [ ] `database/migrations/001_migration_tables.sql` 작성
  - [ ] migration_batches 테이블 + 인덱스
  - [ ] migration_schedule 테이블 + 인덱스
  - [ ] document_chunks.migration_batch_id 컬럼 추가
- [ ] Supabase 마이그레이션 실행 및 검증
- [ ] RLS 정책 설정 (migration_batches, migration_schedule)

### Phase 2: 스키마 + 서비스 (1-2일)

- [ ] `app/models/migration_schemas.py` 작성 (6개 Pydantic 모델)
  - [ ] MigrationBatch
  - [ ] MigrationSchedule
  - [ ] MigrationTriggerRequest
  - [ ] BatchListParams
  - [ ] MigrationScheduleUpdate
  - [ ] BatchResult
- [ ] `app/services/migration_service.py` 구현 (400-500줄)
  - [ ] batch_import_intranet_documents()
  - [ ] detect_changed_documents()
  - [ ] process_batch_documents()
  - [ ] _process_single_document()
  - [ ] CRUD 메서드들
- [ ] Unit 테스트: test_migration_service.py (10개 테스트)

### Phase 3: APScheduler 통합 (1일)

- [ ] `app/scheduler.py` 작성
  - [ ] BackgroundScheduler 초기화
  - [ ] 크론 파싱 로직
  - [ ] Graceful shutdown
- [ ] `app/main.py` 수정
  - [ ] Lifespan context manager에 scheduler 통합
  - [ ] startup: scheduler.initialize()
  - [ ] shutdown: scheduler.shutdown()
- [ ] requirements.txt 업데이트: `apscheduler>=3.10.0`

### Phase 4: API 엔드포인트 (1day)

- [ ] `app/api/routes_migrations.py` 구현 (250-300줄)
  - [ ] GET /api/migrations/batches (조회)
  - [ ] POST /api/migrations/trigger (즉시 시작)
  - [ ] GET /api/migrations/schedule (스케줄 조회)
  - [ ] PUT /api/migrations/schedule/{id} (업데이트)
  - [ ] GET /api/migrations/{batch_id} (상세 조회)
- [ ] 스키마 검증 및 에러 처리
- [ ] 인증 + 권한 확인 (requires_role, require_project_access)
- [ ] Integration 테스트: test_routes_migrations.py (8개 테스트)

### Phase 5: 모니터링 + 테스트 (1-2day)

- [ ] 배치 로깅 강화
  - [ ] 구조화된 로깅 (JSON 형식)
  - [ ] 진행 상황 타임스탬프
- [ ] E2E 테스트 작성
  - [ ] 매달 스케줄 자동 실행
  - [ ] 수동 트리거
  - [ ] 실패 재시도
- [ ] 성능 벤치마크
  - [ ] 1000개 문서 처리 시간 < 1시간
  - [ ] 메모리 사용량 < 500MB
- [ ] 모니터링 대시보드 (선택사항)
  - [ ] 배치 히스토리 차트
  - [ ] 성공률 통계

---

## 6. 에러 처리 및 복구 전략

### 6.1 에러 분류

| 에러 타입 | 원인 | 처리 방식 |
|----------|------|---------|
| **INTRANET_001** | 인트라넷 API 연결 실패 | 재시도 (최대 3회), 이후 경고 |
| **DOC_001** | 손상된 문서 파일 | 스킵, failed_docs에 기록 |
| **CHUNK_001** | 청킹 실패 | 재시도, 실패 시 스킵 |
| **EMBED_001** | 임베딩 API 오류 | 재시도 (Exponential backoff) |
| **DB_001** | DB 연결 끊김 | 트랜잭션 롤백, 배치 중단, 수동 복구 |

### 6.2 재시도 전략

```python
# app/utils/retry.py

async def exponential_backoff_retry(
    func,
    max_retries: int = 3,
    base_delay: int = 5,
    max_delay: int = 300
):
    """
    지수 백오프 재시도

    지연: 5s, 10s, 20s, ... (최대 300s)
    """
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = min(base_delay * (2 ** attempt), max_delay)
            logging.warning(f"Retry attempt {attempt+1} after {delay}s: {e}")
            await asyncio.sleep(delay)
```

### 6.3 배치 복구

```python
# 부분 실패 후 복구
batch = await migration_service.get_batch(batch_id)
if batch.status == "partial_failed":
    # 실패한 문서만 재처리
    retry_batch = await migration_service.retry_failed_batch(batch_id)
```

---

## 7. 성능 고려사항

### 7.1 병렬 처리 제한

```python
max_parallel_documents = 5  # 동시 처리 문서 수
max_parallel_chunks = 20    # 청킹 병렬도
```

**이유**: Supabase 연결 풀 초과 방지, Claude API 속도 제한

### 7.2 배치 크기 최적화

```python
# 한 번에 처리할 최대 문서 수
BATCH_SIZE_LIMIT = 500  # 매달 500개 문서 기준

# 청크 단위 정렬로 순차 처리
CHUNK_BATCH_SIZE = 100
```

### 7.3 타임아웃 설정

```python
timeout_total = 3600  # 전체 배치: 1시간
timeout_document = 300  # 문서당: 5분
timeout_chunk = 30     # 청크당: 30초
```

---

## 8. 보안 고려사항

### 8.1 인증 + 권한

- `POST /api/migrations/trigger`: 프로젝트 관리자 이상 필요
- `GET /api/migrations/*`: 프로젝트 멤버 이상 필요
- `PUT /api/migrations/schedule`: 시스템 관리자만 가능

### 8.2 감사 로깅

```python
# 모든 배치 작업 기록
audit_log(
    action="migration_started",
    user_id=current_user.id,
    batch_id=batch.id,
    details={"batch_type": "monthly", ...}
)
```

### 8.3 데이터 격리 (RLS)

```sql
-- migration_batches RLS 정책
CREATE POLICY migration_batches_select
ON migration_batches
FOR SELECT
USING (auth.uid() IN (
    SELECT user_id FROM project_members
    WHERE project_id = ...
));
```

---

## 9. 테스트 전략

### 9.1 단위 테스트 (10개)

```python
# test_migration_service.py
- test_detect_changed_documents_success
- test_detect_changed_documents_no_changes
- test_process_batch_partial_failure
- test_batch_record_creation
- test_exponential_backoff_retry
- test_update_batch_progress
- test_get_batch_history_with_filters
- test_schedule_crud
- test_next_run_calculation
- test_error_notification
```

### 9.2 통합 테스트 (8개)

```python
# test_routes_migrations.py
- test_trigger_migration_201
- test_batch_list_pagination
- test_get_schedule_200
- test_update_schedule_200
- test_get_batch_detail_200
- test_trigger_without_auth_401
- test_concurrent_triggers_single_job
- test_batch_timeout_handling
```

### 9.3 E2E 테스트 (5개)

```python
# test_e2e_scheduler.py
- test_monthly_cron_execution
- test_manual_trigger_flow
- test_failed_batch_retry_flow
- test_scheduler_graceful_shutdown
- test_notification_on_completion
```

---

## 10. 배포 순서

### 단계별 배포

**1단계**: 데이터베이스 마이그레이션 (무중단)
```bash
supabase migration up --version 001_migration_tables
```

**2단계**: 서비스 + API 배포
```bash
# 기존 document_ingestion과 호환성 유지
# APScheduler는 초기에 disabled 상태로 배포
```

**3단계**: APScheduler 활성화
```bash
# migration_schedule.enabled = true로 변경
# 다음 월 1일부터 자동 실행
```

---

## 11. 모니터링 + 대시보드 (선택사항)

### 11.1 메트릭

```python
migration_batch_duration_seconds  # 배치 처리 시간
migration_documents_processed_total  # 누적 처리 문서 수
migration_failure_rate  # 실패율
migration_schedule_delay_seconds  # 스케줄 지연
```

### 11.2 대시보드 (선택사항)

```
[배치 히스토리 차트]
- 월별 문서 수
- 월별 성공률
- 평균 처리 시간

[최근 배치 상태]
- 최근 10개 배치 목록
- 진행 상황 바
- 에러 요약
```

---

## 12. 롤백 계획

### 배포 실패 시

1. **APScheduler 비활성화**
   ```sql
   UPDATE migration_schedule SET enabled = false;
   ```

2. **DB 마이그레이션 롤백** (필요 시)
   ```bash
   supabase migration down --version 001_migration_tables
   ```

3. **기존 document_ingestion API 유지**
   - 마이그레이션 없이도 수동 호출 가능

---

## 13. 향후 확장 (Low Priority)

- [ ] Celery 분산 처리 (수천 개 문서)
- [ ] 증분 동기화 (diff 기반)
- [ ] 변경 이력 추적 (audit trail)
- [ ] 자동 재시도 스케줄링
- [ ] 여러 소스 지원 (SharePoint, 드라이브 등)

---

## 14. 구현 순서 요약

| 순서 | 작업 | 기간 | 종료 기준 |
|------|------|------|---------|
| 1 | DB 마이그레이션 | 1일 | Supabase 테이블 생성 |
| 2 | MigrationService | 1-2일 | Unit 테스트 통과 |
| 3 | APScheduler 통합 | 1일 | Startup 로그 확인 |
| 4 | API 엔드포인트 | 1일 | Integration 테스트 통과 |
| 5 | E2E 테스트 | 1-2일 | 스테이징 검증 완료 |
| **총 기간** | **5-7일** | - | **프로덕션 준비** |

---

## 참고: 기존 시스템과의 통합

### DocumentIngestionService 재사용

기존 `process_document()` 함수 변경 없음:
```python
# 기존 코드
result = await doc_service.process_document(
    file_path=file_path,
    project_id=project_id
)

# migration_service에서 호출
batch_id = batch.id
result = await doc_service.process_document(
    file_path=file_path,
    project_id=project_id,
    batch_id=batch_id  # 추가 파라미터 (선택)
)
```

### NotificationService 확장

기존 알림 시스템 활용:
```python
await notification_service.send_notification(
    channel="teams",
    title="Monthly Migration Failed",
    details={"batch_id": batch.id, "error": error}
)
```

---

## 다음 단계

→ **`/pdca do scheduler-integration`** 으로 구현 시작
