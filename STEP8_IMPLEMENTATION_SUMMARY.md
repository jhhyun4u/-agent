# STEP 8: 비동기 작업 처리 시스템 (Job Queue) - 구현 계획 수립 완료

**작성일**: 2026-04-20  
**상태**: PLAN & DESIGN 완료 → 구현 준비 완료  
**예상 완료**: 2026-05-07 (18일)

---

## 개요

STEP 8은 tenopa proposer의 **병목 단계(STEP 4A 정확도 검증, STEP 5A 발표자료 생성)를 백그라운드 비동기 처리**로 전환하여:

1. **사용자 응답시간**: 60~120초 → **2초 이내**로 단축
2. **동시 처리 능력**: 1~2개 → **10+개** (5개 워커 × 45초/job)
3. **작업 성공률**: 90% (timeout 제약) → **95%+** (무제한 재시도)
4. **운영 가시성**: 대시보드로 실시간 모니터링

---

## 문서 완성도

### PLAN 문서 (460줄)
**파일**: `docs/01-plan/features/step8-job-queue.plan.md`

#### 포함 내용:
1. **비즈니스 가치** (임팩트 메트릭 3개)
2. **9가지 기능 요구사항** (R1~R9)
   - R1: 비동기 작업 큐 (Redis 기반)
   - R2: Job 생명주기 관리
   - R3: 우선순위 조정 (STEP별)
   - R4: WebSocket 실시간 업데이트
   - R5~R9: 재시도, DLQ, 메트릭, 취소, 일시중지
3. **7가지 기술 요구사항** (TR1~TR7)
4. **현황 분석**: LangGraph와의 통합점 명확화
   - STEP 0~3: 동기 처리 (유지)
   - STEP 4A/5A: 비동기 큐로 이동 (신규)
5. **STEP별 우선도 매트릭**
   ```
   Priority 0 (높음): STEP 4A (정확도 검증)
   Priority 1 (중간): STEP 4B, 5A
   Priority 2 (낮음): STEP 5B, 6
   ```
6. **아키텍처 개요** (5개 모듈)
7. **세부 요구사항**
   - Job 구조 (18개 필드)
   - 상태 기계 (PENDING → RUNNING → SUCCESS/FAILED/CANCELLED)
   - 재시도 정책 (지수 백오프: 2s → 4s → 8s)
   - 우선순위 규칙
   - 성능 목표 (6개)
8. **위험 분석** (6가지 장애 + 완화 전략)
9. **14일 개발 일정** (DO Phase 일별 분해)
10. **성공 기준** (18개 체크리스트)

**핵심**: 명확한 요구사항 정의 + 기존 시스템과의 통합 전략 제시

---

### DESIGN 문서 (1,225줄)
**파일**: `docs/02-design/features/step8-job-queue.design.md`

#### 포함 내용:
1. **3계층 아키텍처** (Layer 1: API → Layer 2: Services → Layer 3: Infrastructure)
2. **5가지 핵심 설계 원칙**
   - Eventual Consistency (상태 일관성보다 가용성)
   - Fault Isolation (워커 격리)
   - Graceful Degradation (Redis 실패 시 fallback)
   - Observability (전체 상태 기록)
   - Immutability (Job 불변)

