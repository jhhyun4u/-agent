# 문서 관리 API 명세서

## 개요

인트라넷 문서를 업로드, 관리, 검색하는 API입니다. 모든 엔드포인트는 조직 단위로 격리되며, 인증이 필요합니다.

**Base URL**: `/api/documents`

**인증**: Bearer Token (JWT)

**콘텐츠 타입**: `application/json` (응답), `multipart/form-data` (업로드)

---

## 1. 문서 업로드

### 요청

```http
POST /api/documents/upload
Content-Type: multipart/form-data

file=<binary>
doc_type=제안서
doc_subtype=&project_id=
```

**파라미터**:

| 파라미터 | 타입 | 필수 | 설명 | 예시 |
|---------|------|------|------|------|
| `file` | File | ✅ | 업로드할 문서 (PDF, HWP, HWPX, DOCX) | `proposal.pdf` |
| `doc_type` | String | ✅ | 문서 유형 | `제안서`, `보고서`, `실적`, `기타` |
| `doc_subtype` | String | ❌ | 문서 세부 유형 | `제안전략`, `기술제안` |
| `project_id` | UUID | ❌ | 연관 프로젝트 ID | `550e8400-e29b-41d4-a716-446655440000` |

**지원 파일 형식**:
- PDF (`.pdf`)
- 한글 (`.hwp`, `.hwpx`)
- Microsoft Word (`.docx`, `.doc`)

**최대 파일 크기**: 500MB

### 응답

**성공 (201 Created)**:

```json
{
  "id": "doc-0a1f2b3c",
  "org_id": "org-001",
  "filename": "proposal.pdf",
  "doc_type": "제안서",
  "doc_subtype": null,
  "processing_status": "extracting",
  "total_chars": 0,
  "chunk_count": 0,
  "created_at": "2026-04-08T10:30:00Z",
  "updated_at": "2026-04-08T10:30:00Z"
}
```

**에러 (400, 415, 422)**:

```json
{
  "detail": "지원하지 않는 파일 형식입니다. (지원: PDF, HWP, HWPX, DOCX, DOC)"
}
```

---

## 2. 문서 목록 조회

### 요청

```http
GET /api/documents?status=completed&doc_type=제안서&search=proposal&sort_by=updated_at&order=desc&limit=20&offset=0
```

**쿼리 파라미터**:

| 파라미터 | 타입 | 필수 | 기본값 | 설명 |
|---------|------|------|--------|------|
| `status` | String | ❌ | - | 처리 상태 필터 (`extracting`, `chunking`, `embedding`, `completed`, `failed`) |
| `doc_type` | String | ❌ | - | 문서 유형 필터 |
| `search` | String | ❌ | - | 파일명 검색 (ILIKE) |
| `sort_by` | String | ❌ | `updated_at` | 정렬 기준 (`created_at`, `updated_at`, `filename`, `total_chars`) |
| `order` | String | ❌ | `desc` | 정렬 순서 (`asc`, `desc`) |
| `limit` | Integer | ❌ | 20 | 페이지당 항목 수 (최대 100) |
| `offset` | Integer | ❌ | 0 | 시작 위치 |

### 응답

**성공 (200 OK)**:

