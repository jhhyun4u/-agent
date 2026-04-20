# STEP 8: 비동기 작업 처리 시스템 (Job Queue) - 상세 설계

**버전**: v1.0  
**작성일**: 2026-04-20  
**상태**: DESIGN READY  
**설계 문서**: 기술 아키텍처 + 모듈 명세

---

## 1. 기술 아키텍처 (3계층)

### 1.1 계층 구조

```
┌────────────────────────────────────────────────────────┐
│ Layer 1: API Gateway (FastAPI Routes)                  │
│ ├─ POST /api/jobs                  (Job 생성)         │
│ ├─ GET  /api/jobs/{id}/status      (상태 조회)        │
│ ├─ GET  /api/jobs/{id}/result      (결과 조회)        │
│ ├─ POST /api/jobs/{id}/cancel      (작업 취소)        │
│ └─ WebSocket /ws/jobs/{job_id}     (실시간 스트림)    │
└────────────────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│ Layer 2: Business Logic (Services)                     │
│ ├─ JobService         (CRUD + 상태 전환)              │
│ ├─ QueueManager       (Redis 큐 관리)                  │
│ ├─ JobExecutor        (실제 작업 수행)                │
│ ├─ WorkerPool         (5개 워커 관리)                  │
│ └─ MetricsCollector   (성능 메트릭 수집)             │
└────────────────────────────────────────────────────────┘
                    │
                    ▼
┌────────────────────────────────────────────────────────┐
│ Layer 3: Infrastructure (Data + Queue)                 │
│ ├─ PostgreSQL         (jobs, job_results 테이블)      │
│ ├─ Redis              (queue, job_state cache)         │
│ └─ Storage            (S3, 결과 아티팩트)              │
└────────────────────────────────────────────────────────┘
```

### 1.2 핵심 설계 원칙

| 원칙 | 설명 | 구현 |
|------|------|------|
| **Eventual Consistency** | 상태 일관성보다 가용성 우선 | Redis + DB 비동기 동기화 |
| **Fault Isolation** | 워커 장애가 시스템 전체에 영향 없음 | Process-level isolation + retry |
| **Graceful Degradation** | Redis 실패 시 fallback to local queue | In-Memory Queue + persistence |
| **Observability** | 모든 상태 변화 기록 | job_events 테이블 로깅 |
| **Immutability** | Job 객체 불변 원칙 | Result는 별도 테이블에 저장 |

---

## 2. 모듈 설계

### 2.1 Job Model (`app/models/job_schemas.py`)

```python
from enum import Enum
from typing import Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

class JobStatus(str, Enum):
    """Job 생명주기 상태"""
    PENDING = "pending"      # 큐 대기 중
    RUNNING = "running"      # 처리 중
    SUCCESS = "success"      # 완료 (성공)
    FAILED = "failed"        # 실패 (최대 재시도 초과)
    CANCELLED = "cancelled"  # 취소됨 (사용자)

class JobType(str, Enum):
    """작업 분류"""
    STEP4A_DIAGNOSIS = "step4a_diagnosis"        # STEP 4A: 정확도 검증
    STEP4A_REGENERATE = "step4a_regenerate"      # STEP 4A: 섹션 재작성
    STEP4B_PRICING = "step4b_pricing"            # STEP 4B: 입찰가 산정
    STEP5A_PPTX = "step5a_pptx"                  # STEP 5A: PPT 생성
    STEP5B_SUBMISSION = "step5b_submission"      # STEP 5B: 제출서류
    STEP6_EVALUATION = "step6_evaluation"        # STEP 6: 모의평가

class JobPriority(int, Enum):
    """우선도 (낮은 수일수록 높은 우선도)"""
    HIGH = 0
    NORMAL = 1
    LOW = 2

class Job(BaseModel):
    """비동기 작업 단위 (DB 모델)"""
    id: UUID
    proposal_id: UUID
    step: Literal["4a", "4b", "5a", "5b", "6"]
    type: JobType
    status: JobStatus = JobStatus.PENDING
    priority: JobPriority = JobPriority.NORMAL
    
    # 입력
    payload: dict = Field(
        default_factory=dict,
        description="작업 입력 파라미터 (< 1MB)"
    )
    
    # 출력 & 에러
    result: Optional[dict] = None
    error: Optional[str] = None
    
    # 재시도
    retries: int = 0
    max_retries: int = 3
    
    # 타이밍
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # 추적
    created_by: UUID                          # 사용자 ID
    assigned_worker_id: Optional[str] = None  # "worker-1", "worker-2" 등
    
    # 태그
    tags: dict = Field(default_factory=dict)  # e.g., {"section_id": "s1", ...}

class JobCreateRequest(BaseModel):
    """Job 생성 요청"""
    proposal_id: UUID
    type: JobType
    payload: dict = Field(default_factory=dict)
    priority: JobPriority = JobPriority.NORMAL
    max_retries: int = 3

class JobStatusResponse(BaseModel):
    """Job 상태 조회 응답"""
    id: UUID
    status: JobStatus
    progress: float = 0.0  # 0~100% (진행률)
    retries: int
    duration_seconds: Optional[float] = None
    created_at: datetime
    started_at: Optional[datetime] = None

class JobResultResponse(BaseModel):
    """Job 결과 조회 응답 (SUCCESS 시)"""
    id: UUID
    result: dict
    duration_seconds: float
    completed_at: datetime

class JobListResponse(BaseModel):
    """Job 목록 조회 응답"""
    total: int
    page: int
    limit: int
    items: list[JobStatusResponse]
```

