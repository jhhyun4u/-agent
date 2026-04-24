"""
FastAPI 애플리케이션 진입점 (v4.0)

Proposal Architect — 프로젝트 수주 성공률을 높이는 AI Coworker
- LangGraph StateGraph 기반 다단계 파이프라인
- RFP 파싱 → 분석 → 전략 → 본문 생성 → 품질 검증
- DOCX + PPTX + HWP 자동 생성
- Azure AD SSO + 역할 기반 접근 제어
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from contextlib import asynccontextmanager
import logging
import asyncio

from prometheus_client import generate_latest, REGISTRY

from app.config import settings
from app.exceptions import TenopAPIError
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from app.middleware.request_id import RequestIdMiddleware
from app.middleware.security_headers import SecurityHeadersMiddleware
from slowapi.errors import RateLimitExceeded

# ── 라우터 임포트 (모듈 상단에 위치) ──
from app.api.routes_auth import router as auth_router
from app.api.routes_users import router as users_router
from app.api.routes_proposal import router as proposal_router
from app.api.routes_workflow import router as workflow_router
from app.api.routes_artifacts import router as artifacts_router
from app.api.routes_notification import router as notification_router
from app.api.routes_performance import router as performance_router
from app.api.routes_admin import router as admin_router
from app.api.routes_kb import router as kb_router
from app.api.routes_intranet import router as intranet_router
from app.api.routes_documents import router as documents_router
from app.api.routes_migrations import router as migrations_router
from app.api.routes_migration_status import router as migration_status_router
from app.api.routes_migration import router as migration_scheduler_router
from app.api.routes_analytics import router as analytics_router
from app.api.routes_qa import router as qa_router
from app.api.routes_files import router as files_router
from app.api.routes_project_archive import router as archive_router
from app.api.routes_master_projects import router as master_projects_router
from app.api.routes_pricing import router as pricing_router
from app.api.routes_bid_submission import router as bid_submission_router
from app.api.routes_prompt_evolution import router as prompt_evolution_router
from app.api.routes_streams import router as streams_router
from app.api.routes_submission_docs import router as submission_docs_router
from app.api.routes_team import router as team_router
from app.api.routes_g2b import router as g2b_router
from app.api.routes_resources import router as resources_router
from app.api.routes_templates import router as templates_router
from app.api.routes_stats import router as stats_router
from app.api.routes_public import router as public_router
from app.api.routes_calendar import router as calendar_router
from app.api.routes_v31 import router as v31_router
from app.api.routes_presentation import router as presentation_router
from app.api.routes_bids import router as bids_router
from app.api.routes_step8a import router as step8a_router
from app.api.routes_step8_review import router as step8_review_router
from app.api.routes_knowledge import router as knowledge_router
from app.api.routes_vault_chat import router as vault_chat_router
from app.api.routes_vault_embeddings import router as vault_embeddings_router
from app.api.routes_comments import router as comments_router
from app.api.routes_ws import router as ws_router
from app.api.routes_phase2_optimization import router as phase2_optimization_router
from app.api.routes_harness_metrics import router as harness_metrics_router
from app.api.routes_feedback import router as feedback_router
from app.api.routes_scheduler import router as scheduler_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_jobs import router as jobs_router
from app.api.websocket_jobs import router as websocket_jobs_router

# OPS-03: 구조화 로깅 (JSON 포맷)
if settings.log_format == "json":
    class _JsonFormatter(logging.Formatter):
        def format(self, record):
            import json as _json
            import datetime as _dt
            from app.middleware.request_id import get_request_id
            log_entry = {
                "timestamp": _dt.datetime.fromtimestamp(record.created, tz=_dt.timezone.utc).isoformat(),
                "level": record.levelname,
                "service": "api",
                "logger": record.name,
                "request_id": getattr(record, "request_id", "") or get_request_id(),
                "message": record.getMessage(),
            }
            if hasattr(record, "data"):
                log_entry["data"] = record.data
            if record.exc_info:
                log_entry["exc"] = self.formatException(record.exc_info)
            return _json.dumps(log_entry, ensure_ascii=False)

    _handler = logging.StreamHandler(encoding='utf-8')
    _handler.setFormatter(_JsonFormatter())
    logging.basicConfig(level=settings.log_level, handlers=[_handler])
else:
    logging.basicConfig(level=settings.log_level)

logger = logging.getLogger(__name__)


async def _mark_stale_proposals(client):
    """Mark proposals with running status for longer than timeout as stale"""
    await client.rpc("mark_stale_running_proposals").execute()


async def _cleanup_g2b_cache(client):
    """Clean up expired G2B cache entries"""
    await client.rpc("cleanup_expired_g2b_cache").execute()


async def _safe_startup_task(task_name: str, coro, critical: bool = False):
    """Execute a startup task with consistent error handling.

    Args:
        task_name: Human-readable task name for logging
        coro: Coroutine to execute
        critical: If True, raise on exception; if False, log warning and continue
    """
    try:
        await coro
        logger.info(f"{task_name} 완료")
    except Exception as e:
        if critical:
            logger.error(f"{task_name} 실패: {e}")
            raise
        logger.warning(f"{task_name} 경고 (무시): {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기"""
    logger.info("Proposal Architect v4.0 시스템 시작")
    import os
    os.makedirs(settings.output_dir, exist_ok=True)

    from app.utils.supabase_client import get_async_client
    client = await get_async_client()

    # 데이터베이스 스키마 초기화 (제안결정 관련 컬럼)
    async def _init_database_schema():
        """제안결정 기능을 위한 필수 컬럼 존재 확인"""
        try:
            await client.table("proposals").select("go_decision, bid_tracked, org_id").limit(1).execute()
            logger.info("필요한 스키마 컬럼 이미 존재")
        except Exception as e:
            logger.warning(f"스키마 초기화 필요 - Supabase SQL 에디터에서 migration 005 적용 필요: {str(e)[:100]}")

    await _safe_startup_task("DB 스키마 확인", _init_database_schema())

    # Supabase 초기화 (stale proposals + cache cleanup) — decoupled for independence
    await _safe_startup_task("Stale proposals 마킹", _mark_stale_proposals(client))
    await _safe_startup_task("G2B 캐시 정리", _cleanup_g2b_cache(client))

    # Storage 버킷 자동 생성
    for bucket_name in [settings.storage_bucket_proposals, settings.storage_bucket_attachments]:
        await _safe_startup_task(
            f"{bucket_name} 버킷 생성",
            client.storage.create_bucket(bucket_name, options={"public": False}),
        )

    # Session management
    from app.services.core.session_manager import session_manager

    async def _load_sessions():
        loaded = await session_manager.startup_load()
        logger.info(f"세션 복원 완료: {loaded}개")
        await session_manager.mark_expired_proposals()

    await _safe_startup_task("세션 관리", _load_sessions())

    # Dev mode: init mock user environment variables at startup (thread-safe)
    if settings.dev_mode:
        from app.api.deps import _init_dev_user
        await _init_dev_user()  # Initialize dev user in DB

        async def _create_dev_user():
            from app.api.deps import _DEV_USER_ID
            check = await client.table("users").select("id").eq("id", _DEV_USER_ID).maybe_single().execute()
            if not (check and check.data):
                await client.table("users").upsert({
                    "id": _DEV_USER_ID,
                    "email": "lead@tenopa.co.kr",
                    "name": "이팀장",
                    "role": "lead",
                }).execute()
                logger.info(f"Dev mock user 생성: {_DEV_USER_ID}")

        await _safe_startup_task("Dev mock user 생성", _create_dev_user())

    # §25-2: G2B 정기 모니터링 스케줄러
    from app.services.domains.bidding.scheduled_monitor import setup_scheduler
    setup_scheduler()

    # 공고 자동 정리 (마감 경과 + days_remaining 갱신)
    async def _cleanup_bids():
        from app.services.domains.bidding.bid_cleanup import cleanup_expired_bids
        cleaned = await cleanup_expired_bids()
        logger.info(f"공고 자동 정리 완료: {cleaned}")

    await _safe_startup_task("공고 자동 정리", _cleanup_bids())

    # DB 마이그레이션: bid_announcements 테이블 자동 생성
    async def _ensure_bid_table():
        try:
            await client.rpc("create_bid_announcements_table").execute()
        except Exception:
            await client.table("bid_announcements").select("id").limit(1).execute()

    await _safe_startup_task("bid_announcements 테이블 생성", _ensure_bid_table())

    # 프롬프트 레지스트리 동기화 (코드 → DB)
    async def _sync_prompts():
        from app.services.domains.proposal.prompt_registry import sync_all_prompts
        sync_result = await sync_all_prompts()
        logger.info(f"프롬프트 레지스트리 동기화: {sync_result}")

    await _safe_startup_task("프롬프트 레지스트리 동기화", _sync_prompts())

    # DB 마이그레이션: apply_migrations.py 자동 실행 (000~019)
    async def _run_migrations():
        from scripts.apply_migrations import apply_all_migrations
        logger.info("DB 마이그레이션 시작...")

        result = await apply_all_migrations(dry_run=False)

        if result['status'] in ['up_to_date', 'completed']:
            logger.info(f"DB 마이그레이션 완료: {result['applied']}/{result['total']} 적용됨")
        else:
            logger.warning(f"DB 마이그레이션 부분 실패: {result['failed']} 오류, {result['applied']} 성공")

    try:
        await _run_migrations()
    except ImportError as e:
        logger.warning(f"DB 마이그레이션 모듈 미발견 (무시): {e}")
    except Exception as e:
        logger.warning(f"DB 마이그레이션 초기화 경고 (무시): {e}")

    # Phase 2 Week 2: Performance Optimization - 정기 최적화 스케줄러 (5분 간격)
    optimization_task = None
    try:
        from app.services.domains.operations.optimization_scheduler import start_optimization_scheduler
        optimization_task = asyncio.create_task(start_optimization_scheduler())
        logger.info("[Phase 2] 성능 최적화 스케줄러 시작 (5분 간격)")
    except ImportError as e:
        logger.warning(f"[Phase 2] 최적화 스케줄러 모듈 미발견 (무시): {e}")
    except Exception as e:
        logger.warning(f"[Phase 2] 최적화 스케줄러 시작 실패 (무시): {e}")

    # §26: WebSocket 실시간 업데이트 - 하트비트 루프 시작
    from app.services.core.ws_manager import ws_manager

    heartbeat_task = None
    try:
        heartbeat_task = asyncio.create_task(ws_manager.heartbeat_loop())
        logger.info("[WS] WebSocket 하트비트 루프 시작")
    except Exception as e:
        logger.error(f"[WS] 하트비트 루프 시작 실패: {e}")

    # Phase 5: 정기 문서 마이그레이션 스케줄러 초기화
    scheduler_service = None
    try:
        from app.services.domains.operations.scheduler_service import SchedulerService
        scheduler_service = SchedulerService(client)
        await scheduler_service.initialize()
        logger.info("[Phase 5] 정기 문서 마이그레이션 스케줄러 초기화 완료")
    except ImportError as e:
        logger.warning(f"[Phase 5] 스케줄러 모듈 미발견 (무시): {e}")
    except Exception as e:
        logger.warning(f"[Phase 5] 스케줄러 초기화 실패 (무시): {e}")

    yield

    # Shutdown: 최적화 스케줄러 취소
    if optimization_task:
        optimization_task.cancel()
        try:
            await optimization_task
        except asyncio.CancelledError:
            pass
        logger.info("[Phase 2] 성능 최적화 스케줄러 종료")

    # Shutdown: 하트비트 태스크 취소
    if heartbeat_task:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        logger.info("[WS] WebSocket 하트비트 루프 종료")

    # Shutdown: 스케줄러 종료 (pending batch jobs 완료 대기)
    if scheduler_service and getattr(scheduler_service, 'scheduler', None) and scheduler_service.scheduler.running:
        try:
            # wait=True: pending batch jobs를 완료할 때까지 기다린 후 shutdown
            scheduler_service.scheduler.shutdown(wait=True)
            logger.info("[Phase 5] 정기 문서 마이그레이션 스케줄러 종료 (pending jobs 완료)")
        except Exception as e:
            logger.warning(f"[Phase 5] 스케줄러 종료 중 오류: {e}")

    logger.info("시스템 종료")


