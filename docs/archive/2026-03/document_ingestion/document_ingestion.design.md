# Document Ingestion 설계 문서 (Design)

**버전**: v1.0
**작성일**: 2026-03-29
**상태**: APPROVED

---

## 1. 아키텍처 개요

```
┌──────────────────────────────────────────────────────────┐
│ 프론트엔드: 문서 업로드 폼                                 │
└─────────────┬──────────────────────────────────────────┘
              │ POST /api/documents/upload
              ↓
┌──────────────────────────────────────────────────────────┐
│ API Layer (FastAPI)                                       │
├──────────────────────────────────────────────────────────┤
│ POST /api/documents/upload                                │
│ GET  /api/documents                                       │
│ GET  /api/documents/{id}                                  │
│ POST /api/documents/{id}/process                          │
│ GET  /api/documents/{id}/chunks                           │
└─────────────┬──────────────────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────────────────────┐
│ Service Layer                                             │
├──────────────────────────────────────────────────────────┤
│ - DocumentIngestionService                                │
│   ├─ upload_file()                                        │
│   ├─ process_document()  (기존 함수 재사용)              │
│   ├─ import_project()    (기존 함수 재사용)              │
│   └─ get_document_status()                                │
│                                                            │
│ - DocumentChunker (기존)                                  │
│ - EmbeddingService (기존)                                 │
│ - RfpParser (기존)                                        │
└─────────────┬──────────────────────────────────────────┘
              │
              ↓
┌──────────────────────────────────────────────────────────┐
│ Storage & Database                                        │
├──────────────────────────────────────────────────────────┤
│ Supabase Storage (파일)     | intranet_documents (메타)  │
│                             | document_chunks (청크+임베딩)│
│                             | capabilities (역량)         │
│                             | client_intelligence (발주기관)│
│                             | market_price_data (시장가격)  │
└──────────────────────────────────────────────────────────┘
```

---

## 2. API 명세

### 2.1 POST /api/documents/upload

**목적**: 문서 파일 업로드 및 처리 시작

**요청:**
```json
{
  "file": "<binary file>",
  "doc_type": "보고서|제안서|실적|기타",
  "doc_subtype": "string (optional)",
  "project_id": "string (optional)"
}
```

**응답 (201):**
```json
{
  "id": "uuid",
  "filename": "string",
  "doc_type": "string",
  "storage_path": "string",
  "processing_status": "extracting",
  "total_chars": 0,
  "chunk_count": 0,
  "created_at": "2026-03-29T10:00:00Z"
}
```

**동작:**
1. 파일을 Supabase Storage에 저장
2. intranet_documents 레코드 생성 (processing_status: extracting)
3. 백그라운드: process_document() 비동기 호출
4. 즉시 응답 (상태는 클라이언트가 주기적으로 조회)

**권한:**
- 인증된 사용자
- 자신의 org_id로만 저장

---

### 2.2 GET /api/documents

**목적**: 문서 목록 조회

**요청:**
```
GET /api/documents?status=completed&doc_type=보고서&limit=20&offset=0
```

**응답 (200):**
```json
{
  "items": [
    {
      "id": "uuid",
      "filename": "string",
      "doc_type": "string",
      "processing_status": "completed",
      "total_chars": 5000,
      "chunk_count": 10,
      "error_message": null,
      "created_at": "2026-03-29T10:00:00Z"
    }
  ],
  "total": 42,
  "limit": 20,
  "offset": 0
}
```

**필터:**
- `status`: extracting, chunking, embedding, completed, failed
- `doc_type`: 보고서, 제안서, 실적, 기타
- `limit`, `offset`: 페이지네이션

---

### 2.3 GET /api/documents/{id}

**목적**: 문서 상세 조회 + 처리 진행상황

**요청:**
```
GET /api/documents/{document_id}
```

**응답 (200):**
```json
{
  "id": "uuid",
  "filename": "string",
  "doc_type": "string",
  "storage_path": "string",
  "extracted_text": "string (처음 1000자)",
  "processing_status": "embedding",
  "total_chars": 50000,
  "chunk_count": 0,
  "error_message": null,
  "created_at": "2026-03-29T10:00:00Z",
  "updated_at": "2026-03-29T10:15:00Z"
}
```

**동작:**
- intranet_documents에서 조회
- extracted_text는 첫 1000자만 반환 (대용량 방지)

---

### 2.4 POST /api/documents/{id}/process

**목적**: 문서 수동 처리 재시작 (실패한 문서 재시도)

**요청:**
```
POST /api/documents/{document_id}
```

**응답 (200):**
```json
{
  "id": "uuid",
  "processing_status": "extracting",
  "message": "재처리 시작됨"
}
```