### 2.2 Queue Manager (`app/services/queue_manager.py`)

```python
import asyncio
import json
import logging
from typing import Optional, List
from uuid import UUID
import aioredis
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class QueueManager:
    """Redis 기반 메시지 큐 관리"""
    
    # 큐 이름 (우선도별)
    QUEUE_HIGH = "jobs:queue:high"
    QUEUE_NORMAL = "jobs:queue:normal"
    QUEUE_LOW = "jobs:queue:low"
    QUEUE_DLQ = "jobs:queue:dlq"  # Dead Letter Queue
    
    # 기타 키
    KEY_JOB_STATE = "jobs:state:{job_id}"      # hash: {status, retries, worker_id}
    KEY_WORKER_HEARTBEAT = "workers:hb:{worker_id}"  # heartbeat (TTL 30s)
    
    def __init__(self, redis_url: str = "redis://localhost"):
        self.redis_url = redis_url
        self.redis: Optional[aioredis.Redis] = None
        self.logger = logger
    
    async def connect(self):
        """Redis 연결"""
        self.redis = await aioredis.from_url(self.redis_url, decode_responses=True)
        self.logger.info(f"Connected to Redis: {self.redis_url}")
    
    async def close(self):
        """Redis 연결 종료"""
        if self.redis:
            await self.redis.close()
    
    # ── Public Methods ──
    
    async def enqueue_job(self, job: "Job") -> bool:
        """Job을 큐에 추가"""
        try:
            queue_key = self._get_queue_key(job.priority)
            job_json = job.model_dump_json()
            
            # 1. 큐에 추가 (list의 우측에 push)
            await self.redis.rpush(queue_key, job_json)
            
            # 2. Job 상태 캐시 (TTL 24시간)
            state_key = self.KEY_JOB_STATE.format(job_id=str(job.id))
            await self.redis.hset(
                state_key,
                mapping={
                    "status": job.status.value,
                    "retries": job.retries,
                    "worker_id": "",
                    "updated_at": datetime.utcnow().isoformat(),
                }
            )
            await self.redis.expire(state_key, 86400)  # 24시간
            
            self.logger.info(f"Job {job.id} enqueued (priority={job.priority})")
            return True
        
        except Exception as e:
            self.logger.error(f"Failed to enqueue job {job.id}: {e}")
            return False
    
    async def dequeue_job(self, worker_id: str, timeout: int = 5) -> Optional[dict]:
        """
        큐에서 Job을 꺼냄 (우선도 순서)
        - HIGH > NORMAL > LOW 순서로 확인
        - blocking=true로 대기
        """
        try:
            # 우선도별로 큐 확인
            for queue_key in [self.QUEUE_HIGH, self.QUEUE_NORMAL, self.QUEUE_LOW]:
                # BLPOP: 왼쪽에서 꺼냄 (FIFO) + blocking
                result = await asyncio.wait_for(
                    self.redis.blpop(queue_key, timeout=1),
                    timeout=timeout
                )
                
                if result:
                    _, job_json = result
                    job_dict = json.loads(job_json)
                    
                    # Job 상태 업데이트: RUNNING
                    state_key = self.KEY_JOB_STATE.format(job_id=job_dict["id"])
                    await self.redis.hset(
                        state_key,
                        mapping={
                            "status": "running",
                            "worker_id": worker_id,
                            "started_at": datetime.utcnow().isoformat(),
                        }
                    )
                    
                    self.logger.info(f"Job dequeued by {worker_id}: {job_dict['id']}")
                    return job_dict
            
            return None
        
        except asyncio.TimeoutError:
            return None
        except Exception as e:
            self.logger.error(f"Failed to dequeue job: {e}")
            return None
    
    async def mark_success(self, job_id: str, result: dict) -> bool:
        """Job 완료 처리"""
        try:
            state_key = self.KEY_JOB_STATE.format(job_id=job_id)
            await self.redis.hset(
                state_key,
                mapping={
                    "status": "success",
                    "completed_at": datetime.utcnow().isoformat(),
                    "result_size": len(json.dumps(result)),
                }
            )
            self.logger.info(f"Job {job_id} marked SUCCESS")
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark job success: {e}")
            return False
    
    async def mark_failure(self, job_id: str, error: str, retries: int) -> bool:
        """Job 실패 처리 (재시도 결정)"""
        try:
            if retries >= 3:  # 최대 재시도 초과
                # DLQ로 이동
                await self.redis.rpush(self.QUEUE_DLQ, json.dumps({
                    "job_id": job_id,
                    "error": error,
                    "failed_at": datetime.utcnow().isoformat(),
                }))
                status = "failed"
                self.logger.warning(f"Job {job_id} moved to DLQ after {retries} retries")
            else:
                # 재시도 큐로 복귀
                status = "pending"
                self.logger.info(f"Job {job_id} will retry (attempt {retries + 1})")
            
            state_key = self.KEY_JOB_STATE.format(job_id=job_id)
            await self.redis.hset(
                state_key,
                mapping={
                    "status": status,
                    "retries": retries,
                    "last_error": error[:200],  # 처음 200자만
                }
            )
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark job failure: {e}")
            return False
    
    async def get_job_state(self, job_id: str) -> Optional[dict]:
        """Job 상태 조회 (캐시에서)"""
        try:
            state_key = self.KEY_JOB_STATE.format(job_id=job_id)
            state = await self.redis.hgetall(state_key)
            return state if state else None
        except Exception as e:
            self.logger.error(f"Failed to get job state: {e}")
            return None
    
    async def worker_heartbeat(self, worker_id: str) -> bool:
        """워커 하트비트 (존재 신호)"""
        try:
            hb_key = self.KEY_WORKER_HEARTBEAT.format(worker_id=worker_id)
            await self.redis.set(hb_key, datetime.utcnow().isoformat(), ex=30)  # TTL 30s
            return True
        except Exception as e:
            self.logger.error(f"Heartbeat failed for {worker_id}: {e}")
            return False
    
    async def get_active_workers(self) -> List[str]:
        """현재 활성 워커 목록"""
        try:
            pattern = "workers:hb:*"
            keys = await self.redis.keys(pattern)
            return [k.replace("workers:hb:", "") for k in keys]
        except Exception as e:
            self.logger.error(f"Failed to get active workers: {e}")
            return []
    
    # ── Private Methods ──
    
    def _get_queue_key(self, priority: "JobPriority") -> str:
        """우선도별 큐 키 반환"""
        if priority == JobPriority.HIGH:
            return self.QUEUE_HIGH
        elif priority == JobPriority.NORMAL:
            return self.QUEUE_NORMAL
        else:
            return self.QUEUE_LOW
```

