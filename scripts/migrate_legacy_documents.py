#!/usr/bin/env python3
"""
레거시 문서 마이그레이션 스크립트

인트라넷 문서(intranet_projects) 대량 임포트 및 처리

사용 방법:
  uv run python scripts/migrate_legacy_documents.py
  uv run python scripts/migrate_legacy_documents.py --batch-type manual
  uv run python scripts/migrate_legacy_documents.py --include-failed
"""

import asyncio
import sys
import logging
from typing import Optional
from pathlib import Path
import argparse

# 프로젝트 루트 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import settings
from app.utils.supabase_client import get_async_supabase_client
from app.services.migration_service import MigrationService
from app.services.notification_service import NotificationService


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


async def main(
    batch_type: str = "manual",
    include_failed: bool = False,
    days_back: Optional[int] = None,
) -> int:
    """
    레거시 문서 마이그레이션 실행

    Args:
        batch_type: 배치 유형 (monthly|manual|incremental)
        include_failed: 이전 실패 문서 재처리
        days_back: N일 이전 문서만 마이그레이션 (None=무제한)

    Returns:
        종료 코드 (0=성공, 1=실패)
    """
    try:
        logger.info("=== 레거시 문서 마이그레이션 시작 ===")
        logger.info(f"배치 유형: {batch_type}, 실패 포함: {include_failed}")

        # 1. Supabase 클라이언트 초기화
        db = get_async_supabase_client(service_role=True)
        logger.info("✓ Supabase 클라이언트 초기화 완료")

        # 2. 알림 서비스 초기화 (선택)
        notification_service = None
        if settings.TEAMS_WEBHOOK_URL:
            notification_service = NotificationService(
                teams_webhook_url=settings.TEAMS_WEBHOOK_URL
            )
            logger.info("✓ Teams 알림 서비스 초기화 완료")

        # 3. 마이그레이션 서비스 초기화
        migration_service = MigrationService(
            db=db,
            notification_service=notification_service
        )
        logger.info("✓ 마이그레이션 서비스 초기화 완료")

        # 4. 마이그레이션 실행
        logger.info("📄 인트라넷 문서 배치 임포트 중...")
        batch = await migration_service.batch_import_intranet_documents(
            batch_type=batch_type,
            include_failed=include_failed
        )

        # 5. 결과 출력
        logger.info("=" * 50)
        logger.info("✓ 마이그레이션 완료!")
        logger.info(f"  배치 ID: {batch.id}")
        logger.info(f"  상태: {batch.status}")
        logger.info(f"  처리됨: {batch.processed_documents}건")
        logger.info(f"  실패: {batch.failed_documents}건")
        if batch.error_message:
            logger.warning(f"  에러: {batch.error_message}")
        logger.info("=" * 50)

        # 성공/부분 성공이면 0, 완전 실패면 1
        return 0 if batch.status in ["completed", "partial_failed"] else 1

    except Exception as e:
        logger.error(f"❌ 마이그레이션 실패: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="레거시 인트라넷 문서 마이그레이션"
    )
    parser.add_argument(
        "--batch-type",
        choices=["monthly", "manual", "incremental"],
        default="manual",
        help="배치 유형 (기본값: manual)"
    )
    parser.add_argument(
        "--include-failed",
        action="store_true",
        help="이전 실패 문서도 재처리 (기본값: False)"
    )
    parser.add_argument(
        "--days-back",
        type=int,
        help="N일 이전 문서만 마이그레이션"
    )

    args = parser.parse_args()

    exit_code = asyncio.run(
        main(
            batch_type=args.batch_type,
            include_failed=args.include_failed,
            days_back=args.days_back,
        )
    )
    sys.exit(exit_code)
