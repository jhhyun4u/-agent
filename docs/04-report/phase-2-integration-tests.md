# Phase 2: Integration Tests — API Endpoint Testing with Mocks

## Overview

Phase 2 implements a comprehensive integration test suite for the document ingestion API using AsyncClient and mock fixtures. The test suite validates all six API endpoints with proper error handling and response validation.

## Test Coverage

### Upload Endpoint (I-UPL-*)
- **I-UPL-01**: Valid PDF upload succeeds with 201 response
  - Tests: file upload, Supabase storage integration, document record creation
  - Validates: response code, document ID, filename, processing status

- **I-UPL-02**: Invalid doc_type returns 400
  - Tests: enum validation for doc_type field
  - Validates: HTTP 400, error message contains "잘못된 문서 타입"

- **I-UPL-03**: Unsupported file extension returns 415
  - Tests: file format validation (.exe, .txt, .pdf, etc.)
  - Validates: HTTP 415, error message mentions supported formats

- **I-UPL-04**: File over 500MB returns 413
  - Tests: file size validation boundary
  - Validates: HTTP 413, error message mentions 500MB limit

### List Endpoint (I-LST-*)
- **I-LST-01**: Returns paginated list structure
  - Tests: document listing with pagination, default limit=20
  - Validates: response structure, total count, limit, offset

- **I-LST-02**: limit parameter respected
  - Tests: custom limit (50) and offset (10) parameters
  - Validates: query parameters applied correctly

- **I-LST-03**: offset beyond total returns empty list
  - Tests: offset=1000 on small dataset
  - Validates: empty items array, correct total count

### Detail Endpoint (I-DET-*)
- **I-DET-01**: extracted_text truncated at 1000 chars
  - Tests: large text truncation at API boundary
  - Validates: response text ≤ 1000 chars, metadata intact

- **I-DET-02**: Non-existent document returns 404
  - Tests: missing document lookup
  - Validates: HTTP 404, error message "찾을 수 없습니다"

### Reprocess Endpoint (I-RPR-*)
- **I-RPR-01**: Failed document can be reprocessed
  - Tests: transition from "failed" → "extracting"
  - Validates: HTTP 200, status reset, error_message cleared

- **I-RPR-02**: In-progress document returns 409
  - Tests: race condition prevention for documents in "extracting", "chunking", "embedding"
  - Validates: HTTP 409, error message mentions current status

### Chunks Endpoint (I-CHK-*)
- **I-CHK-01**: Returns chunks for document
  - Tests: chunk listing with default sort (by chunk_index)
  - Validates: chunks structure, total count, pagination

- **I-CHK-02**: chunk_type filter applied
  - Tests: filtering by chunk_type parameter
  - Validates: all returned chunks match filter type

### Delete Endpoint (I-DEL-*)
- **I-DEL-01**: Valid delete returns 204
  - Tests: document deletion with Supabase Storage cleanup
  - Validates: HTTP 204 (no content), storage removal

- **I-DEL-02**: Storage error doesn't block DB delete
  - Tests: resilience when storage fails
  - Validates: HTTP 204 even if storage.remove() fails, DB deletion succeeds

## Architecture

### Mock Fixtures (conftest.py)

#### `mock_current_user`
- Overrides `get_current_user` dependency
- Overrides `require_project_access` dependency
- Returns test user: `test-user-001` in `test-org-001`

#### `create_chainable_mock()`
- Creates a mock that supports method chaining
- All query methods (.select, .eq, .order, etc.) return self
- .execute() is AsyncMock for true async behavior

#### `mock_supabase_client`
- Mocks Supabase async client
- Supports .table() → query builder pattern
- Supports .storage.from_() → file operations
- Each test configures execute() return values via side_effect

#### `sample_document_response`
- Sample document data structure
- Used for test data setup

### Test Pattern

Each test follows this pattern:

```python
@pytest.mark.asyncio
async def test_xxx(self, mock_current_user, mock_supabase_client):
    from app.main import app
    
    # 1. Prepare mock response data
    mock_supabase_client.table.return_value.execute = AsyncMock(
        return_value=MagicMock(data=response_data)
    )
    
    # 2. Patch get_async_client
    with patch("app.api.routes_documents.get_async_client", return_value=mock_supabase_client):
        # 3. Create AsyncClient and make request
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/api/documents")
    
    # 4. Assert response
    assert response.status_code == 200
```

## Running the Tests

### Run all integration tests:
```bash
pytest tests/integration/test_routes_documents.py -v
```

### Run specific test class:
```bash
pytest tests/integration/test_routes_documents.py::TestUploadEndpoint -v
```

### Run single test:
```bash
pytest tests/integration/test_routes_documents.py::TestUploadEndpoint::test_iupl_01_valid_upload -v
```

### Run with detailed output:
```bash
pytest tests/integration/test_routes_documents.py -v -s
```

## Key Design Decisions

1. **AsyncClient over TestClient**: Proper async/await handling for FastAPI endpoints
2. **Mock chainable queries**: Simulates Supabase's query builder pattern
3. **side_effect for multiple calls**: Tests that make 2+ execute() calls use side_effect lists
4. **Dependency overrides**: Both get_current_user and require_project_access overridden
5. **Minimal mocking**: Only mock what's needed, let FastAPI handle routing/validation

## Improvements from Phase 1

| Aspect | Phase 1 | Phase 2 |
|--------|---------|---------|
| Test Client | None | AsyncClient |
| Async Support | @pytest.mark.asyncio | Full async fixture support |
| Mock Setup | Placeholder (assert True) | Proper Supabase client mocks |
| Coverage | Schema validation only | Full endpoint integration |
| Error Handling | None | HTTP status code validation |
| Response Validation | None | JSON response structure validation |

## Next Steps (Phase 3)

1. **E2E Testing**: Real Supabase + PostgreSQL integration
2. **Load Testing**: Concurrent upload/list operations
3. **Security Testing**: Rate limiting, auth bypass attempts
4. **Performance Profiling**: Response time baselines

## Issues Resolved

- ✅ Async test execution with pytest-asyncio
- ✅ Dependency override for get_current_user
- ✅ Chainable query mock pattern
- ✅ Multiple execute() calls per test
- ✅ HTTP status code validation
- ✅ Response data structure validation

## Test Metrics

- **Total Tests**: 14
- **Test Classes**: 6
- **Coverage**: 100% of API endpoints
- **Estimated Runtime**: ~5 seconds
- **Mock Complexity**: Low (3 fixtures)

---

**Status**: ✅ Complete  
**Last Updated**: 2026-04-02  
**Phase**: 2/3 (Integration Tests)
