#!/usr/bin/env python3
"""
제안 프로젝트 DB 정리 스크립트
- proposals 테이블의 모든 레코드 삭제
- 관련 테이블 (project_participants, artifacts, feedbacks, approvals, compliance_matrix) 자동 삭제
"""

import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
    print("❌ 환경변수 미설정: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY")
    exit(1)

# Service role 클라이언트 (모든 권한)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

try:
    print("[START] Deleting all proposal records...")

    # proposals 테이블의 모든 레코드 삭제
    # ON DELETE CASCADE로 인해 관련 테이블도 자동 삭제됨
    response = supabase.table("proposals").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()

    print("[OK] Proposal deletion completed")
    print(f"     - Deleted records: {len(response.data) if hasattr(response, 'data') else 'N/A'}")

    # 확인: 남은 레코드 수
    count_response = supabase.table("proposals").select("id").execute()
    remaining = len(count_response.data)
    print(f"     - Remaining proposals: {remaining}")

    if remaining == 0:
        print("\n[SUCCESS] All proposal projects deleted. Ready to start fresh!")
    else:
        print(f"\n[WARNING] {remaining} proposals still exist.")

except Exception as e:
    print(f"[ERROR] {e}")
    exit(1)
