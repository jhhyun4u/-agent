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
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.exceptions import TenopAPIError
from app.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

# OPS-03: 구조화 로깅 (JSON 포맷)
if settings.log_format == "json":
    import json as _json
    import datetime as _dt

    class _JsonFormatter(logging.Formatter):
        def format(self, record):
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

    _handler = logging.StreamHandler()
    _handler.setFormatter(_JsonFormatter())
    logging.basicConfig(level=settings.log_level, handlers=[_handler])
else:
    logging.basicConfig(level=settings.log_level)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기"""
    logger.info("Proposal Architect v4.0 시스템 시작")
    import os
    os.makedirs(settings.output_dir, exist_ok=True)

    from app.utils.supabase_client import get_async_client
    client = await get_async_client()
    try:
        await client.rpc("mark_stale_running_proposals").execute()
        await client.rpc("cleanup_expired_g2b_cache").execute()
        logger.info("lifespan Supabase 초기화 완료")
    except Exception as e:
        logger.warning(f"lifespan 초기화 경고 (무시): {e}")

    # Storage 버킷 자동 생성
    for bucket_name in [settings.storage_bucket_proposals, settings.storage_bucket_attachments]:
        try:
            await client.storage.create_bucket(
                bucket_name, options={"public": False},
            )
            logger.info(f"{bucket_name} 버킷 생성 완료")
        except Exception:
            logger.info(f"{bucket_name} 버킷 이미 존재")

    # DB에서 활성 세션 복원
    from app.services.session_manager import session_manager
    loaded = await session_manager.startup_load()
    logger.info(f"세션 복원 완료: {loaded}개")

    # PSM-05: 마감 초과 제안서 expired 전환
    await session_manager.mark_expired_proposals()

    # Dev mode: mock user 자동 생성 (FK 제약 충족)
    if settings.dev_mode:
        try:
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
        except Exception as e:
            logger.warning(f"Dev mock user 생성 실패 (auth.users FK 필요): {e}")

    # §25-2: G2B 정기 모니터링 스케줄러
    from app.services.scheduled_monitor import setup_scheduler
    setup_scheduler()

    # 공고 자동 정리 (마감 경과 + days_remaining 갱신)
    try:
        from app.services.bid_cleanup import cleanup_expired_bids
        cleaned = await cleanup_expired_bids()
        logger.info(f"공고 자동 정리 완료: {cleaned}")
    except Exception as e:
        logger.warning(f"공고 자동 정리 경고 (무시): {e}")

    # 프롬프트 레지스트리 동기화 (코드 → DB)
    try:
        from app.services.prompt_registry import sync_all_prompts
        sync_result = await sync_all_prompts()
        logger.info(f"프롬프트 레지스트리 동기화: {sync_result}")
    except Exception as e:
        logger.warning(f"프롬프트 레지스트리 동기화 경고 (무시): {e}")

    yield
    logger.info("시스템 종료")


# L-3: 프로덕션에서 OpenAPI docs 비활성화
_is_production = settings.log_format == "json"

app = FastAPI(
    title="Proposal Architect — 프로젝트 수주 성공률을 높이는 AI Coworker",
    description="LangGraph 기반 RFP 분석 · 전략 수립 · 제안서 작성 AI 협업 플랫폼 (v4.0)",
    version="4.0.0",
    lifespan=lifespan,
    docs_url=None if _is_production else "/docs",
    redoc_url=None if _is_production else "/redoc",
)

# ── Request ID 미들웨어 (Zero Script QA 핵심) ──
from app.middleware.request_id import RequestIdMiddleware
app.add_middleware(RequestIdMiddleware)

# ── 보안 헤더 미들웨어 (L-1, L-2) ──
from app.middleware.security_headers import SecurityHeadersMiddleware
app.add_middleware(SecurityHeadersMiddleware)

# ── Rate Limiting ──
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# ── CORS ──
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept", "X-Request-ID"],
)

# ── 표준 에러 핸들러 (§12-0) ──

@app.exception_handler(TenopAPIError)
async def tenop_api_error_handler(request: Request, exc: TenopAPIError):
    """TenopAPIError → 표준 JSON 에러 응답"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )

