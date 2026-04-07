#!/usr/bin/env python3
"""proposals 테이블에 누락된 컬럼 추가

마이그레이션: 013_proposals_missing_columns.sql
- deadline TIMESTAMPTZ
- client_name TEXT
- org_id UUID
- division_id UUID
"""

import sys
from pathlib import Path

def print_migration_sql():
    """Supabase 대시보드에서 수동으로 실행할 SQL 제공"""
    migration_file = Path("database/migrations/013_proposals_missing_columns.sql")

    if not migration_file.exists():
        print(f"ERROR: 마이그레이션 파일을 찾을 수 없습니다: {migration_file}")
        return False

    sql = migration_file.read_text(encoding="utf-8")

    print("\n" + "="*70)
    print("Supabase 대시보드에서 다음 SQL을 실행하세요:")
    print("="*70)
    print("\n1. https://supabase.com/dashboard → SQL Editor 로 이동")
    print("2. 다음 SQL을 복사하여 실행:")
    print("-"*70)
    print(sql)
    print("-"*70)
    print("\n이후 프로포절 생성 시 deadline과 client_name이 DB에 저장됩니다.")
    return True

if __name__ == "__main__":
    if print_migration_sql():
        sys.exit(0)
    else:
        sys.exit(1)
