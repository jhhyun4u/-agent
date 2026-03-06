"""
FastAPI 애플리케이션 진입점 (v3.4)

용역 제안서 자동 생성 에이전트:
- 5-Phase Claude API 파이프라인
- RFP 파싱 → 분석 → 전략 → 본문 생성 → 품질 검증
- DOCX + PPTX 자동 생성
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.api.routes import router

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기"""
    logger.info("v3.4 Phase Pipeline 시스템 시작")
    import os
    os.makedirs(settings.output_dir, exist_ok=True)
    from app.utils.supabase_client import get_async_client
    client = await get_async_client()
    try:
        await client.rpc("mark_stale_running_proposals").execute()
        await client.rpc("cleanup_expired_g2b_cache").execute()
        logger.info("lifespan Supabase 초기화 완료")
    except Exception as e:
        logger.warning("lifespan 초기화 경고 (무시): " + str(e))
    # DB에서 활성 세션 복원
    from app.services.session_manager import session_manager
    loaded = await session_manager.startup_load()
    logger.info(f"세션 복원 완료: {loaded}개")
    yield
    logger.info("시스템 종료")


app = FastAPI(
    title="용역 제안서 자동 생성 에이전트",
    description="5-Phase Claude API 파이프라인 기반 RFP 분석 및 제안서 자동 생성 (v3.4)",
    version="3.4.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router, prefix="/api")


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
