"""API 라우터 통합"""

from fastapi import APIRouter

from . import routes_v3, routes_v31, routes_legacy

# 메인 라우터
router = APIRouter()

# 버전별 라우터 포함
router.include_router(routes_v3.router)
router.include_router(routes_v31.router)
router.include_router(routes_legacy.router)

__all__ = ["router"]
