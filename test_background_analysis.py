#!/usr/bin/env python3
"""백그라운드 분석 함수 직접 테스트"""

import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def test():
    """_analyze_bid_background 함수 직접 테스트"""
    bid_no = '2026010001'
    print(f"[TEST] 백그라운드 분석 직접 실행: {bid_no}")

    try:
        from app.api.routes_bids import _analyze_bid_background

        # 직접 함수 호출 (비동기)
        await _analyze_bid_background(bid_no)

        print("[SUCCESS] 분석 완료!")

        # 결과 확인
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()

        result = await client.table("bid_announcements")\
            .select("analysis_status, analysis_completed_at, analysis_error")\
            .eq("bid_no", bid_no)\
            .limit(1)\
            .execute()

        if result.data:
            data = result.data[0]
            print(f"  최종 상태: {data.get('analysis_status')}")
            print(f"  완료 시간: {data.get('analysis_completed_at')}")
            print(f"  에러: {data.get('analysis_error')}")

        return True

    except Exception as e:
        print(f"[ERROR] 분석 실패: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    result = asyncio.run(test())
    exit(0 if result else 1)
