# Document Ingestion 기능 계획 (Plan)

**버전**: v1.0
**작성일**: 2026-03-29
**상태**: APPROVED

---

## 1. 개요

**목표**: 인트라넷 문서를 자동으로 수집하고, 텍스트 추출 → 청킹 → 임베딩 → 저장하는 **자동화된 문서 처리 파이프라인** 구축

**핵심 가치**:
- 조직 문서 자산을 지식 베이스(KB)로 자동 변환
- 제안 작성 시 관련 문서/실적 자동 추천
- 프로젝트 메타데이터를 역량·클라이언트 정보로 시드

---

## 2. 요구사항

### 2.1 기본 요구사항

| 요구사항 | 설명 | 우선도 |
|---------|------|--------|
| **문서 업로드** | UI에서 파일 선택 후 Supabase Storage에 저장 | 높음 |
| **텍스트 추출** | PDF/HWP/HWPX → 텍스트 변환 (rfp_parser.py 활용) | 높음 |
| **청킹** | 문서별 타입(보고서/제안서/실적 등)에 맞게 청킹 | 높음 |
| **임베딩 생성** | Claude API로 청크별 벡터 생성 (batch) | 높음 |
| **DB 저장** | document_chunks 테이블에 저장 | 높음 |
| **상태 추적** | processing_status: extracting → chunking → embedding → completed | 높음 |
| **프로젝트 메타 시드** | capabilities + client_intelligence + market_price_data 자동 생성 | 중간 |
| **에러 처리** | 추출 실패/텍스트 부족 등 자동 감지 및 로깅 | 중간 |

### 2.2 데이터 범위

**입력:**
- 파일: PDF, HWP, HWPX, DOCX, PPTX (지원 포맷)
- 메타: 문서 타입 (보고서, 제안서, 실적, 기타)
- 출처: 인트라넷 업로드 또는 레거시 마이그레이션

**출력:**
- document_chunks 테이블: 청크 데이터 + 임베딩
- capabilities 테이블: 프로젝트 실적 역량
- client_intelligence 테이블: 발주기관 정보
- market_price_data 테이블: 시장가격 데이터

---

## 3. 현황 분석

### 3.1 기존 구현

**파일**: `app/services/document_ingestion.py` (359줄)

**구현 내용:**
- ✅ `process_document()` — 단일 문서 처리 파이프라인
  - 텍스트 추출 (기존 extracted_text 재활용)
  - 청킹 (document_chunker.py 활용)
  - 배치 임베딩 생성 (100개 단위)
  - 결과 저장 (document_chunks 테이블)

- ✅ `import_project()` — 프로젝트 메타 임포트
  - intranet_projects 생성/업데이트
  - capabilities 자동 시드
  - client_intelligence 자동 시드
  - market_price_data 자동 시드

- ✅ 유틸: `_extract_from_storage()`, `_update_doc_status()` 등

**미구현 부분:**
- ❌ API 엔드포인트 (업로드, 상태 조회, 처리 시작)
- ❌ 프론트엔드 UI (문서 업로드 폼, 상태 표시)
- ❌ 배치 처리 스케줄러
- ❌ 마이그레이션 스크립트

### 3.2 의존성

**내부 모듈:**
- `app/services/document_chunker.py` — 문서 청킹 로직
- `app/services/embedding_service.py` — 임베딩 생성 (Claude API)
- `app/services/rfp_parser.py` — 파일 파싱 (PDF/HWP 등)

**DB 테이블:**
- `intranet_documents` — 문서 메타
- `document_chunks` — 청크 + 임베딩
- `intranet_projects` — 프로젝트 메타
- `capabilities` — 역량 (track_record 타입)
- `client_intelligence` — 발주기관
- `market_price_data` — 시장가격

---

## 4. 구현 범위

### 4.1 백엔드 (API)

**새 엔드포인트:**

| 메서드 | 경로 | 기능 | 상태 |
|--------|------|------|------|
| POST | `/api/documents/upload` | 문서 업로드 (파일 + 메타) | ❌ |
| GET | `/api/documents/{id}` | 문서 상세 + 처리 상태 | ❌ |
| GET | `/api/documents` | 문서 목록 + 필터 | ❌ |
| POST | `/api/documents/{id}/process` | 수동 처리 시작 | ❌ |
| GET | `/api/documents/{id}/chunks` | 문서의 청크 목록 | ❌ |

