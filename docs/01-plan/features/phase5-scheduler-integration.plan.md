# Phase 5: Scheduler Integration - 구현 계획

**버전**: v2.0 (실행 계획)  
**작성일**: 2026-04-20  
**상태**: READY FOR IMPLEMENTATION  
**목표 완료**: 2026-05-04 (14일)

---

## 1. 개요 & 비즈니스 가치

### 목표
인트라넷 문서를 **매달 자동으로 마이그레이션**하여 KB를 최신 상태로 유지하고, 제안 품질을 향상

### 비즈니스 임팩트
| 메트릭 | 현재 | 목표 | 임팩트 |
|--------|------|------|--------|
| KB 최신화 주기 | 수동 (불규칙) | 자동 (월 1회) | ⬇️ 25% 시간 절감 |
| 제안 품질 | 기존 데이터 의존 | 최신 실적 포함 | ⬆️ 15% 정확도 향상 |
| 운영 부하 | 월 4시간 | 0시간 (자동) | ⬇️ 완전 자동화 |

---

## 2. 요구사항 (변경 없음)

### 2.1 기능 요구사항

| ID | 요구사항 | 설명 | 우선도 |
|----|---------|------|--------|
| R1 | 정기 스케줄링 | APScheduler로 매달 1회 자동 실행 | **높음** |
| R2 | 변경 감지 | 신규/수정 문서만 선택적 수집 | **높음** |
| R3 | 배치 처리 | 대량 문서 병렬 처리 (5개 스레드) | **높음** |
| R4 | 상태 추적 | 배치 로그 + 진행률 대시보드 | **높음** |
| R5 | 에러 처리 | 부분 실패 시 자동 재시도 (3회) | **중간** |
| R6 | 수동 트리거 | API로 즉시 마이그레이션 시작 | **중간** |
| R7 | 모니터링 | 배치 히스토리 + 성능 메트릭 | **중간** |
| R8 | 롤백 | 실패 시 이전 상태 복구 | **낮음** |

### 2.2 기술 요구사항
- Python 3.11+ 호환성
- Supabase 데이터베이스 스키마 확장
- 외부 의존성 최소화
- 에러 로깅 + 모니터링

---

## 3. 아키텍처 설계

### 3.1 시스템 구성

```
┌─────────────────────────────────────────────────────┐
│  APScheduler (매달 1일 자정)                        │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  Scheduler Service                                  │
│  - 변경 감지 (sync_since 기반)                      │
│  - 배치 큐 생성 (concurrent_batch_processor)        │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  Batch Processor (Thread Pool: 5 workers)           │
│  - 병렬 문서 처리                                   │
│  - 재시도 로직 (3회)                                │
│  - 진행률 추적                                      │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  Document Ingestion Pipeline                        │
│  - 문서 파싱 (process_document)                     │
│  - 청킹 + 임베딩                                    │
│  - DB 저장 (document_chunks)                        │
└────────┬────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────┐
│  Monitoring & Logging                               │
│  - migration_batches 테이블 기록                    │
│  - Slack 알림                                       │
│  - 성능 메트릭                                      │
└─────────────────────────────────────────────────────┘
```

### 3.2 DB 스키마 확장

**신규 테이블 3개:**

```sql
-- 1. 스케줄 설정
CREATE TABLE migration_schedules (
    id UUID PRIMARY KEY,
    name VARCHAR(100),
    cron_expression VARCHAR(50),  -- "0 0 1 * *" (매달 1일 자정)
    enabled BOOLEAN DEFAULT true,
    source_type VARCHAR(50),      -- "intranet", "sharepoint", etc.
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

-- 2. 배치 작업 로그
CREATE TABLE migration_batches (
    id UUID PRIMARY KEY,
    schedule_id UUID REFERENCES migration_schedules,
    status VARCHAR(20),           -- "pending", "running", "success", "partial", "failed"
    total_documents INT,
    processed_documents INT,
    failed_documents INT,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INT,
    created_at TIMESTAMP
);

-- 3. 문서별 마이그레이션 기록
CREATE TABLE migration_logs (
    id UUID PRIMARY KEY,
    batch_id UUID REFERENCES migration_batches,
    source_document_id VARCHAR(100),
    document_name VARCHAR(255),
    status VARCHAR(20),           -- "success", "failed", "skipped"
    error_message TEXT,
    retry_count INT DEFAULT 0,
    processed_at TIMESTAMP,
    created_at TIMESTAMP
);
```

