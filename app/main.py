"""
FastAPI 애플리케이션 진입점 (v3.0 Multi-Agent)

제안서 자동 생성 에이전트:
- Supervisor 오케스트레이터
- 5개 Sub-agent (RFP 분석, 전략, 섹션, 품질, 문서)
- Tool 카탈로그
- MCP 서버 연동
- Claude 토큰/비용 최적화
"""

from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.config import settings
from app.api.routes import router
from app.graph import build_supervisor_graph
from app.tools import create_default_registry
from app.config.claude_optimizer import TokenUsageTracker

# 로깅 설정
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)

# 전역 상태
supervisor_graph = None
tool_registry = None
token_tracker = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 생명주기 관리"""
    global supervisor_graph, tool_registry, token_tracker

    # 시작 시 초기화
    logger.info("🚀 v3.0 Multi-Agent 시스템 초기화 중...")

    try:
        # Tool Registry 생성
        tool_registry = create_default_registry()
        logger.info(f"✅ Tool Registry 생성: {len(tool_registry.get_all_tools())}개 도구")

        # Supervisor 그래프 구성
        # 주의: 현재 단계에서는 Sub-agent 서브그래프가 구현되지 않았으므로,
        #       빈 서브그래프로 초기화합니다.
        supervisor_graph = build_supervisor_graph(subgraphs=None)
        logger.info("✅ Supervisor 오케스트레이터 구성 완료")

        # 토큰 추적기
        token_tracker = TokenUsageTracker()
        logger.info("✅ 토큰 추적 시스템 활성화")

        logger.info("🎉 시스템 초기화 완료")

    except Exception as e:
        logger.error(f"❌ 초기화 실패: {e}")
        raise

    yield

    # 종료 시 정리
    logger.info("🛑 시스템 종료 중...")
    if token_tracker and settings.log_token_usage:
        report = token_tracker.report()
        logger.info(f"📊 토큰 사용 총계: {report['total_tokens']} 토큰, "
                   f"컬 {report['total_cost_usd']} USD")
        for rec in token_tracker.recommend_optimizations():
            logger.warning(rec)
    logger.info("✅ 시스템 종료 완료")


# FastAPI 앱 생성
app = FastAPI(
    title="용역 제안서 자동 생성 에이전트",
    description="LangGraph Multi-Agent 기반 RFP 분석 및 제안서 자동 생성 API (v3.0)",
    version="3.0.0",
    lifespan=lifespan,
)

# CORS 미들웨어
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API 라우터
app.include_router(router, prefix="/api")


# ═══ 헬스 체크 ═══

@app.get("/health")
async def health_check():
    """시스템 상태 확인"""
    return {
        "status": "ok",
        "version": "3.0.0",
        "supervisor_ready": supervisor_graph is not None,
        "tool_registry_ready": tool_registry is not None,
    }


@app.get("/status")
async def status():
    """상세 시스템 상태"""
    report = {}

    if tool_registry:
        tools = tool_registry.get_all_tools()
        report["tools"] = {
            "total": len(tools),
            "categories": list(set(t["category"] for t in tools.values())),
        }

    if token_tracker:
        report["token_usage"] = token_tracker.report()

    return {
        "status": "operational",
        "version": "3.0.0",
        "components": {
            "supervisor": "ready" if supervisor_graph else "not ready",
            "tool_registry": "ready" if tool_registry else "not ready",
            "token_tracker": "ready" if token_tracker else "not ready",
        },
        "details": report,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )

