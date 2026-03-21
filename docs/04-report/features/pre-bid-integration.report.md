# PDCA Completion Report: pre-bid-integration

| 항목 | 내용 |
|------|------|
| Feature | pre-bid-integration |
| 완료일 | 2026-03-21 |
| PDCA 사이클 | Plan → Design → Do → Check → Report (단일 세션) |
| Match Rate | **98%** |
| Act 이터레이션 | 0회 (98% ≥ 90%) |

---

## 1. 목적

AI 추천(`/api/bids/scored`) 경로에 **사전규격**과 **발주계획** 수집을 통합하여, 입찰공고 게시 전 2~4주 앞서 기회를 포착할 수 있도록 개선.

```
[발주계획] ──(4~8주전)──→ [사전규격] ──(2~3주전)──→ [입찰공고] ──→ [마감]
     ↑ 신규 추가              ↑ scored 통합              ↑ 기존
```

## 2. 변경 파일 및 내용

| # | 파일 | 변경 | 추가 라인 |
|---|------|------|----------|
| 1 | `app/services/g2b_service.py` | SERVICE_PREFIX `OrderPlanSttusService: "ao"` + `fetch_all_pre_specs()` + `fetch_all_procurement_plans()` | +90 |
| 2 | `app/services/bid_scorer.py` | `normalize_pre_spec_for_scoring()`, `normalize_plan_for_scoring()` 어댑터 + `BidScore.bid_stage` + `_NOISE_PREFIXES` 확장 + 수의시담 제외 | +55 |
| 3 | `app/services/bid_fetcher.py` | `asyncio.gather` 3소스 병렬 수집 + `sources` 집계 + graceful skip | +50 (수정) |
| 4 | `app/api/routes_bids.py` | 응답에 `sources` 필드 + `days` 최대 30 + `total_fetched` | +5 |
| 5 | `frontend/lib/api.ts` | `ScoredBid.bid_stage` + 응답 `sources` + `total_fetched` 타입 | +4 |
| 6 | `frontend/app/bids/page.tsx` | `StageBadge` 컴포넌트 + 단계 필터 체크박스 + 소스별 건수 헤더 + 기간 옵션 7개 | +65 |
| **합계** | **6파일** | | **~270줄** |

## 3. 핵심 설계 결정

| 결정 | 근거 |
|------|------|
| **정규화 어댑터 패턴** | 사전규격/발주계획 필드를 입찰공고 형식으로 변환 → `score_bid()` 수정 없이 재활용 |
| **`asyncio.gather` + `return_exceptions=True`** | 3소스 병렬 수집, 개별 API 실패 시 나머지만으로 결과 반환 |
| **`_bid_stage` 마커 필드** | 정규화 dict에 소스 구분 태그 삽입 → BidScore까지 전파 → 프론트 뱃지 |
| **수의시담 제외** | `bidMethdNm`에 "수의" 포함 시 스코어링 전 제거 (발주계획에도 적용) |
| **제목 정규화 중복 제거** | `[사전규격]`, `[발주계획]` 접두사 제거 → 동일 건 사전규격↔입찰공고 중복 방지 |

## 4. Gap Analysis 결과

- **62개 설계 항목** 전체 구현 완료
- **미세 차이 2건** (LOW, 의도적 개선):
  1. `sources` 타입: 고정 키 → `Record<string, number>` (유연성)
  2. 예외 체크: `Exception` → `BaseException` (asyncio 호환)
- **검증 8개 항목** 전체 PASS (V1~V8)

## 5. 세션 내 추가 변경 (pre-bid-integration 외)

본 세션에서 Plan 수립 전에 아래 기능도 함께 구현:

| 변경 | 파일 |
|------|------|
| 기간 옵션 확장 (1/3/5/7/10/14/30일) + 결과 헤더 개선 | `bids/page.tsx`, `api.ts` |
| `total_fetched` 반환 추가 | `bid_fetcher.py`, `routes_bids.py` |
| `max_pages` 기본값 20→40 | `g2b_service.py` |
| `days` 최대값 14→30 | `routes_bids.py` |
| 수의시담 제외 (`EXCLUDED_BID_METHODS`) | `bid_scorer.py` |

## 6. 잔여 사항

| 항목 | 상태 | 비고 |
|------|------|------|
| 발주계획 API 활용 신청 | 미완료 | data.go.kr에서 `OrderPlanSttusService` 신청 필요. 미신청 시 graceful skip |
| 사전규격 API 활용 신청 | 미확인 | 기존 코드에 graceful skip 있음. 활용 신청 여부 확인 필요 |
| 발주계획 응답 필드 검증 | 미완료 | API 실제 호출 후 `orderPlanNo`, `orderPlanNm` 등 필드명 확인·조정 필요 |
| 정기 모니터링 통합 | 미반영 | `daily_g2b_monitor()`는 입찰공고만 수집. 향후 3소스 통합 검토 |

## 7. PDCA 문서

| Phase | 문서 |
|-------|------|
| Plan | `docs/01-plan/features/pre-bid-integration.plan.md` |
| Design | `docs/02-design/features/pre-bid-integration.design.md` |
| Analysis | `docs/03-analysis/features/pre-bid-integration.analysis.md` |
| Report | `docs/04-report/features/pre-bid-integration.report.md` |
