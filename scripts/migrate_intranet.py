"""
인트라넷 MSSQL 2000 → 용역제안 Coworker SaaS 마이그레이션 도구

사내 PC(인트라넷 접근 가능)에서 실행.
MSSQL 2000의 Project_List + 파일 서버에서 데이터를 읽어
SaaS API(/api/kb/intranet/*)로 전송한다.

사전 준비:
    pip install pymssql httpx tqdm python-dotenv

사용법:
    python scripts/migrate_intranet.py                        # 전체 마이그레이션
    python scripts/migrate_intranet.py --incremental           # 증분 동기화 (upsert)
    python scripts/migrate_intranet.py --status COMPLETE       # 완료 프로젝트만
    python scripts/migrate_intranet.py --dry-run               # 건수만 확인
    python scripts/migrate_intranet.py --skip-files            # 메타만 (파일 스킵)
    python scripts/migrate_intranet.py --dept-csv mapping.csv  # 부처 매핑 CSV

매월 자동 동기화:
    python scripts/migrate_intranet.py --incremental --triggered-by scheduler

환경 변수 (.env 또는 시스템):
    MSSQL_HOST, MSSQL_USER, MSSQL_PASSWORD, MSSQL_DATABASE
    INTRANET_FILE_ROOT (파일 서버 경로)
    SAAS_API_URL, SAAS_API_TOKEN (관리자 JWT)
"""

import argparse
import asyncio
import csv
import logging
import os
import platform
import re
import sys
from dataclasses import dataclass
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

try:
    import httpx
    import pymssql
    from tqdm import tqdm
except ImportError as e:
    print(f"필수 패키지 없음: {e}")
    print("pip install pymssql httpx tqdm python-dotenv")
    sys.exit(1)

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / "migrate_intranet.env")
except ImportError:
    pass  # dotenv 없이도 시스템 환경 변수로 동작


# ── 파일 슬롯 정의 ──


@dataclass
class FileSlot:
    field_name: str
    doc_type: str
    doc_subtype: str


FILE_SLOTS = [
    FileSlot("file_proposal",    "proposal",     "기술제안서"),
    FileSlot("file_proposal_pt", "presentation", "제안발표자료"),
    FileSlot("file_middle",      "report",       "중간보고서"),
    FileSlot("file_middle_pt",   "presentation", "중간발표자료"),
    FileSlot("file_final",       "report",       "최종보고서"),
    FileSlot("file_final_pt",    "presentation", "최종발표자료"),
    FileSlot("file_summary",     "report",       "요약서"),
    FileSlot("file_contract",    "contract",     "계약서"),
    FileSlot("file_etc01",       "reference",    "기타"),
    FileSlot("file_etc02",       "reference",    "기타"),
]


# ── 설정 ──


class MigrateConfig:
    def __init__(self):
        self.mssql_host = os.getenv("MSSQL_HOST", "localhost")
        self.mssql_user = os.getenv("MSSQL_USER", "sa")
        self.mssql_password = os.getenv("MSSQL_PASSWORD", "")
        self.mssql_database = os.getenv("MSSQL_DATABASE", "intranet")
        self.file_root = Path(os.getenv("INTRANET_FILE_ROOT", r"\\server\upload\intranet"))
        self.api_url = os.getenv("SAAS_API_URL", "http://localhost:8000")
        self.api_token = os.getenv("SAAS_API_TOKEN", "")
        self.board_id = os.getenv("BOARD_ID", "PR_PG")


# ── 키워드 추출 (import_project_history.py에서 가져온 로직) ──

_STOPWORDS = {
    "및", "등", "의", "을", "를", "이", "가", "은", "는", "에", "에서",
    "으로", "로", "과", "와", "대한", "위한", "관한", "따른", "통한",
    "기술", "개발", "사업", "연구", "용역", "수립", "조사", "분석",
    "구축", "운영", "지원", "관리", "서비스", "시스템", "평가",
    "추진", "활용", "방안", "계획", "기반", "강화", "확대",
    "고도화", "개선", "도입", "설계", "제도", "정책", "전략",
    "체계", "플랫폼", "실태", "현황", "보고서", "마련", "수행",
    "과제", "프로젝트", "산업", "기관", "센터", "재단", "진흥원",
    "관련", "분야", "국가", "국내", "종합", "성과", "확보", "신규",
}


