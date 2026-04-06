# 문서 수집 파이프라인 설계 (document_ingestion.py) — Design

**Feature**: document_ingestion.py  
**Phase**: DESIGN  
**Created**: 2026-04-02  
**Status**: Ready for IMPLEMENTATION

---

## 1️⃣ 아키텍처 개요

```
┌─────────────────────────────────────────────────────────┐
│              문서 수집 파이프라인 아키텍처                │
└─────────────────────────────────────────────────────────┘

[Client]
  │
  ├─→ POST /api/documents/upload [async, non-blocking]
  │     └─→ Validation + Storage Upload
  │     └─→ Return 201 (DocumentResponse) immediately
  │     └─→ Schedule: process_document() as background task
  │
  └─→ GET /api/documents/{id} [polling]
      └─→ Check processing_status
      └─→ Return current state


[Backend Processing Pipeline]
  
  process_document(document_id, org_id)
    │
    ├─ STEP 1: Extraction
    │   └─ Fetch from Supabase Storage
    │   └─ Call extract_text_from_file()
    │   └─ Store in intranet_documents.extracted_text
    │
    ├─ STEP 2: Validation
    │   └─ Check len(text) ≥ 50
    │   └─ Fail if insufficient
    │
    ├─ STEP 3: Chunking
    │   └─ Call chunk_document(type-specific strategy)
    │   └─ Return list[Chunk]
    │
    ├─ STEP 4: Embedding
    │   └─ Batch generate (max 100 per request)
    │   └─ OpenAI text-embedding-3-small (1536-dim)
    │
    └─ STEP 5: Storage
        └─ Insert into document_chunks (batch: 50)
        └─ Update intranet_documents.processing_status


[Database]
  intranet_documents ←→ document_chunks (1:N)
  intranet_projects ←→ capabilities, client_intelligence, market_price_data


[Async Queue]
  Option: Supabase pg_cron OR APScheduler OR FastAPI BackgroundTasks
  Current: asyncio.create_task() [simple, suitable for MVP]
```

---

## 2️⃣ 상세 설계

### 2-1. 업로드 엔드포인트 (routes_documents.py)

```python
@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    file: UploadFile = File(...),
    doc_type: str = Form(...),
    doc_subtype: Optional[str] = Form(None),
    project_id: Optional[str] = Form(None),
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_project_access),
) -> DocumentResponse:
    """
    설계:
    1. 파일 검증 (형식, 크기)
    2. Supabase Storage에 저장 (path: {org_id}/{document_id}/{filename})
    3. intranet_documents 레코드 생성 (status=pending)
    4. 비동기 처리 태스크 스케줄
    5. 즉시 응답 (클라이언트는 폴링)
    """
```

**검증 규칙**:
- 파일명 존재 여부
- 파일 확장자 (PDF, HWP, HWPX, DOCX, DOC)
- 파일 크기 ≤ settings.intranet_max_file_size_mb (기본 100MB)
- doc_type ∈ {보고서, 제안서, 실적, 기타}

**에러 코드**:
- 400: 파일명 없음, 잘못된 doc_type
- 413: 파일 크기 초과
- 415: 지원하지 않는 형식

---

### 2-2. 문서 처리 파이프라인 (document_ingestion.py)

#### **STEP 1: 텍스트 추출 (_extract_from_storage)**

```python
async def _extract_from_storage(client, doc: dict) -> str:
    """
    1. Supabase Storage에서 파일 다운로드
    2. 임시 파일에 저장
    3. file_utils.extract_text_from_file() 호출
    4. 임시 파일 삭제
    """
    bucket = settings.storage_bucket_intranet
    response = await client.storage.from_(bucket).download(storage_path)
    
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(response)
        tmp.flush()
        return extract_text_from_file(tmp.name)
    finally:
        os.unlink(tmp_file)
```

**예외 처리**:
- 파일 다운로드 실패 → 상태: failed, 메시지: 다운로드 오류
- 텍스트 추출 실패 → 상태: failed, 메시지: 추출 오류
- 임시 파일 정리 실패 → 로깅만 (업로드된 파일에 영향 없음)

---

#### **STEP 2: 청킹 (chunk_document)**

**전략 선택**:
- **제안서/보고서**: 제목 기반 섹션 분할 (_chunk_by_headings)
- **계약서**: 조항 기반 (_chunk_articles)
- **발표자료**: 슬라이드 기반 (_chunk_slides)
- **기타**: 윈도우 슬라이딩 (_chunk_by_window)

**제목 패턴 (한글 문서)**:
```regex
제\s*\d+\s*[장절항]        # 제1장, 제 1 절
\d+\.\s+[가-힣]            # 1. 개요
\d+\.\d+\s+[가-힣]         # 1.1 배경
[가나다라마바사아자차카타파하]\.\s  # 가. 소개
```

