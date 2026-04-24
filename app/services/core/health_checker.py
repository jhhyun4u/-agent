"""
플랫폼 자가검증 시스템 — 검증 엔진 + 15개 체크 항목

스케줄:
- 인프라 (I-1~I-3): 매 5분
- 데이터 정합성 (D-1~D-5): 매 30분
- 외부 서비스 (E-1~E-3): 매 1시간
- API 스모크 (A-1~A-4): 매 1시간
"""

import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Literal

from app.config import settings
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

CheckStatus = Literal["pass", "warn", "fail", "fixed"]
CheckCategory = Literal["infra", "data", "external", "api"]

_CATEGORY_PREFIX = {"infra": "I", "data": "D", "external": "E", "api": "A"}


@dataclass
class HealthResult:
    """단일 검증 결과"""
    check_id: str
    category: CheckCategory
    status: CheckStatus
    message: str
    detail: dict = field(default_factory=dict)
    auto_recovered: bool = False
    duration_ms: float = 0.0


class HealthCheckRunner:
    """검증 항목 등록 + 실행 엔진"""

    def __init__(self):
        self._checks: dict[str, tuple[CheckCategory, Callable]] = {}
        self._register_all()

    def _register_all(self):
        # 인프라
        self._reg("I-1", "infra", self._check_db_connection)
        self._reg("I-2", "infra", self._check_storage)
        self._reg("I-3", "infra", self._check_resources)
        # 데이터 정합성
        self._reg("D-1", "data", self._check_stale_days_remaining)
        self._reg("D-2", "data", self._check_orphan_recommendations)
        self._reg("D-3", "data", self._check_stale_sessions)
        self._reg("D-4", "data", self._check_mv_freshness)
        self._reg("D-5", "data", self._check_cache_db_sync)
        # 외부 서비스
        self._reg("E-1", "external", self._check_g2b_api)
        self._reg("E-2", "external", self._check_claude_api)
        self._reg("E-3", "external", self._check_teams_webhook)
        # API 스모크
        self._reg("A-1", "api", self._check_health_endpoint)
        self._reg("A-2", "api", self._check_monitor_endpoint)
        self._reg("A-3", "api", self._check_scored_endpoint)
        self._reg("A-4", "api", self._check_proposals_endpoint)

    def _reg(self, check_id: str, cat: CheckCategory, func: Callable):
        self._checks[check_id] = (cat, func)

    async def run_category(self, category: CheckCategory) -> list[HealthResult]:
        prefix = _CATEGORY_PREFIX[category]
        targets = {k: v for k, v in self._checks.items() if k.startswith(prefix)}
        return await self._run_many(targets)

    async def run_all(self) -> list[HealthResult]:
        return await self._run_many(self._checks)

    async def run_single(self, check_id: str) -> HealthResult:
        entry = self._checks.get(check_id)
        if not entry:
            return HealthResult(check_id, "infra", "fail", f"알 수 없는 체크: {check_id}")
        cat, func = entry
        return await self._run_one(check_id, cat, func)

    async def _run_many(self, targets: dict) -> list[HealthResult]:
        results = []
        for check_id, (cat, func) in targets.items():
            results.append(await self._run_one(check_id, cat, func))
        return results

    async def _run_one(self, check_id: str, cat: CheckCategory, func: Callable) -> HealthResult:
        start = time.monotonic()
        try:
            result = await func()
        except Exception as e:
            logger.warning(f"[Health] {check_id} 예외: {e}")
            result = HealthResult(check_id, cat, "fail", f"예외: {type(e).__name__}: {e}")
        result.duration_ms = round((time.monotonic() - start) * 1000, 1)
        return result

    # ════════════════════════════════════════════
    # I: 인프라
    # ════════════════════════════════════════════

    async def _check_db_connection(self) -> HealthResult:
        """I-1: DB 연결 확인. 실패 시 연결 풀 재생성."""
        try:
            client = await get_async_client()
            await client.table("organizations").select("id").limit(1).execute()
            return HealthResult("I-1", "infra", "pass", "DB 연결 정상")
        except Exception as e:
            try:
                from app.utils.supabase_client import reset_client
                await reset_client()
                client = await get_async_client()
                await client.table("organizations").select("id").limit(1).execute()
                return HealthResult("I-1", "infra", "fixed", f"DB 재연결 성공 (원인: {e})", auto_recovered=True)
            except Exception as e2:
                return HealthResult("I-1", "infra", "fail", f"DB 연결 실패 + 복구 실패: {e2}")

    async def _check_storage(self) -> HealthResult:
        """I-2: Supabase Storage 버킷 접근 확인"""
        try:
            client = await get_async_client()
            buckets = await client.storage.list_buckets()
            expected = {settings.storage_bucket_proposals, settings.storage_bucket_attachments}
            found = {b.name for b in buckets} if buckets else set()
            missing = expected - found
            if missing:
                return HealthResult("I-2", "infra", "warn", f"버킷 누락: {missing}", detail={"missing": list(missing)})
            return HealthResult("I-2", "infra", "pass", f"Storage 정상 ({len(found)}개 버킷)")
        except Exception as e:
            return HealthResult("I-2", "infra", "fail", f"Storage 접근 실패: {e}")

    async def _check_resources(self) -> HealthResult:
        """I-3: 메모리/CPU (psutil 선택적)"""
        try:
            import psutil
        except ImportError:
            return HealthResult("I-3", "infra", "pass", "psutil 미설치 — 체크 스킵")

        mem = psutil.virtual_memory()
        cpu = psutil.cpu_percent(interval=0.5)
        detail = {"memory_percent": mem.percent, "cpu_percent": cpu}
        warn_pct = settings.health_resource_warn_pct
        fail_pct = settings.health_resource_fail_pct

        if mem.percent > fail_pct or cpu > fail_pct:
            return HealthResult("I-3", "infra", "fail", f"리소스 위험: mem={mem.percent}% cpu={cpu}%", detail=detail)
        if mem.percent > warn_pct or cpu > warn_pct:
            return HealthResult("I-3", "infra", "warn", f"리소스 주의: mem={mem.percent}% cpu={cpu}%", detail=detail)
        return HealthResult("I-3", "infra", "pass", f"리소스 정상: mem={mem.percent}% cpu={cpu}%", detail=detail)

    # ════════════════════════════════════════════
    # D: 데이터 정합성
    # ════════════════════════════════════════════

    async def _check_stale_days_remaining(self) -> HealthResult:
        """D-1: deadline < now인데 days_remaining > 0인 공고 → 재계산"""
        client = await get_async_client()
        now_iso = datetime.now(timezone.utc).isoformat()

        stale = await (
            client.table("bid_announcements")
            .select("bid_no, deadline_date", count="exact")
            .lt("deadline_date", now_iso)
            .gt("days_remaining", 0)
            .limit(500)
            .execute()
        )
        count = stale.count or 0
        if count == 0:
            return HealthResult("D-1", "data", "pass", "days_remaining 정합성 정상")

        today = datetime.now(timezone.utc).date()
        fixed = 0
        for row in (stale.data or []):
            try:
                dl = datetime.fromisoformat(str(row["deadline_date"]).replace("Z", "+00:00")).date()
                await (
                    client.table("bid_announcements")
                    .update({"days_remaining": (dl - today).days})
                    .eq("bid_no", row["bid_no"])
                    .execute()
                )
                fixed += 1
            except Exception:
                pass

        return HealthResult(
            "D-1", "data", "fixed",
            f"days_remaining 불일치 {count}건 → {fixed}건 재계산",
            detail={"found": count, "fixed": fixed},
            auto_recovered=True,
        )

    async def _check_orphan_recommendations(self) -> HealthResult:
        """D-2: bid_recommendations에 공고 없는 고아 레코드 → 삭제"""
        client = await get_async_client()
        recs = await client.table("bid_recommendations").select("bid_no").execute()
        anns = await client.table("bid_announcements").select("bid_no").execute()

        rec_nos = {r["bid_no"] for r in (recs.data or [])}
        ann_nos = {a["bid_no"] for a in (anns.data or [])}
        orphans = rec_nos - ann_nos

        if not orphans:
            return HealthResult("D-2", "data", "pass", "고아 추천 레코드 없음")

        deleted = 0
        for bid_no in list(orphans)[:100]:
            try:
                await client.table("bid_recommendations").delete().eq("bid_no", bid_no).execute()
                deleted += 1
            except Exception:
                pass

        return HealthResult(
            "D-2", "data", "fixed",
            f"고아 추천 레코드 {len(orphans)}건 → {deleted}건 삭제",
            detail={"orphan_count": len(orphans), "deleted": deleted},
            auto_recovered=True,
        )

    async def _check_stale_sessions(self) -> HealthResult:
        """D-3: running 상태에서 2시간 이상 미갱신 → stale 전환"""
        client = await get_async_client()
        cutoff = (datetime.now(timezone.utc) - timedelta(hours=settings.health_stale_session_hours)).isoformat()

        stale = await (
            client.table("proposals")
            .select("id", count="exact")
            .eq("status", "running")
            .lt("updated_at", cutoff)
            .limit(0)
            .execute()
        )
        count = stale.count or 0
        if count == 0:
            return HealthResult("D-3", "data", "pass", "Stale 세션 없음")

        await (
            client.table("proposals")
            .update({"status": "stale"})
            .eq("status", "running")
            .lt("updated_at", cutoff)
            .execute()
        )
        return HealthResult(
            "D-3", "data", "fixed",
            f"Stale 세션 {count}건 → 'stale' 전환",
            detail={"count": count},
            auto_recovered=True,
        )

    async def _check_mv_freshness(self) -> HealthResult:
        """D-4: MV 갱신 경과 시간 확인 → 24시간 초과 시 REFRESH"""
        client = await get_async_client()
        try:
            res = await client.rpc("check_mv_freshness").execute()
            hours_since = (res.data or {}).get("hours_since_refresh", 999)
        except Exception:
            hours_since = 999

        max_hours = settings.health_mv_max_hours
        if hours_since <= max_hours:
            return HealthResult("D-4", "data", "pass", f"MV 갱신 {hours_since}시간 전")

        try:
            await client.rpc("refresh_performance_views").execute()
            return HealthResult(
                "D-4", "data", "fixed",
                f"MV {hours_since}시간 경과 → 갱신 완료",
                auto_recovered=True,
            )
        except Exception as e:
            return HealthResult("D-4", "data", "warn", f"MV 갱신 RPC 미등록 또는 실패: {e}")

    async def _check_cache_db_sync(self) -> HealthResult:
        """D-5: data/bid_status/*.json ↔ DB proposal_status 불일치 → DB 기준 동기화"""
        status_dir = Path("data/bid_status")
        if not status_dir.exists():
            return HealthResult("D-5", "data", "pass", "파일 캐시 디렉토리 없음")

        client = await get_async_client()
        files = list(status_dir.glob("*.json"))[:200]
        mismatches = 0

        for f in files:
            try:
                cached = json.loads(f.read_text(encoding="utf-8"))
                bid_no = cached.get("bid_no") or f.stem
                db_res = await (
                    client.table("bid_announcements")
                    .select("proposal_status")
                    .eq("bid_no", bid_no)
                    .maybe_single()
                    .execute()
                )
                db_status = (db_res.data or {}).get("proposal_status")
                if db_status and db_status != cached.get("status"):
                    cached["status"] = db_status
                    f.write_text(json.dumps(cached, ensure_ascii=False), encoding="utf-8")
                    mismatches += 1
            except Exception:
                pass

        if mismatches == 0:
            return HealthResult("D-5", "data", "pass", f"캐시-DB 동기화 정상 ({len(files)}건 검사)")

        return HealthResult(
            "D-5", "data", "fixed",
            f"캐시-DB 불일치 {mismatches}건 → DB 기준 동기화",
            detail={"checked": len(files), "fixed": mismatches},
            auto_recovered=True,
        )

    # ════════════════════════════════════════════
    # E: 외부 서비스
    # ════════════════════════════════════════════

    async def _check_g2b_api(self) -> HealthResult:
        """E-1: G2B API 접근 확인"""
        if not settings.g2b_api_key:
            return HealthResult("E-1", "external", "warn", "G2B API 키 미설정")
        try:
            from app.services.domains.bidding.g2b_service import G2BService
            async with G2BService() as g2b:
                result = await g2b.search_bids(keyword="정보시스템", num_of_rows=1)
            if result:
                return HealthResult("E-1", "external", "pass", "G2B API 정상")
            return HealthResult("E-1", "external", "warn", "G2B API 응답 있으나 결과 0건")
        except Exception as e:
            return HealthResult("E-1", "external", "fail", f"G2B API 오류: {e}")

    async def _check_claude_api(self) -> HealthResult:
        """E-2: Claude API 키 형식 확인 (실제 호출 X → 비용 절약)"""
        if not settings.anthropic_api_key:
            return HealthResult("E-2", "external", "fail", "Anthropic API 키 미설정")
        key = settings.anthropic_api_key
        if not key.startswith("sk-ant-"):
            return HealthResult("E-2", "external", "warn", "API 키 형식 의심 (sk-ant- prefix 없음)")
        return HealthResult("E-2", "external", "pass", "Claude API 키 설정됨 (형식 정상)")

    async def _check_teams_webhook(self) -> HealthResult:
        """E-3: Teams Webhook URL 접근 확인 (메시지 전송 X)"""
        if not settings.teams_webhook_url:
            return HealthResult("E-3", "external", "warn", "Teams Webhook URL 미설정")
        try:
            import httpx
            async with httpx.AsyncClient(timeout=10) as http:
                resp = await http.head(settings.teams_webhook_url)
            if resp.status_code < 500:
                return HealthResult("E-3", "external", "pass", f"Teams Webhook 접근 가능 (HTTP {resp.status_code})")
            return HealthResult("E-3", "external", "fail", f"Teams Webhook 서버 오류 (HTTP {resp.status_code})")
        except Exception as e:
            return HealthResult("E-3", "external", "fail", f"Teams Webhook 접근 불가: {e}")

    # ════════════════════════════════════════════
    # A: API 스모크 테스트 (내부 함수 직접 호출)
    # ════════════════════════════════════════════

    async def _check_health_endpoint(self) -> HealthResult:
        """A-1: /health 내부 호출"""
        try:
            from app.main import health_check
            result = await health_check()
            if result.get("status") == "ok":
                return HealthResult("A-1", "api", "pass", "Health OK")
            return HealthResult("A-1", "api", "warn", f"Health degraded: {result.get('database', '?')}")
        except Exception as e:
            return HealthResult("A-1", "api", "fail", f"Health 호출 실패: {e}")

    async def _check_monitor_endpoint(self) -> HealthResult:
        """A-2: 모니터 API 응답 구조 + 리팩토링 필드 존재 검증"""
        try:
            from app.api.routes_bids import _monitor_company, _enrich_monitor_data
            client = await get_async_client()
            data, total = await _monitor_company(client, offset=0, per_page=3)
            await _enrich_monitor_data(client, data, user_id=None)

            if not data:
                return HealthResult("A-2", "api", "pass", "모니터 API 정상 (데이터 0건)")

            required = {"bid_no", "attachments", "bid_stage", "relevance", "is_bookmarked"}
            sample = data[0]
            missing = required - set(sample.keys())
            if missing:
                return HealthResult("A-2", "api", "fail", f"모니터 응답 필드 누락: {missing}")

            return HealthResult("A-2", "api", "pass", f"모니터 API 정상 ({total}건, 필수 필드 OK)")
        except Exception as e:
            return HealthResult("A-2", "api", "fail", f"모니터 API 오류: {e}")

    async def _check_scored_endpoint(self) -> HealthResult:
        """A-3: 스코어링 함수 정상 작동 확인"""
        try:
            from app.services.domains.bidding.bid_scorer import score_and_rank_bids
            score_and_rank_bids([], reference_date=datetime.now(timezone.utc).date())
            return HealthResult("A-3", "api", "pass", "Scored API 함수 정상")
        except Exception as e:
            return HealthResult("A-3", "api", "fail", f"Scored API 오류: {e}")

    async def _check_proposals_endpoint(self) -> HealthResult:
        """A-4: proposals 테이블 접근 확인"""
        try:
            client = await get_async_client()
            await client.table("proposals").select("id").limit(1).execute()
            return HealthResult("A-4", "api", "pass", "Proposals 테이블 접근 정상")
        except Exception as e:
            return HealthResult("A-4", "api", "fail", f"Proposals 접근 오류: {e}")