3. **모듈 5개 상세 설계** (구현용 의사 코드)
   
   **a) Job Model** (`app/models/job_schemas.py`)
   - JobStatus enum: PENDING, RUNNING, SUCCESS, FAILED, CANCELLED
   - JobType enum: STEP4A_DIAGNOSIS, STEP4A_REGENERATE, STEP4B_PRICING 등
   - JobPriority enum: HIGH(0), NORMAL(1), LOW(2)
   - Job Pydantic 모델 (18개 필드 + validation)
   - JobCreateRequest, JobStatusResponse, JobResultResponse, JobListResponse
   
   **b) Queue Manager** (`app/services/queue_manager.py`) - 450줄
   - Redis 클라이언트 래퍼
   - 우선도별 큐: jobs:queue:high, jobs:queue:normal, jobs:queue:low
   - BLPOP으로 FIFO + 우선도 처리
   - Job 상태 캐시 (TTL 24h)
   - 워커 하트비트 관리 (TTL 30s)
   - Methods:
     - enqueue_job(): 우선도 기반 큐 추가
     - dequeue_job(): blocking wait + timeout
     - mark_success(), mark_failure(): 상태 업데이트
     - get_job_state(): 캐시 조회
   
   **c) Job Service** (`app/services/job_service.py`) - 300줄
   - CRUD 연산 (create, get, get_jobs)
   - 상태 전환 (mark_job_running, mark_job_success, mark_job_failed, cancel_job)
   - DB 저장 + 메트릭 기록
   
   **d) Worker Pool** (`app/services/worker_pool.py`) - 250줄
   - ThreadPoolExecutor 기반 5개 워커 스레드
   - _worker_loop(): 메인 루프
     1. 큐에서 Job dequeue (blocking)
     2. JobExecutor.execute() 호출
     3. 결과 저장 또는 재시도 큐 추가
     4. 하트비트 업데이트
   - Graceful shutdown: SIGTERM 수신 후 진행 작업 완료 대기
   
   **e) Job Executor** (`app/services/job_executor.py`) - 350줄
   - 실제 작업 실행 엔진
   - Task handlers:
     - _step4a_diagnosis(): 정확도 검증
     - _step4a_regenerate(): 섹션 재작성
     - _step4b_pricing(): 입찰가 산정
     - _step5a_pptx(): PPT 생성
     - _step5b_submission(): 제출서류 준비

4. **DB 스키마 4개 테이블** (총 150줄 SQL)
   
   **a) jobs** (기본 정보)
   - id, proposal_id, step, type, status, priority
   - payload (< 1MB), result, error
   - retries, max_retries
   - created_at, started_at, completed_at, duration_seconds
   - created_by, assigned_worker_id, tags
   - Index 5개 (proposal_id, status, step, created_at, priority+status)
   
   **b) job_results** (결과 이력)
   - id, job_id, result_data, saved_at
   
   **c) job_metrics** (성과 추적)
   - id, job_id, step, type, status
   - duration_seconds, memory_mb, cpu_percent
   - worker_id, recorded_at
   
   **d) job_events** (감시 로그)
   - id, job_id, event_type, details, occurred_at

5. **API 엔드포인트 명세** (6개 동기 + 1개 WebSocket)
   - POST /api/jobs (Job 생성, 202 응답)
   - GET /api/jobs/{job_id}/status (상태 조회)
   - GET /api/jobs/{job_id}/result (결과 조회, SUCCESS 시)
   - POST /api/jobs/{job_id}/cancel (작업 취소)
   - POST /api/jobs/{job_id}/retry (수동 재시도)
   - GET /api/jobs/dlq (DLQ 목록)
   - WebSocket /ws/jobs/{job_id} (실시간 스트림)

6. **구현 전략: 3단계**
   
   **Phase 1 (4/23~24)**: 기반시설
   - Job Model + DB 스키마
   - Queue Manager (Redis)
   - Job Service (CRUD)
   
   **Phase 2 (4/25~26)**: 실행 엔진
   - Worker Pool + Job Executor
   - API Routes (동기)
   - WebSocket 구현
   
   **Phase 3 (4/27~28)**: 검증
   - 단위 테스트 40개
   - 통합테스트 20개
   - 성능 튜닝 + 모니터링

7. **에러 처리 & 복구** (6가지 장애 시나리오)
   - Redis 연결 실패 → In-Memory Queue fallback
   - Worker 크래시 → 자동 재시작
   - Job 타임아웃 (300s) → FAILED + DLQ
   - DB 쓰기 실패 → Redis only (나중에 동기화)
   - WebSocket 끊김 → 클라이언트 재연결 시 last-known 상태
   - Graceful shutdown → 진행 중 작업 완료 대기 (30s)

8. **모니터링 & 가시성**
   - job_metrics 테이블 수집 (duration, memory, cpu)
   - 대시보드 쿼리 (STEP별 성공률, 평균 시간, P95)
   - 알림 규칙 (DLQ 이동, 큐 대기 > 5분)

9. **Appendix: 설정**
   - REDIS_URL, NUM_WORKERS=5, MAX_RETRIES=3, JOB_TIMEOUT=300s

**핵심**: 프로덕션 수준의 상세한 기술 사양 제시 + 구현 코드 스켈레톤

