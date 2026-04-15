# 문서 수집 파이프라인 (document_ingestion.py) — Plan 문서 & 📦 API 명세
Cohesion: 0.18 | Nodes: 12

## Key Nodes
- **문서 수집 파이프라인 (document_ingestion.py) — Plan 문서** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-04\document_ingestion\document_ingestion.plan.md) -- 7 connections
  - -> contains -> [[1-api]]
  - -> contains -> [[2]]
  - -> contains -> [[3-kb]]
  - -> contains -> [[4-api]]
  - -> contains -> [[intranetdocuments]]
  - -> contains -> [[documentchunks]]
  - -> contains -> [[api]]
- **📦 API 명세** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-04\document_ingestion\document_ingestion.plan.md) -- 6 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - <- contains <- [[documentingestionpy-plan]]
- **2. 문서 처리 파이프라인** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-04\document_ingestion\document_ingestion.plan.md) -- 2 connections
  - <- contains <- [[documentingestionpy-plan]]
  - <- contains <- [[api]]
- **1. 문서 업로드** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-04\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[api]]
- **1. 문서 업로드 & 저장 (API)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-04\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[documentingestionpy-plan]]
- **3. 문서 상세 & 청크 목록** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-04\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[api]]
- **3. 프로젝트 메타 KB 시드** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-04\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[documentingestionpy-plan]]
- **4. 문서 재처리** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-04\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[api]]
- **4. 문서 조회 & 관리 (API)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-04\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[documentingestionpy-plan]]
- **5. 문서 삭제** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-04\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[api]]
- **document_chunks** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-04\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[documentingestionpy-plan]]
- **intranet_documents** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-04\document_ingestion\document_ingestion.plan.md) -- 1 connections
  - <- contains <- [[documentingestionpy-plan]]

## Internal Relationships
- 📦 API 명세 -> contains -> 1. 문서 업로드 [EXTRACTED]
- 📦 API 명세 -> contains -> 2. 문서 처리 파이프라인 [EXTRACTED]
- 📦 API 명세 -> contains -> 3. 문서 상세 & 청크 목록 [EXTRACTED]
- 📦 API 명세 -> contains -> 4. 문서 재처리 [EXTRACTED]
- 📦 API 명세 -> contains -> 5. 문서 삭제 [EXTRACTED]
- 문서 수집 파이프라인 (document_ingestion.py) — Plan 문서 -> contains -> 1. 문서 업로드 & 저장 (API) [EXTRACTED]
- 문서 수집 파이프라인 (document_ingestion.py) — Plan 문서 -> contains -> 2. 문서 처리 파이프라인 [EXTRACTED]
- 문서 수집 파이프라인 (document_ingestion.py) — Plan 문서 -> contains -> 3. 프로젝트 메타 KB 시드 [EXTRACTED]
- 문서 수집 파이프라인 (document_ingestion.py) — Plan 문서 -> contains -> 4. 문서 조회 & 관리 (API) [EXTRACTED]
- 문서 수집 파이프라인 (document_ingestion.py) — Plan 문서 -> contains -> intranet_documents [EXTRACTED]
- 문서 수집 파이프라인 (document_ingestion.py) — Plan 문서 -> contains -> document_chunks [EXTRACTED]
- 문서 수집 파이프라인 (document_ingestion.py) — Plan 문서 -> contains -> 📦 API 명세 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 문서 수집 파이프라인 (document_ingestion.py) — Plan 문서, 📦 API 명세, 2. 문서 처리 파이프라인를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 document_ingestion.plan.md이다.

### Key Facts
- **Feature**: document_ingestion.py **Phase**: PLAN **Created**: 2026-04-02 **Status**: Ready for DESIGN
- 1. 문서 업로드 ``` POST /api/documents/upload Content-Type: multipart/form-data
- **2-1. 텍스트 추출 (Extraction)** - Supabase Storage에서 파일 다운로드 - 파일 타입별 텍스트 추출 (file_utils.extract_text_from_file) - 추출된 텍스트 저장 (extracted_text, total_chars) - 최소 텍스트 길이 검증 (50자 이상)
- 2. 문서 처리 파이프라인 **프로세스**: `process_document(document_id, org_id)` ``` 텍스트 추출 → 청킹 → 임베딩 생성 → DB 저장 ```
- 2. 문서 처리 파이프라인 **프로세스**: `process_document(document_id, org_id)` ``` 텍스트 추출 → 청킹 → 임베딩 생성 → DB 저장 ```
