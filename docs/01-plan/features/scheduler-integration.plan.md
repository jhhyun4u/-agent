# 정기적 문서 마이그레이션 스케줄러 통합 계획 (Plan)

**버전**: v1.0
**작성일**: 2026-03-30
**상태**: DRAFT

---

## 1. 개요

**목표**: 인트라넷 문서를 Supabase로 **정기적으로 자동 마이그레이션**하기 위한 스케줄러 통합

**핵심 가치**:
- 매달 1회 인트라넷 신규 문서 자동 수집
- 수동 작업 제거 (완전 자동화)
- 실시간 KB 최신화로 제안 품질 향상

---

## 2. 요구사항

### 2.1 기본 요구사항

| 요구사항 | 설명 | 우선도 |
|---------|------|--------|
| **정기 스케줄링** | APScheduler 또는 cron으로 매달 1회 자동 실행 | 높음 |
| **문서 수집** | 인트라넷에서 신규/수정된 문서만 선택적 수집 | 높음 |
| **처리 파이프라인** | 기존 document_ingestion.py 재사용 | 높음 |
| **상태 추적** | 배치 작업 로그 및 성공/실패 기록 | 높음 |
| **에러 처리** | 부분 실패 시 자동 재시도 + 관리자 알림 | 중간 |
| **수동 트리거** | API로 즉시 마이그레이션 시작 가능 | 중간 |
| **모니터링** | 배치 실행 히스토리 + 대시보드 표시 | 중간 |

### 2.2 데이터 범위

**입력:**
- 인트라넷 문서 소스 (API 또는 파일 시스템)
- 마지막 마이그레이션 이후 신규/수정 파일

**출력:**
- `document_chunks` 테이블: 청크 데이터 + 임베딩 (추가)
- `migration_batches` 테이블: 배치 작업 로그 (신규)
- `migration_schedule` 테이블: 스케줄 설정 (신규)

---

## 3. 현황 분석

### 3.1 기존 구현

**파일**: `app/services/document_ingestion.py` (359줄)

**구현 내용:**
- ✅ `process_document()` — 단일 문서 처리
- ✅ `import_project()` — 프로젝트 메타 임포트
- ✅ API 엔드포인트 5개 (upload, list, get, process, chunks)

**미구현 부분:**
- ❌ APScheduler 통합 (스케줄러 설정)
- ❌ 인트라넷 배치 수집 API
- ❌ 마이그레이션 배치 로그 테이블
- ❌ 변경 감지 로직 (신규/수정만 수집)
- ❌ 배치 모니터링 대시보드

### 3.2 의존성

**내부 모듈:**
- `app/services/document_ingestion.py` — 문서 처리
- `app/services/document_chunker.py` — 청킹 로직
- `database/schema` — document_chunks 테이블

**외부 라이브러리:**
- APScheduler (스케줄링)
- Supabase (저장소 + DB)

---

## 4. 제안된 솔루션

### 4.1 아키텍처

```
┌─────────────────────────────────────────────┐
│ APScheduler (Cron: 매달 1일 00:00)          │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│ Migration Service (신규)                    │
├─────────────────────────────────────────────┤
│ - batch_import_intranet_documents()         │
│ - detect_changed_files()                    │
│ - track_migration_history()                 │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│ Document Ingestion Service (기존)           │
├─────────────────────────────────────────────┤
│ - process_document()                        │
│ - import_project()                          │
└────────────────┬────────────────────────────┘
                 │
                 ↓
┌─────────────────────────────────────────────┐
│ Database + Storage                          │
├─────────────────────────────────────────────┤
│ - document_chunks (추가)                    │
│ - migration_batches (신규)                  │
│ - migration_schedule (신규)                 │
└─────────────────────────────────────────────┘
```

### 4.2 핵심 컴포넌트

**1. MigrationService (신규)**
```python
class MigrationService:
    async def batch_import_intranet_documents():
        # 1. 인트라넷에서 신규/수정 문서 감지
        # 2. 배치 로그 생성
        # 3. document_ingestion.process_document() 호출
        # 4. 배치 완료 로그 저장
        # 5. 실패 시 알림 발송
```

