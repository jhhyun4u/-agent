#!/usr/bin/env python3
"""
E2E 테스트용 공고 데이터 자동 생성

사용법:
    uv run python tests/seed_test_data.py              # 테스트 데이터 생성
    uv run python tests/seed_test_data.py --cleanup    # 테스트 데이터 삭제
    uv run python tests/seed_test_data.py --check      # 생성된 데이터 확인
"""

import asyncio
import os
import sys
import io
import argparse
from datetime import datetime, timedelta, timezone
import logging

from dotenv import load_dotenv

# Fix UTF-8 encoding on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')

# .env 로드
load_dotenv()

async def get_client():
    """Supabase 클라이언트 생성"""
    from supabase import acreate_client

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")

    if not url or not key:
        raise ValueError("SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY 필수")

    return await acreate_client(url, key)


TEST_BIDS = [
    {
        "bid_no": "E26BK00000001",  # G2B 형식: Eyyxxnnnnnnnn
        "bid_title": "[테스트] AI 시스템 개발용역",
        "agency": "테스트 발주기관",
        "bid_type": "용역",
        "budget_amount": 50_000_000,  # 50M (기준 충족)
        "deadline_date": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
        "days_remaining": 30,
        "content_text": """
# 테스트 공고

## 프로젝트 개요
- 예산: 50,000,000원
- 마감: 30일
- 난이도: 보통

## 주요 요구사항
- AI 모델 개발
- 데이터 전처리
- 성능 평가
""",
        "raw_data": {
            "bid_url": "https://example.com/bid/e26bk00000001"
        }
    },
    {
        "bid_no": "E26BK00000002",
        "bid_title": "[테스트] 클라우드 마이그레이션",
        "agency": "테스트 발주기관",
        "bid_type": "용역",
        "budget_amount": 80_000_000,  # 80M (기준 초과)
        "deadline_date": (datetime.now(timezone.utc) + timedelta(days=45)).isoformat(),
        "days_remaining": 45,
        "content_text": "클라우드 인프라 마이그레이션 프로젝트",
        "raw_data": {
            "bid_url": "https://example.com/bid/e26bk00000002"
        }
    },
    {
        "bid_no": "E26BK00000003",
        "bid_title": "[테스트] 저예산 공고",
        "agency": "테스트 발주기관",
        "bid_type": "용역",
        "budget_amount": 20_000_000,  # 20M (기준 미달)
        "deadline_date": (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),
        "days_remaining": 7,
        "content_text": "저예산 테스트 공고",
        "raw_data": {
            "bid_url": "https://example.com/bid/e26bk00000003"
        }
    },
    {
        "bid_no": "E26BK00000004",
        "bid_title": "[테스트] 마감된 공고",
        "agency": "테스트 발주기관",
        "bid_type": "용역",
        "budget_amount": 30_000_000,
        "deadline_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),  # 어제 마감
        "days_remaining": -1,
        "content_text": "이미 마감된 공고",
        "raw_data": {
            "bid_url": "https://example.com/bid/e26bk00000004"
        }
    }
]


async def create_test_data():
    """테스트 데이터 생성"""
    client = await get_client()

    print("\n📋 E2E 테스트 데이터 생성 중...\n")

    created = 0
    failed = 0

    for bid in TEST_BIDS:
        try:
            # 기존 데이터 확인 (간단한 체크)
            try:
                existing = await client.table("bid_announcements").select("id").eq(
                    "bid_no", bid["bid_no"]
                ).maybe_single().execute()

                if existing and existing.data:
                    print(f"⊘ {bid['bid_no']:<25} (이미 존재, 스킵)")
                    continue
            except Exception:
                # If check fails, continue with insert
                pass

            # 새 공고 생성
            await client.table("bid_announcements").insert({
                "bid_no": bid["bid_no"],
                "bid_title": bid["bid_title"],
                "agency": bid["agency"],
                "bid_type": bid["bid_type"],
                "budget_amount": bid["budget_amount"],
                "deadline_date": bid["deadline_date"],
                "days_remaining": bid["days_remaining"],
                "content_text": bid["content_text"],
                "raw_data": bid["raw_data"],
            }).execute()

            print(f"✅ {bid['bid_no']:<25} (예산: {bid['budget_amount']:,}원)")
            created += 1

        except Exception as e:
            print(f"❌ {bid['bid_no']:<25} 생성 실패: {str(e)[:100]}")
            failed += 1

    print(f"\n[완료] 생성: {created}개, 실패: {failed}개")

    # 생성된 데이터 확인
    print("\n📊 생성된 테스트 공고:")
    print("-" * 70)

    result = await client.table("bid_announcements").select(
        "bid_no, bid_title, budget_amount, deadline_date, days_remaining"
    ).in_("bid_no", [b["bid_no"] for b in TEST_BIDS]).execute()

    if result.data:
        for item in result.data:
            days_left = item.get("days_remaining", 0)
            status_icon = "⏰" if days_left > 0 else "❌"
            budget = item.get("budget_amount", 0)

            print(f"{status_icon} {item['bid_no']:<25} | {budget:>10,}원 | {days_left}일 남음")

    return created > 0


async def cleanup_test_data():
    """테스트 데이터 삭제"""
    client = await get_client()

    print("\n🗑️  E2E 테스트 데이터 삭제 중...\n")

    bid_nos = [b["bid_no"] for b in TEST_BIDS]

    try:
        await client.table("bid_announcements").delete().in_(
            "bid_no", bid_nos
        ).execute()

        print(f"✅ {len(bid_nos)}개 테스트 공고 삭제 완료")
        return True

    except Exception as e:
        print(f"❌ 삭제 실패: {e}")
        return False


async def check_test_data():
    """생성된 테스트 데이터 확인"""
    client = await get_client()

    print("\n📋 E2E 테스트 데이터 상태\n")

    bid_nos = [b["bid_no"] for b in TEST_BIDS]
    result = await client.table("bid_announcements").select(
        "bid_no, bid_title, budget_amount, deadline_date, days_remaining, created_at"
    ).in_("bid_no", bid_nos).execute()

    if not result.data:
        print("⊘ 생성된 테스트 데이터 없음")
        print("\n생성하려면: uv run python tests/seed_test_data.py")
        return

    print(f"발견된 테스트 공고: {len(result.data)}개\n")
    print(f"{'공고번호':<25} {'제목':<30} {'예산':<12} {'마감일'}")
    print("-" * 80)

    for item in result.data:
        title = item['bid_title'][:25]
        budget = item.get('budget_amount', 0)
        days = item.get('days_remaining', 0)
        print(f"{item['bid_no']:<25} {title:<30} {budget:>10,}원 {days}일")


async def main():
    parser = argparse.ArgumentParser(description="E2E 테스트 데이터 관리")
    parser.add_argument("--cleanup", action="store_true", help="테스트 데이터 삭제")
    parser.add_argument("--check", action="store_true", help="테스트 데이터 확인")

    args = parser.parse_args()

    try:
        if args.cleanup:
            success = await cleanup_test_data()
        elif args.check:
            await check_test_data()
            return
        else:
            success = await create_test_data()

        sys.exit(0 if success else 1)

    except Exception as e:
        print(f"\n❌ 오류: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
