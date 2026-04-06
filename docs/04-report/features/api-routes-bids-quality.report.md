# PDCA Completion Report: routes_bids.py 코드 품질 개선

## 개요

| 항목 | 값 |
|------|-----|
| Feature | api (routes_bids.py code quality) |
| PDCA 사이클 | Do → Check → Report (Plan/Design 생략) |
| 시작일 | 2026-03-25 |
| 완료일 | 2026-03-26 |
| Match Rate | **100%** (12/12) |
| 변경 파일 | 2개 (routes_bids.py, bid_schemas.py) |
| 순 코드 변경 | -33줄 (1,651 → 1,618) |

## 배경

`routes_bids.py`는 입찰 추천 API 전체를 담당하는 1,651줄 파일로, 코드 리뷰에서 CRITICAL 6건 + WARNING 8건 + SUGGESTION 5건의 이슈가 식별되었다. 보안 취약점(경로 순회, LIKE injection)과 유지보수성 문제(320줄 함수, 인라인 모델, N+1 쿼리)가 주요 개선 대상이었다.

## 수정 내역

### CRITICAL (6건 → 6건 해결)

| # | 이슈 | 수정 |
|---|------|------|
| CRIT-1 | `get_monitored_bids` 320줄 단일 함수 | 4개 헬퍼로 분해: `_monitor_my`, `_monitor_team_or_division`, `_monitor_company`, `_enrich_monitor_data`. 엔드포인트 40줄 |
| CRIT-2 | `AsyncAnthropic` 직접 생성 + 하드코딩 모델 + 이중 타임아웃 | `_get_claude_client()` 싱글톤 + `settings.claude_model` + 단일 `asyncio.wait_for(timeout=45)` |
| CRIT-3 | `ilike` LIKE 메타문자(%, _, \\) 미이스케이프 | `_escape_like()` 헬퍼 추가, 3곳 적용 |
| CRIT-4 | 인라인 `_BidStatusBody(status: str)` | `bid_schemas.py`에 `BidStatusUpdate` + `BidProposalStatus` Literal 타입. Pydantic 자체 422 검증 |
| CRIT-5 | `update_bid_status` 경로 순회 공격 가능 | `_BID_NO_PATTERN` 검증을 `update_bid_status`, `analyze_bid_for_proposal`, `toggle_bookmark` 3곳 추가 (총 6개 엔드포인트 보호) |
| CRIT-6 | `get_bid_detail`에서 `client` 미할당 NameError | `client = await get_async_client()`를 try 블록 밖으로 이동 + G2B fallback 내 중복 할당 제거 |

### WARNING (6건 → 6건 해결)

| # | 이슈 | 수정 |
|---|------|------|
| WARN-1 | 인라인 import 12건 | `json`, `Path`, `asyncio`, `bid_pipeline`, `bid_scorer`, `bid_attachment_store`, `rfp_parser`, `bid_review`, `claude_client` 모듈 최상단 이동 |
| WARN-2 | `my` 스코프 키워드별 5회 개별 DB 쿼리 | PostgREST `or_()` 필터로 1회 쿼리 변환 |
| WARN-3 | `content_text` 추출 로직 2곳 중복 | `_extract_content_from_raw()` 공유 헬퍼로 통합 |
| WARN-5 | `pipeline_status` 인증 미적용 | `get_current_user_or_none` 의존성 추가 |
| WARN-6 | `activate_search_preset` 비원자적 갱신 | 순서 역전 (활성화 우선) + `.neq("id", preset_id)` 필터로 0개 활성 상태 방지 |
| HIGH-3 | `analyze_bid_for_proposal` 253줄 단일 함수 | 4개 헬퍼: `_check_analysis_cache`, `_load_bid_content`, `_load_teams_info`, `_run_unified_analysis`. 엔드포인트 42줄 |

### 신규 발견 → 즉시 해소 (2건)

| # | 내용 |
|---|------|
| N-1 | `manual_crawl` 내 `BidFetcher` 중복 import 삭제 |
| N-2 | `_extract_text_from_attachments` 미사용 함수 40줄 삭제 + `parse_rfp_from_url` 미사용 import 제거 |

## 리팩토링 구조

```
routes_bids.py (1,618줄)
├── 모듈 import (54줄) — 정리 완료
├── 상수 + 헬퍼 (_escape_like, _BID_NO_PATTERN)
├── 엔드포인트 15개 — 각 20~50줄 이내
├── 모니터 스코프 헬퍼 (4개)
│   ├── _monitor_my()
│   ├── _monitor_team_or_division()
│   ├── _monitor_company()
│   └── _enrich_monitor_data()
├── 분석 헬퍼 (5개)
│   ├── _extract_content_from_raw() — 공유
│   ├── _check_analysis_cache()
│   ├── _load_bid_content()
│   ├── _load_teams_info()
│   └── _run_unified_analysis()
└── 내부 헬퍼 (기존 유지)
    ├── _invalidate_recommendations_cache()
    ├── _get_preset_or_404()
    ├── _get_active_preset_or_422()
    ├── _get_profile_or_422()
    ├── _get_cached_recommendations()
    ├── _build_recommendations_response()
    ├── _run_fetch_and_analyze()
    └── _save_recommendations()
```

## 검증 결과

| 검증 항목 | 결과 |
|-----------|------|
| ruff check | 0 에러 |
| import 검증 | 성공 (`import app.api.routes_bids` OK) |
| 순환 import | 없음 |
| Gap Analysis | 12/12 = 100% |

## 미수정 잔여 (SUGGESTION 급, 향후 검토)

| ID | 내용 | 우선순위 |
|----|------|:--------:|
| SUGA-1 | `_BID_NO_PATTERN` → FastAPI `Path(pattern=...)` 어노테이션으로 통합 | LOW |
| SUGA-2 | 파일 기반 캐시(`data/bid_status/`, `data/bid_analyses/`) DB 전환 후 제거 | LOW |
| SUGA-3 | `_enrich_monitor_data` 내 3회 루프 → 단일 루프 또는 Response 모델 | LOW |
| SUGA-4 | `_run_fetch_and_analyze` 오류 핸들러 내 중복 client 생성 | LOW |
| SUGA-5 | `per_page` 기본값 비일관 (20 vs 30) | LOW |
| WARN-4 | 광범위한 `except Exception` → 구체적 예외 타입 | LOW |
| WARN-8 | `type("R", (), {"data": []})()` 익명 객체 → 명시적 처리 | LOW |

## 교훈

1. **보안 검증은 일관되게** — `_BID_NO_PATTERN` 같은 입력 검증은 하나의 엔드포인트에만 적용하면 다른 곳에서 공격 벡터가 생긴다. FastAPI `Annotated[str, Path(pattern=...)]`로 타입 레벨에서 강제하면 누락 방지 가능.
2. **인라인 import는 기술 부채** — 순환 import 회피가 아니라면 모듈 최상단에 두는 것이 정적 분석 도구 호환성과 가독성 모두에 유리.
3. **함수 분해 시 파라미터 전달 최소화** — `_json` 같은 모듈 참조를 파라미터로 넘기는 것은 인라인 import의 부산물. 최상단 import 정리 후 자연스럽게 해소.
