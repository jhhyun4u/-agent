#!/usr/bin/env python3
"""
Apply Document Ingestion schema fixes to Supabase
Run this script to migrate the intranet_documents table
"""

import asyncio
import sys
from app.utils.supabase_client import get_async_client


async def apply_migration():
    """Apply migration 018: Document Ingestion Fixes"""
    client = await get_async_client()

    migrations = [
        # 1. Make project_id nullable
        (
            "ALTER TABLE intranet_documents ALTER COLUMN project_id DROP NOT NULL;",
            "Made project_id nullable",
        ),
        # 2. Make file_slot nullable
        (
            "ALTER TABLE intranet_documents ALTER COLUMN file_slot DROP NOT NULL;",
            "Made file_slot nullable",
        ),
        # 3. Make file_type nullable
        (
            "ALTER TABLE intranet_documents ALTER COLUMN file_type DROP NOT NULL;",
            "Made file_type nullable",
        ),
        # 4. Update doc_type constraint to include Korean values
        (
            "ALTER TABLE intranet_documents DROP CONSTRAINT IF EXISTS intranet_documents_doc_type_check;",
            "Dropped old doc_type constraint",
        ),
        (
            """ALTER TABLE intranet_documents ADD CONSTRAINT intranet_documents_doc_type_check
               CHECK (doc_type IN ('보고서', '제안서', '실적', '기타', 'proposal', 'report', 'presentation', 'contract', 'reference', 'other'));""",
            "Added updated doc_type constraint with Korean values",
        ),
        # 5. Make UNIQUE constraint handle nullable project_id
        (
            "ALTER TABLE intranet_documents DROP CONSTRAINT IF EXISTS intranet_documents_project_id_file_slot_key;",
            "Dropped old UNIQUE constraint",
        ),
        (
            """CREATE UNIQUE INDEX IF NOT EXISTS idx_intranet_documents_project_file_slot
               ON intranet_documents(project_id, file_slot)
               WHERE project_id IS NOT NULL AND file_slot IS NOT NULL;""",
            "Created new partial unique index",
        ),
    ]

    print("🔄 Applying Document Ingestion Schema Migration...")
    print()

    for i, (sql, description) in enumerate(migrations, 1):
        try:
            result = await client.postgrest.rpc("exec_sql", {"sql": sql}).execute()
            print(f"✅ Step {i}: {description}")
        except Exception as e:
            # For RPC-based approach, we might not have exec_sql
            # Try alternative: use direct admin client if available
            print(f"⚠️  Step {i}: {description}")
            print(f"   Note: {e}")
            print(f"   SQL: {sql[:100]}...")

    print()
    print("✅ Migration complete!")
    print()
    print("Note: If you see warnings above, you may need to apply the SQL manually in Supabase SQL Editor:")
    print("  1. Go to Supabase Dashboard > SQL Editor")
    print("  2. Create a new query and run: database/migrations/018_document_ingestion_fixes.sql")


if __name__ == "__main__":
    asyncio.run(apply_migration())
