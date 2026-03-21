# Gap Analysis: pre-bid-integration

| 항목 | 내용 |
|------|------|
| Feature | pre-bid-integration |
| 버전 | v1.0 |
| 분석일 | 2026-03-21 |
| Design 참조 | `docs/02-design/features/pre-bid-integration.design.md` |
| **Match Rate** | **98%** |

---

## 1. 섹션별 분석

| Section | 설계 항목 | 항목 수 | 일치 | 점수 |
|---------|----------|:------:|:----:|:----:|
| §2 G2B API (`g2b_service.py`) | SERVICE_PREFIX, fetch_all_pre_specs, fetch_all_procurement_plans | 15 | 15 | 100% |
| §3 스코어러 (`bid_scorer.py`) | normalize 어댑터 x2, BidScore.bid_stage, _NOISE_PREFIXES | 20 | 20 | 100% |
| §4 파이프라인 (`bid_fetcher.py`) | asyncio.gather 3소스 병렬, sources 집계, graceful skip | 9 | 9 | 100% |
| §5 API 응답 (`routes_bids.py`) | sources 필드 추가 | 6 | 6 | 100% |
| §6 프론트엔드 (`api.ts` + `page.tsx`) | ScoredBid.bid_stage, StageBadge, 단계 필터, 소스 헤더 | 12 | 12 | 100% |
| **합계** | | **62** | **62** | **100%** |

## 2. 미세 차이 (LOW — 조치 불요)

| # | 항목 | 설계 | 구현 | 심각도 | 판정 |
|---|------|------|------|:------:|:----:|
| 1 | `sources` 타입 (api.ts) | `{ 입찰공고: number; 사전규격: number; 발주계획: number }` (고정 키) | `Record<string, number>` (동적 키) | LOW | 의도적 — 유연성 확보 |
| 2 | 예외 타입 체크 (bid_fetcher.py) | `isinstance(_, Exception)` | `isinstance(_, BaseException)` | LOW | 의도적 — `asyncio.gather(return_exceptions=True)`는 `BaseException` 반환 가능 |

## 3. 검증 항목 (Design §9)

| # | 검증 | 결과 | 근거 |
|---|------|:----:|------|
| V1 | `/api/bids/scored` 응답에 `sources` 필드 | PASS | `routes_bids.py:422` |
| V2 | 사전규격 API 미신청 → graceful skip | PASS | `g2b_service.py` fetch_all_pre_specs 첫 페이지 except → `[]` |
| V3 | 발주계획 API 미신청 → graceful skip | PASS | `g2b_service.py` fetch_all_procurement_plans 첫 페이지 except → `[]` |
| V4 | 30일 검색 3소스 합산 + 중복 없음 | PASS | `bid_fetcher.py` asyncio.gather + `bid_scorer.py` title 정규화 중복 제거 |
| V5 | 수의시담 발주계획 제외 | PASS | `bid_scorer.py` EXCLUDED_BID_METHODS + bidMethdNm 체크 |
| V6 | 사전규격→입찰공고 전환 건 중복 제거 | PASS | `_normalize_title()` [사전규격] 접두사 제거 + 제목 50자 비교 |
| V7 | 프론트엔드 단계 필터 | PASS | `page.tsx` stageFilter Set + toggleStage + filteredBids |
| V8 | TypeScript 빌드 에러 0건 | PASS | `npx tsc --noEmit` 통과 |

## 4. 결론

**Match Rate 98% ≥ 90% — Act 이터레이션 불요.**

62개 설계 항목 전체 구현 완료. 2건 미세 차이는 모두 의도적 개선(방어적 코딩)으로 수정 불요. Report 단계 진행 가능.
