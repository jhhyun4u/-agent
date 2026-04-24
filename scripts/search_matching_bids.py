"""
테크노베이션파트너스 역량 기반 맞춤형 G2B 공고 검색

data/company_profile.json을 로드하여 G2B 공고를 검색하고
키워드 매칭으로 적합도 스코어를 계산한다.

v2: 키워드별 개별 검색 (999건 1회 → 키워드 25개 × 100건)으로 누락 최소화.

사용법:
    uv run python scripts/search_matching_bids.py                    # 기본 검색
    uv run python scripts/search_matching_bids.py --min-score 70     # 70점 이상만
    uv run python scripts/search_matching_bids.py --min-budget 50000 # 5천만원 이상
    uv run python scripts/search_matching_bids.py --days 21          # 최근 21일
    uv run python scripts/search_matching_bids.py --show-excluded    # 마감임박 포함 출력
"""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.domains.bidding.g2b_service import G2BService
from scripts.bid_scoring import (
    MIN_DAYS_BEFORE_DEADLINE,
    SERVICE_TYPES,
    build_client_to_dept,
    format_budget,
    format_d_day,
    load_profile,
    score_bid,
    search_by_keywords,
)

# 키워드별 검색 시 상위 N개 키워드 사용
MAX_KEYWORDS = 25


async def search_and_score(
    profile: dict,
    min_score: int = 50,
    min_budget: int = 0,
    date_range_days: int = 14,
) -> list[dict]:
    """키워드별 개별 검색 → 용역 필터 → 스코어링 → 정렬."""
    keywords = profile["search_keywords"][:MAX_KEYWORDS]
    date_from = (datetime.now() - timedelta(days=date_range_days)).strftime("%Y%m%d") + "0000"

    async with G2BService() as svc:
        print(f"G2B 공고 검색 중 (최근 {date_range_days}일, 키워드 {len(keywords)}개 × 100건)...")
        all_bids = await search_by_keywords(svc, keywords, num_per_kw=100, date_from=date_from)
        print(f"  → {len(all_bids)}건 조회됨 (중복 제거 후)")

    # 용역 유형 필터 (물품/공사 제외)
    service_bids = [
        b for b in all_bids.values()
        if b.get("srvceDivNm", "") in SERVICE_TYPES
    ]
    if len(service_bids) < len(all_bids):
        excluded_count = len(all_bids) - len(service_bids)
        print(f"  → 용역 필터 후 {len(service_bids)}건 (물품/공사 {excluded_count}건 제외)")

    client_dept_map = build_client_to_dept(profile)

    scored = []
    for bid in service_bids:
        result = score_bid(bid, profile, client_dept_map)
        if result["score"] >= min_score and result["budget"] >= min_budget:
            scored.append(result)

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def print_results(scored: list[dict], show_excluded: bool = False):
    """결과 출력."""
    now = datetime.now().strftime("%Y-%m-%d")
    print(f"\n━━━ 테크노베이션파트너스 맞춤 공고 검색 ({now}) ━━━\n")

    active = [s for s in scored if not s["excluded"]]
    excluded = [s for s in scored if s["excluded"]]

    if not active and not excluded:
        print("  매칭되는 공고가 없습니다.")
        return

    for s in active:
        d_str = format_d_day(s["d_days"])
        print(f"[{s['score']}점] {s['title']}")
        print(f"   발주: {s['client']}  예산: {format_budget(s['budget'])}  마감: {d_str}")

        detail = s["score_detail"]
        parts = []
        if s["matched_keywords"]:
            parts.append(f"키워드({','.join(s['matched_keywords'][:4])})")
        if detail["client"] > 0:
            parts.append(f"{'기존고객' if detail['client'] >= 20 else '유사고객'}({detail['client']:.0f}점)")
        if s["matched_dept"]:
            parts.append(f"부처경험:{s['matched_dept']}({detail['department']:.0f}점)")
        if parts:
            print(f"   매칭: {' + '.join(parts)}")
        print()

    if excluded:
        print(f"─── 마감 D-{MIN_DAYS_BEFORE_DEADLINE} 미만 제외 ({len(excluded)}건) ───\n")
        show_count = len(excluded) if show_excluded else min(5, len(excluded))
        for s in excluded[:show_count]:
            d_str = format_d_day(s["d_days"])
            kw_str = f"  [{','.join(s['matched_keywords'][:3])}]" if s["matched_keywords"] else ""
            print(f"  [{s['score']}점] {s['title']}  ({d_str}){kw_str}")
        if not show_excluded and len(excluded) > 5:
            print(f"  ... 외 {len(excluded) - 5}건 (--show-excluded 로 전체 보기)")

    print(f"\n총 {len(active)}건 추천 / {len(excluded)}건 마감임박 제외")


def main():
    parser = argparse.ArgumentParser(description="테크노베이션파트너스 맞춤 G2B 공고 검색")
    parser.add_argument("--min-score", type=int, default=50, help="최소 적합도 (기본: 50)")
    parser.add_argument("--min-budget", type=int, default=0, help="최소 예산 (천원 단위, 기본: 0)")
    parser.add_argument("--days", type=int, default=14, help="검색 기간 일수 (기본: 14)")
    parser.add_argument("--show-excluded", action="store_true", help="마감임박 제외 공고 전체 표시")
    args = parser.parse_args()

    from scripts.bid_scoring import PROFILE_PATH
    if not PROFILE_PATH.exists():
        print(f"[ERROR] 역량 프로필 없음: {PROFILE_PATH}")
        print("먼저 import_project_history.py를 실행하세요.")
        sys.exit(1)

    profile = load_profile()
    print(f"역량 프로필 로드: {profile['company']['stats']['total_projects']}건 실적, "
          f"{len(profile['search_keywords'])}개 키워드")

    scored = asyncio.run(search_and_score(
        profile,
        min_score=args.min_score,
        min_budget=args.min_budget * 1000,
        date_range_days=args.days,
    ))

    print_results(scored, show_excluded=args.show_excluded)


if __name__ == "__main__":
    main()
