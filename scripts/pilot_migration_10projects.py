#!/usr/bin/env python
"""
파일럿 마이그레이션 스크립트: MSSQL → Supabase (10개 프로젝트)

목표:
1. MSSQL의 Project_List에서 10개 프로젝트 추출
2. Supabase intranet_projects 테이블에 직접 삽입
3. 벡터 임베딩 생성
4. 검색 테스트 (벡터 유사도 검색)
5. 결과 검증

사용법:
    python scripts/pilot_migration_10projects.py --dry-run           # 데이터 조회만
    python scripts/pilot_migration_10projects.py --execute          # 실제 마이그레이션 실행
"""

import argparse
import asyncio
import logging
import os
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import uuid4

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

try:
    import pymssql
    from dotenv import load_dotenv
    from openai import OpenAI
except ImportError as e:
    print(f"필수 패키지 없음: {e}")
    print("pip install pymssql python-dotenv openai")
    sys.exit(1)

# .env 로드
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

# Supabase 클라이언트 (비동기)
# 나중에 import하면 asyncio 루프와 충돌 안 함


# ── 설정 ──

@dataclass
class MSSQLConfig:
    """MSSQL 연결 설정"""
    host: str = os.getenv("MSSQL_HOST", "10.1.3.251")
    user: str = os.getenv("MSSQL_USER", "sa")
    password: str = os.getenv("MSSQL_PASSWORD", "")
    database: str = os.getenv("MSSQL_DATABASE", "intranet")


def extract_keywords(text: str, max_keywords: int = 5) -> list[str]:
    """텍스트에서 도메인 키워드 추출."""
    stopwords = {
        "및", "등", "의", "을", "를", "이", "가", "은", "는", "에", "에서",
        "으로", "로", "과", "와", "대한", "위한", "관한", "따른", "통한",
        "기술", "개발", "사업", "연구", "용역", "수립", "조사", "분석",
        "구축", "운영", "지원", "관리", "서비스", "시스템", "평가",
    }
    if not text:
        return []
    tokens = re.findall(r"[가-힣]{2,}|[A-Za-z]{2,}", text.upper())
    keywords = [t for t in tokens if t.lower() not in {s.lower() for s in stopwords}]
    return keywords[:max_keywords]


def parse_budget(raw: str) -> int:
    """예산 문자열 → 원 단위 정수."""
    if not raw:
        return 0
    cleaned = re.sub(r"[^\d.]", "", str(raw))
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return 0


def parse_date(year, month, day) -> Optional[str]:
    """년월일 → ISO 날짜."""
    try:
        if year and month and day:
            return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
    except (ValueError, TypeError):
        pass
    return None


# ── MSSQL 쿼리 ──

class MSSQLMigrator:
    def __init__(self, config: MSSQLConfig):
        self.config = config
        self.conn = None

    def connect(self) -> pymssql.Connection:
        """MSSQL 연결."""
        logger.info(f"MSSQL 연결: {self.config.host}/{self.config.database}")
        try:
            self.conn = pymssql.connect(
                server=self.config.host,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                charset="utf8",
                tds_version="7.0",
                timeout=30,
            )
            logger.info("MSSQL 연결 성공")
            return self.conn
        except Exception as e:
            logger.error(f"MSSQL 연결 실패: {e}")
            raise

    def fetch_sample_projects(self, limit: int = 10) -> list[dict]:
        """Project_List에서 샘플 프로젝트 추출."""
        if not self.conn:
            self.connect()

        cursor = self.conn.cursor(as_dict=True)
        try:
            sql = f"""
            SELECT TOP {limit}
                idx_no, pr_code, pr_title, pr_com, pr_key,
                pr_start_yy, pr_start_mm, pr_start_dd,
                pr_end_yy, pr_end_mm, pr_end_dd,
                pr_account, pr_status, pr_team, pr_manager,
                pr_com_manager, pr_com_tel, pr_com_email,
                pr_complete, board_id
            FROM Project_List
            WHERE pr_status != 'SKIP'
            ORDER BY pr_start_yy DESC, pr_start_mm DESC
            """
            cursor.execute(sql)
            rows = cursor.fetchall()
            logger.info(f"Project_List에서 {len(rows)}건 조회")
            return rows
        except Exception as e:
            logger.error(f"쿼리 실패: {e}")
            raise
        finally:
            cursor.close()

    def close(self):
        """연결 종료."""
        if self.conn:
            self.conn.close()
            logger.info("MSSQL 연결 종료")