# L-3: 프로덕션에서 OpenAPI docs 비활성화
_is_production = getattr(settings, 'is_production', settings.log_format == "json")

app = FastAPI(
    title="Proposal Architect — 프로젝트 수주 성공률을 높이는 AI Coworker",
    description="LangGraph 기반 RFP 분석 · 전략 수립 · 제안서 작성 AI 협업 플랫폼 (v4.0)",
    version="4.0.0",
    lifespan=lifespan,
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
)

# ── Request ID 미들웨어 (Zero Script QA 핵심) ──
app.add_middleware(RequestIdMiddleware)

# ── CORS (반드시 먼저!) ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)

# ── 보안 헤더 미들웨어 (L-1, L-2) ──
app.add_middleware(SecurityHeadersMiddleware)

# ── 메모리 모니터링 미들웨어 (M-1, Beta Testing) ──
from app.middleware.memory_monitor import MemoryMonitorMiddleware
app.add_middleware(MemoryMonitorMiddleware)

# ── Rate Limiting ──
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ── 표준 에러 핸들러 (§12-0) ──

def _add_cors_headers(response: JSONResponse, request: Request) -> JSONResponse:
    """응답에 CORS 헤더 추가"""
    origin = request.headers.get("origin", "")
    if origin in settings.cors_origins:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    return response


