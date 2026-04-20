# STEP 8: 비동기 작업 처리 시스템 (Job Queue) - 구현 계획

**버전**: v1.0 (기능 정의)  
**작성일**: 2026-04-20  
**상태**: PLAN READY  
**목표 완료**: 2026-05-07 (18일)

---

## 1. 개요 & 비즈니스 가치

### 목표
제안서 생성 워크플로의 장시간 작업(정확도 검증, 섹션 재작성, HWPX 빌드)을 백그라운드로 이동하여 **사용자 경험 개선** 및 **서버 안정성 향상**

### 비즈니스 임팩트

| 메트릭 | 현재 | 목표 | 임팩트 |
|--------|------|------|--------|
| 사용자 응답시간 | 60~120초 | 2초 이내 | ⬆️ UX 개선 |
| 동시 작업 처리 | 1~2개 | 10+ 개 | ⬆️ 처리량 5배 증가 |
| 서버 timeout | 월 5~10건 | 거의 0 | ⬇️ 장애율 감소 |
| 작업 성공률 | 90% (timeout 제약) | 95%+ | ⬇️ 재작업 비용 감소 |
| 운영 가시성 | 없음 | 대시보드 | ⬆️ 모니터링 가능 |

### 범위 (STEP 8 전용)

**포함:**
- 비동기 작업 큐 시스템 (Redis 기반 메시지 브로커)
- Job 생명주기 관리 (생성 → 대기 → 실행 → 완료/실패)
- 실시간 상태 업데이트 (WebSocket)
- 우선순위 처리 (STEP별 우선도)
- 자동 재시도 + 데드레터 큐
- 작업 이력 추적 + 성능 메트릭

**미포함 (Phase 6+):**
- 분산 워커 노드 (동일 서버에서 멀티 워커)
- 작업 그룹화 (배치 자동화)
- 장기 실행 작업 스트리밍 (부분 결과 업데이트)

---

## 2. 요구사항 명세

### 2.1 기능 요구사항

| ID | 요구사항 | 설명 | 우선도 | 선행 |
|----|---------|------|--------|------|
| R1 | 비동기 작업 큐 | Redis 기반 메시지 브로커 + Worker Pool | **높음** | - |
| R2 | Job 생명주기 관리 | PENDING → RUNNING → SUCCESS/FAILED 상태 추적 | **높음** | R1 |
| R3 | 우선순위 조정 | STEP 단계별 우선도 (STEP 1 > STEP 4 > STEP 5) | **높음** | R2 |
| R4 | 실시간 상태 업데이트 | WebSocket `/ws/jobs/{job_id}` 스트리밍 | **높음** | R2 |
| R5 | 자동 재시도 | 실패 시 지수 백오프로 최대 3회 재시도 | **중간** | R2 |
| R6 | 데드레터 큐 | 최종 실패 시 수동 개입 가능한 별도 큐 | **중간** | R5 |
| R7 | 작업 이력 + 메트릭 | DB 저장 + 성공/실패/평균 시간 대시보드 | **중간** | R2 |
| R8 | 작업 취소 | 실행 중이 아닌 작업 취소 가능 | **낮음** | R2 |
| R9 | 작업 일시중지 | 중단 후 나중에 재개 (선택) | **낮음** | R8 |

### 2.2 기술 요구사항

| ID | 요구사항 | 설명 |
|----|---------|------|
| TR1 | Python 3.11+ 호환성 | FastAPI + asyncio 기반 |
| TR2 | Redis 클라이언트 | aioredis 또는 redis-py asyncio 모드 |
| TR3 | 데이터베이스 스키마 확장 | jobs + job_results + job_metrics 테이블 |
| TR4 | Worker 동시성 | ThreadPoolExecutor 또는 asyncio.gather (5 workers) |
| TR5 | 메모리 효율 | Job 페이로드 < 1MB, 이력 자동 정리 (7일) |
| TR6 | 장애 격리 | 한 워커 장애가 다른 워커에 영향 없음 (process-level isolation) |
| TR7 | 모니터링 | 하트비트 + 타임아웃 감지 (5분) + 로깅 |

### 2.3 성공 기준 (Definition of Done)

- [ ] API 응답 시간 < 2초 (job 생성 시)
- [ ] 95%+ 작업 완료율 (최종 성공 또는 DLQ 진입)
- [ ] WebSocket 실시간 업데이트 < 500ms 지연
- [ ] 재시도 성공률 > 80%
- [ ] 대시보드 메트릭 정확도 99%
- [ ] 무중단 배포 지원 (워커 graceful shutdown)
- [ ] E2E 테스트 커버리지 >= 80%