---

## 핵심 설계 결정사항 (3가지)

### 1. Redis 메시지 브로커 선택
**이유:**
- Celery(RabbitMQ) vs **Redis** 비교
  - Redis: 단순, 기존 가능성, BLPOP으로 우선도 처리
  - RabbitMQ: 복잡, 추가 설정 필요
- 메시지 유실 괜찮음 (모든 Job은 DB에 영구 저장)
- BLPOP(queue:high) → BLPOP(queue:normal) → BLPOP(queue:low) 로 우선도 구현

### 2. 5개 워커 스레드 (Thread Pool)
**근거:**
- STEP 4A 평균 처리시간: 45초 (개선 목표)
- 5개 워커 × 45초/job = 225초 대기 시간 (3.75분)
- 대역폭 충분 (필요시 나중에 10개로 확장 가능)
- ProcessPoolExecutor vs **ThreadPoolExecutor**
  - Thread: asyncio 친화적, 리소스 효율
  - Process: 메모리 오버헤드, I/O 작업 비효율

### 3. 지수 백오프 재시도 정책
**적용:**
```
1차 실패 (retry=1): wait 2초 → PENDING
2차 실패 (retry=2): wait 4초 → PENDING
3차 실패 (retry=3): wait 8초 → PENDING
최종 실패: FAILED → DLQ (수동 개입)
```
**이유:**
- 네트워크 일시적 오류 회복 가능
- 외부 API 일시적 과부하 대응
- 최대 3회로 무한 루프 방지
- DLQ로 수동 개입 경로 제공

---

## 예상 구현 규모

| 항목 | 수량 | 상세 |
|------|------|------|
| **신규 코드** | 1,700줄 | Python (서비스 + 모델 + API) 1,200줄 + SQL 500줄 |
| **신규 테이블** | 4개 | jobs, job_results, job_metrics, job_events |
| **신규 모듈** | 5개 | Model, QueueManager, JobService, WorkerPool, JobExecutor |
| **API 엔드포인트** | 7개 | 6개 동기 (REST) + 1개 WebSocket |
| **예상 테스트** | 60개 | 40개 단위 + 20개 통합 |
| **개발 기간** | 14일 | 4/23~5/7 (DO 8일 + CHECK 2일 + ACT 1일) |
| **패키지 의존성** | 2개 | aioredis, redis (신규 추가) |

---

## 14일 일정 분해

### PLAN (1일) ✅ 완료
- 요구사항 정의
- 기존 시스템 분석
- 위험 식별

### DESIGN (1일) ✅ 완료
- 아키텍처 설계
- 모듈 명세
- DB 스키마 설계
- API 엔드포인트 정의

### DO (8일) 📅 예정
**4/23 (월)**: DB + Job Model
- DB 마이그레이션: jobs 테이블 생성 (150줄 SQL)
- Job Model: Pydantic 스키마 (100줄)

**4/24 (화)**: Queue Manager + Job Service
- Queue Manager: Redis 클라이언트 (300줄)
- Job Service: CRUD + 상태 전환 (250줄)

**4/25 (수)**: Worker Pool + Job Executor
- Worker Pool: 5개 스레드 관리 (250줄)
- Job Executor: STEP별 핸들러 (350줄)

**4/26 (목)**: API Routes + WebSocket
- API Routes: 6개 엔드포인트 (200줄)
- WebSocket: /ws/jobs/{job_id} (150줄)
- 앱 통합: main.py 수정 (50줄)

**4/27 (금)**: 기본 테스트
- 단위 테스트: JobService, QueueManager (20개, 200줄)
- 통합테스트: 워커 풀 + 큐 (10개, 150줄)

**4/28 (토)**: 성능 튜닝
- Redis 응답 시간 최적화
- Worker 메모리 프로파일링
- DB 쿼리 인덱스 확인

**4/29 (일)**: 엣지케이스 테스트
- 재시도 시나리오 (6개 테스트)
- DLQ 전환 검증 (3개 테스트)
- 동시성 충돌 테스트 (3개 테스트)

**5/1 (월)**: 스트레스 테스트
- 50개 동시 작업 처리
- 메모리 누수 모니터링 (8시간)
- 응답시간 P95/P99 측정

