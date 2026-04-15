# sql & DB 스키마 변경
Cohesion: 0.67 | Nodes: 4

## Key Nodes
- **sql** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_STORAGE_REDESIGN.md) -- 2 connections
  - <- has_code_example <- [[intranetdocuments]]
  - <- has_code_example <- [[intranetprojects]]
- **DB 스키마 변경** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_STORAGE_REDESIGN.md) -- 2 connections
  - -> contains -> [[intranetdocuments]]
  - -> contains -> [[intranetprojects]]
- **intranet_documents 테이블 (변경)** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_STORAGE_REDESIGN.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[db]]
- **intranet_projects 테이블 (변경 없음)** (C:\project\tenopa proposer\-agent-master\docs\INTRANET_STORAGE_REDESIGN.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[db]]

## Internal Relationships
- DB 스키마 변경 -> contains -> intranet_documents 테이블 (변경) [EXTRACTED]
- DB 스키마 변경 -> contains -> intranet_projects 테이블 (변경 없음) [EXTRACTED]
- intranet_documents 테이블 (변경) -> has_code_example -> sql [EXTRACTED]
- intranet_projects 테이블 (변경 없음) -> has_code_example -> sql [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 sql, DB 스키마 변경, intranet_documents 테이블 (변경)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 INTRANET_STORAGE_REDESIGN.md이다.

### Key Facts
- ```sql CREATE TABLE intranet_documents ( id                UUID PRIMARY KEY, project_id        UUID NOT NULL,         -- ← 강화: 항상 필수 org_id            UUID NOT NULL,         -- ← 유지: RLS 용도 -- 파일 메타 file_slot         TEXT NOT NULL, doc_type          TEXT NOT NULL,         -- proposal, report,…
- intranet_documents 테이블 (변경)
- ```sql CREATE TABLE intranet_documents ( id                UUID PRIMARY KEY, project_id        UUID NOT NULL,         -- ← 강화: 항상 필수 org_id            UUID NOT NULL,         -- ← 유지: RLS 용도 -- 파일 메타 file_slot         TEXT NOT NULL, doc_type          TEXT NOT NULL,         -- proposal, report,…
- 스키마는 이미 프로젝트 ID 중심이므로 그대로 유지: ```sql CREATE TABLE intranet_projects ( id              UUID PRIMARY KEY,        -- ← 중심축 org_id          UUID NOT NULL,           -- ← RLS용 (참조용) project_name    TEXT NOT NULL, client_name     TEXT, budget_krw      BIGINT, keywords        TEXT[], status          TEXT,…
