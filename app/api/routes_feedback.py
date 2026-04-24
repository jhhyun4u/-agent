"""
주간 피드백 분석 및 가중치 조정 (STEP 4A Gap 3)

POST /api/feedback/analyze  — 피드백 분석 & 권장사항 생성
"""

import logging
from typing import List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.deps import get_current_user, require_role
from app.models.auth_schemas import CurrentUser
from app.services.domains.proposal.feedback_analyzer import FeedbackAnalyzer
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/feedback", tags=["feedback"])


class FeedbackEntry(BaseModel):
    """피드백 항목"""
    section_type: str
    decision: str  # APPROVE, REJECT
    ratings: Optional[dict] = None
    comment: Optional[str] = None
    created_at: Optional[str] = None


class FeedbackAnalysisRequest(BaseModel):
    """피드백 분석 요청"""
    proposal_id: Optional[str] = None  # 특정 제안서만, None=전체
    days: int = 7  # 최근 N일


class FeedbackAnalysisResponse(BaseModel):
    """피드백 분석 응답"""
    period: str
    analysis_date: str
    total_feedback: int
    section_stats: List[dict]
    weight_recommendations: List[dict]
    summary: dict


@router.post(
    "/analyze",
    response_model=FeedbackAnalysisResponse,
    summary="주간 피드백 분석",
    description="최근 7일 피드백을 수집하여 섹션별 성능 분석 및 가중치 조정 권장사항 생성",
)
async def analyze_feedback(
    request: FeedbackAnalysisRequest,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_role("pm", "reviewer", "admin")),
):
    """
    주간 피드백 분석.

    - **proposal_id**: 특정 제안서만 분석 (없으면 전체)
    - **days**: 분석 대상 기간 (기본 7일)
    """
    try:
        client = await get_async_client()

        # Supabase에서 피드백 데이터 조회
        from_date = (datetime.now() - timedelta(days=request.days)).isoformat()

        query = client.table("feedback_submissions").select("*").gte(
            "created_at", from_date
        )

        if request.proposal_id:
            query = query.eq("proposal_id", request.proposal_id)

        response = await query.execute()
        feedback_entries = response.data or []

        # FeedbackAnalyzer 실행
        analyzer = FeedbackAnalyzer()
        analysis_result = analyzer.analyze_weekly_feedback(feedback_entries)

        logger.info(
            f"피드백 분석 완료: {len(feedback_entries)}개 항목, "
            f"전체 승인률 {analysis_result['summary']['overall_approval_rate']*100:.1f}%"
        )

        return FeedbackAnalysisResponse(**analysis_result)

    except Exception as e:
        logger.error(f"피드백 분석 실패: {e}", exc_info=True)
        raise


@router.get(
    "/report",
    response_model=dict,
    summary="피드백 분석 텍스트 리포트",
)
async def get_feedback_report(
    proposal_id: Optional[str] = None,
    days: int = 7,
    current_user: CurrentUser = Depends(get_current_user),
    _: None = Depends(require_role("pm", "reviewer", "admin")),
):
    """
    피드백 분석 텍스트 리포트 조회.
    """
    try:
        client = await get_async_client()

        from_date = (datetime.now() - timedelta(days=days)).isoformat()

        query = client.table("feedback_submissions").select("*").gte(
            "created_at", from_date
        )

        if proposal_id:
            query = query.eq("proposal_id", proposal_id)

        response = await query.execute()
        feedback_entries = response.data or []

        analyzer = FeedbackAnalyzer()
        report_text = analyzer.get_feedback_analysis_report(feedback_entries)

        return {
            "report": report_text,
            "generated_at": datetime.now().isoformat(),
            "entries_analyzed": len(feedback_entries),
        }

    except Exception as e:
        logger.error(f"리포트 생성 실패: {e}", exc_info=True)
        raise
