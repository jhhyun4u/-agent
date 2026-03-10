"""API 라우터 통합 (v3.5)"""

from fastapi import APIRouter

from . import routes_v31, routes_team, routes_g2b, routes_resources, routes_templates, routes_stats, routes_calendar, routes_presentation

# 메인 라우터
router = APIRouter()

# v3.1 파이프라인: /api/v3.1/*
router.include_router(routes_v31.router)

# 팀 협업: /api/teams/*, /api/proposals/*, /api/invitations/*, etc.
router.include_router(routes_team.router)

# 나라장터 프록시: /api/g2b/*
router.include_router(routes_g2b.router)

# 섹션 라이브러리 + 아카이브: /api/resources/*, /api/archive
router.include_router(routes_resources.router)

# 공통서식 라이브러리: /api/form-templates/*
router.include_router(routes_templates.router)

# 낙찰률 통계: /api/stats/*
router.include_router(routes_stats.router)

# RFP 일정 관리: /api/calendar/*
router.include_router(routes_calendar.router)

# 발표 자료 생성: /api/v3.1/presentation/templates, /api/v3.1/proposals/{id}/presentation/*
router.include_router(routes_presentation.router)

__all__ = ["router"]
