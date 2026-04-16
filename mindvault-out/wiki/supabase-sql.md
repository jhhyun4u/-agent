# Supabase 데이터베이스 설정 가이드 & sql
Cohesion: 0.17 | Nodes: 15

## Key Nodes
- **Supabase 데이터베이스 설정 가이드** (C:\project\tenopa proposer\database\README.md) -- 10 connections
  - -> contains -> [[1-supabase]]
  - -> contains -> [[2]]
  - -> contains -> [[3-api]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[proposals]]
  - -> contains -> [[personnel]]
  - -> contains -> [[references]]
  - -> contains -> [[documents]]
  - -> contains -> [[row-level-security-rls]]
- **sql** (C:\project\tenopa proposer\database\README.md) -- 5 connections
  - <- has_code_example <- [[proposals]]
  - <- has_code_example <- [[personnel]]
  - <- has_code_example <- [[references]]
  - <- has_code_example <- [[documents]]
  - <- has_code_example <- [[row-level-security-rls]]
- **documents 테이블** (C:\project\tenopa proposer\database\README.md) -- 3 connections
  - -> has_code_example -> [[sql]]
  - -> has_code_example -> [[python]]
  - <- contains <- [[supabase]]
- **4. 환경 변수 설정** (C:\project\tenopa proposer\database\README.md) -- 2 connections
  - -> has_code_example -> [[env]]
  - <- contains <- [[supabase]]
- **5. 의존성 설치** (C:\project\tenopa proposer\database\README.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[supabase]]
- **personnel 테이블** (C:\project\tenopa proposer\database\README.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[supabase]]
- **proposals 테이블** (C:\project\tenopa proposer\database\README.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[supabase]]
- **references 테이블** (C:\project\tenopa proposer\database\README.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[supabase]]
- **Row Level Security (RLS)** (C:\project\tenopa proposer\database\README.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[supabase]]
- **bash** (C:\project\tenopa proposer\database\README.md) -- 1 connections
  - <- has_code_example <- [[5]]
- **env** (C:\project\tenopa proposer\database\README.md) -- 1 connections
  - <- has_code_example <- [[4]]
- **python** (C:\project\tenopa proposer\database\README.md) -- 1 connections
  - <- has_code_example <- [[documents]]
- **1. Supabase 프로젝트 생성** (C:\project\tenopa proposer\database\README.md) -- 1 connections
  - <- contains <- [[supabase]]
- **2. 데이터베이스 스키마 적용** (C:\project\tenopa proposer\database\README.md) -- 1 connections
  - <- contains <- [[supabase]]
- **3. API 키 확인** (C:\project\tenopa proposer\database\README.md) -- 1 connections
  - <- contains <- [[supabase]]

## Internal Relationships
- 4. 환경 변수 설정 -> has_code_example -> env [EXTRACTED]
- 5. 의존성 설치 -> has_code_example -> bash [EXTRACTED]
- documents 테이블 -> has_code_example -> sql [EXTRACTED]
- documents 테이블 -> has_code_example -> python [EXTRACTED]
- personnel 테이블 -> has_code_example -> sql [EXTRACTED]
- proposals 테이블 -> has_code_example -> sql [EXTRACTED]
- references 테이블 -> has_code_example -> sql [EXTRACTED]
- Row Level Security (RLS) -> has_code_example -> sql [EXTRACTED]
- Supabase 데이터베이스 설정 가이드 -> contains -> 1. Supabase 프로젝트 생성 [EXTRACTED]
- Supabase 데이터베이스 설정 가이드 -> contains -> 2. 데이터베이스 스키마 적용 [EXTRACTED]
- Supabase 데이터베이스 설정 가이드 -> contains -> 3. API 키 확인 [EXTRACTED]
- Supabase 데이터베이스 설정 가이드 -> contains -> 4. 환경 변수 설정 [EXTRACTED]
- Supabase 데이터베이스 설정 가이드 -> contains -> 5. 의존성 설치 [EXTRACTED]
- Supabase 데이터베이스 설정 가이드 -> contains -> proposals 테이블 [EXTRACTED]
- Supabase 데이터베이스 설정 가이드 -> contains -> personnel 테이블 [EXTRACTED]
- Supabase 데이터베이스 설정 가이드 -> contains -> references 테이블 [EXTRACTED]
- Supabase 데이터베이스 설정 가이드 -> contains -> documents 테이블 [EXTRACTED]
- Supabase 데이터베이스 설정 가이드 -> contains -> Row Level Security (RLS) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Supabase 데이터베이스 설정 가이드, sql, documents 테이블를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 README.md이다.

### Key Facts
- 이 프로젝트는 Supabase를 데이터베이스로 사용합니다. Supabase는 PostgreSQL 기반의 오픈소스 Firebase 대체제로, 실시간 데이터베이스, 인증, 스토리지 등을 제공합니다.
- 프로젝트 루트의 `.env` 파일을 수정:
- references 테이블 ```sql id              UUID PRIMARY KEY title           TEXT NOT NULL content         TEXT topics          TEXT[] created_at      TIMESTAMP updated_at      TIMESTAMP ```
- personnel 테이블 ```sql id              UUID PRIMARY KEY name            TEXT NOT NULL grade           TEXT NOT NULL role            TEXT NOT NULL expertise       TEXT[] available       BOOLEAN DEFAULT TRUE projects        INTEGER DEFAULT 0 created_at      TIMESTAMP updated_at      TIMESTAMP ```
- documents 테이블 ```sql id              UUID PRIMARY KEY filename        TEXT NOT NULL path            TEXT size            INTEGER metadata        JSONB created_at      TIMESTAMP updated_at      TIMESTAMP ```
