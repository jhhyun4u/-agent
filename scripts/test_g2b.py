"""
나라장터 G2B API 실제 호출 테스트

실행: uv run python -X utf8 scripts/test_g2b.py
"""

import asyncio
import json
import sys
from datetime import datetime

sys.path.insert(0, ".")


async def test_raw_api_call():
    """G2B API 직접 호출 - 인증 키 동작 확인."""
    import aiohttp
    from app.config import settings

    key = settings.g2b_api_key
    if not key:
        print("[FAIL] G2B_API_KEY가 .env에 설정되지 않았습니다.")
        return False

    print(f"[INFO] API 키 길이: {len(key)}자")

    url = "https://apis.data.go.kr/1230000/BidPublicInfoService04/getBidPblancListInfoServc"
    params = {
        "serviceKey": key,
        "_type": "json",
        "numOfRows": "3",
        "pageNo": "1",
        "bidNtceNm": "정보",
    }

    async with aiohttp.ClientSession() as session:
        # 시도 1: params 전달 (aiohttp 자동 인코딩)
        print("\n[TEST 1] params 전달 (인코딩 없음)")
        try:
            async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                print(f"  HTTP Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    header = data.get("response", {}).get("header", {})
                    print(f"  resultCode: {header.get('resultCode')}")
                    print(f"  resultMsg: {header.get('resultMsg')}")
                    if header.get("resultCode") == "00":
                        body = data.get("response", {}).get("body", {})
                        print(f"  totalCount: {body.get('totalCount', 0)}")
                        items = body.get("items", {}).get("item", [])
                        if isinstance(items, dict):
                            items = [items]
                        print(f"  반환 건수: {len(items)}건")
                        if items:
                            print(f"  첫 번째: {items[0].get('bidNtceNm', 'N/A')}")
                        return True
                    else:
                        print(f"  [WARN] API 오류: {header.get('resultMsg')}")
                else:
                    text = await resp.text()
                    print(f"  [FAIL] HTTP {resp.status}")
                    # 에러 내용에서 키는 가림
                    safe_text = text.replace(key, "***KEY***")
                    print(f"  응답: {safe_text[:300]}")
        except Exception as e:
            print(f"  [ERROR] {e}")

        # 시도 2: serviceKey를 URL에 직접 넣기 (인코딩 없이)
        print("\n[TEST 2] URL에 직접 삽입")
        from urllib.parse import urlencode
        qs = urlencode({"_type": "json", "numOfRows": "3", "pageNo": "1", "bidNtceNm": "정보"})
        direct_url = f"{url}?serviceKey={key}&{qs}"
        try:
            async with session.get(direct_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                print(f"  HTTP Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    header = data.get("response", {}).get("header", {})
                    print(f"  resultCode: {header.get('resultCode')}")
                    print(f"  resultMsg: {header.get('resultMsg')}")
                    if header.get("resultCode") == "00":
                        body = data.get("response", {}).get("body", {})
                        print(f"  totalCount: {body.get('totalCount', 0)}")
                        return True
                else:
                    print(f"  [FAIL] HTTP {resp.status}")
        except Exception as e:
            print(f"  [ERROR] {e}")

        # 시도 3: quote된 키 사용 (현재 코드 방식)
        print("\n[TEST 3] quote 인코딩된 키")
        from urllib.parse import quote
        encoded_key = quote(key, safe="")
        direct_url2 = f"{url}?serviceKey={encoded_key}&{qs}"
        try:
            async with session.get(direct_url2, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                print(f"  HTTP Status: {resp.status}")
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    header = data.get("response", {}).get("header", {})
                    print(f"  resultCode: {header.get('resultCode')}")
                    print(f"  resultMsg: {header.get('resultMsg')}")
                    if header.get("resultCode") == "00":
                        body = data.get("response", {}).get("body", {})
                        print(f"  totalCount: {body.get('totalCount', 0)}")
                        return True
                else:
                    print(f"  [FAIL] HTTP {resp.status}")
        except Exception as e:
            print(f"  [ERROR] {e}")

    return False


async def test_search_bids():
    """standalone wrapper search_bids() 테스트."""
    print("\n" + "=" * 50)
    print("[TEST 4] search_bids('클라우드')")
    print("=" * 50)

    from app.services.g2b_service import search_bids

    bids = await search_bids("클라우드")
    print(f"  결과: {len(bids)}건")
    for i, b in enumerate(bids[:3]):
        print(f"  [{i+1}] {b.get('project_name', 'N/A')}")
        print(f"      공고번호: {b.get('bid_no')}, 발주처: {b.get('client')}")
        print(f"      예산: {b.get('budget')}, 마감: {b.get('deadline')}")
    return len(bids) > 0


async def test_bid_detail(bid_no: str):
    """standalone wrapper get_bid_detail() 테스트."""
    print(f"\n[TEST 5] get_bid_detail('{bid_no}')")
    from app.services.g2b_service import get_bid_detail

    detail = await get_bid_detail(bid_no)
    print(f"  공고명: {detail.get('project_name', 'N/A')}")
    print(f"  발주처: {detail.get('client', 'N/A')}")
    print(f"  예산: {detail.get('budget', 'N/A')}")
    print(f"  요구사항: {str(detail.get('requirements_summary', ''))[:100]}")
    print(f"  첨부파일: {len(detail.get('attachments', []))}건")
    return bool(detail.get("project_name"))


async def main():
    print("=" * 50)
    print(f"  G2B API Test - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    # 1. API 인증 확인 (3가지 방식 시도)
    api_ok = await test_raw_api_call()

    if not api_ok:
        print("\n[결론] API 인증 실패. 확인 사항:")
        print("  1. 공공데이터포털(data.go.kr)에서 발급받은 '인코딩' 키를 사용하세요")
        print("  2. 키 형태 예시: Abc123%2Fxyz%3D%3D (URL-encoded, 보통 100자 이상)")
        print("  3. 현재 키는 64자 hex - 공공데이터포털 키 형태가 아닐 수 있습니다")
        print("  4. API 활용 신청 후 승인까지 1-2시간 소요될 수 있습니다")
        return

    # 2. standalone 래퍼 테스트
    search_ok = await test_search_bids()

    # 3. 상세 조회 (검색 성공 시)
    if search_ok:
        from app.services.g2b_service import search_bids
        bids = await search_bids("클라우드")
        if bids:
            await test_bid_detail(bids[0]["bid_no"])

    print("\n" + "=" * 50)
    print("  DONE")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
