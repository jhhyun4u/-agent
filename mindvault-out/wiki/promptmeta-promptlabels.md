# PromptMeta & promptLabels
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **PromptMeta** (C:\project\tenopa proposer\frontend\components\prompt\promptLabels.ts) -- 1 connections
  - <- contains <- [[promptlabels]]
- **promptLabels** (C:\project\tenopa proposer\frontend\components\prompt\promptLabels.ts) -- 1 connections
  - -> contains -> [[promptmeta]]

## Internal Relationships
- promptLabels -> contains -> PromptMeta [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 PromptMeta, promptLabels를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 promptLabels.ts이다.

### Key Facts
- interface PromptMeta { label: string; description: string; step: string; }
