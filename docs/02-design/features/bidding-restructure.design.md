# Bidding 모듈 리스트럭처링 설계

> 날짜: 2026-03-24
> Plan 참조: `docs/01-plan/features/bidding-restructure.plan.md`

## 1. 파일 이동 매핑

### 1.1 전체 매핑 테이블

| # | 원본 경로 | 이동 경로 | 서브패키지 |
|---|----------|----------|-----------|
| 1 | `services/bid_calculator.py` | `services/bidding/calculator.py` | (루트) |
| 2 | `services/bid_fetcher.py` | `services/bidding/monitor/fetcher.py` | monitor |
| 3 | `services/bid_scorer.py` | `services/bidding/monitor/scorer.py` | monitor |
| 4 | `services/bid_preprocessor.py` | `services/bidding/monitor/preprocessor.py` | monitor |
| 5 | `services/bid_cleanup.py` | `services/bidding/monitor/cleanup.py` | monitor |
| 6 | `services/bid_recommender.py` | `services/bidding/monitor/recommender.py` | monitor |
| 7 | `services/bid_handoff.py` | `services/bidding/submission/handoff.py` | submission |
| 8 | `services/bidding_stream.py` | `services/bidding/submission/stream.py` | submission |
| 9 | `services/bid_market_research.py` | `services/bidding/submission/market_research.py` | submission |
| 10 | `services/cost_sheet_builder.py` | `services/bidding/artifacts/cost_sheet_builder.py` | artifacts |
| 11 | `services/pricing/` (9파일) | `services/bidding/pricing/` (9파일) | pricing |

### 1.2 이동하지 않는 파일

| 파일 | 사유 |
|------|------|
| `api/routes_bids.py` | API 레이어 — 서비스만 이동 |
| `api/routes_bid_submission.py` | API 레이어 |
| `api/routes_pricing.py` | API 레이어 |
| `graph/nodes/bid_plan.py` | 그래프 노드 — 구조 유지 |
| `prompts/bid_review.py` | 프롬프트 — 구조 유지 |
| `models/bid_schemas.py` | 모델 — 구조 유지 |
| `services/token_pricing.py` | bidding 무관 |

## 2. 디렉토리 구조 상세

```
app/services/bidding/
├── __init__.py                      § 2.1
├── calculator.py                    § 2.2  (190줄)
│
├── monitor/                         § 2.3
│   ├── __init__.py
│   ├── fetcher.py                   (454줄) BidFetcher 클래스
│   ├── scorer.py                    (391줄) BidScore, score_bid, score_and_rank_bids
│   ├── preprocessor.py              (101줄) BidPreprocessor 클래스
│   ├── cleanup.py                   (124줄) cleanup_expired_bids()
│   └── recommender.py               (424줄) BidRecommender 클래스
│
├── pricing/                         § 2.4  (기존 services/pricing/ 그대로)
│   ├── __init__.py                  PricingEngine, 모델 re-export
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
├── submission/                      § 2.5
│   ├── __init__.py
│   ├── handoff.py                   (221줄) persist_bid_confirmation, record_bid_submission 등
│   ├── stream.py                    (173줄) get_bidding_workspace, update_bid_price_post_workflow
│   └── market_research.py           (272줄) ensure_market_data
│
└── artifacts/                       § 2.6
    ├── __init__.py
    └── cost_sheet_builder.py        (369줄) build_cost_sheet
```

## 3. `__init__.py` Re-export 정의

### 3.1 `app/services/bidding/__init__.py`

```python
"""Bidding 도메인 통합 패키지.

서브패키지:
- monitor: 공고 수집·분석·추천
- pricing: 가격 시뮬레이션 엔진
- submission: 투찰·핸드오프
- artifacts: 산출내역서 빌더
"""
```

### 3.2 `app/services/bidding/monitor/__init__.py`

```python
from app.services.bidding.monitor.fetcher import BidFetcher
from app.services.bidding.monitor.scorer import BidScore, score_bid, score_and_rank_bids
from app.services.bidding.monitor.preprocessor import BidPreprocessor
from app.services.bidding.monitor.cleanup import cleanup_expired_bids
from app.services.bidding.monitor.recommender import BidRecommender
```

### 3.3 `app/services/bidding/submission/__init__.py`

```python
from app.services.bidding.submission.handoff import (
    persist_bid_confirmation,
    record_bid_submission,
    verify_bid_submission,
    get_bid_price_history,
    get_bid_submission_status,
)
from app.services.bidding.submission.stream import (
    get_bidding_workspace,
    update_bid_price_post_workflow,
    get_market_tracking_summary,
)
from app.services.bidding.submission.market_research import ensure_market_data
```

### 3.4 `app/services/bidding/artifacts/__init__.py`

```python
from app.services.bidding.artifacts.cost_sheet_builder import build_cost_sheet
```

### 3.5 `app/services/bidding/pricing/__init__.py`

기존 `app/services/pricing/__init__.py`와 동일 (내부 import 경로만 변경).

## 4. 호환 래퍼 상세

원래 위치에 남기는 래퍼 파일. 기존 import을 깨뜨리지 않으면서 점진적 마이그레이션 가능.

### 4.1 래퍼 파일 목록 (11개)

