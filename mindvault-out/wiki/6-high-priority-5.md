# 📋 갭 목록 (6개) & HIGH Priority (5개) - 즉시 수정 필요
Cohesion: 0.09 | Nodes: 24

## Key Nodes
- **📋 갭 목록 (6개)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 14 connections
  - -> contains -> [[high-priority-5]]
  - -> contains -> [[low-priority-1]]
  - -> contains -> [[fr-01-migrationhistory-71]]
  - -> contains -> [[fr-02-applymigrationspy-92]]
  - -> contains -> [[fr-03-api-0]]
  - -> contains -> [[fr-04-mainpy-lifespan-100]]
  - -> contains -> [[fr-05-v2]]
  - -> contains -> [[p0-high]]
  - -> contains -> [[p1-low]]
  - -> contains -> [[90]]
  - -> contains -> [[95]]
  - -> contains -> [[option-1]]
  - -> contains -> [[option-2]]
  - <- contains <- [[db-gap-analysis-report]]
- **HIGH Priority (5개) - 즉시 수정 필요** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 6 connections
  - -> contains -> [[gap-h1-getmigrationstatus-sql]]
  - -> contains -> [[gap-h2]]
  - -> contains -> [[gap-h3-get-apimigrationsstatus]]
  - -> contains -> [[gap-h4-get-apimigrationshistory]]
  - -> contains -> [[gap-h5-get-apimigrationssummary]]
  - <- contains <- [[6]]
- **sql** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 3 connections
  - <- has_code_example <- [[gap-h1-getmigrationstatus-sql]]
  - <- has_code_example <- [[gap-l1-idxmigrationhistorystatus]]
  - <- has_code_example <- [[p0-high]]
- **GAP-H1: get_migration_status() SQL 함수 버그** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[high-priority-5]]
- **GAP-H2: 재시도 로직 누락** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[high-priority-5]]
- **GAP-L1: idx_migration_history_status 인덱스 누락** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[low-priority-1]]
- **LOW Priority (1개) - 향후 최적화** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 2 connections
  - -> contains -> [[gap-l1-idxmigrationhistorystatus]]
  - <- contains <- [[6]]
- **Option 1: 자동 개선 (추천)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[6]]
- **P0 - 즉시 수정 (HIGH)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[6]]
- **bash** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 1 connections
  - <- has_code_example <- [[option-1]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 1 connections
  - <- has_code_example <- [[gap-h2]]
- **아키텍처 준수 (90%)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 1 connections
  - <- contains <- [[6]]
- **코드 품질 (95%)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 1 connections
  - <- contains <- [[6]]
- **DB 마이그레이션 자동화 - Gap Analysis Report** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 1 connections
  - -> contains -> [[6]]
- **FR-01: migration_history 테이블 (71%)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 1 connections
  - <- contains <- [[6]]
- **FR-02: apply_migrations.py (92%)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 1 connections
  - <- contains <- [[6]]
- **FR-03: API 엔드포인트 (0%)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 1 connections
  - <- contains <- [[6]]
- **FR-04: main.py lifespan (100%)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 1 connections
  - <- contains <- [[6]]
- **FR-05: 롤백 기능 (v2)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 1 connections
  - <- contains <- [[6]]
- **GAP-H3: GET /api/migrations/status 미구현** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 1 connections
  - <- contains <- [[high-priority-5]]
- **GAP-H4: GET /api/migrations/history 미구현** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 1 connections
  - <- contains <- [[high-priority-5]]
- **GAP-H5: GET /api/migrations/summary 미구현** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 1 connections
  - <- contains <- [[high-priority-5]]
- **Option 2: 수동 수정** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 1 connections
  - <- contains <- [[6]]
- **P1 - 단기 수정 (LOW)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\db-migration-automation\db-migration-automation.analysis.md) -- 1 connections
  - <- contains <- [[6]]

