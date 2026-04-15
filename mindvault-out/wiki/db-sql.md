# 📊 DB 테이블 구조 (통합 설계) & sql
Cohesion: 0.14 | Nodes: 20

## Key Nodes
- **📊 DB 테이블 구조 (통합 설계)** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 9 connections
  - -> contains -> [[1-masterprojects]]
  - -> contains -> [[2-intranetdocuments]]
  - -> contains -> [[3-projectarchive]]
  - -> contains -> [[4-proposals]]
  - -> contains -> [[1-historical]]
  - -> contains -> [[2-rfp]]
  - -> contains -> [[3]]
  - -> contains -> [[masterprojectsmetadata-json]]
  - <- contains <- [[archive]]
- **sql** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 8 connections
  - <- has_code_example <- [[a]]
  - <- has_code_example <- [[1-masterprojects]]
  - <- has_code_example <- [[2-intranetdocuments]]
  - <- has_code_example <- [[3-projectarchive]]
  - <- has_code_example <- [[4-proposals]]
  - <- has_code_example <- [[phase-1-masterprojects]]
  - <- has_code_example <- [[phase-2]]
  - <- has_code_example <- [[phase-3]]
- **API 엔드포인트** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 6 connections
  - -> has_code_example -> [[typescript]]
  - -> contains -> [[phase-1-masterprojects]]
  - -> contains -> [[phase-2]]
  - -> contains -> [[phase-3]]
  - -> contains -> [[phase-4-api]]
  - <- contains <- [[archive]]
- **인트라넷 자료 + Archive 통합 설계** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 5 connections
  - -> contains -> [[3]]
  - -> contains -> [[a]]
  - -> contains -> [[storage]]
  - -> contains -> [[db]]
  - -> contains -> [[api]]
- **1. master_projects (신규)** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[db]]
- **2. intranet_documents (수정)** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[db]]
- **독립적 상태 변수 (3개)** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 2 connections
  - <- contains <- [[archive]]
  - <- contains <- [[db]]
- **3. project_archive (유지 - 링크 추가)** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[db]]
- **4. proposals (유지 - 링크 추가)** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[db]]
- **옵션 A: 완전 통합 (권장)** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[archive]]
- **master_projects.metadata (JSON)** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 2 connections
  - -> has_code_example -> [[json]]
  - <- contains <- [[db]]
- **Phase 1: master_projects 테이블 생성 (즉시)** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[api]]
- **Phase 2: 기존 데이터 이관** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[api]]
- **Phase 3: 외래키 업데이트** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[api]]
- **json** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 1 connections
  - <- has_code_example <- [[masterprojectsmetadata-json]]
- **typescript** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 1 connections
  - <- has_code_example <- [[api]]
- **흐름 1: Historical 프로젝트 + 자료** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 1 connections
  - <- contains <- [[db]]
- **흐름 2: 새 제안서 작성 (RFP → 완료)** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 1 connections
  - <- contains <- [[db]]
- **Phase 4: API 업데이트** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 1 connections
  - <- contains <- [[api]]
- **Storage 경로 통합** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_ARCHIVE_INTEGRATION_DESIGN.md) -- 1 connections
  - <- contains <- [[archive]]

## Internal Relationships
- 1. master_projects (신규) -> has_code_example -> sql [EXTRACTED]
- 2. intranet_documents (수정) -> has_code_example -> sql [EXTRACTED]
- 3. project_archive (유지 - 링크 추가) -> has_code_example -> sql [EXTRACTED]
- 4. proposals (유지 - 링크 추가) -> has_code_example -> sql [EXTRACTED]
- 옵션 A: 완전 통합 (권장) -> has_code_example -> sql [EXTRACTED]
- API 엔드포인트 -> has_code_example -> typescript [EXTRACTED]
- API 엔드포인트 -> contains -> Phase 1: master_projects 테이블 생성 (즉시) [EXTRACTED]
- API 엔드포인트 -> contains -> Phase 2: 기존 데이터 이관 [EXTRACTED]
- API 엔드포인트 -> contains -> Phase 3: 외래키 업데이트 [EXTRACTED]
- API 엔드포인트 -> contains -> Phase 4: API 업데이트 [EXTRACTED]
- 인트라넷 자료 + Archive 통합 설계 -> contains -> 독립적 상태 변수 (3개) [EXTRACTED]
- 인트라넷 자료 + Archive 통합 설계 -> contains -> 옵션 A: 완전 통합 (권장) [EXTRACTED]
- 인트라넷 자료 + Archive 통합 설계 -> contains -> Storage 경로 통합 [EXTRACTED]
- 인트라넷 자료 + Archive 통합 설계 -> contains -> 📊 DB 테이블 구조 (통합 설계) [EXTRACTED]
- 인트라넷 자료 + Archive 통합 설계 -> contains -> API 엔드포인트 [EXTRACTED]
- 📊 DB 테이블 구조 (통합 설계) -> contains -> 1. master_projects (신규) [EXTRACTED]
- 📊 DB 테이블 구조 (통합 설계) -> contains -> 2. intranet_documents (수정) [EXTRACTED]
- 📊 DB 테이블 구조 (통합 설계) -> contains -> 3. project_archive (유지 - 링크 추가) [EXTRACTED]
- 📊 DB 테이블 구조 (통합 설계) -> contains -> 4. proposals (유지 - 링크 추가) [EXTRACTED]
- 📊 DB 테이블 구조 (통합 설계) -> contains -> 흐름 1: Historical 프로젝트 + 자료 [EXTRACTED]
- 📊 DB 테이블 구조 (통합 설계) -> contains -> 흐름 2: 새 제안서 작성 (RFP → 완료) [EXTRACTED]
- 📊 DB 테이블 구조 (통합 설계) -> contains -> 독립적 상태 변수 (3개) [EXTRACTED]
- 📊 DB 테이블 구조 (통합 설계) -> contains -> master_projects.metadata (JSON) [EXTRACTED]
- master_projects.metadata (JSON) -> has_code_example -> json [EXTRACTED]
- Phase 1: master_projects 테이블 생성 (즉시) -> has_code_example -> sql [EXTRACTED]
- Phase 2: 기존 데이터 이관 -> has_code_example -> sql [EXTRACTED]
- Phase 3: 외래키 업데이트 -> has_code_example -> sql [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 📊 DB 테이블 구조 (통합 설계), sql, API 엔드포인트를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 INTRANET_ARCHIVE_INTEGRATION_DESIGN.md이다.

### Key Facts
- 1. master_projects (신규) 모든 프로젝트의 단일 진실 공급원 (SSOT)
- ```sql CREATE TABLE master_projects ( id                      UUID PRIMARY KEY, org_id                  UUID NOT NULL, -- 기본 정보 project_name            TEXT NOT NULL, project_year            INTEGER, client_name             TEXT, -- 요약/내용 summary                 TEXT,              -- 주요 내용 요약…
- 프로젝트 검색 (통합) ```typescript GET /api/master-projects?keyword=AI&year=2025&type=historical,completed_proposal
- > **상태:** 통합 설계 제안 > **작성일:** 2026-04-11 > **핵심:** 과거 프로젝트 자료(intranet_projects)와 제안서 완료 자료(archive) 통합 관리
- ```sql id                      -- master_project_id (불변) org_id project_name project_year start_date              -- 프로젝트 시작일 end_date                -- 프로젝트 종료일 client_name summary                 -- 주요 내용 요약 budget_krw project_type           -- historical | active_proposal | completed_proposal…
