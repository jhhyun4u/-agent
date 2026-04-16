# run_scheduled_migration & run_scheduled_migration
Cohesion: 0.40 | Nodes: 6

## Key Nodes
- **run_scheduled_migration** (C:\project\tenopa proposer\app\jobs\migration_jobs.py) -- 6 connections
  - -> calls -> [[unresolvedrefinfo]]
  - -> calls -> [[unresolvedrefgetasyncclient]]
  - -> calls -> [[unresolvedrefmigrationservice]]
  - -> calls -> [[unresolvedrefbatchimportintranetdocuments]]
  - -> calls -> [[unresolvedreferror]]
  - <- contains <- [[migrationjobs]]
- **run_scheduled_migration** (C:\project\tenopa proposer\app\services\scheduled_monitor.py) -- 6 connections
  - -> calls -> [[unresolvedrefinfo]]
  - -> calls -> [[unresolvedrefgetasyncclient]]
  - -> calls -> [[unresolvedrefmigrationservice]]
  - -> calls -> [[unresolvedrefbatchimportintranetdocuments]]
  - -> calls -> [[unresolvedreferror]]
  - <- contains <- [[scheduledmonitor]]
- **__unresolved__::ref::batch_import_intranet_documents** () -- 4 connections
  - <- calls <- [[runscheduledmigration]]
  - <- calls <- [[retryfailedbatch]]
  - <- calls <- [[runscheduledmigration]]
  - <- calls <- [[main]]
- **__unresolved__::ref::migrationservice** () -- 4 connections
  - <- calls <- [[getmigrationservice]]
  - <- calls <- [[runscheduledmigration]]
  - <- calls <- [[runscheduledmigration]]
  - <- calls <- [[main]]
- **retry_failed_batch** (C:\project\tenopa proposer\app\services\migration_service.py) -- 3 connections
  - -> calls -> [[unresolvedrefinfo]]
  - -> calls -> [[unresolvedrefbatchimportintranetdocuments]]
  - <- contains <- [[migrationservice]]
- **_get_migration_service** (C:\project\tenopa proposer\app\api\routes_migrations.py) -- 2 connections
  - -> calls -> [[unresolvedrefmigrationservice]]
  - <- contains <- [[routesmigrations]]

## Internal Relationships
- _get_migration_service -> calls -> __unresolved__::ref::migrationservice [EXTRACTED]
- run_scheduled_migration -> calls -> __unresolved__::ref::migrationservice [EXTRACTED]
- run_scheduled_migration -> calls -> __unresolved__::ref::batch_import_intranet_documents [EXTRACTED]
- retry_failed_batch -> calls -> __unresolved__::ref::batch_import_intranet_documents [EXTRACTED]
- run_scheduled_migration -> calls -> __unresolved__::ref::migrationservice [EXTRACTED]
- run_scheduled_migration -> calls -> __unresolved__::ref::batch_import_intranet_documents [EXTRACTED]

## Cross-Community Connections
- run_scheduled_migration -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- run_scheduled_migration -> calls -> __unresolved__::ref::get_async_client (-> [[unresolvedrefget-unresolvedrefexecute]])
- run_scheduled_migration -> calls -> __unresolved__::ref::error (-> [[unresolvedrefget-unresolvedrefexecute]])
- retry_failed_batch -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- run_scheduled_migration -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- run_scheduled_migration -> calls -> __unresolved__::ref::get_async_client (-> [[unresolvedrefget-unresolvedrefexecute]])
- run_scheduled_migration -> calls -> __unresolved__::ref::error (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 run_scheduled_migration, run_scheduled_migration, __unresolved__::ref::batch_import_intranet_documents를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 migration_jobs.py, migration_service.py, routes_migrations.py, scheduled_monitor.py이다.

### Key Facts
- run_scheduled_migration() 함수는 app/services/scheduled_monitor.py로 이전. 이 파일은 기존 테스트 호환성을 위해 보존되며, 실제 스케줄러 잡은 scheduled_monitor.setup_scheduler() 안의 'monthly_migration' 잡을 사용. """
- async def run_scheduled_migration() -> None: """인트라넷 문서 정기 배치 마이그레이션 (매월 1일 00:00 KST).
- async def retry_failed_batch(self, batch_id: UUID) -> MigrationBatch: """ 이전 실패 배치 재실행
- def _get_migration_service(db) -> MigrationService: """마이그레이션 서비스 팩토리 (notification_service는 M-5로 추후 주입).""" return MigrationService(db=db, notification_service=None)
