# bid-monitoring-pipeline — 갭 분석 & GAP 목록
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **bid-monitoring-pipeline — 갭 분석** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\bid-monitoring-pipeline.analysis.md) -- 2 connections
  - -> contains -> [[match-rate]]
  - -> contains -> [[gap]]
- **GAP 목록** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\bid-monitoring-pipeline.analysis.md) -- 1 connections
  - <- contains <- [[bid-monitoring-pipeline]]
- **Match Rate** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\bid-monitoring-pipeline.analysis.md) -- 1 connections
  - <- contains <- [[bid-monitoring-pipeline]]

## Internal Relationships
- bid-monitoring-pipeline — 갭 분석 -> contains -> Match Rate [EXTRACTED]
- bid-monitoring-pipeline — 갭 분석 -> contains -> GAP 목록 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 bid-monitoring-pipeline — 갭 분석, GAP 목록, Match Rate를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 bid-monitoring-pipeline.analysis.md이다.

### Key Facts
- | 항목 | 내용 | |------|------| | 분석일 | 2026-03-25 | | Design 참조 | docs/02-design/features/bid-monitoring-pipeline.design.md (v1.0) | | Match Rate | **95%** (BUG-1 수정 후 97%) |
- | ID | Type | Severity | 설명 | 조치 | |----|------|----------|------|------| | BUG-1 | Bug | **HIGH** | `scheduled_monitor.py:170` — `b["bid_no"]` dict 접근을 BidScore dataclass에 사용. RuntimeError 발생 | 즉시 수정: `b.bid_no` / `b.score` | | ADD-2 | Added | MEDIUM | `POST /bids/pipeline/trigger` 엔드포인트 — 설계에 없으나…
- | 항목 | 내용 | |------|------| | 분석일 | 2026-03-25 | | Design 참조 | docs/02-design/features/bid-monitoring-pipeline.design.md (v1.0) | | Match Rate | **95%** (BUG-1 수정 후 97%) |
