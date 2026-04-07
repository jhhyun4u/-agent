#!/usr/bin/env python3
"""공고 분석 직접 테스트"""

import asyncio
from app.services.bid_analysis_service import generate_bid_analysis_documents

async def test():
    bid_no = '2026010001'
    print(f"[TEST] 공고 분석 직접 실행: {bid_no}")

    try:
        result = await generate_bid_analysis_documents(
            bid_no=bid_no,
            bid_title='테스트 공고',
            agency='테스트 기관',
            budget_amount=100000000,
            deadline_date='2026-05-06',
            content_text='테스트 공고 내용입니다.',
            raw_data={}
        )
        print("[SUCCESS] 분석 완료!")
        print(f"  결과: {result}")
        return True
    except Exception as e:
        print(f"[ERROR] 분석 실패: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    result = asyncio.run(test())
    exit(0 if result else 1)
