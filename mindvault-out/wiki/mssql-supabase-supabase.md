# 파일럿 마이그레이션 (MSSQL → Supabase) - 실행 가이드 & 🔍 Supabase 데이터 구조
Cohesion: 0.14 | Nodes: 19

## Key Nodes
- **파일럿 마이그레이션 (MSSQL → Supabase) - 실행 가이드** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 7 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[step-1]]
  - -> contains -> [[step-2]]
  - -> contains -> [[step-3]]
  - -> contains -> [[step-4]]
  - -> contains -> [[supabase]]
- **🔍 Supabase 데이터 구조** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 7 connections
  - -> contains -> [[intranetprojects]]
  - -> contains -> [[rpc]]
  - -> contains -> [[mssql-a]]
  - -> contains -> [[supabase]]
  - -> contains -> [[openai-api]]
  - <- contains <- [[mssql-supabase]]
  - <- contains <- [[supabase]]
- **bash** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 5 connections
  - <- has_code_example <- [[step-2]]
  - <- has_code_example <- [[step-3]]
  - <- has_code_example <- [[1]]
  - <- has_code_example <- [[2]]
  - <- has_code_example <- [[3]]
- **1. 마이그레이션 스크립트** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 5 connections
  - -> contains -> [[a-mssql]]
  - -> contains -> [[b]]
  - -> has_code_example -> [[bash]]
  - <- contains <- [[mssql-supabase]]
  - <- contains <- [[openai-api]]
- **OpenAI API 오류** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 4 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - <- contains <- [[supabase]]
- **2. 문서** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 3 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[mssql-supabase]]
  - <- contains <- [[openai-api]]
- **3. 프론트엔드 통합** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 3 connections
  - -> references -> [[unresolvedrefpilotmigrationguide]]
  - -> has_code_example -> [[bash]]
  - <- contains <- [[openai-api]]
- **벡터 검색 RPC 함수** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[supabase]]
- **Step 1: 환경 변수 설정** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 2 connections
  - -> has_code_example -> [[env]]
  - <- contains <- [[mssql-supabase]]
- **Step 2: 데이터 미리보기 (권장)** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[mssql-supabase]]
- **Step 3: 실제 마이그레이션 실행** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[mssql-supabase]]
- **__unresolved__::ref::pilot_migration_guide** () -- 1 connections
  - <- references <- [[3]]
- **env** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 1 connections
  - <- has_code_example <- [[step-1]]
- **sql** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 1 connections
  - <- has_code_example <- [[rpc]]
- **A. MSSQL 직접 연결 버전** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 1 connections
  - <- contains <- [[1]]
- **B. 테스트 데이터 버전 (권장)** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 1 connections
  - <- contains <- [[1]]
- **intranet_projects 테이블** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 1 connections
  - <- contains <- [[supabase]]
- **MSSQL 연결 오류 (스크립트 A 사용 시)** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 1 connections
  - <- contains <- [[supabase]]
- **Step 4: 자동 검증** (C:\project\tenopa proposer\-agent-master\PILOT_MIGRATION_README.md) -- 1 connections
  - <- contains <- [[mssql-supabase]]

## Internal Relationships
- 1. 마이그레이션 스크립트 -> contains -> A. MSSQL 직접 연결 버전 [EXTRACTED]
- 1. 마이그레이션 스크립트 -> contains -> B. 테스트 데이터 버전 (권장) [EXTRACTED]
- 1. 마이그레이션 스크립트 -> has_code_example -> bash [EXTRACTED]
- 2. 문서 -> has_code_example -> bash [EXTRACTED]
- 3. 프론트엔드 통합 -> references -> __unresolved__::ref::pilot_migration_guide [EXTRACTED]
- 3. 프론트엔드 통합 -> has_code_example -> bash [EXTRACTED]
- 파일럿 마이그레이션 (MSSQL → Supabase) - 실행 가이드 -> contains -> 1. 마이그레이션 스크립트 [EXTRACTED]
- 파일럿 마이그레이션 (MSSQL → Supabase) - 실행 가이드 -> contains -> 2. 문서 [EXTRACTED]
- 파일럿 마이그레이션 (MSSQL → Supabase) - 실행 가이드 -> contains -> Step 1: 환경 변수 설정 [EXTRACTED]
- 파일럿 마이그레이션 (MSSQL → Supabase) - 실행 가이드 -> contains -> Step 2: 데이터 미리보기 (권장) [EXTRACTED]
- 파일럿 마이그레이션 (MSSQL → Supabase) - 실행 가이드 -> contains -> Step 3: 실제 마이그레이션 실행 [EXTRACTED]
- 파일럿 마이그레이션 (MSSQL → Supabase) - 실행 가이드 -> contains -> Step 4: 자동 검증 [EXTRACTED]
- 파일럿 마이그레이션 (MSSQL → Supabase) - 실행 가이드 -> contains -> 🔍 Supabase 데이터 구조 [EXTRACTED]
- OpenAI API 오류 -> contains -> 1. 마이그레이션 스크립트 [EXTRACTED]
- OpenAI API 오류 -> contains -> 2. 문서 [EXTRACTED]
- OpenAI API 오류 -> contains -> 3. 프론트엔드 통합 [EXTRACTED]
- 벡터 검색 RPC 함수 -> has_code_example -> sql [EXTRACTED]
- Step 1: 환경 변수 설정 -> has_code_example -> env [EXTRACTED]
- Step 2: 데이터 미리보기 (권장) -> has_code_example -> bash [EXTRACTED]
- Step 3: 실제 마이그레이션 실행 -> has_code_example -> bash [EXTRACTED]
- 🔍 Supabase 데이터 구조 -> contains -> intranet_projects 테이블 [EXTRACTED]
- 🔍 Supabase 데이터 구조 -> contains -> 벡터 검색 RPC 함수 [EXTRACTED]
- 🔍 Supabase 데이터 구조 -> contains -> MSSQL 연결 오류 (스크립트 A 사용 시) [EXTRACTED]
- 🔍 Supabase 데이터 구조 -> contains -> 🔍 Supabase 데이터 구조 [EXTRACTED]
- 🔍 Supabase 데이터 구조 -> contains -> OpenAI API 오류 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 파일럿 마이그레이션 (MSSQL → Supabase) - 실행 가이드, 🔍 Supabase 데이터 구조, bash를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 PILOT_MIGRATION_README.md이다.

### Key Facts
- > **상태:** ✅ 준비 완료 > **작성일:** 2026-04-11 > **담당:** 사용자
- intranet_projects 테이블
- ```bash 스크립트 B 사용 (권장: 테스트 데이터, MSSQL 불필요) python scripts/pilot_migration_demo.py --dry-run
- A. MSSQL 직접 연결 버전 ``` scripts/pilot_migration_10projects.py ``` - **용도:** MSSQL 10.1.3.251에서 직접 데이터 추출 - **대상:** Project_List 테이블의 상위 10개 프로젝트 - **전제:** MSSQL 접근 가능 (내부 네트워크)
- ``` Error: Invalid API key ```
