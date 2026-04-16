# Project: TENOPA Proposer & Current State (2026-03-16)
Cohesion: 0.25 | Nodes: 8

## Key Nodes
- **Project: TENOPA Proposer** (C:\project\tenopa proposer\.claude\agent-memory\bkit-gap-detector\MEMORY.md) -- 7 connections
  - -> contains -> [[current-state-2026-03-16]]
  - -> contains -> [[key-file-paths]]
  - -> contains -> [[match-rate-history]]
  - -> contains -> [[v2-re-analysis-resolved-items-6-medium]]
  - -> contains -> [[remaining-gaps]]
  - -> contains -> [[notes]]
  - <- contains <- [[gap-detector-agent-memory]]
- **Current State (2026-03-16)** (C:\project\tenopa proposer\.claude\agent-memory\bkit-gap-detector\MEMORY.md) -- 1 connections
  - <- contains <- [[project-tenopa-proposer]]
- **Gap Detector - Agent Memory** (C:\project\tenopa proposer\.claude\agent-memory\bkit-gap-detector\MEMORY.md) -- 1 connections
  - -> contains -> [[project-tenopa-proposer]]
- **Key File Paths** (C:\project\tenopa proposer\.claude\agent-memory\bkit-gap-detector\MEMORY.md) -- 1 connections
  - <- contains <- [[project-tenopa-proposer]]
- **Match Rate History** (C:\project\tenopa proposer\.claude\agent-memory\bkit-gap-detector\MEMORY.md) -- 1 connections
  - <- contains <- [[project-tenopa-proposer]]
- **Notes** (C:\project\tenopa proposer\.claude\agent-memory\bkit-gap-detector\MEMORY.md) -- 1 connections
  - <- contains <- [[project-tenopa-proposer]]
- **Remaining Gaps** (C:\project\tenopa proposer\.claude\agent-memory\bkit-gap-detector\MEMORY.md) -- 1 connections
  - <- contains <- [[project-tenopa-proposer]]
- **v2 Re-analysis Resolved Items (6 MEDIUM)** (C:\project\tenopa proposer\.claude\agent-memory\bkit-gap-detector\MEMORY.md) -- 1 connections
  - <- contains <- [[project-tenopa-proposer]]

## Internal Relationships
- Gap Detector - Agent Memory -> contains -> Project: TENOPA Proposer [EXTRACTED]
- Project: TENOPA Proposer -> contains -> Current State (2026-03-16) [EXTRACTED]
- Project: TENOPA Proposer -> contains -> Key File Paths [EXTRACTED]
- Project: TENOPA Proposer -> contains -> Match Rate History [EXTRACTED]
- Project: TENOPA Proposer -> contains -> v2 Re-analysis Resolved Items (6 MEDIUM) [EXTRACTED]
- Project: TENOPA Proposer -> contains -> Remaining Gaps [EXTRACTED]
- Project: TENOPA Proposer -> contains -> Notes [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Project: TENOPA Proposer, Current State (2026-03-16), Gap Detector - Agent Memory를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 MEMORY.md이다.

### Key Facts
- Current State (2026-03-16) - Requirements: v4.9 (archived) - Design: v3.6 (archived to `docs/archive/2026-03/proposal-agent-v1/design/`, 18 modular files) - Gap Analysis (proposal-agent-v1): 99% (archived) - Gap Analysis (proposal-platform-v1): **98%** (v2 re-analysis, 2026-03-16) - HIGH remaining:…
- Key File Paths - Design (archived): `docs/archive/2026-03/proposal-agent-v1/design/_index.md` - Previous analysis (archived): `docs/archive/2026-03/proposal-agent-v1/proposal-agent-v1.analysis.md` (99%) - Platform v1 design (archived):…
- Project: TENOPA Proposer
- Match Rate History - v3.0: 82% | v3.1: 94% | v3.2: 96% | v3.3: 97% | v3.4: 97% | v3.5: 98% | v3.6: 99% (prompt/graph focus) - platform-v1: 10% (2026-03-06) -> 88% (2026-03-16) -> 92% (Iteration 1) -> 96% (full analysis) -> **98% (v2, MEDIUM 6 resolved)**
- v2 Re-analysis Resolved Items (6 MEDIUM) 1. goto/{step} API: routes_workflow.py (aget_state_history + aupdate_state) 2. impact/{step} API: routes_workflow.py (_NODE_ORDER topology) 3. Section regenerate API: routes_artifacts.py (classify_section_type + get_section_prompt) 4. AI assist API:…
