"""
나라장터 G2B API 실제 호출 테스트

서비스별 경로:
  - 입찰공고: /ad/BidPublicInfoService
  - 낙찰정보: /as/ScsbidInfoService

필수 파라미터: inqryDiv(1), inqryBgnDt(YYYYMMDDHHMM), inqryEndDt(YYYYMMDDHHMM)

실행: uv run python -X utf8 scripts/test_g2b.py
"""

import asyncio
import sys
from datetime import datetime, timedelta

sys.path.insert(0, ".")


async def test_bid_search():
    """1단계: 입찰공고 검색 테스트."""
    print("=" * 60)
    print("[1] 입찰공고 검색 (G2BService.search_bid_announcements)")
    print("=" * 60)

    from app.services.g2b_service import G2BService

    async with G2BService() as svc:
        results = await svc.search_bid_announcements("시스템", num_of_rows=100)
        print(f"  결과: {len(results)}건\n")
        for i, r in enumerate(results[:5]):
            title = r.get("bidNtceNm", "N/A")
            bid_no = r.get("bidNtceNo", "")
            agency = r.get("ntceInsttNm", r.get("dminsttNm", ""))
            budget = r.get("presmptPrce", r.get("asignBdgtAmt", ""))
            deadline = r.get("bidClseDt", "")
            print(f"  [{i+1}] {title[:55]}")
            print(f"      공고번호: {bid_no}  기관: {agency}")
            print(f"      예산: {budget}  마감: {deadline}")
            print()
        return results


async def test_bid_results():
    """2단계: 낙찰결과 조회 테스트."""
    print("=" * 60)
    print("[2] 낙찰결과 조회 (G2BService.get_bid_results)")
    print("=" * 60)

    from app.services.g2b_service import G2BService

    async with G2BService() as svc:
        results = await svc.get_bid_results("정보", num_of_rows=5, date_range_days=7)
        print(f"  결과: {len(results)}건\n")
        for i, r in enumerate(results[:5]):
            title = r.get("bidNtceNm", "N/A")
            winner = r.get("bidwinnrNm", "")
            bid_no = r.get("bidNtceNo", "")
            count = r.get("prtcptCnum", "")
            print(f"  [{i+1}] {title[:50]}")
            print(f"      낙찰업체: {winner}  참여: {count}개사  공고번호: {bid_no}")
            print()
        return results


async def test_standalone_wrapper():
    """3단계: search_bids 래퍼 테스트."""
    print("=" * 60)
    print("[3] search_bids 래퍼 (LangGraph 노드용)")
    print("=" * 60)

    from app.services.g2b_service import search_bids

    bids = await search_bids("용역")
    print(f"  결과: {len(bids)}건\n")
    for i, b in enumerate(bids[:3]):
        print(f"  [{i+1}] {b.get('project_name', 'N/A')[:55]}")
        print(f"      공고번호: {b.get('bid_no')}  발주처: {b.get('client')}")
        print(f"      예산: {b.get('budget')}  마감: {b.get('deadline')}")
        print()
    return bids


async def test_bid_detail(bid_no: str):
    """4단계: 공고 상세 조회 테스트."""
    print("=" * 60)
    print(f"[4] 공고 상세 조회: {bid_no}")
    print("=" * 60)

    from app.services.g2b_service import get_bid_detail

    detail = await get_bid_detail(bid_no)
    print(f"  공고명: {detail.get('project_name', 'N/A')}")
    print(f"  발주처: {detail.get('client', 'N/A')}")
    print(f"  예산: {detail.get('budget', 'N/A')}")
    print(f"  요구사항: {str(detail.get('requirements_summary', ''))[:100]}")
    print(f"  첨부파일: {len(detail.get('attachments', []))}건")
    return detail


async def main():
    print(f"\n{'━'*60}")
    print(f"  G2B API 통합 테스트 — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'━'*60}\n")

    # 1. 입찰공고 검색
    try:
        results = await test_bid_search()
        print(f"  ✅ 입찰공고 검색 성공 ({len(results)}건)\n")
    except Exception as e:
        print(f"  ❌ 입찰공고 검색 실패: {e}\n")
        results = []

    # 2. 낙찰결과 조회
    try:
        bid_results = await test_bid_results()
        print(f"  ✅ 낙찰결과 조회 성공 ({len(bid_results)}건)\n")
    except Exception as e:
        print(f"  ❌ 낙찰결과 조회 실패: {e}\n")

    # 3. search_bids 래퍼
    try:
        bids = await test_standalone_wrapper()
        print(f"  ✅ search_bids 래퍼 성공 ({len(bids)}건)\n")
    except Exception as e:
        print(f"  ❌ search_bids 래퍼 실패: {e}\n")
        bids = []

    # 4. 상세 조회
    if bids:
        try:
            await test_bid_detail(bids[0]["bid_no"])
            print(f"\n  ✅ 상세 조회 성공\n")
        except Exception as e:
            print(f"\n  ❌ 상세 조회 실패: {e}\n")

    print(f"{'━'*60}")
    print("  DONE")
    print(f"{'━'*60}")


if __name__ == "__main__":
    asyncio.run(main())
