# Changelog

All notable changes to 용역제안 Coworker project are documented here.

---

## [2026-03-29] - Document Ingestion Feature Complete

**Status**: ✅ Complete (95% Match Rate)

### Added
- **5 Document Management APIs**
  - `POST /api/documents/upload` — 파일 업로드 (Supabase Storage)
  - `GET /api/documents` — 문서 목록 조회 (필터+페이지네이션)
  - `GET /api/documents/{id}` — 문서 상세 조회
  - `POST /api/documents/{id}/process` — 수동 재처리
  - `GET /api/documents/{id}/chunks` — 청크 목록 조회

- **8 Pydantic Data Models**
  - DocumentUploadRequest, DocumentResponse, DocumentListResponse
  - DocumentDetailResponse, ChunkResponse, ChunkListResponse
  - DocumentProcessRequest, DocumentProcessResponse

- **Document Processing Pipeline**
  - 텍스트 추출 (PDF/HWP/HWPX/DOCX/PPTX)
  - 자동 청킹 (문서 타입별)
  - 배치 임베딩 생성 (Claude API)
  - 상태 추적 (extracting → chunking → embedding → completed)
  - 프로젝트 메타 자동 시드 (capabilities, client_intelligence, market_price_data)

- **Security & Authorization**
  - 인증 (get_current_user)
  - 인가 (require_project_access)
  - org_id 기반 데이터 격리
  - 파일 크기 제한 (500MB)
  - 파일 타입 검증

- **Error Handling & Logging**
  - 파일 파싱 실패 감지
  - 텍스트 부족 감지 (< 50자)
  - 청킹 결과 0건 감지
  - API 오류 감지
  - 모든 에러 경로에 로깅 적용

### Changed
- `app/main.py` — routes_documents 라우터 등록

### Fixed
- **GAP-1**: list_documents에서 doc_type 필터 미적용 (commit 11c8c8b)
  - count 쿼리에 doc_type 필터 추가
  - 페이지네이션 정확도 개선

### Quality Metrics
- **Design Match Rate**: 95% ✅
- **API Match**: 96% ✅
- **Data Model Match**: 97% ✅
- **Security Compliance**: 100% ✅
- **Code Lines**: ~600줄
- **Endpoints**: 5/5 완전 구현
- **Models**: 8/8 완전 구현
- **PDCA Verification**: 16/16 통과

### Documentation
- Plan: `docs/01-plan/features/document_ingestion.plan.md`
- Design: `docs/02-design/features/document_ingestion.design.md`
- Analysis: `docs/03-analysis/features/document_ingestion.analysis.md`
- Report: `docs/04-report/features/document_ingestion.report.md`

### Implementation Files
- **New**: `app/models/document_schemas.py` (91줄, 8개 모델)
- **New**: `app/api/routes_documents.py` (420+줄, 5개 엔드포인트)
- **Modified**: `app/main.py` (+3줄)

---

## Future Enhancements

### v2.0 - Batch Processing & Migration
- [ ] Celery/APScheduler를 이용한 정기적 자동 처리
- [ ] 레거시 문서 마이그레이션 스크립트
- [ ] 프론트엔드 UI (업로드 폼, 상태 진행률, 청크 미리보기)

### Backlog
- [ ] 문서 삭제 API
- [ ] 청크 벡터 유사도 검색
- [ ] 문서별 처리 이력 추적
- [ ] 대용량 파일 분할 처리 (> 500MB)

---

**보고서**: 2026-03-29 완료 | **PDCA Cycle**: #1 | **Status**: Complete ✅