---

## 3. 현황 분석 & 통합점

### 3.1 기존 LangGraph 워크플로와의 관계

**현재 구조:**
```
사용자 요청 (FastAPI)
  ↓
POST /api/proposals/{id}/start
  ↓
LangGraph StateGraph (동기 block)
  ├─ STEP 0: RFP 검색 (3~5초)
  ├─ STEP 1: RFP 분석 + Go/No-Go (10~15초)
  ├─ STEP 2: 포지셔닝 전략 (8~10초)
  ├─ STEP 3: 팀 & 계획 (15~20초)
  ├─ STEP 4A: 제안서 작성 (30~60초) ← 이 부분을 Job Queue로 이동
  └─ STEP 5: 발표 자료 생성 (20~30초) ← 이 부분을 Job Queue로 이동
  ↓
응답 반환 (사용자가 기다림)
```

**개선된 구조:**
```
사용자 요청 (FastAPI)
  ↓
POST /api/proposals/{id}/start
  ↓
LangGraph StateGraph (즉시 반환: 2초)
  ├─ STEP 0~3: 즉시 실행 (동기)
  ├─ STEP 4A: Job Queue 큐잉 (PENDING)
  └─ STEP 5: Job Queue 큐잉 (PENDING)
  ↓
202 Accepted + job_id 반환 (사용자에게 즉시 응답)
  ↓
[백그라운드] Worker Pool이 큐에서 Job 꺼내서 처리
  ├─ 재시도 로직 (3회)
  ├─ 실패 → DLQ (수동 개입)
  └─ 완료 → WebSocket 알림
  ↓
사용자가 WebSocket으로 실시간 상태 모니터링
```

### 3.2 STEP별 작업 분류

| STEP | 현재 처리시간 | 큐 우선도 | 작업 타입 | 설명 |
|------|--------------|----------|---------|------|
| 0 (검색) | 3~5초 | - | SYNC | 빠름, 즉시 처리 (큐 미사용) |
| 1 (분석) | 10~15초 | - | SYNC | 비교적 빠름, 즉시 처리 (큐 미사용) |
| 2 (전략) | 8~10초 | - | SYNC | 중간, 즉시 처리 (큐 미사용) |
| 3 (계획) | 15~20초 | - | SYNC | 중간, 즉시 처리 (큐 미사용) |
| **4A** (제안서) | **30~60초** | **높음** | ASYNC | ⏱️ 병목, 우선처리 필요 |
| **4B** (입찰가) | **10~20초** | **중간** | ASYNC | 점수계산, 재계산 빈번 |
| **5A** (발표) | **20~30초** | **중간** | ASYNC | PPTX 렌더링, 재작업 빈번 |
| 5B (제출) | 5~10초 | 낮음 | ASYNC | 빠름, 선택적 비동기 |
| 6+ (평가) | 가변 | 낮음 | ASYNC | 종료 단계, 낮은 우선도 |

### 3.3 통합 API 엔드포인트

**새 엔드포인트 (Job Queue 제어):**

```
POST   /api/jobs/{job_id}/cancel           — 작업 취소 (PENDING → CANCELLED)
GET    /api/jobs/{job_id}/status           — 작업 상태 조회
GET    /api/jobs/{job_id}/result           — 작업 결과 조회 (SUCCESS 시)
GET    /api/jobs?step=4a&status=running    — 작업 목록 조회 (필터링)
POST   /api/jobs/{job_id}/retry            — 실패 작업 재시도 (수동)
GET    /api/jobs/dlq                       — 데드레터 큐 조회
WebSocket /ws/jobs/{job_id}                — 실시간 상태 스트리밍
```

**기존 엔드포인트 (동기 유지):**
```
POST   /api/proposals/{id}/start           — 워크플로 시작 (202 Accepted)
GET    /api/proposals/{id}/state           — 현재 그래프 상태
POST   /api/proposals/{id}/resume          — Human 리뷰 입력
```

---

## 4. 아키텍처 개요

### 4.1 시스템 구성도

