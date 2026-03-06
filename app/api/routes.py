"""API 라우터 통합 (v3.4)"""

from fastapi import APIRouter

from . import routes_v31, routes_team

# 메인 라우터
router = APIRouter()

# v3.1 파이프라인: /api/v3.1/*
router.include_router(routes_v31.router)

# 팀 협업: /api/team/*  (design 명세: /api/team/ prefix)
router.include_router(routes_team.router, prefix="/team")

__all__ = ["router"]