# ── 라우터 등록 ──

# Phase 0: 인증·사용자
from app.api.routes_auth import router as auth_router
from app.api.routes_users import router as users_router
app.include_router(auth_router)
app.include_router(users_router)

# Phase 1: 제안서 CRUD + 워크플로
from app.api.routes_proposal import router as proposal_router
from app.api.routes_workflow import router as workflow_router
app.include_router(proposal_router)
app.include_router(workflow_router)

# Phase 3: 산출물 + 알림
from app.api.routes_artifacts import router as artifacts_router
from app.api.routes_notification import router as notification_router
app.include_router(artifacts_router)
app.include_router(notification_router)

# Phase 4: 성과 추적 + 대시보드
from app.api.routes_performance import router as performance_router
app.include_router(performance_router)

# Phase 5: 관리자 + 감사 로그 + 본부장/경영진 대시보드
from app.api.routes_admin import router as admin_router
app.include_router(admin_router)

# Phase 6: Knowledge Base + 시맨틱 검색
from app.api.routes_kb import router as kb_router
app.include_router(kb_router)

# Phase 4: 분석 대시보드 (§12-13)
from app.api.routes_analytics import router as analytics_router
app.include_router(analytics_router)

# PSM-16: Q&A 기록 CRUD + 검색
from app.api.routes_qa import router as qa_router
app.include_router(qa_router)

# 프로젝트 파일 관리 (GAP-1~6)
from app.api.routes_files import router as files_router
app.include_router(files_router)

# 프로젝트 아카이브 (중간 산출물 파일 관리)
from app.api.routes_project_archive import router as archive_router
app.include_router(archive_router)

# 비딩 가격 시뮬레이션
from app.api.routes_pricing import router as pricing_router
app.include_router(pricing_router)

# 투찰 관리
from app.api.routes_bid_submission import router as bid_submission_router
app.include_router(bid_submission_router)

# 프롬프트 진화 시스템
from app.api.routes_prompt_evolution import router as prompt_evolution_router
app.include_router(prompt_evolution_router)

# 3-Stream 병행 업무
from app.api.routes_streams import router as streams_router
from app.api.routes_submission_docs import router as submission_docs_router
app.include_router(streams_router)
app.include_router(submission_docs_router)

# 팀 협업: /api/teams/*, /api/proposals/comments/*, /api/invitations/*
from app.api.routes_team import router as team_router
app.include_router(team_router)

# 나라장터 프록시: /api/g2b/* (router prefix="/g2b", 여기서 /api 추가)
from app.api.routes_g2b import router as g2b_router
app.include_router(g2b_router, prefix="/api")

# 섹션 라이브러리 + 아카이브: /api/resources/*, /api/assets, /api/archive
from app.api.routes_resources import router as resources_router
app.include_router(resources_router)

# 공통서식 라이브러리: /api/form-templates/*
from app.api.routes_templates import router as templates_router
app.include_router(templates_router)

# 낙찰률 통계: /api/stats/*
from app.api.routes_stats import router as stats_router
app.include_router(stats_router)

# RFP 일정 관리: /api/calendar/*
from app.api.routes_calendar import router as calendar_router
app.include_router(calendar_router)

# v3.1 레거시 파이프라인: /api/v3.1/* (router prefix="/v3.1", 여기서 /api 추가)
from app.api.routes_v31 import router as v31_router
app.include_router(v31_router, prefix="/api")

# 발표 자료 생성: /api/v3.1/* (router prefix="/v3.1", 여기서 /api 추가)
from app.api.routes_presentation import router as presentation_router
app.include_router(presentation_router, prefix="/api")

# 입찰 관리: /api/teams/*/bids/*, /api/bids/*
from app.api.routes_bids import router as bids_router
app.include_router(bids_router)


# ── 헬스체크 ──

@app.get("/health")
async def health_check():
    """시스템 상태 확인 (OPS-02: DB 연결 포함)"""
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


@app.get("/status")
async def status():
    """세션 현황"""
    from app.services.session_manager import session_manager
    return {
        "status": "operational",
        "version": "4.0.0",
        "active_sessions": session_manager.get_session_count(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
