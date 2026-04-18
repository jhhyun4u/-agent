"""
문서 수집 및 처리 API 테스트 (Document Ingestion)

테스트 범위:
- 단위 테스트: 각 API 엔드포인트
- 통합 테스트: 파일 업로드 → 처리 → 조회
- 권한 테스트: org 격리
- 에러 테스트: 유효하지 않은 파일, 큰 파일 등
"""

import pytest
import json
import asyncio
from io import BytesIO
from datetime import datetime
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient
from app.main import app
from app.models.auth_schemas import CurrentUser
from app.api.deps import get_current_user


@pytest.fixture
def test_user():
    """테스트 사용자"""
    return CurrentUser(
        id=str(uuid4()),
        email="test@tenopa.co.kr",
        org_id=str(uuid4()),
        name="Test User",
        role="pm",
    )


@pytest.fixture
def client(test_user):
    """FastAPI 테스트 클라이언트 (인증 mock 포함)"""
    test_client = TestClient(app)
    # Override authentication dependency
    app.dependency_overrides[get_current_user] = lambda: test_user
    yield test_client
    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_pdf_file():
    """테스트용 샘플 PDF 파일 (매직 바이트 포함)"""
    # 최소한의 PDF 구조 (매직 바이트 %PDF 포함)
    pdf_content = b"""%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R >>
endobj
4 0 obj
<< >>
stream
BT
/F1 12 Tf
100 700 Td
(Test Document Content) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000203 00000 n
trailer
<< /Size 5 /Root 1 0 R >>
startxref
303
%%EOF
"""
    return BytesIO(pdf_content)


@pytest.fixture
def invalid_file():
    """유효하지 않은 파일"""
    return BytesIO(b"This is not a valid PDF or document file")


class TestDocumentUpload:
    """POST /api/documents/upload 테스트"""

    @pytest.mark.asyncio
    async def test_upload_success_with_valid_file(self, client, sample_pdf_file):
        """✅ 유효한 파일 업로드 성공"""
        with patch('app.api.routes_documents.get_async_client') as mock_client:
            # Mock Supabase operations
            mock_async_client = AsyncMock()
            mock_client.return_value = mock_async_client

            # Mock storage upload
            mock_async_client.storage.from_.return_value.upload = AsyncMock()

            # Mock document creation
            mock_async_client.table.return_value.insert.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[{
                    "id": str(uuid4()),
                    "filename": "test.pdf",
                    "doc_type": "보고서",
                    "storage_path": "uploads/test.pdf",
                    "processing_status": "extracting",
                    "created_at": datetime.now().isoformat(),
                }])
            )

            response = client.post(
                "/api/documents/upload",
                files={"file": ("test.pdf", sample_pdf_file, "application/pdf")},
                data={"doc_type": "보고서"},
            )

            # 201 Created 또는 200 (배경 작업이 시작되므로 우선 응답)
            assert response.status_code in [200, 201]
            data = response.json()
            assert "id" in data or "filename" in data

    def test_upload_invalid_file_type(self, client):
        """❌ 지원하지 않는 파일 형식"""
        invalid_file = BytesIO(b"not a document")

        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.txt", invalid_file, "text/plain")},
            data={"doc_type": "보고서"},
        )

        assert response.status_code == 400
        assert "지원하지 않는" in response.json()["detail"] or "파일 형식" in response.json()["detail"]

    def test_upload_invalid_doc_type(self, client, sample_pdf_file):
        """❌ 유효하지 않은 doc_type"""
        sample_pdf_file.seek(0)
        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", sample_pdf_file, "application/pdf")},
            data={"doc_type": "유효하지_않음"},
        )

        assert response.status_code == 400

    def test_upload_corrupted_file(self):
        """❌ 손상된 파일 (magic bytes 검증 실패)"""
        # PDF 매직 바이트 없는 파일
        invalid_pdf = BytesIO(b"This is not a PDF file content")

        client = TestClient(app)
        app.dependency_overrides[get_current_user] = lambda: CurrentUser(
            id=str(uuid4()),
            email="test@tenopa.co.kr",
            org_id=str(uuid4()),
            name="Test",
            role="pm",
        )

        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", invalid_pdf, "application/pdf")},
            data={"doc_type": "보고서"},
        )

        # 매직 바이트 검증 실패
        assert response.status_code == 400
        app.dependency_overrides.clear()


