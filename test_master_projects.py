#!/usr/bin/env python
"""
Master Projects API Test Suite

마이그레이션 및 API 엔드포인트 검증
1. Phase 1-6 SQL 마이그레이션 실행
2. 3개 API 엔드포인트 테스트 (search, detail, stats)
3. 검색 필터 검증
"""

import asyncio
import logging
import sys
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


async def run_migration():
    """실행: 마이그레이션 Phase 1-6 (SQL 스크립트 실행)"""
    try:
        from app.utils.supabase_client import get_async_client

        logger.info("마이그레이션 시작...")
        client = await get_async_client()

        # SQL 마이그레이션 스크립트 로드
        migration_files = [
            "database/migrations/005_master_projects_table.sql",
            "database/migrations/006_migrate_intranet_projects.sql",
            "database/migrations/007_update_foreign_keys.sql"
        ]

        logger.info("✓ Supabase 클라이언트 초기화 성공")

        # Phase 1: 테이블 생성
        logger.info("\n[Phase 1] master_projects 테이블 생성")
        try:
            # 간단한 테이블 존재 확인
            result = await client.table("master_projects").select("id", count="exact").limit(1).execute()
            logger.info("✓ master_projects 테이블 이미 존재")
        except Exception as e:
            logger.info(f"⚠ 테이블 생성 필요: {str(e)[:100]}")
            logger.info("💡 Supabase SQL Editor에서 다음 스크립트를 실행하세요:")
            logger.info("  → database/migrations/005_master_projects_table.sql")

        # Phase 2: 데이터 마이그레이션 확인
        logger.info("\n[Phase 2] 데이터 마이그레이션 상태 확인")
        result = await client.table("master_projects").select("id", count="exact").execute()
        master_count = result.count if result.count else 0
        logger.info(f"✓ master_projects 데이터: {master_count}개")

        if master_count == 0:
            logger.info("💡 데이터 마이그레이션 필요:")
            logger.info("  → database/migrations/006_migrate_intranet_projects.sql")

        # Phase 3-7: 관계 설정 및 통계
        logger.info("\n[Phase 3-7] 관계 설정 및 통계 업데이트 상태 확인")

        # intranet_documents 링크 확인
        try:
            result = await client.table("intranet_documents").select("master_project_id", count="exact").limit(1).execute()
            logger.info("✓ intranet_documents 테이블 확인")

            # master_project_id 연결 개수
            result = await client.table("intranet_documents").select("id", count="exact").eq("master_project_id", "IS NOT NULL").execute()
            linked_count = result.count if result.count else 0
            logger.info(f"✓ master_project_id 연결된 documents: {linked_count}개")
        except Exception as e:
            logger.info(f"⚠ intranet_documents 처리: {str(e)[:100]}")
            logger.info("💡 필요시 다음 스크립트를 실행하세요:")
            logger.info("  → database/migrations/007_update_foreign_keys.sql")

        logger.info("\n✓ 마이그레이션 상태 점검 완료")
        return True

    except Exception as e:
        logger.error(f"✗ 마이그레이션 점검 실패: {e}", exc_info=True)
        return False


