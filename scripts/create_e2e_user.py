"""
E2E test user creation script for Supabase Auth.

Usage:
    uv run python scripts/create_e2e_user.py

Requires: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY in .env
"""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

E2E_EMAIL = os.getenv("E2E_USER_EMAIL", "e2e-test@tenopa.co.kr")
E2E_PASSWORD = os.getenv("E2E_USER_PASSWORD", "e2e-test-password-2026!")


async def main():
    from app.utils.supabase_client import get_async_client

    client = await get_async_client()

    print(f"Creating E2E user: {E2E_EMAIL}")

    # 1) Create auth user
    uid = None
    try:
        res = await client.auth.admin.create_user({
            "email": E2E_EMAIL,
            "password": E2E_PASSWORD,
            "email_confirm": True,
        })
        uid = res.user.id
        print(f"  Auth user created: {uid}")
    except Exception as e:
        err_msg = str(e)
        if "already been registered" in err_msg or "already exists" in err_msg:
            print("  Auth user already exists - looking up ID...")
            users = await client.auth.admin.list_users()
            for u in users:
                if u.email == E2E_EMAIL:
                    uid = u.id
                    break
            if uid:
                print(f"  Found existing user: {uid}")
            else:
                print("  ERROR: could not find user")
                return
        else:
            print(f"  ERROR creating auth user: {e}")
            return

    # 2) Upsert profile (skip FKs that don't exist)
    profile = {
        "id": uid,
        "email": E2E_EMAIL,
        "name": "E2E Test",
        "role": "admin",
        "must_change_password": False,
    }

    for table, col, fk_id in [
        ("organizations", "org_id", "00000000-0000-0000-0000-000000000001"),
        ("divisions", "division_id", "00000000-0000-0000-0001-000000000001"),
        ("teams", "team_id", "00000000-0000-0000-0002-000000000001"),
    ]:
        try:
            check = await client.table(table).select("id").eq("id", fk_id).execute()
            if check.data:
                profile[col] = fk_id
        except Exception:
            pass

    try:
        await client.table("users").upsert(profile).execute()
        print("  Profile upsert OK")
    except Exception as e:
        print(f"  Profile upsert failed (login still works): {e}")

    print("\n=== E2E account ready ===")
    print(f"  Email:    {E2E_EMAIL}")
    print(f"  Password: {E2E_PASSWORD}")
    print("\nAdd to frontend/.env.local:")
    print(f"  E2E_USER_EMAIL={E2E_EMAIL}")
    print(f"  E2E_USER_PASSWORD={E2E_PASSWORD}")


if __name__ == "__main__":
    asyncio.run(main())