---

## 4. 구현 계획 (4단계 PDCA)

### Phase 1: PLAN (2026-04-20 ~ 04-21) - 1일

**산출물:**
- ✅ 이 문서 (완료)
- [ ] 데이터베이스 마이그레이션 스크립트
- [ ] API 명세서 (수동 트리거 엔드포인트)
- [ ] 테스트 계획 (단위 + 통합)

**체크 포인트:**
- [ ] 요구사항 검증
- [ ] 아키텍처 동의
- [ ] 의존성 확인

---

### Phase 2: DESIGN (2026-04-21 ~ 04-23) - 3일

**모듈 설계:**

#### 2.1 `app/services/scheduler_service.py` (250줄)
```python
class SchedulerService:
    def __init__(self, db_client, intranet_client):
        self.scheduler = APScheduler()
        self.db = db_client
        
    async def add_schedule(self, name, cron, source_type):
        # migration_schedules에 기록
        pass
    
    async def start_scheduled_jobs(self):
        # 모든 활성 스케줄 시작
        pass
    
    async def trigger_migration_now(self, schedule_id):
        # 즉시 마이그레이션 시작
        pass
```

#### 2.2 `app/services/batch_processor.py` (300줄)
```python
class ConcurrentBatchProcessor:
    def __init__(self, num_workers=5, max_retries=3):
        self.executor = ThreadPoolExecutor(max_workers)
        self.max_retries = max_retries
        
    async def process_batch(self, documents):
        # 병렬 처리 + 재시도
        pass
    
    def _process_single_document(self, doc):
        # 개별 문서 처리
        pass
```

#### 2.3 Database Migrations
```sql
-- migration_001_add_scheduler_tables.sql
-- migration_002_add_rls_policies.sql
-- migration_003_add_indices.sql
```

#### 2.4 API Endpoints (`app/api/routes_migration.py`)
- `POST /api/migration/trigger/{schedule_id}` - 즉시 트리거
- `GET /api/migration/batches` - 배치 히스토리
- `GET /api/migration/batches/{batch_id}` - 배치 상세
- `POST /api/migration/schedules` - 스케줄 등록
- `GET /api/migration/schedules` - 스케줄 목록

**산출물:**
- ✅ 상세 설계 문서
- [ ] ERD (Entity Relationship Diagram)
- [ ] API 명세 (OpenAPI 3.0)
- [ ] 클래스 다이어그램

---

### Phase 3: DO (2026-04-23 ~ 04-29) - 7일

#### 3.1 데이터베이스 스키마 (2일)
- [ ] 마이그레이션 스크립트 작성
- [ ] RLS 정책 설정
- [ ] 인덱스 최적화
- [ ] 테스트 (DB 스키마)

#### 3.2 백엔드 구현 (4일)
- [ ] `scheduler_service.py` 구현
- [ ] `batch_processor.py` 구현
- [ ] 변경 감지 로직
- [ ] 에러 처리 + 재시도
- [ ] API 엔드포인트 구현
- [ ] 통합 테스트

#### 3.3 모니터링 & 로깅 (1일)
- [ ] 배치 진행률 추적
- [ ] Slack 알림 통합
- [ ] 성능 메트릭
- [ ] 헬스 체크

**산출물:**
- ✅ 완성된 코드 (~800줄)
- ✅ 24개 테스트 (단위 + 통합)
- ✅ 마이그레이션 스크립트

---

### Phase 4: CHECK (2026-04-29 ~ 05-02) - 4일

#### 4.1 품질 검증 (2일)
- [ ] 모든 24개 테스트 통과 (100%)
- [ ] 코드 커버리지 ≥ 80%
- [ ] 성능 테스트 (1000개 문서 처리)
- [ ] 보안 스캔 (secrets, injection)

#### 4.2 통합 테스트 (1일)
- [ ] E2E 배치 실행
- [ ] DB 마이그레이션 검증
- [ ] 롤백 절차 테스트
- [ ] 에러 시나리오

#### 4.3 배포 준비 (1일)
- [ ] 설계-코드 매칭 (≥ 90%)
- [ ] 성능 기준 충족
- [ ] 운영 문서 작성

**성공 기준:**
- ✅ 모든 테스트 통과
- ✅ 설계 일치도 ≥ 90%
- ✅ 성능: 1000 docs 처리 < 300초
- ✅ 배포 준비 완료

