# StreamTabBar & Props
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **StreamTabBar** (C:\project\tenopa proposer\-agent-master\frontend\components\StreamTabBar.tsx) -- 2 connections
  - -> contains -> [[streaminfo]]
  - -> contains -> [[props]]
- **Props** (C:\project\tenopa proposer\-agent-master\frontend\components\StreamTabBar.tsx) -- 1 connections
  - <- contains <- [[streamtabbar]]
- **StreamInfo** (C:\project\tenopa proposer\-agent-master\frontend\components\StreamTabBar.tsx) -- 1 connections
  - <- contains <- [[streamtabbar]]

## Internal Relationships
- StreamTabBar -> contains -> StreamInfo [EXTRACTED]
- StreamTabBar -> contains -> Props [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 StreamTabBar, Props, StreamInfo를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 StreamTabBar.tsx이다.

### Key Facts
- /** * StreamTabBar — 4개 탭 전환 (정성제안서 / 비딩관리 / 제출서류 / 통합현황) * * 각 탭에 스트림 상태 뱃지 표시. */
- interface Props { activeTab: StreamTab; onTabChange: (tab: StreamTab) => void; streams: StreamInfo[]; }
- interface StreamInfo { stream: string; status: string; progress_pct: number; }