**5/2 (화)**: 최종 점검
- 모든 엣지케이스 수정
- 문서화 (README, 배포 가이드)
- 배포 준비 (환경 변수 설정)

### CHECK (2일) 📅 예정
**5/3 (수)**: 통합테스트
- 전체 워크플로 E2E (STEP 0~5)
- WebSocket 클라이언트 연결 테스트
- Graceful shutdown 검증

**5/4 (목)**: 성능 검증
- 응답시간 목표 달성 확인
  - Job 생성: < 100ms ✓
  - 상태 조회: < 50ms ✓
  - WebSocket: < 500ms 지연 ✓
- 처리량 목표 달성 확인
  - 5개 동시 작업 무중단 처리 ✓
  - 95%+ 성공률 (재시도 포함) ✓

### ACT (1일) 📅 예정
**5/5 (금)**: 버그 수정 + 배포
- CHECK 단계 이슈 수정
- 모니터링 대시보드 설정
- 프로덕션 배포 계획 수립

---

## 성공 기준 (18개 체크리스트)

### 기능성 (6개)
- [ ] Job 생성 API: POST /api/jobs → 202 Accepted + job_id
- [ ] 우선순위 처리: HIGH(0) > NORMAL(1) > LOW(2) 순서
- [ ] 재시도 로직: 3회 자동 재시도 + 지수 백오프 (2s → 4s → 8s)
- [ ] DLQ 전환: 최종 실패 시 jobs:queue:dlq로 이동
- [ ] 작업 취소: PENDING → CANCELLED 상태 변경 (RUNNING 불가)
- [ ] WebSocket: /ws/jobs/{job_id} 실시간 스트리밍 (10초마다 하트비트)

### 성능 (4개)
- [ ] Job 생성 응답: < 100ms (Redis enqueue 비동기)
- [ ] 상태 조회 응답: < 50ms (캐시 기반, TTL 5초)
- [ ] 동시 처리: 5개 Job 무중단 처리 (워커 충돌 없음)
- [ ] 평균 처리시간: STEP 4A 45초 (기존 60초 → 25% 개선)

### 안정성 (4개)
- [ ] Redis 장애 감지: 연결 실패 시 In-Memory Queue fallback
- [ ] Worker 크래시: 예외 발생 시 자동 재시작 (계속 루프 실행)
- [ ] 타임아웃 감지: duration > 300s → FAILED + DLQ
- [ ] Graceful Shutdown: SIGTERM 수신 후 진행 작업 완료 대기 (최대 30초)

### 모니터링 (4개)
- [ ] 대시보드 메트릭: job_metrics 정확도 99% (비교 검증)
- [ ] 하트비트 로그: 10초마다 worker heartbeat 기록
- [ ] 실패 작업 알림: DLQ 진입 시 Slack 알림
- [ ] 성능 수집: 평균/P95/P99 duration_seconds + memory_mb

---

## 기존 코드 통합점

### 1. LangGraph 통합 (app/graph/graph.py, proposal_nodes.py)
**현재 구조 (동기):**
```python
# STEP 4A 노드
async def step_4a_proposal_generation(state):
    proposal_content = await ai.generate_proposal(...)  # 30~60초
    return {"proposal_content": proposal_content}
```

**개선 후 (비동기 큐):**
```python
# STEP 4A 노드
async def step_4a_proposal_generation(state):
    job_id = await job_service.create_job(
        proposal_id=state["proposal_id"],
        job_type="step4a_diagnosis",
        payload={"section_ids": [...]}
    )
    return {"job_id": job_id}  # 즉시 반환 (2초)
```

**변경 파일:**
- `app/graph/nodes/proposal_nodes.py`: 함수 분해
- `app/graph/graph.py`: STEP 4A/5A → Job 큐로 전환

### 2. Document Ingestion 통합 (app/services/document_ingestion_service.py)
**호출 경로:**
```
Job Executor._step4a_diagnosis()
  → JobService.execute()
    → document_ingestion_service.run_accuracy_validator()
      → DB 조회 + AI 진단
```

**수정 사항:**
- Async 호환성 확인 (기존 동기 → 비동기 래퍼)
- 결과 포맷 표준화 (Job result schema와 일치)

