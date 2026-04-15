# EditPatternChart & EditPattern
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **EditPatternChart** (C:\project\tenopa proposer\-agent-master\frontend\components\prompt\EditPatternChart.tsx) -- 2 connections
  - -> contains -> [[editpattern]]
  - -> contains -> [[editpatternchartprops]]
- **EditPattern** (C:\project\tenopa proposer\-agent-master\frontend\components\prompt\EditPatternChart.tsx) -- 1 connections
  - <- contains <- [[editpatternchart]]
- **EditPatternChartProps** (C:\project\tenopa proposer\-agent-master\frontend\components\prompt\EditPatternChart.tsx) -- 1 connections
  - <- contains <- [[editpatternchart]]

## Internal Relationships
- EditPatternChart -> contains -> EditPattern [EXTRACTED]
- EditPatternChart -> contains -> EditPatternChartProps [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 EditPatternChart, EditPattern, EditPatternChartProps를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 EditPatternChart.tsx이다.

### Key Facts
- /** * EditPatternChart — 수정 패턴 수평 막대 차트 * * "사람이 어떤 종류의 수정을 많이 하는가"를 시각화. */
- /** * EditPatternChart — 수정 패턴 수평 막대 차트 * * "사람이 어떤 종류의 수정을 많이 하는가"를 시각화. */
- interface EditPatternChartProps { patterns: EditPattern[]; maxItems?: number; }
