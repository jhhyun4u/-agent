"""
team_structure.json 기반 사용자 프로비저닝 스크립트

조직/본부/팀 생성 → Supabase Auth 계정 + users 행 일괄 등록.
배포 시 1회 실행. 중복 이메일은 건너뜁니다.

사용법:
    uv run python scripts/provision_users.py
    uv run python scripts/provision_users.py --dry-run   # 실행 없이 미리보기
    uv run python scripts/provision_users.py --password MyPw123!  # 공통 임시 비밀번호 지정
"""

import asyncio
import json
import os
import secrets
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.utils.supabase_client import get_async_client

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data" / "team_structure.json"

# 엑셀 role → 시스템 role 매핑
ROLE_MAP = {
    "대표이사": "admin",
    "본부장": "director",
    "연구소장": "director",
    "실장": "director",
    "팀장": "lead",
    "팀원": "member",
    "사업관리담당": "member",
    "인사총무담당": "member",
    "총괄기획": "admin",
    "개발": "member",
}


def map_role(excel_role: str, grade: str) -> str:
    """엑셀 역할/직급 → 시스템 role 변환."""
    if excel_role in ROLE_MAP:
        return ROLE_MAP[excel_role]
    # 직급 기반 fallback
    if grade in ("대표이사",):
        return "admin"
    if grade in ("파트너", "연구소장"):
        return "director"
    if grade in ("수석", "책임") and "팀장" in excel_role:
        return "lead"
    return "member"


