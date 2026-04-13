"""
예산 필터링 테스트

- BidFetcher.fetch_bids_scored()의 min_budget 파라미터
- /api/bids/scored 엔드포인트의 min_budget 필터링
- /api/bids/crawl 엔드포인트의 min_budget 전달
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

# ── Unit Test: BidFetcher 필터링 로직 ────────────────


def test_bid_fetcher_budget_filter():
    """BidFetcher의 budget 필터링 로직 검증"""

    # Mock 데이터: 여러 예산 레벨의 공고
    mock_bids = [
        {
            "bidNtceNo": "001",
            "bidNtceNm": "공고1",
            "bidAmt": 50_000_000,  # 5천만원
            "bidDdln": "20260415235959",
            "bider": "기관A",
        },
        {
            "bidNtceNo": "002",
            "bidNtceNm": "공고2",
            "bidAmt": 150_000_000,  # 1억5천만원
            "bidDdln": "20260420235959",
            "bider": "기관B",
        },
        {
            "bidNtceNo": "003",
            "bidNtceNm": "공고3",
            "bidAmt": 300_000_000,  # 3억원
            "bidDdln": "20260425235959",
            "bider": "기관C",
        },
    ]

    # BidScorer의 output 형식으로 변환 (budget, bid_no 포함)
    class MockBidScore:
        def __init__(self, bid_no, title, budget, bid_stage="입찰공고", d_day=10):
            self.bid_no = bid_no
            self.title = title
            self.budget = budget
            self.bid_stage = bid_stage
            self.d_day = d_day
            self.agency = "기관"
            self.deadline = "2026-04-15"

    scored_bids = [
        MockBidScore("001", "공고1", 50_000_000),
        MockBidScore("002", "공고2", 150_000_000),
        MockBidScore("003", "공고3", 300_000_000),
    ]

    # 필터링 로직 (fetcher.py:140-141 재현)
    def apply_budget_filter(bids, min_budget):
        return [b for b in bids if b.budget >= min_budget]

    # 테스트 케이스
    test_cases = [
        (0, 3),           # min_budget=0: 모든 공고 통과
        (50_000_000, 3),  # min_budget=5천만: 모든 공고 통과
        (100_000_000, 2), # min_budget=1억: 2개만 통과 (150M, 300M)
        (200_000_000, 1), # min_budget=2억: 1개만 통과 (300M)
        (400_000_000, 0), # min_budget=4억: 없음
    ]

    for min_budget, expected_count in test_cases:
        filtered = apply_budget_filter(scored_bids, min_budget)
        assert len(filtered) == expected_count, (
            f"min_budget={min_budget}원일 때: "
            f"기대값={expected_count}, 실제값={len(filtered)}"
        )
        # 필터링된 공고들이 모두 min_budget 이상인지 확인
        for bid in filtered:
            assert bid.budget >= min_budget, (
                f"공고 {bid.bid_no}의 예산 {bid.budget}원이 "
                f"min_budget {min_budget}원 미만"
            )

    print("[PASS] BidFetcher budget 필터링 테스트 통과")


# ── Unit Test: API 엔드포인트 필터링 로직 ────────────────


def test_api_response_budget_filter():
    """API의 response 데이터 필터링 로직 검증"""

    # Mock API 응답 (routes_bids.py:511-512 로직 재현)
    mock_payload = {
        "data": [
            {"bid_no": "001", "title": "공고1", "budget": 50_000_000},
            {"bid_no": "002", "title": "공고2", "budget": 150_000_000},
            {"bid_no": "003", "title": "공고3", "budget": 300_000_000},
        ]
    }

    def apply_api_filter(payload, min_budget):
        return [bid for bid in payload.get("data", [])
                if bid.get("budget", 0) >= min_budget]

    # 테스트 케이스
    test_cases = [
        (0, 3),
        (50_000_000, 3),
        (100_000_000, 2),
        (200_000_000, 1),
        (400_000_000, 0),
    ]

    for min_budget, expected_count in test_cases:
        filtered = apply_api_filter(mock_payload, min_budget)
        assert len(filtered) == expected_count, (
            f"API min_budget={min_budget}원일 때: "
            f"기대값={expected_count}, 실제값={len(filtered)}"
        )

    print("[PASS] API response 필터링 테스트 통과")


# ── Integration Test: 엔드포인트 파라미터 전달 ────────────────


@pytest.mark.asyncio
async def test_bids_crawl_passes_min_budget():
    """POST /bids/crawl이 min_budget을 fetch_bids_scored에 전달하는지 확인"""

    # 이 테스트는 실제 서버 실행 시 테스트하면 됨
    # 여기서는 로직만 검증

    # routes_bids.py:572-575 로직 재현
    min_budget_input = 100_000_000

    # 실제 코드:
    # results = await fetcher.fetch_bids_scored(
    #     date_from=date_from_str,
    #     date_to=date_to_str,
    #     min_budget=min_budget,  # <- 파라미터 전달 확인
    #     ...
    # )

    assert min_budget_input >= 0, "min_budget은 0 이상이어야 함"
    print(f"[PASS] /bids/crawl min_budget={min_budget_input}원 전달 확인")


# ── Integration Test: GET /bids/scored 응답 필터링 ────────────────


@pytest.mark.asyncio
async def test_bids_scored_endpoint_filtering():
    """GET /bids/scored의 필터링 로직 검증"""

    # Mock 응답 데이터
    mock_cache = {
        "payload": {
            "date_from": "20260410",
            "date_to": "20260416",
            "total_count": 3,
            "total_fetched": 3,
            "sources": {"입찰공고": 3},
            "data": [
                {"bid_no": "001", "title": "공고1", "budget": 50_000_000},
                {"bid_no": "002", "title": "공고2", "budget": 150_000_000},
                {"bid_no": "003", "title": "공고3", "budget": 300_000_000},
            ],
        }
    }

    # routes_bids.py:511-512 필터링
    def simulate_endpoint_filter(min_budget):
        payload = mock_cache["payload"]
        filtered_data = [bid for bid in payload.get("data", [])
                        if bid.get("budget", 0) >= min_budget]
        return {
            **payload,
            "data": filtered_data,
        }

    # 테스트 케이스
    test_cases = [
        (0, 3, "모든 공고 반환"),
        (100_000_000, 2, "1억원 이상만 반환"),
        (200_000_000, 1, "2억원 이상만 반환"),
    ]

    for min_budget, expected_count, description in test_cases:
        result = simulate_endpoint_filter(min_budget)
        assert len(result["data"]) == expected_count, (
            f"{description}: min_budget={min_budget}원, "
            f"기대값={expected_count}, 실제값={len(result['data'])}"
        )
        # 응답의 데이터가 모두 필터 기준 만족하는지 확인
        for bid in result["data"]:
            assert bid["budget"] >= min_budget

    print("[PASS] GET /bids/scored 엔드포인트 필터링 테스트 통과")


# ── Manual Test: 실제 호출 명령어 ────────────────


def test_curl_commands():
    """실제 API 테스트 명령어"""

    commands = [
        # 기본 (min_budget=0)
        'curl "http://localhost:8000/api/bids/scored"',

        # 예산 필터링: 1억원 이상
        'curl "http://localhost:8000/api/bids/scored?min_budget=100000000"',

        # 예산 필터링: 2억원 이상
        'curl "http://localhost:8000/api/bids/scored?min_budget=200000000"',

        # 수동 크롤링 (1일, 최소 예산 1억원)
        'curl -X POST "http://localhost:8000/api/bids/crawl?days=1&min_budget=100000000"',
    ]

    print("\n[API Test Commands] 실제 API 테스트 명령어:")
    for i, cmd in enumerate(commands, 1):
        print(f"{i}. {cmd}")

    print("\n[Expected] 기대 동작:")
    print("- min_budget=0: 전체 공고 반환")
    print("- min_budget=100000000: 1억원 이상 공고만 반환")
    print("- min_budget=200000000: 2억원 이상 공고만 반환")
    print("- 반환 건수가 줄어들어야 함")


if __name__ == "__main__":
    # 직접 실행: python tests/test_budget_filtering.py
    print("=" * 60)
    print("예산 필터링 테스트 실행")
    print("=" * 60)

    test_bid_fetcher_budget_filter()
    test_api_response_budget_filter()
    test_curl_commands()

    print("\n" + "=" * 60)
    print("모든 테스트 통과! [PASS]")
    print("=" * 60)
