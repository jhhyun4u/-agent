#!/usr/bin/env python3
"""API 쿼리 방식 테스트"""

import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def test_api():
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()

    bid_no = "2026010001"
    print("[TEST] 방식 1: .execute() 사용")
    try:
        result = await client.table("bid_announcements")\
            .select("*")\
            .eq("bid_no", bid_no)\
            .maybe_single()\
            .execute()
        print(f"  result: {result}")
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\n[TEST] 방식 2: await 직접 사용")
    try:
        result = await client.table("bid_announcements")\
            .select("*")\
            .eq("bid_no", bid_no)\
            .maybe_single()
        print(f"  result: {result}")
    except Exception as e:
        print(f"  ERROR: {e}")

    print("\n[TEST] 방식 3: .limit(1) 사용")
    try:
        response = await client.table("bid_announcements")\
            .select("*")\
            .eq("bid_no", bid_no)\
            .limit(1)\
            .execute()
        print(f"  response: {response}")
        if response:
            print(f"  response.data: {response.data if hasattr(response, 'data') else 'N/A'}")
    except Exception as e:
        print(f"  ERROR: {e}")


if __name__ == "__main__":
    asyncio.run(test_api())
