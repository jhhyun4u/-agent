# Project Overview: tenopa Proposal AI Coworker & Key Commands
Cohesion: 0.29 | Nodes: 7

## Key Nodes
- **Project Overview: tenopa Proposal AI Coworker** (C:\project\tenopa proposer\-agent-master\.serena\memories\project_overview.md) -- 5 connections
  - -> contains -> [[purpose]]
  - -> contains -> [[tech-stack]]
  - -> contains -> [[key-commands]]
  - -> contains -> [[workflow-structure-v40]]
  - -> contains -> [[current-task]]
- **Key Commands** (C:\project\tenopa proposer\-agent-master\.serena\memories\project_overview.md) -- 2 connections
  - -> has_code_example -> [[bash]]
  - <- contains <- [[project-overview-tenopa-proposal-ai-coworker]]
- **bash** (C:\project\tenopa proposer\-agent-master\.serena\memories\project_overview.md) -- 1 connections
  - <- has_code_example <- [[key-commands]]
- **Current Task** (C:\project\tenopa proposer\-agent-master\.serena\memories\project_overview.md) -- 1 connections
  - <- contains <- [[project-overview-tenopa-proposal-ai-coworker]]
- **Purpose** (C:\project\tenopa proposer\-agent-master\.serena\memories\project_overview.md) -- 1 connections
  - <- contains <- [[project-overview-tenopa-proposal-ai-coworker]]
- **Tech Stack** (C:\project\tenopa proposer\-agent-master\.serena\memories\project_overview.md) -- 1 connections
  - <- contains <- [[project-overview-tenopa-proposal-ai-coworker]]
- **Workflow Structure (v4.0)** (C:\project\tenopa proposer\-agent-master\.serena\memories\project_overview.md) -- 1 connections
  - <- contains <- [[project-overview-tenopa-proposal-ai-coworker]]

## Internal Relationships
- Key Commands -> has_code_example -> bash [EXTRACTED]
- Project Overview: tenopa Proposal AI Coworker -> contains -> Purpose [EXTRACTED]
- Project Overview: tenopa Proposal AI Coworker -> contains -> Tech Stack [EXTRACTED]
- Project Overview: tenopa Proposal AI Coworker -> contains -> Key Commands [EXTRACTED]
- Project Overview: tenopa Proposal AI Coworker -> contains -> Workflow Structure (v4.0) [EXTRACTED]
- Project Overview: tenopa Proposal AI Coworker -> contains -> Current Task [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Project Overview: tenopa Proposal AI Coworker, Key Commands, bash를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 project_overview.md이다.

### Key Facts
- Purpose 내부 직원이 활용하는 용역제안 AI 협업 플랫폼. 용역과제 모니터링과 제안서 공동 작성을 수행하는 AI Coworker가 제안 워크플로우를 지원.
- Workflow Structure (v4.0) STEP 1 → STEP 2 → FORK → Path A (3A→4A→5A→6A) + Path B (3B→4B→5B→6B) → Convergence → STEP 7→8
- Key Commands ```bash uv sync                              # Install dependencies uv run uvicorn app.main:app --reload  # Run dev server uv run pytest                         # Run tests uv run python scripts/seed_data.py    # Seed data ```
- Current Task Implement redesigned STEP 3A-5A workflow per plan document: wise-munching-kahan.md - Move customer_analysis from STEP 8A to STEP 3A parallel execution - Create section_quality_check node (4-axis diagnosis) - Create storyline_gap_analysis node (plan vs actual comparison) - Update graph…
- Tech Stack - Backend: Python 3.11+ / FastAPI (Railway/Render) - Frontend: Next.js 15+ / React 19+ / TypeScript (Vercel) - Orchestration: LangGraph (StateGraph + interrupt + PostgresSaver) - AI: Anthropic Claude API (claude-sonnet-4-5-20250929) - Database: Supabase (PostgreSQL + Auth + RLS + Storage…