@app.exception_handler(TenopAPIError)
async def tenop_api_error_handler(request: Request, exc: TenopAPIError):
    """TenopAPIError → 표준 JSON 에러 응답"""
    response = JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )
    return _add_cors_headers(response, request)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """미처리 예외 → 500 + 로그 출력 (디버깅용)"""
    import traceback
    from app.middleware.request_id import get_request_id

    request_id = get_request_id()
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {type(exc).__name__}", extra={"request_id": request_id})
    if settings.log_level == "DEBUG":
        logger.debug(f"Full traceback: {traceback.format_exc()}", extra={"request_id": request_id})
    else:
        logger.warning(f"Exception type {type(exc).__name__} in request {request_id} — enable DEBUG logging for full traceback", extra={"request_id": request_id})

    response = JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "request_id": request_id},
    )
    return _add_cors_headers(response, request)

# ── 라우터 등록 ──

# Phase 0: 인증·사용자
app.include_router(auth_router)
app.include_router(users_router)

# Phase 1: 제안서 CRUD + 워크플로
app.include_router(proposal_router)
app.include_router(workflow_router)

# Phase 3: 산출물 + 알림
app.include_router(artifacts_router)
app.include_router(notification_router)

# Phase 4: 성과 추적 + 대시보드
app.include_router(performance_router)