```
┌─────────────────────────────────────────────────────────────┐
│  FastAPI Server (app.main)                                  │
│  ├─ POST /api/proposals/{id}/start                          │
│  │   └─ LangGraph (STEP 0~3: SYNC) → Job 생성 → 202 반환  │
│  │                                                           │
│  ├─ Job Queue API (/api/jobs/*)                            │
│  │   ├─ GET /api/jobs/{job_id}/status                      │
│  │   ├─ POST /api/jobs/{job_id}/cancel                     │
│  │   └─ WebSocket /ws/jobs/{job_id}                        │
│  │                                                           │
│  └─ Health Check: /health/queue                            │
│     └─ Redis + Worker Pool 상태 검사                       │
└─────────────────────────────────────────────────────────────┘
         │
         ├─────────────────────────────────────────┐
         │                                           │
         ▼                                           ▼
┌──────────────────────┐              ┌─────────────────────┐
│  Redis Queue         │              │  PostgreSQL (jobs)  │
│  ├─ high_priority    │              │  ├─ id              │
│  ├─ normal_priority  │              │  ├─ proposal_id     │
│  └─ low_priority     │              │  ├─ type (step4a)   │
│                      │              │  ├─ status          │
│ Key-Value Store      │              │  ├─ payload         │
│ (job_state)          │              │  ├─ result          │
└──────────────────────┘              │  ├─ created_at      │
         ▲                              │  └─ completed_at    │
         │                              └─────────────────────┘
         │
         └──────────────────────────────────────────┐
                                                    │
┌────────────────────────────────────────────────────┴──────────┐
│  Worker Pool (5 workers @ app startup)                        │
│  ├─ Worker 1: fetch job → process → save result             │
│  ├─ Worker 2: ...                                            │
│  ├─ Worker 3: ...                                            │
│  ├─ Worker 4: ...                                            │
│  └─ Worker 5: ...                                            │
│                                                               │
│  Retry Logic:                                                 │
│  • 1차 실패 → wait 2s → retry (max_retries=3)               │
│  • 최종 실패 → DLQ (dead_letter_queue)                       │
│  • 타임아웃 (300s) → mark failed + DLQ                       │
│                                                               │
│  Heartbeat:                                                   │
│  • 10초마다 상태 업데이트                                    │
│  • WebSocket 구독자에게 broadcast                            │
└───────────────────────────────────────────────────────────────┘
```

### 4.2 주요 모듈

| 모듈 | 파일 | 책임 | LOC |
|------|------|------|-----|
| Job Model | `app/models/job_schemas.py` | Job + JobResult Pydantic 스키마 | 100 |
| Job Service | `app/services/job_service.py` | CRUD, 상태 전환, 재시도 로직 | 300 |
| Queue Manager | `app/services/queue_manager.py` | Redis 큐 관리 (enqueue, dequeue) | 200 |
| Worker Pool | `app/services/worker_pool.py` | 5개 워커 스레드 관리 + graceful shutdown | 250 |
| Job Executor | `app/services/job_executor.py` | 실제 작업 실행 (step4a, step4b, step5a) | 350 |
| DB Schema | `database/migrations/step8_job_queue.sql` | jobs, job_results, job_metrics 테이블 | 150 |
| API Routes | `app/api/routes_jobs.py` | Job Queue API 엔드포인트 | 200 |
| WebSocket | `app/api/routes_ws_jobs.py` | /ws/jobs/{job_id} 스트리밍 | 150 |

**총 신규 코드:** ~1,700줄

---

## 5. 세부 요구사항

### 5.1 Job 구조

```python
@dataclass
class Job:
    """비동기 작업 단위"""
    id: str                              # UUID
    proposal_id: str                     # 제안서 프로젝트 ID
    step: Literal["4a", "4b", "5a"]     # STEP 분류
    type: str                            # 작업 타입 (diagnosis, regenerate, build_pptx 등)
    status: JobStatus                    # PENDING | RUNNING | SUCCESS | FAILED | CANCELLED
    priority: int                        # 0~3 (높음~낮음)
    payload: dict                        # 입력 파라미터 (e.g., {"section_ids": [...]})
    result: Optional[dict]               # 결과 (SUCCESS 시 채워짐)
    error: Optional[str]                 # 에러 메시지 (FAILED 시)
    retries: int                         # 시도 횟수 (0~3)
    max_retries: int                     # 최대 재시도 횟수 (기본값 3)
    created_at: datetime                 # 생성 시각
    started_at: Optional[datetime]       # 시작 시각
    completed_at: Optional[datetime]     # 완료 시각
    duration_seconds: Optional[float]    # 실행 소요시간
    created_by: str                      # 사용자 ID
    assigned_worker_id: Optional[str]    # 현재 처리중인 워커 ID
```

