# 로그/모니터링 개선 설계 (Monitoring Enhancement)

| 항목 | 내용 |
|------|------|
| 문서 버전 | v1.0 |
| 작성일 | 2026-03-26 |
| 상태 | 초안 |
| Plan 참조 | `docs/01-plan/features/monitoring-enhancement.plan.md` v1.0 |

---

## 1. 설계 범위

Plan §4의 요구사항 MON-01~MON-11을 구현하기 위한 상세 설계.
Phase A (HIGH) + Phase B (MEDIUM) + Phase C (LOW) 순서로 구성.

---

## 2. Phase A — Silent Exception 제거 + 에러 DB 기록

### 2-1. track_tokens 데코레이터 개선 (MON-03)

**현재 문제**: `track_tokens`의 wrapper에서 `await fn(state, ...)` 호출이 try/except 없이 실행됨. 노드가 exception을 던지면 토큰도 기록되지 않고 에러도 DB에 남지 않음.

**변경 — `app/graph/token_tracking.py`**:

```python
def track_tokens(node_name: str):
    def decorator(fn):
        @functools.wraps(fn)
        async def wrapper(state, *args, **kwargs):
            reset_usage_context()
            started_at = time.time()

            try:
                result = await fn(state, *args, **kwargs)
            except Exception as exc:
                # ── 실패 시에도 토큰 사용량 + 에러 기록 ──
                duration_ms = int((time.time() - started_at) * 1000)
                proposal_id = state.get("project_id", "")
                logger.error(
                    f"[NODE ERROR] {node_name}: {type(exc).__name__}: {exc}",
                    exc_info=True,
                    extra={"data": {
                        "node": node_name,
                        "proposal_id": proposal_id,
                        "duration_ms": duration_ms,
                    }},
                )
                # DB에 에러 로그 기록
                if proposal_id:
                    records = get_accumulated_usage()
                    summary = summarize_usage(records) if records else {}
                    await _persist_ai_task_log_error(
                        proposal_id, node_name, summary, duration_ms,
                        error_message=f"{type(exc).__name__}: {str(exc)[:500]}",
                    )
                    # 에러 알림 (Phase B에서 구현, import guard)
                    try:
                        from app.services.notification_service import notify_agent_error
                        await notify_agent_error(proposal_id, node_name, str(exc)[:200])
                    except ImportError:
                        pass
                raise  # 원래 exception 재전파

            # ── 성공 경로 (기존 로직 유지) ──
            duration_ms = int((time.time() - started_at) * 1000)
            # ... (기존 코드 동일)

            return result
        return wrapper
    return decorator


async def _persist_ai_task_log_error(
    proposal_id: str,
    step: str,
    summary: dict,
    duration_ms: int,
    error_message: str,
) -> None:
    """ai_task_logs 테이블에 에러 상태 기록."""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        from datetime import datetime, timezone
        row = {
            "proposal_id": proposal_id,
            "step": step,
            "status": "error",
            "duration_ms": duration_ms,
            "input_tokens": summary.get("input_tokens", 0),
            "output_tokens": summary.get("output_tokens", 0),
            "cost_usd": summary.get("cost_usd", 0),
            "model": summary.get("model", ""),
            "error_message": error_message,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }
        await client.table("ai_task_logs").insert(row).execute()
    except Exception as e:
        logger.warning(f"ai_task_log error insert 실패: {e}")
```

**핵심 원칙**: `track_tokens`가 에러 경로도 책임지므로, 개별 노드에서 에러 DB 기록을 중복할 필요 없음.

### 2-2. Silent Exception 패턴 정리 (MON-01, MON-02)

그래프 노드 11개 파일에서 `except Exception:` (로깅 없는) 26건을 3가지 카테고리로 분류하여 처리:

#### 카테고리 A — "보조 데이터 조회 실패" (대부분)
- **패턴**: KB 조회, 과거 전략 조회, 프롬프트 레지스트리 조회 등
- **현재**: `except Exception: pass`
- **변경**: `except Exception as e: logger.debug(f"보조 데이터 조회 실패 (무시): {e}")`
- **이유**: 핵심 로직이 아니므로 debug 레벨로 충분. 단 완전히 삼키지는 않음
- **해당 파일/라인** (16건):
  - `proposal_nodes.py`: 164, 201, 271, 426, 481, 483
  - `strategy_generate.py`: 3건 (past_strategy, KB fallback)
  - `plan_nodes.py`: 38, 57, 201
  - `ppt_nodes.py`: 44, 220, 259, 306
  - `rfp_analyze.py`: 1건
  - `rfp_search.py`: 1건

