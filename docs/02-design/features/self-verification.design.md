# Design: 플랫폼 자가검증 시스템 (Self-Verification)

> Plan: `docs/01-plan/features/self-verification.plan.md`

## 1. 모듈 구조

```
app/services/
  health_checker.py    ← 검증 실행 엔진 + 15개 체크 구현
  alert_manager.py     ← 알림 발송 + DB 로깅 + 중복 억제

app/api/
  routes_admin.py      ← 관리자 API 확장 (health detail, manual run)

app/main.py            ← /health 확장 + lifespan 연동
app/services/scheduled_monitor.py  ← setup_scheduler() 잡 3개 추가

database/migrations/
  012_health_check_logs.sql  ← 테이블 + 인덱스
```

## 2. DB 스키마

### `database/migrations/012_health_check_logs.sql`

```sql
-- 자가검증 이력
CREATE TABLE IF NOT EXISTS health_check_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    check_id TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN ('infra', 'data', 'external', 'api')),
    status TEXT NOT NULL CHECK (status IN ('pass', 'warn', 'fail', 'fixed')),
    message TEXT,
    detail JSONB DEFAULT '{}',
    auto_recovered BOOLEAN DEFAULT FALSE,
    duration_ms REAL DEFAULT 0,
    checked_at TIMESTAMPTZ DEFAULT NOW()
);

-- 최근 이력 조회 최적화
CREATE INDEX idx_health_logs_checked ON health_check_logs (checked_at DESC);
-- fail/warn만 빠르게 조회
CREATE INDEX idx_health_logs_failures ON health_check_logs (status, checked_at DESC)
    WHERE status IN ('fail', 'warn', 'fixed');
-- check_id별 최근 상태 (중복 억제 판단용)
CREATE INDEX idx_health_logs_check_id ON health_check_logs (check_id, checked_at DESC);

-- 30일 이상 pass 로그 자동 삭제 (저장 공간 관리)
-- Supabase pg_cron 또는 lifespan에서 주기적 실행
-- DELETE FROM health_check_logs WHERE status = 'pass' AND checked_at < NOW() - INTERVAL '30 days';
```

## 3. 핵심 모델: `HealthResult`

```python
# app/services/health_checker.py

from dataclasses import dataclass, field
from typing import Literal

CheckStatus = Literal["pass", "warn", "fail", "fixed"]
CheckCategory = Literal["infra", "data", "external", "api"]

@dataclass
class HealthResult:
    check_id: str                    # "I-1", "D-3", "E-1", "A-2"
    category: CheckCategory
    status: CheckStatus
    message: str
    detail: dict = field(default_factory=dict)  # 추가 정보 (건수, 대상 목록 등)
    auto_recovered: bool = False
    duration_ms: float = 0.0
```

## 4. `HealthCheckRunner` 상세 설계

```python
class HealthCheckRunner:
    """검증 항목 등록 + 실행 엔진"""

    def __init__(self):
        self._checks: dict[str, Callable] = {}   # check_id → async func
        self._register_all()

    def _register_all(self):
        """15개 검증 함수 등록"""
        # 인프라
        self._checks["I-1"] = self._check_db_connection
        self._checks["I-2"] = self._check_storage
        self._checks["I-3"] = self._check_resources
        # 데이터
        self._checks["D-1"] = self._check_stale_days_remaining
        self._checks["D-2"] = self._check_orphan_recommendations
        self._checks["D-3"] = self._check_stale_sessions
        self._checks["D-4"] = self._check_mv_freshness
        self._checks["D-5"] = self._check_cache_db_sync
        # 외부
        self._checks["E-1"] = self._check_g2b_api
        self._checks["E-2"] = self._check_claude_api
        self._checks["E-3"] = self._check_teams_webhook
        # API 스모크
        self._checks["A-1"] = self._check_health_endpoint
        self._checks["A-2"] = self._check_monitor_endpoint
        self._checks["A-3"] = self._check_scored_endpoint
        self._checks["A-4"] = self._check_proposals_endpoint

    async def run_category(self, category: CheckCategory) -> list[HealthResult]:
        """카테고리별 실행"""
        prefix = {"infra": "I", "data": "D", "external": "E", "api": "A"}[category]
        targets = {k: v for k, v in self._checks.items() if k.startswith(prefix)}
        return await self._run_checks(targets)

    async def run_all(self) -> list[HealthResult]:
        """전체 15개 실행"""
        return await self._run_checks(self._checks)

    async def run_single(self, check_id: str) -> HealthResult:
        """단일 검증 실행"""
        func = self._checks.get(check_id)
        if not func:
            return HealthResult(check_id, "infra", "fail", f"알 수 없는 체크: {check_id}")
        return await self._run_one(check_id, func)

    async def _run_checks(self, targets: dict) -> list[HealthResult]:
        results = []
        for check_id, func in targets.items():
            results.append(await self._run_one(check_id, func))
        return results

    async def _run_one(self, check_id: str, func: Callable) -> HealthResult:
        import time
        start = time.monotonic()
        try:
            result = await func()
        except Exception as e:
            result = HealthResult(check_id, "infra", "fail", f"예외: {type(e).__name__}: {e}")
        result.duration_ms = (time.monotonic() - start) * 1000
        return result
```

