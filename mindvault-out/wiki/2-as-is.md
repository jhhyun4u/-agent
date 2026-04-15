# 2. 현재 상태 (AS-IS)
Cohesion: 1.00 | Nodes: 1

## Key Nodes
- **2. 현재 상태 (AS-IS)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bid-monitoring-pipeline.plan.md) -- 0 connections

## Internal Relationships

## Cross-Community Connections

## Context
이 커뮤니티는 2. 현재 상태 (AS-IS)를 중심으로 related 관계로 연결되어 있다. 주요 소스 파일은 bid-monitoring-pipeline.plan.md이다.

### Key Facts
- ``` [G2B API] ──→ [scored/monitor 목록] ──→ [화면 표시] │ 사용자 클릭 │ ▼ [실시간] GET /bids/{id} │ DB 조회 (불안정) │ G2B fallback ▼ [실시간] GET /bids/{id}/analysis │ DB 조회 → 첨부파일 다운로드 │ → 텍스트 추출 → Claude x2 │ → 캐시 저장 ▼ [30초+ 후] 화면 표시 ```
