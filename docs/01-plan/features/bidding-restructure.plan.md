# Bidding 모듈 리스트럭처링 계획

> 날짜: 2026-03-24
> 유형: 리팩토링 (기능 변경 없음)
> 위험도: MEDIUM (import 경로 변경 → 전체 영향)

## 1. 배경 및 목적

Bidding 관련 파일 26개가 `app/services/` 루트에 flat하게 산재.
`pricing/` 패키지만 유일하게 정리됨. 나머지 10개 `bid_*.py`가 다른 서비스(auth, kb, notification 등)와 섞여 가독성·탐색성 저하.

**목표**: Bidding 도메인 파일을 `app/services/bidding/` 하위 패키지로 응집, import 호환성 유지.

## 2. 현황 분석

### 2.1 대상 파일 (서비스 레이어)

| 파일 | 줄수 | 관심사 | import 참조 수 |
|------|------|--------|:------------:|
| `bid_calculator.py` | 190 | 노임단가 계산 (레거시 하드코딩) | 10 |
| `bid_recommender.py` | 424 | AI 입찰 추천 | 2 |
| `bid_scorer.py` | 391 | 공고 적합도 스코어링 | 3 |
| `bid_fetcher.py` | 454 | G2B 공고 수집 + upsert | 2 |
| `bid_preprocessor.py` | 101 | 공고문 전처리 | 2 |
| `bid_cleanup.py` | 124 | 마감 공고 자동 정리 | 1 |
| `bid_handoff.py` | 221 | 투찰 핸드오프 (확정가 저장) | 4 |
| `bid_market_research.py` | 272 | 유사과제 낙찰정보 조사 | 1 |
| `bidding_stream.py` | 173 | Stream 2 비딩 워크스페이스 | 2 |
| `cost_sheet_builder.py` | 369 | 산출내역서 DOCX 빌더 | 2 |
| `pricing/` (9파일) | ~800 | 가격 시뮬레이션 엔진 | 24 (내부 포함) |
| **합계** | **~3,519** | | **53** |

### 2.2 API·그래프·프롬프트·모델

| 파일 | 줄수 | 관심사 |
|------|------|--------|
| `routes_bids.py` | 1,471 | 공고 모니터링 + AI 추천 (비대) |
| `routes_bid_submission.py` | 158 | 투찰 관리 |
| `routes_pricing.py` | 286 | 가격 시뮬레이션 API |
| `graph/nodes/bid_plan.py` | 167 | LangGraph STEP 2.5 |
| `prompts/bid_review.py` | 160 | 입찰가격 리뷰 프롬프트 |
| `models/bid_schemas.py` | 215 | 입찰 스키마 |

### 2.3 제외 대상

| 파일 | 사유 |
|------|------|
| `token_pricing.py` | AI 토큰 비용 — bidding 무관 |
| `routes_v31.py` | 레거시 v3.1 API — 별도 정리 대상 |
| `phase_executor.py` | 레거시 v3.1 파이프라인 — 별도 정리 대상 |

## 3. 목표 구조

```
app/services/bidding/               ← 새 패키지
├── __init__.py                     ── re-export (호환성)
│
├── calculator.py                   (← bid_calculator.py)
│
├── monitor/                        ── 공고 모니터링 ──
│   ├── __init__.py
│   ├── fetcher.py                  (← bid_fetcher.py)
│   ├── scorer.py                   (← bid_scorer.py)
│   ├── preprocessor.py             (← bid_preprocessor.py)
│   ├── cleanup.py                  (← bid_cleanup.py)
│   └── recommender.py              (← bid_recommender.py)
│
├── pricing/                        ── 가격 시뮬레이션 ── (기존 이동)
│   ├── __init__.py
│   ├── engine.py
│   ├── models.py
│   ├── cost_estimator.py
│   ├── cost_standard_selector.py
│   ├── competitor_pricing.py
│   ├── win_probability.py
│   ├── sensitivity.py
│   ├── client_preference.py
│   └── price_score.py
│
├── submission/                     ── 투찰·핸드오프 ──
│   ├── __init__.py
│   ├── handoff.py                  (← bid_handoff.py)
│   ├── stream.py                   (← bidding_stream.py)
│   └── market_research.py          (← bid_market_research.py)
│
└── artifacts/                      ── 산출물 ──
    ├── __init__.py
    └── cost_sheet_builder.py       (← cost_sheet_builder.py)
```

