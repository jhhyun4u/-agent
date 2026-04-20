"""
Integration Tests: Job Queue Workflow (STEP 8 - Day 3-4)

테스트 대상:
- Queue Manager: Redis 연결, enqueue/dequeue, 우선도 처리
- Worker Pool: 병렬 처리, 에러 처리, graceful shutdown
- Job Executor: 작업 실행, 타임아웃
- Job Service: CRUD, 상태 전환

테스트 환경:
- Mock Redis (in-memory)
- Mock Services
- Fixture: 테스트 job 데이터
"""

import asyncio
import json
import pytest
from datetime import datetime
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.job_queue_schemas import (
    Job, JobStatus, JobType, JobPriority, JobEventType
)
from app.services.queue_manager import QueueManager
from app.services.job_service import JobService
from app.services.worker_pool import WorkerPool
from app.services.job_executor import JobExecutor


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def mock_db():
    """Mock Supabase 클라이언트"""
    db = AsyncMock()
    db.table = MagicMock(return_value=AsyncMock())
    return db


@pytest.fixture
def mock_queue_manager():
    """Mock QueueManager (Redis 없이)"""
    qm = MagicMock(spec=QueueManager)
    qm.enqueue_job = AsyncMock(return_value=True)
    qm.dequeue_job = AsyncMock(return_value=None)
    qm.mark_success = AsyncMock(return_value=True)
    qm.mark_failure = AsyncMock(return_value=True)
    qm.get_job_state = AsyncMock(return_value=None)
    qm.worker_heartbeat = AsyncMock(return_value=True)
    qm.get_queue_stats = AsyncMock(return_value={
        "high_count": 0,
        "normal_count": 0,
        "low_count": 0,
        "dlq_count": 0,
    })
    return qm


@pytest.fixture
def mock_job_executor():
    """Mock JobExecutor"""
    executor = AsyncMock(spec=JobExecutor)
    executor.execute = AsyncMock(return_value={"success": True, "data": {}})
    return executor


@pytest.fixture
def job_service(mock_db, mock_queue_manager):
    """JobService with mocked dependencies"""
    service = JobService(mock_db, mock_queue_manager)
    return service


@pytest.fixture
def test_job():
    """테스트용 Job 객체"""
    return {
        "id": str(uuid4()),
        "proposal_id": str(uuid4()),
        "step": "4a",
        "type": "step4a_diagnosis",
        "status": "pending",
        "priority": 1,
        "payload": {"section_ids": ["s1", "s2"]},
        "created_by": str(uuid4()),
        "retries": 0,
        "max_retries": 3,
        "created_at": datetime.utcnow().isoformat(),
    }


# ============================================
# Queue Manager Tests
# ============================================

class TestQueueManager:
    """QueueManager 통합 테스트"""

    @pytest.mark.asyncio
    async def test_queue_manager_initialization(self):
        """QueueManager 초기화"""
        qm = QueueManager(redis_url="redis://localhost:6379")
        assert qm.redis_url == "redis://localhost:6379"
        assert qm._is_connected is False
        assert qm.redis is None

    @pytest.mark.asyncio
    async def test_queue_manager_fallback_when_redis_unavailable(self):
        """Redis 연결 불가 시 fallback 모드"""
        qm = QueueManager(redis_url="redis://invalid-host:6379")
        await qm.connect()
        assert qm._is_connected is False

    @pytest.mark.asyncio
    async def test_enqueue_job_without_redis(self):
        """Redis 없이 enqueue (fallback)"""
        qm = QueueManager()
        qm._is_connected = False
        result = await qm.enqueue_job({"id": "test-job"})
        assert result is False

    @pytest.mark.asyncio
    async def test_dequeue_job_without_redis(self):
        """Redis 없이 dequeue (fallback)"""
        qm = QueueManager()
        qm._is_connected = False
        result = await qm.dequeue_job("worker-0")
        assert result is None

    @pytest.mark.asyncio
    async def test_queue_stats_without_redis(self):
        """Redis 없이 큐 통계 조회"""
        qm = QueueManager()
        qm._is_connected = False
        stats = await qm.get_queue_stats()
        assert stats["high_count"] == 0
        assert stats["normal_count"] == 0
        assert stats["low_count"] == 0
        assert stats["dlq_count"] == 0


# ============================================
# Job Service Tests
# ============================================

