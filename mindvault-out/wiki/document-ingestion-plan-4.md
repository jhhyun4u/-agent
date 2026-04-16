# Document Ingestion 기능 계획 (Plan) & 4. 구현 범위
Cohesion: 0.09 | Nodes: 22

## Key Nodes
- **Document Ingestion 기능 계획 (Plan)** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 10 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
  - -> contains -> [[9]]
  - -> contains -> [[10]]
- **4. 구현 범위** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 4 connections
  - -> contains -> [[41-api]]
  - -> contains -> [[42]]
  - -> contains -> [[43-v20]]
  - <- contains <- [[document-ingestion-plan]]
- **6. 예상 산출물** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 4 connections
  - -> contains -> [[61]]
  - -> contains -> [[62]]
  - -> contains -> [[63]]
  - <- contains <- [[document-ingestion-plan]]
- **2. 요구사항** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 3 connections
  - -> contains -> [[21]]
  - -> contains -> [[22]]
  - <- contains <- [[document-ingestion-plan]]
- **3. 현황 분석** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 3 connections
  - -> contains -> [[31]]
  - -> contains -> [[32]]
  - <- contains <- [[document-ingestion-plan]]
- **4.2 데이터베이스** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[4]]
- **sql** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- has_code_example <- [[42]]
- **1. 개요** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[document-ingestion-plan]]
- **10. 참고 사항** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[document-ingestion-plan]]
- **2.1 기본 요구사항** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **2.2 데이터 범위** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **3.1 기존 구현** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **3.2 의존성** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **4.1 백엔드 (API)** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **4.3 프론트엔드 (선택사항, v2.0)** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **5. 기술 스택** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[document-ingestion-plan]]
- **6.1 코드 변경사항** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[6]]
- **6.2 테스트** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[6]]
- **6.3 문서** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[6]]
- **7. 일정** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[document-ingestion-plan]]
- **8. 성공 기준** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[document-ingestion-plan]]
- **9. 위험 요소 및 완화 방안** (C:\project\tenopa proposer\docs\archive\2026-03\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[document-ingestion-plan]]

## Internal Relationships
- 2. 요구사항 -> contains -> 2.1 기본 요구사항 [EXTRACTED]
- 2. 요구사항 -> contains -> 2.2 데이터 범위 [EXTRACTED]
- 3. 현황 분석 -> contains -> 3.1 기존 구현 [EXTRACTED]
- 3. 현황 분석 -> contains -> 3.2 의존성 [EXTRACTED]
- 4. 구현 범위 -> contains -> 4.1 백엔드 (API) [EXTRACTED]
- 4. 구현 범위 -> contains -> 4.2 데이터베이스 [EXTRACTED]
- 4. 구현 범위 -> contains -> 4.3 프론트엔드 (선택사항, v2.0) [EXTRACTED]
- 4.2 데이터베이스 -> has_code_example -> sql [EXTRACTED]
- 6. 예상 산출물 -> contains -> 6.1 코드 변경사항 [EXTRACTED]
- 6. 예상 산출물 -> contains -> 6.2 테스트 [EXTRACTED]
- 6. 예상 산출물 -> contains -> 6.3 문서 [EXTRACTED]
- Document Ingestion 기능 계획 (Plan) -> contains -> 1. 개요 [EXTRACTED]
- Document Ingestion 기능 계획 (Plan) -> contains -> 2. 요구사항 [EXTRACTED]
- Document Ingestion 기능 계획 (Plan) -> contains -> 3. 현황 분석 [EXTRACTED]
- Document Ingestion 기능 계획 (Plan) -> contains -> 4. 구현 범위 [EXTRACTED]
- Document Ingestion 기능 계획 (Plan) -> contains -> 5. 기술 스택 [EXTRACTED]
- Document Ingestion 기능 계획 (Plan) -> contains -> 6. 예상 산출물 [EXTRACTED]
- Document Ingestion 기능 계획 (Plan) -> contains -> 7. 일정 [EXTRACTED]
- Document Ingestion 기능 계획 (Plan) -> contains -> 8. 성공 기준 [EXTRACTED]
- Document Ingestion 기능 계획 (Plan) -> contains -> 9. 위험 요소 및 완화 방안 [EXTRACTED]
- Document Ingestion 기능 계획 (Plan) -> contains -> 10. 참고 사항 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Document Ingestion 기능 계획 (Plan), 4. 구현 범위, 6. 예상 산출물를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 document_ingestion.plan.md이다.

### Key Facts
- **버전**: v1.0 **작성일**: 2026-03-29 **상태**: APPROVED
- **intranet_documents (기존 확인)** ```sql id, org_id, filename, doc_type, doc_subtype, storage_path, extracted_text, processing_status, error_message, total_chars, chunk_count, created_at ```
- **목표**: 인트라넷 문서를 자동으로 수집하고, 텍스트 추출 → 청킹 → 임베딩 → 저장하는 **자동화된 문서 처리 파이프라인** 구축
- **기존 코드 위치:** - `app/services/document_ingestion.py` — 핵심 로직 (359줄) - `app/services/document_chunker.py` — 청킹 로직 - `app/services/embedding_service.py` — 임베딩 서비스 - `database/schema_v3.4.sql` — 테이블 정의
- | 요구사항 | 설명 | 우선도 | |---------|------|--------| | **문서 업로드** | UI에서 파일 선택 후 Supabase Storage에 저장 | 높음 | | **텍스트 추출** | PDF/HWP/HWPX → 텍스트 변환 (rfp_parser.py 활용) | 높음 | | **청킹** | 문서별 타입(보고서/제안서/실적 등)에 맞게 청킹 | 높음 | | **임베딩 생성** | Claude API로 청크별 벡터 생성 (batch) | 높음 | | **DB 저장** | document_chunks 테이블에…