### 2.3 Job Service (`app/services/job_service.py`)

```python
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class JobService:
    """Job CRUD + 상태 관리"""
    
    def __init__(self, db_client, queue_manager):
        self.db = db_client
        self.queue = queue_manager
        self.logger = logger
    
    # ── CRUD ──
    
    async def create_job(
        self,
        proposal_id: UUID,
        job_type: str,
        payload: dict,
        priority: int = 1,
        created_by: UUID = None,
    ) -> "Job":
        """새로운 Job 생성 및 큐에 등록"""
        job_id = uuid4()
        
        job = Job(
            id=job_id,
            proposal_id=proposal_id,
            step=job_type.split("_")[1],  # "step4a_diagnosis" → "4a"
            type=JobType(job_type),
            status=JobStatus.PENDING,
            priority=JobPriority(priority),
            payload=payload,
            created_by=created_by,
            created_at=datetime.utcnow(),
        )
        
        # 1. DB에 저장
        await self._save_to_db(job)
        
        # 2. 큐에 추가
        success = await self.queue.enqueue_job(job)
        
        if not success:
            self.logger.error(f"Failed to enqueue job {job_id}, falling back to local queue")
            # Fallback: local in-memory queue (나중에 구현)
        
        return job
    
    async def get_job(self, job_id: UUID) -> Optional[Job]:
        """Job 조회"""
        response = await self.db.table("jobs").select("*").eq("id", str(job_id)).single()
        if response:
            return Job(**response)
        return None
    
    async def get_jobs(
        self,
        proposal_id: UUID = None,
        status: str = None,
        step: str = None,
        limit: int = 20,
        offset: int = 0,
    ) -> tuple[List[Job], int]:
        """Job 목록 조회 (필터링)"""
        query = self.db.table("jobs").select("*", count="exact")
        
        if proposal_id:
            query = query.eq("proposal_id", str(proposal_id))
        if status:
            query = query.eq("status", status)
        if step:
            query = query.eq("step", step)
        
        response = await query.order("created_at", ascending=False).range(offset, offset + limit)
        
        jobs = [Job(**row) for row in response.data]
        total = response.count
        
        return jobs, total
    
    # ── 상태 전환 ──
    
    async def mark_job_running(self, job_id: UUID, worker_id: str) -> bool:
        """Job 상태를 RUNNING으로 변경"""
        try:
            await self.db.table("jobs").update({
                "status": "running",
                "started_at": datetime.utcnow().isoformat(),
                "assigned_worker_id": worker_id,
            }).eq("id", str(job_id))
            
            # 캐시도 동시 업데이트
            await self.queue.get_job_state(str(job_id))
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark job as running: {e}")
            return False
    
    async def mark_job_success(self, job_id: UUID, result: dict) -> bool:
        """Job 상태를 SUCCESS로 변경"""
        try:
            duration = self._calculate_duration(job_id)
            
            await self.db.table("jobs").update({
                "status": "success",
                "result": result,
                "completed_at": datetime.utcnow().isoformat(),
                "duration_seconds": duration,
            }).eq("id", str(job_id))
            
            # 성과 메트릭 기록
            await self._record_metric(job_id, "success", duration)
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark job as success: {e}")
            return False
    
    async def mark_job_failed(self, job_id: UUID, error: str, attempt: int) -> bool:
        """Job 상태를 FAILED로 변경 (또는 PENDING with retries++)"""
        try:
            if attempt >= 3:
                # 최대 재시도 초과
                await self.db.table("jobs").update({
                    "status": "failed",
                    "error": error,
                    "completed_at": datetime.utcnow().isoformat(),
                    "retries": attempt,
                }).eq("id", str(job_id))
                
                self.logger.error(f"Job {job_id} FAILED after {attempt} attempts")
            else:
                # 재시도 가능
                await self.db.table("jobs").update({
                    "retries": attempt,
                    "error": error,  # 마지막 에러만 저장
                }).eq("id", str(job_id))
                
                self.logger.info(f"Job {job_id} will retry (attempt {attempt + 1})")
            
            return True
        except Exception as e:
            self.logger.error(f"Failed to mark job as failed: {e}")
            return False
    
    async def cancel_job(self, job_id: UUID) -> bool:
        """Job 취소 (PENDING 또는 RUNNING → CANCELLED)"""
        try:
            job = await self.get_job(job_id)
            if job.status in [JobStatus.SUCCESS, JobStatus.FAILED]:
                return False  # 이미 완료된 작업은 취소 불가
            
            await self.db.table("jobs").update({
                "status": "cancelled",
                "completed_at": datetime.utcnow().isoformat(),
            }).eq("id", str(job_id))
            
            self.logger.info(f"Job {job_id} cancelled")
            return True
        except Exception as e:
            self.logger.error(f"Failed to cancel job: {e}")
            return False
    
    # ── Private Helpers ──
    
    async def _save_to_db(self, job: Job):
        """Job을 DB에 저장"""
        await self.db.table("jobs").insert({
            "id": str(job.id),
            "proposal_id": str(job.proposal_id),
            "step": job.step,
            "type": job.type.value,
            "status": job.status.value,
            "priority": job.priority.value,
            "payload": job.payload,
            "created_at": job.created_at.isoformat(),
            "created_by": str(job.created_by) if job.created_by else None,
        })
    
    def _calculate_duration(self, job_id: UUID) -> float:
        """Job 처리 시간 계산 (started_at -> completed_at)"""
        # DB에서 조회 후 계산
        pass
    
    async def _record_metric(self, job_id: UUID, status: str, duration: float):
        """성과 메트릭 기록 (job_metrics 테이블)"""
        await self.db.table("job_metrics").insert({
            "job_id": str(job_id),
            "status": status,
            "duration_seconds": duration,
            "recorded_at": datetime.utcnow().isoformat(),
        })
```

