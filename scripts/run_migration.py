#!/usr/bin/env python3
"""마이그레이션 실행 스크립트"""

import asyncio
import sys
from pathlib import Path

from app.utils.supabase_client import get_async_client

async def run_migration(migration_file: str):
    """SQL 마이그레이션 파일 실행"""
    migration_path = Path(migration_file)

    if not migration_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {migration_path}")
        return False

    # SQL 읽기
    sql = migration_path.read_text(encoding="utf-8")
    print(f"📖 마이그레이션 파일 읽음: {migration_path}")
    print(f"📝 SQL:\n{sql}\n")

    try:
        client = await get_async_client()

        # Supabase RPC를 통해 SQL 실행
        # 또는 직접 실행 (service role 권한 필요)
        await client.rpc("execute_sql", {"sql": sql}).execute()

        print("✅ 마이그레이션 실행 완료!")
        return True

    except Exception as e:
        # Fallback: 다른 방식으로 시도
        print(f"⚠️  RPC 방식 실패 ({e.__class__.__name__}): {e}")
        print("💡 Supabase Dashboard에서 수동으로 실행해주세요:")
        print("\n1. https://supabase.com/dashboard → SQL Editor")
        print("2. 아래 SQL을 복사하여 실행:\n")
        print("---")
        print(sql)
        print("---")
        return False

async def main():
    migration_file = "database/migrations/013_add_analysis_columns.sql"
    success = await run_migration(migration_file)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())
