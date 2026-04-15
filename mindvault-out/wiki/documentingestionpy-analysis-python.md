# 문서 수집 파이프라인 갭 분석 (document_ingestion.py) — Analysis & python
Cohesion: 0.16 | Nodes: 15

## Key Nodes
- **문서 수집 파이프라인 갭 분석 (document_ingestion.py) — Analysis** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\document_ingestion.py.analysis.md) -- 9 connections
  - -> contains -> [[api-55-100]]
  - -> contains -> [[55-100]]
  - -> contains -> [[45-80]]
  - -> contains -> [[56-83]]
  - -> contains -> [[68-75]]
  - -> contains -> [[db-12]]
  - -> contains -> [[18-12]]
  - -> contains -> [[api]]
  - -> contains -> [[approved-90]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\document_ingestion.py.analysis.md) -- 4 connections
  - <- has_code_example <- [[18-12]]
  - <- has_code_example <- [[post-upload]]
  - <- has_code_example <- [[get-list]]
  - <- has_code_example <- [[step-4-embedding]]
- **API 엔드포인트 상세 비교** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\document_ingestion.py.analysis.md) -- 4 connections
  - -> contains -> [[post-upload]]
  - -> contains -> [[get-list]]
  - -> contains -> [[step-4-embedding]]
  - <- contains <- [[documentingestionpy-analysis]]
- **❌ 테스트 커버리지 (1/8 = 12%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\document_ingestion.py.analysis.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[documentingestionpy-analysis]]
- **⚠️ DB 스키마 (1/2 테이블 존재)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\document_ingestion.py.analysis.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[documentingestionpy-analysis]]
- **GET / (list) ✅** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\document_ingestion.py.analysis.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[api]]
- **POST /upload ✅** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\document_ingestion.py.analysis.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[api]]
- **STEP 4: Embedding 배치 처리 ✅** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\document_ingestion.py.analysis.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[api]]
- **sql** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\document_ingestion.py.analysis.md) -- 1 connections
  - <- has_code_example <- [[db-12]]
- **✅ 성능 최적화 (4/5 = 80%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\document_ingestion.py.analysis.md) -- 1 connections
  - <- contains <- [[documentingestionpy-analysis]]
- **✅ 파이프라인 단계 (5/5 = 100%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\document_ingestion.py.analysis.md) -- 1 connections
  - <- contains <- [[documentingestionpy-analysis]]
- **✅ 보안 (5/6 = 83%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\document_ingestion.py.analysis.md) -- 1 connections
  - <- contains <- [[documentingestionpy-analysis]]
- **⚠️ 에러 처리 (6/8 = 75%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\document_ingestion.py.analysis.md) -- 1 connections
  - <- contains <- [[documentingestionpy-analysis]]
- **✅ API 엔드포인트 (5/5 = 100%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\document_ingestion.py.analysis.md) -- 1 connections
  - <- contains <- [[documentingestionpy-analysis]]
- **배포 판정: ✅ **APPROVED** (≥90%)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\document_ingestion.py.analysis.md) -- 1 connections
  - <- contains <- [[documentingestionpy-analysis]]

## Internal Relationships
- ❌ 테스트 커버리지 (1/8 = 12%) -> has_code_example -> python [EXTRACTED]
- API 엔드포인트 상세 비교 -> contains -> POST /upload ✅ [EXTRACTED]
- API 엔드포인트 상세 비교 -> contains -> GET / (list) ✅ [EXTRACTED]
- API 엔드포인트 상세 비교 -> contains -> STEP 4: Embedding 배치 처리 ✅ [EXTRACTED]
- ⚠️ DB 스키마 (1/2 테이블 존재) -> has_code_example -> sql [EXTRACTED]
- 문서 수집 파이프라인 갭 분석 (document_ingestion.py) — Analysis -> contains -> ✅ API 엔드포인트 (5/5 = 100%) [EXTRACTED]
- 문서 수집 파이프라인 갭 분석 (document_ingestion.py) — Analysis -> contains -> ✅ 파이프라인 단계 (5/5 = 100%) [EXTRACTED]
- 문서 수집 파이프라인 갭 분석 (document_ingestion.py) — Analysis -> contains -> ✅ 성능 최적화 (4/5 = 80%) [EXTRACTED]
- 문서 수집 파이프라인 갭 분석 (document_ingestion.py) — Analysis -> contains -> ✅ 보안 (5/6 = 83%) [EXTRACTED]
- 문서 수집 파이프라인 갭 분석 (document_ingestion.py) — Analysis -> contains -> ⚠️ 에러 처리 (6/8 = 75%) [EXTRACTED]
- 문서 수집 파이프라인 갭 분석 (document_ingestion.py) — Analysis -> contains -> ⚠️ DB 스키마 (1/2 테이블 존재) [EXTRACTED]
- 문서 수집 파이프라인 갭 분석 (document_ingestion.py) — Analysis -> contains -> ❌ 테스트 커버리지 (1/8 = 12%) [EXTRACTED]
- 문서 수집 파이프라인 갭 분석 (document_ingestion.py) — Analysis -> contains -> API 엔드포인트 상세 비교 [EXTRACTED]
- 문서 수집 파이프라인 갭 분석 (document_ingestion.py) — Analysis -> contains -> 배포 판정: ✅ **APPROVED** (≥90%) [EXTRACTED]
- GET / (list) ✅ -> has_code_example -> python [EXTRACTED]
- POST /upload ✅ -> has_code_example -> python [EXTRACTED]
- STEP 4: Embedding 배치 처리 ✅ -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 문서 수집 파이프라인 갭 분석 (document_ingestion.py) — Analysis, python, API 엔드포인트 상세 비교를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 document_ingestion.py.analysis.md이다.

### Key Facts
- **Feature**: document_ingestion.py **Phase**: CHECK **Created**: 2026-04-02 **Analysis Date**: 2026-04-02 **Match Rate**: 92% ✅
- **필요한 테스트**: ```python 단위 테스트 test_chunk_by_headings()      # ← 필요 test_chunk_by_window()        # ← 필요 test_compute_file_hash()      # ← 필요 test_generate_embedding()     # ← 필요 (모의)
- POST /upload ✅ ```python 설계 - 파일 검증 (확장자, 크기) - Supabase Storage 저장 - intranet_documents 레코드 생성 - 비동기 process_document() 스케줄
- **설계 계획**: - 단위 테스트 4개 - 통합 테스트 3개 - E2E 테스트 1개
- | 테이블 | 설계 | 상태 | 확인 | |--------|------|------|------| | **intranet_documents** | ✅ 설계 | ✅ 존재 | 마이그레이션 완료 | | **document_chunks** | ✅ 신규 설계 | ❌ 미생성 | **마이그레이션 필수** |
