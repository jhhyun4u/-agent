# 문서 수집 파이프라인 (document_ingestion.py) — Plan 문서

**Feature**: document_ingestion.py  
**Phase**: PLAN  
**Created**: 2026-04-02  
**Status**: Ready for DESIGN

---

## 📋 요구사항

### 기능 요구사항

#### 1. 문서 업로드 & 저장 (API)
- **엔드포인트**: `POST /api/documents/upload`
- **입력**: 파일 (PDF, HWP, HWPX, DOCX, DOC) + 메타데이터 (doc_type, doc_subtype, project_id)
- **처리**: Supabase Storage에 저장 + intranet_documents 레코드 생성
- **출력**: DocumentResponse (id, filename, size, status, uploaded_at)
- **상태 관리**: processing_status = "pending" → "extracting" → "chunking" → "embedding" → "completed" | "failed"

#### 2. 문서 처리 파이프라인
**프로세스**: `process_document(document_id, org_id)`
```
텍스트 추출 → 청킹 → 임베딩 생성 → DB 저장
```

**2-1. 텍스트 추출 (Extraction)**
- Supabase Storage에서 파일 다운로드
- 파일 타입별 텍스트 추출 (file_utils.extract_text_from_file)
- 추출된 텍스트 저장 (extracted_text, total_chars)
- 최소 텍스트 길이 검증 (50자 이상)

**2-2. 청킹 (Chunking)**
- 문서 타입별 지능형 청킹 (document_chunker.chunk_document)
  - **제안서/보고서**: 제목 기반 섹션 분할
  - **계약서**: 조항(제N조) 단위
  - **기타**: 고정 윈도우 + 오버랩
- 매개변수: max_chunk_chars=3000, overlap_chars=200
- 출력: list[Chunk] (index, chunk_type, section_title, content, char_count)

**2-3. 임베딩 생성 (Embedding)**
- OpenAI text-embedding-3-small 사용 (1536차원)
- 배치 처리 (최대 100건)
- 텍스트 길이 제한: 8000자
- 실패 시 제로 벡터 반환

**2-4. DB 저장 (Storage)**
- document_chunks 테이블에 일괄 삽입 (배치: 50건)
- 기존 청크 삭제 후 재삽입 (reprocess 대응)
- intranet_documents 업데이트 (chunk_count, processing_status=completed)

#### 3. 프로젝트 메타 KB 시드
**프로세스**: `import_project(org_id, project_data, upsert=False)`

**3-1. 프로젝트 레코드 (intranet_projects)**
- 중복 체크: legacy_idx + board_id 기반
- 프로젝트 임베딩 생성 (project_name + client_name + keywords + team)
- 신규 생성 또는 upsert 업데이트
- 반환: {id, action: "created"|"updated"|"skipped"}

**3-2. KB 자동 시드**
- **Capability** (수행실적 역량): _seed_capability
  - Type: track_record
  - Title: project_name
  - Detail: 발주기관 + PM + 예산 + 기간
  
- **Client Intelligence** (발주기관 정보): _seed_client_intelligence
  - client_name, contact_info (manager/tel/email)
  - relationship: neutral
  
- **Market Price Data** (시장가격): _seed_market_price_data
  - project_name, client_name, domain, budget_krw
  - source: "intranet_migration"

#### 4. 문서 조회 & 관리 (API)
- **목록**: `GET /api/documents` (필터 + 페이지네이션)
- **상세**: `GET /api/documents/{id}` (메타데이터 + 청크 목록)
- **청크**: `GET /api/documents/{id}/chunks` (청크 데이터)
- **재처리**: `POST /api/documents/{id}/process` (실패 문서)
- **삭제**: `DELETE /api/documents/{id}` (문서 + 청크)

---

## 🏗️ 시스템 설계

### 데이터 구조

#### intranet_documents
```
id: UUID
org_id: UUID
filename: string (max 255)
doc_type: string (보고서|제안서|실적|기타)
doc_subtype: string? (분류/세부 타입)
project_id: UUID? (선택적)
storage_path: string (path/to/file.pdf)
file_size_bytes: integer
extracted_text: text (추출된 텍스트)
total_chars: integer
processing_status: string (pending|extracting|chunking|embedding|completed|failed)
chunk_count: integer (생성된 청크 수)
error_message: string? (실패 사유)
created_at: timestamp
updated_at: timestamp
```

#### document_chunks
```
id: UUID
document_id: UUID (FK)
org_id: UUID
chunk_index: integer (0부터 시작)
chunk_type: string (section|slide|article|window)
section_title: string? (제목 기반 청킹)
content: text (최대 8000자)
char_count: integer
embedding: vector[1536] (pgvector)
created_at: timestamp
```

### 처리 흐름

