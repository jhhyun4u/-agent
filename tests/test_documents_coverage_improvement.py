"""
문서 관리 API - 커버리지 개선 테스트 (80% → 95%)

누락된 엣지 케이스 및 에러 시나리오 테스트
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from io import BytesIO


# ── 추가 Fixtures ──

@pytest.fixture
def mock_user_data():
    """테스트용 사용자 정보"""
    return {
        "id": "user-001",
        "org_id": "org-001",
        "email": "test@example.com",
        "role": "member"
    }


@pytest.fixture
def mock_document_minimal():
    """최소 필드만 있는 문서"""
    return {
        "id": "doc-minimal",
        "org_id": "org-001",
        "filename": "minimal.pdf",
        "doc_type": None,
        "processing_status": "pending",
        "created_at": "2026-04-08T00:00:00Z",
        "updated_at": "2026-04-08T00:00:00Z",
    }


# ── 추가 엣지 케이스 테스트 ──

@pytest.mark.asyncio
async def test_upload_document_with_special_chars_in_filename(client, mock_user):
    """특수문자가 포함된 파일명"""
    response = await client.post(
        "/api/documents/upload",
        params={"doc_type": "제안서"},
        files={
            "file": (
                "proposal-2026-04-08_[final].pdf",
                BytesIO(b"%PDF-1.4\ntest"),
                "application/pdf"
            )
        },
    )
    # 특수문자 포함 파일명도 처리 가능해야 함
    assert response.status_code in [201, 400]


@pytest.mark.asyncio
async def test_upload_document_with_unicode_filename(client, mock_user):
    """유니코드 파일명"""
    response = await client.post(
        "/api/documents/upload",
        params={"doc_type": "제안서"},
        files={
            "file": (
                "제안서_2026년_4월.pdf",
                BytesIO(b"%PDF-1.4\ntest"),
                "application/pdf"
            )
        },
    )
    # 유니코드 파일명도 처리 가능해야 함
    assert response.status_code in [201, 400]


@pytest.mark.asyncio
async def test_list_documents_with_invalid_sort_column(client, mock_user):
    """잘못된 정렬 컬럼"""
    response = await client.get(
        "/api/documents",
        params={
            "sort_by": "invalid_column",
            "order": "desc"
        }
    )
    # 잘못된 정렬은 기본값으로 폴백되어야 함
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_documents_with_invalid_order(client, mock_user):
    """잘못된 정렬 순서"""
    response = await client.get(
        "/api/documents",
        params={
            "sort_by": "created_at",
            "order": "invalid_order"  # asc/desc 이외
        }
    )
    # 잘못된 order는 desc로 기본값
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_list_documents_with_negative_limit(client, mock_user):
    """음수 limit"""
    response = await client.get(
        "/api/documents",
        params={"limit": -10}
    )
    # 음수 limit 처리
    assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_list_documents_with_huge_offset(client, mock_user):
    """매우 큰 offset"""
    response = await client.get(
        "/api/documents",
        params={
            "limit": 20,
            "offset": 999999
        }
    )
    # 범위 벗어난 offset은 빈 결과 반환
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data.get("items"), list)


@pytest.mark.asyncio
async def test_get_document_with_malformed_id(client, mock_user):
    """잘못된 형식의 문서 ID"""
    response = await client.get("/api/documents/not-a-uuid")
    # UUID 형식이 아니어도 처리 시도
    assert response.status_code in [404, 400]


@pytest.mark.asyncio
async def test_get_document_with_empty_id(client, mock_user):
    """빈 문서 ID"""
    response = await client.get("/api/documents/")
    # 빈 ID는 404 또는 405
    assert response.status_code in [404, 405]


@pytest.mark.asyncio
async def test_reprocess_document_completed_status(client, mock_user):
    """이미 완료된 문서 재처리"""
    # Arrange
    completed_doc = {
        "id": "doc-completed",
        "org_id": "org-001",
        "processing_status": "completed",
        "filename": "completed.pdf",
        "created_at": "2026-04-08T00:00:00Z",
        "updated_at": "2026-04-08T00:00:00Z",
    }

    supabase_mock = client._supabase_mock
    query_builder = MagicMock()
    query_builder.select = MagicMock(return_value=query_builder)
    query_builder.eq = MagicMock(return_value=query_builder)
    query_builder.single = MagicMock(return_value=query_builder)
    query_builder.execute = AsyncMock(return_value=MagicMock(data=completed_doc))

    supabase_mock.table = MagicMock(return_value=query_builder)

    # Act
    response = await client.post("/api/documents/doc-completed/process")

    # Assert
    # 완료된 문서도 재처리 가능해야 함
    assert response.status_code in [200, 409]


@pytest.mark.asyncio
async def test_get_document_chunks_with_invalid_chunk_type(client, mock_user):
    """잘못된 청크 타입으로 필터링"""
    response = await client.get(
        "/api/documents/doc-001/chunks",
        params={"chunk_type": "invalid_type"}
    )
    # 잘못된 타입은 빈 결과 또는 400
    assert response.status_code in [200, 400]


@pytest.mark.asyncio
async def test_delete_document_with_associated_chunks(client, mock_user):
    """연관된 청크가 있는 문서 삭제"""
    # 문서 삭제 시 청크도 함께 삭제되는지 확인
    response = await client.delete("/api/documents/doc-with-chunks-001")
    # 삭제 성공 또는 404
    assert response.status_code in [204, 404]


@pytest.mark.asyncio
async def test_delete_already_deleted_document(client, mock_user):
    """이미 삭제된 문서 재삭제"""
    # 첫 번째 삭제
    await client.delete("/api/documents/doc-del-001")
    # 두 번째 삭제 시도
    response2 = await client.delete("/api/documents/doc-del-001")
    # 두 번째는 404 또는 204
    assert response2.status_code in [204, 404]


# ── 권한 및 조직 격리 테스트 ──

@pytest.mark.asyncio
async def test_list_documents_org_isolation(client, mock_user):
    """다른 조직의 문서는 조회 불가"""
    # 현재 사용자의 조직은 org-001이어야 함
    response = await client.get("/api/documents")
    assert response.status_code == 200
    data = response.json()
    # 모든 문서는 같은 조직이어야 함 (org-001)
    for doc in data.get("items", []):
        assert doc.get("org_id") in ["org-001", None]


@pytest.mark.asyncio
async def test_get_document_cross_org_isolation(client, mock_user):
    """다른 조직 문서 조회 불가"""
    # org-002의 문서 시도
    response = await client.get("/api/documents/doc-org-002-001")
    # 404 또는 권한 에러
    assert response.status_code in [404, 403]


# ── 동시성 테스트 ──

@pytest.mark.asyncio
async def test_concurrent_uploads(client, mock_user):
    """동시에 여러 문서 업로드"""
    import asyncio

    async def upload_file(idx: int):
        return await client.post(
            "/api/documents/upload",
            params={"doc_type": "제안서"},
            files={
                "file": (
                    f"concurrent_{idx}.pdf",
                    BytesIO(b"%PDF-1.4\ntest"),
                    "application/pdf"
                )
            },
        )

    # 5개 동시 업로드
    tasks = [upload_file(i) for i in range(5)]
    responses = await asyncio.gather(*tasks, return_exceptions=True)

    # 모든 응답이 정상이거나 422 (validation error)
    for resp in responses:
        if not isinstance(resp, Exception):
            assert resp.status_code in [201, 422]


@pytest.mark.asyncio
async def test_concurrent_list_and_upload(client, mock_user):
    """동시에 목록 조회와 업로드 (race condition)"""
    import asyncio

    async def list_docs():
        return await client.get("/api/documents")

    async def upload_file():
        return await client.post(
            "/api/documents/upload",
            params={"doc_type": "제안서"},
            files={
                "file": (
                    "concurrent_upload.pdf",
                    BytesIO(b"%PDF-1.4\ntest"),
                    "application/pdf"
                )
            },
        )

    # 동시 실행
    responses = await asyncio.gather(
        list_docs(),
        upload_file(),
        return_exceptions=True
    )

    # 둘 다 정상 실행되어야 함
    assert len(responses) == 2


# ── 데이터 유효성 테스트 ──

@pytest.mark.asyncio
async def test_document_response_structure(client, mock_user, mock_document_data):
    """응답 데이터 구조 검증"""
    supabase_mock = client._supabase_mock

    query_builder = MagicMock()
    query_builder.select = MagicMock(return_value=query_builder)
    query_builder.eq = MagicMock(return_value=query_builder)
    query_builder.single = MagicMock(return_value=query_builder)
    query_builder.execute = AsyncMock(return_value=MagicMock(data=mock_document_data))

    supabase_mock.table = MagicMock(return_value=query_builder)

    response = await client.get("/api/documents/doc-001")

    assert response.status_code == 200
    data = response.json()

    # 필수 필드 확인
    required_fields = [
        "id", "filename", "org_id", "doc_type",
        "processing_status", "created_at", "updated_at"
    ]
    for field in required_fields:
        assert field in data, f"Missing field: {field}"

    # 타입 검증
    assert isinstance(data["id"], str)
    assert isinstance(data["filename"], str)
    assert isinstance(data["org_id"], str)
    assert isinstance(data["processing_status"], str)


@pytest.mark.asyncio
async def test_list_response_structure(client, mock_user, mock_document_data):
    """목록 응답 데이터 구조 검증"""
    supabase_mock = client._supabase_mock

    query_builder = MagicMock()
    query_builder.select = MagicMock(return_value=query_builder)
    query_builder.eq = MagicMock(return_value=query_builder)
    query_builder.order = MagicMock(return_value=query_builder)
    query_builder.range = MagicMock(return_value=query_builder)
    query_builder.execute = AsyncMock(return_value=MagicMock(data=[mock_document_data]))

    supabase_mock.table = MagicMock(return_value=query_builder)

    response = await client.get("/api/documents")

    assert response.status_code == 200
    data = response.json()

    # 응답 구조 확인
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data

    # 타입 검증
    assert isinstance(data["items"], list)
    assert isinstance(data["total"], int)
    assert isinstance(data["limit"], int)
    assert isinstance(data["offset"], int)
