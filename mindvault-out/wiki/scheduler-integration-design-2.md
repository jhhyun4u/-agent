# scheduler-integration Design & 2. 아키텍처 결정
Cohesion: 0.11 | Nodes: 19

## Key Nodes
- **scheduler-integration Design** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 9 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3-db]]
  - -> contains -> [[4-api]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
  - -> contains -> [[9]]
- **2. 아키텍처 결정** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 4 connections
  - -> contains -> [[21]]
  - -> contains -> [[22-asiaseoul-kst]]
  - -> contains -> [[23-apscheduler]]
  - <- contains <- [[scheduler-integration-design]]
- **3. DB 스키마** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 3 connections
  - -> contains -> [[migrationbatches]]
  - -> contains -> [[migrationschedule]]
  - <- contains <- [[scheduler-integration-design]]
- **5. 서비스 레이어 설계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 3 connections
  - -> contains -> [[migrationservice-appservicesmigrationservicepy]]
  - -> contains -> [[runscheduledmigration-scheduledmonitorpy]]
  - <- contains <- [[scheduler-integration-design]]
- **sql** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 2 connections
  - <- has_code_example <- [[migrationbatches]]
  - <- has_code_example <- [[migrationschedule]]
- **migration_batches** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[3-db]]
- **migration_schedule** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[3-db]]
- **MigrationService (app/services/migration_service.py)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[5]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 1 connections
  - <- has_code_example <- [[migrationservice-appservicesmigrationservicepy]]
- **1. 개요** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 1 connections
  - <- contains <- [[scheduler-integration-design]]
- **2.1 단일 스케줄러 패턴 (통합 결정)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 1 connections
  - <- contains <- [[2]]
- **2.2 타임존: Asia/Seoul (KST)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 1 connections
  - <- contains <- [[2]]
- **2.3 APScheduler 선택 이유** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 1 connections
  - <- contains <- [[2]]
- **4. API 스펙** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 1 connections
  - <- contains <- [[scheduler-integration-design]]
- **6. 문서 처리 흐름** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 1 connections
  - <- contains <- [[scheduler-integration-design]]
- **7. 에러 처리 전략** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 1 connections
  - <- contains <- [[scheduler-integration-design]]
- **8. 관련 파일** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 1 connections
  - <- contains <- [[scheduler-integration-design]]
- **9. 갭 분석 연계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 1 connections
  - <- contains <- [[scheduler-integration-design]]
- **run_scheduled_migration (scheduled_monitor.py)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.design.md) -- 1 connections
  - <- contains <- [[5]]

## Internal Relationships
- 2. 아키텍처 결정 -> contains -> 2.1 단일 스케줄러 패턴 (통합 결정) [EXTRACTED]
- 2. 아키텍처 결정 -> contains -> 2.2 타임존: Asia/Seoul (KST) [EXTRACTED]
- 2. 아키텍처 결정 -> contains -> 2.3 APScheduler 선택 이유 [EXTRACTED]
- 3. DB 스키마 -> contains -> migration_batches [EXTRACTED]
- 3. DB 스키마 -> contains -> migration_schedule [EXTRACTED]
- 5. 서비스 레이어 설계 -> contains -> MigrationService (app/services/migration_service.py) [EXTRACTED]
- 5. 서비스 레이어 설계 -> contains -> run_scheduled_migration (scheduled_monitor.py) [EXTRACTED]
- migration_batches -> has_code_example -> sql [EXTRACTED]
- migration_schedule -> has_code_example -> sql [EXTRACTED]
- MigrationService (app/services/migration_service.py) -> has_code_example -> python [EXTRACTED]
- scheduler-integration Design -> contains -> 1. 개요 [EXTRACTED]
- scheduler-integration Design -> contains -> 2. 아키텍처 결정 [EXTRACTED]
- scheduler-integration Design -> contains -> 3. DB 스키마 [EXTRACTED]
- scheduler-integration Design -> contains -> 4. API 스펙 [EXTRACTED]
- scheduler-integration Design -> contains -> 5. 서비스 레이어 설계 [EXTRACTED]
- scheduler-integration Design -> contains -> 6. 문서 처리 흐름 [EXTRACTED]
- scheduler-integration Design -> contains -> 7. 에러 처리 전략 [EXTRACTED]
- scheduler-integration Design -> contains -> 8. 관련 파일 [EXTRACTED]
- scheduler-integration Design -> contains -> 9. 갭 분석 연계 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 scheduler-integration Design, 2. 아키텍처 결정, 3. DB 스키마를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 scheduler-integration.design.md이다.

### Key Facts
- **Version:** 1.0 **Date:** 2026-03-30 **Status:** Retroactive Design (Act Phase — post-implementation) **Feature:** 인트라넷 문서 월간 배치 마이그레이션 스케줄러 통합 **PDCA Phase:** Design (retroactive, inferred from implementation + gap analysis)
- 2.1 단일 스케줄러 패턴 (통합 결정)
- MigrationService (app/services/migration_service.py)
- ```sql CREATE TABLE migration_batches ( id UUID PRIMARY KEY DEFAULT gen_random_uuid(), batch_name VARCHAR(200) NOT NULL, status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending|processing|completed|failed|partial_failed started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ, scheduled_at TIMESTAMPTZ…
- ```sql CREATE TABLE migration_batches ( id UUID PRIMARY KEY DEFAULT gen_random_uuid(), batch_name VARCHAR(200) NOT NULL, status VARCHAR(50) NOT NULL DEFAULT 'pending',  -- pending|processing|completed|failed|partial_failed started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ, scheduled_at TIMESTAMPTZ…
