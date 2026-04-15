# python & Backend (app/graph/state.py)
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **python** (C:\project\tenopa proposer\-agent-master\docs\02-design\proposal-workflow-states.md) -- 1 connections
  - <- has_code_example <- [[backend-appgraphstatepy]]
- **Backend (app/graph/state.py)** (C:\project\tenopa proposer\-agent-master\docs\02-design\proposal-workflow-states.md) -- 1 connections
  - -> has_code_example -> [[python]]

## Internal Relationships
- Backend (app/graph/state.py) -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 python, Backend (app/graph/state.py)를 중심으로 has_code_example 관계로 연결되어 있다. 주요 소스 파일은 proposal-workflow-states.md이다.

### Key Facts
- Backend (app/graph/state.py) ```python class ProposalStatus(str, Enum): WAITING = "waiting"           # 대기 IN_PROGRESS = "in_progress"   # 진행 COMPLETED = "completed"       # 완료 SUBMITTED = "submitted"       # 제출 PRESENTATION = "presentation" # 발표 CLOSED = "closed"             # 종료 ARCHIVED =…
- Database Migration ```sql -- proposals 테이블 status enum 확장 ALTER TYPE proposal_status ADD VALUE 'submitted', 'presentation', 'closed', 'archived';