### 5.2 Job Status 상태 기계

```
PENDING
  ├─ (worker picks up)
  ├→ RUNNING
  │   ├─ (success)
  │   ├→ SUCCESS ✓
  │   │
  │   └─ (error, retries < max_retries)
  │   ├→ PENDING (back to queue)
  │   │
  │   └─ (error, retries >= max_retries)
  │   └→ FAILED (→ DLQ)
  │
  └─ (user cancels)
  └→ CANCELLED
```

### 5.3 우선순위 규칙

```python
PRIORITY_MAP = {
    "step_4a_diagnosis": 0,     # 높음 (정확도 검증)
    "step_4a_regenerate": 0,    # 높음 (섹션 재작성)
    "step_4b_pricing": 1,       # 중간 (입찰가)
    "step_5a_pptx": 1,          # 중간 (발표 자료)
    "step_5b_submission": 2,    # 낮음 (제출서류)
    "step_6_evaluation": 3,     # 매우 낮음 (모의평가)
}
```

### 5.4 재시도 정책

```
1차 실패 (retry=1):
  • wait 2초 → PENDING 상태로 복귀
  
2차 실패 (retry=2):
  • wait 4초 → PENDING 상태로 복귀
  
3차 실패 (retry=3):
  • wait 8초 → PENDING 상태로 복귀
  
4차 실패 (retry 초과):
  • FAILED 상태 → DLQ (dead_letter_queue) 이동
  • 수동 개입 필요 (관리자 대시보드)
```

### 5.5 성능 목표

| 메트릭 | 목표 | 근거 |
|--------|------|------|
| Job 생성 응답시간 | < 100ms | Redis enqueue (비동기) |
| 상태 조회 응답시간 | < 50ms | DB 캐시 (TTL 5초) |
| WebSocket 알림 지연 | < 500ms | 하트비트 간격 10초 |
| 평균 처리시간 | STEP 4A: 45초 | 기존 60초 → 45초 (최적화) |
| 큐 대기시간 | < 30초 | 5 workers × 30초 / job |
| 메모리 사용 (Worker) | < 500MB | 제약이 있는 환경 고려 |
| Redis 메모리 | < 1GB | job_state + queue (24시간 이력) |

---

## 6. 위험 분석 & 완화 전략

| 위험 | 영향 | 확률 | 완화 전략 |
|------|------|------|---------|
| **Redis 장애** | 큐 기능 전체 중단 | 중간 | Failover 설정 + 로컬 In-Memory Queue (fallback) |
| **Worker 메모리 누수** | 장기 운영 중 성능 저하 | 높음 | 주기적 재시작 (24시간) + 메모리 모니터링 |
| **DB 과부하** | job_results 대량 쓰기 | 중간 | 배치 쓰기 (100개 단위) + 자동 아카이빙 (7일 이후) |
| **동시성 경합** | 같은 job을 2개 워커가 처리 | 낮음 | Redis SETEX로 lock 획득 (TTL 5분) |
| **WebSocket 연결 누수** | 좀비 연결 증가 | 중간 | 하트비트 (10초) + 자동 ping/pong |
| **작업 페이로드 너무 큼** | Redis 메모리 고갈 | 낮음 | Payload 검증 (< 1MB) + 압축 (gzip) |

---

## 7. 일정 & 마일스톤

### 7.1 2주일 (14일) 개발 일정

| Phase | 일정 | 태스크 | 결과물 |
|-------|------|--------|--------|
| **PLAN** | 1일 (4/20) | 요구사항 명세 + DB 설계 | ✓ 본 문서 |
| **DESIGN** | 2일 (4/21~22) | 아키텍처 + 모듈 설계 | design.md |
| **DO** | 8일 (4/23~5/2) | 구현 (모듈별) | 코드 + 테스트 |
| **CHECK** | 2일 (5/3~4) | 통합테스트 + 성능 검증 | test 결과 |
| **ACT** | 1일 (5/5) | 버그 수정 + 문서화 | 최종 코드 |

### 7.2 DO Phase 상세 일정

| 일자 | 태스크 | 담당 | 예상 LOC |
|------|--------|------|---------|
| 4/23 | DB 스키마 + Job Model | BE | 250 |
| 4/24 | Queue Manager + Job Service | BE | 350 |
| 4/25 | Worker Pool + Job Executor | BE | 400 |
| 4/26 | API Routes + WebSocket | BE | 300 |
| 4/27 | 기본 테스트 (단위 + 통합) | QA | 400 |
| 4/28 | 성능 튜닝 + 모니터링 | BE | 150 |
| 4/29 | 엣지케이스 + 재시도 검증 | QA | 200 |
| 5/1 | 스트레스 테스트 (동시 작업 50개) | QA | 150 |
| 5/2 | 문서화 + 배포 준비 | BE/Doc | 100 |

