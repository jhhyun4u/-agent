#!/usr/bin/env python3
"""
Insert test data directly into PostgreSQL via Supabase
"""
import asyncio
import os
import asyncpg
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

async def insert_test_data_async():
    """Insert test data using asyncpg"""
    # Supabase connection string
    supabase_url = os.getenv("SUPABASE_URL", "").replace("https://", "")
    db_host = supabase_url.split(".")[0] + ".supabase.co"
    db_user = "postgres"
    db_pass = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
    db_name = "postgres"

    print(f"Connecting to {db_host}...")

    try:
        conn = await asyncpg.connect(
            host=db_host,
            port=5432,
            user=db_user,
            password=db_pass,
            database=db_name,
            ssl='require'
        )

        test_bids = [
            ("E2E_TEST_001", "[테스트] AI 시스템 개발용역", "테스트 발주기관", "용역", 50_000_000, 30),
            ("E2E_TEST_002", "[테스트] 클라우드 마이그레이션", "테스트 발주기관", "용역", 80_000_000, 45),
            ("E2E_TEST_LOW_BUDGET", "[테스트] 저예산 공고", "테스트 발주기관", "용역", 20_000_000, 7),
            ("E2E_TEST_EXPIRED", "[테스트] 마감된 공고", "테스트 발주기관", "용역", 30_000_000, -1),
        ]

        for bid_no, title, agency, bid_type, budget, days in test_bids:
            deadline = datetime.now(timezone.utc) + timedelta(days=days)

            # Check if already exists
            existing = await conn.fetchval(
                "SELECT id FROM bid_announcements WHERE bid_no = $1",
                bid_no
            )

            if existing:
                print(f"⊘ {bid_no} (이미 존재)")
                continue

            # Insert
            try:
                await conn.execute(
                    """
                    INSERT INTO bid_announcements
                    (bid_no, bid_title, agency, bid_type, budget_amount, deadline_date, days_remaining, content_text)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    """,
                    bid_no, title, agency, bid_type, budget, deadline, days, f"테스트: {title}"
                )
                print(f"✅ {bid_no} (예산: {budget:,}원)")
            except Exception as e:
                print(f"❌ {bid_no} 삽입 실패: {e}")

        await conn.close()
        print("\n완료!")

    except Exception as e:
        print(f"데이터베이스 연결 실패: {e}")

if __name__ == "__main__":
    asyncio.run(insert_test_data_async())
