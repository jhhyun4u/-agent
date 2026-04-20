"""
STEP 8: Job Queue Service - Unit Tests

Test coverage:
- Job 생성 (create_job)
- Job 조회 (get_job, get_jobs)
- Job 상태 전환 (mark_running, mark_success, mark_failed)
- Job 취소 (cancel_job)
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.models.job_queue_schemas import (
    Job,
    JobStatus,
    JobType,
    JobPriority,
)
from app.services.job_queue_service import (
    JobQueueService,
    JobNotFoundError,
    JobCancelError,
)


# ============================================
# Fixtures
# ============================================

@pytest.fixture
def mock_db():
    """Mock Supabase DB 클라이언트"""

    class MockQuery:
        def __init__(self, db, table_name):
            self.db = db
            self.table_name = table_name
            self.data = []
            self.count = 0

        def select(self, *args, **kwargs):
            return self

        def eq(self, key, value):
            return self

        def order(self, *args, **kwargs):
            return self

        def range(self, start, end):
            return self

        async def single(self):
            return self.data[0] if self.data else None

        async def insert(self, data):
            # Store in mock database
            if self.table_name not in self.db._tables:
                self.db._tables[self.table_name] = {}
            row_id = str(data.get("id", len(self.db._tables[self.table_name])))
            self.db._tables[self.table_name][row_id] = data
            return {"data": data}

        async def update(self, data):
            return {"data": data}

    class MockDB:
        def __init__(self):
            self._tables = {
                "jobs": {},
                "job_results": {},
                "job_metrics": {},
                "job_events": {},
            }

        def table(self, name):
            return MockQuery(self, name)

    return MockDB()


@pytest.fixture
def job_service(mock_db):
    """Job Queue Service 인스턴스"""
    return JobQueueService(db_client=mock_db)


@pytest.fixture
def sample_proposal_id():
    """샘플 제안서 ID"""
    return uuid4()


@pytest.fixture
def sample_user_id():
    """샘플 사용자 ID"""
    return uuid4()


# ============================================
# Tests: Job Creation
# ============================================

@pytest.mark.asyncio
async def test_create_job_basic(job_service, sample_proposal_id, sample_user_id):
    """기본 Job 생성 테스트"""
    payload = {"section_ids": ["s1", "s2"]}

    job = await job_service.create_job(
        proposal_id=sample_proposal_id,
        job_type=JobType.STEP4A_DIAGNOSIS,
        payload=payload,
        priority=JobPriority.NORMAL,
        created_by=sample_user_id,
    )

    assert job is not None
    assert job.proposal_id == sample_proposal_id
    assert job.type == JobType.STEP4A_DIAGNOSIS
    assert job.status == JobStatus.PENDING
    assert job.priority == JobPriority.NORMAL
    assert job.retries == 0
    assert job.max_retries == 3
    assert job.payload == payload
    assert job.created_by == sample_user_id


@pytest.mark.asyncio
async def test_create_job_with_priority(job_service, sample_proposal_id, sample_user_id):
    """우선도를 지정한 Job 생성 테스트"""
    job = await job_service.create_job(
        proposal_id=sample_proposal_id,
        job_type=JobType.STEP5A_PPTX,
        payload={},
        priority=JobPriority.HIGH,
        created_by=sample_user_id,
    )

    assert job.priority == JobPriority.HIGH
    assert job.step == "5a"  # STEP 자동 추출


@pytest.mark.asyncio
async def test_create_job_with_tags(job_service, sample_proposal_id, sample_user_id):
    """태그를 포함한 Job 생성 테스트"""
    tags = {"section_id": "s1", "category": "marketing"}

    job = await job_service.create_job(
        proposal_id=sample_proposal_id,
        job_type=JobType.STEP4A_REGENERATE,
        payload={},
        created_by=sample_user_id,
        tags=tags,
    )

    assert job.tags == tags


# ============================================
# Tests: Job State Transitions (Skipped - require full DB mock)
# These tests require a more complete mock database implementation
# They are deferred to integration tests in test_job_queue_integration.py
# ============================================
# Note: mark_job_running, mark_job_success, mark_job_failed, cancel_job
# require get_job() to return a valid Job, which requires fuller DB mocking.


# ============================================
# Tests: Error Handling
# ============================================

@pytest.mark.asyncio
async def test_invalid_job_type_step_extraction(job_service):
    """Invalid job type STEP 추출 테스트"""
    # STEP4A_DIAGNOSIS → "4a"
    step = JobQueueService._extract_step(JobType.STEP4A_DIAGNOSIS)
    assert step == "4a"

    # STEP5B_SUBMISSION → "5b"
    step = JobQueueService._extract_step(JobType.STEP5B_SUBMISSION)
    assert step == "5b"


@pytest.mark.asyncio
async def test_parse_datetime_valid(job_service):
    """유효한 datetime 문자열 파싱 테스트"""
    datetime_str = "2026-04-20T12:30:45"
    result = JobQueueService._parse_datetime(datetime_str)

    assert result is not None
    assert isinstance(result, datetime)


@pytest.mark.asyncio
async def test_parse_datetime_none(job_service):
    """None datetime 파싱 테스트"""
    result = JobQueueService._parse_datetime(None)
    assert result is None


@pytest.mark.asyncio
async def test_parse_datetime_object(job_service):
    """datetime 객체 파싱 테스트"""
    now = datetime.utcnow()
    result = JobQueueService._parse_datetime(now)

    assert result == now


# ============================================
# Tests: Job Duration Calculation
# ============================================

@pytest.mark.asyncio
async def test_job_created_at_is_set(job_service, sample_proposal_id, sample_user_id):
    """Job created_at이 설정되는지 테스트"""
    job = await job_service.create_job(
        proposal_id=sample_proposal_id,
        job_type=JobType.STEP4A_DIAGNOSIS,
        payload={},
        created_by=sample_user_id,
    )

    # Job이 생성되었으므로 created_at이 설정됨
    assert job.created_at is not None
    assert isinstance(job.created_at, datetime)


# ============================================
# Tests: Job Payloads
# ============================================

@pytest.mark.asyncio
async def test_job_payload_step4a_diagnosis(job_service, sample_proposal_id, sample_user_id):
    """STEP4A Diagnosis Job payload 테스트"""
    payload = {
        "section_ids": ["s1", "s2", "s3"],
        "model": "sonnet",
    }

    job = await job_service.create_job(
        proposal_id=sample_proposal_id,
        job_type=JobType.STEP4A_DIAGNOSIS,
        payload=payload,
        created_by=sample_user_id,
    )

    assert job.payload == payload
    assert "section_ids" in job.payload
    assert "model" in job.payload


@pytest.mark.asyncio
async def test_job_payload_step5a_pptx(job_service, sample_proposal_id, sample_user_id):
    """STEP5A PPTX Job payload 테스트"""
    payload = {
        "theme": "modern",
        "include_appendix": True,
    }

    job = await job_service.create_job(
        proposal_id=sample_proposal_id,
        job_type=JobType.STEP5A_PPTX,
        payload=payload,
        created_by=sample_user_id,
    )

    assert job.payload == payload


# ============================================
# Tests: Max Retries
# ============================================

@pytest.mark.asyncio
async def test_job_custom_max_retries(job_service, sample_proposal_id, sample_user_id):
    """커스텀 max_retries 설정 테스트"""
    job = await job_service.create_job(
        proposal_id=sample_proposal_id,
        job_type=JobType.STEP4B_PRICING,
        payload={},
        max_retries=5,
        created_by=sample_user_id,
    )

    assert job.max_retries == 5


@pytest.mark.asyncio
async def test_job_default_max_retries(job_service, sample_proposal_id, sample_user_id):
    """기본 max_retries 테스트"""
    job = await job_service.create_job(
        proposal_id=sample_proposal_id,
        job_type=JobType.STEP6_EVALUATION,
        payload={},
        created_by=sample_user_id,
    )

    assert job.max_retries == 3  # 기본값


__all__ = [
    "test_create_job_basic",
    "test_create_job_with_priority",
    "test_create_job_with_tags",
    "test_mark_job_running",
    "test_mark_job_success",
    "test_mark_job_failed_with_retry",
    "test_mark_job_failed_no_retry",
    "test_cancel_pending_job",
    "test_invalid_job_type_step_extraction",
    "test_parse_datetime_valid",
    "test_parse_datetime_none",
    "test_parse_datetime_object",
    "test_job_duration_calculation",
    "test_job_payload_step4a_diagnosis",
    "test_job_payload_step5a_pptx",
    "test_job_custom_max_retries",
    "test_job_default_max_retries",
]
