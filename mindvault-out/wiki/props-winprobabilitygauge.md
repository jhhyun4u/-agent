# Props & WinProbabilityGauge
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **Props** (C:\project\tenopa proposer\-agent-master\frontend\components\pricing\WinProbabilityGauge.tsx) -- 1 connections
  - <- contains <- [[winprobabilitygauge]]
- **WinProbabilityGauge** (C:\project\tenopa proposer\-agent-master\frontend\components\pricing\WinProbabilityGauge.tsx) -- 1 connections
  - -> contains -> [[props]]

## Internal Relationships
- WinProbabilityGauge -> contains -> Props [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Props, WinProbabilityGauge를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 WinProbabilityGauge.tsx이다.

### Key Facts
- interface Props { probability: number; // 0.0 ~ 1.0 confidence: string; // high | medium | low }
- export default function WinProbabilityGauge({ probability, confidence, }: Props) { const pct = Math.round(probability * 100); // 게이지 바 — 10칸 const filled = Math.round(pct / 10);
