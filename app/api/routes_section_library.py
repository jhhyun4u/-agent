"""
성공 섹션 라이브러리 API — 학술연구용역 특화

GET  /api/section-library/recommend    — 섹션 작성 중 추천
GET  /api/section-library/content/{id} — 섹션 전문 조회 + 재사용 카운트
POST /api/section-library/extract/{proposal_id} — 수주 제안서 섹션 수동 추출
GET  /api/section-library/stats        — 라이브러리 현황
"""

import logging

from fastapi import APIRouter, Depends

from app.api.deps import get_current_user
from app.api.response import ok
from app.exceptions import TenopAPIError
from app.models.auth_schemas import CurrentUser
from app.services.domains.proposal.success_section_library import (
    extract_and_register_won_sections,
    get_library_stats,
    get_section_full_content,
    recommend_winning_sections,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/section-library", tags=["section-library"])


@router.get("/recommend")
async def recommend_sections(
    section_title: str,
    section_category: str | None = None,
    study_type: str | None = None,
    top_k: int = 5,
    user: CurrentUser = Depends(get_current_user),
):
    """섹션 작성 중 유사 수주 섹션 추천.

    - section_title: 현재 작성 중인 섹션 제목 (예: "수행 실적")
    - section_category: TRACK_RECORD | METHODOLOGY | PERSONNEL 등
    - study_type: 정책연구 | 기초조사 | 타당성분석 등
    """
    if not section_title.strip():
        raise TenopAPIError("SL_001", "section_title 필수입니다.", 400)

    results = await recommend_winning_sections(
        section_title=section_title,
        section_category=section_category,
        study_type=study_type,
        org_id=user.org_id,
        top_k=min(top_k, 10),
    )
    return ok(results)


@router.get("/content/{content_id}")
async def get_content_full(
    content_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """섹션 전문 조회 (재사용 카운트 증가)."""
    body = await get_section_full_content(content_id, user.org_id)
    if body is None:
        raise TenopAPIError("SL_002", "섹션을 찾을 수 없습니다.", 404)
    return ok({"content_id": content_id, "body": body})


@router.post("/extract/{proposal_id}")
async def extract_won_sections(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """수주 제안서 섹션 수동 추출 트리거.

    수주 처리 시 자동 호출되지만, 수동 재실행도 가능.
    """
    count = await extract_and_register_won_sections(proposal_id, user.org_id)
    return ok({"extracted": count, "proposal_id": proposal_id})


@router.get("/stats")
async def get_stats(user: CurrentUser = Depends(get_current_user)):
    """라이브러리 현황 통계."""
    stats = await get_library_stats(user.org_id)
    return ok(stats)