#### 카테고리 B — "핵심 로직 실패" (주의 필요)
- **패턴**: Claude API 호출 실패, JSON 파싱 실패 등
- **현재**: `except Exception:` 후 빈 결과 반환
- **변경**: `except Exception as e: logger.error(f"[NODE CRITICAL] {node}: {e}", exc_info=True)` + state에 에러 정보 주입
- **해당 파일/라인** (7건):
  - `go_no_go.py`: 94 (Claude 호출)
  - `ppt_nodes.py`: 114, 122 (PPT 생성)
  - `research_gather.py`: 1건 (리서치 수집)
  - `rfp_fetch.py`: 1건 (첨부파일)
  - `submission_nodes.py`: 79, 151 (제출서류/산출내역서)

#### 카테고리 C — "이미 로깅 있음" (변경 불필요)
- `except Exception as e: logger.warning(...)` — 기존 코드 유지
- 해당: 3건 (go_no_go:171, bid_plan:47, review_node 2건)

#### State 에러 정보 주입 패턴 (MON-02)

카테고리 B의 핵심 로직 실패 시, state에 에러 정보를 남겨 프론트엔드에서 표시:

```python
# 기존 패턴 (나쁨)
except Exception:
    return {"strategy": None}

# 개선 패턴
except Exception as e:
    logger.error(f"[NODE CRITICAL] strategy_generate: {e}", exc_info=True)
    return {
        "strategy": None,
        "node_errors": {
            **state.get("node_errors", {}),
            "strategy_generate": {
                "error": f"{type(e).__name__}: {str(e)[:300]}",
                "step": "strategy_generate",
            },
        },
    }
```

**ProposalState 확장 — `app/graph/state.py`**:

```python
# 기존 필드에 추가
node_errors: Annotated[dict, lambda a, b: {**a, **b}]  # 노드별 에러 누적
```

### 2-3. ai_status_manager.fail_task → persist_log 연동 (MON-04)

**변경 — `app/services/ai_status_manager.py`**:

```python
async def fail_task(
    self, proposal_id: str, error_message: str
) -> dict[str, Any] | None:
    """작업 오류 처리 + DB 자동 기록."""
    task = self._statuses.get(proposal_id)
    if not task:
        return None
    task["status"] = "error"
    task["error"] = error_message
    logger.error(f"AI 작업 오류: {proposal_id}/{task['step']}: {error_message}")
    self._emit_status_change(proposal_id, "error")

    # ── 추가: DB 자동 기록 ──
    duration_ms = int((time.time() - task.get("started_at", time.time())) * 1000)
    await self.persist_log(
        proposal_id=proposal_id,
        step=task["step"],
        status="error",
        duration_ms=duration_ms,
        error_message=error_message,
    )

    return task
```

---

## 3. Phase B — 에러 알림 + 노드 헬스 집계

### 3-1. 에러 알림 함수 (MON-05, MON-06)

**추가 — `app/services/notification_service.py`**:

```python
async def notify_agent_error(
    proposal_id: str,
    node_name: str,
    error_summary: str,
):
    """에이전트 노드 에러 알림 (Teams + 인앱)."""
    try:
        client = await get_async_client()
        proposal = await client.table("proposals").select(
            "title, team_id, created_by"
        ).eq("id", proposal_id).single().execute()

        if not proposal.data:
            return

        title = proposal.data.get("title", "")
        team_id = proposal.data.get("team_id", "")
        created_by = proposal.data.get("created_by", "")

        # 1) Teams Webhook 알림
        if team_id:
            await send_teams_notification(
                team_id=team_id,
                title=f"AI 작업 오류: {node_name}",
                body=(
                    f"**제안서**: {title}\n\n"
                    f"**노드**: {node_name}\n\n"
                    f"**오류**: {error_summary}\n\n"
                    f"관리자 확인이 필요합니다."
                ),
                link=f"/projects/{proposal_id}",
            )

        # 2) 인앱 알림 (생성자에게)
        if created_by:
            await create_notification(
                user_id=created_by,
                proposal_id=proposal_id,
                type="ai_error",
                title=f"AI 작업 오류 — {node_name}",
                body=f"'{title}' 프로젝트의 {node_name} 단계에서 오류가 발생했습니다: {error_summary[:100]}",
                link=f"/projects/{proposal_id}",
            )
    except Exception as e:
        logger.warning(f"에이전트 에러 알림 실패 (무시): {e}")
```

**알림 타입 추가**: `notifications` 테이블의 `type` 컬럼에 `"ai_error"` 값 추가 (기존 `ai_complete`와 대칭).

### 3-2. 노드 헬스 Materialized View (MON-07)

