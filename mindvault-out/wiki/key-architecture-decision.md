# Key Architecture Decision
Cohesion: 1.00 | Nodes: 1

## Key Nodes
- **Key Architecture Decision** (C:\project\tenopa proposer\-agent-master\.claude\agent-memory\bkit-pdca-iterator\project_scheduler_integration_act1.md) -- 0 connections

## Internal Relationships

## Cross-Community Connections

## Context
이 커뮤니티는 Key Architecture Decision를 중심으로 related 관계로 연결되어 있다. 주요 소스 파일은 project_scheduler_integration_act1.md이다.

### Key Facts
- Single-scheduler pattern: app/scheduler.py (UTC, separate instance) was effectively removed from lifespan. All scheduled jobs live in app/services/scheduled_monitor.setup_scheduler() with KST timezone. app/scheduler.py file still exists on disk but is no longer called.
