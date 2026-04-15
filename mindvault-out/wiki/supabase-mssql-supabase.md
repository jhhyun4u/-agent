# Supabase 데이터 구조 & 파일럿 마이그레이션 가이드 (MSSQL → Supabase)
Cohesion: 0.21 | Nodes: 15

## Key Nodes
- **Supabase 데이터 구조** (C:\project\tenopa proposer\-agent-master\docs\PILOT_MIGRATION_GUIDE.md) -- 11 connections
  - -> contains -> [[intranetprojects]]
  - -> contains -> [[rpc]]
  - -> contains -> [[1-mssql]]
  - -> contains -> [[2]]
  - -> contains -> [[3-supabase]]
  - -> contains -> [[4]]
  - -> contains -> [[mssql]]
  - -> contains -> [[supabase]]
  - -> contains -> [[openai]]
  - <- contains <- [[mssql-supabase]]
  - <- contains <- [[supabase]]
- **파일럿 마이그레이션 가이드 (MSSQL → Supabase)** (C:\project\tenopa proposer\-agent-master\docs\PILOT_MIGRATION_GUIDE.md) -- 5 connections
  - -> has_code_example -> [[bash]]
  - -> contains -> [[1-dry-run]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[supabase]]
- **bash** (C:\project\tenopa proposer\-agent-master\docs\PILOT_MIGRATION_GUIDE.md) -- 4 connections
  - <- has_code_example <- [[mssql-supabase]]
  - <- has_code_example <- [[1-dry-run]]
  - <- has_code_example <- [[2]]
  - <- has_code_example <- [[4]]
- **4. 임베딩 생성** (C:\project\tenopa proposer\-agent-master\docs\PILOT_MIGRATION_GUIDE.md) -- 4 connections
  - -> has_code_example -> [[python]]
  - -> has_code_example -> [[sql]]
  - -> has_code_example -> [[bash]]
  - <- contains <- [[supabase]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\PILOT_MIGRATION_GUIDE.md) -- 3 connections
  - <- has_code_example <- [[1-mssql]]
  - <- has_code_example <- [[3-supabase]]
  - <- has_code_example <- [[4]]
- **sql** (C:\project\tenopa proposer\-agent-master\docs\PILOT_MIGRATION_GUIDE.md) -- 3 connections
  - <- has_code_example <- [[intranetprojects]]
  - <- has_code_example <- [[rpc]]
  - <- has_code_example <- [[4]]
- **2단계: 실제 마이그레이션 실행** (C:\project\tenopa proposer\-agent-master\docs\PILOT_MIGRATION_GUIDE.md) -- 3 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[mssql-supabase]]
  - <- contains <- [[supabase]]
- **1단계: 데이터 미리보기 (DRY-RUN)** (C:\project\tenopa proposer\-agent-master\docs\PILOT_MIGRATION_GUIDE.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[mssql-supabase]]
- **1. 데이터 추출 (MSSQL)** (C:\project\tenopa proposer\-agent-master\docs\PILOT_MIGRATION_GUIDE.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[supabase]]
- **3. Supabase 삽입** (C:\project\tenopa proposer\-agent-master\docs\PILOT_MIGRATION_GUIDE.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[supabase]]
- **intranet_projects 테이블** (C:\project\tenopa proposer\-agent-master\docs\PILOT_MIGRATION_GUIDE.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[supabase]]
- **벡터 검색 RPC 함수** (C:\project\tenopa proposer\-agent-master\docs\PILOT_MIGRATION_GUIDE.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[supabase]]
- **3단계: 벡터 검색 테스트** (C:\project\tenopa proposer\-agent-master\docs\PILOT_MIGRATION_GUIDE.md) -- 1 connections
  - <- contains <- [[mssql-supabase]]
- **MSSQL 연결 오류** (C:\project\tenopa proposer\-agent-master\docs\PILOT_MIGRATION_GUIDE.md) -- 1 connections
  - <- contains <- [[supabase]]
- **OpenAI 임베딩 오류** (C:\project\tenopa proposer\-agent-master\docs\PILOT_MIGRATION_GUIDE.md) -- 1 connections
  - <- contains <- [[supabase]]

## Internal Relationships
- 1단계: 데이터 미리보기 (DRY-RUN) -> has_code_example -> bash [EXTRACTED]
- 1. 데이터 추출 (MSSQL) -> has_code_example -> python [EXTRACTED]
- 2단계: 실제 마이그레이션 실행 -> has_code_example -> bash [EXTRACTED]
- 3. Supabase 삽입 -> has_code_example -> python [EXTRACTED]
- 4. 임베딩 생성 -> has_code_example -> python [EXTRACTED]
- 4. 임베딩 생성 -> has_code_example -> sql [EXTRACTED]
- 4. 임베딩 생성 -> has_code_example -> bash [EXTRACTED]
- intranet_projects 테이블 -> has_code_example -> sql [EXTRACTED]
- 파일럿 마이그레이션 가이드 (MSSQL → Supabase) -> has_code_example -> bash [EXTRACTED]
- 파일럿 마이그레이션 가이드 (MSSQL → Supabase) -> contains -> 1단계: 데이터 미리보기 (DRY-RUN) [EXTRACTED]
- 파일럿 마이그레이션 가이드 (MSSQL → Supabase) -> contains -> 2단계: 실제 마이그레이션 실행 [EXTRACTED]
- 파일럿 마이그레이션 가이드 (MSSQL → Supabase) -> contains -> 3단계: 벡터 검색 테스트 [EXTRACTED]
- 파일럿 마이그레이션 가이드 (MSSQL → Supabase) -> contains -> Supabase 데이터 구조 [EXTRACTED]
- 벡터 검색 RPC 함수 -> has_code_example -> sql [EXTRACTED]
- Supabase 데이터 구조 -> contains -> intranet_projects 테이블 [EXTRACTED]
- Supabase 데이터 구조 -> contains -> 벡터 검색 RPC 함수 [EXTRACTED]
- Supabase 데이터 구조 -> contains -> 1. 데이터 추출 (MSSQL) [EXTRACTED]
- Supabase 데이터 구조 -> contains -> 2단계: 실제 마이그레이션 실행 [EXTRACTED]
- Supabase 데이터 구조 -> contains -> 3. Supabase 삽입 [EXTRACTED]
- Supabase 데이터 구조 -> contains -> 4. 임베딩 생성 [EXTRACTED]
- Supabase 데이터 구조 -> contains -> MSSQL 연결 오류 [EXTRACTED]
- Supabase 데이터 구조 -> contains -> Supabase 데이터 구조 [EXTRACTED]
- Supabase 데이터 구조 -> contains -> OpenAI 임베딩 오류 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Supabase 데이터 구조, 파일럿 마이그레이션 가이드 (MSSQL → Supabase), bash를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 PILOT_MIGRATION_GUIDE.md이다.

### Key Facts
- intranet_projects 테이블
- ```bash 필수 환경 변수 설정 (.env 파일) MSSQL_HOST=10.1.3.251 MSSQL_USER=sa MSSQL_PASSWORD=<your-password> MSSQL_DATABASE=intranet
- ```python OpenAI API로 임베딩 생성 embedding = openai_client.embeddings.create( model="text-embedding-3-small", input="AI 기반 제안서 자동 작성 플랫폼... 국방부" ).data[0].embedding  # 1536-dim vector
- 스크립트 1: 실제 MSSQL에서 가져오기 python scripts/pilot_migration_10projects.py --dry-run
- ```bash 스크립트 1: MSSQL 연결 가능할 경우 python scripts/pilot_migration_10projects.py --execute