## 5. 검증 항목별 구현 명세

### 5-1. 인프라 (I-1 ~ I-3)

#### I-1: DB 연결

```python
async def _check_db_connection(self) -> HealthResult:
    """SELECT 1 실행. 실패 시 연결 풀 재생성 시도."""
    try:
        client = await get_async_client()
        await client.table("organizations").select("id").limit(1).execute()
        return HealthResult("I-1", "infra", "pass", "DB 연결 정상")
    except Exception as e:
        # 자동 복구: 연결 풀 재생성
        try:
            from app.utils.supabase_client import reset_client
            await reset_client()
            client = await get_async_client()
            await client.table("organizations").select("id").limit(1).execute()
            return HealthResult("I-1", "infra", "fixed", f"DB 재연결 성공 (원인: {e})", auto_recovered=True)
        except Exception as e2:
            return HealthResult("I-1", "infra", "fail", f"DB 연결 실패 + 복구 실패: {e2}")
```

> `reset_client()`는 `supabase_client.py`에 추가 필요: 전역 `_client`를 `None`으로 리셋.

#### I-2: Supabase Storage

```python
async def _check_storage(self) -> HealthResult:
    client = await get_async_client()
    buckets = await client.storage.list_buckets()
    expected = {settings.storage_bucket_proposals, settings.storage_bucket_attachments}
    found = {b.name for b in buckets}
    missing = expected - found
    if missing:
        return HealthResult("I-2", "infra", "warn", f"버킷 누락: {missing}")
    return HealthResult("I-2", "infra", "pass", f"Storage 정상 ({len(found)}개 버킷)")
```

#### I-3: 메모리/CPU

```python
async def _check_resources(self) -> HealthResult:
    try:
        import psutil
    except ImportError:
        return HealthResult("I-3", "infra", "pass", "psutil 미설치 — 체크 스킵")

    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=0.5)
    detail = {"memory_percent": mem.percent, "cpu_percent": cpu}

    if mem.percent > 90 or cpu > 90:
        return HealthResult("I-3", "infra", "fail", f"리소스 위험: mem={mem.percent}% cpu={cpu}%", detail=detail)
    if mem.percent > 75 or cpu > 75:
        return HealthResult("I-3", "infra", "warn", f"리소스 주의: mem={mem.percent}% cpu={cpu}%", detail=detail)
    return HealthResult("I-3", "infra", "pass", f"리소스 정상: mem={mem.percent}% cpu={cpu}%", detail=detail)
```

### 5-2. 데이터 정합성 (D-1 ~ D-5)

#### D-1: 마감 경과 공고 days_remaining 불일치

