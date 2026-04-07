# Gap Analysis: routes_bids.py 코드 품질 개선

- **Date**: 2026-03-26
- **Feature**: api (routes_bids.py code quality refactoring)
- **Match Rate**: 100% (12/12 + 신규 2건 즉시 해소)

## 분석 대상

| 파일 | 변경 전 | 변경 후 |
|------|---------|---------|
| `app/api/routes_bids.py` | 1,651줄 | 1,618줄 (-33줄) |
| `app/models/bid_schemas.py` | 222줄 | 234줄 (+12줄) |

## 이슈별 검증 결과

| # | 이슈 ID | 심각도 | 내용 | 상태 |
|---|---------|:------:|------|:----:|
| 1 | CRIT-1 | CRITICAL | `get_monitored_bids` 320줄 → 4개 헬퍼 분해 | FIXED |
| 2 | CRIT-2 | CRITICAL | Raw AsyncAnthropic → `_get_claude_client()` + `settings.claude_model` | FIXED |
| 3 | CRIT-3 | CRITICAL | ilike 메타문자 미이스케이프 → `_escape_like()` 3곳 적용 | FIXED |
| 4 | CRIT-4 | CRITICAL | 인라인 `_BidStatusBody` → `BidStatusUpdate` + `Literal` 타입 | FIXED |
| 5 | CRIT-5 | CRITICAL | 경로 순회 공격 → `_BID_NO_PATTERN` 검증 6개 엔드포인트 | FIXED |
| 6 | CRIT-6 | CRITICAL | `client` NameError → try 블록 밖 할당 | FIXED |
| 7 | WARN-1 | WARNING | 인라인 import 12건 → 모듈 최상단 이동 | FIXED |
| 8 | WARN-2 | WARNING | my 스코프 N+1 쿼리 → `or_()` 단일 쿼리 | FIXED |
| 9 | WARN-3 | WARNING | content 추출 중복 → `_extract_content_from_raw()` | FIXED |
| 10 | WARN-5 | WARNING | `pipeline_status` 인증 미적용 → `get_current_user_or_none` 추가 | FIXED |
| 11 | WARN-6 | WARNING | 프리셋 활성화 비원자적 → 순서 역전 + `neq` 필터 | FIXED |
| 12 | HIGH-3 | HIGH | `analyze_bid_for_proposal` 253줄 → 4개 헬퍼 분해 | FIXED |

## 신규 발견 → 즉시 해소

| # | 내용 | 상태 |
|---|------|:----:|
| N-1 | `manual_crawl` 내 `BidFetcher` 중복 import | 삭제 완료 |
| N-2 | `_extract_text_from_attachments` 미사용 함수 (40줄) | 삭제 완료 |

## 리팩토링 구조 요약

### 엔드포인트 → 헬퍼 매핑

```
get_monitored_bids (40줄)
  ├── _monitor_my()
  ├── _monitor_team_or_division()
  ├── _monitor_company()
  └── _enrich_monitor_data()

analyze_bid_for_proposal (42줄)
  ├── _check_analysis_cache()
  ├── _load_bid_content()
  │   └── _extract_content_from_raw()  (공유)
  ├── _load_teams_info()
  └── _run_unified_analysis()

get_bid_detail
  └── _extract_content_from_raw()  (공유)
```

### 보안 개선

- `_escape_like()`: PostgREST ilike 메타문자 이스케이프
- `_BID_NO_PATTERN`: 모든 `{bid_no}` 엔드포인트에 경로 순회 방지
- `_get_claude_client()`: 재시도 로직 포함 싱글톤 클라이언트

## 검증

- **ruff check**: 0 에러
- **import 검증**: `import app.api.routes_bids` 성공
- **순환 import**: 없음
