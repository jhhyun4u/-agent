# Gap 목록 & Workflow UX Gap Analysis
Cohesion: 0.29 | Nodes: 7

## Key Nodes
- **Gap 목록** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\workflow-ux.analysis.md) -- 4 connections
  - -> contains -> [[high-1]]
  - -> contains -> [[medium-4]]
  - -> contains -> [[low-5]]
  - <- contains <- [[workflow-ux-gap-analysis]]
- **Workflow UX Gap Analysis** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\workflow-ux.analysis.md) -- 3 connections
  - -> contains -> [[match-rate-92]]
  - -> contains -> [[gap]]
  - -> contains -> [[gap-04-paused-ui]]
- **즉시 대응: GAP-04 (paused UI)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\workflow-ux.analysis.md) -- 1 connections
  - <- contains <- [[workflow-ux-gap-analysis]]
- **HIGH (1건)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\workflow-ux.analysis.md) -- 1 connections
  - <- contains <- [[gap]]
- **LOW (5건)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\workflow-ux.analysis.md) -- 1 connections
  - <- contains <- [[gap]]
- **Match Rate: 92%** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\workflow-ux.analysis.md) -- 1 connections
  - <- contains <- [[workflow-ux-gap-analysis]]
- **MEDIUM (4건)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\workflow-ux.analysis.md) -- 1 connections
  - <- contains <- [[gap]]

## Internal Relationships
- Gap 목록 -> contains -> HIGH (1건) [EXTRACTED]
- Gap 목록 -> contains -> MEDIUM (4건) [EXTRACTED]
- Gap 목록 -> contains -> LOW (5건) [EXTRACTED]
- Workflow UX Gap Analysis -> contains -> Match Rate: 92% [EXTRACTED]
- Workflow UX Gap Analysis -> contains -> Gap 목록 [EXTRACTED]
- Workflow UX Gap Analysis -> contains -> 즉시 대응: GAP-04 (paused UI) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Gap 목록, Workflow UX Gap Analysis, 즉시 대응: GAP-04 (paused UI)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 workflow-ux.analysis.md이다.

### Key Facts
- > Plan 문서 vs 구현 비교 (2026-03-18)
- page.tsx + WorkflowPanel.tsx에 paused 상태 감지 + 재개/돌아가기 버튼 추가 필요.
- | ID | 영역 | 설명 | |----|------|------| | GAP-04 | 2-2 | **paused 상태 전용 UI 미구현** — ai-abort 후 "재개"+"이전 단계로" 버튼 없음 |
- | ID | 영역 | 설명 | |----|------|------| | GAP-02 | 2-1 | PHASES 상수가 page.tsx에 잔존 (WORKFLOW_STEPS와 불일치) | | GAP-07 | 2-3 | ppt_storyboard 전용 렌더러 없음 | | GAP-08 | 2-3 | RfpAnalyze에 Compliance Matrix 미표시 | | GAP-09 | 2-3 | Strategy에 가격 전략 미표시 | | GAP-10 | 2-4 | goto 후 리뷰 패널 자동 전환 미구현 |
- | 영역 | 점수 | 상태 | |------|:---:|:---:| | 2-1 세부 진행 표시 (SSE) | 93% | PASS | | 2-2 중단/재개 버튼 | 85% | WARNING | | 2-3 산출물 뷰어 | 90% | PASS | | 2-4 타임트래블 | 95% | PASS | | 2-5 로그 패널 | 95% | PASS |