# ── Supabase 삽입 ──

class SupabaseMigrator:
    def __init__(self, org_id: str = "tenopa-default"):
        """Supabase 마이그레이션 초기화."""
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

    async def insert_project(self, row: dict, org_id: str) -> Optional[str]:
        """MSSQL 행 → Supabase intranet_projects 삽입."""
        try:
            # 프로젝트 데이터 변환
            title = (row.get("pr_title") or "").strip()
            client_name = (row.get("pr_com") or "").strip()
            keywords_text = (row.get("pr_key") or "").strip()

            # 키워드 추출
            if keywords_text:
                keywords = [k.strip() for k in re.split(r"[,;/·]", keywords_text) if k.strip()]
            else:
                keywords = extract_keywords(title)

            # 날짜 파싱
            start_date = parse_date(row.get("pr_start_yy"), row.get("pr_start_mm"), row.get("pr_start_dd"))
            end_date = parse_date(row.get("pr_end_yy"), row.get("pr_end_mm"), row.get("pr_end_dd"))

            # 프로젝트 데이터
            project_data = {
                "id": str(uuid4()),
                "org_id": org_id,
                "legacy_idx": row["idx_no"],
                "legacy_code": row.get("pr_code"),
                "project_name": title,
                "client_name": client_name,
                "keywords": keywords,
                "start_date": start_date,
                "end_date": end_date,
                "budget_krw": parse_budget(row.get("pr_account")),
                "manager": (row.get("pr_manager") or "").strip(),
                "team_name": (row.get("pr_team") or "").strip(),
                "status": (row.get("pr_status") or "").strip(),
                "migration_status": "metadata_only",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            # Supabase에 삽입
            result = await self.client.table("intranet_projects").insert(project_data).execute()
            if result.data:
                project_id = result.data[0]["id"]
                logger.info(f"✓ 프로젝트 삽입: {title} (ID: {project_id})")
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
                input=text[:512],  # 512글자 제한
            )
            embedding = response.data[0].embedding

            # Supabase에 업데이트
            await self.client.table("intranet_projects").update({
                "embedding": embedding
            }).eq("id", project_id).execute()

            logger.info(f"✓ 임베딩 생성: {project_id}")
            self.stats["embeddings_created"] += 1
            return embedding

        except Exception as e:
            logger.warning(f"✗ 임베딩 생성 실패: {e}")
            self.stats["embeddings_failed"] += 1
            return None

    async def run_migration(self, rows: list[dict], dry_run: bool = False):
        """마이그레이션 실행."""
        await self.init_client()

        if dry_run:
            logger.info(f"\n[DRY RUN] {len(rows)}개 프로젝트 미리보기:")
            for i, row in enumerate(rows, 1):
                print(f"\n{i}. {row.get('pr_title', 'Unknown')}")
                print(f"   발주처: {row.get('pr_com', 'N/A')}")
                print(f"   예산: {row.get('pr_account', 'N/A')}")
                print(f"   상태: {row.get('pr_status', 'N/A')}")
            return

        # 실제 마이그레이션
        logger.info(f"\n마이그레이션 시작 ({len(rows)}개 프로젝트)")
        for i, row in enumerate(rows, 1):
            logger.info(f"\n[{i}/{len(rows)}] {row.get('pr_title', 'Unknown')}")

            project_id = await self.insert_project(row, self.org_id)
            if project_id:
                title = row.get("pr_title", "")
                client = row.get("pr_com", "")
                text = f"{title} {client}"
                await self.create_embedding(project_id, text)

    def print_summary(self):
        """결과 요약."""
        print("\n" + "="*60)
        print("파일럿 마이그레이션 완료 리포트")
        print("="*60)
        print(f"프로젝트 삽입 성공: {self.stats['projects_inserted']}건")
        print(f"프로젝트 삽입 실패: {self.stats['projects_failed']}건")
        print(f"임베딩 생성: {self.stats['embeddings_created']}건")
        print(f"임베딩 실패: {self.stats['embeddings_failed']}건")
        print("="*60)


