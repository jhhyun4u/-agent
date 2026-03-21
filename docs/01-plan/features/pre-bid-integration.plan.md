# 사전규격 + 발주계획 통합 Plan

| 항목 | 내용 |
|------|------|
| Feature | pre-bid-integration |
| 버전 | v1.0 |
| 작성일 | 2026-03-21 |
| 상태 | Plan |

## 1. 배경 및 목적

현재 AI 추천(`/api/bids/scored`) 경로는 **입찰공고(getBidPblancListInfoServc)만** 수집한다. 나라장터 공고 생명주기는 `발주계획 → 사전규격 → 입찰공고` 순서로 진행되므로, 발주계획과 사전규격을 함께 수집하면 **2~4주 더 앞서** 기회를 포착할 수 있다.

```
[발주계획] ──(4~8주전)──→ [사전규격] ──(2~3주전)──→ [입찰공고] ──→ [마감]
     ↑ 현재 미수집            ↑ 프리셋 전용             ↑ AI 추천 수집 중
```

## 2. 현황 분석

### 수집 경로별 소스 현황

| 소스 | AI 추천 (scored) | 정기 모니터링 | 프리셋 수집 |
|------|:---:|:---:|:---:|
| 입찰공고 (`BidPublicInfoService`) | O | O | O |
| 사전규격 (`BfSpecRgstInfoService`) | **X** | X | O |
| 발주계획 (`OrderPlanSttusService`) | **X** | X | X |

### 기존 코드 자산

- `g2b_service.py` — `search_pre_bid_specifications()` 메서드 이미 존재 (사전규격)
- `bid_fetcher.py` — `fetch_pre_bids_by_preset()` + `_normalize_pre_spec()` 이미 존재
- `bid_scorer.py` — 역할 키워드 + 분류 가중치 스코어링 (입찰공고 필드 기반)
- 발주계획 API 코드는 **없음** — 신규 구현 필요

## 3. 변경 범위

### 3-1. G2B API 추가: 발주계획 (`OrderPlanSttusService`)
**파일**: `app/services/g2b_service.py`

- `SERVICE_PREFIX`에 `"OrderPlanSttusService": "ao"` 추가
- `search_procurement_plans()` 메서드 신규
  - 엔드포인트: `OrderPlanSttusService/getOrderPlanSttusListThng` (용역)
  - 파라미터: `numOfRows`, `pageNo`, `inqryBgnDt`, `inqryEndDt`, `type=json`
  - 에러 처리: API 미활용 신청 시 500 → graceful skip (사전규격 패턴 동일)
- `fetch_all_procurement_plans()` 전수 수집 메서드 (페이지네이션)

### 3-2. 사전규격 전수 수집 메서드
**파일**: `app/services/g2b_service.py`

- `fetch_all_pre_specs()` 메서드 신규 — `search_pre_bid_specifications()` 기반 페이지네이션 수집
- 기존 `search_pre_bid_specifications()`는 키워드 필터링 포함 → 전수 수집 시 키워드 없이 호출

### 3-3. 스코어링 파이프라인 통합
**파일**: `app/services/bid_fetcher.py`

- `fetch_bids_scored()` 수정:
  1. `g2b.fetch_all_bids()` — 입찰공고 (기존)
  2. `g2b.fetch_all_pre_specs()` — 사전규격 (**추가**)
  3. `g2b.fetch_all_procurement_plans()` — 발주계획 (**추가**)
  4. 3개 소스 합산 → `score_and_rank_bids()` 스코어링
- 각 소스의 raw 필드명이 다르므로 **정규화 레이어** 필요

### 3-4. 스코어러 정규화 어댑터
**파일**: `app/services/bid_scorer.py`

- `score_bid()` 현재 입찰공고 필드(`bidNtceNm`, `bidNtceNo` 등)만 참조
- 사전규격/발주계획의 필드를 입찰공고 형식으로 정규화하는 어댑터 함수 추가:
  - `normalize_pre_spec_for_scoring(raw) -> dict` — `bfSpecRgstNm` → `bidNtceNm` 등
  - `normalize_plan_for_scoring(raw) -> dict` — 발주계획 필드 → `bidNtceNm` 등
- `bid_stage` 필드 주입: `"입찰공고"` / `"사전규격"` / `"발주계획"`

### 3-5. API 응답 확장
**파일**: `app/api/routes_bids.py`