```python
async def _check_stale_days_remaining(self) -> HealthResult:
    client = await get_async_client()
    now_iso = datetime.now(timezone.utc).isoformat()

    # deadline < now 인데 days_remaining > 0인 건 조회
    stale = await (
        client.table("bid_announcements")
        .select("bid_no", count="exact")
        .lt("deadline_date", now_iso)
        .gt("days_remaining", 0)
        .limit(0)
        .execute()
    )
    count = stale.count or 0
    if count == 0:
        return HealthResult("D-1", "data", "pass", "days_remaining 정합성 정상")

    # 자동 복구: 재계산
    today = datetime.now(timezone.utc).date()
    expired = await (
        client.table("bid_announcements")
        .select("bid_no, deadline_date")
        .lt("deadline_date", now_iso)
        .gt("days_remaining", 0)
        .limit(500)
        .execute()
    )
    fixed = 0
    for row in (expired.data or []):
        try:
            dl = datetime.fromisoformat(str(row["deadline_date"]).replace("Z", "+00:00")).date()
            new_days = (dl - today).days
            await client.table("bid_announcements").update(
                {"days_remaining": new_days}
            ).eq("bid_no", row["bid_no"]).execute()
            fixed += 1
        except Exception:
            pass

    return HealthResult(
        "D-1", "data", "fixed",
        f"days_remaining 불일치 {count}건 → {fixed}건 재계산",
        detail={"found": count, "fixed": fixed},
        auto_recovered=True,
    )
```

#### D-2: 고아 추천 레코드

```python
async def _check_orphan_recommendations(self) -> HealthResult:
    client = await get_async_client()
    # bid_recommendations에는 있지만 bid_announcements에 없는 bid_no
    # Supabase에서 anti-join이 어려우므로 양쪽 bid_no 집합 비교
    recs = await client.table("bid_recommendations").select("bid_no").execute()
    anns = await client.table("bid_announcements").select("bid_no").execute()

    rec_nos = {r["bid_no"] for r in (recs.data or [])}
    ann_nos = {a["bid_no"] for a in (anns.data or [])}
    orphans = rec_nos - ann_nos

    if not orphans:
        return HealthResult("D-2", "data", "pass", "고아 추천 레코드 없음")

    # 자동 복구: 삭제
    for bid_no in list(orphans)[:100]:
        await client.table("bid_recommendations").delete().eq("bid_no", bid_no).execute()

    return HealthResult(
        "D-2", "data", "fixed",
        f"고아 추천 레코드 {len(orphans)}건 삭제",
        detail={"orphan_count": len(orphans), "deleted": min(len(orphans), 100)},
        auto_recovered=True,
    )
```

#### D-3: Stale 세션

```python
async def _check_stale_sessions(self) -> HealthResult:
    client = await get_async_client()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()

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

    # 자동 복구: stale 전환
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
```

#### D-4: MV 최신성

```python
async def _check_mv_freshness(self) -> HealthResult:
    client = await get_async_client()
    try:
        # pg_stat_user_tables에서 MV 갱신 시각 조회
        res = await client.rpc("check_mv_freshness").execute()
        # RPC가 없으면 fallback: 항상 갱신
        hours_since = res.data.get("hours_since_refresh", 999) if res.data else 999
    except Exception:
        hours_since = 999

    if hours_since <= 24:
        return HealthResult("D-4", "data", "pass", f"MV 갱신 {hours_since}시간 전")

    # 자동 복구: REFRESH
    try:
        await client.rpc("refresh_performance_views").execute()
        return HealthResult(
            "D-4", "data", "fixed",
            f"MV {hours_since}시간 경과 → 갱신 완료",
            auto_recovered=True,
        )
    except Exception as e:
        return HealthResult("D-4", "data", "fail", f"MV 갱신 실패: {e}")
```

#### D-5: 파일 캐시-DB 불일치

```python
async def _check_cache_db_sync(self) -> HealthResult:
    import json as _json
    from pathlib import Path

    status_dir = Path("data/bid_status")
    if not status_dir.exists():
        return HealthResult("D-5", "data", "pass", "파일 캐시 디렉토리 없음")

    client = await get_async_client()
    files = list(status_dir.glob("*.json"))[:200]
    mismatches = 0

    for f in files:
        try:
            cached = _json.loads(f.read_text(encoding="utf-8"))
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
                # DB가 정본 → 파일 덮어쓰기
                cached["status"] = db_status
                f.write_text(_json.dumps(cached, ensure_ascii=False), encoding="utf-8")
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
```

### 5-3. 외부 서비스 (E-1 ~ E-3)

#### E-1: G2B API

