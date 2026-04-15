# Implementation Summary & Files Created (3)
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **Implementation Summary** (C:\project\tenopa proposer\-agent-master\.claude\agent-memory\bkit-report-generator\project_token_tracking_complete.md) -- 2 connections
  - -> contains -> [[files-created-3]]
  - -> contains -> [[files-modified-3]]
- **Files Created (3)** (C:\project\tenopa proposer\-agent-master\.claude\agent-memory\bkit-report-generator\project_token_tracking_complete.md) -- 1 connections
  - <- contains <- [[implementation-summary]]
- **Files Modified (3)** (C:\project\tenopa proposer\-agent-master\.claude\agent-memory\bkit-report-generator\project_token_tracking_complete.md) -- 1 connections
  - <- contains <- [[implementation-summary]]

## Internal Relationships
- Implementation Summary -> contains -> Files Created (3) [EXTRACTED]
- Implementation Summary -> contains -> Files Modified (3) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Implementation Summary, Files Created (3), Files Modified (3)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 project_token_tracking_complete.md이다.

### Key Facts
- Files Created (3) - `app/services/token_pricing.py` (79 lines) — Model pricing dict + cost calculation - `app/graph/token_tracking.py` (82 lines) — Decorator + fire-and-forget DB persist - `database/migrations/005_token_cost.sql` (6 lines) — Schema extension
- Files Modified (3) - `app/services/claude_client.py` — ContextVar infrastructure + token append logic - `app/graph/graph.py` — 16 AI-calling nodes wrapped with `track_tokens()` - `app/api/routes_workflow.py` — Token usage query endpoint + token_summary field
- Architecture Decisions