# Phase 5: 관리자 + 감사 로그 + 본부장/경영진 대시보드
app.include_router(admin_router)

# Phase 6: Knowledge Base + 시맨틱 검색
app.include_router(kb_router)

# 인트라넷 KB 마이그레이션
app.include_router(intranet_router)
app.include_router(documents_router)

# Phase 4: 배치 마이그레이션 관리 (scheduler-integration)
app.include_router(migrations_router)

# DB 마이그레이션 상태 API (설계 §4.4 — GAP-H3/H4/H5)
app.include_router(migration_status_router)

# Phase 5: 정기 문서 마이그레이션 스케줄러 (APScheduler + ConcurrentBatchProcessor)
app.include_router(migration_scheduler_router)

# Phase 4: 분석 대시보드 (§12-13)
app.include_router(analytics_router)

# Dashboard KPI: /api/dashboard/* (팀/본부/경영진 KPI 메트릭 + 캐싱)
app.include_router(dashboard_router)

# PSM-16: Q&A 기록 CRUD + 검색
app.include_router(qa_router)

# 프로젝트 파일 관리 (GAP-1~6)
app.include_router(files_router)

# 프로젝트 아카이브 (중간 산출물 파일 관리)
app.include_router(archive_router)

# 마스터 프로젝트 (통합 프로젝트/제안 검색 + 문서 관리)
app.include_router(master_projects_router)

# 비딩 가격 시뮬레이션
app.include_router(pricing_router)

# 투찰 관리
app.include_router(bid_submission_router)

# 프롬프트 진화 시스템
app.include_router(prompt_evolution_router)

# 3-Stream 병행 업무
app.include_router(streams_router)
app.include_router(submission_docs_router)

# 팀 협업: /api/teams/*, /api/proposals/comments/*, /api/invitations/*
app.include_router(team_router)

# 나라장터 프록시: /api/g2b/* (router prefix="/g2b", 여기서 /api 추가)
app.include_router(g2b_router, prefix="/api")

# 섹션 라이브러리 + 아카이브: /api/resources/*, /api/assets, /api/archive
app.include_router(resources_router)

# 공통서식 라이브러리: /api/form-templates/*
app.include_router(templates_router)

# 낙찰률 통계: /api/stats/*
app.include_router(stats_router)

# 랜딩페이지 공개 통계: /api/public/*
app.include_router(public_router)