```python
async def _check_g2b_api(self) -> HealthResult:
    if not settings.g2b_api_key:
        return HealthResult("E-1", "external", "warn", "G2B API 키 미설정")
    try:
        from app.services.g2b_service import G2BService
        async with G2BService() as g2b:
            result = await g2b.search_bids(keyword="정보시스템", num_of_rows=1)
        if result:
            return HealthResult("E-1", "external", "pass", "G2B API 정상")
        return HealthResult("E-1", "external", "warn", "G2B API 응답은 있으나 결과 없음")
    except Exception as e:
        return HealthResult("E-1", "external", "fail", f"G2B API 오류: {e}")
```

#### E-2: Claude API 키 유효성

```python
async def _check_claude_api(self) -> HealthResult:
    if not settings.anthropic_api_key:
        return HealthResult("E-2", "external", "fail", "Anthropic API 키 미설정")
    # 키 형식 검증만 (실제 호출 X → 비용 절약)
    key = settings.anthropic_api_key
    if not key.startswith("sk-ant-"):
        return HealthResult("E-2", "external", "warn", "API 키 형식 의심 (sk-ant- prefix 없음)")
    return HealthResult("E-2", "external", "pass", "Claude API 키 설정됨 (형식 정상)")
```

#### E-3: Teams Webhook

```python
async def _check_teams_webhook(self) -> HealthResult:
    if not settings.teams_webhook_url:
        return HealthResult("E-3", "external", "warn", "Teams Webhook URL 미설정")
    try:
        import httpx
        # HEAD 요청으로 URL 접근 가능성만 확인 (메시지 전송 X)
        async with httpx.AsyncClient(timeout=10) as http:
            resp = await http.head(settings.teams_webhook_url)
        if resp.status_code < 500:
            return HealthResult("E-3", "external", "pass", f"Teams Webhook 접근 가능 (HTTP {resp.status_code})")
        return HealthResult("E-3", "external", "fail", f"Teams Webhook 서버 오류 (HTTP {resp.status_code})")
    except Exception as e:
        return HealthResult("E-3", "external", "fail", f"Teams Webhook 접근 불가: {e}")
```

### 5-4. API 스모크 테스트 (A-1 ~ A-4)

> **설계 결정**: localhost HTTP 호출 대신 **내부 함수 직접 호출**. 이유: 포트 충돌 없음, 더 빠름, 인증 우회 불필요.

#### A-1: /health

```python
async def _check_health_endpoint(self) -> HealthResult:
    from app.main import health_check
    result = await health_check()
    if result.get("status") == "ok":
        return HealthResult("A-1", "api", "pass", "Health OK")
    return HealthResult("A-1", "api", "warn", f"Health degraded: {result}")
```

#### A-2: /bids/monitor (핵심 검증)

```python
async def _check_monitor_endpoint(self) -> HealthResult:
    """모니터 API 응답 구조 + 리팩토링 필드 존재 검증"""
    from app.api.routes_bids import _monitor_company, _enrich_monitor_data

    client = await get_async_client()
    data, total = await _monitor_company(client, offset=0, per_page=3)
    await _enrich_monitor_data(client, data, user_id=None)

    if not data:
        return HealthResult("A-2", "api", "pass", "모니터 API 정상 (데이터 0건)")

    # 필수 필드 검증
    required = {"bid_no", "attachments", "bid_stage", "relevance", "is_bookmarked"}
    sample = data[0]
    missing = required - set(sample.keys())
    if missing:
        return HealthResult("A-2", "api", "fail", f"모니터 응답 필드 누락: {missing}")

    return HealthResult(
        "A-2", "api", "pass",
        f"모니터 API 정상 ({total}건, 필수 필드 OK)",
        detail={"total": total, "sample_fields": list(sample.keys())},
    )
```

#### A-3, A-4: scored, proposals

```python
async def _check_scored_endpoint(self) -> HealthResult:
    from app.services.bid_scorer import score_and_rank_bids
    # 빈 입력으로 함수 호출 → 오류 없이 빈 결과 반환되는지
    try:
        result = score_and_rank_bids([], reference_date=datetime.now(timezone.utc).date())
        return HealthResult("A-3", "api", "pass", "Scored API 함수 정상")
    except Exception as e:
        return HealthResult("A-3", "api", "fail", f"Scored API 오류: {e}")

async def _check_proposals_endpoint(self) -> HealthResult:
    client = await get_async_client()
    try:
        res = await client.table("proposals").select("id").limit(1).execute()
        return HealthResult("A-4", "api", "pass", "Proposals 테이블 접근 정상")
    except Exception as e:
        return HealthResult("A-4", "api", "fail", f"Proposals 접근 오류: {e}")
```

