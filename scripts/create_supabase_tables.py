#!/usr/bin/env python3
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

async def main():
    import sys
    sys.path.insert(0, '.')
    
    # Import the async database connection
    from app.utils.supabase_client import supabase_async
    
    # Test connection
    result = await supabase_async.table("users").select("id").limit(1).execute()
    print(f"Connection test: OK - {len(result.data)} users found")
    
    print("
Note: Raw SQL execution requires database credentials and psycopg2")
    print("Please execute the following SQL manually in Supabase SQL Editor:")
    print("=" * 80)
    
    sql_statements = ["CREATE TABLE IF NOT EXISTS g2b_bids (\n        bid_no VARCHAR(50) PRIMARY KEY,\n        name TEXT NOT NULL,\n        client VARCHAR(255),\n        budget DECIMAL(15, 2),\n        deadline TIMESTAMP,\n        project_type VARCHAR(100),\n        bid_status VARCHAR(50) DEFAULT 'open',\n        proposal_status VARCHAR(50) DEFAULT 'not_started',\n        announcement_date TIMESTAMP,\n        bid_open_date TIMESTAMP,\n        bid_close_date TIMESTAMP,\n        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n        metadata JSONB\n    )", 'CREATE INDEX IF NOT EXISTS idx_g2b_bids_status ON g2b_bids(bid_status)', 'CREATE INDEX IF NOT EXISTS idx_g2b_bids_proposal_status ON g2b_bids(proposal_status)', 'CREATE INDEX IF NOT EXISTS idx_g2b_bids_deadline ON g2b_bids(deadline)', "CREATE TABLE IF NOT EXISTS proposal_status (\n        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),\n        bid_no VARCHAR(50) NOT NULL,\n        status VARCHAR(50) NOT NULL DEFAULT 'not_started',\n        current_step INT DEFAULT 0,\n        progress_pct INT DEFAULT 0,\n        last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n        metadata JSONB,\n        FOREIGN KEY (bid_no) REFERENCES g2b_bids(bid_no) ON DELETE CASCADE\n    )", 'CREATE INDEX IF NOT EXISTS idx_proposal_status_bid_no ON proposal_status(bid_no)', 'CREATE INDEX IF NOT EXISTS idx_proposal_status_status ON proposal_status(status)']
    
    for i, stmt in enumerate(sql_statements, 1):
        print(f"
-- Statement {i}")
        print(stmt + ";")
    
    print("
" + "=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