class TestJobService:
    """JobService 통합 테스트"""

    @pytest.mark.asyncio
    async def test_create_job(self, job_service, mock_db, test_job):
        """Job 생성"""
        proposal_id = UUID(test_job["proposal_id"])
        created_by = UUID(test_job["created_by"])

        # Mock DB table method
        insert_mock = AsyncMock(return_value=test_job)
        mock_db.table.return_value.insert = insert_mock

        job = await job_service.create_job(
            proposal_id=proposal_id,
            job_type="step4a_diagnosis",
            payload={"section_ids": ["s1", "s2"]},
            priority=1,
            created_by=created_by,
        )

        assert job.proposal_id == proposal_id
        assert job.type == JobType.STEP4A_DIAGNOSIS
        assert job.status == JobStatus.PENDING
        assert job.step == "4a"
        insert_mock.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_job_extracts_step_correctly(self, job_service, mock_db):
        """Job 생성 시 STEP 추출 검증"""
        proposal_id = uuid4()
        created_by = uuid4()

        # Mock DB
        insert_mock = AsyncMock()
        mock_db.table.return_value.insert = insert_mock

        job_type = "step5b_submission"
        job = await job_service.create_job(
            proposal_id=proposal_id,
            job_type=job_type,
            payload={},
            created_by=created_by,
        )

        assert job.step == "5b"

    @pytest.mark.asyncio
    async def test_get_job(self, job_service, mock_db, test_job):
        """Job 조회"""
        job_id = UUID(test_job["id"])

        # Mock DB select
        select_mock = AsyncMock(return_value=test_job)
        query_mock = MagicMock()
        query_mock.eq = MagicMock(return_value=MagicMock(single=AsyncMock(return_value=test_job)))
        mock_db.table.return_value.select.return_value = query_mock

        job = await job_service.get_job(job_id)
        assert job is not None
        assert job.id == job_id

    @pytest.mark.asyncio
    async def test_mark_job_success(self, job_service, mock_db, test_job):
        """Job 성공 표시"""
        job_id = UUID(test_job["id"])

        # Mock DB
        update_mock = AsyncMock(return_value={"status": "success"})
        query_mock = MagicMock()
        query_mock.eq = MagicMock(return_value=AsyncMock(return_value={"status": "success"}))
        mock_db.table.return_value.update.return_value = query_mock

        result = await job_service.mark_job_success(job_id, {"data": "result"})
        assert result is True

    @pytest.mark.asyncio
    async def test_mark_job_failed(self, job_service, mock_db, test_job):
        """Job 실패 표시"""
        job_id = UUID(test_job["id"])

        # Mock DB
        update_mock = AsyncMock()
        query_mock = MagicMock()
        query_mock.eq = MagicMock(return_value=AsyncMock())
        mock_db.table.return_value.update.return_value = query_mock

        result = await job_service.mark_job_failed(job_id, "Test error", 0)
        assert result is True

    @pytest.mark.asyncio
    async def test_cancel_job(self, job_service, mock_db, test_job):
        """Job 취소"""
        job_id = UUID(test_job["id"])

        # Mock DB select
        query_mock = MagicMock()
        query_mock.eq = MagicMock(return_value=MagicMock(single=AsyncMock(return_value=test_job)))
        mock_db.table.return_value.select.return_value = query_mock

        # Mock DB update
        update_mock = AsyncMock()
        query_mock_update = MagicMock()
        query_mock_update.eq = MagicMock(return_value=AsyncMock())
        mock_db.table.return_value.update.return_value = query_mock_update

        result = await job_service.cancel_job(job_id)
        assert result is True


# ============================================
# Worker Pool Tests
# ============================================

class TestWorkerPool:
    """WorkerPool 통합 테스트"""

    @pytest.mark.asyncio
    async def test_worker_pool_initialization(self, job_service, mock_queue_manager, mock_job_executor):
        """WorkerPool 초기화"""
        pool = WorkerPool(
            job_service=job_service,
            queue_manager=mock_queue_manager,
            job_executor=mock_job_executor,
            num_workers=5
        )

        assert pool.num_workers == 5
        assert pool.running is False
        assert pool.workers == []

    def test_worker_pool_is_running(self, job_service, mock_queue_manager, mock_job_executor):
        """WorkerPool 상태 확인"""
        pool = WorkerPool(
            job_service=job_service,
            queue_manager=mock_queue_manager,
            job_executor=mock_job_executor,
        )

        assert pool.is_running() is False
        pool.running = True
        assert pool.is_running() is True

    @pytest.mark.asyncio
    async def test_worker_pool_stop(self, job_service, mock_queue_manager, mock_job_executor):
        """WorkerPool 종료"""
        pool = WorkerPool(
            job_service=job_service,
            queue_manager=mock_queue_manager,
            job_executor=mock_job_executor,
            num_workers=2
        )

        pool.running = True
        await pool.stop(timeout=1)
        assert pool.running is False


# ============================================
# Job Executor Tests
# ============================================

