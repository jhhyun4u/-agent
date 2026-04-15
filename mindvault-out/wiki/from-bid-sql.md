# 제안결정 완전 워크플로 (from-bid) & sql
Cohesion: 0.33 | Nodes: 7

## Key Nodes
- **제안결정 완전 워크플로 (from-bid)** (C:\project\tenopa proposer\-agent-master\WORKFLOW_PROPOSAL_DECISION.md) -- 4 connections
  - -> contains -> [[1-proposals]]
  - -> contains -> [[2-proposaltasks]]
  - -> contains -> [[3-backend-routesproposalpy]]
  - -> contains -> [[4-frontend]]
- **sql** (C:\project\tenopa proposer\-agent-master\WORKFLOW_PROPOSAL_DECISION.md) -- 2 connections
  - <- has_code_example <- [[1-proposals]]
  - <- has_code_example <- [[2-proposaltasks]]
- **1️⃣ 필요한 컬럼 추가 (proposals 테이블)** (C:\project\tenopa proposer\-agent-master\WORKFLOW_PROPOSAL_DECISION.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[from-bid]]
- **2️⃣ 새 테이블 생성 (proposal_tasks)** (C:\project\tenopa proposer\-agent-master\WORKFLOW_PROPOSAL_DECISION.md) -- 2 connections
  - -> has_code_example -> [[sql]]
  - <- contains <- [[from-bid]]
- **3️⃣ Backend 로직 (routes_proposal.py)** (C:\project\tenopa proposer\-agent-master\WORKFLOW_PROPOSAL_DECISION.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[from-bid]]
- **python** (C:\project\tenopa proposer\-agent-master\WORKFLOW_PROPOSAL_DECISION.md) -- 1 connections
  - <- has_code_example <- [[3-backend-routesproposalpy]]
- **4️⃣ Frontend 조회 엔드포인트** (C:\project\tenopa proposer\-agent-master\WORKFLOW_PROPOSAL_DECISION.md) -- 1 connections
  - <- contains <- [[from-bid]]

## Internal Relationships
- 1️⃣ 필요한 컬럼 추가 (proposals 테이블) -> has_code_example -> sql [EXTRACTED]
- 2️⃣ 새 테이블 생성 (proposal_tasks) -> has_code_example -> sql [EXTRACTED]
- 3️⃣ Backend 로직 (routes_proposal.py) -> has_code_example -> python [EXTRACTED]
- 제안결정 완전 워크플로 (from-bid) -> contains -> 1️⃣ 필요한 컬럼 추가 (proposals 테이블) [EXTRACTED]
- 제안결정 완전 워크플로 (from-bid) -> contains -> 2️⃣ 새 테이블 생성 (proposal_tasks) [EXTRACTED]
- 제안결정 완전 워크플로 (from-bid) -> contains -> 3️⃣ Backend 로직 (routes_proposal.py) [EXTRACTED]
- 제안결정 완전 워크플로 (from-bid) -> contains -> 4️⃣ Frontend 조회 엔드포인트 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 제안결정 완전 워크플로 (from-bid), sql, 1️⃣ 필요한 컬럼 추가 (proposals 테이블)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 WORKFLOW_PROPOSAL_DECISION.md이다.

### Key Facts
- │                                                                     │ └─────────────────────────────────────────────────────────────────┘ ↓ ┌─ Database (Supabase PostgreSQL) ──────────────────────────────────┐ │                                                                    │ │ proposals 테이블:…
- ```sql -- 마이그레이션: 005_proposal_decision_and_tasks.sql 참고 ALTER TABLE proposals ADD COLUMN go_decision BOOLEAN DEFAULT false, ADD COLUMN decision_date TIMESTAMPTZ, ADD COLUMN bid_tracked BOOLEAN DEFAULT true; ```
- ```sql CREATE TABLE proposal_tasks ( id              UUID PRIMARY KEY, proposal_id     UUID REFERENCES proposals(id), assigned_team_id UUID REFERENCES teams(id), description     TEXT, status          TEXT DEFAULT 'waiting',  -- waiting | in_progress | completed | blocked priority        TEXT…
- ```python from-bid 엔드포인트 POST /api/proposals/from-bid
- ```python from-bid 엔드포인트 POST /api/proposals/from-bid