def extract_keywords(text: str) -> list[str]:
    """텍스트에서 도메인 키워드 추출."""
    if not text:
        return []
    tokens = re.findall(r"[가-힣]{2,}|[A-Za-z]{2,}", text)
    return [t for t in tokens if t.lower() not in {s.lower() for s in _STOPWORDS} and len(t) >= 2]


def parse_budget(raw: str) -> int:
    """예산 문자열 → 원 단위 정수."""
    if not raw:
        return 0
    cleaned = re.sub(r"[^\d.]", "", str(raw))
    try:
        return int(float(cleaned))
    except (ValueError, TypeError):
        return 0


# ── 마이그레이터 ──


class IntranetMigrator:
    def __init__(self, config: MigrateConfig, dept_map: dict[str, str] | None = None):
        self.config = config
        self.dept_map = dept_map or {}
        self.stats = {
            "projects": 0, "updated": 0, "skipped": 0,
            "files": 0, "file_errors": 0, "total_found": 0,
        }

    def connect_mssql(self):
        """MSSQL 2000 연결."""
        logger.info(f"MSSQL 연결: {self.config.mssql_host}/{self.config.mssql_database}")
        return pymssql.connect(
            server=self.config.mssql_host,
            user=self.config.mssql_user,
            password=self.config.mssql_password,
            database=self.config.mssql_database,
            charset="cp949",
            tds_version="7.0",
        )

    def fetch_projects(self, conn, status_filter: str | None = None) -> list[dict]:
        """Project_List 조회."""
        cursor = conn.cursor(as_dict=True)
        sql = "SELECT TOP 5000 * FROM Project_List WHERE board_id = %s"
        params = [self.config.board_id]
        if status_filter:
            sql += " AND pr_status = %s"
            params.append(status_filter)
        sql += " ORDER BY idx_no"
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        logger.info(f"프로젝트 {len(rows)}건 조회")
        return rows

    def row_to_project_data(self, row: dict) -> dict:
        """MSSQL 행 → API 요청 데이터 변환."""
        title = (row.get("pr_title") or "").strip()
        client = (row.get("pr_com") or "").strip()
        pr_key = (row.get("pr_key") or "").strip()

        # 키워드: pr_key 있으면 파싱, 없으면 제목에서 추출
        if pr_key:
            keywords = [k.strip() for k in re.split(r"[,;/·]", pr_key) if k.strip()]
        else:
            keywords = extract_keywords(title)

        # 날짜 조합
        start_date = end_date = None
        try:
            sy, sm, sd = row.get("pr_start_yy"), row.get("pr_start_mm"), row.get("pr_start_dd")
            if sy and sm and sd:
                start_date = f"{int(sy):04d}-{int(sm):02d}-{int(sd):02d}"
        except (ValueError, TypeError):
            pass
        try:
            ey, em, ed = row.get("pr_end_yy"), row.get("pr_end_mm"), row.get("pr_end_dd")
            if ey and em and ed:
                end_date = f"{int(ey):04d}-{int(em):02d}-{int(ed):02d}"
        except (ValueError, TypeError):
            pass

        budget_text = (row.get("pr_account") or "").strip()

        return {
            "legacy_idx": row["idx_no"],
            "legacy_code": row.get("pr_code"),
            "board_id": row.get("board_id", self.config.board_id),
            "project_name": title,
            "client_name": client,
            "client_manager": (row.get("pr_com_manager") or "").strip(),
            "client_tel": (row.get("pr_com_tel") or "").strip(),
            "client_email": (row.get("pr_com_email") or "").strip(),
            "start_date": start_date,
            "end_date": end_date,
            "budget_text": budget_text,
            "budget_krw": parse_budget(budget_text),
            "manager": (row.get("pr_manager") or "").strip(),
            "attendants": (row.get("pr_attendant") or "").strip(),
            "partner": (row.get("pr_partner") or "").strip(),
            "pm": (row.get("pr_pm") or "").strip(),
            "pm_members": (row.get("pr_pmem") or "").strip(),
            "keywords": keywords,
            "team": (row.get("pr_team") or "").strip(),
            "status": (row.get("pr_status") or "").strip(),
            "inout": (row.get("pr_inout") or "").strip(),
            "progress_pct": row.get("pr_complete") or 0,
            "department": self.dept_map.get(client, ""),
        }

    def find_file(self, row: dict, slot: FileSlot) -> Path | None:
        """파일 슬롯에 해당하는 실제 파일 찾기."""
        base_dir = self.config.file_root / str(row.get("board_id", self.config.board_id))
        if not base_dir.exists():
            return None

        prefix = f"{slot.field_name}_{row['idx_no']}_"
        try:
            for f in base_dir.iterdir():
                if f.name.startswith(prefix) and f.is_file():
                    return f
        except PermissionError:
            logger.warning(f"디렉터리 접근 불가: {base_dir}")
        return None

    async def run(
        self,
        status_filter: str | None = None,
        dry_run: bool = False,
        skip_files: bool = False,
        incremental: bool = False,
        triggered_by: str = "manual",
    ):
        """전체/증분 마이그레이션 실행."""
        conn = self.connect_mssql()
        projects = self.fetch_projects(conn, status_filter)
        conn.close()

        self.stats["total_found"] = len(projects)

        if dry_run:
            print(f"\n[DRY RUN] 프로젝트 {len(projects)}건 발견")
            file_count = 0
            for row in projects:
                for slot in FILE_SLOTS:
                    if self.find_file(row, slot):
                        file_count += 1
            print(f"[DRY RUN] 파일 {file_count}건 발견")
            return

        headers = {"Authorization": f"Bearer {self.config.api_token}"}
        sync_id: str | None = None

        async with httpx.AsyncClient(
            base_url=self.config.api_url,
            headers=headers,
            timeout=120.0,
        ) as http:
            # 동기화 시작 기록
            sync_id = await self._sync_start(
                http, sync_type="incremental" if incremental else "full",
                triggered_by=triggered_by,
            )

            try:
                for row in tqdm(projects, desc="프로젝트 임포트"):
                    data = self.row_to_project_data(row)

                    # 프로젝트 메타 전송 (incremental이면 upsert=true)
                    try:
                        resp = await http.post(
                            "/api/kb/intranet/import-project",
                            json=data,
                            params={"upsert": str(incremental).lower()},
                        )
                        resp.raise_for_status()
                        result = resp.json()
                    except Exception as e:
                        logger.error(f"프로젝트 임포트 실패 [{data['project_name']}]: {e}")
                        continue

                    action = result.get("action")
                    if action == "skipped":
                        self.stats["skipped"] += 1
                        continue
                    elif action == "updated":
                        self.stats["updated"] += 1
                    else:
                        self.stats["projects"] += 1

                    project_id = result["id"]

                    # 파일 업로드
                    if skip_files:
                        continue

                    for slot in FILE_SLOTS:
                        file_path = self.find_file(row, slot)
                        if not file_path:
                            continue

                        try:
                            with open(file_path, "rb") as f:
                                files = {"file": (file_path.name, f)}
                                params = {
                                    "project_id": project_id,
                                    "file_slot": slot.field_name,
                                    "doc_type": slot.doc_type,
                                    "doc_subtype": slot.doc_subtype,
                                }
                                resp = await http.post(
                                    "/api/kb/intranet/upload-file",
                                    params=params,
                                    files=files,
                                )
                                resp.raise_for_status()
                                self.stats["files"] += 1
                        except Exception as e:
                            logger.warning(f"파일 업로드 실패 [{file_path.name}]: {e}")
                            self.stats["file_errors"] += 1

                # 동기화 완료 기록
                await self._sync_complete(http, sync_id, status="completed")

            except Exception as e:
                logger.error(f"동기화 중 오류: {e}")
                if sync_id:
                    await self._sync_complete(
                        http, sync_id, status="failed", error_message=str(e)[:500],
                    )
                raise

        self._print_summary()

    async def _sync_start(self, http: httpx.AsyncClient, sync_type: str, triggered_by: str) -> str | None:
        """SaaS API에 동기화 시작 기록."""
        try:
            resp = await http.post("/api/kb/intranet/sync/start", json={
                "sync_type": sync_type,
                "triggered_by": triggered_by,
                "source_host": platform.node(),
            })
            resp.raise_for_status()
            sync_id = resp.json().get("sync_id")
            logger.info(f"동기화 세션 시작: {sync_id}")
            return sync_id
        except Exception as e:
            logger.warning(f"동기화 시작 기록 실패 (계속 진행): {e}")
            return None

    async def _sync_complete(
        self, http: httpx.AsyncClient, sync_id: str | None,
        status: str = "completed", error_message: str | None = None,
    ):
        """SaaS API에 동기화 완료 기록."""
        if not sync_id:
            return
        try:
            resp = await http.post(f"/api/kb/intranet/sync/{sync_id}/complete", json={
                "status": status,
                "projects_found": self.stats["total_found"],
                "projects_created": self.stats["projects"],
                "projects_updated": self.stats["updated"],
                "projects_skipped": self.stats["skipped"],
                "files_uploaded": self.stats["files"],
                "files_failed": self.stats["file_errors"],
                "error_message": error_message,
            })
            resp.raise_for_status()
            logger.info(f"동기화 세션 완료: {sync_id} ({status})")
        except Exception as e:
            logger.warning(f"동기화 완료 기록 실패: {e}")

    def _print_summary(self):
        """결과 요약 출력."""
        s = self.stats
        print("\n━━━ 마이그레이션 완료 ━━━")
        print(f"전체 발견: {s['total_found']}건")
        print(f"신규 생성: {s['projects']}건 | 업데이트: {s['updated']}건 | 스킵: {s['skipped']}건")
        print(f"파일 업로드: {s['files']}건 (실패: {s['file_errors']}건)")


