# scheduler-integration Design

**Version:** 1.0
**Date:** 2026-03-30
**Status:** Retroactive Design (Act Phase — post-implementation)
**Feature:** 인트라넷 문서 월간 배치 마이그레이션 스케줄러 통합
**PDCA Phase:** Design (retroactive, inferred from implementation + gap analysis)

---

## 1. 개요

인트라넷 KB 문서를 매월 자동으로 Supabase로 마이그레이션하기 위한 배치 스케줄러 통합.
관리자(admin/executive)가 수동 트리거 및 스케줄 관리를 할 수 있는 REST API 제공.

---

## 2. 아키텍처 결정

### 2.1 단일 스케줄러 패턴 (통합 결정)

**결정:** `app/scheduler.py` (별도 APScheduler 인스턴스) 제거.
`app/services/scheduled_monitor.py`의 `setup_scheduler()` 안에 월간 마이그레이션 잡 통합.

**근거:**
- FastAPI 앱에 APScheduler 인스턴스는 1개만 유지 (리소스 낭비 방지, 유지보수 단순화)
- 기존 `scheduled_monitor.py`는 이미 KST 타임존 설정 + 4개 잡 운영 중
- 중복 인스턴스는 레이스 컨디션 위험 (동일 도메인의 두 잡이 동시 실행 가능)
- `app/scheduler.py`는 UTC 기본값 사용 → 앱 전체 KST 컨벤션 위반

**대안 검토:**
- Celery: 인프라 복잡도 증가 (Redis/RabbitMQ 추가 필요) → 현재 단계 과도
- 별도 APScheduler 유지: 두 인스턴스 → H-1 갭 유지 → 기각
- Cron (OS): 배포 환경(Railway/Render)에서 관리 불편 → 기각

### 2.2 타임존: Asia/Seoul (KST)

모든 스케줄 잡은 KST 기준. 배치 실행 시각: **매월 1일 00:00 KST**.

### 2.3 APScheduler 선택 이유

- 기존 `scheduled_monitor.py`에서 이미 사용 중
- FastAPI 비동기 루프와 자연스러운 통합 (AsyncIOScheduler)
- 별도 워커/브로커 불필요 (소규모 팀 운영 맞춤)

---

## 3. DB 스키마

### migration_batches