**기존 함수 재사용:**
- `process_document()` ✅ (내부 함수)
- `import_project()` ✅ (내부 함수)

### 4.2 데이터베이스

**필요한 테이블/칼럼:**

**intranet_documents (기존 확인)**
```sql
id, org_id, filename, doc_type, doc_subtype,
storage_path, extracted_text, processing_status,
error_message, total_chars, chunk_count, created_at
```

**document_chunks (기존 확인)**
```sql
id, document_id, org_id, chunk_index, chunk_type,
section_title, content, char_count, embedding, created_at
```

**확인 필요:**
- RLS 정책 (org_id 기반 격리)
- 인덱스 (document_id, org_id, chunk_type)

### 4.3 프론트엔드 (선택사항, v2.0)

**화면:**
- [ ] 문서 업로드 폼
- [ ] 문서 목록 + 처리 상태
- [ ] 청크 미리보기

**구현은 API 완성 후 (우선도 낮음)**

---

## 5. 기술 스택

| 계층 | 기술 | 용도 |
|------|------|------|
| Backend | FastAPI | REST API |
| Async | asyncio | 비동기 처리 |
| DB | Supabase PostgreSQL | 저장소 |
| File Storage | Supabase Storage | 문서 저장 |
| Embedding | Claude API | 벡터 생성 |
| Parsing | python-pdf2, python-hwpx | 파일 파싱 |

---

## 6. 예상 산출물

### 6.1 코드 변경사항

| 파일 | 변경 | 줄수 |
|------|------|------|
| `app/api/routes_documents.py` | 신규 (5개 엔드포인트) | ~200 |
| `app/models/document_schemas.py` | 신규 (Pydantic 스키마) | ~100 |
| `app/graph/nodes/document_ingest_node.py` | 신규 (LangGraph 노드) | ~150 |
| `app/main.py` | 라우터 추가 | ~5 |

### 6.2 테스트

- [ ] API 단위 테스트 (pytest)
- [ ] 통합 테스트 (파일 업로드 → 임베딩 저장)
- [ ] 권한 테스트 (다른 org 접근 차단)

### 6.3 문서

- [ ] Design 문서 (구현 상세)
- [ ] API 문서 (엔드포인트 명세)

---

## 7. 일정

| 단계 | 내용 | 예상 일정 |
|------|------|---------|
| Plan | 요구사항 정의 | ✅ 완료 |
| Design | 아키텍처 설계 | 필요 |
| Do | 코드 구현 | 필요 |
| Check | 갭 분석 | 필요 |
| Act | 개선/수정 | 필요 |

---

## 8. 성공 기준

- [ ] 5개 API 엔드포인트 구현
- [ ] 파일 업로드 → 텍스트 추출 → 청킹 → 임베딩 → 저장 자동화
- [ ] 에러 처리 (추출 실패, 텍스트 부족 등)
- [ ] 프로젝트 메타 자동 시드 (capabilities, client_intelligence)
- [ ] API 테스트 80% 이상
- [ ] Design 문서 95% 이상 구현 일치

---

## 9. 위험 요소 및 완화 방안

| 위험 | 영향 | 완화 방안 |
|------|------|---------|
| 대용량 파일 처리 시간 초과 | 사용자 대기 | 비동기 큐 + 진행률 반환 |
| 임베딩 API 비용 증가 | 예산 초과 | 배치 처리 + 중복 제거 |
| 파일 파싱 실패 | 문서 미처리 | 폴백 + 상세 에러 로깅 |
| RLS 정책 누락 | 보안 문제 | 마이그레이션 전 검증 |

---

## 10. 참고 사항

**기존 코드 위치:**
- `app/services/document_ingestion.py` — 핵심 로직 (359줄)
- `app/services/document_chunker.py` — 청킹 로직
- `app/services/embedding_service.py` — 임베딩 서비스
- `database/schema_v3.4.sql` — 테이블 정의

**관련 이슈:**
- document_chunks에 embedding 칼럼 유무 확인
- intranet_documents 테이블 스키마 확인 (storage_path, extracted_text 칼럼)

