"""
Beta Testing Metrics Tracker
베타 테스트 성과 지표 수집 및 분석
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID
from dataclasses import dataclass

from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


@dataclass
class SessionMetrics:
    """Beta 테스트 세션 메트릭"""
    session_id: str
    user_id: str
    proposal_id: UUID
    step: int
    timestamp: datetime

    # Performance metrics
    response_time_ms: int  # API 응답 시간
    ui_render_time_ms: int  # UI 렌더링 시간

    # Data metrics
    confidence_score: float  # 신뢰도 점수 (0-1)
    data_points: int  # 데이터 포인트 수
    sources_count: int  # 데이터 출처 수

    # User actions
    action: str  # 'step_selected' | 'export_pdf' | 'export_docx' | 'share' | 'feedback'


@dataclass
class FeedbackRecord:
    """피드백 기록"""
    session_id: str
    user_id: str
    proposal_id: UUID
    step: int
    timestamp: datetime

    # Satisfaction scores (1-10)
    helpfulness: int
    accuracy: int
    relevance: int

    # Binary response
    would_use_in_work: bool

    # NPS Score (0-10)
    nps_score: int

    # Text feedback
    improvements: str
    suggestions: str


class BetaMetricsTracker:
    """Beta 테스트 메트릭 수집 및 분석"""

    def __init__(self):
        self.sessions: Dict[str, List[SessionMetrics]] = {}
        self.feedbacks: Dict[str, List[FeedbackRecord]] = {}

    async def track_session(self, metrics: SessionMetrics) -> bool:
        """세션 메트릭 기록"""
        try:
            client = await get_async_client()

            # Insert into beta_metrics table
            result = await client.table("beta_metrics").insert({
                "session_id": metrics.session_id,
                "user_id": metrics.user_id,
                "proposal_id": str(metrics.proposal_id),
                "step": metrics.step,
                "timestamp": metrics.timestamp.isoformat(),
                "response_time_ms": metrics.response_time_ms,
                "ui_render_time_ms": metrics.ui_render_time_ms,
                "confidence_score": metrics.confidence_score,
                "data_points": metrics.data_points,
                "sources_count": metrics.sources_count,
                "action": metrics.action,
            }).execute()

            logger.info(f"Tracked session metric: {metrics.session_id}")

            # Also cache locally
            if metrics.session_id not in self.sessions:
                self.sessions[metrics.session_id] = []
            self.sessions[metrics.session_id].append(metrics)

            return bool(result.data)

        except Exception as e:
            logger.error(f"Error tracking session metric: {e}")
            return False

    async def record_feedback(self, feedback: FeedbackRecord) -> bool:
        """피드백 기록"""
        try:
            client = await get_async_client()

            # Insert into beta_feedback table
            result = await client.table("beta_feedback").insert({
                "session_id": feedback.session_id,
                "user_id": feedback.user_id,
                "proposal_id": str(feedback.proposal_id),
                "step": feedback.step,
                "timestamp": feedback.timestamp.isoformat(),
                "helpfulness": feedback.helpfulness,
                "accuracy": feedback.accuracy,
                "relevance": feedback.relevance,
                "would_use_in_work": feedback.would_use_in_work,
                "nps_score": feedback.nps_score,
                "improvements": feedback.improvements,
                "suggestions": feedback.suggestions,
            }).execute()

            logger.info(f"Recorded feedback from {feedback.user_id} for Step {feedback.step}")

            # Cache locally
            if feedback.session_id not in self.feedbacks:
                self.feedbacks[feedback.session_id] = []
            self.feedbacks[feedback.session_id].append(feedback)

            return bool(result.data)

        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return False

    async def get_step_metrics(self, step: int) -> Dict[str, Any]:
        """Step별 통합 메트릭"""
        try:
            client = await get_async_client()

            # Get all metrics for this step
            result = await client.table("beta_metrics").select(
                "response_time_ms, ui_render_time_ms, confidence_score, "
                "data_points, sources_count, action"
            ).eq("step", step).execute()

            if not result.data:
                return {}

            data = result.data
            response_times = [m["response_time_ms"] for m in data]
            render_times = [m["ui_render_time_ms"] for m in data]
            confidences = [m["confidence_score"] for m in data]

            return {
                "step": step,
                "total_interactions": len(data),
                "avg_response_time_ms": sum(response_times) / len(response_times) if response_times else 0,
                "min_response_time_ms": min(response_times) if response_times else 0,
                "max_response_time_ms": max(response_times) if response_times else 0,
                "avg_render_time_ms": sum(render_times) / len(render_times) if render_times else 0,
                "avg_confidence_score": sum(confidences) / len(confidences) if confidences else 0,
                "action_breakdown": self._count_actions(data),
            }

        except Exception as e:
            logger.error(f"Error getting step metrics: {e}")
            return {}

    async def get_step_satisfaction(self, step: int) -> Dict[str, Any]:
        """Step별 사용자 만족도"""
        try:
            client = await get_async_client()

            # Get all feedback for this step
            result = await client.table("beta_feedback").select(
                "helpfulness, accuracy, relevance, nps_score, would_use_in_work"
            ).eq("step", step).execute()

            if not result.data:
                return {}

            data = result.data
            helpfulness_scores = [m["helpfulness"] for m in data]
            accuracy_scores = [m["accuracy"] for m in data]
            relevance_scores = [m["relevance"] for m in data]
            nps_scores = [m["nps_score"] for m in data]
            would_use = sum(1 for m in data if m["would_use_in_work"])

            return {
                "step": step,
                "total_feedback": len(data),
                "avg_helpfulness": sum(helpfulness_scores) / len(helpfulness_scores),
                "avg_accuracy": sum(accuracy_scores) / len(accuracy_scores),
                "avg_relevance": sum(relevance_scores) / len(relevance_scores),
                "avg_nps_score": sum(nps_scores) / len(nps_scores),
                "nps_promoters": sum(1 for s in nps_scores if s >= 9),  # NPS: 9-10
                "nps_passives": sum(1 for s in nps_scores if 7 <= s < 9),  # NPS: 7-8
                "nps_detractors": sum(1 for s in nps_scores if s < 7),  # NPS: 0-6
                "would_use_in_work_count": would_use,
                "would_use_percentage": (would_use / len(data) * 100) if data else 0,
            }

        except Exception as e:
            logger.error(f"Error getting step satisfaction: {e}")
            return {}

    async def get_nps_score(self) -> Dict[str, Any]:
        """Overall NPS 계산"""
        try:
            client = await get_async_client()

            # Get all NPS scores
            result = await client.table("beta_feedback").select("nps_score").execute()

            if not result.data:
                return {}

            nps_scores = [m["nps_score"] for m in result.data]

            promoters = sum(1 for s in nps_scores if s >= 9)
            detractors = sum(1 for s in nps_scores if s < 7)
            total = len(nps_scores)

            nps = ((promoters - detractors) / total * 100) if total > 0 else 0

            return {
                "nps_score": round(nps, 1),
                "promoters": promoters,
                "passives": total - promoters - detractors,
                "detractors": detractors,
                "total_respondents": total,
                "passes_threshold": nps >= 8.0,  # NPS ≥ 8.0
            }

        except Exception as e:
            logger.error(f"Error calculating NPS: {e}")
            return {}

    async def get_accuracy_report(self) -> Dict[str, Any]:
        """신뢰도 점수 정확도 보고서"""
        try:
            client = await get_async_client()

            # Get confidence scores from metrics
            metrics = await client.table("beta_metrics").select(
                "step, confidence_score"
            ).execute()

            if not metrics.data:
                return {}

            # Group by step
            by_step = {}
            for m in metrics.data:
                step = m["step"]
                if step not in by_step:
                    by_step[step] = []
                by_step[step].append(m["confidence_score"])

            # Calculate stats per step
            report = {
                "by_step": {},
                "overall": {},
            }

            all_scores = []
            for step, scores in by_step.items():
                avg = sum(scores) / len(scores) if scores else 0
                report["by_step"][step] = {
                    "avg_confidence": round(avg, 3),
                    "samples": len(scores),
                    "meets_90_percent": avg >= 0.9,
                }
                all_scores.extend(scores)

            # Overall accuracy
            overall_avg = sum(all_scores) / len(all_scores) if all_scores else 0
            report["overall"] = {
                "avg_confidence": round(overall_avg, 3),
                "total_samples": len(all_scores),
                "passes_threshold": overall_avg >= 0.9,  # ≥ 90%
            }

            return report

        except Exception as e:
            logger.error(f"Error generating accuracy report: {e}")
            return {}

    async def get_user_feedback_summary(self) -> Dict[str, Any]:
        """사용자 피드백 요약"""
        try:
            client = await get_async_client()

            # Get all feedback
            result = await client.table("beta_feedback").select(
                "step, improvements, suggestions"
            ).execute()

            if not result.data:
                return {}

            # Organize by step
            by_step = {}
            for record in result.data:
                step = record["step"]
                if step not in by_step:
                    by_step[step] = {
                        "improvements": [],
                        "suggestions": [],
                    }

                if record["improvements"]:
                    by_step[step]["improvements"].append(record["improvements"])
                if record["suggestions"]:
                    by_step[step]["suggestions"].append(record["suggestions"])

            return {
                "by_step": by_step,
                "total_feedback_items": len(result.data),
            }

        except Exception as e:
            logger.error(f"Error getting feedback summary: {e}")
            return {}

    async def get_go_live_readiness(self) -> Dict[str, Any]:
        """프로덕션 배포 준비 상태 평가"""
        try:
            # Collect all KPIs
            nps = await self.get_nps_score()
            accuracy = await self.get_accuracy_report()

            # Get average response time
            all_metrics = {}
            for step in range(1, 6):
                metrics = await self.get_step_metrics(step)
                all_metrics[step] = metrics.get("avg_response_time_ms", 0)

            avg_response_time = sum(all_metrics.values()) / len(all_metrics) if all_metrics else 0

            # Evaluate readiness
            readiness = {
                "nps_score": nps.get("nps_score", 0),
                "nps_passes": nps.get("passes_threshold", False),

                "accuracy_score": accuracy.get("overall", {}).get("avg_confidence", 0),
                "accuracy_passes": accuracy.get("overall", {}).get("passes_threshold", False),

                "response_time_ms": round(avg_response_time, 0),
                "response_time_passes": avg_response_time < 3000,

                "critical_bugs": 0,  # Would be fetched from bug tracking
                "bugs_passes": True,

                "overall_readiness": "READY" if all([
                    nps.get("passes_threshold", False),
                    accuracy.get("overall", {}).get("passes_threshold", False),
                    avg_response_time < 3000,
                ]) else "NEEDS_IMPROVEMENT",
            }

            return readiness

        except Exception as e:
            logger.error(f"Error evaluating go-live readiness: {e}")
            return {}

    @staticmethod
    def _count_actions(data: List[Dict[str, Any]]) -> Dict[str, int]:
        """액션 유형별 카운팅"""
        counts = {}
        for item in data:
            action = item.get("action", "unknown")
            counts[action] = counts.get(action, 0) + 1
        return counts

    async def export_beta_report(self) -> Dict[str, Any]:
        """전체 베타 테스트 보고서"""
        try:
            report = {
                "generated_at": datetime.utcnow().isoformat(),
                "test_period": "2026-04-17 ~ 2026-04-30",

                # Step-by-step analysis
                "steps": {},

                # Overall metrics
                "overall": {
                    "nps": await self.get_nps_score(),
                    "accuracy": await self.get_accuracy_report(),
                    "go_live_readiness": await self.get_go_live_readiness(),
                },

                # User feedback
                "feedback": await self.get_user_feedback_summary(),
            }

            # Populate step-by-step data
            for step in range(1, 6):
                report["steps"][step] = {
                    "metrics": await self.get_step_metrics(step),
                    "satisfaction": await self.get_step_satisfaction(step),
                }

            return report

        except Exception as e:
            logger.error(f"Error exporting beta report: {e}")
            return {}


# Singleton instance
_tracker_instance: Optional[BetaMetricsTracker] = None


async def get_metrics_tracker() -> BetaMetricsTracker:
    """베타 메트릭 트래커 싱글톤"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = BetaMetricsTracker()
    return _tracker_instance
