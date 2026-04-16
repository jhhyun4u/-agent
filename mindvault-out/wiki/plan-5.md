# 정기적 문서 마이그레이션 스케줄러 통합 계획 (Plan) & 5. 구현 순서
Cohesion: 0.08 | Nodes: 24

## Key Nodes
- **정기적 문서 마이그레이션 스케줄러 통합 계획 (Plan)** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 9 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
  - -> contains -> [[9]]
- **5. 구현 순서** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 7 connections
  - -> contains -> [[phase-0-1]]
  - -> contains -> [[phase-1-1]]
  - -> contains -> [[phase-2-migrationservice-2-3]]
  - -> contains -> [[phase-3-apscheduler-1day]]
  - -> contains -> [[phase-4-api-1day]]
  - -> contains -> [[phase-5-1-2day]]
  - <- contains <- [[plan]]
- **2. 요구사항** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 3 connections
  - -> contains -> [[21]]
  - -> contains -> [[22]]
  - <- contains <- [[plan]]
- **3. 현황 분석** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 3 connections
  - -> contains -> [[31]]
  - -> contains -> [[32]]
  - <- contains <- [[plan]]
- **4. 제안된 솔루션** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 3 connections
  - -> contains -> [[41]]
  - -> contains -> [[42]]
  - <- contains <- [[plan]]
- **4.2 핵심 컴포넌트** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 3 connections
  - -> has_code_example -> [[python]]
  - -> has_code_example -> [[sql]]
  - <- contains <- [[4]]
- **python** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- has_code_example <- [[42]]
- **sql** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- has_code_example <- [[42]]
- **1. 개요** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **2.1 기본 요구사항** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **2.2 데이터 범위** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **3.1 기존 구현** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **3.2 의존성** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- contains <- [[3]]
- **4.1 아키텍처** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- contains <- [[4]]
- **6. 예상 일정** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **7. 리스크 및 완화 방안** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **8. 성공 기준** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **9. 다음 단계** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **Phase 0: 설계 검토 (1일)** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **Phase 1: 데이터베이스 마이그레이션 (1일)** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **Phase 2: MigrationService 구현 (2-3일)** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **Phase 3: APScheduler 통합 (1day)** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **Phase 4: API 엔드포인트 (1day)** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **Phase 5: 모니터링 + 테스트 (1-2day)** (C:\project\tenopa proposer\docs\01-plan\features\scheduler-integration.plan.md) -- 1 connections
  - <- contains <- [[5]]

## Internal Relationships
- 2. 요구사항 -> contains -> 2.1 기본 요구사항 [EXTRACTED]
- 2. 요구사항 -> contains -> 2.2 데이터 범위 [EXTRACTED]
- 3. 현황 분석 -> contains -> 3.1 기존 구현 [EXTRACTED]
- 3. 현황 분석 -> contains -> 3.2 의존성 [EXTRACTED]
- 4. 제안된 솔루션 -> contains -> 4.1 아키텍처 [EXTRACTED]
- 4. 제안된 솔루션 -> contains -> 4.2 핵심 컴포넌트 [EXTRACTED]
- 4.2 핵심 컴포넌트 -> has_code_example -> python [EXTRACTED]
- 4.2 핵심 컴포넌트 -> has_code_example -> sql [EXTRACTED]
- 5. 구현 순서 -> contains -> Phase 0: 설계 검토 (1일) [EXTRACTED]
- 5. 구현 순서 -> contains -> Phase 1: 데이터베이스 마이그레이션 (1일) [EXTRACTED]
- 5. 구현 순서 -> contains -> Phase 2: MigrationService 구현 (2-3일) [EXTRACTED]
- 5. 구현 순서 -> contains -> Phase 3: APScheduler 통합 (1day) [EXTRACTED]
- 5. 구현 순서 -> contains -> Phase 4: API 엔드포인트 (1day) [EXTRACTED]
- 5. 구현 순서 -> contains -> Phase 5: 모니터링 + 테스트 (1-2day) [EXTRACTED]
- 정기적 문서 마이그레이션 스케줄러 통합 계획 (Plan) -> contains -> 1. 개요 [EXTRACTED]
- 정기적 문서 마이그레이션 스케줄러 통합 계획 (Plan) -> contains -> 2. 요구사항 [EXTRACTED]
- 정기적 문서 마이그레이션 스케줄러 통합 계획 (Plan) -> contains -> 3. 현황 분석 [EXTRACTED]
- 정기적 문서 마이그레이션 스케줄러 통합 계획 (Plan) -> contains -> 4. 제안된 솔루션 [EXTRACTED]
- 정기적 문서 마이그레이션 스케줄러 통합 계획 (Plan) -> contains -> 5. 구현 순서 [EXTRACTED]
- 정기적 문서 마이그레이션 스케줄러 통합 계획 (Plan) -> contains -> 6. 예상 일정 [EXTRACTED]
- 정기적 문서 마이그레이션 스케줄러 통합 계획 (Plan) -> contains -> 7. 리스크 및 완화 방안 [EXTRACTED]
- 정기적 문서 마이그레이션 스케줄러 통합 계획 (Plan) -> contains -> 8. 성공 기준 [EXTRACTED]
- 정기적 문서 마이그레이션 스케줄러 통합 계획 (Plan) -> contains -> 9. 다음 단계 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 정기적 문서 마이그레이션 스케줄러 통합 계획 (Plan), 5. 구현 순서, 2. 요구사항를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 scheduler-integration.plan.md이다.

### Key Facts
- **버전**: v1.0 **작성일**: 2026-03-30 **상태**: DRAFT
- Phase 0: 설계 검토 (1일) - [ ] 스케줄 전략 확정 (cron vs APScheduler vs Lambda) - [ ] 변경 감지 방식 선정 - [ ] 에러 재시도 전략 수립
- **1. MigrationService (신규)** ```python class MigrationService: async def batch_import_intranet_documents(): # 1. 인트라넷에서 신규/수정 문서 감지 # 2. 배치 로그 생성 # 3. document_ingestion.process_document() 호출 # 4. 배치 완료 로그 저장 # 5. 실패 시 알림 발송 ```
- **1. MigrationService (신규)** ```python class MigrationService: async def batch_import_intranet_documents(): # 1. 인트라넷에서 신규/수정 문서 감지 # 2. 배치 로그 생성 # 3. document_ingestion.process_document() 호출 # 4. 배치 완료 로그 저장 # 5. 실패 시 알림 발송 ```
- **4. 데이터베이스 테이블 (신규)** ```sql -- migration_batches: 배치 작업 기록 CREATE TABLE migration_batches ( id UUID PRIMARY KEY, started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ, status VARCHAR (processing|completed|failed), total_docs INT, processed_docs INT, error_count INT, error_details JSONB, created_by…
