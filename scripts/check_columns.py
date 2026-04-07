#!/usr/bin/env python3
"""bid_announcements 테이블의 컬럼 확인"""

import asyncio
import sys
from dotenv import load_dotenv
from app.utils.supabase_client import get_async_client

load_dotenv()

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def check_columns():
    try:
        client = await get_async_client()

        # information_schema.columns에서 컬럼 조회
        result = await client.table("information_schema_columns")\
            .select("column_name, data_type")\
            .eq("table_name", "bid_announcements")\
            .order("ordinal_position")\
            .execute()

        if result.data:
            print("[INFO] bid_announcements 테이블의 컬럼:")
            print("-" * 60)
            for col in result.data:
                print(f"  - {col['column_name']:<35} {col['data_type']}")
            print("-" * 60)

            # 필요한 컬럼 체크
            required = [
                'analysis_status', 'rfp_summary', 'rfp_sections',
                'suitability_score', 'verdict', 'fit_level'
            ]
            existing = [col['column_name'] for col in result.data]

            missing = [c for c in required if c not in existing]
            if missing:
                print(f"\n[WARNING] 누락된 컬럼: {missing}")
                print("[ACTION] Supabase Dashboard에서 마이그레이션 SQL을 실행해주세요!")
            else:
                print("\n[SUCCESS] 모든 필요한 컬럼이 있습니다!")

            return len(missing) == 0
        else:
            print("[ERROR] 테이블 정보를 조회할 수 없습니다.")
            return False

    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(check_columns())
    sys.exit(0 if result else 1)
