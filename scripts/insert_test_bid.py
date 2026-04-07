#!/usr/bin/env python3
"""테스트 공고 데이터 삽입"""

import asyncio
import sys
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv()

if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


async def insert_test_bid():
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()

    # 테스트 공고 데이터
    test_bid = {
        "bid_no": "2026010001",
        "bid_title": "클라우드 기반 제안관리 시스템 개발 용역",
        "agency": "한국정보화진흥원",
        "budget_amount": 500000000,
        "deadline_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "bid_type": "입찰공고",
        "content_text": """
## 사업 개요
클라우드 기반 제안관리 시스템 개발 및 구축

## 사업 목적
정부 용역 제안 프로세스 자동화 및 효율화

## 주요 요구사항
1. AI 기반 공고 분석 기능
2. 제안서 자동 생성
3. 실시간 협업 도구
4. 성과 분석 대시보드

## 평가항목
- 기술점수: 60점
- 가격점수: 40점
        """,
        "raw_data": {
            "공고번호": "2026010001",
            "공고명": "클라우드 기반 제안관리 시스템 개발 용역",
            "발주기관": "한국정보화진흥원"
        },
        "analysis_status": "pending"
    }

    print("[INFO] 테스트 공고 데이터 삽입 중...")
    print(f"  bid_no: {test_bid['bid_no']}")
    print(f"  title: {test_bid['bid_title']}")

    try:
        result = await client.table("bid_announcements").insert(test_bid).execute()

        if result.data:
            print("[SUCCESS] 데이터 삽입 완료!")
            print(f"  ID: {result.data[0].get('id')}")
            return True
        else:
            print("[ERROR] 데이터 삽입 실패")
            return False

    except Exception as e:
        # 이미 존재하는 경우 무시
        if "duplicate" in str(e).lower():
            print("[INFO] 데이터가 이미 존재합니다 (무시)")
            return True
        print(f"[ERROR] {type(e).__name__}: {e}")
        return False


if __name__ == "__main__":
    result = asyncio.run(insert_test_bid())
    sys.exit(0 if result else 1)
