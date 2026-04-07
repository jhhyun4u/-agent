#!/usr/bin/env python3
"""Storage 파일 확인"""

import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def check_files():
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()
    bucket_name = "documents"
    bid_no = "2026010001"
    folder = f"bids/{bid_no}"

    print(f"[INFO] Storage bucket '{bucket_name}' 파일 확인:\n")

    try:
        # List files in the bid folder
        response = await client.storage.from_(bucket_name).list(folder)

        if response:
            print(f"[SUCCESS] {len(response)} 파일 발견:\n")
            for file in response:
                print(f"  ✓ {file['name']}")
                print(f"    Size: {file.get('metadata', {}).get('size', 'N/A')} bytes")
        else:
            print("[INFO] 파일 없음")

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(check_files())