- 응답에 `sources` 필드 추가: `{"입찰공고": N, "사전규격": M, "발주계획": K}`
- 각 bid 항목에 `bid_stage` 필드 포함

### 3-6. 프론트엔드 표시
**파일**: `frontend/app/bids/page.tsx`

- `ScoredBidsView` 결과 헤더에 소스별 건수 표시
- 테이블에 `단계` 컬럼 추가 (발주계획/사전규격/입찰공고 뱃지)
- 단계별 필터 체크박스 (선택적 표시/숨김)

**파일**: `frontend/lib/api.ts`

- `ScoredBid` 인터페이스에 `bid_stage` 필드 추가
- 응답 타입에 `sources` 필드 추가

## 4. 기술 고려사항

### G2B API 제약

| 항목 | 입찰공고 | 사전규격 | 발주계획 |
|------|---------|---------|---------|
| 활용 신청 | 완료 | 필요 (미신청 시 500) | 필요 (미신청 시 500) |
| 날짜 범위 | 제한 없음(페이지네이션) | ~30일 | 분기별 |
| 페이지당 건수 | 999 | 999 | 확인 필요 |
| Rate Limit | 0.1초 | 0.1초 | 0.1초 |

### 성능

- 3개 API를 순차 호출하면 30일 기준 수집 시간이 3배 증가
- **병렬 수집** (`asyncio.gather`)으로 완화 — rate limit은 API별 독립
- 각 소스별 graceful skip: 하나가 실패해도 나머지 소스로 결과 반환

### 중복 제거

- 사전규격 → 입찰공고로 전환된 건은 제목 유사도 기반 중복 제거로 처리
- `bid_no` 체계가 다르므로 (`PRE-` prefix, `PLN-` prefix) bid_no 중복은 없음
- `_normalize_title()` 기존 함수가 `[사전규격]`, `[발주계획]` 접두사도 제거하도록 확장

## 5. 수정 대상 파일

| 파일 | 변경 유형 | 내용 |
|------|----------|------|
| `app/services/g2b_service.py` | 수정+추가 | SERVICE_PREFIX, `search_procurement_plans()`, `fetch_all_pre_specs()`, `fetch_all_procurement_plans()` |
| `app/services/bid_scorer.py` | 수정 | 정규화 어댑터 2개, `_normalize_title()` 접두사 확장 |
| `app/services/bid_fetcher.py` | 수정 | `fetch_bids_scored()` 3소스 병렬 수집 + 합산 |
| `app/api/routes_bids.py` | 수정 | 응답에 `sources`, `bid_stage` 필드 |
| `frontend/app/bids/page.tsx` | 수정 | 단계 뱃지, 소스별 건수, 단계 필터 |
| `frontend/lib/api.ts` | 수정 | `ScoredBid.bid_stage`, 응답 `sources` 타입 |

## 6. 구현 순서

1. **G2B API 추가** — `g2b_service.py`에 발주계획 + 사전규격 전수 수집 메서드
2. **스코어러 정규화** — `bid_scorer.py`에 어댑터 함수 + 접두사 제거 확장
3. **파이프라인 통합** — `bid_fetcher.py`에서 3소스 병렬 수집 + 합산
4. **API 응답 확장** — `routes_bids.py` 응답 필드 추가
5. **프론트엔드** — 단계 뱃지 + 소스 건수 + 필터

## 7. 검증 계획

1. `GET /api/bids/scored?days=7` → `sources` 필드에 3개 소스 건수 표시
2. 사전규격 API 미신청 시 → 입찰공고만으로 정상 동작 (graceful skip)
3. 발주계획 API 미신청 시 → 입찰공고+사전규격만으로 정상 동작
4. 30일 검색 → 3소스 합산 결과, 중복 없음
5. 프론트엔드 → 단계별 뱃지 + 필터 동작
6. TypeScript 빌드 에러 0건

## 8. 리스크

| 리스크 | 대응 |
|--------|------|
| 발주계획 API 응답 필드명 불확실 | API 호출 후 raw 로깅 → 필드 확인 후 어댑터 조정 |
| API 활용 신청 미완료 | graceful skip으로 입찰공고만 반환 (기능 저하 허용) |
| 3소스 병렬 수집 시 rate limit 위반 | API별 독립 rate limit이므로 문제 없음. 동일 API 내 순차 유지 |
| 사전규격↔입찰공고 중복 | `_normalize_title()` 기반 제목 유사도 제거로 처리 |
