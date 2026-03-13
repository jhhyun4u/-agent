"""
초기 데이터 시딩 스크립트

Phase 0: 조직 구조, 테스트 사용자, 기본 역량 DB 데이터 생성.
Supabase service_role_key로 실행 (RLS 우회).

사용법:
    uv run python scripts/seed_data.py
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.supabase_client import get_async_client


async def seed():
    client = await get_async_client()
    print("=== TENOPA v3.4 시드 데이터 생성 시작 ===\n")

    # ── 1. 조직 ──
    print("1. 조직 생성...")
    org_res = await client.table("organizations").upsert({
        "id": "00000000-0000-0000-0000-000000000001",
        "name": "TENOPA",
    }).execute()
    org_id = org_res.data[0]["id"]
    print(f"   → 조직: TENOPA ({org_id})")

    # ── 2. 본부 ──
    print("2. 본부 생성...")
    divisions = [
        {"id": "00000000-0000-0000-0001-000000000001", "org_id": org_id, "name": "ICT사업본부"},
        {"id": "00000000-0000-0000-0001-000000000002", "org_id": org_id, "name": "컨설팅본부"},
    ]
    for div in divisions:
        await client.table("divisions").upsert(div).execute()
        print(f"   → 본부: {div['name']}")

    # ── 3. 팀 ──
    print("3. 팀 생성...")
    teams = [
        {"id": "00000000-0000-0000-0002-000000000001", "division_id": divisions[0]["id"], "name": "AI사업팀"},
        {"id": "00000000-0000-0000-0002-000000000002", "division_id": divisions[0]["id"], "name": "클라우드팀"},
        {"id": "00000000-0000-0000-0002-000000000003", "division_id": divisions[1]["id"], "name": "전략컨설팅팀"},
    ]
    for team in teams:
        await client.table("teams").upsert(team).execute()
        print(f"   → 팀: {team['name']}")

    # ── 4. 테스트 사용자 ──
    # 참고: 실제 사용자는 Azure AD SSO로 생성됨.
    # 여기서는 auth.users 없이 프로필만 생성 (개발 테스트용).
    print("4. 테스트 사용자 생성...")
    users = [
        {
            "id": "00000000-0000-0000-0003-000000000001",
            "email": "admin@tenopa.co.kr",
            "name": "관리자",
            "role": "admin",
            "org_id": org_id,
            "division_id": divisions[0]["id"],
        },
        {
            "id": "00000000-0000-0000-0003-000000000002",
            "email": "director@tenopa.co.kr",
            "name": "김본부장",
            "role": "director",
            "org_id": org_id,
            "division_id": divisions[0]["id"],
        },
        {
            "id": "00000000-0000-0000-0003-000000000003",
            "email": "lead@tenopa.co.kr",
            "name": "이팀장",
            "role": "lead",
            "org_id": org_id,
            "team_id": teams[0]["id"],
            "division_id": divisions[0]["id"],
        },
        {
            "id": "00000000-0000-0000-0003-000000000004",
            "email": "member1@tenopa.co.kr",
            "name": "박대리",
            "role": "member",
            "org_id": org_id,
            "team_id": teams[0]["id"],
            "division_id": divisions[0]["id"],
        },
        {
            "id": "00000000-0000-0000-0003-000000000005",
            "email": "member2@tenopa.co.kr",
            "name": "최사원",
            "role": "member",
            "org_id": org_id,
            "team_id": teams[0]["id"],
            "division_id": divisions[0]["id"],
        },
        {
            "id": "00000000-0000-0000-0003-000000000006",
            "email": "executive@tenopa.co.kr",
            "name": "정경영",
            "role": "executive",
            "org_id": org_id,
            "division_id": divisions[0]["id"],
        },
    ]
    for u in users:
        try:
            await client.table("users").upsert(u).execute()
            print(f"   → {u['role']:10s} {u['name']} ({u['email']})")
        except Exception as e:
            print(f"   ⚠ {u['name']} 생성 실패 (auth.users FK 필요): {e}")

    # ── 5. 기본 역량 DB ──
    print("5. 기본 역량 데이터 생성...")
    capabilities = [
        {
            "org_id": org_id,
            "type": "track_record",
            "title": "AI 플랫폼 구축",
            "detail": "2024년 과학기술정보통신부 AI 기반 정책분석 플랫폼 구축 (12억원, 8개월)",
            "keywords": ["AI", "플랫폼", "정책분석"],
            "created_by": users[3]["id"],
        },
        {
            "org_id": org_id,
            "type": "track_record",
            "title": "클라우드 마이그레이션",
            "detail": "2025년 행정안전부 정부통합전산센터 클라우드 전환 사업 (8억원, 6개월)",
            "keywords": ["클라우드", "마이그레이션", "공공"],
            "created_by": users[3]["id"],
        },
        {
            "org_id": org_id,
            "type": "tech",
            "title": "LLM 기반 문서 자동화",
            "detail": "Claude/GPT API 활용 대규모 문서 분석·생성 파이프라인 기술 보유",
            "keywords": ["LLM", "문서자동화", "AI"],
            "created_by": users[3]["id"],
        },
        {
            "org_id": org_id,
            "type": "personnel",
            "title": "AI 전문 인력 풀",
            "detail": "AI/ML 박사 3명, 석사 7명, 클라우드 아키텍트 5명 보유",
            "keywords": ["AI", "인력", "전문가"],
            "created_by": users[3]["id"],
        },
    ]
    for cap in capabilities:
        try:
            await client.table("capabilities").insert(cap).execute()
            print(f"   → {cap['type']:15s} {cap['title']}")
        except Exception as e:
            print(f"   ⚠ {cap['title']} 생성 실패: {e}")

    # ── 6. 노임단가 샘플 데이터 ──
    print("6. 노임단가 샘플 데이터...")
    labor_rates = [
        {"standard_org": "KOSA", "year": 2026, "grade": "기술사", "monthly_rate": 6_500_000, "daily_rate": 295_000},
        {"standard_org": "KOSA", "year": 2026, "grade": "특급", "monthly_rate": 5_800_000, "daily_rate": 263_000},
        {"standard_org": "KOSA", "year": 2026, "grade": "고급", "monthly_rate": 4_900_000, "daily_rate": 222_000},
        {"standard_org": "KOSA", "year": 2026, "grade": "중급", "monthly_rate": 3_800_000, "daily_rate": 172_000},
        {"standard_org": "KOSA", "year": 2026, "grade": "초급", "monthly_rate": 2_700_000, "daily_rate": 122_000},
    ]
    for lr in labor_rates:
        try:
            await client.table("labor_rates").insert(lr).execute()
            print(f"   → {lr['standard_org']} {lr['year']} {lr['grade']}: {lr['monthly_rate']:,}원/월")
        except Exception as e:
            print(f"   ⚠ 노임단가 생성 실패: {e}")

    print("\n=== 시드 데이터 생성 완료 ===")


if __name__ == "__main__":
    asyncio.run(seed())