def load_dept_mapping(csv_path: str | None) -> dict[str, str]:
    """발주처→부처 매핑 CSV 로드."""
    if not csv_path or not Path(csv_path).exists():
        return {}
    mapping = {}
    with open(csv_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            client = (row.get("발주처") or row.get("client") or "").strip()
            dept = (row.get("관련부처") or row.get("department") or "").strip()
            if client and dept:
                mapping[client] = dept
    logger.info(f"부처 매핑 {len(mapping)}건 로드: {csv_path}")
    return mapping


def main():
    parser = argparse.ArgumentParser(description="인트라넷 → SaaS 마이그레이션")
    parser.add_argument("--status", help="프로젝트 상태 필터 (COMPLETE 등)")
    parser.add_argument("--dry-run", action="store_true", help="건수만 확인")
    parser.add_argument("--skip-files", action="store_true", help="파일 업로드 스킵")
    parser.add_argument("--dept-csv", help="발주처→부처 매핑 CSV 경로")
    parser.add_argument(
        "--incremental", action="store_true",
        help="증분 동기화 (기존 프로젝트 업데이트, 신규 추가)",
    )
    parser.add_argument(
        "--triggered-by", default="manual",
        choices=["manual", "scheduler", "api"],
        help="실행 트리거 구분 (동기화 로그 기록용)",
    )
    args = parser.parse_args()

    config = MigrateConfig()
    dept_map = load_dept_mapping(args.dept_csv)
    migrator = IntranetMigrator(config, dept_map)

    asyncio.run(migrator.run(
        status_filter=args.status,
        dry_run=args.dry_run,
        skip_files=args.skip_files,
        incremental=args.incremental,
        triggered_by=args.triggered_by,
    ))


if __name__ == "__main__":
    main()
