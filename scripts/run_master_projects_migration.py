#!/usr/bin/env python
"""
Master Projects Migration Script
=================================

Phase 1: Create master_projects table
Phase 2: Migrate data from intranet_projects
Phase 3: Update foreign keys (intranet_documents, project_archive)
Phase 4: Verify results

사용법:
    python scripts/run_master_projects_migration.py --dry-run    # 검증만
    python scripts/run_master_projects_migration.py --execute    # 실제 실행
"""

import argparse
import asyncio
import logging
from pathlib import Path
from typing import Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


async def run_migration():
    """마이그레이션 실행"""
    try:
        # SQLAlchemy로 직접 DB 연결 (Supabase PostgreSQL)
        from sqlalchemy.ext.asyncio import create_async_engine
        from app.config import settings

        # Supabase PostgreSQL 연결 문자열
        db_url = settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        engine = create_async_engine(db_url, echo=False)

        logger.info("✓ PostgreSQL 클라이언트 초기화 성공")

        # Phase 1: master_projects 테이블 생성
        logger.info("\n" + "="*70)
        logger.info("Phase 1: master_projects 테이블 생성")
        logger.info("="*70)

        async with engine.begin() as conn:
            # 텍스트 기반 SQL 실행
            from sqlalchemy import text

            await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS master_projects (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                org_id UUID NOT NULL,
                project_name TEXT NOT NULL,
                project_year INTEGER,
                start_date DATE,
                end_date DATE,
                client_name TEXT,
                summary TEXT,
                description TEXT,
                budget_krw BIGINT,
                project_type TEXT NOT NULL,
                proposal_status TEXT,
                result_status TEXT,
                execution_status TEXT,
                legacy_idx INTEGER,
                legacy_code TEXT,
                proposal_id UUID REFERENCES proposals(id),
                actual_teams JSONB,
                actual_participants JSONB,
                proposal_teams JSONB,
                proposal_participants JSONB,
                document_count INTEGER DEFAULT 0,
                archive_count INTEGER DEFAULT 0,
                keywords TEXT[],
                embedding vector(1536),
                created_at TIMESTAMPTZ DEFAULT now(),
                updated_at TIMESTAMPTZ DEFAULT now(),
                UNIQUE(org_id, legacy_idx) WHERE project_type = 'historical',
                UNIQUE(proposal_id) WHERE proposal_id IS NOT NULL,
                CHECK (project_type IN ('historical', 'active_proposal', 'completed_proposal')),
                CHECK (proposal_status IN ('DRAFT', 'SUBMITTED', 'RESULT_ANNOUNCED')),
                CHECK (result_status IN ('PENDING', 'WON', 'LOST')),
                CHECK (execution_status IN ('IN_PROGRESS', 'COMPLETED'))
            )
            """))

            await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_master_projects_org ON master_projects(org_id);
            CREATE INDEX IF NOT EXISTS idx_master_projects_type ON master_projects(project_type);
            CREATE INDEX IF NOT EXISTS idx_master_projects_proposal ON master_projects(proposal_id) WHERE proposal_id IS NOT NULL;
            CREATE INDEX IF NOT EXISTS idx_master_projects_year ON master_projects(project_year);
            CREATE INDEX IF NOT EXISTS idx_master_projects_status ON master_projects(proposal_status, result_status, execution_status);
            """))

        logger.info("✓ master_projects 테이블 생성 완료")

        # Phase 2: intranet_projects → master_projects 마이그레이션
        logger.info("\n" + "="*70)
        logger.info("Phase 2: intranet_projects → master_projects 데이터 마이그레이션")
        logger.info("="*70)

        # SQLAlchemy를 통한 데이터 마이그레이션
        phase2_sql = """
        INSERT INTO master_projects (
            id, org_id, project_name, project_year, start_date, end_date,
            client_name, summary, description, budget_krw, project_type,
            proposal_status, result_status, execution_status, legacy_idx,
            legacy_code, proposal_id, actual_teams, actual_participants,
            proposal_teams, proposal_participants, document_count, archive_count,
            keywords, embedding, created_at, updated_at
        )
        SELECT
            id, org_id, pr_title, EXTRACT(YEAR FROM COALESCE(pr_start_date, CURRENT_DATE))::integer,
            pr_start_date, pr_end_date, pr_com, pr_summary, pr_description, pr_budget_krw,
            'historical', 'RESULT_ANNOUNCED', NULL, NULL, idx_no, pr_code, NULL,
            CASE WHEN pr_team IS NOT NULL AND pr_team != ''
                THEN jsonb_build_array(jsonb_build_object('team_id', gen_random_uuid()::text, 'team_name', pr_team))
                ELSE jsonb_build_array()
            END,
            CASE WHEN pr_manager IS NOT NULL AND pr_manager != ''
                THEN jsonb_build_array(jsonb_build_object('name', pr_manager, 'role', 'Manager', 'team_id', gen_random_uuid()::text, 'years_involved', 0))
                ELSE jsonb_build_array()
            END,
            NULL, NULL, 0, 0,
            CASE WHEN pr_key IS NOT NULL AND pr_key != '' THEN STRING_TO_ARRAY(TRIM(BOTH FROM pr_key), ',') ELSE ARRAY[]::text[] END,
            NULL, COALESCE(created_at, CURRENT_TIMESTAMP), COALESCE(updated_at, CURRENT_TIMESTAMP)
        FROM intranet_projects
        WHERE org_id IS NOT NULL
        ON CONFLICT (id) DO NOTHING;
        """

        async with engine.begin() as conn:
            result = await conn.execute(text(phase2_sql))
            rows_inserted = result.rowcount
            logger.info(f"✓ 총 {rows_inserted}개 프로젝트 마이그레이션 완료")

        # Phase 3: intranet_documents → master_project_id 링크
        logger.info("\n" + "="*70)
        logger.info("Phase 3: intranet_documents → master_project_id 링크")
        logger.info("="*70)

        phase3_sql = [
            """ALTER TABLE intranet_documents
               ADD COLUMN IF NOT EXISTS master_project_id UUID REFERENCES master_projects(id) ON DELETE CASCADE;""",
            """CREATE INDEX IF NOT EXISTS idx_intranet_documents_master_project ON intranet_documents(master_project_id);""",
            """UPDATE intranet_documents
               SET master_project_id = mp.id
               FROM master_projects mp
               WHERE intranet_documents.project_id = mp.legacy_idx
                 AND intranet_documents.org_id = mp.org_id
                 AND mp.project_type = 'historical'
                 AND intranet_documents.master_project_id IS NULL;""",
            """UPDATE intranet_documents
               SET storage_path = 'projects/' || master_project_id || '/intranet-documents/' || filename
               WHERE master_project_id IS NOT NULL AND storage_path NOT LIKE 'projects/%';"""
        ]

        async with engine.begin() as conn:
            for sql in phase3_sql:
                await conn.execute(text(sql))
        logger.info("✓ intranet_documents 링크 완료")

        # Phase 4: project_archive → master_project_id 링크
        logger.info("\n" + "="*70)
        logger.info("Phase 4: project_archive → master_project_id 링크")
        logger.info("="*70)

        phase4_sql = [
            """ALTER TABLE project_archive
               ADD COLUMN IF NOT EXISTS master_project_id UUID REFERENCES master_projects(id) ON DELETE CASCADE;""",
            """CREATE INDEX IF NOT EXISTS idx_project_archive_master_project ON project_archive(master_project_id);""",
            """UPDATE project_archive
               SET master_project_id = mp.id
               FROM master_projects mp
               WHERE project_archive.proposal_id = mp.proposal_id
                 AND project_archive.org_id = mp.org_id
                 AND mp.project_type IN ('active_proposal', 'completed_proposal')
                 AND project_archive.master_project_id IS NULL;""",
            """UPDATE project_archive
               SET storage_path = 'projects/' || master_project_id || '/proposal-archive/' || COALESCE(category, 'other') || '/' || filename
               WHERE master_project_id IS NOT NULL AND storage_path NOT LIKE 'projects/%';"""
        ]

        async with engine.begin() as conn:
            for sql in phase4_sql:
                await conn.execute(text(sql))
        logger.info("✓ project_archive 링크 완료")

        # Phase 5: 통계 업데이트
        logger.info("\n" + "="*70)
        logger.info("Phase 5: 문서/산출물 통계 업데이트")
        logger.info("="*70)

        phase5_sql = [
            """UPDATE master_projects mp
               SET document_count = (
                   SELECT COUNT(*) FROM intranet_documents
                   WHERE intranet_documents.master_project_id = mp.id
               )
               WHERE project_type = 'historical' AND document_count = 0;""",
            """UPDATE master_projects mp
               SET archive_count = (
                   SELECT COUNT(*) FROM project_archive
                   WHERE project_archive.master_project_id = mp.id
               )
               WHERE project_type IN ('active_proposal', 'completed_proposal') AND archive_count = 0;"""
        ]

        async with engine.begin() as conn:
            for sql in phase5_sql:
                await conn.execute(text(sql))
        logger.info("✓ 통계 업데이트 완료")

        # Phase 6: 검증
        logger.info("\n" + "="*70)
        logger.info("Phase 6: 마이그레이션 결과 검증")
        logger.info("="*70)

        async with engine.begin() as conn:
            # 마스터 프로젝트 총 건수
            result = await conn.execute(text("SELECT COUNT(*) as cnt FROM master_projects"))
            mp_count = result.scalar()
            logger.info(f"✓ master_projects 총 건수: {mp_count}건")

            # intranet_documents 링크
            result = await conn.execute(text("SELECT COUNT(*) as cnt FROM intranet_documents WHERE master_project_id IS NOT NULL"))
            doc_count = result.scalar()
            logger.info(f"✓ master_project_id 연결된 documents: {doc_count}건")

            # project_archive 링크
            result = await conn.execute(text("SELECT COUNT(*) as cnt FROM project_archive WHERE master_project_id IS NOT NULL"))
            arc_count = result.scalar()
            logger.info(f"✓ master_project_id 연결된 archive: {arc_count}건")

        logger.info("\n" + "="*70)
        logger.info("✓ 마이그레이션 완료!")
        logger.info("="*70)

    except Exception as e:
        logger.error(f"✗ 마이그레이션 실패: {e}", exc_info=True)
        raise


