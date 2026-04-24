"""G2B 공고 검색 단독 테스트 스크립트.

사용법:
    uv run python scripts/test_g2b_search.py "인공지능"
    uv run python scripts/test_g2b_search.py "클라우드" --budget-min 100000000
"""
import asyncio
import sys
from datetime import datetime

# 프로젝트 루트를 path에 추가
sys.path.insert(0, ".")

from app.services.domains.bidding.g2b_service import G2BService


async def test_search(keyword: str, budget_min: int = 0):
    print(f"\n{'='*60}")
    print("  G2B 공고 검색 테스트")
    print(f"  키워드: {keyword}")
    if budget_min:
        print(f"  최소예산: {budget_min:,}원")
    print(f"  시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")

    async with G2BService() as svc:
        # 1단계: 공고 검색
        print("[1] 입찰공고 검색 중...")
        try:
            results = await svc.search_bid_announcements(keyword, num_of_rows=10)
        except RuntimeError as e:
            print(f"  ERROR: {e}")
            return

        if not results:
            print("  결과 없음")
            return

        print(f"  {len(results)}건 조회됨\n")

        # 결과 출력
        for i, r in enumerate(results, 1):
            bid_no = r.get("bidNtceNo", "")
            title = r.get("bidNtceNm", "")
            agency = r.get("ntceInsttNm", r.get("dminsttNm", ""))
            budget_raw = r.get("presmptPrce", r.get("asignBdgtAmt", ""))
            deadline = r.get("bidClseDt", "")

            # 예산 파싱
            budget_val = 0
            try:
                budget_val = int(str(budget_raw).replace(",", "").strip() or "0")
            except (ValueError, TypeError):
                pass

            # 최소예산 필터
            if budget_min and budget_val < budget_min:
                continue

            budget_display = f"{budget_val:>15,}원" if budget_val else f"{'미정':>16}"

            print(f"  [{i:2d}] {title[:50]}")
            print(f"       공고번호: {bid_no}")
            print(f"       발주기관: {agency}")
            print(f"       예산:     {budget_display}")
            print(f"       마감:     {deadline}")
            print()

        # 2단계: 첫 번째 공고 상세 조회
        first_bid_no = results[0].get("bidNtceNo", "")
        if first_bid_no:
            print(f"\n[2] 첫 번째 공고 상세 조회: {first_bid_no}")
            try:
                detail = await svc.get_bid_detail(first_bid_no)
                spec = detail.get("ntceSpecCn", "")
                if spec:
                    print(f"  규격서 내용 (첫 300자):\n  {spec[:300]}...")
                else:
                    print("  규격서 내용 없음 (첨부파일 참조 방식)")

                # 주요 필드 출력
                print(f"\n  상세 필드 ({len(detail)}개):")
                for key in ["bidNtceNm", "ntceInsttNm", "presmptPrce", "bidClseDt",
                             "ntceSpecDocUrl1", "bidNtceDtlUrl"]:
                    val = detail.get(key, "")
                    if val:
                        print(f"    {key}: {str(val)[:80]}")
            except Exception as e:
                print(f"  상세 조회 실패: {e}")


if __name__ == "__main__":
    keyword = sys.argv[1] if len(sys.argv) > 1 else "인공지능"
    budget_min = 0

    if "--budget-min" in sys.argv:
        idx = sys.argv.index("--budget-min")
        if idx + 1 < len(sys.argv):
            budget_min = int(sys.argv[idx + 1])

    asyncio.run(test_search(keyword, budget_min))