**동작:**
- 기존 error_message 초기화
- processing_status: extracting으로 리셋
- process_document() 비동기 호출

---

### 2.5 GET /api/documents/{id}/chunks

**목적**: 문서의 청크 목록 조회

**요청:**
```
GET /api/documents/{document_id}?chunk_type=body&limit=10
```

**응답 (200):**
```json
{
  "items": [
    {
      "id": "uuid",
      "chunk_index": 0,
      "chunk_type": "title|heading|body|table|image",
      "section_title": "string",
      "content": "string",
      "char_count": 500,
      "created_at": "2026-03-29T10:00:00Z"
    }
  ],
  "total": 25,
  "limit": 10,
  "offset": 0
}
```

**필터:**
- `chunk_type`: title, heading, body, table, image
- `limit`, `offset`: 페이지네이션

---

## 3. 데이터 모델

### 3.1 Pydantic 스키마

```python
# DocumentUploadRequest
class DocumentUploadRequest(BaseModel):
    doc_type: Literal["보고서", "제안서", "실적", "기타"]
    doc_subtype: Optional[str] = None
    project_id: Optional[str] = None

# DocumentResponse
class DocumentResponse(BaseModel):
    id: str
    filename: str
    doc_type: str
    storage_path: str
    processing_status: str
    total_chars: int
    chunk_count: int
    error_message: Optional[str]
    created_at: datetime
    updated_at: datetime

# DocumentListResponse
class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    limit: int
    offset: int

# ChunkResponse
class ChunkResponse(BaseModel):
    id: str
    chunk_index: int
    chunk_type: str
    section_title: Optional[str]
    content: str
    char_count: int
    created_at: datetime
```

### 3.2 DB 테이블 (기존)

**intranet_documents**
```sql
CREATE TABLE intranet_documents (
  id UUID PRIMARY KEY,
  org_id UUID NOT NULL REFERENCES organizations(id),
  filename VARCHAR NOT NULL,
  doc_type VARCHAR NOT NULL,
  doc_subtype VARCHAR,
  storage_path VARCHAR NOT NULL,
  extracted_text TEXT,
  processing_status VARCHAR DEFAULT 'extracting',
  error_message TEXT,
  total_chars INTEGER DEFAULT 0,
  chunk_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT now(),
  updated_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_intranet_documents_org_id ON intranet_documents(org_id);
CREATE INDEX idx_intranet_documents_status ON intranet_documents(processing_status);
```

**document_chunks**
```sql
CREATE TABLE document_chunks (
  id UUID PRIMARY KEY,
  document_id UUID NOT NULL REFERENCES intranet_documents(id) ON DELETE CASCADE,
  org_id UUID NOT NULL REFERENCES organizations(id),
  chunk_index INTEGER NOT NULL,
  chunk_type VARCHAR NOT NULL,
  section_title VARCHAR,
  content TEXT NOT NULL,
  char_count INTEGER NOT NULL,
  embedding vector(1536),
  created_at TIMESTAMP DEFAULT now()
);

CREATE INDEX idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX idx_document_chunks_org_id ON document_chunks(org_id);
```

---

## 4. 비즈니스 로직

### 4.1 문서 처리 파이프라인

```
1. 파일 업로드
   ├─ Supabase Storage에 저장
   ├─ intranet_documents 생성 (status: extracting)
   └─ 응답 즉시 반환

2. 텍스트 추출 (백그라운드)
   ├─ storage_path에서 파일 다운로드
   ├─ rfp_parser.extract_text_from_file() 호출
   ├─ extracted_text 업데이트
   └─ status: chunking으로 변경

3. 청킹 (백그라운드)
   ├─ document_chunker.chunk_document() 호출
   ├─ doc_type별 청킹 규칙 적용
   └─ status: embedding으로 변경

4. 임베딩 생성 (백그라운드)
   ├─ 청크 100개 단위로 배치 처리
   ├─ embedding_service.generate_embeddings_batch() 호출
   ├─ document_chunks 레코드 생성 (embedding 포함)
   └─ status: completed로 변경

5. 프로젝트 메타 시드 (조건부)
   ├─ doc_type이 "실적"일 때만 시도
   ├─ import_project() 호출
   └─ capabilities, client_intelligence, market_price_data 생성
```

### 4.2 에러 처리

| 상황 | 감지 방법 | 처리 |
|------|---------|------|
| 파일 파싱 실패 | extract_text_from_file() 예외 | status: failed, error_message 저장 |
| 텍스트 길이 < 50자 | len(text.strip()) < 50 | status: failed, error 메시지 |
| 청킹 결과 0건 | len(chunks) == 0 | status: failed, error 메시지 |
| 임베딩 API 오류 | generate_embeddings_batch() 예외 | retry 3회 후 status: failed |
| DB 저장 실패 | insert() 예외 | status: failed, 트랜잭션 롤백 |

