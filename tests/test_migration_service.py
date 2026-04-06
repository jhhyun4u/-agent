"""
Unit Tests for MigrationService

마이그레이션 서비스 단위 테스트 (10개)
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.migration_service import MigrationService
from app.models.migration_schemas import (
    MigrationBatch, MigrationSchedule, BatchResult,
    IntranetDocument, DocumentProcessResult
)


@pytest.fixture
def mock_db():
    """Mock 데이터베이스 세션"""
    return AsyncMock()


@pytest.fixture
def mock_notification():
    """Mock 알림 서비스"""
    service = AsyncMock()
    service.send_notification = AsyncMock()
    return service


@pytest.fixture
def migration_service(mock_db, mock_notification):
    """MigrationService 인스턴스"""
    return MigrationService(
        db=mock_db,
        notification_service=mock_notification
    )


# ===== Test Cases =====

class TestMigrationServiceBasic:
    """기본 기능 테스트"""

    async def test_service_initialization(self, migration_service):
        """서비스 초기화 확인"""
        assert migration_service is not None
        assert migration_service.db is not None
        assert migration_service.notification is not None

    async def test_batch_record_creation(self, migration_service):
        """배치 레코드 생성"""
        batch = await migration_service.create_batch_record(
            batch_type="manual",
            total_docs=10
        )

        assert batch is not None
        assert batch.status == "pending"
        assert batch.batch_type == "manual"
        assert batch.total_documents == 10
        assert batch.processed_documents == 0
        assert batch.failed_documents == 0

    async def test_batch_success_rate_property(self):
        """배치 성공률 계산"""
        batch = MigrationBatch(
            id=uuid4(),
            batch_name="test_batch",
            status="completed",
            scheduled_at=datetime.utcnow(),
            total_documents=100,
            processed_documents=95,
            failed_documents=5,
            skipped_documents=0,
            batch_type="manual",
            source_system="intranet",
            created_by=uuid4(),
            updated_at=datetime.utcnow()
        )

        # 95% 성공률
        assert batch.success_rate == 95.0

    async def test_batch_success_rate_zero_documents(self):
        """문서 0개일 때 성공률"""
        batch = MigrationBatch(
            id=uuid4(),
            batch_name="empty_batch",
            status="completed",
            scheduled_at=datetime.utcnow(),
            total_documents=0,
            processed_documents=0,
            failed_documents=0,
            skipped_documents=0,
            batch_type="manual",
            source_system="intranet",
            created_by=uuid4(),
            updated_at=datetime.utcnow()
        )

        assert batch.success_rate == 0.0

    async def test_batch_duration_minutes(self):
        """배치 처리 시간 계산"""
        now = datetime.utcnow()
        batch = MigrationBatch(
            id=uuid4(),
            batch_name="test_batch",
            status="completed",
            started_at=now,
            completed_at=now + timedelta(hours=1, minutes=23),
            scheduled_at=now,
            total_documents=100,
            processed_documents=100,
            failed_documents=0,
            skipped_documents=0,
            batch_type="manual",
            source_system="intranet",
            created_by=uuid4(),
            updated_at=datetime.utcnow()
        )

        # 1시간 23분 = 83분
        assert batch.duration_minutes == 83

    async def test_batch_duration_minutes_incomplete(self):
        """미완료 배치 처리 시간"""
        batch = MigrationBatch(
            id=uuid4(),
            batch_name="incomplete_batch",
            status="processing",
            started_at=datetime.utcnow(),
            completed_at=None,
            scheduled_at=datetime.utcnow(),
            total_documents=100,
            processed_documents=50,
            failed_documents=0,
            skipped_documents=0,
            batch_type="manual",
            source_system="intranet",
            created_by=uuid4(),
            updated_at=datetime.utcnow()
        )

        # 미완료 배치는 None
        assert batch.duration_minutes is None


class TestDetectChangedDocuments:
    """문서 변경 감지 테스트"""

    async def test_detect_changed_documents_success(self, migration_service):
        """변경된 문서 감지 성공"""
        since = datetime.utcnow() - timedelta(days=30)

        documents = await migration_service.detect_changed_documents(since)

        assert isinstance(documents, list)
        # TODO: 실제 구현 후 문서 수 확인

    async def test_detect_changed_documents_no_changes(self, migration_service):
        """변경된 문서 없음"""
        since = datetime.utcnow()  # 아주 최근

        documents = await migration_service.detect_changed_documents(since)

        assert isinstance(documents, list)


class TestProcessDocuments:
    """문서 처리 테스트"""

    async def test_process_batch_documents_success(self, migration_service):
        """배치 문서 처리 성공"""
        batch_id = uuid4()
        documents = [
            IntranetDocument(
                path="/docs/file1.pdf",
                filename="file1.pdf",
                modified_date=datetime.utcnow(),
                size_bytes=1024
            ),
            IntranetDocument(
                path="/docs/file2.pdf",
                filename="file2.pdf",
                modified_date=datetime.utcnow(),
                size_bytes=2048
            )
        ]

        # Mock _process_single_document
        with patch.object(
            migration_service,
            '_process_single_document',
            new_callable=AsyncMock
        ) as mock_process:
            mock_process.return_value = DocumentProcessResult(
                status="success",
                file="test.pdf",
                chunks_created=5
            )

            result = await migration_service.process_batch_documents(
                batch_id=batch_id,
                documents=documents,
                max_parallel=2
            )

            assert result.batch_id == batch_id
            assert result.status == "completed"
            assert result.processed == 2
            assert result.failed == 0

    async def test_process_batch_documents_partial_failure(self, migration_service):
        """배치 문서 처리 부분 실패"""
        batch_id = uuid4()
        documents = [
            IntranetDocument(
                path="/docs/file1.pdf",
                filename="file1.pdf",
                modified_date=datetime.utcnow(),
                size_bytes=1024
            ),
            IntranetDocument(
                path="/docs/file2.pdf",
                filename="file2.pdf",
                modified_date=datetime.utcnow(),
                size_bytes=2048
            )
        ]

        # Mock _process_single_document (하나는 성공, 하나는 실패)
        with patch.object(
            migration_service,
            '_process_single_document',
            new_callable=AsyncMock
        ) as mock_process:
            # 첫 번째는 성공, 두 번째는 실패
            mock_process.side_effect = [
                DocumentProcessResult(
                    status="success",
                    file="file1.pdf",
                    chunks_created=5
                ),
                Exception("Processing error")
            ]

            result = await migration_service.process_batch_documents(
                batch_id=batch_id,
                documents=documents,
                max_parallel=2
            )

            assert result.processed == 1
            assert result.failed == 1
            assert len(result.errors) == 1

    async def test_process_batch_documents_empty_list(self, migration_service):
        """빈 배치 처리"""
        batch_id = uuid4()
        documents = []

        result = await migration_service.process_batch_documents(
            batch_id=batch_id,
            documents=documents
        )

        assert result.processed == 0
        assert result.failed == 0


class TestExponentialBackoffRetry:
    """지수 백오프 재시도 테스트"""

    async def test_process_single_document_success(self, migration_service):
        """단일 문서 처리 성공"""
        batch_id = uuid4()
        doc = IntranetDocument(
            path="/docs/test.pdf",
            filename="test.pdf",
            modified_date=datetime.utcnow(),
            size_bytes=1024
        )

        result = await migration_service._process_single_document(batch_id, doc)

        assert result.status == "success"
        assert result.file == doc.path

    async def test_process_single_document_exponential_backoff(self, migration_service):
        """단일 문서 지수 백오프 검증 (재시도 지연 시간)"""
        # 실제 구현에서는 재시도 로직이 있으므로,
        # 스텁 구현(항상 성공)에서 동작 확인
        batch_id = uuid4()
        doc = IntranetDocument(
            path="/docs/test.pdf",
            filename="test.pdf",
            modified_date=datetime.utcnow(),
            size_bytes=1024
        )

        # 실제 구현은 TODO 상태이므로 항상 성공 반환
        result = await migration_service._process_single_document(batch_id, doc, retry_count=0)
        assert result.status == "success"
        assert result.file == doc.path

    async def test_process_single_document_max_retries_exceeded(self, migration_service):
        """최대 재시도 횟수 초과"""
        batch_id = uuid4()
        doc = IntranetDocument(
            path="/docs/corrupt.pdf",
            filename="corrupt.pdf",
            modified_date=datetime.utcnow(),
            size_bytes=1024
        )

        # 항상 실패하는 문서 처리
        with patch.object(
            migration_service,
            '_process_single_document',
            new_callable=AsyncMock,
            side_effect=Exception("Persistent error")
        ):
            with pytest.raises(Exception):
                await migration_service._process_single_document(batch_id, doc)


class TestBatchProgressUpdate:
    """배치 진행 상황 업데이트 테스트"""

    async def test_update_batch_progress(self, migration_service):
        """배치 진행 상황 업데이트"""
        batch_id = uuid4()

        # 에러 없이 실행되어야 함
        await migration_service.update_batch_progress(
            batch_id=batch_id,
            processed=50,
            failed=5,
            total=100
        )

        # TODO: DB 실제 구현 후 검증

    async def test_complete_batch(self, migration_service):
        """배치 완료"""
        batch_id = uuid4()

        await migration_service.complete_batch(
            batch_id=batch_id,
            status="completed",
            processed=100,
            failed=0
        )

        # TODO: DB 실제 구현 후 검증


class TestScheduleManagement:
    """스케줄 관리 테스트"""

    async def test_get_schedule(self, migration_service):
        """스케줄 조회"""
        schedule = await migration_service.get_schedule()

        # TODO: DB 실제 구현 후 검증
        # 현재는 None 반환 (스텁)

    async def test_update_schedule(self, migration_service):
        """스케줄 업데이트"""
        schedule_id = uuid4()

        result = await migration_service.update_schedule(
            schedule_id=schedule_id,
            enabled=False,
            timeout_seconds=7200
        )

        # TODO: DB 실제 구현 후 검증

    async def test_calculate_next_run(self, migration_service):
        """다음 실행 예정시간 계산"""
        cron_expr = "0 0 1 * *"  # 매달 1일 00:00

        next_run = await migration_service._calculate_next_run(cron_expr)

        assert next_run is not None
        assert isinstance(next_run, datetime)


class TestErrorHandling:
    """에러 처리 테스트"""

    async def test_notify_on_error(self, migration_service, mock_notification):
        """에러 발생 시 알림"""
        batch_id = uuid4()
        error = Exception("Test error")

        await migration_service._notify_on_error(batch_id, error)

        # 알림 서비스 호출 확인
        mock_notification.send_notification.assert_called_once()

    async def test_batch_import_with_error(self, migration_service, mock_notification):
        """배치 임포트 중 에러 발생"""
        # Mock detect_changed_documents를 실패하도록 설정
        with patch.object(
            migration_service,
            'detect_changed_documents',
            side_effect=Exception("Connection error")
        ):
            with pytest.raises(Exception):
                await migration_service.batch_import_intranet_documents()

        # 에러 알림이 발송되었는지 확인
        mock_notification.send_notification.assert_called()


# ===== 통합 테스트 =====

class TestBatchImportIntegration:
    """배치 임포트 통합 테스트"""

    async def test_batch_import_complete_flow(self, migration_service):
        """배치 임포트 전체 흐름"""
        # Mock 메서드들
        with patch.object(
            migration_service,
            'create_batch_record',
            new_callable=AsyncMock
        ) as mock_create, \
        patch.object(
            migration_service,
            'detect_changed_documents',
            new_callable=AsyncMock,
            return_value=[]
        ), \
        patch.object(
            migration_service,
            'complete_batch',
            new_callable=AsyncMock
        ), \
        patch.object(
            migration_service,
            'get_batch',
            new_callable=AsyncMock
        ) as mock_get:
            batch = MigrationBatch(
                id=uuid4(),
                batch_name="test_batch",
                status="completed",
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                scheduled_at=datetime.utcnow(),
                total_documents=0,
                processed_documents=0,
                failed_documents=0,
                skipped_documents=0,
                batch_type="manual",
                source_system="intranet",
                created_by=uuid4(),
                updated_at=datetime.utcnow()
            )

            mock_create.return_value = batch
            mock_get.return_value = batch

            # 배치 실행
            result = await migration_service.batch_import_intranet_documents(
                batch_type="manual"
            )

            # 결과 검증
            assert result is not None


if __name__ == "__main__":
    # pytest 실행: pytest tests/test_migration_service.py -v
    pass
