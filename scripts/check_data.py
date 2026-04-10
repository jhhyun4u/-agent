#!/usr/bin/env python3
"""bid_announcements의 실제 데이터 확인"""

import asyncio
import sys
from dotenv import load_dotenv
from app.utils.supabase_client import get_async_client

load_dotenv()

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def check_data():
    try:
        client = await get_async_client()

        # 2026010001 공고 조회
        bid_no = "2026010001"
        result = await client.table("bid_announcements")\
            .select("bid_no, bid_title, analysis_status, analysis_error")\
            .eq("bid_no", bid_no)\
            .maybe_single()\
            .execute()

        if result.data:
            print(f"[SUCCESS] bid_no={bid_no}인 레코드 찾음:")
            print(f"  - bid_title: {result.data.get('bid_title')}")
            print(f"  - analysis_status: {result.data.get('analysis_status')}")
            print(f"  - analysis_error: {result.data.get('analysis_error')}")
            return True
        else:
            print(f"[WARNING] bid_no={bid_no}인 레코드가 없습니다!")
            print("\n[ACTION] 테스트 레코드 생성 중...")

            # 테스트 레코드 생성
            insert_result = await client.table("bid_announcements").insert({
                "bid_no": bid_no,
                "bid_title": "테스트 공고",
                "agency": "테스트 발주기관",
                "budget_amount": 100000000,
                "analysis_status": "pending",
            }).execute()

            if insert_result.data:
                print("[SUCCESS] 레코드 생성 완료!")
                return True
            else:
                print("[ERROR] 레코드 생성 실패")
                return False

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(check_data())
    sys.exit(0 if result else 1)