### 3. HWPX/PPTX 빌더 통합 (app/services/hwpx_service.py, pptx_builder.py)
**호출 경로:**
```
Job Executor._step5a_pptx()
  → pptx_builder.build()
    → pptx_bytes
  → proposal_service.save_artifact()
    → S3 저장
```

**수정 사항:**
- Async 메서드 보장
- 바이너리 결과를 JSON result로 변환 (S3 URL 저장)

---

## 위험 & 완화 전략

| 위험 | 확률 | 영향 | 완화 전략 |
|------|------|------|---------|
| **Redis 장애** | 중간 | 큐 기능 중단 | Local In-Memory Queue fallback + 알림 |
| **Worker 메모리 누수** | 높음 | 장기 운영 성능 저하 | 주기적 재시작 (24h) + 메모리 모니터링 |
| **DB 과부하** (job_results 대량) | 중간 | 쓰기 속도 저하 | 배치 쓰기 (100개 단위) + 자동 아카이빙 (7일) |
| **동시성 경합** | 낮음 | 같은 job 중복 처리 | Redis SETEX lock (TTL 5분) |
| **WebSocket 좀비 연결** | 중간 | 메모리 누수 | 하트비트 + 자동 ping/pong (30s timeout) |
| **Job 페이로드 너무 큼** | 낮음 | Redis 메모리 고갈 | Payload 검증 (< 1MB) + 압축 (gzip) |

---

## 배포 준비 체크리스트

### 환경 설정
- [ ] Redis 서버 준비 (로컬 또는 AWS ElastiCache)
- [ ] PostgreSQL 마이그레이션 실행 (jobs 테이블 4개)
- [ ] 신규 패키지 설치 (aioredis)

### 코드 통합
- [ ] app/graph/graph.py에서 STEP 4A/5A Job 생성 로직 추가
- [ ] document_ingestion_service 비동기 호환성 확인
- [ ] hwpx_service, pptx_builder 비동기 호환성 확인

### 테스트
- [ ] 60개 테스트 전부 PASS (40 unit + 20 integration)
- [ ] E2E 테스트 (STEP 0~5 전체 워크플로)
- [ ] 스트레스 테스트 (50개 동시 작업)

### 모니터링
- [ ] job_metrics 대시보드 설정
- [ ] 알림 규칙 설정 (Slack DLQ, 큐 대기)
- [ ] 하트비트 로깅 확인

### 문서화
- [ ] README: Job Queue 시스템 개요
- [ ] 배포 가이드: 환경 변수, 마이그레이션 스크립트
- [ ] 운영 매뉴얼: 모니터링, 트러블슈팅, 수동 재시도

---

## 다음 단계

### 즉시 (4/21~22)
1. ✅ PLAN & DESIGN 문서 검토 완료
2. 기존 코드 통합점 확인
   - graph.py, proposal_nodes.py 분석
   - document_ingestion_service 시그니처 확인
3. Redis 환경 준비 (로컬 또는 클라우드)

### DO Phase (4/23~5/2)
1. DB 스키마 생성 (jobs 테이블 4개)
2. Job Model + Pydantic 스키마 구현
3. Queue Manager, Job Service, Worker Pool 순차 구현
4. API Routes + WebSocket 구현
5. 통합테스트 작성 + 성능 검증

### CHECK Phase (5/3~4)
1. E2E 워크플로 테스트
2. 성능 목표 달성 확인
3. 모니터링 대시보드 설정

### ACT Phase (5/5)
1. 버그 수정
2. 문서화 완성
3. 프로덕션 배포

---

## 참고 자료

| 문서 | 경로 | 용도 |
|------|------|------|
| PLAN | `docs/01-plan/features/step8-job-queue.plan.md` | 요구사항 정의 |
| DESIGN | `docs/02-design/features/step8-job-queue.design.md` | 기술 설계 |
| 기존 설계 | `docs/02-design/features/proposal-agent-v1/_index.md` | 시스템 참고 |
| DB 스키마 | `database/schema_v3.4.sql` | 기존 테이블 구조 |

---

**작성자**: AI Coworker (Claude Code)  
**작성일**: 2026-04-20  
**상태**: READY FOR DO PHASE  
**예상 완료**: 2026-05-07
