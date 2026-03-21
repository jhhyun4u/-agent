"""
G2B 파이프라인 운영 모니터링 하네스

4단계 검증 파이프라인:
  L1: 검색 결과 존재 (3개 키워드)
  L2: 결과 정확성 (필드 파싱 검증)
  L3: AI 추천 품질 (자격판정 + 점수)
  L4: E2E 파이프라인 (검색→필터→상세→정규화)

실행:
  uv run python scripts/monitor_g2b_pipeline.py               # 전체 L1~L4
  uv run python scripts/monitor_g2b_pipeline.py --level 1,2    # L1+L2만
  uv run python scripts/monitor_g2b_pipeline.py --notify        # Teams 알림 포함
  uv run python scripts/monitor_g2b_pipeline.py --json          # JSON 출력

크론: 0 8 * * 1-5  uv run python scripts/monitor_g2b_pipeline.py --notify
"""

import argparse
import asyncio
import json
import logging
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal

sys.path.insert(0, ".")

logger = logging.getLogger("g2b_monitor")

# ── 데이터 구조 ─────────────────────────────────────────────

Status = Literal["PASS", "WARN", "FAIL", "SKIP"]

MONITOR_KEYWORDS = ["시스템", "용역", "정보"]
GLOBAL_TIMEOUT = 120  # 초


@dataclass
class CheckResult:
    level: int
    status: Status
    title: str
    details: list[str] = field(default_factory=list)
    elapsed: float = 0.0


@dataclass
class MonitorReport:
    timestamp: str
    results: list[CheckResult] = field(default_factory=list)

    @property
    def overall(self) -> Status:
        statuses = [r.status for r in self.results if r.status != "SKIP"]
        if not statuses:
            return "SKIP"
        if "FAIL" in statuses:
            return "FAIL"
        if "WARN" in statuses:
            return "WARN"
        return "PASS"

    @property
    def summary_counts(self) -> dict[str, int]:
        counts: dict[str, int] = {"PASS": 0, "WARN": 0, "FAIL": 0, "SKIP": 0}
        for r in self.results:
            counts[r.status] += 1
        return counts


# ── L1: 검색 결과 존재 ──────────────────────────────────────

async def check_search_exists() -> CheckResult:
    """L1: 3개 키워드로 검색, 1개 이상 결과 반환 시 PASS."""
    from app.services.g2b_service import G2BService

    result = CheckResult(level=1, status="FAIL", title="검색 결과 존재")
    details = []
    total_found = 0
    t0 = time.monotonic()

    try:
        async with G2BService() as svc:
            for kw in MONITOR_KEYWORDS:
                try:
                    rows = await svc.search_bid_announcements(kw, num_of_rows=20)
                    count = len(rows)
                    total_found += count
                    elapsed_kw = round(time.monotonic() - t0, 1)
                    details.append(f'"{kw}": {count}건 ({elapsed_kw}초)')
                except Exception as e:
                    details.append(f'"{kw}": 오류 — {e}')

        if total_found > 0:
            result.status = "PASS"
        else:
            details.append("전체 0건 — G2B API 장애 또는 키워드 문제 의심")

    except Exception as e:
        details.append(f"G2B 연결 실패: {e}")

    result.elapsed = round(time.monotonic() - t0, 1)
    result.details = details
    return result


# ── L2: 결과 정확성 ─────────────────────────────────────────

def _parse_budget(raw) -> bool:
    """예산 필드가 유효한 숫자로 파싱 가능한지 확인."""
    if not raw:
        return False
    try:
        val = int(str(raw).replace(",", "").strip())
        return val > 0
    except (ValueError, TypeError):
        return False


def _parse_deadline(raw: str) -> bool:
    """마감일 필드가 유효한 날짜 형태인지 확인."""
    if not raw:
        return False
    # 다양한 형식: "2026/03/20 18:00:00", "20260320180000", ISO 등
    cleaned = str(raw).strip()
    return bool(re.match(r"\d{4}[/\-]?\d{2}[/\-]?\d{2}", cleaned))