### 4.3 권한 검증

**API 엔드포인트:**
- 모든 엔드포인트: `require_project_access()` 의존성 사용 (이미 구현됨)
- 문서 조회: org_id로 자동 필터링

**RLS 정책:**
- document_chunks 테이블: org_id 기반 (마이그레이션 필요 확인)

---

## 5. 구현 체크리스트

### 5.1 백엔드

- [ ] `app/models/document_schemas.py` 작성 (Pydantic 스키마 5개)
- [ ] `app/api/routes_documents.py` 작성 (5개 엔드포인트)
  - [ ] POST /api/documents/upload
  - [ ] GET /api/documents
  - [ ] GET /api/documents/{id}
  - [ ] POST /api/documents/{id}/process
  - [ ] GET /api/documents/{id}/chunks
- [ ] 비동기 처리 구현 (asyncio + Celery 또는 RQ)
- [ ] 에러 처리 + 로깅
- [ ] API 권한 검증
- [ ] `app/main.py`에 라우터 등록

### 5.2 데이터베이스

- [ ] intranet_documents 테이블 스키마 확인
- [ ] document_chunks 테이블 스키마 확인
- [ ] RLS 정책 설정 (org_id 기반)
- [ ] 인덱스 생성 확인

### 5.3 테스트

- [ ] 단위 테스트: 각 API 엔드포인트
- [ ] 통합 테스트: 파일 업로드 → 처리 → 조회
- [ ] 권한 테스트: 다른 org 접근 차단
- [ ] 에러 테스트: 큰 파일, 손상된 파일, 빈 파일

### 5.4 문서

- [ ] API 문서 (Swagger)
- [ ] 처리 플로우 다이어그램
- [ ] 에러 코드 참조

---

## 6. 구현 순서

### Phase 1: 코어 API (Priority: HIGH)
1. `routes_documents.py` — POST /api/documents/upload
2. `routes_documents.py` — GET /api/documents/{id}
3. `document_schemas.py` — Pydantic 스키마

### Phase 2: 목록 조회 (Priority: HIGH)
4. `routes_documents.py` — GET /api/documents (목록 + 필터)
5. `routes_documents.py` — GET /api/documents/{id}/chunks

### Phase 3: 재처리 (Priority: MEDIUM)
6. `routes_documents.py` — POST /api/documents/{id}/process

### Phase 4: 테스트 (Priority: MEDIUM)
7. 통합 테스트
8. 권한 테스트

---

## 7. 성능 고려사항

| 항목 | 목표 | 방안 |
|------|------|------|
| 임베딩 생성 | 100개 청크당 2초 | 배치 처리 (100개 단위) |
| DB 저장 | 50개 레코드 일괄 insert | 배치 insert (50개 단위) |
| 파일 크기 | 최대 500MB | 클라이언트 validation + 서버 제한 |
| 동시 처리 | 최대 5개 문서 동시 처리 | 큐 기반 처리 (Celery/RQ) |

---

## 8. 보안 고려사항

| 위험 | 대응 |
|------|------|
| 악성 파일 업로드 | 파일 타입 검증 (Magic Bytes) |
| 대용량 파일 DoS | 파일 크기 제한 (500MB) |
| org 간 데이터 유출 | RLS + org_id 필터링 |
| 임베딩 API 비용 초과 | 요청당 토큰 예산 계산 + 제한 |

---

## 9. 의존성 확인

**내부 모듈 (기존 사용 가능):**
- ✅ `app/services/document_ingestion.py` — process_document(), import_project()
- ✅ `app/services/document_chunker.py` — chunk_document()
- ✅ `app/services/embedding_service.py` — generate_embeddings_batch()
- ✅ `app/services/rfp_parser.py` — extract_text_from_file()
- ✅ `app/api/deps.py` — require_project_access()

**외부 라이브러리:**
- ✅ PyPDF2, python-docx, python-pptx, python-hwpx (이미 설치됨)

**확인 필요:**
- [ ] document_chunks 테이블의 embedding 칼럼 (pgvector)
- [ ] intranet_documents, document_chunks 테이블의 RLS 정책

---

## 10. 참고

**테이블 스키마 위치:**
- `database/schema_v3.4.sql`

**기존 코드 참고:**
- `app/services/document_ingestion.py` (359줄 — 구현됨)
- `app/api/routes_proposal.py` (권한 패턴)
- `app/api/routes_artifacts.py` (파일 다운로드 패턴)