## Internal Relationships
- 📋 갭 목록 (6개) -> contains -> HIGH Priority (5개) - 즉시 수정 필요 [EXTRACTED]
- 📋 갭 목록 (6개) -> contains -> LOW Priority (1개) - 향후 최적화 [EXTRACTED]
- 📋 갭 목록 (6개) -> contains -> FR-01: migration_history 테이블 (71%) [EXTRACTED]
- 📋 갭 목록 (6개) -> contains -> FR-02: apply_migrations.py (92%) [EXTRACTED]
- 📋 갭 목록 (6개) -> contains -> FR-03: API 엔드포인트 (0%) [EXTRACTED]
- 📋 갭 목록 (6개) -> contains -> FR-04: main.py lifespan (100%) [EXTRACTED]
- 📋 갭 목록 (6개) -> contains -> FR-05: 롤백 기능 (v2) [EXTRACTED]
- 📋 갭 목록 (6개) -> contains -> P0 - 즉시 수정 (HIGH) [EXTRACTED]
- 📋 갭 목록 (6개) -> contains -> P1 - 단기 수정 (LOW) [EXTRACTED]
- 📋 갭 목록 (6개) -> contains -> 아키텍처 준수 (90%) [EXTRACTED]
- 📋 갭 목록 (6개) -> contains -> 코드 품질 (95%) [EXTRACTED]
- 📋 갭 목록 (6개) -> contains -> Option 1: 자동 개선 (추천) [EXTRACTED]
- 📋 갭 목록 (6개) -> contains -> Option 2: 수동 수정 [EXTRACTED]
- DB 마이그레이션 자동화 - Gap Analysis Report -> contains -> 📋 갭 목록 (6개) [EXTRACTED]
- GAP-H1: get_migration_status() SQL 함수 버그 -> has_code_example -> sql [EXTRACTED]
- GAP-H2: 재시도 로직 누락 -> has_code_example -> python [EXTRACTED]
- GAP-L1: idx_migration_history_status 인덱스 누락 -> has_code_example -> sql [EXTRACTED]
- HIGH Priority (5개) - 즉시 수정 필요 -> contains -> GAP-H1: get_migration_status() SQL 함수 버그 [EXTRACTED]
- HIGH Priority (5개) - 즉시 수정 필요 -> contains -> GAP-H2: 재시도 로직 누락 [EXTRACTED]
- HIGH Priority (5개) - 즉시 수정 필요 -> contains -> GAP-H3: GET /api/migrations/status 미구현 [EXTRACTED]
- HIGH Priority (5개) - 즉시 수정 필요 -> contains -> GAP-H4: GET /api/migrations/history 미구현 [EXTRACTED]
- HIGH Priority (5개) - 즉시 수정 필요 -> contains -> GAP-H5: GET /api/migrations/summary 미구현 [EXTRACTED]
- LOW Priority (1개) - 향후 최적화 -> contains -> GAP-L1: idx_migration_history_status 인덱스 누락 [EXTRACTED]
- Option 1: 자동 개선 (추천) -> has_code_example -> bash [EXTRACTED]
- P0 - 즉시 수정 (HIGH) -> has_code_example -> sql [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 📋 갭 목록 (6개), HIGH Priority (5개) - 즉시 수정 필요, sql를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 db-migration-automation.analysis.md이다.

### Key Facts
- HIGH Priority (5개) - 즉시 수정 필요
- GAP-H1: get_migration_status() SQL 함수 버그 - **위치**: Design §2.1 (line 193-200) / SQL §27-28 - **문제**: 함수가 존재하지 않는 `information_schema.files` 테이블 참조 - **영향**: 함수 호출 시 런타임 오류 발생 (HIGH) - **수정**: ```sql -- 현재 (오류): SELECT COUNT(*) FROM information_schema.files WHERE type = 'migration'
- -- 수정: SELECT COUNT(DISTINCT version) FROM migration_history WHERE status = 'success' ```
- -- 수정: SELECT COUNT(DISTINCT version) FROM migration_history WHERE status = 'success' ```
- GAP-H3: GET /api/migrations/status 미구현 - **위치**: Design §4.4.1 (line 341-376) - **문제**: 마이그레이션 상태 조회 API 엔드포인트 없음 - **영향**: 웹 대시보드에서 상태 확인 불가 (HIGH) - **필드**: status, total, successful, failed, migrations[]