async def check_result_accuracy(search_results: list[dict] | None = None) -> CheckResult:
    """L2: L1 결과의 필드 파싱 검증. bid_no/제목 90%↑, 예산 80%↑, 마감일 70%↑."""
    result = CheckResult(level=2, status="FAIL", title="결과 정확성")
    t0 = time.monotonic()

    # L1 결과 재사용 or 새로 검색
    if not search_results:
        from app.services.g2b_service import G2BService
        try:
            async with G2BService() as svc:
                search_results = await svc.search_bid_announcements("시스템", num_of_rows=20)
        except Exception as e:
            result.details = [f"검색 실패: {e}"]
            result.elapsed = round(time.monotonic() - t0, 1)
            return result

    if not search_results:
        result.details = ["검증 대상 0건"]
        result.elapsed = round(time.monotonic() - t0, 1)
        return result

    total = len(search_results)

    # 필드 검증
    has_bid_no = sum(1 for r in search_results if r.get("bidNtceNo", "").strip())
    has_title = sum(1 for r in search_results if r.get("bidNtceNm", "").strip())
    has_budget = sum(
        1 for r in search_results
        if _parse_budget(r.get("presmptPrce") or r.get("asignBdgtAmt"))
    )
    has_deadline = sum(
        1 for r in search_results
        if _parse_deadline(r.get("bidClseDt", ""))
    )

    field_rate = round((has_bid_no + has_title) / (total * 2) * 100)
    budget_rate = round(has_budget / total * 100)
    deadline_rate = round(has_deadline / total * 100)

    result.details = [
        f"필드(공고번호+제목) {field_rate}% ({has_bid_no}+{has_title}/{total*2})",
        f"예산 파싱 {budget_rate}% ({has_budget}/{total})",
        f"마감일 파싱 {deadline_rate}% ({has_deadline}/{total})",
    ]

    # 판정
    if field_rate >= 90 and budget_rate >= 80 and deadline_rate >= 70:
        result.status = "PASS"
    elif field_rate < 50 or budget_rate < 50 or deadline_rate < 50:
        result.status = "FAIL"
        result.details.append("필드 검증 50% 미만 항목 존재")
    else:
        result.status = "WARN"
        result.details.append("일부 기준 미달 (정상 범위 내)")

    result.elapsed = round(time.monotonic() - t0, 1)
    return result


# ── L3: AI 추천 품질 ────────────────────────────────────────

async def check_ai_quality(search_results: list[dict] | None = None) -> CheckResult:
    """L3: 2~3건으로 자격판정 + 점수 테스트."""
    from app.models.bid_schemas import BidAnnouncement, TeamBidProfile
    from app.services.bid_recommender import BidRecommender

    result = CheckResult(level=3, status="FAIL", title="AI 추천 품질")
    t0 = time.monotonic()

    # 테스트용 프로필
    test_profile = TeamBidProfile(
        team_id="monitor-test",
        expertise_areas=["SI", "소프트웨어개발", "정보시스템"],
        tech_keywords=["Java", "Python", "클라우드"],
        past_projects="공공 SI 다수 수행",
        company_size="중소기업",
        certifications=["정보통신공사업"],
    )

    # 검색 결과에서 2~3건 추출
    if not search_results:
        from app.services.g2b_service import G2BService
        try:
            async with G2BService() as svc:
                search_results = await svc.search_bid_announcements("시스템", num_of_rows=10)
        except Exception as e:
            result.details = [f"검색 실패: {e}"]
            result.elapsed = round(time.monotonic() - t0, 1)
            return result

    if not search_results:
        result.details = ["분석 대상 0건"]
        result.elapsed = round(time.monotonic() - t0, 1)
        return result

    # BidAnnouncement 변환 (최대 3건)
    test_bids: list[BidAnnouncement] = []
    for raw in search_results[:3]:
        bid_no = raw.get("bidNtceNo", "").strip()
        title = raw.get("bidNtceNm", "").strip()
        agency = raw.get("ntcInsttNm", raw.get("ntceInsttNm", "")).strip()
        if bid_no and title and agency:
            test_bids.append(BidAnnouncement(
                bid_no=bid_no,
                bid_title=title,
                agency=agency,
                content_text=raw.get("ntceSpecCn", "자격요건 정보 없음"),
                qualification_available=True,
            ))

    if not test_bids:
        result.details = ["BidAnnouncement 변환 실패"]
        result.elapsed = round(time.monotonic() - t0, 1)
        return result

    try:
        recommender = BidRecommender()

        # 1단계: 자격판정
        qual_results = await recommender.check_qualifications(test_profile, test_bids)
        qual_ok = all(
            q.qualification_status in ("pass", "fail", "ambiguous")
            for q in qual_results
        )
        result.details.append(f"자격판정 {len(qual_results)}건 (유효: {qual_ok})")

        # 2단계: 점수 산출
        scores = await recommender.score_bids(test_profile, test_bids)
        if scores:
            score_values = [s.match_score for s in scores]
            avg_score = round(sum(score_values) / len(score_values))
            score_range_ok = all(0 <= s <= 100 for s in score_values)
            has_reasons = all(len(s.recommendation_reasons) > 0 for s in scores)
            result.details.append(
                f"점수 {len(scores)}건, 평균 {avg_score} "
                f"(범위 유효: {score_range_ok}, 추천사유: {has_reasons})"
            )

            if qual_ok and score_range_ok and has_reasons:
                result.status = "PASS"
            else:
                result.status = "WARN"
                if not score_range_ok:
                    result.details.append("점수 범위 이상")
                if not has_reasons:
                    result.details.append("추천사유 누락")
        else:
            result.details.append("점수 산출 결과 0건")
            result.status = "WARN"

    except Exception as e:
        result.details.append(f"AI 분석 실패: {e}")
        result.status = "FAIL"

    result.elapsed = round(time.monotonic() - t0, 1)
    return result


