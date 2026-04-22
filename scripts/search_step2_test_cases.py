#!/usr/bin/env python3
"""
STEP 2 검증용 나라장터 공고 검색 스크립트

목표:
- IT/클라우드 분야 공고 검색 (예산 500M~1B 원)
- 충분한 상세정보가 있는 공고 선택
- STEP 0/1 입력 데이터로 활용 가능한 공고 확보
"""

import asyncio
import json
import sys
from datetime import datetime, timedelta

# 경로 추가
sys.path.insert(0, '/c/project/tenopa proposer')

from app.config import settings
from app.services.g2b_service import G2BService


async def search_test_cases():
    """IT/클라우드 분야 공고 검색"""

    print("=" * 80)
    print("STEP 2 검증용 나라장터 공고 검색 시작")
    print("=" * 80)
    print()

    # 검색 키워드 (IT/클라우드 분야)
    keywords = [
        "클라우드",
        "시스템 구축",
        "정보시스템",
        "네트워크",
        "통합",
        "플랫폼",
    ]

    candidates = []

    async with G2BService() as svc:
        for keyword in keywords:
            print(f"검색: '{keyword}' 키워드로 공고 조회 중...")
            try:
                results = await svc.search_bid_announcements(
                    keyword=keyword,
                    num_of_rows=50,
                    page_no=1,
                    date_from=(datetime.now() - timedelta(days=30)).strftime("%Y%m%d0000"),
                    date_to=datetime.now().strftime("%Y%m%d2359"),
                )

                print(f"  → {len(results)}개 공고 발견")

                for r in results:
                    try:
                        # 예산 필터링: 500M ~ 1B 원
                        budget = int(r.get("estmtPrdct", 0) or 0)
                        if budget < 500_000_000 or budget > 1_000_000_000:
                            continue

                        # 마감이 충분히 남은 공고
                        deadline = r.get("bascProcProcedBidClseDt", "")

                        candidate = {
                            "bid_no": r.get("bidNtceNo"),
                            "title": r.get("bidNtceNm"),
                            "budget": budget,
                            "agency": r.get("baskOrgNm"),
                            "deadline": deadline,
                            "category": r.get("ctgryNm"),
                            "type": r.get("bidNtceType"),
                            "received_date": r.get("bascProcRcptDt"),
                        }

                        candidates.append(candidate)

                    except Exception as e:
                        pass

                await asyncio.sleep(0.5)  # Rate limit 대비

            except Exception as e:
                print(f"  ✗ 검색 실패: {e}")

    # 결과 정렬 (예산 기준)
    candidates.sort(key=lambda x: x["budget"], reverse=True)

    print()
    print("=" * 80)
    print(f"검색 결과: {len(candidates)}개 적합 공고 발견")
    print("=" * 80)
    print()

    if not candidates:
        print("✗ 조건에 맞는 공고를 찾지 못했습니다.")
        return

    # 상위 10개 공고 출력
    for i, cand in enumerate(candidates[:10], 1):
        print(f"{i}. {cand['title']}")
        print(f"   공고번호: {cand['bid_no']}")
        print(f"   예산: ₩{cand['budget']:,}")
        print(f"   발주기관: {cand['agency']}")
        print(f"   분류: {cand['category']} ({cand['type']})")
        print(f"   마감일: {cand['deadline']}")
        print()

    # 검색 결과를 파일로 저장
    output_file = "/c/project/tenopa proposer/scripts/step2_test_candidates.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(candidates[:10], f, ensure_ascii=False, indent=2)

    print(f"결과가 {output_file}에 저장되었습니다.")
    print()
    print("다음 단계:")
    print("1. 위 목록에서 하나 선택")
    print("2. STEP 0 (G2B 공고 검색) 실행")
    print("3. STEP 1 (RFP 분석 + Go/No-Go) 실행")
    print("4. STEP 2 (포지셔닝/전략) 실행")
    print("5. 출력 검증")


if __name__ == "__main__":
    asyncio.run(search_test_cases())
