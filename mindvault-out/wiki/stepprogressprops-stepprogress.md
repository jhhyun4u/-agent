# StepProgressProps & StepProgress
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **StepProgressProps** (C:\project\tenopa proposer\-agent-master\frontend\components\prompt\StepProgress.tsx) -- 1 connections
  - <- contains <- [[stepprogress]]
- **StepProgress** (C:\project\tenopa proposer\-agent-master\frontend\components\prompt\StepProgress.tsx) -- 1 connections
  - -> contains -> [[stepprogressprops]]

## Internal Relationships
- StepProgress -> contains -> StepProgressProps [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 StepProgressProps, StepProgress를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 StepProgress.tsx이다.

### Key Facts
- interface StepProgressProps { currentStep: StepId; onStepClick?: (step: StepId) => void; }
- /** * StepProgress — 4스텝 진행 표시기 * * 문제파악 → 개선안 → 시뮬레이션 → 실험 */