# ── L4: E2E 파이프라인 ──────────────────────────────────────

async def check_e2e_pipeline() -> CheckResult:
    """L4: 검색→필터→상세→정규화 전 과정 (DB upsert 제외)."""
    from app.services.bid_fetcher import BidFetcher
    from app.services.g2b_service import G2BService

    result = CheckResult(level=4, status="FAIL", title="E2E 파이프라인")
    t0 = time.monotonic()
    warnings: list[str] = []

    try:
        async with G2BService() as svc:
            # Step 1: 검색
            raw_results = await svc.search_bid_announcements("시스템", num_of_rows=10)
            result.details.append(f"검색: {len(raw_results)}건")
            if not raw_results:
                result.details.append("검색 결과 0건 — 파이프라인 중단")
                result.elapsed = round(time.monotonic() - t0, 1)
                return result

            # Step 2: 정규화 (BidFetcher._normalize 사용, DB 없이)
            fetcher = BidFetcher(g2b_service=svc, supabase_client=None)
            normalized = []
            normalize_fail = 0
            for raw in raw_results[:5]:
                bid = fetcher._normalize(raw)
                if bid:
                    normalized.append(bid)
                else:
                    normalize_fail += 1
            result.details.append(
                f"정규화: {len(normalized)}건 성공, {normalize_fail}건 실패"
            )

            # Step 3: 상세 조회 (최대 2건)
            detail_ok = 0
            detail_fail = 0
            for bid in normalized[:2]:
                try:
                    detail = await svc.get_bid_detail(bid.bid_no)
                    if detail:
                        detail_ok += 1
                    else:
                        detail_fail += 1
                        warnings.append(f"상세 없음: {bid.bid_no}")
                except Exception as e:
                    detail_fail += 1
                    warnings.append(f"상세 실패 {bid.bid_no}: {e}")
            result.details.append(f"상세조회: {detail_ok}건 성공, {detail_fail}건 실패")

        # 판정
        if normalized and detail_fail == 0:
            result.status = "PASS"
        elif normalized and detail_fail > 0:
            result.status = "WARN"
            for w in warnings:
                result.details.append(f"⚠ {w}")
        else:
            result.details.append("정규화 결과 0건 — 파이프라인 이상")

    except Exception as e:
        result.details.append(f"파이프라인 예외: {e}")

    result.elapsed = round(time.monotonic() - t0, 1)
    return result


# ── 리포트 포맷 ─────────────────────────────────────────────

_STATUS_ICON = {"PASS": "✅", "WARN": "⚠️", "FAIL": "❌", "SKIP": "⏭️"}


def format_report_console(report: MonitorReport) -> str:
    """콘솔 리포트 출력."""
    lines = [
        f"{'━'*40}",
        f"  G2B 파이프라인 모니터링 리포트",
        f"  {report.timestamp}",
        f"{'━'*40}",
    ]
    for r in report.results:
        icon = _STATUS_ICON[r.status]
        lines.append(f"[{r.status}] {icon} L{r.level} {r.title}")
        for d in r.details:
            lines.append(f"  {d}")
        if r.elapsed > 0:
            lines.append(f"  ({r.elapsed}초)")
        lines.append("")

    counts = report.summary_counts
    summary_parts = []
    for s in ("PASS", "WARN", "FAIL", "SKIP"):
        if counts[s] > 0:
            summary_parts.append(f"{counts[s]} {s}")
    lines.append(f"{'━'*40}")
    lines.append(f"  결과: {report.overall} ({', '.join(summary_parts)})")
    lines.append(f"{'━'*40}")
    return "\n".join(lines)