async def main():
    parser = argparse.ArgumentParser(description="Master Projects 마이그레이션")
    parser.add_argument("--dry-run", action="store_true", help="검증만 (실행 안 함)")
    parser.add_argument("--execute", action="store_true", help="실제 마이그레이션 실행")
    args = parser.parse_args()

    if not args.execute and not args.dry_run:
        parser.print_help()
        print("\n옵션을 지정하세요:")
        print("  --dry-run   : 검증만 (실행 안 함)")
        print("  --execute   : 실제 마이그레이션 실행")
        return

    if args.dry_run:
        logger.info("━━━ DRY RUN MODE (검증만) ━━━\n")
        logger.info("마이그레이션 시뮬레이션:")
        logger.info("  Phase 1: master_projects 테이블 생성")
        logger.info("  Phase 2: intranet_projects 데이터 마이그레이션")
        logger.info("  Phase 3: intranet_documents 링크")
        logger.info("  Phase 4: project_archive 링크")
        logger.info("  Phase 5: 통계 업데이트")
        logger.info("  Phase 6: 검증")
        return

    if args.execute:
        logger.info("━━━ EXECUTE MODE (실제 마이그레이션) ━━━\n")
        await run_migration()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n사용자 중단")
    except Exception as e:
        logger.error(f"오류: {e}", exc_info=True)
        exit(1)
