#!/usr/bin/env python
"""
DB 마이그레이션 자동 실행 스크립트

사용법:
    uv run python scripts/apply_migrations.py                  # 모든 미적용 마이그레이션 실행
    uv run python scripts/apply_migrations.py --status         # 마이그레이션 상태 조회
    uv run python scripts/apply_migrations.py --dry-run        # 실제 실행하지 않고 확인만
    uv run python scripts/apply_migrations.py --rollback 019   # 특정 마이그레이션 롤백
"""

import asyncio
import os
import sys
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# .env 로드
from dotenv import load_dotenv
load_dotenv()

# Supabase 클라이언트
from supabase import create_client, Client
import asyncpg

async def get_db_connection():
    """PostgreSQL 직접 연결"""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL 환경변수 설정 필요")

    # SSL 관련 파라미터 제거 (Supabase 풀러에서 문제 발생)
    if "?sslmode=" in db_url:
        db_url = db_url.split("?")[0]

    try:
        # Supabase 풀러 연결 (SSL 안 함)
        conn = await asyncpg.connect(
            db_url,
            timeout=30,
            ssl=False
        )
        return conn
    except asyncpg.exceptions.InternalServerError as e:
        if "Tenant or user not found" in str(e):
            print(f"[ERROR] Supabase 자격증명 오류:")
            print(f"  - DATABASE_URL의 사용자명/비밀번호 확인")
            print(f"  - Supabase 계정 상태 확인")
            print(f"  - .env 파일 설정 확인")
            raise ValueError(f"Supabase 인증 실패: {e}")
        else:
            raise
    except Exception as e:
        print(f"[ERROR] DB 연결 실패: {type(e).__name__}: {e}")
        raise

async def get_applied_migrations(conn) -> set:
    """적용된 마이그레이션 목록 조회"""
    try:
        rows = await conn.fetch(
            "SELECT version FROM migration_history WHERE status = 'success' ORDER BY version"
        )
        return {row['version'] for row in rows}
    except Exception:
        # migration_history 테이블이 없으면 초기화 필요
        return set()

async def get_migration_files() -> list:
    """migration 디렉토리의 모든 .sql 파일 조회"""
    migration_dir = Path(__file__).parent.parent / "database" / "migrations"
    files = sorted(migration_dir.glob("*.sql"))

    # 파일명에서 버전 추출 (e.g., "001_create_tables.sql" -> "001")
    migrations = []
    for f in files:
        version = f.stem.split("_")[0]  # 파일명에서 숫자 부분만 추출
        migrations.append({
            "version": version,
            "filename": f.name,
            "path": f,
            "size": f.stat().st_size
        })

    return migrations