### 2.4 Worker Pool (`app/services/worker_pool.py`)

```python
import asyncio
import logging
import signal
from typing import Optional, Callable, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
import uuid

logger = logging.getLogger(__name__)

class WorkerPool:
    """5개 워커 스레드 관리"""
    
    def __init__(
        self,
        job_service: "JobService",
        queue_manager: "QueueManager",
        job_executor: "JobExecutor",
        num_workers: int = 5,
    ):
        self.job_service = job_service
        self.queue = queue_manager
        self.executor = job_executor
        self.num_workers = num_workers
        
        self.thread_pool: Optional[ThreadPoolExecutor] = None
        self.workers: List[str] = []
        self.running = False
        self.logger = logger
        
        # Graceful shutdown 신호
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    async def start(self):
        """워커 풀 시작"""
        self.running = True
        self.thread_pool = ThreadPoolExecutor(max_workers=self.num_workers)
        
        # 각 워커를 스레드에서 실행
        loop = asyncio.get_event_loop()
        futures = []
        
        for i in range(self.num_workers):
            worker_id = f"worker-{i}"
            self.workers.append(worker_id)
            
            # asyncio.run_in_executor로 동기 워커를 async 환경에서 실행
            future = loop.run_in_executor(
                self.thread_pool,
                self._worker_loop,
                worker_id
            )
            futures.append(future)
        
        self.logger.info(f"Worker pool started with {self.num_workers} workers")
    
    async def stop(self, timeout: int = 30):
        """워커 풀 종료 (graceful shutdown)"""
        self.running = False
        self.logger.info("Initiating graceful shutdown of worker pool...")
        
        # 진행 중인 작업 완료 대기 (최대 timeout초)
        if self.thread_pool:
            self.thread_pool.shutdown(wait=True, timeout=timeout)
        
        self.logger.info("Worker pool stopped")
    
    # ── Private Methods ──
    
    def _worker_loop(self, worker_id: str):
        """워커 메인 루프 (스레드에서 실행)"""
        self.logger.info(f"{worker_id} started")
        
        while self.running:
            try:
                # 큐에서 Job을 꺼냄 (blocking, timeout=5초)
                job_dict = asyncio.run(
                    self.queue.dequeue_job(worker_id, timeout=5)
                )
                
                if not job_dict:
                    continue
                
                job_id = job_dict["id"]
                
                # Job 실행
                self.logger.info(f"{worker_id} processing job {job_id}")
                
                try:
                    # 실제 작업 실행 (JobExecutor)
                    result = asyncio.run(
                        self.executor.execute(job_dict)
                    )
                    
                    # 성공
                    asyncio.run(
                        self.job_service.mark_job_success(
                            UUID(job_id),
                            result
                        )
                    )
                    asyncio.run(
                        self.queue.mark_success(job_id, result)
                    )
                    
                    self.logger.info(f"{worker_id} completed job {job_id}")
                
                except Exception as e:
                    # 실패 처리
                    self.logger.error(
                        f"{worker_id} job {job_id} failed: {str(e)}"
                    )
                    
                    retries = job_dict.get("retries", 0)
                    
                    # Job을 다시 큐에 추가 (재시도)
                    if retries < 3:
                        job_dict["retries"] = retries + 1
                        asyncio.run(
                            self.queue.enqueue_job(
                                Job(**job_dict)
                            )
                        )
                    else:
                        # DLQ로 이동
                        asyncio.run(
                            self.job_service.mark_job_failed(
                                UUID(job_id),
                                str(e),
                                retries
                            )
                        )
                
                # 하트비트 업데이트
                asyncio.run(
                    self.queue.worker_heartbeat(worker_id)
                )
            
            except Exception as e:
                self.logger.error(f"{worker_id} critical error: {e}", exc_info=True)
                # 워커는 계속 돌음 (graceful recovery)
        
        self.logger.info(f"{worker_id} stopped")
    
    def _signal_handler(self, signum, frame):
        """SIGTERM/SIGINT 신호 처리"""
        self.logger.info(f"Signal {signum} received, shutting down...")
        self.running = False
```

