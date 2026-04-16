"""
Vault Beta Testing API Routes
베타 테스트 피드백 및 메트릭 수집 엔드포인트
"""

import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.services.beta_metrics_tracker import (
    BetaMetricsTracker,
    SessionMetrics,
    FeedbackRecord,
    get_metrics_tracker,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vault", tags=["vault-beta"])


# ============================================================================
# Pydantic Models
# ============================================================================

class SessionMetricsRequest(BaseModel):
    """세션 메트릭 수집 요청"""
    session_id: str
    proposal_id: UUID
    step: int

    response_time_ms: int
    ui_render_time_ms: int

    confidence_score: float  # 0-1
    data_points: int
    sources_count: int

    action: str  # 'step_selected' | 'export_pdf' | 'share' | etc


class FeedbackRequest(BaseModel):
    """피드백 수집 요청"""
    proposal_id: UUID
    step: int

    helpfulness: int  # 1-10
    accuracy: int  # 1-10
    relevance: int  # 1-10

    would_use_in_work: bool
    nps_score: int  # 0-10

    improvements: Optional[str] = None
    suggestions: Optional[str] = None


class MetricsResponse(BaseModel):
    """메트릭 응답"""
    step: int
    total_interactions: int
    avg_response_time_ms: float
    min_response_time_ms: float
    max_response_time_ms: float
    avg_render_time_ms: float
    avg_confidence_score: float
    action_breakdown: dict


class SatisfactionResponse(BaseModel):
    """만족도 응답"""
    step: int
    total_feedback: int
    avg_helpfulness: float
    avg_accuracy: float
    avg_relevance: float
    avg_nps_score: float
    nps_promoters: int
    nps_passives: int
    nps_detractors: int
    would_use_in_work_count: int
    would_use_percentage: float


class NPSResponse(BaseModel):
    """NPS 점수"""
    nps_score: float
    promoters: int
    passives: int
    detractors: int
    total_respondents: int
    passes_threshold: bool


class GoLiveReadinessResponse(BaseModel):
    """Go-Live 준비 상태"""
    nps_score: float
    nps_passes: bool
    accuracy_score: float
    accuracy_passes: bool
    response_time_ms: float
    response_time_passes: bool
    critical_bugs: int
    bugs_passes: bool
    overall_readiness: str  # 'READY' | 'NEEDS_IMPROVEMENT'


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/metrics")
async def track_metrics(
    request: SessionMetricsRequest,
    current_user: dict = Depends(get_current_user),
    tracker: BetaMetricsTracker = Depends(get_metrics_tracker),
) -> dict:
    """
    세션 메트릭 기록

    - 응답 시간, 렌더링 시간
    - 신뢰도 점수
    - 사용자 액션
    """
    try:
        metrics = SessionMetrics(
            session_id=request.session_id,
            user_id=current_user["id"],
            proposal_id=request.proposal_id,
            step=request.step,
            timestamp=datetime.utcnow(),
            response_time_ms=request.response_time_ms,
            ui_render_time_ms=request.ui_render_time_ms,
            confidence_score=request.confidence_score,
            data_points=request.data_points,
            sources_count=request.sources_count,
            action=request.action,
        )

        success = await tracker.track_session(metrics)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to track metrics"
            )

        return {
            "success": True,
            "message": "Metrics tracked successfully",
        }

    except Exception as e:
        logger.error(f"Error tracking metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    current_user: dict = Depends(get_current_user),
    tracker: BetaMetricsTracker = Depends(get_metrics_tracker),
) -> dict:
    """
    사용자 피드백 수집

    - 만족도 점수 (1-10)
    - NPS 점수
    - 개선 사항 및 제안
    """
    try:
        feedback = FeedbackRecord(
            session_id=f"session-{current_user['id']}-{datetime.utcnow().timestamp()}",
            user_id=current_user["id"],
            proposal_id=request.proposal_id,
            step=request.step,
            timestamp=datetime.utcnow(),
            helpfulness=request.helpfulness,
            accuracy=request.accuracy,
            relevance=request.relevance,
            would_use_in_work=request.would_use_in_work,
            nps_score=request.nps_score,
            improvements=request.improvements or "",
            suggestions=request.suggestions or "",
        )

        success = await tracker.record_feedback(feedback)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to record feedback"
            )

        return {
            "success": True,
            "message": "Feedback recorded successfully",
        }

    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/metrics/step/{step}")
async def get_step_metrics(
    step: int,
    current_user: dict = Depends(get_current_user),
    tracker: BetaMetricsTracker = Depends(get_metrics_tracker),
) -> dict:
    """Step별 성능 메트릭 조회"""
    try:
        metrics = await tracker.get_step_metrics(step)

        if not metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No metrics found for step {step}"
            )

        return metrics

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting step metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/satisfaction/step/{step}")
async def get_step_satisfaction(
    step: int,
    current_user: dict = Depends(get_current_user),
    tracker: BetaMetricsTracker = Depends(get_metrics_tracker),
) -> dict:
    """Step별 사용자 만족도 조회"""
    try:
        satisfaction = await tracker.get_step_satisfaction(step)

        if not satisfaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No satisfaction data found for step {step}"
            )

        return satisfaction

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting step satisfaction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/nps")
async def get_overall_nps(
    current_user: dict = Depends(get_current_user),
    tracker: BetaMetricsTracker = Depends(get_metrics_tracker),
) -> NPSResponse:
    """전체 NPS (Net Promoter Score) 조회"""
    try:
        nps_data = await tracker.get_nps_score()

        if not nps_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No NPS data available"
            )

        return NPSResponse(**nps_data)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting NPS: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/accuracy")
async def get_accuracy_report(
    current_user: dict = Depends(get_current_user),
    tracker: BetaMetricsTracker = Depends(get_metrics_tracker),
) -> dict:
    """신뢰도 점수 정확도 보고서"""
    try:
        accuracy = await tracker.get_accuracy_report()

        if not accuracy:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No accuracy data available"
            )

        return accuracy

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting accuracy report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/feedback/summary")
async def get_feedback_summary(
    current_user: dict = Depends(get_current_user),
    tracker: BetaMetricsTracker = Depends(get_metrics_tracker),
) -> dict:
    """사용자 피드백 요약"""
    try:
        summary = await tracker.get_user_feedback_summary()

        if not summary:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No feedback data available"
            )

        return summary

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/readiness")
async def get_go_live_readiness(
    current_user: dict = Depends(get_current_user),
    tracker: BetaMetricsTracker = Depends(get_metrics_tracker),
) -> GoLiveReadinessResponse:
    """Go-Live 준비 상태 평가"""
    try:
        readiness = await tracker.get_go_live_readiness()

        if not readiness:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to evaluate readiness"
            )

        return GoLiveReadinessResponse(**readiness)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating go-live readiness: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/report")
async def export_beta_report(
    current_user: dict = Depends(get_current_user),
    tracker: BetaMetricsTracker = Depends(get_metrics_tracker),
) -> dict:
    """전체 베타 테스트 보고서 내보내기"""
    try:
        report = await tracker.export_beta_report()

        if not report:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate report"
            )

        return report

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting beta report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
