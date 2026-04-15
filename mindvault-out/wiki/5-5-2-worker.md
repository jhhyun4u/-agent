# 5. 기술 설계 방향 & 5-2. 파이프라인 Worker
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **5. 기술 설계 방향** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bid-monitoring-pipeline.plan.md) -- 4 connections
  - -> contains -> [[5-1]]
  - -> contains -> [[5-2-worker]]
  - -> contains -> [[5-3]]
  - -> contains -> [[5-4]]
- **5-2. 파이프라인 Worker** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bid-monitoring-pipeline.plan.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[5]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bid-monitoring-pipeline.plan.md) -- 1 connections
  - <- has_code_example <- [[5-2-worker]]
- **5-1. 트리거 시점** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bid-monitoring-pipeline.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **5-3. 첨부파일 저장 전략** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bid-monitoring-pipeline.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **5-4. 파일 구조** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\bid-monitoring-pipeline.plan.md) -- 1 connections
  - <- contains <- [[5]]

## Internal Relationships
- 5. 기술 설계 방향 -> contains -> 5-1. 트리거 시점 [EXTRACTED]
- 5. 기술 설계 방향 -> contains -> 5-2. 파이프라인 Worker [EXTRACTED]
- 5. 기술 설계 방향 -> contains -> 5-3. 첨부파일 저장 전략 [EXTRACTED]
- 5. 기술 설계 방향 -> contains -> 5-4. 파일 구조 [EXTRACTED]
- 5-2. 파이프라인 Worker -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 5. 기술 설계 방향, 5-2. 파이프라인 Worker, python를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 bid-monitoring-pipeline.plan.md이다.

### Key Facts
- ```python async def run_bid_pipeline(bid_nos: list[str]): """백그라운드 파이프라인 — scored/monitor 결과 후처리""" for bid_no in bid_nos: try: # Step 1: DB 확인/저장 (G2B fallback) await ensure_bid_in_db(bid_no)
- ```python async def run_bid_pipeline(bid_nos: list[str]): """백그라운드 파이프라인 — scored/monitor 결과 후처리""" for bid_no in bid_nos: try: # Step 1: DB 확인/저장 (G2B fallback) await ensure_bid_in_db(bid_no)
- | 트리거 | 설명 | |--------|------| | **scored API 호출 후** | `/bids/scored` 응답 반환 후 백그라운드 태스크 시작 | | **스케줄 모니터링 후** | `scheduled_monitor.py` 08:00/15:00 실행 후 | | **수동** | 관리자가 `/api/bids/pipeline/trigger` 호출 |
- | 항목 | 방식 | |------|------| | 저장소 | Supabase Storage `bid-attachments` 버킷 | | 경로 | `{bid_no}/{파일명}` | | 우선순위 | 제안요청서 > 과업지시서 > 공고문 (최대 3파일) | | 텍스트 | 추출 후 `bid_announcements.content_text`에 저장 | | 보존기간 | 90일 (마감일 기준 자동 삭제) |
- ``` app/services/ bid_pipeline.py          ← NEW: 파이프라인 오케스트레이터 bid_attachment_store.py   ← NEW: 첨부파일 다운로드/저장 app/api/ routes_bids.py           ← 수정: scored 후 파이프라인 트리거 ```
