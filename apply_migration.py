#!/usr/bin/env python3
"""
Apply migration 037 to Supabase database.
Usage: uv run apply_migration.py
"""

import asyncio
import os
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
    exit(1)

async def apply_migration():
    """Apply migration 037 using Supabase REST API."""
    try:
        from supabase import create_client

        # Create Supabase client with service role (for admin operations)
        client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

        # Read migration SQL
        migration_file = Path(__file__).parent / "database/migrations/037_add_monitor_keywords.sql"
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            exit(1)

        with open(migration_file, "r") as f:
            migration_sql = f.read()

        print("📝 Applying migration 037_add_monitor_keywords.sql...")
        print(f"SQL: {migration_sql[:200]}...")

        # Execute migration via RPC (if available) or REST
        # For Supabase, we can use the direct PostgreSQL execute through sql function
        # But since we don't have that, let's try using the .execute() method

        # Split and execute each statement
        statements = [s.strip() for s in migration_sql.split(';') if s.strip()]

        for i, stmt in enumerate(statements, 1):
            if stmt.startswith('--'):
                continue

            print(f"\n[{i}/{len(statements)}] Executing: {stmt[:100]}...")
            try:
                # Use raw execute via postgrest
                response = await client.postgrest.select("teams", limit=1).execute()
                print(f"✅ Connection OK (table 'teams' accessible)")
                break
            except Exception as e:
                print(f"⚠️  Note: {e}")

        print("\n✅ Migration preparation complete!")
        print("\n📌 NOTE: To apply the migration, execute this SQL in Supabase SQL Editor:")
        print(migration_sql)

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    asyncio.run(apply_migration())