# ── 벡터 검색 테스트 ──

async def test_vector_search(project_ids: list[str]):
    """벡터 검색 기능 테스트."""
    logger.info("\n벡터 검색 테스트 시작...")
    from app.utils.supabase_client import get_async_client
    client = await get_async_client()

    test_queries = [
        "AI 기술 개발",
        "데이터 분석 시스템",
        "플랫폼 구축",
    ]

    for query in test_queries:
        logger.info(f"\n검색어: '{query}'")
        try:
            # OpenAI 임베딩 생성
            openai_key = os.getenv("OPENAI_API_KEY")
            if not openai_key:
                logger.warning("OPENAI_API_KEY 미설정 - 검색 테스트 스킵")
                return

            openai_client = OpenAI(api_key=openai_key)
            response = openai_client.embeddings.create(
                model="text-embedding-3-small",
                input=query,
            )
            query_embedding = response.data[0].embedding

            # RPC로 유사도 검색
            results = await client.rpc(
                "search_projects_by_embedding",
                {
                    "query_embedding": query_embedding,
                    "org_id": "tenopa-default",
                    "limit": 5,
                    "similarity_threshold": 0.5,
                }
            ).execute()

            if results.data:
                logger.info(f"  → 검색 결과 {len(results.data)}건")
                for item in results.data:
                    print(f"    • {item.get('project_name', 'N/A')} (유사도: {item.get('similarity', 0):.3f})")
            else:
                logger.info("  → 검색 결과 없음")

        except Exception as e:
            logger.error(f"  ✗ 검색 실패: {e}")


# ── 메인 ──

async def main():
    """메인 함수."""
    parser = argparse.ArgumentParser(description="파일럿 마이그레이션 (10개 프로젝트)")
    parser.add_argument("--dry-run", action="store_true", help="데이터 조회만 (실행 안 함)")
    parser.add_argument("--execute", action="store_true", help="실제 마이그레이션 실행")
    parser.add_argument("--count", type=int, default=10, help="마이그레이션할 프로젝트 수 (기본값: 10)")
    args = parser.parse_args()

    if not args.dry_run and not args.execute:
        parser.print_help()
        print("\n옵션을 지정하세요:")
        print("  --dry-run   : 데이터 조회만 (실행 안 함)")
        print("  --execute   : 실제 마이그레이션 실행")
        return

    # MSSQL 쿼리
    logger.info("MSSQL 데이터 조회 중...")
    migrator = MSSQLMigrator(MSSQLConfig())
    try:
        rows = migrator.fetch_sample_projects(limit=args.count)
        logger.info(f"✓ {len(rows)}개 프로젝트 조회 완료")
    except Exception as e:
        logger.error(f"MSSQL 쿼리 실패: {e}")
        return
    finally:
        migrator.close()

    # Supabase 마이그레이션
    if args.dry_run:
        logger.info("\n━━━ DRY RUN MODE (실제 삽입 없음) ━━━")
        supabase_migrator = SupabaseMigrator()
        await supabase_migrator.run_migration(rows, dry_run=True)
        return

    if args.execute:
        logger.info("\n━━━ EXECUTE MODE (실제 마이그레이션) ━━━")
        supabase_migrator = SupabaseMigrator()
        project_ids = []

        await supabase_migrator.run_migration(rows, dry_run=False)
        supabase_migrator.print_summary()

        # 벡터 검색 테스트
        logger.info("\n벡터 검색 기능 테스트를 위해 삽입된 프로젝트 ID 수집...")
        try:
            from app.utils.supabase_client import get_async_client
            client = await get_async_client()
            result = await client.table("intranet_projects").select("id").eq("org_id", "tenopa-default").limit(10).execute()
            project_ids = [p["id"] for p in result.data]
            logger.info(f"✓ {len(project_ids)}개 프로젝트 ID 수집 완료")

            # 검색 테스트
            await test_vector_search(project_ids)
        except Exception as e:
            logger.error(f"검색 테스트 실패: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\n사용자 중단")
        sys.exit(0)
    except Exception as e:
        logger.error(f"오류: {e}", exc_info=True)
        sys.exit(1)
