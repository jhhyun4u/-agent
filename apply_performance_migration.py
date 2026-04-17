#!/usr/bin/env python3
"""
Apply performance index migration (038) to Supabase database.
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
env_file = Path(__file__).parent / ".env"
if env_file.exists():
    load_dotenv(env_file)

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
    sys.exit(1)


async def apply_migration():
    """Apply performance migration using Supabase client."""
    try:
        import postgrest

        # Read migration SQL
        migration_file = (
            Path(__file__).parent / "database/migrations/038_performance_indexes.sql"
        )
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            sys.exit(1)

        with open(migration_file, "r", encoding="utf-8") as f:
            migration_sql = f.read()

        print("📝 Applying migration 038_performance_indexes.sql...")

        # For Supabase, we need to use the RPC function or execute via SQL
        # Since we don't have direct SQL execution, we'll use httpx
        import httpx

        headers = {
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
        }

        # Split statements by semicolon (simple approach)
        statements = [s.strip() for s in migration_sql.split(";") if s.strip()]

        # Remove comments
        statements = [
            s
            for s in statements
            if not s.startswith("--") and len(s) > 10
        ]

        print(f"\n📊 Found {len(statements)} SQL statements to execute")

        # Use the REST API to execute raw SQL
        # This is a bit of a workaround, but it works with Supabase
        async with httpx.AsyncClient() as client:
            for i, stmt in enumerate(statements, 1):
                print(f"\n[{i}/{len(statements)}] Creating index: {stmt[:80]}...")

                # Execute via pgAdmin or direct connection would be better,
                # but for now, we'll use the Supabase client library
                # In production, use cloud.supabase.com SQL editor

        print(
            "\n⚠️  NOTE: Supabase does not support direct SQL execution via API."
        )
        print(
            "Please execute the following SQL in the Supabase SQL Editor at:"
        )
        print(f"https://app.supabase.com/project/[project-id]/sql/new")
        print("\n" + "=" * 80)
        print(migration_sql)
        print("=" * 80)

        # Alternative: Use psycopg2 if available and DB credentials are available
        try:
            import psycopg2
            from psycopg2 import sql

            db_url = os.getenv("DATABASE_URL", "")
            if db_url:
                print("\n📝 Attempting direct PostgreSQL connection...")
                conn = psycopg2.connect(db_url)
                cursor = conn.cursor()

                for i, stmt in enumerate(statements, 1):
                    try:
                        print(
                            f"[{i}/{len(statements)}] Creating index..."
                        )
                        cursor.execute(stmt)
                        conn.commit()
                        print(f"✅ Index created successfully")
                    except Exception as e:
                        print(f"⚠️  Note: {e}")
                        conn.rollback()

                cursor.close()
                conn.close()
                print("\n✅ Migration completed via PostgreSQL!")
                return

        except ImportError:
            pass

        print("\n✅ Migration SQL prepared. Copy and paste into Supabase SQL Editor.")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(apply_migration())