async def provision(dry_run: bool = False, common_password: str | None = None):
    if not DATA_PATH.exists():
        print(f"[ERROR] {DATA_PATH} 없음. 먼저 import_team_structure.py 실행하세요.")
        sys.exit(1)

    with open(DATA_PATH, encoding="utf-8") as f:
        data = json.load(f)

    client = await get_async_client()
    print(f"=== TENOPA 사용자 프로비저닝 {'(DRY RUN)' if dry_run else ''} ===\n")

    # ── 1. 조직 ──
    org_id = "00000000-0000-0000-0000-000000000001"
    if not dry_run:
        await client.table("organizations").upsert({
            "id": org_id, "name": data["organization"],
        }).execute()
    print(f"1. 조직: {data['organization']} ({data['full_name']})")

    # ── 2. 본부 ──
    print("\n2. 본부 생성...")
    division_ids: dict[str, str] = {}  # name → id
    for i, div in enumerate(data["divisions"], 1):
        div_id = f"00000000-0000-0000-0001-{i:012d}"
        division_ids[div["name"]] = div_id
        if not dry_run:
            await client.table("divisions").upsert({
                "id": div_id, "org_id": org_id, "name": div["name"],
            }).execute()
        print(f"   [{div_id[-4:]}] {div['name']}")

    # ── 3. 팀 ──
    print("\n3. 팀 생성...")
    team_ids: dict[str, str] = {}  # name → id
    for i, team in enumerate(data["teams"], 1):
        team_id = f"00000000-0000-0000-0002-{i:012d}"
        team_ids[team["name"]] = team_id
        div_id = division_ids.get(team["division"])
        if not div_id:
            print(f"   ⚠ 본부 '{team['division']}' 없음 → {team['name']} 건너뜀")
            continue
        if not dry_run:
            await client.table("teams").upsert({
                "id": team_id, "division_id": div_id, "name": team["name"],
            }).execute()
        specs = ", ".join(team["specializations"][:3])
        if len(team["specializations"]) > 3:
            specs += f" 외 {len(team['specializations']) - 3}개"
        print(f"   [{team_id[-4:]}] {team['name']} ({team['division']}) — {specs or '(없음)'}")

    # ── 팀명 별칭 매핑 (JSON의 users.team 필드에서 사용하는 약칭) ──
    team_aliases = {
        "AX1팀": "버티컬AX1팀",
        "T2B1팀": "기술사업화1팀",
        "AX추진팀": "AX혁신팀",
    }

    # ── 4. 사용자 ──
    print("\n4. 사용자 프로비저닝...")
    seen_emails: set[str] = set()
    created = 0
    skipped = 0
    failed = 0
    credentials: list[dict] = []

    for user in data["users"]:
        email = user["email"]
        name = user["name"]

        # 중복 이메일 건너뛰기 (현재호, 김연정 등 복수 소속)
        if email in seen_emails:
            print(f"   ↩ {name} ({email}) — 중복, 건너뜀")
            skipped += 1
            continue
        seen_emails.add(email)

        sys_role = map_role(user["role"], user["grade"])
        team_name = user["team"]
        canonical_team = team_aliases.get(team_name, team_name)
        team_id = team_ids.get(canonical_team)
        div_name = user["division"]
        div_id = division_ids.get(div_name)

        temp_pw = common_password or secrets.token_urlsafe(12)

        if dry_run:
            print(f"   [{sys_role:8s}] {name:6s} {email:30s} 팀={canonical_team or '-':12s} 본부={div_name}")
            credentials.append({"email": email, "name": name, "password": temp_pw})
            created += 1
            continue

        # Supabase Auth 계정 생성
        try:
            auth_res = await client.auth.admin.create_user({
                "email": email,
                "password": temp_pw,
                "email_confirm": True,
            })
            auth_user = auth_res.user
            if not auth_user:
                print(f"   ✗ {name} ({email}) — Auth 응답 없음")
                failed += 1
                continue
        except Exception as e:
            err_msg = str(e)
            if "already been registered" in err_msg or "already exists" in err_msg:
                # 이미 Auth에 존재 → users 행만 upsert
                print(f"   ↩ {name} ({email}) — Auth 이미 존재, DB 행만 동기화")
                # 기존 Auth user id 조회
                try:
                    existing = await client.table("users").select("id").eq("email", email).maybe_single().execute()
                    if existing.data:
                        skipped += 1
                        continue
                except Exception:
                    pass
                skipped += 1
                continue
            print(f"   ✗ {name} ({email}) — {err_msg}")
            failed += 1
            continue

        # users 테이블 행 생성
        user_row = {
            "id": str(auth_user.id),
            "email": email,
            "name": name,
            "role": sys_role,
            "org_id": org_id,
            "must_change_password": True,
        }
        if team_id:
            user_row["team_id"] = team_id
        if div_id:
            user_row["division_id"] = div_id

        try:
            await client.table("users").upsert(user_row).execute()
            print(f"   ✓ [{sys_role:8s}] {name:6s} ({email})")
            credentials.append({"email": email, "name": name, "password": temp_pw})
            created += 1
        except Exception as e:
            # 롤백 Auth
            try:
                await client.auth.admin.delete_user(str(auth_user.id))
            except Exception:
                pass
            print(f"   ✗ {name} ({email}) — DB 실패: {e}")
            failed += 1

    # ── 결과 요약 ──
    print(f"\n{'=' * 50}")
    print(f"결과: 생성 {created} / 건너뜀 {skipped} / 실패 {failed} (총 {len(data['users'])})")

    # 임시 비밀번호 파일 저장
    if credentials and not dry_run:
        creds_path = PROJECT_ROOT / "data" / "initial_credentials.csv"
        with open(creds_path, "w", encoding="utf-8-sig") as f:
            f.write("이메일,이름,임시비밀번호\n")
            for c in credentials:
                f.write(f"{c['email']},{c['name']},{c['password']}\n")
        print(f"\n임시 비밀번호 목록: {creds_path}")
        print("⚠ 이 파일은 배포 후 반드시 삭제하세요!")
    elif credentials and dry_run:
        print("\n[DRY RUN] 실제 생성하려면 --dry-run 없이 실행하세요.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="team_structure.json → Supabase 프로비저닝")
    parser.add_argument("--dry-run", action="store_true", help="실행 없이 미리보기")
    parser.add_argument("--password", default=None, help="공통 임시 비밀번호 (미지정 시 개별 랜덤)")
    args = parser.parse_args()

    asyncio.run(provision(dry_run=args.dry_run, common_password=args.password))


if __name__ == "__main__":
    main()
