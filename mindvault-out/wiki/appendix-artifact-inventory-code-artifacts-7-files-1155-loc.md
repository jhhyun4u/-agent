# Appendix: Artifact Inventory & Code Artifacts (7 files, 1,155 LOC)
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **Appendix: Artifact Inventory** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.report.md) -- 4 connections
  - -> contains -> [[code-artifacts-7-files-1155-loc]]
  - -> contains -> [[test-artifacts-3-files-43-tests]]
  - -> contains -> [[documentation-artifacts-4-files]]
  - -> contains -> [[database-artifacts-1-sql-migration]]
- **Code Artifacts (7 files, 1,155 LOC)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.report.md) -- 1 connections
  - <- contains <- [[appendix-artifact-inventory]]
- **Database Artifacts (1 SQL migration)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.report.md) -- 1 connections
  - <- contains <- [[appendix-artifact-inventory]]
- **Documentation Artifacts (4 files)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.report.md) -- 1 connections
  - <- contains <- [[appendix-artifact-inventory]]
- **Test Artifacts (3 files, 43 tests)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\scheduler-integration\scheduler-integration.report.md) -- 1 connections
  - <- contains <- [[appendix-artifact-inventory]]

## Internal Relationships
- Appendix: Artifact Inventory -> contains -> Code Artifacts (7 files, 1,155 LOC) [EXTRACTED]
- Appendix: Artifact Inventory -> contains -> Test Artifacts (3 files, 43 tests) [EXTRACTED]
- Appendix: Artifact Inventory -> contains -> Documentation Artifacts (4 files) [EXTRACTED]
- Appendix: Artifact Inventory -> contains -> Database Artifacts (1 SQL migration) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Appendix: Artifact Inventory, Code Artifacts (7 files, 1,155 LOC), Database Artifacts (1 SQL migration)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 scheduler-integration.report.md이다.

### Key Facts
- Code Artifacts (7 files, 1,155 LOC)
- ``` app/services/migration_service.py         506 lines  Service layer + CRUD app/models/migration_schemas.py          149 lines  10 Pydantic models app/api/routes_migrations.py             187 lines  5 REST endpoints app/services/scheduled_monitor.py        Modified  Scheduler integration…
- ``` database/migrations/016_scheduler_integration.sql - 2 tables (migration_batches, migration_schedule) - 9 indexes - 5 RLS policies ```
- ``` docs/01-plan/features/scheduler-integration.plan.md docs/02-design/features/scheduler-integration.design.md docs/03-analysis/features/scheduler-integration.analysis.md docs/04-report/features/scheduler-integration.report.md (THIS FILE) ```
- ``` tests/test_migration_service.py          22 tests  Service & schemas tests/test_scheduler_integration.py      10 tests  Scheduler lifecycle tests/test_migration_api.py              11 tests  API endpoints ```