---

### Phase 5: ACT (2026-05-02 ~ 05-04) - 2일

#### 5.1 갭 분석 & 수정
- [ ] 설계-구현 갭 분석
- [ ] 발견된 이슈 수정
- [ ] 재 테스트

#### 5.2 문서화 & 배포 준비
- [ ] 운영 가이드 작성
- [ ] 배포 절차 수립
- [ ] 팀 교육

#### 5.3 프로덕션 배포
- [ ] Staging 검증
- [ ] Production 배포
- [ ] 모니터링

---

## 5. 시간 및 자원 계획

### 5.1 타임라인

| 단계 | 기간 | 소요일 | 상태 |
|------|------|--------|------|
| PLAN | 2026-04-20 ~ 21 | 1일 | 예정 |
| DESIGN | 2026-04-21 ~ 23 | 3일 | 예정 |
| DO | 2026-04-23 ~ 29 | 7일 | 예정 |
| CHECK | 2026-04-29 ~ 05-02 | 4일 | 예정 |
| ACT | 2026-05-02 ~ 04 | 2일 | 예정 |
| **총계** | **2026-04-20 ~ 05-04** | **17일** | - |

### 5.2 예상 코드량

| 모듈 | 라인 수 |
|------|---------|
| scheduler_service.py | 250 |
| batch_processor.py | 300 |
| routes_migration.py | 150 |
| 데이터베이스 스크립트 | 200 |
| 테스트 (24개) | 600 |
| 문서 | 300 |
| **합계** | **~1,800줄** |

### 5.3 테스트 계획 (24개)

**단위 테스트 (12개):**
- SchedulerService: 4개
- BatchProcessor: 4개
- 변경 감지: 2개
- 재시도 로직: 2개

**통합 테스트 (12개):**
- DB 마이그레이션: 3개
- E2E 배치 실행: 3개
- API 엔드포인트: 3개
- 에러 시나리오: 3개

---

## 6. 의존성 & 위험 관리

### 6.1 외부 의존성
- ✅ APScheduler (설치됨)
- ✅ Supabase Python 클라이언트
- ✅ document_ingestion.py (재사용)

### 6.2 위험 요소

| 위험 | 확률 | 임팩트 | 완화책 |
|------|------|--------|--------|
| DB 스키마 마이그레이션 실패 | 낮음 | 높음 | 백업 + 테스트 환경 검증 |
| 배치 처리 성능 부족 | 중간 | 중간 | 스레드풀 튜닝, 병렬화 |
| 스케줄 충돌 (Phase 4 배포) | 낮음 | 낮음 | 2026-05-04 배포 (배포 후) |
| 변경 감지 누락 | 중간 | 중간 | 이중 검증 + 수동 트리거 |

### 6.3 완화 전략
- Phase 4 배포 완료 후 시작 (5월 25일 이후)
- 테스트 환경에서 전수 검증
- 점진적 롤아웃 (초기 100 docs → 전체)

---

## 7. 성공 기준

### 7.1 기능 기준
- ✅ 매달 1회 자동 마이그레이션 실행
- ✅ 신규/수정 문서만 처리 (변경 감지)
- ✅ 병렬 처리 (5 workers)
- ✅ 부분 실패 시 재시도 (3회)
- ✅ 배치 로그 + 진행률 대시보드

### 7.2 품질 기준
- ✅ 모든 24 테스트 통과
- ✅ 코드 커버리지 ≥ 80%
- ✅ 설계 일치도 ≥ 90%
- ✅ 성능: 1000 docs < 300초
- ✅ 에러율 < 0.5%

### 7.3 배포 기준
- ✅ Staging 검증 완료
- ✅ 운영 문서 작성
- ✅ 팀 교육 완료
- ✅ Production 배포 (2026-05-04)

---

## 8. 다음 단계

1. **지금**: 이 계획 검토 및 승인
2. **2026-04-20**: PLAN 단계 시작
3. **2026-04-21**: DESIGN 단계 시작
4. **2026-04-23**: DO 단계 시작 (구현)
5. **2026-04-29**: CHECK 단계 시작 (테스트)
6. **2026-05-04**: ACT + 배포

---

**계획 작성**: 2026-04-20  
**마지막 검토**: 2026-04-20  
**상태**: READY FOR REVIEW ✅
