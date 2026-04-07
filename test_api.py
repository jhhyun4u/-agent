#!/usr/bin/env python3
"""API 직접 테스트"""

import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def test_api():
    from app.utils.supabase_client import get_async_client

    print("[TEST] Supabase 클라이언트 초기화...")
    try:
        client = await get_async_client()
        print("[OK] 클라이언트 초기화 성공")
        print(f"[DEBUG] client type: {type(client)}")
        print(f"[DEBUG] client: {client}")
    except Exception as e:
        print(f"[ERROR] 클라이언트 초기화 실패: {e}")
        return

    print("\n[TEST] bid_announcements 테이블 쿼리...")
    try:
        bid_no = "2026010001"

        print(f"[DEBUG] 쿼리 시작: bid_no={bid_no}")
        result = await client.table("bid_announcements")\
            .select(
                "bid_no, analysis_status, rfp_summary, rfp_sections, "
                "suitability_score, verdict, fit_level, positive, negative, "
                "action_plan, recommended_teams, rfp_period, "
                "analysis_completed_at, analysis_error"
            )\
            .eq("bid_no", bid_no)\
            .maybe_single()\
            .execute()

        print(f"[DEBUG] 쿼리 완료")
        print(f"[DEBUG] result type: {type(result)}")
        print(f"[DEBUG] result: {result}")

        if hasattr(result, 'data'):
            print(f"[DEBUG] result.data: {result.data}")
            if result.data:
                print("[OK] 데이터 조회 성공!")
                for key, value in result.data.items():
                    print(f"  {key}: {value}")
            else:
                print("[WARNING] 데이터가 없습니다 (새 레코드 생성 필요)")
        else:
            print(f"[ERROR] result에 data 속성이 없습니다!")

    except Exception as e:
        print(f"[ERROR] 쿼리 실패: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_api())