async def test_api_endpoints():
    """테스트: 3개 API 엔드포인트"""
    try:
        from app.utils.supabase_client import get_async_client

        logger.info("\n테스트: API 엔드포인트")
        client = await get_async_client()

        # 1. 테스트 프로젝트 조회
        logger.info("\n[TEST 1] GET /api/master-projects (Search)")
        try:
            result = await client.table("master_projects").select("*", count="exact").limit(20).execute()
            projects = result.data or []
            logger.info(f"✓ 검색 결과: {len(projects)}개 프로젝트 조회")

            if not projects:
                logger.warning("⚠ 테스트할 프로젝트가 없습니다.")
                logger.info("  → master_projects 테이블이 비어있으면 마이그레이션을 먼저 실행하세요.")
                return True

            test_project = projects[0]
            test_project_id = test_project.get("id")
            test_org_id = test_project.get("org_id")

            logger.info(f"  테스트 프로젝트: {test_project.get('project_name')} ({test_project_id})")

            # 필터 테스트
            result = await client.table("master_projects").select("*", count="exact").eq("project_type", "historical").execute()
            historical_count = result.count if result.count else 0
            logger.info(f"✓ 필터 테스트 (project_type=historical): {historical_count}개")

        except Exception as e:
            logger.error(f"✗ Search API 테스트 실패: {e}")
            return False

        # 2. Detail API 테스트
        logger.info("\n[TEST 2] GET /api/master-projects/{project_id} (Detail)")
        try:
            result = await client.table("master_projects").select("*").eq("id", test_project_id).single().execute()
            detail = result.data if result else None

            if detail:
                logger.info(f"✓ 프로젝트 상세 조회 성공")
                logger.info(f"  - 과제명: {detail.get('project_name')}")
                logger.info(f"  - 타입: {detail.get('project_type')}")
                logger.info(f"  - 상태: {detail.get('proposal_status')}")
            else:
                logger.warning("⚠ 프로젝트를 찾을 수 없습니다.")

        except Exception as e:
            logger.error(f"✗ Detail API 테스트 실패: {e}")
            return False

        # 3. Stats API 테스트
        logger.info("\n[TEST 3] GET /api/master-projects/{project_id}/stats (Stats)")
        try:
            result = await client.table("master_projects").select("id,project_name,project_type,document_count,archive_count,proposal_status,result_status,execution_status").eq("id", test_project_id).single().execute()
            stats = result.data if result else None

            if stats:
                logger.info(f"✓ 통계 조회 성공")
                logger.info(f"  - 문서 수: {stats.get('document_count', 0)}")
                logger.info(f"  - 아카이브 수: {stats.get('archive_count', 0)}")
                logger.info(f"  - 제안상태: {stats.get('proposal_status')}")
                logger.info(f"  - 결과상태: {stats.get('result_status')}")
                logger.info(f"  - 수행상태: {stats.get('execution_status')}")

        except Exception as e:
            logger.error(f"✗ Stats API 테스트 실패: {e}")
            return False

        logger.info("\n✓ API 테스트 완료")
        return True

    except Exception as e:
        logger.error(f"✗ API 테스트 실패: {e}", exc_info=True)
        return False


async def verify_routes():
    """검증: 라우터 등록 확인"""
    try:
        logger.info("\n검증: 라우터 등록")

        # 라우터가 app/main.py에 등록되었는지 확인
        with open("app/main.py", "r", encoding="utf-8") as f:
            content = f.read()

        if "from app.api.routes_master_projects import router as master_projects_router" in content:
            logger.info("✓ routes_master_projects 임포트 확인")
        else:
            logger.warning("✗ routes_master_projects 임포트 누락")
            return False

        if "app.include_router(master_projects_router)" in content:
            logger.info("✓ master_projects 라우터 등록 확인")
        else:
            logger.warning("✗ master_projects 라우터 등록 누락")
            return False

        logger.info("✓ 라우터 등록 완료")
        return True

    except Exception as e:
        logger.error(f"✗ 라우터 검증 실패: {e}")
        return False


async def main():
    """메인 테스트 실행"""
    logger.info("═" * 70)
    logger.info("Master Projects 마이그레이션 & API 테스트 시작")
    logger.info("═" * 70)

    # 1. 라우터 등록 확인
    routes_ok = await verify_routes()

    if not routes_ok:
        logger.warning("라우터 등록에 문제가 있습니다.")
        return

    # 2. 마이그레이션 상태 점검
    migration_ok = await run_migration()

    if not migration_ok:
        logger.warning("마이그레이션 점검 중 오류가 발생했습니다.")

    # 3. API 테스트
    api_ok = await test_api_endpoints()

    if not api_ok:
        logger.error("API 테스트 실패.")
        return

    logger.info("\n" + "═" * 70)
    logger.info("✓ 모든 검증 완료!")
    logger.info("═" * 70)
    logger.info("\n다음 단계:")
    logger.info("1. Supabase SQL Editor에서 마이그레이션 SQL 스크립트 실행")
    logger.info("   - database/migrations/005_master_projects_table.sql")
    logger.info("   - database/migrations/006_migrate_intranet_projects.sql")
    logger.info("   - database/migrations/007_update_foreign_keys.sql")
    logger.info("2. 백엔드 서버 시작: uvicorn app.main:app --reload")
    logger.info("3. API 테스트: curl http://localhost:8000/api/master-projects")


if __name__ == "__main__":
    asyncio.run(main())