```json
{
  "items": [
    {
      "id": "doc-0a1f2b3c",
      "filename": "proposal.pdf",
      "doc_type": "제안서",
      "processing_status": "completed",
      "total_chars": 25000,
      "chunk_count": 50,
      "created_at": "2026-04-08T10:30:00Z",
      "updated_at": "2026-04-08T10:45:00Z"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

---

## 3. 문서 상세 조회

### 요청

```http
GET /api/documents/{document_id}
```

**경로 파라미터**:

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `document_id` | String | 문서 ID |

### 응답

**성공 (200 OK)**:

```json
{
  "id": "doc-0a1f2b3c",
  "org_id": "org-001",
  "filename": "proposal.pdf",
  "doc_type": "제안서",
  "doc_subtype": null,
  "storage_path": "org-001/doc-0a1f2b3c/proposal.pdf",
  "extracted_text": "제안서 내용 (최대 1000자 요약)...",
  "processing_status": "completed",
  "total_chars": 25000,
  "chunk_count": 50,
  "error_message": null,
  "created_at": "2026-04-08T10:30:00Z",
  "updated_at": "2026-04-08T10:45:00Z"
}
```

**에러 (404 Not Found)**:

```json
{
  "detail": "문서를 찾을 수 없습니다."
}
```

---

## 4. 문서 재처리

### 요청

```http
POST /api/documents/{document_id}/process
```

**경로 파라미터**:

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `document_id` | String | 문서 ID |

### 응답

**성공 (200 OK)**:

```json
{
  "id": "doc-0a1f2b3c",
  "processing_status": "extracting",
  "message": "문서 재처리 시작됨"
}
```

**에러 (409 Conflict)**:

```json
{
  "detail": "문서가 현재 처리 중입니다. 처리 완료 후 재시도하세요."
}
```

**에러 (404 Not Found)**:

```json
{
  "detail": "문서를 찾을 수 없습니다."
}
```

---

## 5. 문서 청크 조회

### 요청

```http
GET /api/documents/{document_id}/chunks?chunk_type=body&limit=20&offset=0
```

**경로 파라미터**:

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `document_id` | String | 문서 ID |

**쿼리 파라미터**:

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `chunk_type` | String | - | 청크 타입 필터 (`title`, `heading`, `body`, `table`, `image`) |
| `limit` | Integer | 20 | 페이지당 항목 수 |
| `offset` | Integer | 0 | 시작 위치 |

### 응답

**성공 (200 OK)**:

```json
{
  "items": [
    {
      "id": "chunk-0a1f2b3c",
      "document_id": "doc-0a1f2b3c",
      "chunk_index": 0,
      "chunk_type": "title",
      "section_title": "제목",
      "content": "제안서 제목",
      "char_count": 10,
      "created_at": "2026-04-08T10:30:00Z"
    }
  ],
  "total": 50,
  "limit": 20,
  "offset": 0
}
```

---

## 6. 문서 삭제

### 요청

```http
DELETE /api/documents/{document_id}
```

**경로 파라미터**:

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `document_id` | String | 문서 ID |

### 응답

**성공 (204 No Content)**:

```
(본문 없음)
```

**에러 (404 Not Found)**:

```json
{
  "detail": "문서를 찾을 수 없습니다."
}
```

---

## 에러 코드

| HTTP 코드 | 의미 | 설명 |
|----------|------|------|
| 200 | OK | 성공 |
| 201 | Created | 문서 생성 성공 |
| 204 | No Content | 삭제 성공 |
| 400 | Bad Request | 요청 파라미터 오류 |
| 401 | Unauthorized | 인증 필요 |
| 403 | Forbidden | 권한 없음 |
| 404 | Not Found | 리소스 없음 |
| 409 | Conflict | 요청 충돌 (예: 진행 중인 문서 재처리) |
| 413 | Payload Too Large | 파일 크기 초과 |
| 415 | Unsupported Media Type | 지원하지 않는 파일 형식 |
| 422 | Unprocessable Entity | 요청 데이터 검증 실패 |
| 500 | Internal Server Error | 서버 에러 |

---

## 상태 코드 설명

### `processing_status` 값

| 상태 | 설명 | 다음 상태 |
|------|------|---------|
| `pending` | 대기 중 | `extracting` |
| `extracting` | 텍스트 추출 중 | `chunking` |
| `chunking` | 청크 분할 중 | `embedding` |
| `embedding` | 임베딩 생성 중 | `completed` |
| `completed` | 완료 | - |
| `failed` | 실패 | `extracting` (재처리 시) |

---

## 인증

모든 엔드포인트는 다음 헤더에서 JWT 토큰이 필요합니다:

```http
Authorization: Bearer {JWT_TOKEN}
```

토큰은 `/api/auth/login` 또는 `/api/auth/sso` 엔드포인트에서 획득합니다.

---

## 조직 격리

모든 문서는 조직 단위로 격리됩니다. 사용자는 자신의 조직에 속한 문서만 조회/수정/삭제할 수 있습니다.

**예**:
- 사용자 A (org-001) → org-001 문서만 접근 가능
- 사용자 B (org-002) → org-002 문서만 접근 가능

---

## 사용 예시

### cURL

```bash
# 1. 문서 업로드
curl -X POST http://localhost:3000/api/documents/upload \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -F "file=@proposal.pdf" \
  -F "doc_type=제안서"

# 2. 문서 목록 조회
curl -X GET "http://localhost:3000/api/documents?status=completed" \
  -H "Authorization: Bearer $JWT_TOKEN"

# 3. 문서 상세 조회
curl -X GET "http://localhost:3000/api/documents/doc-0a1f2b3c" \
  -H "Authorization: Bearer $JWT_TOKEN"

# 4. 문서 청크 조회
curl -X GET "http://localhost:3000/api/documents/doc-0a1f2b3c/chunks" \
  -H "Authorization: Bearer $JWT_TOKEN"

# 5. 문서 삭제
curl -X DELETE "http://localhost:3000/api/documents/doc-0a1f2b3c" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Python (httpx)

```python
import httpx

async with httpx.AsyncClient() as client:
    # 문서 업로드
    with open("proposal.pdf", "rb") as f:
        response = await client.post(
            "http://localhost:3000/api/documents/upload",
            params={"doc_type": "제안서"},
            files={"file": f},
            headers={"Authorization": f"Bearer {jwt_token}"}
        )
        print(response.json())

    # 문서 목록 조회
    response = await client.get(
        "http://localhost:3000/api/documents",
        params={"status": "completed"},
        headers={"Authorization": f"Bearer {jwt_token}"}
    )
    print(response.json())
```

---

## 버전 정보

- **API 버전**: v1.0
- **마지막 업데이트**: 2026-04-08
- **문서 작성**: Claude Code