```
Upload (sync)
  ↓
intranet_documents 레코드 생성 (status=pending)
  ↓
Background: process_document() [async]
  ├─ Extraction (storage_path → extracted_text)
  ├─ Validation (total_chars ≥ 50)
  ├─ Chunking (type-specific strategy)
  ├─ Embedding (batch: 100 chunks)
  ├─ Storage (insert into document_chunks)
  └─ Update (status=completed | failed)
  
Client: Poll GET /api/documents/{id} (status)
```

### 에러 처리

| 경우 | 상태 | 메시지 | 대응 |
|------|------|--------|------|
| 파일 너무 큼 | 400 | "파일이 XX MB를 초과합니다" | 재업로드 |
| 지원 안 함 형식 | 415 | "지원하지 않는 파일 형식입니다" | 형식 변환 |
| 텍스트 추출 실패 | failed | 추출 오류 메시지 | 재처리 |
| 텍스트 너무 짧음 | failed | "텍스트가 너무 짧음" | 문서 재검토 |
| 청킹 실패 | failed | "청킹 결과 0건" | 자동 재처리 |
| 임베딩 타임아웃 | failed | "임베딩 생성 실패" | 재처리 |

---

## 📦 API 명세

### 1. 문서 업로드
```
POST /api/documents/upload
Content-Type: multipart/form-data

file: File (required)
doc_type: string (required) — 보고서|제안서|실적|기타
doc_subtype: string? (optional)
project_id: UUID? (optional)

Response 201:
{
  "id": "uuid",
  "filename": "proposal.pdf",
  "file_size_bytes": 2048000,
  "doc_type": "제안서",
  "doc_subtype": null,
  "processing_status": "pending",
  "uploaded_at": "2026-04-02T12:00:00Z"
}
```

### 2. 문서 목록
```
GET /api/documents?org_id=uuid&status=completed&page=1&limit=20

Response 200:
{
  "total": 45,
  "page": 1,
  "limit": 20,
  "items": [
    {
      "id": "uuid",
      "filename": "...",
      "doc_type": "제안서",
      "processing_status": "completed",
      "chunk_count": 12,
      "uploaded_at": "..."
    }
  ]
}
```

### 3. 문서 상세 & 청크 목록
```
GET /api/documents/{id}

Response 200:
{
  "id": "uuid",
  "filename": "proposal.pdf",
  "doc_type": "제안서",
  "file_size_bytes": 2048000,
  "extracted_text_preview": "첫 500자...",
  "total_chars": 45000,
  "processing_status": "completed",
  "chunk_count": 12,
  "error_message": null,
  "uploaded_at": "...",
  "updated_at": "...",
  "chunks": [
    {
      "chunk_index": 0,
      "chunk_type": "section",
      "section_title": "제1장 제안 개요",
      "content_preview": "...",
      "char_count": 3000
    }
  ]
}
```

### 4. 문서 재처리
```
POST /api/documents/{id}/process

Response 200:
{
  "id": "uuid",
  "status": "pending",
  "message": "문서 재처리가 시작되었습니다"
}
```

### 5. 문서 삭제
```
DELETE /api/documents/{id}

Response 204: (No Content)
```

---

## 🔌  의존성 & 외부 서비스

| 서비스 | 용도 | 설정 |
|--------|------|------|
| **Supabase Storage** | 파일 저장소 | `settings.storage_bucket_intranet` |
| **Supabase PostgreSQL** | 메타데이터 + 벡터 저장 | `intranet_documents`, `document_chunks` |
| **OpenAI Embeddings** | 1536차원 벡터 생성 | `settings.openai_api_key` |
| **file_utils** | PDF/HWP/HWPX/DOCX 파싱 | `extract_text_from_file()` |

---

## 🎯 성공 기준

| 항목 | 기준 |
|------|------|
| **문서 업로드** | 5초 이내 응답, 최대 100MB |
| **텍스트 추출** | 99% 성공률 (형식 오류 제외) |
| **청킹** | 최소 2개 청크, 최대 3000자 |
| **임베딩** | 배치당 < 2초 |
| **DB 저장** | 50건 배치 < 1초 |
| **전체 처리** | 문서당 < 30초 (< 100MB) |
| **에러 처리** | 실패 시 자동 로그 + 상태 업데이트 |

---

## 📅 일정

| 단계 | 소요시간 | 결과물 |
|------|---------|--------|
| PLAN | 1시간 | 이 문서 ✓ |
| DESIGN | 2시간 | 설계 사양 (DB 스키마, 에러 핸들링, 캐싱) |
| DO | 4시간 | 테스트 완료된 구현 코드 |
| CHECK | 1시간 | 설계-구현 갭 분석 (Match Rate ≥ 90%) |
| DEPLOY | 1시간 | DEV → STAGING → PROD |

---

## ✅ 다음 단계

→ **DESIGN 단계**: 설계 사양 문서 작성 (db_schema, error_handling, caching, security)
