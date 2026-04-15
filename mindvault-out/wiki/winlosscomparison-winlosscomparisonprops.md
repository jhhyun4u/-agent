# WinLossComparison & WinLossComparisonProps
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **WinLossComparison** (C:\project\tenopa proposer\-agent-master\frontend\components\prompt\WinLossComparison.tsx) -- 2 connections
  - -> contains -> [[winlossdata]]
  - -> contains -> [[winlosscomparisonprops]]
- **WinLossComparisonProps** (C:\project\tenopa proposer\-agent-master\frontend\components\prompt\WinLossComparison.tsx) -- 1 connections
  - <- contains <- [[winlosscomparison]]
- **WinLossData** (C:\project\tenopa proposer\-agent-master\frontend\components\prompt\WinLossComparison.tsx) -- 1 connections
  - <- contains <- [[winlosscomparison]]

## Internal Relationships
- WinLossComparison -> contains -> WinLossData [EXTRACTED]
- WinLossComparison -> contains -> WinLossComparisonProps [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 WinLossComparison, WinLossComparisonProps, WinLossData를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 WinLossComparison.tsx이다.

### Key Facts
- /** * WinLossComparison — 수주/패찰 제안서 비교 테이블 */
- interface WinLossComparisonProps { data: WinLossData; }
- interface WinLossData { win_avg_quality: number; loss_avg_quality: number; win_count: number; loss_count: number; key_differences: string[]; }
