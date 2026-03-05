"""API 라우터 통합 (v3.4)"""

from fastapi import APIRouter

from . import routes_v31

# 메인 라우터
router = APIRouter()

router.include_router(routes_v31.router)

__all__ = ["router"]