**2. APScheduler 통합**
```python
# main.py 또는 scheduler.py
scheduler = AsyncIOScheduler()
scheduler.add_job(
    migration_service.batch_import_intranet_documents,
    'cron',
    day_of_month=1,  # 매달 1일
    hour=0,
    minute=0
)
scheduler.start()
```

**3. API 엔드포인트 (신규)**
- `GET /api/migrations/batches` — 배치 히스토리 조회
- `POST /api/migrations/trigger` — 즉시 마이그레이션 트리거
- `GET /api/migrations/schedule` — 현재 스케줄 조회

**4. 데이터베이스 테이블 (신규)**
```sql
-- migration_batches: 배치 작업 기록
CREATE TABLE migration_batches (
    id UUID PRIMARY KEY,
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    status VARCHAR (processing|completed|failed),
    total_docs INT,
    processed_docs INT,
    error_count INT,
    error_details JSONB,
    created_by UUID
);

-- migration_schedule: 스케줄 설정
CREATE TABLE migration_schedule (
    id UUID PRIMARY KEY,
    enabled BOOLEAN,
    cron_expression VARCHAR DEFAULT '0 0 1 * *',  -- 매달 1일 00:00
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ
);
```

---

## 5. 구현 순서

### Phase 0: 설계 검토 (1일)
- [ ] 스케줄 전략 확정 (cron vs APScheduler vs Lambda)
- [ ] 변경 감지 방식 선정
- [ ] 에러 재시도 전략 수립

### Phase 1: 데이터베이스 마이그레이션 (1일)
- [ ] `migration_batches` 테이블 생성
- [ ] `migration_schedule` 테이블 생성
- [ ] 인덱스 생성

### Phase 2: MigrationService 구현 (2-3일)
- [ ] `batch_import_intranet_documents()` 구현
- [ ] 변경 감지 로직 구현
- [ ] 에러 처리 + 재시도 로직
- [ ] 로깅 + 모니터링

### Phase 3: APScheduler 통합 (1day)
- [ ] `main.py`에 스케줄러 초기화
- [ ] 크론 표현식 설정 (매달 1일 00:00)
- [ ] Graceful shutdown 처리

### Phase 4: API 엔드포인트 (1day)
- [ ] GET /api/migrations/batches
- [ ] POST /api/migrations/trigger
- [ ] GET /api/migrations/schedule

### Phase 5: 모니터링 + 테스트 (1-2day)
- [ ] 배치 대시보드 UI (선택)
- [ ] E2E 테스트
- [ ] 성능 벤치마크

---

## 6. 예상 일정

| 단계 | 기간 | 마일스톤 |
|------|------|---------|
| 설계 | 1일 | Plan → Design 완료 |
| DB + Service | 3-4일 | MigrationService 구현 |
| Scheduler + API | 2일 | APScheduler 통합 |
| 테스트 + 배포 | 2일 | 스테이징 검증 |
| **총 기간** | **8-9일** | **프로덕션 준비** |

---

## 7. 리스크 및 완화 방안

| 리스크 | 완화 방안 |
|--------|---------|
| 인트라넷 API 불안정 | Retry + Fallback 로직, 실패 알림 |
| 배치 중 DB 연결 끊김 | 트랜잭션 + Checkpoint (재시작 가능) |
| 대용량 문서 처리 오버헤드 | 배치 크기 제한 (예: 100개/배치) |
| 스케줄 놓침 | 수동 트리거 API + 체크 로직 |

---

## 8. 성공 기준

✅ **Go Live 체크리스트**
- [ ] 매달 1일 00:00 자동 실행 확인
- [ ] 배치 로그 테이블 기록 확인
- [ ] 실패 시 관리자 알림 발송 확인
- [ ] API 3개 엔드포인트 모두 정상 작동
- [ ] E2E 테스트 통과 (95% 이상)
- [ ] 성능: 1시간 내 처리 완료

---

## 9. 다음 단계

→ **`/pdca design scheduler-integration`** 로 설계 문서 작성 시작

---

## 참고: 기존 시스템

**document_ingestion.py 재사용:**
- 단일 문서 처리 함수 있음
- 테스트 완료 (95% match rate)
- 프로덕션 준비됨

**이번 작업의 가치:**
- 수동 작업 완전 제거
- 매달 자동 신규 문서 수집
- KB 최신화로 제안 품질 향상
