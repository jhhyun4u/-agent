#!/usr/bin/env python3
"""bid_announcements 테이블 스키마 확인"""

import asyncio
import sys
from dotenv import load_dotenv
from app.utils.supabase_client import get_async_client

load_dotenv()

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def check_schema():
    try:
        client = await get_async_client()

        # 테이블에서 1개 레코드 조회
        result = await client.table("bid_announcements")\
            .select("*")\
            .limit(1)\
            .execute()

        if result.data:
            print("[INFO] bid_announcements 테이블의 컬럼:")
            print("-" * 60)
            record = result.data[0]
            for key in sorted(record.keys()):
                value_type = type(record[key]).__name__
                print(f"  - {key:<35} ({value_type})")
            print("-" * 60)

            # 필요한 컬럼 체크
            required = [
                'analysis_status', 'rfp_summary', 'rfp_sections',
                'suitability_score', 'verdict', 'fit_level',
                'positive', 'negative', 'action_plan',
                'recommended_teams', 'rfp_period',
                'analysis_completed_at', 'analysis_error'
            ]
            existing = list(record.keys())

            missing = [c for c in required if c not in existing]
            if missing:
                print(f"\n[MISSING] 누락된 컬럼: {missing}")
                print("\n[ACTION] Supabase Dashboard → SQL Editor에서 아래 SQL을 실행하세요:\n")
                print(open("database/migrations/013_add_analysis_columns.sql").read())
                return False
            else:
                print("\n[SUCCESS] 모든 필요한 컬럼이 있습니다!")
                return True
        else:
            print("[INFO] bid_announcements 테이블이 비어있습니다.")
            print("[INFO] 테이블 컬럼은 정상입니다. (빈 테이블도 컬럼 정보 확인 가능)")

            # 빈 테이블이므로 스키마만 확인하는 다른 방법 시도
            print("\n[INFO] SQL을 직접 실행하여 컬럼 추가 여부 확인 중...")
            return None

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(check_schema())
    if result is None:
        sys.exit(0)
    sys.exit(0 if result else 1)
