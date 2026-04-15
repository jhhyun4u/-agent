# TrendChart & TrendChartProps
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **TrendChart** (C:\project\tenopa proposer\-agent-master\frontend\components\prompt\TrendChart.tsx) -- 2 connections
  - -> contains -> [[trendpoint]]
  - -> contains -> [[trendchartprops]]
- **TrendChartProps** (C:\project\tenopa proposer\-agent-master\frontend\components\prompt\TrendChart.tsx) -- 1 connections
  - <- contains <- [[trendchart]]
- **TrendPoint** (C:\project\tenopa proposer\-agent-master\frontend\components\prompt\TrendChart.tsx) -- 1 connections
  - <- contains <- [[trendchart]]

## Internal Relationships
- TrendChart -> contains -> TrendPoint [EXTRACTED]
- TrendChart -> contains -> TrendChartProps [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 TrendChart, TrendChartProps, TrendPoint를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 TrendChart.tsx이다.

### Key Facts
- /** * TrendChart — 월별 추이 라인 차트 * * 수정율/품질/수주율 추이를 시각화. 버전 변경 마커 포함. */
- interface TrendChartProps { data: TrendPoint[]; metric: "quality" | "edit_ratio" | "win_rate"; }
- interface TrendPoint { period: string; quality: number | null; edit_ratio: number | null; win_rate: number | null; }