### 2.5 Job Executor (`app/services/job_executor.py`)

```python
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class JobExecutor:
    """실제 작업을 실행하는 엔진"""
    
    def __init__(
        self,
        proposal_service,
        document_ingestion_service,
        hwpx_service,
        pptx_builder,
    ):
        self.proposal_svc = proposal_service
        self.ingestion_svc = document_ingestion_service
        self.hwpx_svc = hwpx_service
        self.pptx = pptx_builder
        self.logger = logger
    
    async def execute(self, job_dict: dict) -> dict:
        """Job 실행"""
        job_type = job_dict.get("type")
        payload = job_dict.get("payload", {})
        proposal_id = job_dict.get("proposal_id")
        
        self.logger.info(f"Executing job {job_dict['id']} (type={job_type})")
        
        try:
            if job_type == "step4a_diagnosis":
                result = await self._step4a_diagnosis(proposal_id, payload)
            elif job_type == "step4a_regenerate":
                result = await self._step4a_regenerate(proposal_id, payload)
            elif job_type == "step4b_pricing":
                result = await self._step4b_pricing(proposal_id, payload)
            elif job_type == "step5a_pptx":
                result = await self._step5a_pptx(proposal_id, payload)
            elif job_type == "step5b_submission":
                result = await self._step5b_submission(proposal_id, payload)
            else:
                raise ValueError(f"Unknown job type: {job_type}")
            
            return {"success": True, "data": result}
        
        except Exception as e:
            self.logger.error(f"Job execution failed: {e}", exc_info=True)
            raise
    
    # ── Task Handlers ──
    
    async def _step4a_diagnosis(self, proposal_id: str, payload: dict) -> dict:
        """
        STEP 4A: 정확도 검증
        
        payload:
          - section_ids: list[str]  # 검증할 섹션 목록
          - model: str              # 사용할 모델 (default: sonnet)
        """
        section_ids = payload.get("section_ids", [])
        model = payload.get("model", "sonnet")
        
        self.logger.info(f"Running STEP 4A diagnosis for {len(section_ids)} sections")
        
        # 1. 제안서 조회
        proposal = await self.proposal_svc.get_proposal(proposal_id)
        
        # 2. Document Ingestion의 정확도 검증 엔진 호출
        result = await self.ingestion_svc.run_accuracy_validator(
            proposal_id=proposal_id,
            section_ids=section_ids,
            model=model,
        )
        
        return result
    
    async def _step4a_regenerate(self, proposal_id: str, payload: dict) -> dict:
        """
        STEP 4A: 섹션 재작성
        
        payload:
          - section_ids: list[str]
          - feedback: str           # 사용자 피드백
        """
        section_ids = payload.get("section_ids", [])
        feedback = payload.get("feedback", "")
        
        self.logger.info(f"Regenerating {len(section_ids)} sections")
        
        # LangGraph에서 proposal_nodes.py의 재작성 로직 호출
        result = await self.proposal_svc.regenerate_sections(
            proposal_id=proposal_id,
            section_ids=section_ids,
            feedback=feedback,
        )
        
        return result
    
    async def _step4b_pricing(self, proposal_id: str, payload: dict) -> dict:
        """STEP 4B: 입찰가 산정"""
        # bid_plan.py의 로직 호출
        result = await self.proposal_svc.calculate_pricing(
            proposal_id=proposal_id,
            **payload
        )
        return result
    
    async def _step5a_pptx(self, proposal_id: str, payload: dict) -> dict:
        """STEP 5A: PPT 생성"""
        self.logger.info("Building PPTX presentation")
        
        # pptx_builder.py의 로직 호출
        pptx_bytes = await self.pptx.build(
            proposal_id=proposal_id,
            **payload
        )
        
        # S3에 저장
        s3_url = await self.proposal_svc.save_artifact(
            proposal_id=proposal_id,
            name="presentation.pptx",
            content=pptx_bytes,
            mime_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        
        return {"pptx_url": s3_url}
    
    async def _step5b_submission(self, proposal_id: str, payload: dict) -> dict:
        """STEP 5B: 제출서류 준비"""
        result = await self.proposal_svc.prepare_submission(
            proposal_id=proposal_id,
            **payload
        )
        return result
```

