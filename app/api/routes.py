"""API 라우터 통합 (v3.4)"""

from fastapi import APIRouter

from . import routes_v31, routes_team, routes_g2b

# 메인 라우터
router = APIRouter()

# v3.1 파이프라인: /api/v3.1/*
router.include_router(routes_v31.router)

# 팀 협업: /api/team/*
router.include_router(routes_team.router, prefix="/team")

# 나라장터 프록시: /api/g2b/*
router.include_router(routes_g2b.router)

__all__ = ["router"]
