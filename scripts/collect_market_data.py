"""
G2B 낙찰정보 일괄 수집 스크립트

market_price_data 테이블에 도메인별 낙찰 실적을 적재한다.
통계 모델(KDE 기반 수주확률)의 기반 데이터로 사용.

Usage:
    uv run python scripts/collect_market_data.py \
        --domain "SI/SW개발" --keyword "소프트웨어" \
        --from-year 2024 --to-year 2026
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


async def collect(domain: str, keyword: str, from_year: int, to_year: int, max_pages: int):
    from app.services.g2b_service import G2BService, fetch_and_store_bid_result

    total_found = 0
    total_stored = 0
    total_failed = 0

    async with G2BService() as svc:
        for year in range(from_year, to_year + 1):
            logger.info(f"=== {year}년 '{keyword}' 검색 시작 ===")

            # 연도별 검색 (1월~12월)
            from_date = f"{year}0101"
            to_date = f"{year}1231"

            try:
                results = await svc.search_bid_announcements(
                    keyword=keyword,
                    from_date=from_date,
                    to_date=to_date,
                    num_of_rows=100 * max_pages,
                )
            except Exception as e:
                logger.warning(f"{year}년 검색 실패: {e}")
                continue

            bid_ids = []
            for r in results:
                bid_no = r.get("bidNtceNo", r.get("bfSpecRgstNo", ""))
                if bid_no:
                    bid_ids.append(bid_no)

            bid_ids = list(set(bid_ids))
            total_found += len(bid_ids)
            logger.info(f"  {year}년 공고 {len(bid_ids)}건 발견")

            for i, bid_id in enumerate(bid_ids, 1):
                try:
                    result = await fetch_and_store_bid_result(bid_id, domain=domain)
                    status = result.get("status", "unknown")
                    if status == "stored":
                        total_stored += 1
                        if i % 10 == 0:
                            logger.info(f"  [{i}/{len(bid_ids)}] 적재 완료 — 낙찰률: {result.get('bid_ratio', '-')}")
                    else:
                        total_failed += 1
                except Exception as e:
                    total_failed += 1
                    if i <= 3:
                        logger.warning(f"  [{i}] {bid_id} 실패: {e}")

    logger.info("=" * 50)
    logger.info(f"수집 완료!")
    logger.info(f"  발견: {total_found}건")
    logger.info(f"  적재: {total_stored}건")
    logger.info(f"  실패: {total_failed}건")
    logger.info("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="G2B 낙찰정보 일괄 수집")
    parser.add_argument("--domain", default="SI/SW개발", help="도메인 (기본: SI/SW개발)")
    parser.add_argument("--keyword", default="소프트웨어", help="검색 키워드")
    parser.add_argument("--from-year", type=int, default=2024, help="시작 연도")
    parser.add_argument("--to-year", type=int, default=2026, help="종료 연도")
    parser.add_argument("--max-pages", type=int, default=5, help="최대 페이지 수")
    args = parser.parse_args()

    asyncio.run(collect(args.domain, args.keyword, args.from_year, args.to_year, args.max_pages))


if __name__ == "__main__":
    main()