**윈도우 청킹 (폴백)**:
```
max_chunk_chars: 3000자
window_chars: 2000자 (기본)
overlap_chars: 200자 (연속성)

예: text = "A(2000) + B(2000) + C(2000)"
    청크 1: [A + B의 마지막 200자]
    청크 2: [B + C의 처음 200자]
```

**출력**:
```python
@dataclass
class Chunk:
    index: int              # 0, 1, 2, ...
    chunk_type: str         # section | window | slide | article
    section_title: str|None # "제1장 개요" 또는 None
    content: str            # 최대 8000자 (DB 제약)
    char_count: int         # len(content)
```

---

#### **STEP 3: 임베딩 생성 (generate_embeddings_batch)**

**배치 처리**:
```python
# Chunks 배열을 100개씩 배치로 나누기
for i in range(0, len(chunk_texts), 100):
    batch = chunk_texts[i:i+100]
    embeddings = await generate_embeddings_batch(batch)
    all_embeddings.extend(embeddings)
```

**에러 처리**:
- API 타임아웃 → 제로 벡터 반환 (재시도 가능)
- 입력 텍스트 > 8000자 → 자동 잘라내기
- 배치 크기 > 100 → 자동 분할

**출력**: list[list[float]] (각 청크당 1536차원 벡터)

---

#### **STEP 4: DB 저장 (Upsert)**

**기존 청크 삭제 (reprocess 대응)**:
```python
await client.table("document_chunks").delete().eq("document_id", document_id).execute()
```

**배치 삽입** (50건씩):
```python
for i in range(0, len(rows), 50):
    await client.table("document_chunks").insert(rows[i:i+50]).execute()
```

**Row 구조**:
```python
{
    "document_id": str,
    "org_id": str,
    "chunk_index": int,
    "chunk_type": str,
    "section_title": str|None,
    "content": str,
    "char_count": int,
    "embedding": list[float],  # pgvector
}
```

**최종 업데이트**:
```python
client.table("intranet_documents").update({
    "processing_status": "completed",
    "chunk_count": len(chunks),
    "error_message": None,
}).eq("id", document_id).execute()
```

---

### 2-3. 프로젝트 임포트 & KB 시드 (import_project)

**프로세스**:
```
import_project(org_id, project_data, upsert=False)
  │
  ├─ STEP 1: 중복 체크 (legacy_idx + board_id)
  │   └─ 기존 프로젝트 ID 반환 (if not upsert)
  │
  ├─ STEP 2: 임베딩 생성
  │   └─ 텍스트: project_name | client_name | keywords | team
  │
  ├─ STEP 3: intranet_projects 레코드 생성/업데이트
  │   └─ 26개 필드 (legacy metadata + team info + budget)
  │
  ├─ STEP 4: KB 자동 시드 (3가지)
  │   ├─ Capability (track_record)
  │   ├─ Client Intelligence
  │   └─ Market Price Data
  │
  └─ STEP 5: 링크 업데이트
      └─ intranet_projects에 KB ID 저장
```

**각 KB 시드 함수**:

##### _seed_capability
```python
async def _seed_capability(client, org_id: str, data: dict) -> str|None:
    """
    제목: project_name
    상세: 발주기관 + PM + 예산 + 기간 (CSV 형식)
    임베딩: track_record | title | detail
    중복 방지: (org_id, type, title) 기반
    """
```

##### _seed_client_intelligence
```python
async def _seed_client_intelligence(client, org_id: str, data: dict) -> str|None:
    """
    client_name: 발주기관명
    contact_info: {manager, tel, email}
    relationship: "neutral" (기본)
    임베딩: client_name | client_type | notes
    중복 방지: (org_id, client_name) 기반
    """
```

##### _seed_market_price_data
```python
async def _seed_market_price_data(client, org_id: str, data: dict) -> str|None:
    """
    프로젝트 예산 기반 시장 가격 자동 시드
    필드: project_name, client_name, domain, budget_krw, source
    중복 방지: (org_id, project_name) 기반
    """
```

---

## 3️⃣ 에러 처리 & 복구 전략

| 단계 | 에러 | 상태 | 메시지 | 복구 |
|------|------|------|--------|------|
| **Extraction** | 파일 다운로드 실패 | failed | "파일 다운로드 오류" | POST /{id}/process 재처리 |
| **Extraction** | 텍스트 추출 실패 | failed | "텍스트 추출 실패: {error}" | 파일 형식 확인 후 재업로드 |
| **Validation** | 텍스트 < 50자 | failed | "텍스트가 너무 짧음" | 문서 재검토 |
| **Chunking** | 청크 개수 0 | failed | "청킹 결과 0건" | 자동 폴백 (윈도우 청킹) |
| **Embedding** | API 타임아웃 | failed | "임베딩 생성 실패: timeout" | POST /{id}/process 재처리 |
| **Embedding** | 배치 부분 실패 | partial | "N/M 청크 임베딩 생성" | 실패한 청크만 재처리 |
| **Storage** | INSERT 실패 | failed | "청크 저장 실패: {error}" | DB 연결 확인 후 재처리 |