```sql
CREATE TABLE migration_batches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    batch_name VARCHAR(200) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending|processing|completed|failed|partial_failed
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    scheduled_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_documents INTEGER NOT NULL DEFAULT 0,
    processed_documents INTEGER NOT NULL DEFAULT 0,
    failed_documents INTEGER NOT NULL DEFAULT 0,
    skipped_documents INTEGER NOT NULL DEFAULT 0,
    batch_type VARCHAR(50) NOT NULL DEFAULT 'monthly',  -- monthly|manual|incremental
    source_system VARCHAR(100) NOT NULL DEFAULT 'intranet',
    error_message TEXT,
    error_details JSONB,
    created_by UUID REFERENCES users(id),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### migration_schedule

```sql
CREATE TABLE migration_schedule (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    enabled BOOLEAN NOT NULL DEFAULT true,
    cron_expression VARCHAR(100) NOT NULL DEFAULT '0 0 1 * *',
    schedule_name VARCHAR(200) NOT NULL,
    schedule_type VARCHAR(50) NOT NULL DEFAULT 'monthly',
    next_run_at TIMESTAMPTZ,
    last_run_at TIMESTAMPTZ,
    last_batch_id UUID REFERENCES migration_batches(id),
    timeout_seconds INTEGER NOT NULL DEFAULT 3600,
    max_retries INTEGER NOT NULL DEFAULT 3,
    retry_delay_seconds INTEGER NOT NULL DEFAULT 300,
    notify_on_success BOOLEAN NOT NULL DEFAULT false,
    notify_on_failure BOOLEAN NOT NULL DEFAULT true,
    notification_channels VARCHAR[] NOT NULL DEFAULT ARRAY['teams'],
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_by UUID REFERENCES users(id)
);
```

---

## 4. API 스펙

### 기본 경로

`/api/migrations`

### 엔드포인트

| Method | Path | Auth | 설명 |
|--------|------|------|------|
| POST | `/trigger` | admin, executive | 배치 즉시 시작 (202 Accepted) |
| GET | `/batches` | 로그인 사용자 | 배치 목록 조회 |
| GET | `/batches/{batch_id}` | 로그인 사용자 | 배치 상세 조회 |
| GET | `/schedule` | admin, executive | 스케줄 설정 조회 |
| PUT | `/schedule/{schedule_id}` | admin, executive | 스케줄 설정 업데이트 |

### 인증 방식

- `require_role("admin", "executive")` dependency 사용 (inline 체크 금지)
- `get_current_user` dependency (JWT 검증)

### 에러 코드

| 상황 | 에러 클래스 | HTTP |
|------|------------|------|
| 권한 부족 | `AuthInsufficientRoleError` | 403 |
| 리소스 없음 | `ResourceNotFoundError` | 404 |
| 내부 오류 | `InternalServiceError` | 500 |

---

## 5. 서비스 레이어 설계

### MigrationService (app/services/migration_service.py)

**핵심 메서드:**

| 메서드 | DB 작업 | 설명 |
|--------|---------|------|
| `create_batch_record()` | INSERT migration_batches | 배치 시작 레코드 생성 |
| `update_batch_progress()` | UPDATE migration_batches | 진행 상황 업데이트 |
| `complete_batch()` | UPDATE migration_batches | 완료 처리 |
| `get_batch()` | SELECT single | 단건 조회 |
| `get_batch_history()` | SELECT with filter/sort/page | 목록 조회 |
| `get_schedule()` | SELECT single | 스케줄 조회 |
| `update_schedule()` | UPDATE migration_schedule | 스케줄 업데이트 |
| `detect_changed_documents()` | SELECT intranet_projects | 변경 문서 감지 |
| `_get_failed_documents()` | SELECT migration_batches | 실패 문서 재조회 |
| `_calculate_next_run()` | croniter | 다음 실행 시간 계산 |

**Supabase 패턴:**
```python
result = await self.db.table("migration_batches").select("*").eq("id", str(batch_id)).maybe_single().execute()
```

### run_scheduled_migration (scheduled_monitor.py)

스케줄러 잡 함수. `MigrationService.batch_import_intranet_documents()` 호출.
에러 발생 시 로깅 후 조용히 종료 (스케줄러 루프 보호).

---

## 6. 문서 처리 흐름

```
run_scheduled_migration()
  └── MigrationService.batch_import_intranet_documents()
        ├── create_batch_record()          → INSERT
        ├── detect_changed_documents()     → SELECT intranet_projects
        ├── update_batch_progress()        → UPDATE (total)
        ├── process_batch_documents()
        │     └── _process_single_document() × N (async, max_parallel=5)
        │           └── [document_ingestion 연동 예정]
        ├── complete_batch()               → UPDATE (status, completed_at)
        └── notification (옵션)
```

---

## 7. 에러 처리 전략

| 레이어 | 에러 유형 | 처리 |
|--------|-----------|------|
| 스케줄러 잡 | 모든 예외 | 로깅 후 조용히 종료 (스케줄러 루프 유지) |
| 서비스 | DB 저장 실패 | 인메모리 객체로 폴백 (배치 처리 계속 진행) |
| 서비스 | 문서 처리 실패 | 개별 에러 격리 + 지수 백오프 재시도 (3회) |
| API | TenopAPIError | 표준 에러 코드 응답 |
| API | 기타 예외 | InternalServiceError(GEN_005) |

---

## 8. 관련 파일

| 파일 | 역할 |
|------|------|
| `app/services/scheduled_monitor.py` | 통합 스케줄러 (run_scheduled_migration 포함) |
| `app/services/migration_service.py` | 배치 오케스트레이션 서비스 |
| `app/api/routes_migrations.py` | REST API 엔드포인트 |
| `app/models/migration_schemas.py` | Pydantic 스키마 |
| `app/jobs/migration_jobs.py` | 레거시 (scheduled_monitor.py로 통합됨) |
| `database/migrations/016_scheduler_integration.sql` | DB 스키마 |

---

## 9. 갭 분석 연계

- **H-1 (Duplicate Scheduler):** 단일 스케줄러 패턴으로 통합 (§2.1)
- **H-3 (DB Stubs):** 실제 Supabase 쿼리로 구현 (§5)
- **H-5 (Timezone):** KST 통일 (§2.2)
- **M-1 (HTTPException):** TenopAPIError 사용 (§4)
- **M-2 (MigrationScheduleUpdate):** Request body 스키마 사용 (§4)
- **M-3 (RBAC):** require_role dependency 사용 (§4)
- **M-4 (response_model):** 모든 엔드포인트 response_model 명시 (§4)

---

**참고 문서:**
- `docs/archive/2026-03/intranet-kb-migration/intranet-kb-migration.plan.md` (v2.0)
- `docs/03-analysis/features/scheduler-integration.analysis.md`
