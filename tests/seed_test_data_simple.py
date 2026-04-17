#!/usr/bin/env python3
"""
Direct SQL-based test data insertion
"""
import asyncio
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

async def insert_test_data():
    """Insert test data using direct SQL"""
    from supabase import acreate_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY required")

    client = await acreate_client(url, key)

    # Test data
    test_data = [
        {
            "bid_no": "E2E_TEST_001",
            "bid_title": "[테스트] AI 시스템 개발용역",
            "agency": "테스트 발주기관",
            "bid_type": "용역",
            "budget_amount": 50_000_000,
            "deadline_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "days_remaining": 30,
            "content_text": "AI 모델 개발 테스트 공고",
        },
    ]

    for item in test_data:
        print(f"Inserting {item['bid_no']}...")
        try:
            # Try direct SQL insert
            sql = f"""
            INSERT INTO bid_announcements
            (bid_no, bid_title, agency, bid_type, budget_amount, deadline_date, days_remaining, content_text)
            VALUES ('{item['bid_no']}', '{item['bid_title']}', '{item['agency']}', '{item['bid_type']}', {item['budget_amount']}, '{item['deadline_date']}', {item['days_remaining']}, '{item['content_text']}')
            ON CONFLICT (bid_no) DO NOTHING
            """
            result = await client.rpc('exec_sql', {'query': sql}).execute()
            print(f"Result: {result}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(insert_test_data())