---

## 3. 데이터베이스 스키마

### 3.1 신규 테이블

```sql
-- ============================================
-- §8-1. Job 테이블
-- ============================================

CREATE TABLE jobs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    proposal_id UUID NOT NULL REFERENCES proposals(id) ON DELETE CASCADE,
    step        VARCHAR(10) NOT NULL,  -- "4a", "4b", "5a", "5b", "6"
    type        VARCHAR(50) NOT NULL,  -- "step4a_diagnosis", "step4a_regenerate" 등
    
    status      VARCHAR(20) DEFAULT 'pending',  -- pending | running | success | failed | cancelled
    priority    INTEGER DEFAULT 1,               -- 0=high, 1=normal, 2=low
    
    -- 입력 & 출력
    payload     JSONB DEFAULT '{}'::jsonb,      -- 작업 파라미터 (< 1MB)
    result      JSONB,                          -- 결과 (성공 시)
    error       TEXT,                           -- 에러 메시지
    
    -- 재시도
    retries     INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- 타이밍
    created_at  TIMESTAMPTZ DEFAULT now(),
    started_at  TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    duration_seconds NUMERIC(10, 2),  -- NULL 계산: completed_at - started_at
    
    -- 추적
    created_by  UUID NOT NULL REFERENCES users(id),
    assigned_worker_id VARCHAR(50),  -- "worker-0" 등
    
    -- 태그 (필터링용)
    tags        JSONB DEFAULT '{}'::jsonb,
    
    created_at_idx TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_jobs_proposal_id ON jobs(proposal_id);
CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_step ON jobs(step);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_priority_status ON jobs(priority, status);  -- 큐 쿼리용

CREATE TRIGGER update_jobs_updated_at BEFORE UPDATE ON jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- §8-2. Job Result 테이블 (결과 이력)
-- ============================================

CREATE TABLE job_results (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id      UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    result_data JSONB NOT NULL,  -- 상세 결과
    saved_at    TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_job_results_job_id ON job_results(job_id);

-- ============================================
-- §8-3. Job Metrics 테이블 (성과 추적)
-- ============================================

CREATE TABLE job_metrics (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id      UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    step        VARCHAR(10),  -- "4a", "4b" 등
    type        VARCHAR(50),  -- 작업 타입
    status      VARCHAR(20),  -- "success", "failed"
    
    duration_seconds NUMERIC(10, 2),
    memory_mb   NUMERIC(8, 2),  -- 메모리 사용량
    cpu_percent NUMERIC(5, 2),  -- CPU 사용률
    
    worker_id   VARCHAR(50),
    recorded_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_job_metrics_recorded_at ON job_metrics(recorded_at DESC);
CREATE INDEX idx_job_metrics_step ON job_metrics(step);

-- ============================================
-- §8-4. Job Events 테이블 (감시 로그)
-- ============================================

CREATE TABLE job_events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id      UUID NOT NULL REFERENCES jobs(id) ON DELETE CASCADE,
    event_type  VARCHAR(50),  -- "created", "started", "progress", "completed", "failed"
    
    details     JSONB,        -- {progress: 50, message: "..."}
    occurred_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_job_events_job_id ON job_events(job_id);
CREATE INDEX idx_job_events_occurred_at ON job_events(occurred_at DESC);

-- ============================================
-- §8-5. 자동 정리 정책
-- ============================================

-- 7일 이상 된 완료/실패 job 자동 삭제 (아카이빙 후)
-- 이는 별도의 cron job으로 관리
```

