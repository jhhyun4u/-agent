# Supabase 설정 완료 가이드 & bash
Cohesion: 0.19 | Nodes: 13

## Key Nodes
- **Supabase 설정 완료 가이드** (C:\project\tenopa proposer\-agent-master\docs\SUPABASE_SETUP.md) -- 10 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4-supabase]]
  - -> contains -> [[5-mcp]]
  - -> contains -> [[1-rls-row-level-security]]
  - -> contains -> [[2-sql]]
  - -> contains -> [[3-postgresql]]
  - -> contains -> [[2-api]]
  - -> contains -> [[3-mcp]]
- **bash** (C:\project\tenopa proposer\-agent-master\docs\SUPABASE_SETUP.md) -- 4 connections
  - <- has_code_example <- [[2]]
  - <- has_code_example <- [[3-postgresql]]
  - <- has_code_example <- [[1]]
  - <- has_code_example <- [[2-api]]
- **1. 의존성 변경** (C:\project\tenopa proposer\-agent-master\docs\SUPABASE_SETUP.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[supabase]]
- **문제 1: RLS (Row Level Security) 정책으로 인한 접근 불가** (C:\project\tenopa proposer\-agent-master\docs\SUPABASE_SETUP.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[supabase]]
- **2. 환경 변수 설정** (C:\project\tenopa proposer\-agent-master\docs\SUPABASE_SETUP.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[supabase]]
- **2. API 엔드포인트 테스트** (C:\project\tenopa proposer\-agent-master\docs\SUPABASE_SETUP.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[supabase]]
- **문제 3: PostgreSQL 텍스트 검색 설정** (C:\project\tenopa proposer\-agent-master\docs\SUPABASE_SETUP.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[supabase]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\SUPABASE_SETUP.md) -- 1 connections
  - <- has_code_example <- [[1-rls-row-level-security]]
- **문제 2: SQL 예약어 충돌** (C:\project\tenopa proposer\-agent-master\docs\SUPABASE_SETUP.md) -- 1 connections
  - <- contains <- [[supabase]]
- **3. 데이터베이스 스키마** (C:\project\tenopa proposer\-agent-master\docs\SUPABASE_SETUP.md) -- 1 connections
  - <- contains <- [[supabase]]
- **3. MCP 서버 실제 사용 테스트** (C:\project\tenopa proposer\-agent-master\docs\SUPABASE_SETUP.md) -- 1 connections
  - <- contains <- [[supabase]]
- **4. Supabase 클라이언트 구현** (C:\project\tenopa proposer\-agent-master\docs\SUPABASE_SETUP.md) -- 1 connections
  - <- contains <- [[supabase]]
- **5. MCP 서버 통합** (C:\project\tenopa proposer\-agent-master\docs\SUPABASE_SETUP.md) -- 1 connections
  - <- contains <- [[supabase]]

## Internal Relationships
- 1. 의존성 변경 -> has_code_example -> bash [EXTRACTED]
- 문제 1: RLS (Row Level Security) 정책으로 인한 접근 불가 -> has_code_example -> python [EXTRACTED]
- 2. 환경 변수 설정 -> has_code_example -> bash [EXTRACTED]
- 2. API 엔드포인트 테스트 -> has_code_example -> bash [EXTRACTED]
- 문제 3: PostgreSQL 텍스트 검색 설정 -> has_code_example -> bash [EXTRACTED]
- Supabase 설정 완료 가이드 -> contains -> 1. 의존성 변경 [EXTRACTED]
- Supabase 설정 완료 가이드 -> contains -> 2. 환경 변수 설정 [EXTRACTED]
- Supabase 설정 완료 가이드 -> contains -> 3. 데이터베이스 스키마 [EXTRACTED]
- Supabase 설정 완료 가이드 -> contains -> 4. Supabase 클라이언트 구현 [EXTRACTED]
- Supabase 설정 완료 가이드 -> contains -> 5. MCP 서버 통합 [EXTRACTED]
- Supabase 설정 완료 가이드 -> contains -> 문제 1: RLS (Row Level Security) 정책으로 인한 접근 불가 [EXTRACTED]
- Supabase 설정 완료 가이드 -> contains -> 문제 2: SQL 예약어 충돌 [EXTRACTED]
- Supabase 설정 완료 가이드 -> contains -> 문제 3: PostgreSQL 텍스트 검색 설정 [EXTRACTED]
- Supabase 설정 완료 가이드 -> contains -> 2. API 엔드포인트 테스트 [EXTRACTED]
- Supabase 설정 완료 가이드 -> contains -> 3. MCP 서버 실제 사용 테스트 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Supabase 설정 완료 가이드, bash, 1. 의존성 변경를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 SUPABASE_SETUP.md이다.

### Key Facts
- 📋 개요 PostgreSQL에서 Supabase로 성공적으로 마이그레이션 완료했습니다.
- 2. 환경 변수 설정 `.env` 파일에 다음 값들이 설정되었습니다: ```bash SUPABASE_URL=https://qrejgelizidpqakbkvmp.supabase.co SUPABASE_KEY=eyJhbGci...  # anon key (클라이언트용) SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...  # service_role key (서버용, RLS 우회) ```
- 2. 환경 변수 설정 `.env` 파일에 다음 값들이 설정되었습니다: ```bash SUPABASE_URL=https://qrejgelizidpqakbkvmp.supabase.co SUPABASE_KEY=eyJhbGci...  # anon key (클라이언트용) SUPABASE_SERVICE_ROLE_KEY=eyJhbGci...  # service_role key (서버용, RLS 우회) ```
- **원인**: - `anon` 키는 RLS 정책의 제약을 받음 - RLS 정책이 `authenticated` 및 `service_role`만 허용
- 3. 데이터베이스 스키마 `database/supabase_schema.sql` 파일 실행 완료: - ✅ `proposals` 테이블: 제안서 데이터 (2건 샘플) - ✅ `personnel` 테이블: 인력 정보 (4명 샘플) - ✅ `reference_materials` 테이블: 참고 자료 (4건 샘플) - ✅ `documents` 테이블: 문서 메타데이터 (비어있음)
