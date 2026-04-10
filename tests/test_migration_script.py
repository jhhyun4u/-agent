"""
마이그레이션 스크립트 테스트

레거시 문서 대량 임포트 스크립트 검증
"""

import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.services.migration_service import MigrationService


# ── Fixtures ──

@pytest.fixture
def mock_legacy_documents():
    """레거시 intranet_projects 데이터"""
    return [
        {
            "id": str(uuid4()),
            "file_path": "legacy/proposal_001.pdf",
            "file_name": "proposal_001.pdf",
            "updated_at": "2026-04-01T10:00:00Z",
            "size_bytes": 1024000,
            "project_id": str(uuid4()),
            "file_type": "제안서",
        },
        {
            "id": str(uuid4()),
            "file_path": "legacy/report_002.hwp",
            "file_name": "report_002.hwp",
            "updated_at": "2026-04-02T15:30:00Z",
            "size_bytes": 512000,
            "project_id": str(uuid4()),
            "file_type": "보고서",
        },
    ]


@pytest.fixture
def mock_db(mock_legacy_documents):
    """Supabase 비동기 클라이언트 Mock"""
    db = MagicMock()

    # intranet_projects 테이블 mock
    projects_query = MagicMock()
    projects_query.select = MagicMock(return_value=projects_query)
    projects_query.gte = MagicMock(return_value=projects_query)
    projects_query.order = MagicMock(return_value=projects_query)
    projects_query.execute = AsyncMock(
        return_value=MagicMock(data=mock_legacy_documents)
    )

    # migration_batches 테이블 mock
    batches_query = MagicMock()
    batches_query.insert = MagicMock(return_value=MagicMock(
        execute=AsyncMock(return_value=MagicMock(data=[{
            "id": str(uuid4()),
            "batch_name": f"{datetime.now(timezone.utc).strftime('%Y-%m-%d')}__manual",
            "status": "pending",
            "started_at": datetime.now(timezone.utc).isoformat(),
            "scheduled_at": datetime.now(timezone.utc).isoformat(),
            "total_documents": len(mock_legacy_documents),
            "processed_documents": 0,
            "failed_documents": 0,
            "skipped_documents": 0,
            "batch_type": "manual",
            "source_system": "intranet",
            "completed_at": None,
            "error_message": None,
            "error_details": None,
        }]))
    ))
    batches_query.update = MagicMock(return_value=MagicMock(
        eq=MagicMock(return_value=MagicMock(
            execute=AsyncMock(return_value=MagicMock(data=[]))
        ))
    ))
    batches_query.select = MagicMock(return_value=MagicMock(
        eq=MagicMock(return_value=MagicMock(
            maybe_single=MagicMock(return_value=MagicMock(
                execute=AsyncMock(return_value=MagicMock(data=None))
            ))
        ))
    ))

    def table_side_effect(name):
        if name == "intranet_projects":
            return projects_query
        elif name == "migration_batches":
            return batches_query
        return projects_query

    db.table = MagicMock(side_effect=table_side_effect)
    return db


# ── Tests ──

@pytest.mark.asyncio
async def test_migration_service_initialization(mock_db):
    """마이그레이션 서비스 초기화"""
    # Act
    service = MigrationService(db=mock_db)

    # Assert
    assert service.db is mock_db
    assert service.notification is None


@pytest.mark.asyncio
async def test_detect_changed_documents(mock_db, mock_legacy_documents):
    """변경된 문서 감지"""
    # Arrange
    service = MigrationService(db=mock_db)
    since = datetime.now(timezone.utc) - timedelta(days=30)

    # Act
    documents = await service.detect_changed_documents(since)

    # Assert
    assert len(documents) == len(mock_legacy_documents)
    assert documents[0].filename == "proposal_001.pdf"
    assert documents[1].filename == "report_002.hwp"