### 3.2 기존 테이블 확장 (선택)

```sql
-- proposals 테이블에 추가할 칼럼 (선택)
ALTER TABLE proposals ADD COLUMN
    job_queue_enabled BOOLEAN DEFAULT true;  -- 비동기 큐 사용 여부
```

---

## 4. API 엔드포인트 명세

### 4.1 동기 API

```
POST /api/jobs
├─ Request:
│   {
│     "proposal_id": "uuid",
│     "type": "step4a_diagnosis",
│     "payload": {
│       "section_ids": ["s1", "s2"],
│       "model": "sonnet"
│     },
│     "priority": 0
│   }
├─ Response (202 Accepted):
│   {
│     "job_id": "uuid",
│     "status": "pending",
│     "queue_position": 3,
│     "estimated_wait_seconds": 90
│   }
└─ Errors: 400 (invalid payload), 404 (proposal not found)

GET /api/jobs/{job_id}/status
├─ Response (200):
│   {
│     "id": "uuid",
│     "status": "running",
│     "progress": 45.5,
│     "retries": 0,
│     "started_at": "2026-04-20T...",
│     "estimated_completion": "2026-04-20T..."
│   }
└─ Errors: 404 (job not found)

GET /api/jobs/{job_id}/result
├─ Response (200):
│   {
│     "id": "uuid",
│     "result": {...},
│     "duration_seconds": 45.2,
│     "completed_at": "2026-04-20T..."
│   }
├─ Errors: 404 (not found), 409 (not completed)
└─ Note: 결과는 SUCCESS 상태일 때만 반환

POST /api/jobs/{job_id}/cancel
├─ Request: {}
├─ Response (200):
│   {"cancelled": true}
└─ Errors: 409 (cannot cancel running job)

POST /api/jobs/{job_id}/retry (수동 재시도)
├─ Request: {}
├─ Response (202):
│   {"job_id": "uuid", "status": "pending", "retry_attempt": 1}
└─ Note: DLQ 작업에만 적용

GET /api/jobs?proposal_id=uuid&status=running&limit=20&offset=0
├─ Response (200):
│   {
│     "total": 100,
│     "items": [
│       {"id": "...", "status": "running", "progress": 45}
│     ]
│   }

GET /api/jobs/dlq
├─ Response (200):
│   {
│     "total": 5,
│     "items": [
│       {
│         "job_id": "uuid",
│         "error": "timeout after 300s",
│         "failed_at": "2026-04-20T...",
│         "retries_exhausted": 3
│       }
│     ]
│   }
```

### 4.2 WebSocket API

```
WebSocket /ws/jobs/{job_id}
├─ Connection:
│   Client initiates: GET /ws/jobs/uuid with Upgrade header
│
├─ Messages (Server → Client):
│   {
│     "type": "status",
│     "status": "running",
│     "progress": 45.5,
│     "timestamp": "2026-04-20T..."
│   }
│   
│   {
│     "type": "completion",
│     "status": "success",
│     "result": {...},
│     "duration_seconds": 45.2
│   }
│   
│   {
│     "type": "error",
│     "error": "timeout",
│     "message": "Job exceeded 300s timeout"
│   }
│
├─ Heartbeat:
│   - Server sends status every 10 seconds
│   - Client should disconnect if no message for 30s (timeout)
│
└─ Reconnection:
    - Client reconnects automatically using job_id
    - Server resends last known status
```