# RFP 일정 관리: /api/calendar/*
app.include_router(calendar_router)

# v3.1 레거시 파이프라인: /api/v3.1/* (router prefix="/v3.1", 여기서 /api 추가)
app.include_router(v31_router, prefix="/api")

# 발표 자료 생성: /api/v3.1/* (router prefix="/v3.1", 여기서 /api 추가)
app.include_router(presentation_router, prefix="/api")

# 입찰 관리: /api/teams/*/bids/*, /api/bids/*
app.include_router(bids_router)

# STEP 8A-8F: 새 노드 + 아티팩트 버전 관리 (DB-backed implementation)
app.include_router(step8a_router)

# STEP 8 Review: AI-powered review interface for STEP 8 nodes
app.include_router(step8_review_router)

# 지식 관리 시스템: /api/knowledge/* (Module-5: 분류, 검색, 추천)
app.include_router(knowledge_router)

# Vault AI Chat: /api/vault/chat, /api/vault/conversations/*
app.include_router(vault_chat_router)

# Vault Embeddings: /api/vault/embeddings/*
app.include_router(vault_embeddings_router)

# Sprint 1 Phase 2: Team Comments & Feedback
# Comments: /api/proposals/{proposal_id}/comments, /api/comments/{comment_id}/reactions
app.include_router(comments_router)

# STEP 4A Gap 3: 주간 피드백 분석 & 가중치 조정
# Feedback: /api/feedback/analyze, /api/feedback/report
app.include_router(feedback_router)

# Phase 3.1: WebSocket 실시간 업데이트: /api/ws/dashboard
app.include_router(ws_router)

# Phase 2: Performance Optimization (Week 2) — Data-Driven Optimization
# Endpoints: /api/phase2/analyze/*, /api/phase2/cache/*, /api/phase2/optimize/*
app.include_router(phase2_optimization_router)

# STEP 4A: Harness Metrics Monitoring (Phase 3-4)
# Endpoints: /api/harness/metrics/record, /api/harness/metrics/phase/*, /api/harness/metrics/report, etc.
app.include_router(harness_metrics_router)

# Phase 5: Scheduler Integration - 정기 문서 마이그레이션
# Endpoints: /api/scheduler/schedules/*, /api/scheduler/batches/*
app.include_router(scheduler_router)

# STEP 8: Job Queue - 비동기 작업 처리 (Day 5)
# Endpoints: /api/jobs/* (REST) + /ws/jobs/* (WebSocket)
app.include_router(jobs_router, prefix="/api")
app.include_router(websocket_jobs_router)


# ── 헬스체크 ──

@app.get("/health")
async def health_check():
    """시스템 상태 확인 (OPS-02: DB 연결 + 자가검증 요약)"""
    health = {"status": "ok", "version": "4.0.0"}
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        await client.table("organizations").select("id", count="exact").limit(1).execute()
        health["database"] = "connected"
    except Exception as e:
        health["status"] = "degraded"
        health["database"] = f"error: {type(e).__name__}"
        return health

    # 최근 자가검증 요약
    try:
        logs = await client.table("health_check_logs").select(
            "check_id, status, checked_at"
        ).order("checked_at", desc=True).limit(30).execute()

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
            health["checks"]["failing"] = [
                k for k, v in latest.items() if v["status"] == "fail"
            ]
    except Exception:
        pass

    return health


@app.get("/status")
async def status():
    """세션 현황"""
    from app.services.core.session_manager import session_manager
    return {
        "status": "operational",
        "version": "4.0.0",
        "active_sessions": session_manager.get_session_count(),
    }


# ── Prometheus 메트릭 엔드포인트 ──

@app.get("/metrics")
async def metrics():
    """
    Prometheus 메트릭 엔드포인트
    
    Prometheus의 scrape_configs에서 이 엔드포인트를 수집하도록 설정:
    
    ```yaml
    scrape_configs:
      - job_name: 'proposal-architect'
        static_configs:
          - targets: ['localhost:8000']
        metrics_path: '/metrics'
        scrape_interval: 15s
    ```
    """
    return Response(
        content=generate_latest(REGISTRY),
        media_type="text/plain; version=0.0.4; charset=utf-8"
    )


if __name__ == "__main__":
    import uvicorn
    host = "127.0.0.1" if not settings.dev_mode else "0.0.0.0"
    uvicorn.run("app.main:app", host=host, port=8000, reload=settings.dev_mode)
