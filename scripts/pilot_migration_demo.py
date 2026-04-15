#!/usr/bin/env python
"""
파일럿 마이그레이션 데모 (테스트 데이터)

MSSQL 연결이 불가능한 환경에서 테스트 데이터를 사용하여
Supabase 마이그레이션 및 벡터 검색 기능을 검증하는 데모입니다.

사용법:
    python scripts/pilot_migration_demo.py --dry-run           # 데이터 미리보기만
    python scripts/pilot_migration_demo.py --execute           # 실제 Supabase 삽입 + 검색 테스트
"""

import argparse
import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
except ImportError:
    print("필수 패키지 없음: openai")
    print("pip install openai")
    import sys
    sys.exit(1)


# ── 테스트 데이터 ──

SAMPLE_PROJECTS = [
    {
        "pr_title": "AI 기반 제안서 자동 작성 플랫폼 개발",
        "pr_com": "국방부",
        "pr_key": "AI, NLP, 자동화, 문서생성",
        "pr_account": "500,000,000",
        "pr_status": "COMPLETE",
        "pr_team": "AI팀",
        "pr_manager": "김철수",
    },
    {
        "pr_title": "대용량 데이터 분석 및 시각화 시스템 구축",
        "pr_com": "과학기술정보통신부",
        "pr_key": "빅데이터, 분석, 시각화, 대시보드",
        "pr_account": "750,000,000",
        "pr_status": "COMPLETE",
        "pr_team": "데이터팀",
        "pr_manager": "이영희",
    },
    {
        "pr_title": "클라우드 기반 IoT 플랫폼 설계 및 구현",
        "pr_com": "환경부",
        "pr_key": "IoT, 클라우드, 실시간 모니터링",
        "pr_account": "1,200,000,000",
        "pr_status": "COMPLETE",
        "pr_team": "클라우드팀",
        "pr_manager": "박준호",
    },
    {
        "pr_title": "고급 보안 시스템 취약점 분석 및 개선",
        "pr_com": "방위사업청",
        "pr_key": "보안, 취약점분석, 암호화, 인증",
        "pr_account": "350,000,000",
        "pr_status": "COMPLETE",
        "pr_team": "보안팀",
        "pr_manager": "최민수",
    },
    {
        "pr_title": "스마트 시티 통합 관리 솔루션 개발",
        "pr_com": "국토교통부",
        "pr_key": "스마트시티, IoT, 통합관리",
        "pr_account": "2,000,000,000",
        "pr_status": "COMPLETE",
        "pr_team": "솔루션팀",
        "pr_manager": "정수영",
    },
    {
        "pr_title": "머신러닝 기반 수요 예측 모델 개발",
        "pr_com": "중소벤처기업부",
        "pr_key": "머신러닝, 예측, 수요분석",
        "pr_account": "600,000,000",
        "pr_status": "COMPLETE",
        "pr_team": "AI팀",
        "pr_manager": "김철수",
    },
    {
        "pr_title": "연방 학습 기반 의료 진단 시스템",
        "pr_com": "보건복지부",
        "pr_key": "연방학습, 의료AI, 진단",
        "pr_account": "1,500,000,000",
        "pr_status": "COMPLETE",
        "pr_team": "AI팀",
        "pr_manager": "이영희",
    },
    {
        "pr_title": "엣지 컴퓨팅 프레임워크 설계",
        "pr_com": "과학기술정보통신부",
        "pr_key": "엣지컴퓨팅, 분산처리, 실시간",
        "pr_account": "800,000,000",
        "pr_status": "COMPLETE",
        "pr_team": "클라우드팀",
        "pr_manager": "박준호",
    },
    {
        "pr_title": "자동화된 컴플라이언스 검사 플랫폼",
        "pr_com": "금융위원회",
        "pr_key": "컴플라이언스, 자동화, 규제",
        "pr_account": "400,000,000",
        "pr_status": "COMPLETE",
        "pr_team": "솔루션팀",
        "pr_manager": "정수영",
    },
    {
        "pr_title": "블록체인 기반 공급망 추적 시스템",
        "pr_com": "산업통상자원부",
        "pr_key": "블록체인, 공급망, 투명성",
        "pr_account": "900,000,000",
        "pr_status": "COMPLETE",
        "pr_team": "보안팀",
        "pr_manager": "최민수",
    },
]


