# project_scheduler_integration_act1 & Changes Made
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **project_scheduler_integration_act1** (C:\project\tenopa proposer\-agent-master\.claude\agent-memory\bkit-pdca-iterator\project_scheduler_integration_act1.md) -- 1 connections
  - -> contains -> [[changes-made]]
- **Changes Made** (C:\project\tenopa proposer\-agent-master\.claude\agent-memory\bkit-pdca-iterator\project_scheduler_integration_act1.md) -- 1 connections
  - <- contains <- [[projectschedulerintegrationact1]]

## Internal Relationships
- project_scheduler_integration_act1 -> contains -> Changes Made [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 project_scheduler_integration_act1, Changes Made를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 project_scheduler_integration_act1.md이다.

### Key Facts
- - `app/services/scheduled_monitor.py` — Added `run_scheduled_migration()` async function; registered `monthly_migration` job (KST, 매월 1일 00:00) - `app/main.py` — Removed duplicate `init_scheduler()` / `shutdown_scheduler()` calls from lifespan - `app/services/migration_service.py` — Replaced all 10…
