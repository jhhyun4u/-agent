#!/usr/bin/env python
"""
Master Projects SQL 마이그레이션 실행 (asyncpg 직접 실행)

Supabase PostgreSQL에 직접 연결해서 마이그레이션 SQL 실행
"""

import asyncio
import logging
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


async def run_sql_file(conn, file_path: str):
    """SQL 파일 실행"""
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # 주석 제거 및 빈 줄 제거
    lines = [line.strip() for line in sql_content.split('\n')
             if line.strip() and not line.strip().startswith('--')]
    sql_content = '\n'.join(lines)

    # 여러 SQL 문으로 분리 (세미콜론 기준)
    statements = [s.strip() for s in sql_content.split(';') if s.strip()]

    logger.info(f"\n실행: {Path(file_path).name}")
    logger.info(f"SQL 문 수: {len(statements)}")

    for i, statement in enumerate(statements, 1):
        if not statement.strip():
            continue

        try:
            logger.info(f"  [{i}/{len(statements)}] {statement[:60]}...")
            await conn.execute(statement)
        except Exception as e:
            error_msg = str(e)
            # 테이블이 이미 존재하는 경우 무시
            if "already exists" in error_msg or "duplicate key" in error_msg:
                logger.info(f"  ⚠ 이미 존재 (무시): {error_msg[:80]}")
            else:
                logger.error(f"  ✗ 오류: {error_msg}")
                raise


async def main():
    import asyncpg
    import ssl
    from app.config import settings

    logger.info("═" * 70)
    logger.info("Master Projects SQL 마이그레이션 시작")
    logger.info("═" * 70)

    if not settings.database_url:
        logger.error("❌ DATABASE_URL이 설정되지 않았습니다.")
        sys.exit(1)

    # Supabase PostgreSQL 연결
    # database_url 형식: postgresql://user:password@host:port/database
    conn = None
    try:
        logger.info(f"✓ 데이터베이스 연결 중...")

        # URL에서 asyncpg 연결 파라미터 추출
        from urllib.parse import urlparse
        parsed = urlparse(settings.database_url)

        # SSL 컨텍스트 생성 (Supabase 자체 서명 인증서 신뢰)
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

        conn = await asyncpg.connect(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            ssl=ssl_context,
            server_settings={'application_name': 'master_projects_migration'}
        )

        logger.info("✓ 데이터베이스 연결 성공")

        # Phase 1: master_projects 테이블 생성
        await run_sql_file(conn, "database/migrations/005_master_projects_table.sql")
        logger.info("✓ Phase 1 완료")

        # Phase 2: 데이터 마이그레이션
        await run_sql_file(conn, "database/migrations/006_migrate_intranet_projects.sql")
        logger.info("✓ Phase 2 완료")

        # Phase 3-7: 관계 설정 및 통계
        await run_sql_file(conn, "database/migrations/007_update_foreign_keys.sql")
        logger.info("✓ Phase 3-7 완료")

        # 검증
        logger.info("\n검증:")

        # master_projects 건수
        mp_count = await conn.fetchval("SELECT COUNT(*) FROM master_projects")
        logger.info(f"✓ master_projects 프로젝트: {mp_count}개")

        # intranet_documents 링크
        doc_count = await conn.fetchval(
            "SELECT COUNT(*) FROM intranet_documents WHERE master_project_id IS NOT NULL"
        )
        logger.info(f"✓ intranet_documents 링크: {doc_count}개")

        # 테이블 구조 확인
        columns = await conn.fetch("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'master_projects'
            ORDER BY ordinal_position
            LIMIT 5
        """)
        logger.info(f"✓ master_projects 테이블 컬럼:")
        for col in columns:
            logger.info(f"    - {col['column_name']}: {col['data_type']}")

        logger.info("\n" + "═" * 70)
        logger.info("✓ 마이그레이션 완료!")
        logger.info("═" * 70)

    except Exception as e:
        logger.error(f"❌ 마이그레이션 실패: {e}", exc_info=True)
        sys.exit(1)

    finally:
        if conn:
            await conn.close()
            logger.info("데이터베이스 연결 종료")


if __name__ == "__main__":
    asyncio.run(main())