---

## 5. 구현 전략

### 5.1 3단계 구현

**Phase 1: 기반시설 (4/23~24)**
- Job Model + DB 스키마
- Queue Manager (Redis)
- Job Service (CRUD)

**Phase 2: 실행 엔진 (4/25~26)**
- Worker Pool + Job Executor
- API Routes (동기)
- WebSocket /ws/jobs/{job_id}

**Phase 3: 검증 & 최적화 (4/27~28)**
- 단위 테스트 (40개)
- 통합테스트 (20개)
- 성능 튜닝 + 모니터링

### 5.2 의존성 관리

**신규 패키지:**
```python
# pyproject.toml에 추가
aioredis = "^2.0"
redis = "^5.0"      # (sync 버전도 필요시)
```

**기존 패키지 활용:**
- FastAPI (라우트)
- asyncpg (DB 접근, 기존)
- Supabase (기존)

### 5.3 성능 최적화 팁

| 병목 | 해결책 |
|------|--------|
| Redis 응답 지연 | 로컬 Redis 또는 In-Memory Queue (fallback) |
| DB 쿼리 지연 | 배치 쓰기 (100개 단위) + 캐시 (job_state) |
| 메모리 누수 | 주기적 워커 재시작 (24h) + 이력 자동 삭제 (7일) |
| 동시성 충돌 | Redis SETEX lock (job_id 기반) |

---

## 6. 에러 처리 & 복구

### 6.1 장애 시나리오

| 장애 | 감지 | 대응 |
|------|------|------|
| **Redis 연결 실패** | QueueManager.connect() exception | Local In-Memory Queue fallback |
| **Worker 크래시** | _worker_loop exception | 자동 재시작 (supervisor 또는 systemd) |
| **Job 타임아웃** | duration > 300s | FAILED + DLQ 이동 |
| **DB 쓰기 실패** | update() exception | Redis에만 기록 (나중에 동기화) |
| **WebSocket 연결 끊김** | client disconnect | 클라이언트 재연결 시 last-known 상태 반환 |

### 6.2 Graceful Shutdown

```python
# 서버 종료 시 (SIGTERM)
1. 신규 Job 수신 중단 (accept=false)
2. 기존 Job 완료 대기 (최대 30초)
3. 큐 내용 Redis에 저장 (복구용)
4. 워커 스레드 종료
5. Redis/DB 연결 종료
```

---

## 7. 모니터링 & 가시성

### 7.1 메트릭 수집

```python
# job_metrics 테이블에 기록되는 메트릭
- duration_seconds: 처리 시간
- memory_mb: 메모리 사용
- cpu_percent: CPU 사용률
- status: success / failed
- worker_id: 담당 워커

# 대시보드 쿼리 (예)
SELECT 
    step,
    COUNT(*) as total,
    COUNT(CASE WHEN status='success' THEN 1) as success_count,
    AVG(CASE WHEN status='success' THEN duration_seconds END) as avg_duration,
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_seconds) as p95_duration
FROM job_metrics
WHERE recorded_at > now() - interval '24 hours'
GROUP BY step
```

### 7.2 알림 규칙

| 조건 | 액션 |
|------|------|
| Job 실패 (DLQ 이동) | Slack 알림 (관리자) |
| 큐 대기 시간 > 5분 | 경고 (모니터링) |
| 워커 하트비트 끊김 | 즉시 재시작 |
| Redis 응답 시간 > 100ms | 로그 기록 + 분석 |

---

## Appendix A: 설정 (config.py 추가)

```python
# JOB_QUEUE 섹션 추가
JOB_QUEUE = {
    "REDIS_URL": os.getenv("REDIS_URL", "redis://localhost:6379"),
    "NUM_WORKERS": int(os.getenv("JOB_QUEUE_WORKERS", 5)),
    "MAX_RETRIES": int(os.getenv("JOB_QUEUE_MAX_RETRIES", 3)),
    "JOB_TIMEOUT_SECONDS": int(os.getenv("JOB_TIMEOUT_SECONDS", 300)),
    "HEARTBEAT_INTERVAL": int(os.getenv("JOB_HEARTBEAT_INTERVAL", 10)),
    "RESULT_TTL_DAYS": int(os.getenv("JOB_RESULT_TTL_DAYS", 7)),
}
```

---

**문서 버전:** v1.0  
**마지막 수정:** 2026-04-20  
**다음 단계:** DO Phase 시작 (4/23)