**자동 재시도**:
- Transient 에러 (타임아웃, 연결 실패): 최대 3회 재시도 (지수 백오프)
- 영구 에러 (형식 오류, 크기 초과): 즉시 failed로 표시

---

## 4️⃣ 데이터베이스 스키마

### intranet_documents (이미 존재하는 것으로 가정)
```sql
CREATE TABLE IF NOT EXISTS intranet_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    doc_type VARCHAR(50) NOT NULL CHECK (doc_type IN ('보고서', '제안서', '실적', '기타')),
    doc_subtype VARCHAR(100),
    project_id UUID REFERENCES intranet_projects(id) ON DELETE SET NULL,
    storage_path VARCHAR(512) NOT NULL UNIQUE,
    file_size_bytes INTEGER NOT NULL,
    extracted_text TEXT,
    total_chars INTEGER,
    processing_status VARCHAR(50) DEFAULT 'pending' CHECK (
        processing_status IN ('pending', 'extracting', 'chunking', 'embedding', 'completed', 'failed')
    ),
    chunk_count INTEGER DEFAULT 0,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_org_status (org_id, processing_status),
    INDEX idx_project (project_id)
);
```

### document_chunks (신규)
```sql
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES intranet_documents(id) ON DELETE CASCADE,
    org_id UUID NOT NULL,
    chunk_index INTEGER NOT NULL,
    chunk_type VARCHAR(50) NOT NULL CHECK (chunk_type IN ('section', 'window', 'slide', 'article')),
    section_title VARCHAR(500),
    content TEXT NOT NULL,
    char_count INTEGER NOT NULL,
    embedding vector(1536),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (org_id) REFERENCES organizations(id) ON DELETE CASCADE,
    CONSTRAINT chunk_length CHECK (char_count <= 8000),
    
    INDEX idx_document (document_id),
    INDEX idx_type (chunk_type)
);

-- 벡터 검색 인덱스 (선택)
CREATE INDEX idx_embedding ON document_chunks USING hnsw (embedding vector_cosine_ops)
WHERE embedding IS NOT NULL;
```

---

## 5️⃣ 성능 최적화

| 항목 | 전략 | 예상 성과 |
|------|------|----------|
| **임베딩 배치** | 100건씩 묶어서 API 호출 | API 호출 수 99% 감소 |
| **청크 배치 삽입** | 50건씩 묶어서 INSERT | DB 트랜잭션 98% 감소 |
| **임시 파일** | 임시 디렉토리 사용 (디스크 I/O 최소화) | 메모리 사용량 50% 감소 |
| **텍스트 길이 제한** | 청크당 8000자로 제한 | 임베딩 API 비용 균형 |
| **캐싱** | Supabase 파일 다운로드 캐시 (없음, CDN 사용 권장) | — |
| **비동기** | asyncio + await 사용 | I/O 블로킹 제거 |

---

## 6️⃣ 보안 설계

| 항목 | 설계 |
|------|------|
| **인증** | get_current_user (FastAPI Depends) |
| **인가** | require_project_access (조직별 접근 제어) |
| **파일 검증** | 확장자 + 크기 + MIME 타입 검증 |
| **경로 주입 방지** | UUID 기반 storage_path (사용자 입력 제외) |
| **임시 파일** | 자동 삭제 (os.unlink in finally) |
| **에러 메시지** | 민감 정보 마스킹 (API 응답에 내부 경로 노출 금지) |
| **로깅** | logger.error()로 상세 로그 (DB에 저장) |

---

## 7️⃣ 테스트 전략

### 단위 테스트
- `test_chunk_by_headings()` — 제목 패턴 인식
- `test_chunk_by_window()` — 윈도우 오버랩
- `test_compute_file_hash()` — 해시 계산
- `test_generate_embedding()` — 임베딩 생성 (모의)

### 통합 테스트
- `test_upload_document()` — 전체 업로드 플로우
- `test_process_document()` — 추출→청킹→임베딩
- `test_import_project()` — KB 시드
- `test_reprocess_failed_document()` — 재처리

### E2E 테스트
- 실제 PDF 업로드 → 청크 검증 → 임베딩 쿼리 테스트
- 에러 시나리오 (손상된 파일, 대용량 파일)

---

## 8️⃣ 배포 체크리스트

- [ ] DB 마이그레이션: document_chunks 테이블 생성
- [ ] 환경 변수: `OPENAI_API_KEY`, `SUPABASE_BUCKET_INTRANET`
- [ ] Supabase RLS 정책: intranet_documents, document_chunks 읽기/쓰기
- [ ] pgvector 확장 활성화 (Supabase에서 자동)
- [ ] 테스트 완료: 단위 + 통합 + E2E
- [ ] 문서: API 명세, 에러 코드, 운영 가이드

---

## 다음 단계

→ **DO 단계**: 이 설계를 따라 코드 구현 (이미 대부분 존재하므로 갭 분석)