| 원본 경로 (래퍼로 변환) | 내용 |
|------------------------|------|
| `services/bid_calculator.py` | `from app.services.bidding.calculator import *` |
| `services/bid_fetcher.py` | `from app.services.bidding.monitor.fetcher import *` |
| `services/bid_scorer.py` | `from app.services.bidding.monitor.scorer import *` |
| `services/bid_preprocessor.py` | `from app.services.bidding.monitor.preprocessor import *` |
| `services/bid_cleanup.py` | `from app.services.bidding.monitor.cleanup import *` |
| `services/bid_recommender.py` | `from app.services.bidding.monitor.recommender import *` |
| `services/bid_handoff.py` | `from app.services.bidding.submission.handoff import *` |
| `services/bidding_stream.py` | `from app.services.bidding.submission.stream import *` |
| `services/bid_market_research.py` | `from app.services.bidding.submission.market_research import *` |
| `services/cost_sheet_builder.py` | `from app.services.bidding.artifacts.cost_sheet_builder import *` |
| `services/pricing/__init__.py` | `from app.services.bidding.pricing import *` (+ 개별 서브모듈 래퍼) |

### 4.2 래퍼 파일 형식

```python
"""레거시 호환 래퍼 — 실제 구현: app.services.bidding.{subpackage}.{module}

이 파일은 기존 import 경로 호환을 위해 유지됩니다.
새 코드에서는 app.services.bidding.{subpackage} 경로를 사용하세요.
"""
from app.services.bidding.{subpackage}.{module} import *  # noqa: F401,F403
```

### 4.3 pricing/ 서브모듈 래퍼

`pricing/` 디렉토리는 통째로 이동하되, 원래 위치의 각 모듈에도 래퍼 필요.
기존 `from app.services.pricing.models import PersonnelInput` 같은 import이 작동해야 함.

```
services/pricing/           ← 래퍼 디렉토리로 변환
├── __init__.py             from app.services.bidding.pricing import *
├── engine.py               from app.services.bidding.pricing.engine import *
├── models.py               from app.services.bidding.pricing.models import *
├── cost_estimator.py       from app.services.bidding.pricing.cost_estimator import *
├── ... (각 파일별 래퍼)
```

## 5. 내부 import 변경

이동된 파일 내부에서 서로를 참조하는 import 수정.

### 5.1 pricing/ 내부 (8건)

| 파일 | 기존 import | 변경 후 |
|------|------------|---------|
| `engine.py` | `from app.services.bid_calculator import _fmt` | `from app.services.bidding.calculator import _fmt` |
| `engine.py` | `from app.services.pricing.{x} import` | `from app.services.bidding.pricing.{x} import` |
| `cost_estimator.py` | `from app.services.bid_calculator import ...` | `from app.services.bidding.calculator import ...` |
| `cost_estimator.py` | `from app.services.pricing.models import ...` | `from app.services.bidding.pricing.models import ...` |
| `win_probability.py` | `from app.services.bid_calculator import ...` | `from app.services.bidding.calculator import ...` |
| 기타 pricing 내부 | `from app.services.pricing.{x}` | `from app.services.bidding.pricing.{x}` |

### 5.2 monitor/ 내부 (2건)

| 파일 | 기존 import | 변경 후 |
|------|------------|---------|
| `fetcher.py` | `from app.services.bid_scorer import ...` | `from app.services.bidding.monitor.scorer import ...` |
| `recommender.py` | `from app.services.bid_preprocessor import BidPreprocessor` | `from app.services.bidding.monitor.preprocessor import BidPreprocessor` |

### 5.3 submission/ 내부 (1건)

| 파일 | 기존 import | 변경 후 |
|------|------------|---------|
| `stream.py` | `from app.services.bid_handoff import ...` | `from app.services.bidding.submission.handoff import ...` |

## 6. 구현 절차 (8단계)

| 단계 | 작업 | 파일 수 | 검증 |
|:----:|------|:------:|------|
| 1 | `bidding/` + 4 서브패키지 디렉토리 + `__init__.py` 생성 | 5 | import 가능 확인 |
| 2 | monitor/ 5파일 복사 + 내부 import 수정 | 5 | `pytest tests/` 일부 |
| 3 | submission/ 3파일 복사 + 내부 import 수정 | 3 | `pytest tests/` 일부 |
| 4 | artifacts/ 1파일 복사 | 1 | — |
| 5 | calculator.py 복사 | 1 | — |
| 6 | pricing/ 9파일 복사 + 내부 import 일괄 수정 | 9 | `pytest tests/` 일부 |
| 7 | 원본 11파일 → 호환 래퍼로 교체 + pricing/ 래퍼 | 20 | **전체 테스트** |
| 8 | `__pycache__` 정리 + 최종 검증 | — | **전체 482+ 테스트** |

## 7. 성공 기준

- [ ] `app/services/bidding/` 디렉토리에 20개 파일 존재
- [ ] 기존 53개 import 참조 전부 호환 래퍼 경유로 작동
- [ ] pricing/ 내부 import이 `bidding/pricing/` 경로로 작동
- [ ] 전체 테스트 482+ 통과 (0 실패)
- [ ] 새 경로 `from app.services.bidding.monitor import BidFetcher` 작동 확인