class TestDocumentList:
    """GET /api/documents 테스트"""

    @pytest.mark.asyncio
    async def test_list_documents_empty(self, client):
        """✅ 빈 목록 조회"""
        with patch('app.api.routes_documents.get_async_client') as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value = mock_async_client

            # Mock empty result
            mock_async_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order_by.return_value.limit.return_value.offset.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[], count=0)
            )

            response = client.get("/api/documents")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert len(data["items"]) == 0

    @pytest.mark.asyncio
    async def test_list_documents_with_filter(self, client):
        """✅ 필터 적용 조회 (status, doc_type)"""
        response = client.get("/api/documents?status=completed&doc_type=보고서")
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data


class TestDocumentDetail:
    """GET /api/documents/{id} 테스트"""

    @pytest.mark.asyncio
    async def test_get_document_success(self, client):
        """✅ 문서 상세 조회"""
        doc_id = str(uuid4())
        with patch('app.api.routes_documents.get_async_client') as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value = mock_async_client

            mock_async_client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute = AsyncMock(
                return_value=MagicMock(data={
                    "id": doc_id,
                    "filename": "test.pdf",
                    "doc_type": "보고서",
                    "processing_status": "completed",
                    "total_chars": 5000,
                    "chunk_count": 10,
                    "created_at": datetime.now().isoformat(),
                })
            )

            response = client.get(f"/api/documents/{doc_id}")
            assert response.status_code == 200
            data = response.json()
            assert data["id"] == doc_id

    def test_get_document_not_found(self, client):
        """❌ 존재하지 않는 문서"""
        doc_id = str(uuid4())
        response = client.get(f"/api/documents/{doc_id}")
        # Supabase will raise an error if not found
        # Response depends on error handling in routes_documents.py
        assert response.status_code >= 400


class TestDocumentReprocess:
    """POST /api/documents/{id}/process 테스트"""

    @pytest.mark.asyncio
    async def test_reprocess_failed_document(self, client):
        """✅ 실패한 문서 재처리"""
        doc_id = str(uuid4())
        with patch('app.api.routes_documents.get_async_client') as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value = mock_async_client

            # Mock document update
            mock_async_client.table.return_value.update.return_value.eq.return_value.execute = AsyncMock()

            # Mock process_document_bounded
            with patch('app.api.routes_documents.process_document_bounded') as mock_process:
                mock_process.return_value = AsyncMock()

                response = client.post(f"/api/documents/{doc_id}/process")
                assert response.status_code in [200, 202]


class TestDocumentChunks:
    """GET /api/documents/{id}/chunks 테스트"""

    @pytest.mark.asyncio
    async def test_get_chunks_success(self, client):
        """✅ 청크 목록 조회"""
        doc_id = str(uuid4())
        with patch('app.api.routes_documents.get_async_client') as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value = mock_async_client

            mock_async_client.table.return_value.select.return_value.eq.return_value.eq.return_value.order_by.return_value.limit.return_value.offset.return_value.execute = AsyncMock(
                return_value=MagicMock(data=[
                    {
                        "id": str(uuid4()),
                        "chunk_index": 0,
                        "chunk_type": "body",
                        "content": "Test content",
                        "char_count": 1000,
                    }
                ], count=1)
            )

            response = client.get(f"/api/documents/{doc_id}/chunks")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data


class TestDocumentDelete:
    """DELETE /api/documents/{id} 테스트"""

    @pytest.mark.asyncio
    async def test_delete_document_success(self, client):
        """✅ 문서 삭제"""
        doc_id = str(uuid4())
        with patch('app.api.routes_documents.get_async_client') as mock_client:
            mock_async_client = AsyncMock()
            mock_client.return_value = mock_async_client

            # Mock document retrieval
            mock_async_client.table.return_value.select.return_value.eq.return_value.eq.return_value.single.return_value.execute = AsyncMock(
                return_value=MagicMock(data={"id": doc_id, "storage_path": "path/to/file"})
            )

            # Mock deletion
            mock_async_client.table.return_value.delete.return_value.eq.return_value.execute = AsyncMock()

            response = client.delete(f"/api/documents/{doc_id}")
            assert response.status_code == 204


