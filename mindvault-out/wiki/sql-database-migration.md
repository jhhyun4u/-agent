# sql & Database Migration
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **sql** (C:\project\tenopa proposer\-agent-master\docs\02-design\proposal-workflow-states.md) -- 1 connections
  - <- has_code_example <- [[database-migration]]
- **Database Migration** (C:\project\tenopa proposer\-agent-master\docs\02-design\proposal-workflow-states.md) -- 1 connections
  - -> has_code_example -> [[sql]]

## Internal Relationships
- Database Migration -> has_code_example -> sql [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 sql, Database Migration를 중심으로 has_code_example 관계로 연결되어 있다. 주요 소스 파일은 proposal-workflow-states.md이다.

### Key Facts
- Database Migration ```sql -- proposals 테이블 status enum 확장 ALTER TYPE proposal_status ADD VALUE 'submitted', 'presentation', 'closed', 'archived';
- -- archived_at 컬럼 추가 ALTER TABLE proposals ADD COLUMN archived_at TIMESTAMP NULL;