**추가 — `database/migrations/013_node_health.sql`**:

```sql
-- 노드별 헬스 메트릭 (24h / 7d)
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_node_health AS
SELECT
    step                                                    AS node_name,
    COUNT(*)                                                AS total_runs,
    COUNT(*) FILTER (WHERE status = 'complete')             AS success_count,
    COUNT(*) FILTER (WHERE status = 'error')                AS error_count,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'complete') / NULLIF(COUNT(*), 0),
        1
    )                                                       AS success_rate_pct,
    ROUND(AVG(duration_ms))                                 AS avg_duration_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY duration_ms))
                                                            AS p95_duration_ms,
    SUM(COALESCE(cost_usd, 0))                              AS total_cost_usd,
    SUM(COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0))
                                                            AS total_tokens,
    -- 기간 구분
    CASE
        WHEN created_at >= NOW() - INTERVAL '24 hours' THEN '24h'
        WHEN created_at >= NOW() - INTERVAL '7 days'   THEN '7d'
    END                                                     AS period
FROM ai_task_logs
WHERE created_at >= NOW() - INTERVAL '7 days'
GROUP BY step, period
ORDER BY step, period;

CREATE UNIQUE INDEX IF NOT EXISTS idx_mv_node_health
    ON mv_node_health (node_name, period);

-- MV 리프레시 (lifespan 또는 cron에서 호출)
-- SELECT refresh_materialized_view_concurrently('mv_node_health');
```

### 3-3. 모니터링 API 엔드포인트 (MON-08, MON-09)

**추가 — `app/api/routes_admin.py`에 엔드포인트 추가**:

```python
# ── 모니터링 API (§MON-08, MON-09) ──

@router.get("/admin/monitoring/node-health")
async def get_node_health(
    user: CurrentUser = Depends(require_role("admin")),
) -> ItemsResponse:
    """노드별 헬스 메트릭 조회 (mv_node_health)."""
    client = await get_async_client()
    # MV 리프레시 (concurrent)
    try:
        await client.rpc("refresh_materialized_view_concurrently", {
            "view_name": "mv_node_health"
        }).execute()
    except Exception:
        pass  # MV 리프레시 실패해도 stale 데이터 반환

    result = await client.table("mv_node_health").select("*").execute()
    return ok_list(result.data or [])


@router.get("/admin/monitoring/recent-errors")
async def get_recent_errors(
    limit: int = Query(20, le=100),
    node: str | None = Query(None),
    user: CurrentUser = Depends(require_role("admin")),
) -> ItemsResponse:
    """최근 에러 로그 조회 (ai_task_logs status='error')."""
    client = await get_async_client()
    query = (
        client.table("ai_task_logs")
        .select("id, proposal_id, step, error_message, duration_ms, model, created_at")
        .eq("status", "error")
        .order("created_at", desc=True)
        .limit(limit)
    )
    if node:
        query = query.eq("step", node)

    result = await query.execute()
    return ok_list(result.data or [])
```

**Pydantic 스키마** — 기존 `ItemsResponse` 재사용으로 별도 스키마 불필요.

### 3-4. MV 리프레시 RPC 함수

```sql
-- database/migrations/013_node_health.sql (계속)
CREATE OR REPLACE FUNCTION refresh_materialized_view_concurrently(view_name TEXT)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('REFRESH MATERIALIZED VIEW CONCURRENTLY %I', view_name);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
```

---

## 4. Phase C — 프론트엔드 에러 수집

### 4-1. client_error_logs 테이블 (MON-11)

**추가 — `database/migrations/014_client_errors.sql`**:

```sql
CREATE TABLE IF NOT EXISTS client_error_logs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     UUID REFERENCES users(id) ON DELETE SET NULL,
    url         TEXT NOT NULL,
    error       TEXT NOT NULL,
    stack       TEXT,
    user_agent  TEXT,
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_client_errors_created ON client_error_logs(created_at DESC);

-- 30일 이전 자동 정리 (optional)
-- CREATE OR REPLACE FUNCTION cleanup_old_client_errors() ...
```

### 4-2. 에러 수집 API (MON-10)

**추가 — `app/api/routes_admin.py`**:

```python
class ClientErrorReport(BaseModel):
    url: str
    error: str
    stack: str | None = None
    metadata: dict | None = None


@router.post("/client-errors", status_code=201)
async def report_client_error(
    body: ClientErrorReport,
    user: CurrentUser | None = Depends(get_current_user_or_none),
) -> StatusResponse:
    """프론트엔드 JS 에러 수집."""
    client = await get_async_client()
    await client.table("client_error_logs").insert({
        "user_id": user.id if user else None,
        "url": body.url[:500],
        "error": body.error[:2000],
        "stack": (body.stack or "")[:5000],
        "metadata": body.metadata or {},
    }).execute()
    return ok({"status": "recorded"})
```