async def read_migration_file(path: Path) -> str:
    """마이그레이션 파일 읽기"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read()

async def apply_migration(conn, version: str, filename: str, sql_content: str, dry_run: bool = False) -> bool:
    """개별 마이그레이션 실행"""
    try:
        print(f"  [{version}] {filename}...", end=" ", flush=True)

        if dry_run:
            print("[DRY-RUN] 실행 예정")
            return True

        start_time = time.time()

        # 마이그레이션 실행
        async with conn.transaction():
            # 각 SQL 문을 분리해서 실행 (; 기준)
            statements = [s.strip() for s in sql_content.split(';') if s.strip()]

            for stmt in statements:
                # 주석 제거
                lines = [l.strip() for l in stmt.split('\n') if not l.strip().startswith('--')]
                clean_stmt = '\n'.join(lines).strip()

                if clean_stmt:
                    await conn.execute(clean_stmt)

            # migration_history에 기록
            await conn.execute(
                """
                INSERT INTO migration_history (version, name, status, execution_time_ms)
                VALUES ($1, $2, 'success', $3)
                ON CONFLICT (version) DO NOTHING
                """,
                version,
                f"{filename}",
                int((time.time() - start_time) * 1000)
            )

        elapsed = time.time() - start_time
        print(f"[OK] {elapsed:.2f}s")
        return True

    except Exception as e:
        print(f"[ERROR] {str(e)[:100]}")

        # 실패 기록
        try:
            await conn.execute(
                """
                INSERT INTO migration_history (version, name, status, error_message)
                VALUES ($1, $2, 'failed', $3)
                ON CONFLICT (version) DO UPDATE SET
                    status = 'failed',
                    error_message = $3
                """,
                version,
                filename,
                str(e)[:500]
            )
        except:
            pass

        return False

async def apply_all_migrations(dry_run: bool = False) -> dict:
    """모든 미적용 마이그레이션 실행"""
    conn = await get_db_connection()

    try:
        # 000_init_migrations 먼저 실행 (migration_history 테이블 생성)
        print("\n[INIT] 마이그레이션 추적 테이블 초기화...")
        migration_files = await get_migration_files()
        init_migration = next((m for m in migration_files if m['version'] == '000'), None)

        if init_migration:
            sql = await read_migration_file(init_migration['path'])
            await apply_migration(conn, '000', init_migration['filename'], sql, dry_run)

        # 적용된 마이그레이션 조회
        applied = await get_applied_migrations(conn)

        # 미적용 마이그레이션 찾기
        pending = [m for m in migration_files if m['version'] not in applied and m['version'] != '000']

        if not pending:
            print("\n[OK] 적용할 마이그레이션이 없습니다")
            return {
                "total": len(migration_files),
                "applied": len(applied),
                "pending": 0,
                "status": "up_to_date"
            }

        print(f"\n[MIGRATION] {len(pending)}개 마이그레이션 적용 예정")
        print("-" * 70)

        success_count = 0
        failed_count = 0

        for migration in pending:
            sql = await read_migration_file(migration['path'])

            # 재시도 로직: 최대 3회, 지수 백오프 (설계 §5.2)
            success = False
            for attempt in range(1, 4):
                success = await apply_migration(
                    conn,
                    migration['version'],
                    migration['filename'],
                    sql,
                    dry_run
                )
                if success:
                    break
                if attempt < 3:
                    wait_sec = 2 ** attempt  # 2s, 4s
                    logger.warning(
                        f"[{migration['version']}] Retry {attempt}/3 after {wait_sec}s"
                    )
                    print(
                        f"  [{migration['version']}] Retry {attempt}/3 — {wait_sec}s 후 재시도..."
                    )
                    await asyncio.sleep(wait_sec)
                else:
                    logger.error(
                        f"[{migration['version']}] Final failure after 3 attempts"
                    )

            if success:
                success_count += 1
            else:
                failed_count += 1

        print("-" * 70)
        print(f"\n[SUMMARY]")
        print(f"  성공: {success_count}개")
        print(f"  실패: {failed_count}개")
        print(f"  총계: {len(migration_files)}개 / 적용됨: {len(applied) + success_count}개")

        return {
            "total": len(migration_files),
            "applied": len(applied) + success_count,
            "failed": failed_count,
            "status": "completed_with_errors" if failed_count > 0 else "completed"
        }

    finally:
        await conn.close()

async def show_migration_status() -> None:
    """마이그레이션 상태 조회"""
    conn = await get_db_connection()

    try:
        # 전체 마이그레이션 파일 조회
        migration_files = await get_migration_files()
        applied = await get_applied_migrations(conn)

        print(f"\n[STATUS] 마이그레이션 현황")
        print("-" * 70)
        print(f"{'버전':<10} {'파일명':<45} {'상태':<15}")
        print("-" * 70)

        for m in migration_files:
            status = "APPLIED" if m['version'] in applied else "PENDING"
            status_color = "✓" if status == "APPLIED" else "•"
            filename = m['filename'][:40]

            print(f"{m['version']:<10} {filename:<45} {status_color} {status:<12}")

        # 통계
        pending_count = len([m for m in migration_files if m['version'] not in applied])

        print("-" * 70)
        print(f"\n통계:")
        print(f"  전체: {len(migration_files)}개")
        print(f"  적용: {len(applied)}개")
        print(f"  대기: {pending_count}개")

        # 최근 적용 마이그레이션
        last = await conn.fetchrow(
            "SELECT version, name, applied_at FROM migration_history WHERE status = 'success' ORDER BY applied_at DESC LIMIT 1"
        )
        if last:
            print(f"  최근: {last['version']} ({last['applied_at'].strftime('%Y-%m-%d %H:%M:%S')})")

    finally:
        await conn.close()

async def main():
    parser = argparse.ArgumentParser(description="DB 마이그레이션 관리")
    parser.add_argument("--status", action="store_true", help="마이그레이션 상태 조회")
    parser.add_argument("--dry-run", action="store_true", help="실행하지 않고 확인만 (실행 예정 목록 표시)")
    parser.add_argument("--rollback", type=str, help="특정 마이그레이션 롤백 (예: 019)")

    args = parser.parse_args()

    try:
        if args.status:
            await show_migration_status()
        elif args.rollback:
            print(f"[INFO] 롤백 기능은 아직 구현되지 않았습니다")
        else:
            result = await apply_all_migrations(dry_run=args.dry_run)
            sys.exit(0 if result["status"] in ["up_to_date", "completed"] else 1)

    except Exception as e:
        print(f"\n[FATAL] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