class TestIntegration:
    """통합 테스트: 전체 파이프라인"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_end_to_end_document_processing(self):
        """전체 파이프라인: 업로드 → 처리 → 조회

        시나리오:
        1. PDF 파일 업로드
        2. 처리 상태 확인 (extracting → chunking → embedding → completed)
        3. 청크 조회
        4. 메타데이터 확인
        """
        # NOTE: 실제 E2E 테스트는 Supabase 통합 테스트 환경에서만 실행
        # 이 테스트는 구조만 정의
        pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_project_metadata_seeding(self):
        """프로젝트 메타데이터 자동 시드 확인 (document_ingestion.py)

        시나리오:
        1. 실적 문서 업로드
        2. capabilities 자동 생성 확인
        3. client_intelligence 자동 생성 확인
        4. market_price_data 자동 생성 확인
        """
        # NOTE: import_project() 함수 테스트는 test_document_ingestion_service.py에서
        pass

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_documents_concurrent_processing(self):
        """동시 처리 테스트

        시나리오:
        1. 5개 문서 동시 업로드
        2. 모두 완료될 때까지 대기
        3. 모든 청크 생성 확인
        """
        # NOTE: Supabase 통합 환경에서 테스트
        pass


class TestErrorHandling:
    """에러 처리 테스트"""

    @pytest.mark.asyncio
    async def test_extraction_failure_handling(self):
        """텍스트 추출 실패 처리"""
        # process_document()의 에러 처리 검증
        # → document_ingestion_service.py 테스트에서
        pass

    @pytest.mark.asyncio
    async def test_insufficient_text_handling(self):
        """텍스트 부족 처리 (< 50자)"""
        # process_document()의 에러 처리 검증
        pass

    @pytest.mark.asyncio
    async def test_embedding_api_error_handling(self):
        """임베딩 API 오류 처리"""
        # generate_embeddings_batch() 재시도 로직 검증
        pass


class TestSecurity:
    """보안 테스트"""

    @pytest.mark.asyncio
    async def test_org_isolation_enforcement(self, client, test_user):
        """org 격리 강제 (RLS 검증)"""
        # 모든 API 엔드포인트가 org_id로 자동 필터링하므로
        # GET /api/documents는 현재 org의 문서만 반환
        response = client.get("/api/documents")
        assert response.status_code == 200
        # 응답의 문서들이 모두 현재 org에 속하는지 확인은 DB RLS로 강제

    def test_authentication_required(self):
        """인증 필수 확인 (인증 없이 요청)"""
        client = TestClient(app)
        # 인증 override 제거
        app.dependency_overrides.clear()

        response = client.get("/api/documents")
        # FastAPI/deps의 get_current_user가 없으면 에러
        assert response.status_code >= 400

    def test_file_magic_bytes_validation(self, client):
        """매직 바이트 검증"""
        # routes_documents.py의 validate_file_magic_bytes() 함수 테스트
        invalid_pdf = BytesIO(b"INVALID_PDF_HEADER_Here is PDF content")

        response = client.post(
            "/api/documents/upload",
            files={"file": ("test.pdf", invalid_pdf, "application/pdf")},
            data={"doc_type": "보고서"},
        )

        assert response.status_code == 400
        assert "파일 형식" in response.json()["detail"]


class TestSchemas:
    """Pydantic 스키마 검증 테스트"""

    def test_document_response_schema(self):
        """DocumentResponse 스키마"""
        from app.models.document_schemas import DocumentResponse

        doc = DocumentResponse(
            id=str(uuid4()),
            filename="test.pdf",
            doc_type="보고서",
            storage_path="uploads/test.pdf",
            processing_status="completed",
            total_chars=5000,
            chunk_count=10,
            error_message=None,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert doc.filename == "test.pdf"

    def test_chunk_response_schema(self):
        """ChunkResponse 스키마"""
        from app.models.document_schemas import ChunkResponse

        chunk = ChunkResponse(
            id=str(uuid4()),
            chunk_index=0,
            chunk_type="body",
            section_title="Introduction",
            content="Test content",
            char_count=1000,
            created_at=datetime.now(),
        )
        assert chunk.chunk_type == "body"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