### 4-3. 프론트엔드 에러 리포터

**추가 — `frontend/src/lib/error-reporter.ts`**:

```typescript
const ERROR_ENDPOINT = "/api/client-errors";
let recentErrors: string[] = [];  // 중복 방지

export function initErrorReporter() {
  if (typeof window === "undefined") return;

  window.addEventListener("error", (event) => {
    reportError({
      url: window.location.href,
      error: event.message,
      stack: event.error?.stack,
    });
  });

  window.addEventListener("unhandledrejection", (event) => {
    reportError({
      url: window.location.href,
      error: String(event.reason),
      stack: event.reason?.stack,
    });
  });
}

async function reportError(payload: {
  url: string;
  error: string;
  stack?: string;
  metadata?: Record<string, unknown>;
}) {
  // 동일 에러 1분 내 중복 방지
  const key = `${payload.error}:${payload.url}`;
  if (recentErrors.includes(key)) return;
  recentErrors.push(key);
  setTimeout(() => {
    recentErrors = recentErrors.filter((e) => e !== key);
  }, 60_000);

  try {
    await fetch(ERROR_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
  } catch {
    // 에러 리포터 자체 실패는 무시
  }
}
```

**통합**: `frontend/src/app/layout.tsx`에서 `initErrorReporter()` 호출.

---

## 5. 파일 변경 매트릭스

| Phase | 파일 | 작업 | 신규/수정 |
|-------|------|------|-----------|
| **A** | `app/graph/token_tracking.py` | try/except 추가, `_persist_ai_task_log_error` 신규 | 수정 |
| **A** | `app/graph/state.py` | `node_errors` 필드 추가 | 수정 |
| **A** | `app/graph/nodes/*.py` (11파일) | silent except → 로깅 추가 (26건) | 수정 |
| **A** | `app/services/ai_status_manager.py` | `fail_task()` → `persist_log()` 연동 | 수정 |
| **B** | `app/services/notification_service.py` | `notify_agent_error()` 추가 | 수정 |
| **B** | `database/migrations/013_node_health.sql` | mv_node_health + RPC | 신규 |
| **B** | `app/api/routes_admin.py` | 모니터링 EP 2개 추가 | 수정 |
| **C** | `database/migrations/014_client_errors.sql` | client_error_logs 테이블 | 신규 |
| **C** | `app/api/routes_admin.py` | POST /client-errors EP | 수정 |
| **C** | `frontend/src/lib/error-reporter.ts` | 글로벌 에러 핸들러 | 신규 |
| **C** | `frontend/src/app/layout.tsx` | initErrorReporter() 호출 | 수정 |

---

## 6. 구현 순서

```
Phase A-1: token_tracking.py 에러 경로 추가
Phase A-2: state.py node_errors 필드 추가
Phase A-3: 그래프 노드 11파일 silent except 정리
Phase A-4: ai_status_manager.py fail_task 연동
    ↓
Phase B-1: notification_service.py notify_agent_error
Phase B-2: 013_node_health.sql MV + RPC
Phase B-3: routes_admin.py 모니터링 EP 2개
    ↓
Phase C-1: 014_client_errors.sql 테이블
Phase C-2: routes_admin.py POST /client-errors
Phase C-3: error-reporter.ts + layout.tsx 통합
```

---

## 7. 검증 방법

| 검증 항목 | 방법 |
|-----------|------|
| silent except 0건 | `grep -rn "except Exception:\s*$" app/graph/nodes/` → 0건 |
| 에러 시 DB 기록 | 의도적으로 Claude API key 무효화 → `ai_task_logs` error 행 확인 |
| Teams 알림 | 에러 발생 시 Teams 채널 수신 확인 |
| 인앱 알림 | `/api/notifications` 조회 시 `ai_error` 타입 존재 |
| 노드 헬스 API | `GET /api/admin/monitoring/node-health` → 200 + 노드별 메트릭 |
| 최근 에러 API | `GET /api/admin/monitoring/recent-errors` → 200 + 에러 목록 |
| 프론트 에러 수집 | 브라우저 콘솔에서 `throw new Error("test")` → DB 확인 |

---

## 8. Out of Scope (Plan §6 재확인)

- Sentry/Datadog 연동
- OpenTelemetry 분산 트레이싱
- 로그 파일 로테이션
- 별도 모니터링 대시보드 UI 페이지 (기존 Admin에 EP만 추가)
