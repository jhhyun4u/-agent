# PDCA Completion Report: routes_bids.py 코드 품질 개선 & 신규 발견 → 즉시 해소 (2건)
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **PDCA Completion Report: routes_bids.py 코드 품질 개선** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-routes-bids-quality.report.md) -- 4 connections
  - -> contains -> [[critical-6-6]]
  - -> contains -> [[warning-6-6]]
  - -> contains -> [[2]]
  - -> contains -> [[suggestion]]
- **신규 발견 → 즉시 해소 (2건)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-routes-bids-quality.report.md) -- 1 connections
  - <- contains <- [[pdca-completion-report-routesbidspy]]
- **CRITICAL (6건 → 6건 해결)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-routes-bids-quality.report.md) -- 1 connections
  - <- contains <- [[pdca-completion-report-routesbidspy]]
- **미수정 잔여 (SUGGESTION 급, 향후 검토)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-routes-bids-quality.report.md) -- 1 connections
  - <- contains <- [[pdca-completion-report-routesbidspy]]
- **WARNING (6건 → 6건 해결)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\api-routes-bids-quality.report.md) -- 1 connections
  - <- contains <- [[pdca-completion-report-routesbidspy]]

## Internal Relationships
- PDCA Completion Report: routes_bids.py 코드 품질 개선 -> contains -> CRITICAL (6건 → 6건 해결) [EXTRACTED]
- PDCA Completion Report: routes_bids.py 코드 품질 개선 -> contains -> WARNING (6건 → 6건 해결) [EXTRACTED]
- PDCA Completion Report: routes_bids.py 코드 품질 개선 -> contains -> 신규 발견 → 즉시 해소 (2건) [EXTRACTED]
- PDCA Completion Report: routes_bids.py 코드 품질 개선 -> contains -> 미수정 잔여 (SUGGESTION 급, 향후 검토) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 PDCA Completion Report: routes_bids.py 코드 품질 개선, 신규 발견 → 즉시 해소 (2건), CRITICAL (6건 → 6건 해결)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 api-routes-bids-quality.report.md이다.

### Key Facts
- | # | 내용 | |---|------| | N-1 | `manual_crawl` 내 `BidFetcher` 중복 import 삭제 | | N-2 | `_extract_text_from_attachments` 미사용 함수 40줄 삭제 + `parse_rfp_from_url` 미사용 import 제거 |
- | # | 이슈 | 수정 | |---|------|------| | CRIT-1 | `get_monitored_bids` 320줄 단일 함수 | 4개 헬퍼로 분해: `_monitor_my`, `_monitor_team_or_division`, `_monitor_company`, `_enrich_monitor_data`. 엔드포인트 40줄 | | CRIT-2 | `AsyncAnthropic` 직접 생성 + 하드코딩 모델 + 이중 타임아웃 | `_get_claude_client()` 싱글톤 +…
- | ID | 내용 | 우선순위 | |----|------|:--------:| | SUGA-1 | `_BID_NO_PATTERN` → FastAPI `Path(pattern=...)` 어노테이션으로 통합 | LOW | | SUGA-2 | 파일 기반 캐시(`data/bid_status/`, `data/bid_analyses/`) DB 전환 후 제거 | LOW | | SUGA-3 | `_enrich_monitor_data` 내 3회 루프 → 단일 루프 또는 Response 모델 | LOW | | SUGA-4 |…
- | # | 이슈 | 수정 | |---|------|------| | WARN-1 | 인라인 import 12건 | `json`, `Path`, `asyncio`, `bid_pipeline`, `bid_scorer`, `bid_attachment_store`, `rfp_parser`, `bid_review`, `claude_client` 모듈 최상단 이동 | | WARN-2 | `my` 스코프 키워드별 5회 개별 DB 쿼리 | PostgREST `or_()` 필터로 1회 쿼리 변환 | | WARN-3 | `content_text`…