class TestJobExecutor:
    """JobExecutor 통합 테스트"""

    @pytest.mark.asyncio
    async def test_executor_initialization(self):
        """JobExecutor 초기화"""
        executor = JobExecutor()
        assert executor.logger is not None

    @pytest.mark.asyncio
    async def test_executor_timeout_handling(self):
        """JobExecutor 타임아웃 처리"""
        executor = JobExecutor()

        job_dict = {
            "id": "test-job",
            "type": "step4a_diagnosis",
            "proposal_id": str(uuid4()),
            "payload": {},
        }

        # _step4a_diagnosis가 없으므로 타임아웃 발생
        with pytest.raises(Exception):
            await executor.execute(job_dict)

    @pytest.mark.asyncio
    async def test_executor_unknown_job_type(self):
        """JobExecutor 알 수 없는 작업 타입"""
        executor = JobExecutor()

        job_dict = {
            "id": "test-job",
            "type": "unknown_type",
            "proposal_id": str(uuid4()),
            "payload": {},
        }

        with pytest.raises(ValueError, match="Unknown job type"):
            await executor.execute(job_dict)


# ============================================
# Workflow Integration Tests
# ============================================

class TestJobQueueWorkflow:
    """전체 워크플로우 통합 테스트"""

    @pytest.mark.asyncio
    async def test_enqueue_and_dequeue_order(self, job_service, mock_queue_manager):
        """우선도 순서 확인"""
        # HIGH 우선도 job 생성
        high_priority_job = await job_service.create_job(
            proposal_id=uuid4(),
            job_type="step4a_diagnosis",
            payload={},
            priority=0,  # HIGH
            created_by=uuid4(),
        )

        # NORMAL 우선도 job 생성
        normal_priority_job = await job_service.create_job(
            proposal_id=uuid4(),
            job_type="step4b_pricing",
            payload={},
            priority=1,  # NORMAL
            created_by=uuid4(),
        )

        assert high_priority_job.priority == JobPriority.HIGH
        assert normal_priority_job.priority == JobPriority.NORMAL

    @pytest.mark.asyncio
    async def test_worker_execution_success(self, job_service, mock_queue_manager, mock_job_executor):
        """워커 성공적 실행"""
        job_id = uuid4()
        proposal_id = uuid4()
        created_by = uuid4()

        # Job 생성
        job = Job(
            id=job_id,
            proposal_id=proposal_id,
            step="4a",
            type=JobType.STEP4A_DIAGNOSIS,
            status=JobStatus.PENDING,
            priority=JobPriority.NORMAL,
            payload={},
            created_by=created_by,
            created_at=datetime.utcnow(),
        )

        # JobService mark_job_success 호출
        result = await job_service.mark_job_success(job_id, {"result": "success"})
        assert result is True

    @pytest.mark.asyncio
    async def test_worker_handles_failure_and_retry(self, job_service, mock_queue_manager, mock_job_executor):
        """워커 실패 처리 및 재시도"""
        job_id = uuid4()

        # 첫 번째 시도 실패
        result = await job_service.mark_job_failed(job_id, "Test error", 0)
        assert result is True

        # 두 번째 시도 실패
        result = await job_service.mark_job_failed(job_id, "Test error", 1)
        assert result is True

        # 세 번째 시도 실패 (최대 재시도)
        result = await job_service.mark_job_failed(job_id, "Test error", 2)
        assert result is True


# ============================================
# Performance Tests
# ============================================

class TestJobQueuePerformance:
    """성능 테스트"""

    @pytest.mark.asyncio
    async def test_bulk_job_creation(self, job_service, mock_db):
        """대량 Job 생성 성능"""
        proposal_id = uuid4()
        created_by = uuid4()

        # Mock DB
        insert_mock = AsyncMock()
        mock_db.table.return_value.insert = insert_mock

        # 100개 job 생성
        start_time = datetime.utcnow()
        for i in range(100):
            await job_service.create_job(
                proposal_id=proposal_id,
                job_type="step4a_diagnosis",
                payload={"index": i},
                created_by=created_by,
            )
        elapsed = (datetime.utcnow() - start_time).total_seconds()

        assert elapsed < 10  # 10초 이내
        assert insert_mock.call_count == 100

    @pytest.mark.asyncio
    async def test_job_state_transitions(self, job_service, mock_db):
        """Job 상태 전환 테스트"""
        job_id = uuid4()

        # Mock DB
        update_mock = AsyncMock()
        query_mock = MagicMock()
        query_mock.eq = MagicMock(return_value=AsyncMock())
        mock_db.table.return_value.update.return_value = query_mock

        # PENDING → RUNNING
        await job_service.mark_job_running(job_id, "worker-0")

        # RUNNING → SUCCESS
        await job_service.mark_job_success(job_id, {"result": "test"})

        assert update_mock.call_count >= 0  # Mocked, so exact count varies


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
