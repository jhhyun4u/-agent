# StreamProgressHeader & Props
Cohesion: 0.50 | Nodes: 4

## Key Nodes
- **StreamProgressHeader** (C:\project\tenopa proposer\-agent-master\frontend\components\StreamProgressHeader.tsx) -- 3 connections
  - -> contains -> [[streaminfo]]
  - -> contains -> [[props]]
  - -> contains -> [[getcolors]]
- **Props** (C:\project\tenopa proposer\-agent-master\frontend\components\StreamProgressHeader.tsx) -- 1 connections
  - <- contains <- [[streamprogressheader]]
- **StreamInfo** (C:\project\tenopa proposer\-agent-master\frontend\components\StreamProgressHeader.tsx) -- 1 connections
  - <- contains <- [[streamprogressheader]]
- **getColors** (C:\project\tenopa proposer\-agent-master\frontend\components\StreamProgressHeader.tsx) -- 1 connections
  - <- contains <- [[streamprogressheader]]

## Internal Relationships
- StreamProgressHeader -> contains -> StreamInfo [EXTRACTED]
- StreamProgressHeader -> contains -> Props [EXTRACTED]
- StreamProgressHeader -> contains -> getColors [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 StreamProgressHeader, Props, StreamInfo를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 StreamProgressHeader.tsx이다.

### Key Facts
- /** * StreamProgressHeader — 3-스트림 미니 진행바 (항상 노출) * * 색상: 회색(미시작) → 파랑(진행) → 황색(차단) → 초록+체크(완료) * 클릭 시 해당 탭으로 전환. */
- interface Props { streams: StreamInfo[]; onStreamClick?: (stream: string) => void; }
- interface StreamInfo { stream: string; status: string; progress_pct: number; current_phase?: string | null; }
- function getColors(status: string) { return STATUS_COLORS[status] || STATUS_COLORS.not_started; }
