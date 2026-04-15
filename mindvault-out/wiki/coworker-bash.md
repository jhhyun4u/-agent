# 용역제안 Coworker & bash
Cohesion: 0.28 | Nodes: 9

## Key Nodes
- **용역제안 Coworker** (C:\project\tenopa proposer\-agent-master\README.md) -- 8 connections
  - -> has_code_example -> [[bash]]
  - -> contains -> [[docker-compose]]
  - -> contains -> [[1-supabase]]
  - -> contains -> [[2-railway]]
  - -> contains -> [[3-vercel]]
  - -> contains -> [[4-cicd]]
  - -> contains -> [[5-db]]
  - -> contains -> [[api]]
- **bash** (C:\project\tenopa proposer\-agent-master\README.md) -- 3 connections
  - <- has_code_example <- [[coworker]]
  - <- has_code_example <- [[docker-compose]]
  - <- has_code_example <- [[5-db]]
- **5. DB 마이그레이션** (C:\project\tenopa proposer\-agent-master\README.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[coworker]]
- **Docker Compose (통합 환경)** (C:\project\tenopa proposer\-agent-master\README.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[coworker]]
- **1. Supabase 설정** (C:\project\tenopa proposer\-agent-master\README.md) -- 1 connections
  - <- contains <- [[coworker]]
- **2. 백엔드 배포 (Railway)** (C:\project\tenopa proposer\-agent-master\README.md) -- 1 connections
  - <- contains <- [[coworker]]
- **3. 프론트엔드 배포 (Vercel)** (C:\project\tenopa proposer\-agent-master\README.md) -- 1 connections
  - <- contains <- [[coworker]]
- **4. CI/CD** (C:\project\tenopa proposer\-agent-master\README.md) -- 1 connections
  - <- contains <- [[coworker]]
- **API 엔드포인트** (C:\project\tenopa proposer\-agent-master\README.md) -- 1 connections
  - <- contains <- [[coworker]]

## Internal Relationships
- 5. DB 마이그레이션 -> has_code_example -> bash [EXTRACTED]
- 용역제안 Coworker -> has_code_example -> bash [EXTRACTED]
- 용역제안 Coworker -> contains -> Docker Compose (통합 환경) [EXTRACTED]
- 용역제안 Coworker -> contains -> 1. Supabase 설정 [EXTRACTED]
- 용역제안 Coworker -> contains -> 2. 백엔드 배포 (Railway) [EXTRACTED]
- 용역제안 Coworker -> contains -> 3. 프론트엔드 배포 (Vercel) [EXTRACTED]
- 용역제안 Coworker -> contains -> 4. CI/CD [EXTRACTED]
- 용역제안 Coworker -> contains -> 5. DB 마이그레이션 [EXTRACTED]
- 용역제안 Coworker -> contains -> API 엔드포인트 [EXTRACTED]
- Docker Compose (통합 환경) -> has_code_example -> bash [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 용역제안 Coworker, bash, 5. DB 마이그레이션를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 README.md이다.

### Key Facts
- > 프로젝트 수주 성공률을 높이는 AI Coworker
- ```bash uv sync                                # 의존성 설치 cp .env.example .env                   # 환경변수 설정 uv run uvicorn app.main:app --reload   # 개발 서버 (http://localhost:8000) ```
- 신규 마이그레이션 적용 시: ```bash Supabase SQL Editor에서 직접 실행 database/migrations/ 내 해당 SQL 파일 내용 복사 → 실행 ```
- ```bash docker compose up -d                   # 백엔드 + PostgreSQL + 프론트엔드 docker compose logs -f backend         # 로그 확인 docker compose down                    # 종료 ```
- 1. [Supabase](https://supabase.com)에서 프로젝트 생성 2. SQL Editor에서 `database/schema_v3.4.sql` 실행 3. `database/migrations/` 내 SQL 파일을 순서대로 실행 (004 → 011) 4. 프로젝트 URL과 키 확보 (Settings → API)