## 4. 마이그레이션 전략

### 4.1 호환성 레이어 (단계적 전환)

**기존 import 경로를 즉시 깨뜨리지 않기 위해** 원래 위치에 re-export 파일을 남깁니다.

```python
# app/services/bid_calculator.py (호환 래퍼)
"""레거시 호환 — 실제 구현은 app.services.bidding.calculator"""
from app.services.bidding.calculator import *  # noqa: F401,F403
```

이렇게 하면:
- 기존 `from app.services.bid_calculator import X` → 계속 작동
- 새 코드는 `from app.services.bidding.calculator import X` 사용
- 향후 래퍼 파일을 제거하면 완전 전환 완료

### 4.2 pricing/ 이동

`app/services/pricing/` → `app/services/bidding/pricing/`

마찬가지로 `app/services/pricing/__init__.py`에 re-export 래퍼 유지.

### 4.3 Import 변경 영향 범위

| 참조 위치 | 파일 수 | 전략 |
|-----------|:-------:|------|
| `app/graph/nodes/` | 5 | 호환 래퍼로 즉시 작동, 점진 교체 |
| `app/api/routes_*.py` | 4 | 호환 래퍼로 즉시 작동, 점진 교체 |
| `app/services/pricing/` 내부 | 8 | bidding/pricing 이동 시 내부 import 일괄 변경 |
| `app/services/` 기타 | 3 | 호환 래퍼로 즉시 작동 |
| `tests/` | 다수 | 호환 래퍼로 즉시 작동 |
| 레거시 (`routes_v31`, `phase_executor`) | 2 | 호환 래퍼로 즉시 작동 (정리 대상) |

## 5. 구현 순서

| 단계 | 작업 | 위험 | 검증 |
|:----:|------|------|------|
| 1 | `app/services/bidding/` 패키지 생성 + `__init__.py` | LOW | import 테스트 |
| 2 | monitor/ 서브패키지 생성 + 5파일 이동 | LOW | 기존 테스트 통과 |
| 3 | submission/ 서브패키지 생성 + 3파일 이동 | LOW | 기존 테스트 통과 |
| 4 | artifacts/ 서브패키지 생성 + 1파일 이동 | LOW | 기존 테스트 통과 |
| 5 | calculator.py 이동 | MEDIUM | 참조 10곳 — 호환 래퍼 필수 |
| 6 | pricing/ 이동 → bidding/pricing/ | MEDIUM | 참조 24곳 — 호환 래퍼 필수 |
| 7 | 원래 위치에 re-export 래퍼 생성 | LOW | 전체 테스트 통과 |
| 8 | 전체 테스트 (482+ tests) | — | 0 실패 확인 |

## 6. 성공 기준

- [ ] 전체 테스트 482+ 통과 (0 실패)
- [ ] 기존 import 경로 100% 호환 (래퍼 경유)
- [ ] bidding 관련 파일이 `app/services/bidding/` 한 곳에 응집
- [ ] `pricing/` 내부 import이 `bidding/pricing/` 경로로 정상 작동
- [ ] TypeScript 프론트엔드 빌드 0 에러 (백엔드만 변경이므로 영향 없음)

## 7. 리스크 및 대응

| 리스크 | 확률 | 영향 | 대응 |
|--------|:----:|:----:|------|
| 순환 import | 중 | 중 | 지연 import 유지 (현재도 사용 중) |
| 래퍼 파일 누락 | 저 | 고 | grep으로 모든 import 참조 검증 |
| pricing 내부 상대 import 깨짐 | 중 | 중 | 이동 후 즉시 내부 import 일괄 교체 |
| 테스트 mock 경로 불일치 | 중 | 저 | 호환 래퍼가 해결 |

## 8. 범위 외

- `routes_bids.py` 1,471줄 분리 → 별도 리팩토링 과제
- `bid_calculator.py` 레거시 코드 정리 (하드코딩 → DB 조회) → 별도 기능 개선 과제
- `routes_v31.py` / `phase_executor.py` 레거시 제거 → 별도 정리 과제
- API·그래프·프롬프트·모델 파일 이동 → 현재 범위 외 (서비스 레이어만)