# ── 마이그레이션 ──

class SupabaseMigrator:
    def __init__(self, org_id: str = None):
        """Supabase 마이그레이션 초기화."""
        # org_id는 UUID 타입이어야 함 - 환경변수에서 읽거나 기본값 사용
        if org_id is None:
            org_id = os.getenv("TENOPA_ORG_ID", "b92b8f14-f0d2-4d9e-a6c8-a5b0ec1dd114")  # TENOPA organization
        self.org_id = org_id
        self.client = None
        self.stats = {
            "projects_inserted": 0,
            "projects_failed": 0,
            "embeddings_created": 0,
            "embeddings_failed": 0,
        }

    async def init_client(self):
        """Supabase 클라이언트 초기화."""
        try:
            from app.utils.supabase_client import get_async_client
            self.client = await get_async_client()
            logger.info("Supabase 클라이언트 초기화 완료")
        except Exception as e:
            logger.error(f"Supabase 클라이언트 초기화 실패: {e}")
            raise

    async def insert_project(self, idx: int, row: dict, org_id: str) -> Optional[str]:
        """프로젝트 데이터 → Supabase 삽입."""
        try:
            title = row.get("pr_title", "").strip()
            client_name = row.get("pr_com", "").strip()
            keywords_text = row.get("pr_key", "").strip()

            # 키워드
            if keywords_text:
                keywords = [k.strip() for k in keywords_text.split(",") if k.strip()]
            else:
                keywords = []

            # 예산 파싱
            budget_text = row.get("pr_account", "").strip()
            budget_krw = 0
            if budget_text:
                import re
                cleaned = re.sub(r"[^\d.]", "", budget_text)
                try:
                    budget_krw = int(float(cleaned))
                except (ValueError, TypeError):
                    pass

            # 프로젝트 데이터
            project_data = {
                "id": str(uuid4()),
                "org_id": org_id,
                "legacy_idx": idx,
                "legacy_code": f"PR_{idx:05d}",
                "project_name": title,
                "client_name": client_name,
                "keywords": keywords,
                "budget_krw": budget_krw,
                "manager": row.get("pr_manager", "").strip(),
                "status": row.get("pr_status", "").strip(),
                "migration_status": "metadata_only",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            # Supabase에 삽입
            result = await self.client.table("intranet_projects").insert(project_data).execute()
            if result.data:
                project_id = result.data[0]["id"]
                logger.info(f"✓ 프로젝트 삽입: {title} (ID: {project_id[:8]}...)")
                self.stats["projects_inserted"] += 1
                return project_id
            else:
                logger.error(f"✗ 프로젝트 삽입 실패: {title}")
                self.stats["projects_failed"] += 1
                return None

        except Exception as e:
            logger.error(f"✗ 프로젝트 처리 실패 [{row.get('pr_title', 'Unknown')}]: {e}")
            self.stats["projects_failed"] += 1
            return None

    async def create_embedding(self, project_id: str, text: str) -> Optional[list[float]]:
        """텍스트 임베딩 생성 (OpenAI)."""
        try:
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                logger.warning("OPENAI_API_KEY 미설정 - 임베딩 생성 스킵")
                return None

            client = OpenAI(api_key=openai_key)
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=text[:512],
            )
            embedding = response.data[0].embedding

            # Supabase에 업데이트
            await self.client.table("intranet_projects").update({
                "embedding": embedding
            }).eq("id", project_id).execute()

            logger.info(f"  ✓ 임베딩 생성")
            self.stats["embeddings_created"] += 1
            return embedding

        except Exception as e:
            logger.warning(f"  ✗ 임베딩 생성 실패: {e}")
            self.stats["embeddings_failed"] += 1
            return None

    async def run_migration(self, rows: list[dict], dry_run: bool = False):
        """마이그레이션 실행."""
        await self.init_client()

        if dry_run:
            logger.info(f"\n[DRY RUN] {len(rows)}개 프로젝트 미리보기:\n")
            for i, row in enumerate(rows, 1):
                print(f"{i:2d}. {row.get('pr_title', 'Unknown')}")
                print(f"      발주처: {row.get('pr_com', 'N/A')}")
                print(f"      예산: {row.get('pr_account', 'N/A')}")
                print(f"      팀: {row.get('pr_team', 'N/A')}")
                print()
            return

        # 실제 마이그레이션
        logger.info(f"\n마이그레이션 시작 ({len(rows)}개 프로젝트)\n")
        for i, row in enumerate(rows, 1):
            logger.info(f"[{i}/{len(rows)}] {row.get('pr_title', 'Unknown')}")

            project_id = await self.insert_project(i, row, self.org_id)
            if project_id:
                title = row.get("pr_title", "")
                client = row.get("pr_com", "")
                text = f"{title} {client}"
                await self.create_embedding(project_id, text)

    def print_summary(self):
        """결과 요약."""
        print("\n" + "="*70)
        print("파일럿 마이그레이션 완료 리포트".center(70))
        print("="*70)
        print(f"프로젝트 삽입 성공: {self.stats['projects_inserted']}건")
        print(f"프로젝트 삽입 실패: {self.stats['projects_failed']}건")
        print(f"임베딩 생성: {self.stats['embeddings_created']}건")
        print(f"임베딩 실패: {self.stats['embeddings_failed']}건")
        print("="*70)