## 6. `AlertManager` 상세 설계

```python
# app/services/alert_manager.py

class AlertManager:
    """검증 결과 → 알림 + DB 로깅 + 중복 억제"""

    SUPPRESS_WINDOW_MINUTES = 30

    def __init__(self):
        # 인메모리 최근 fail 캐시: {check_id: last_fail_time}
        self._recent_fails: dict[str, datetime] = {}

    async def handle_results(self, results: list[HealthResult]) -> None:
        for r in results:
            await self._log_to_db(r)
            if r.status in ("fail", "fixed"):
                await self._maybe_alert(r)

    async def _log_to_db(self, r: HealthResult) -> None:
        try:
            client = await get_async_client()
            await client.table("health_check_logs").insert({
                "check_id": r.check_id,
                "category": r.category,
                "status": r.status,
                "message": r.message,
                "detail": r.detail,
                "auto_recovered": r.auto_recovered,
                "duration_ms": r.duration_ms,
            }).execute()
        except Exception as e:
            logger.warning(f"헬스체크 로그 저장 실패: {e}")

    async def _maybe_alert(self, r: HealthResult) -> None:
        now = datetime.now(timezone.utc)

        # fixed는 항상 알림 (복구 확인)
        if r.status == "fixed":
            await self._send_teams_alert(r)
            self._recent_fails.pop(r.check_id, None)
            return

        # fail 중복 억제
        last = self._recent_fails.get(r.check_id)
        if last and (now - last).total_seconds() < self.SUPPRESS_WINDOW_MINUTES * 60:
            logger.info(f"[Health] {r.check_id} fail 중복 억제 (마지막: {last.isoformat()})")
            return

        self._recent_fails[r.check_id] = now
        await self._send_teams_alert(r)

    async def _send_teams_alert(self, r: HealthResult) -> None:
        icon = {"pass": "🟢", "warn": "🟡", "fail": "🔴", "fixed": "🟢"}[r.status]
        title = f"{icon} [{r.status.upper()}] {r.check_id}: 자가검증"
        body = r.message
        if r.auto_recovered:
            body += "\n자동 복구: ✅"

        from app.services.notification_service import send_teams_notification
        await send_teams_notification(team_id="", title=title, body=body)
```

## 7. 스케줄러 통합

### `scheduled_monitor.py` 추가 잡

```python
def setup_scheduler() -> None:
    # ... 기존 코드 유지 ...

    # ── 자가검증 잡 추가 ──
    from app.services.health_checker import HealthCheckRunner
    from app.services.alert_manager import AlertManager

    runner = HealthCheckRunner()
    alerter = AlertManager()

    async def _run_and_alert(category):
        results = await runner.run_category(category)
        await alerter.handle_results(results)

    # 인프라: 매 5분
    scheduler.add_job(
        lambda: asyncio.ensure_future(_run_and_alert("infra")),
        trigger=CronTrigger(minute="*/5", timezone=kst),
        id="health_infra",
        replace_existing=True,
    )

    # 데이터 정합성: 매 30분
    scheduler.add_job(
        lambda: asyncio.ensure_future(_run_and_alert("data")),
        trigger=CronTrigger(minute="5,35", timezone=kst),
        id="health_data",
        replace_existing=True,
    )

    # 외부 서비스 + API 스모크: 매 1시간
    async def _run_external_and_api():
        r1 = await runner.run_category("external")
        r2 = await runner.run_category("api")
        await alerter.handle_results(r1 + r2)

    scheduler.add_job(
        lambda: asyncio.ensure_future(_run_external_and_api()),
        trigger=CronTrigger(minute=15, timezone=kst),
        id="health_external_api",
        replace_existing=True,
    )
```

## 8. API 엔드포인트

### `GET /health` 확장 (`main.py`)