@pytest.mark.asyncio
async def test_detect_changed_documents_empty(mock_db):
    """변경된 문서가 없는 경우"""
    # Arrange
    empty_query = MagicMock()
    empty_query.select = MagicMock(return_value=empty_query)
    empty_query.gte = MagicMock(return_value=empty_query)
    empty_query.order = MagicMock(return_value=empty_query)
    empty_query.execute = AsyncMock(return_value=MagicMock(data=[]))

    mock_db.table = MagicMock(return_value=empty_query)

    service = MigrationService(db=mock_db)
    since = datetime.now(timezone.utc) - timedelta(days=30)

    # Act
    documents = await service.detect_changed_documents(since)

    # Assert
    assert len(documents) == 0


@pytest.mark.asyncio
async def test_create_batch_record(mock_db):
    """배치 레코드 생성"""
    # Arrange
    service = MigrationService(db=mock_db)

    # Act
    batch = await service.create_batch_record(
        batch_type="manual",
        total_docs=2
    )

    # Assert
    assert batch is not None
    assert batch.status == "pending"
    assert batch.batch_type == "manual"
    assert batch.total_documents == 2


@pytest.mark.asyncio
async def test_process_batch_documents(mock_db, mock_legacy_documents):
    """배치 문서 처리"""
    # Arrange
    service = MigrationService(db=mock_db)
    batch_id = uuid4()

    # intranet_documents를 위한 mock 추가
    doc_query = MagicMock()
    doc_query.insert = MagicMock(return_value=MagicMock(
        execute=AsyncMock(return_value=MagicMock(data=[{"id": str(uuid4())}]))
    ))
    doc_query.update = MagicMock(return_value=MagicMock(
        eq=MagicMock(return_value=MagicMock(
            execute=AsyncMock(return_value=MagicMock(data=[]))
        ))
    ))

    def table_side_effect(name):
        if name == "intranet_documents":
            return doc_query
        return mock_db.table.return_value

    mock_db.table = MagicMock(side_effect=table_side_effect)

    # Act
    from app.models.migration_schemas import IntranetDocument
    documents = [
        IntranetDocument(
            path=doc["file_path"],
            filename=doc["file_name"],
            modified_date=datetime.fromisoformat(doc["updated_at"]),
            size_bytes=doc["size_bytes"],
            doc_type=doc.get("file_type"),
        )
        for doc in mock_legacy_documents
    ]

    result = await service.process_batch_documents(batch_id, documents)

    # Assert
    assert result is not None
    assert result.status == "completed"
    assert result.batch_id == batch_id


@pytest.mark.asyncio
async def test_batch_import_intranet_documents(mock_db, mock_legacy_documents):
    """전체 마이그레이션 플로우"""
    # Arrange
    service = MigrationService(db=mock_db)

    # Act
    batch = await service.batch_import_intranet_documents(
        batch_type="manual",
        include_failed=False
    )

    # Assert
    assert batch is not None
    assert batch.status in ["completed", "partial_failed"]
    assert batch.batch_type == "manual"


# ── Integration Tests ──

@pytest.mark.asyncio
async def test_batch_import_with_failure_handling(mock_db):
    """배치 임포트 - 에러 처리"""
    # Arrange
    error_query = MagicMock()
    error_query.select = MagicMock(return_value=error_query)
    error_query.gte = MagicMock(return_value=error_query)
    error_query.order = MagicMock(return_value=error_query)
    error_query.execute = AsyncMock(
        side_effect=Exception("Database connection error")
    )

    mock_db.table = MagicMock(return_value=error_query)

    service = MigrationService(db=mock_db)

    # Act & Assert
    with pytest.raises(Exception) as exc_info:
        await service.batch_import_intranet_documents()

    assert "Database connection error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_retry_failed_batch(mock_db, mock_legacy_documents):
    """이전 실패 배치 재실행"""
    # Arrange
    service = MigrationService(db=mock_db)
    failed_batch_id = uuid4()

    # Act
    batch = await service.retry_failed_batch(failed_batch_id)

    # Assert
    assert batch is not None
    assert batch.status in ["completed", "partial_failed"]
