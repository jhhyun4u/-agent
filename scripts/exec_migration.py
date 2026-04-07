#!/usr/bin/env python3
"""마이그레이션 직접 실행"""

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from app.utils.supabase_client import get_async_client

# .env 파일 로드
load_dotenv()

# Windows UTF-8 인코딩 설정
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def run_migration():
    migration_file = Path("database/migrations/013_add_analysis_columns.sql")
    if not migration_file.exists():
        print(f"[ERROR] 파일을 찾을 수 없습니다: {migration_file}")
        return False

    sql = migration_file.read_text(encoding="utf-8")
    print(f"[INFO] 마이그레이션 파일 읽음: {migration_file}")
    print(f"[INFO] SQL 문장 수: {len(sql.split(';'))}")

    try:
        # Supabase 클라이언트 (service role)
        client = await get_async_client()
        print("[SUCCESS] Supabase 클라이언트 초기화 완료")

        # SQL 실행 (rpc 또는 직접)
        result = await client.rpc("exec_sql", {"sql_text": sql}).execute()

        print("[SUCCESS] 마이그레이션 실행 완료!")
        print(f"[INFO] 결과: {result}")
        return True

    except Exception as e:
        print(f"[WARNING] RPC 실패 ({type(e).__name__}): {e}")
        print("[INFO] Supabase Dashboard에서 수동으로 실행해주세요:")
        print("\n1. https://supabase.com/dashboard → SQL Editor")
        print("2. 아래 SQL을 복사하여 실행:\n")
        print("---")
        print(sql)
        print("---")
        return False


if __name__ == "__main__":
    result = asyncio.run(run_migration())
    exit(0 if result else 1)