```python
@app.get("/health")
async def health_check():
    health = {"status": "ok", "version": "4.0.0"}
    # DB 체크 (기존)
    try:
        client = await get_async_client()
        await client.table("organizations").select("id", count="exact").limit(1).execute()
        health["database"] = "connected"
    except Exception as e:
        health["status"] = "degraded"
        health["database"] = f"error: {type(e).__name__}"

    # 최근 자가검증 요약 추가
    try:
        logs = await client.table("health_check_logs").select(
            "check_id, status, checked_at"
        ).order("checked_at", desc=True).limit(15).execute()

        latest: dict[str, dict] = {}
        for row in (logs.data or []):
            cid = row["check_id"]
            if cid not in latest:
                latest[cid] = {"status": row["status"], "at": row["checked_at"]}

        fail_count = sum(1 for v in latest.values() if v["status"] == "fail")
        health["checks"] = {
            "total": len(latest),
            "fail": fail_count,
            "last_run": logs.data[0]["checked_at"] if logs.data else None,
        }
        if fail_count > 0:
            health["status"] = "degraded"
    except Exception:
        pass

    return health
```

### `GET /api/admin/health/detail` (관리자용)

```python
@router.get("/api/admin/health/detail")
async def health_detail(
    category: str | None = Query(default=None),
    status: str | None = Query(default=None),
    hours: int = Query(default=24, ge=1, le=168),
    current_user: CurrentUser = Depends(get_current_user),
):
    """최근 검증 이력 상세 (관리자 전용)"""
    await require_role(current_user, "admin")
    client = await get_async_client()
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    query = client.table("health_check_logs").select("*").gte("checked_at", since)
    if category:
        query = query.eq("category", category)
    if status:
        query = query.eq("status", status)

    res = await query.order("checked_at", desc=True).limit(200).execute()
    return ok(res.data or [])
```

### `POST /api/admin/health/run` (수동 실행)

```python
@router.post("/api/admin/health/run")
async def health_run(
    category: str | None = Query(default=None),
    check_id: str | None = Query(default=None),
    current_user: CurrentUser = Depends(get_current_user),
):
    """검증 수동 실행 (관리자 전용)"""
    await require_role(current_user, "admin")
    runner = HealthCheckRunner()
    alerter = AlertManager()

    if check_id:
        results = [await runner.run_single(check_id)]
    elif category:
        results = await runner.run_category(category)
    else:
        results = await runner.run_all()

    await alerter.handle_results(results)
    return ok([{
        "check_id": r.check_id, "status": r.status,
        "message": r.message, "auto_recovered": r.auto_recovered,
        "duration_ms": round(r.duration_ms, 1),
    } for r in results])
```

## 9. `supabase_client.py` 확장

```python
# 기존 _client 전역 변수 리셋 함수 추가
async def reset_client() -> None:
    """연결 풀 재생성 (I-1 자동 복구용)"""
    global _client
    _client = None
    logger.info("Supabase 클라이언트 리셋 완료")
```

## 10. 설정 확장 (`config.py`)

```python
# Health Check
health_check_enabled: bool = True
health_suppress_minutes: int = 30      # 중복 알림 억제 시간
health_resource_warn_pct: int = 75     # I-3 리소스 경고 임계치
health_resource_fail_pct: int = 90     # I-3 리소스 위험 임계치
health_mv_max_hours: int = 24          # D-4 MV 최대 허용 경과 시간
health_stale_session_hours: int = 2    # D-3 Stale 세션 판정 시간
```

## 11. 구현 순서 (Plan §8 기반)

| # | Phase | 파일 | 의존성 |
|---|:-----:|------|--------|
| 1 | **A** | `health_checker.py` — HealthResult + HealthCheckRunner 코어 + 레지스트리 | 없음 |
| 2 | **B** | `alert_manager.py` — AlertManager + DB 로깅 + 중복 억제 | A |
| 3 | **SQL** | `012_health_check_logs.sql` | 없음 (병렬 가능) |
| 4 | **C** | 인프라 검증 I-1~I-3 + `supabase_client.py` reset_client | A |
| 5 | **D** | 데이터 정합성 D-1~D-5 + 자동 복구 | A |
| 6 | **E** | 외부 서비스 E-1~E-3 | A |
| 7 | **F** | API 스모크 A-1~A-4 | A |
| 8 | **G** | 스케줄러 통합 + `/health` 확장 | A, B |
| 9 | **H** | 관리자 API + config 확장 | A, B, G |