# ── 벡터 검색 테스트 ──

async def test_vector_search(org_id: str = None):
    """벡터 검색 기능 테스트."""
    if org_id is None:
        org_id = os.getenv("TENOPA_ORG_ID", "b92b8f14-f0d2-4d9e-a6c8-a5b0ec1dd114")

    logger.info("\n" + "="*70)
    logger.info("벡터 검색 기능 테스트".center(70))
    logger.info("="*70 + "\n")

    from app.utils.supabase_client import get_async_client
    client = await get_async_client()

    test_queries = [
        ("AI 플랫폼", "AI 기반 자동화 기술"),
        ("데이터 분석", "빅데이터 처리 및 분석"),
        ("클라우드", "클라우드 기반 시스템"),
    ]

    for query_text, description in test_queries:
        logger.info(f"검색어: '{query_text}' ({description})")
        try:
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                logger.warning("  ✗ OPENAI_API_KEY 미설정 - 검색 테스트 스킵")
                continue

            openai_client = OpenAI(api_key=openai_key)
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=query_text,
            )
            query_embedding = response.data[0].embedding

            # RPC로 유사도 검색
            results = await client.rpc(
                "search_projects_by_embedding",
                {
                    "query_embedding": query_embedding,
                    "org_id": org_id,
                    "limit": 3,
                    "similarity_threshold": 0.5,
                }
            ).execute()

            if results.data:
                logger.info(f"  ✓ 검색 결과 {len(results.data)}건:\n")
                for j, item in enumerate(results.data, 1):
                    similarity = item.get('similarity', 0)
                    project_name = item.get('project_name', 'N/A')
                    print(f"     {j}. {project_name}")
                    print(f"        유사도: {similarity:.3f}\n")
            else:
                logger.info("  ✗ 검색 결과 없음")

        except Exception as e:
            logger.error(f"  ✗ 검색 실패: {e}")

        logger.info("")


# ── 메인 ──

async def main():
    """메인 함수."""
    parser = argparse.ArgumentParser(description="파일럿 마이그레이션 데모 (테스트 데이터)")
    parser.add_argument("--dry-run", action="store_true", help="데이터 조회만 (실행 안 함)")
    parser.add_argument("--execute", action="store_true", help="실제 마이그레이션 실행 + 검색 테스트")
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        parser.print_help()
        print("\n옵션을 지정하세요:")
        print("  --dry-run   : 데이터 조회만 (실행 안 함)")
        print("  --execute   : 실제 마이그레이션 실행 + 검색 테스트")
        return

    # Supabase 마이그레이션
    migrator = SupabaseMigrator()

    if args.dry_run:
        logger.info("━━━ DRY RUN MODE (실제 삽입 없음) ━━━")
        await migrator.run_migration(SAMPLE_PROJECTS, dry_run=True)
        return

    if args.execute:
        logger.info("━━━ EXECUTE MODE (실제 마이그레이션) ━━━")
        await migrator.run_migration(SAMPLE_PROJECTS, dry_run=False)
        migrator.print_summary()

        # 벡터 검색 테스트
        await test_vector_search(migrator.org_id)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n사용자 중단")
        import sys
        sys.exit(0)
    except Exception as e:
        logger.error(f"오류: {e}", exc_info=True)
        import sys
        sys.exit(1)
