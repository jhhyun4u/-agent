"""
예산 필터링 통합 테스트

실제 API 엔드포인트 호출 전에 필터링 로직 검증
"""

import asyncio
from pathlib import Path

# ── 파일 캐시 상태 확인 ────────────────


def check_cache_status():
    """파일 캐시 상태 확인"""

    cache_file = Path("app/services/bidding/monitor/.bid_cache.json")

    if cache_file.exists():
        import json
        with open(cache_file, "r", encoding="utf-8") as f:
            cache = json.load(f)

        payload = cache.get("payload", {})
        bids = payload.get("data", [])

        print(f"\n[CACHE] 파일 캐시 상태: 존재함")
        print(f"  - 전체 공고 수: {len(bids)}건")

        if bids:
            budgets = [b.get("budget", 0) for b in bids]
            print(f"  - 예산 범위: {min(budgets):,}원 ~ {max(budgets):,}원")

            # 예산별 통계
            ranges = [
                (0, 100_000_000, "1억 미만"),
                (100_000_000, 200_000_000, "1억~2억"),
                (200_000_000, 500_000_000, "2억~5억"),
                (500_000_000, float('inf'), "5억 이상"),
            ]

            print("\n[Budget Stats] 예산별 공고 수:")
            for low, high, label in ranges:
                count = sum(1 for b in budgets if low <= b < high)
                if count > 0:
                    print(f"  - {label}: {count}건")
        else:
            print("  - 캐시에 공고 데이터 없음")
    else:
        print(f"\n[CACHE] 파일 캐시 상태: 없음")
        print(f"  경로: {cache_file}")
        print("  -> /api/bids/crawl 또는 새로고침으로 데이터 수집 필요")


# ── 필터링 시뮬레이션 ────────────────


def simulate_budget_filtering():
    """파일 캐시 데이터로 필터링 시뮬레이션"""

    cache_file = Path("app/services/bidding/monitor/.bid_cache.json")

    if not cache_file.exists():
        print("\n[ERROR] 파일 캐시 없음. 먼저 /api/bids/crawl로 데이터 수집하세요.")
        return

    import json
    with open(cache_file, "r", encoding="utf-8") as f:
        cache = json.load(f)

    payload = cache.get("payload", {})
    bids = payload.get("data", [])

    print(f"\n[Simulation] 필터링 시뮬레이션")
    print(f"원본 공고 수: {len(bids)}건\n")

    # 테스트할 min_budget 값들
    test_budgets = [
        0,
        50_000_000,
        100_000_000,
        150_000_000,
        200_000_000,
        300_000_000,
    ]

    for min_budget in test_budgets:
        filtered = [b for b in bids if b.get("budget", 0) >= min_budget]
        reduction = len(bids) - len(filtered)

        print(f"min_budget={min_budget:>10,}원: {len(filtered):>3}건 "
              f"(제외: {reduction}건, {reduction/len(bids)*100:.1f}%)")


# ── API 테스트 문서 생성 ────────────────


def generate_test_plan():
    """API 테스트 계획 출력"""

    print("\n" + "="*70)
    print("[TEST PLAN] 예산 필터링 통합 테스트")
    print("="*70)

    print("\n1. 캐시 데이터 확인:")
    check_cache_status()

    print("\n2. 필터링 시뮬레이션:")
    simulate_budget_filtering()

    print("\n" + "="*70)
    print("[Manual Testing] 실제 API 테스트")
    print("="*70)

    commands = [
        ("1. 기본 (모든 공고)", "curl -s 'http://localhost:8000/api/bids/scored' | jq '.data | length'"),
        ("2. 1억원 필터링", "curl -s 'http://localhost:8000/api/bids/scored?min_budget=100000000' | jq '.data | length'"),
        ("3. 2억원 필터링", "curl -s 'http://localhost:8000/api/bids/scored?min_budget=200000000' | jq '.data | length'"),
        ("4. 수동 크롤링 + 필터", "curl -X POST 'http://localhost:8000/api/bids/crawl?min_budget=100000000'"),
    ]

    for desc, cmd in commands:
        print(f"\n{desc}:")
        print(f"  Command: {cmd}")

    print("\n" + "="*70)
    print("[Expected Results]")
    print("="*70)
    print("- 각 필터 값마다 반환 건수가 감소")
    print("- min_budget이 높을수록 건수 감소")
    print("- 모든 반환 공고는 budget >= min_budget 만족")
    print("- 로그에 필터링 통계 출력: 'min_budget=XXX원 필터링: N건 → M건'")

    print("\n" + "="*70)


if __name__ == "__main__":
    generate_test_plan()
