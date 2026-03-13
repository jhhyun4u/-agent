"""
FastAPI 애플리케이션 진입점 (v3.4)

용역 제안서 자동 생성 에이전트:
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

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기"""
    logger.info("TENOPA v3.4 시스템 시작")
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
    try:
        await client.storage.create_bucket(
            "proposal-files", options={"public": False},
        )
        logger.info("proposal-files 버킷 생성 완료")
    except Exception:
        logger.info("proposal-files 버킷 이미 존재")

    # DB에서 활성 세션 복원
    from app.services.session_manager import session_manager
    loaded = await session_manager.startup_load()
    logger.info(f"세션 복원 완료: {loaded}개")

    yield
    logger.info("시스템 종료")


app = FastAPI(
    title="TENOPA — 용역제안 AI Coworker",
    description="LangGraph 기반 RFP 분석 및 제안서 자동 생성 (v3.4)",
    version="3.4.0",
    lifespan=lifespan,
)

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
app.include_router(auth_router, prefix="/api")
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

# 기존 라우터
from app.api.routes import router as main_router
from app.api.routes_bids import router as bids_router
app.include_router(main_router, prefix="/api")
app.include_router(bids_router)


# ── 헬스체크 ──

@app.get("/health")
async def health_check():
    """시스템 상태 확인"""
    return {"status": "ok", "version": "3.4.0"}


@app.get("/status")
async def status():
    """세션 현황"""
    from app.services.session_manager import session_manager
    return {
        "status": "operational",
        "version": "3.4.0",
        "active_sessions": session_manager.get_session_count(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
