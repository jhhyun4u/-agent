#!/usr/bin/env python3
"""공고 분석 상태 확인"""

import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def check_status():
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()
    bid_no = "2026010001"

    print(f"[INFO] bid_no={bid_no}의 상태 확인...")

    result = await client.table("bid_announcements")\
        .select(
            "bid_no, bid_title, analysis_status, "
            "analysis_started_at, analysis_completed_at, analysis_error"
        )\
        .eq("bid_no", bid_no)\
        .limit(1)\
        .execute()

    if result.data and len(result.data) > 0:
        data = result.data[0]
        print("\n[DATA] 현재 상태:")
        print(f"  bid_no: {data.get('bid_no')}")
        print(f"  title: {data.get('bid_title')}")
        print(f"  analysis_status: {data.get('analysis_status')}")
        print(f"  analysis_started_at: {data.get('analysis_started_at')}")
        print(f"  analysis_completed_at: {data.get('analysis_completed_at')}")
        print(f"  analysis_error: {data.get('analysis_error')}")

        status = data.get('analysis_status')

        if status == 'pending':
            print("\n[INFO] 상태: 분석 대기 중")
            print("[ACTION] _queue_bid_analysis() 함수가 백그라운드에서 분석을 시작해야 합니다")
        elif status == 'analyzing':
            print("\n[INFO] 상태: 분석 진행 중")
        elif status == 'analyzed':
            print("\n[INFO] 상태: 분석 완료")
        elif status == 'failed':
            print("\n[ERROR] 상태: 분석 실패")
            print(f"  에러: {data.get('analysis_error')}")
    else:
        print("[ERROR] 데이터를 찾을 수 없습니다")


if __name__ == "__main__":
    asyncio.run(check_status())