---

## 8. 성공 기준 (검증 체크리스트)

### 기능성

- [ ] Job 생성 API 동작 (POST /api/jobs → 202 + job_id)
- [ ] 우선순위 처리 확인 (high > normal > low)
- [ ] 재시도 로직 동작 (3회 최대)
- [ ] DLQ 전환 동작 (최종 실패)
- [ ] 작업 취소 동작 (PENDING → CANCELLED)
- [ ] WebSocket 실시간 업데이트 (< 500ms 지연)

### 성능

- [ ] Job 생성 응답시간 < 100ms
- [ ] 상태 조회 응답시간 < 50ms
- [ ] 5개 동시 작업 처리 (no conflict)
- [ ] 50개 작업 큐 (메모리 < 100MB)
- [ ] 평균 처리시간 45초 (STEP 4A, 기존 60초)

### 안정성

- [ ] Redis 장애 감지 + fallback (local queue)
- [ ] Worker 크래시 감지 + 자동 재시작
- [ ] 타임아웃 감지 (300s > job 처리시간)
- [ ] DB 연결 끊김 시 재시도
- [ ] Graceful shutdown (진행 중 작업 완료 대기)

### 모니터링

- [ ] 대시보드 메트릭 정확도 99%
- [ ] 하트비트 로그 기록 (10초마다)
- [ ] 실패 작업 알림 (Slack)
- [ ] 성능 메트릭 수집 (평균/P95/P99)

---

## 9. 의존성 & 사전 조건

### 9.1 환경 설정

- [ ] Redis 서버 (localhost:6379 또는 AWS ElastiCache)
- [ ] PostgreSQL (Supabase, 기존 연결 사용)
- [ ] Python 3.11+
- [ ] 신규 패키지: `aioredis`, `python-dotenv` (기존에 있으면 스킵)

### 9.2 권한 & 접근

- [ ] DB 마이그레이션 권한 (job 테이블 생성)
- [ ] Redis 접근 권한 (로컬 또는 클라우드)
- [ ] Slack Webhook (선택, 알림용)

### 9.3 기존 코드 의존

- [ ] LangGraph graph.py (STEP 4A/5A Job 생성 지점)
- [ ] Document Ingestion Pipeline (Job Executor에서 호출)
- [ ] HWPX Service (Job Executor에서 호출)
- [ ] PPTX Builder (Job Executor에서 호출)

---

## 10. 질문 & 추가 검토 사항

1. **Job 페이로드 저장 위치**: DB 또는 S3?
   - 권장: 작은 payload (< 10KB)는 DB, 큰 것은 S3 + URL 참조

2. **Worker 수**: 5개가 적절한지?
   - STEP 4A 평균 45초 × 5 = 225초 큐 시간 (3.75분)
   - 대역폭 충분함, 필요시 확장 가능

3. **Redis vs RabbitMQ**: 왜 Redis?
   - 기존 시스템에 이미 있을 가능성 + 구현 단순
   - 메시지 유실 상관없음 (DB에 영구 저장)

4. **무중단 배포**: 어떻게?
   - 신규 워커 시작 → 기존 워커는 진행 중 작업 완료 대기 → 종료
   - 큐에 남은 job은 다시 PENDING으로 (재시작 후 처리)

---

## Appendix A: 용어정의

| 용어 | 정의 |
|------|------|
| **Job** | 하나의 비동기 작업 단위 (e.g., "STEP 4A 진단") |
| **Queue** | Redis 기반 메시지 큐 (FIFO + 우선순위) |
| **Worker** | 큐에서 Job을 꺼내 실행하는 스레드 (최대 5개) |
| **DLQ** | Dead Letter Queue, 최종 실패 Job의 격리소 |
| **Heartbeat** | 주기적 상태 업데이트 신호 (10초마다) |
| **Graceful Shutdown** | 진행 중 작업 완료 후 종료 |
| **Payload** | Job 입력 파라미터 (JSON) |
| **Result** | Job 출력 데이터 (JSON) |

---

**문서 버전:** v1.0  
**마지막 수정:** 2026-04-20  
**다음 단계:** DESIGN 문서 작성 (4/21)
