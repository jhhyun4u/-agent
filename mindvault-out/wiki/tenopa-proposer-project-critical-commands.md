# Tenopa Proposer Project & Critical Commands
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **Tenopa Proposer Project** (C:\project\tenopa proposer\.serena\memories\project_overview.md) -- 5 connections
  - -> contains -> [[purpose]]
  - -> contains -> [[tech-stack]]
  - -> contains -> [[key-features]]
  - -> contains -> [[project-root]]
  - -> contains -> [[critical-commands]]
- **Critical Commands** (C:\project\tenopa proposer\.serena\memories\project_overview.md) -- 1 connections
  - <- contains <- [[tenopa-proposer-project]]
- **Key Features** (C:\project\tenopa proposer\.serena\memories\project_overview.md) -- 1 connections
  - <- contains <- [[tenopa-proposer-project]]
- **Project Root** (C:\project\tenopa proposer\.serena\memories\project_overview.md) -- 1 connections
  - <- contains <- [[tenopa-proposer-project]]
- **Purpose** (C:\project\tenopa proposer\.serena\memories\project_overview.md) -- 1 connections
  - <- contains <- [[tenopa-proposer-project]]
- **Tech Stack** (C:\project\tenopa proposer\.serena\memories\project_overview.md) -- 1 connections
  - <- contains <- [[tenopa-proposer-project]]

## Internal Relationships
- Tenopa Proposer Project -> contains -> Purpose [EXTRACTED]
- Tenopa Proposer Project -> contains -> Tech Stack [EXTRACTED]
- Tenopa Proposer Project -> contains -> Key Features [EXTRACTED]
- Tenopa Proposer Project -> contains -> Project Root [EXTRACTED]
- Tenopa Proposer Project -> contains -> Critical Commands [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Tenopa Proposer Project, Critical Commands, Key Features를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 project_overview.md이다.

### Key Facts
- Purpose AI-powered proposal and project management system with document ingestion, workflow tracking, and decision support. Includes Document Ingestion API, Vault AI Chat for knowledge retrieval, and project proposal lifecycle management.
- Critical Commands - Start dev: `start-dev.sh` or `npm run dev` - Run tests: `pytest tests/` or specific test files - Docker: `docker-compose up -d` - Migrations: Located in `database/migrations/`
- Project Root `-agent-master/` (main source code directory)
- Critical Commands - Start dev: `start-dev.sh` or `npm run dev` - Run tests: `pytest tests/` or specific test files - Docker: `docker-compose up -d` - Migrations: Located in `database/migrations/`
- Tech Stack - **Backend**: Python 3.9+, FastAPI, async/await patterns, asyncio - **Frontend**: Node.js, React/Next.js - **Database**: Supabase (PostgreSQL + pgvector for embeddings) - **AI**: OpenAI embeddings and GPT models - **Monitoring**: Prometheus + Grafana - **Testing**: pytest with async…
