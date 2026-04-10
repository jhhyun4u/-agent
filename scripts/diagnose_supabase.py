#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Supabase 연결 진단 스크립트

사용법:
  uv run python scripts/diagnose_supabase.py
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# .env 파일 로드
env_path = Path(".env")
if env_path.exists():
    load_dotenv(env_path)

async def diagnose():
    """Supabase 연결 진단"""
    print("=" * 70)
    print("Supabase Database Connection Diagnosis")
    print("=" * 70)

    # 1. 환경변수 확인
    print("\n[1] Environment Variables")
    print("-" * 70)

    db_url = os.getenv("DATABASE_URL")
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")

    if db_url:
        try:
            # URL에서 민감한 정보 마스킹
            parts = db_url.split("@")
            masked = parts[0][:30] + "***@" + parts[1]
            print(f"[OK] DATABASE_URL: {masked}")
        except:
            print("[OK] DATABASE_URL: configured")
    else:
        print("[FAIL] DATABASE_URL: not set")

    if supabase_url:
        print(f"[OK] SUPABASE_URL: {supabase_url}")
    else:
        print("[FAIL] SUPABASE_URL: not set")

    if supabase_key:
        masked_key = supabase_key[:20] + "..." if len(supabase_key) > 20 else supabase_key
        print(f"[OK] SUPABASE_KEY: {masked_key}")
    else:
        print("[FAIL] SUPABASE_KEY: not set")

    # 2. asyncpg 연결 테스트
    print("\n[2] asyncpg Connection Test")
    print("-" * 70)

    try:
        import asyncpg

        if not db_url:
            print("[FAIL] DATABASE_URL not set - cannot test")
        else:
            # SSL 파라미터 제거
            clean_url = db_url.split("?")[0] if "?sslmode=" in db_url else db_url

            try:
                print("Attempting to connect...")
                conn = await asyncpg.connect(clean_url, timeout=10, ssl=False)
                print("[OK] asyncpg connection successful")

                # 테이블 확인
                table_count = await conn.fetchval("""
                    SELECT COUNT(*) FROM information_schema.tables
                    WHERE table_schema = 'public'
                """)

                print(f"[OK] Current tables: {table_count}")

                # migration_history 테이블 확인
                try:
                    mh_count = await conn.fetchval(
                        "SELECT COUNT(*) FROM migration_history"
                    )
                    print(f"[OK] migration_history table: {mh_count} records")
                except Exception:
                    print("[INFO] migration_history table: not found (expected)")

                await conn.close()

            except asyncpg.exceptions.InternalServerError as e:
                if "Tenant or user not found" in str(e):
                    print("[FAIL] Authentication error: Tenant or user not found")
                    print("  - Check DATABASE_URL credentials in .env")
                    print("  - Verify user exists in Supabase dashboard")
                else:
                    print(f"[FAIL] Supabase error: {e}")
            except asyncpg.exceptions.AuthenticationFailureError as e:
                print("[FAIL] Auth failure: password or username incorrect")
                print(f"  {e}")
            except asyncpg.exceptions.ServerError as e:
                print(f"[FAIL] Server error: {e}")
            except Exception as e:
                print(f"[FAIL] Connection error: {type(e).__name__}: {e}")

    except ImportError:
        print("[FAIL] asyncpg not installed")

    # 3. supabase 클라이언트 테스트
    print("\n[3] Supabase Python Client Test")
    print("-" * 70)

    try:
        from supabase import create_client

        if supabase_url and supabase_key:
            try:
                client = create_client(supabase_url, supabase_key)
                print("[OK] Supabase client created")

                # 간단한 쿼리 테스트
                try:
                    client.table("proposals").select("id", count="exact").limit(1).execute()
                    print("[OK] Query test successful (proposals table)")
                except Exception as e:
                    print(f"[WARN] Query test failed: {str(e)[:100]}")

            except Exception as e:
                print(f"[FAIL] Supabase client error: {e}")
        else:
            print("[FAIL] SUPABASE_URL or SUPABASE_KEY not set")

    except ImportError:
        print("[INFO] supabase client not installed (asyncpg is sufficient)")

    print("\n" + "=" * 70)
    print("Diagnosis Complete")
    print("=" * 70)

if __name__ == "__main__":
    asyncio.run(diagnose())