def format_report_json(report: MonitorReport) -> str:
    """JSON 리포트 출력."""
    data = {
        "timestamp": report.timestamp,
        "overall": report.overall,
        "counts": report.summary_counts,
        "checks": [
            {
                "level": r.level,
                "status": r.status,
                "title": r.title,
                "details": r.details,
                "elapsed_sec": r.elapsed,
            }
            for r in report.results
        ],
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


# ── Teams 알림 ──────────────────────────────────────────────

async def notify_teams(report: MonitorReport) -> None:
    """FAIL/WARN 시 Teams Adaptive Card 발송."""
    if report.overall == "PASS":
        logger.info("전체 PASS — Teams 알림 생략")
        return

    from app.config import settings

    webhook_url = settings.teams_webhook_url
    if not webhook_url:
        logger.warning("Teams Webhook URL 미설정 — 알림 생략")
        return

    counts = report.summary_counts
    status_icon = "🔴" if report.overall == "FAIL" else "🟡"
    title = f"{status_icon} G2B 모니터링: {report.overall}"
    body_lines = [f"**{report.timestamp}**", ""]
    for r in report.results:
        icon = _STATUS_ICON[r.status]
        body_lines.append(f"{icon} **L{r.level} {r.title}**: {r.status}")
        for d in r.details:
            body_lines.append(f"  - {d}")
    body = "\n".join(body_lines)

    import httpx
    card = {
        "type": "message",
        "attachments": [{
            "contentType": "application/vnd.microsoft.card.adaptive",
            "content": {
                "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
                "type": "AdaptiveCard",
                "version": "1.4",
                "body": [
                    {"type": "TextBlock", "text": title, "weight": "bolder", "size": "medium"},
                    {"type": "TextBlock", "text": body, "wrap": True},
                ],
            },
        }],
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as http:
            resp = await http.post(webhook_url, json=card)
            if resp.status_code == 200:
                logger.info("Teams 알림 발송 완료")
            else:
                logger.warning(f"Teams 알림 실패: {resp.status_code}")
    except Exception as e:
        logger.warning(f"Teams 알림 오류: {e}")


# ── CLI 진입점 ──────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="G2B 파이프라인 모니터링")
    parser.add_argument(
        "--level", type=str, default="1,2,3,4",
        help="실행할 레벨 (예: 1,2 또는 1,2,3,4)",
    )
    parser.add_argument("--notify", action="store_true", help="Teams 알림 발송")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    return parser.parse_args()


async def main():
    args = parse_args()
    levels = {int(x.strip()) for x in args.level.split(",")}

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    report = MonitorReport(timestamp=datetime.now().strftime("%Y-%m-%d %H:%M"))

    # L1 결과를 L2/L3에서 재사용
    l1_search_results: list[dict] | None = None

    try:
        # L1
        if 1 in levels:
            r = await asyncio.wait_for(check_search_exists(), timeout=GLOBAL_TIMEOUT)
            report.results.append(r)
            # L2/L3 용으로 검색 결과 보관
            if r.status != "FAIL":
                from app.services.g2b_service import G2BService
                async with G2BService() as svc:
                    l1_search_results = await svc.search_bid_announcements(
                        "시스템", num_of_rows=20
                    )
        else:
            report.results.append(
                CheckResult(level=1, status="SKIP", title="검색 결과 존재")
            )

        # L2
        if 2 in levels:
            r = await asyncio.wait_for(
                check_result_accuracy(l1_search_results), timeout=GLOBAL_TIMEOUT
            )
            report.results.append(r)
        else:
            report.results.append(
                CheckResult(level=2, status="SKIP", title="결과 정확성")
            )

        # L3
        if 3 in levels:
            r = await asyncio.wait_for(
                check_ai_quality(l1_search_results), timeout=GLOBAL_TIMEOUT
            )
            report.results.append(r)
        else:
            report.results.append(
                CheckResult(level=3, status="SKIP", title="AI 추천 품질")
            )

        # L4
        if 4 in levels:
            r = await asyncio.wait_for(
                check_e2e_pipeline(), timeout=GLOBAL_TIMEOUT
            )
            report.results.append(r)
        else:
            report.results.append(
                CheckResult(level=4, status="SKIP", title="E2E 파이프라인")
            )

    except asyncio.TimeoutError:
        report.results.append(
            CheckResult(level=0, status="FAIL", title="전체 타임아웃",
                        details=[f"{GLOBAL_TIMEOUT}초 초과"])
        )

    # 출력
    if args.json:
        print(format_report_json(report))
    else:
        print(format_report_console(report))

    # Teams 알림
    if args.notify:
        await notify_teams(report)

    # 종료 코드: FAIL=1, WARN=0, PASS=0
    sys.exit(1 if report.overall == "FAIL" else 0)


if __name__ == "__main__":
    asyncio.run(main())
