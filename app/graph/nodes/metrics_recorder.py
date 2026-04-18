"""
Phase 4: Proposal Completion Metrics Recorder

제안서 작성 완료 후 전체 제안 메트릭 기록
"""

import logging
from app.graph.state import ProposalState
from app.services.ensemble_metrics_monitor import get_global_monitor

logger = logging.getLogger(__name__)


async def record_proposal_completion_metrics(state: ProposalState) -> dict:
    """
    제안서 작성 완료 후 전체 메트릭 기록.

    Args:
        state: ProposalState

    Returns:
        {"current_step": "metrics_recorded", "metrics_summary": {...}}
    """
    proposal_id = state.get("project_id", "unknown")
    sections = state.get("proposal_sections", [])

    if not sections:
        logger.debug(f"섹션 데이터 없음 (메트릭 스킵): {proposal_id}")
        return {"current_step": "metrics_recorded"}

    # ── 섹션별 메트릭 수집 ──
    confidences = []
    scores = []
    ensemble_applied_count = 0
    feedback_triggered_count = 0

    harness_results = state.get("harness_results", {})

    for section in sections:
        section_id = section.section_id if hasattr(section, "section_id") else section.get("section_id")

        # harness_results에서 점수 추출
        if section_id in harness_results:
            result = harness_results[section_id]
            score = result.get("score", 0.0)
            confidence = result.get("confidence")
            ensemble_applied = result.get("ensemble_applied", False)
            feedback_triggered = result.get("feedback_triggered", False)

            scores.append(score)
            if confidence is not None:
                confidences.append(confidence)

            if ensemble_applied:
                ensemble_applied_count += 1

            if feedback_triggered:
                feedback_triggered_count += 1

    # ── 제안 메트릭 기록 ──
    try:
        monitor = get_global_monitor()

        monitor.record_proposal(
            proposal_id=proposal_id,
            section_count=len(sections),
            confidences=confidences if confidences else scores,  # confidence 있으면 사용, 없으면 score
            scores=scores,
            ensemble_applied=ensemble_applied_count > 0,
            feedback_triggered_count=feedback_triggered_count,
        )

        # 요약 정보
        avg_score = sum(scores) / len(scores) if scores else 0.0
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        ensemble_rate = (ensemble_applied_count / len(sections) * 100) if sections else 0.0

        summary = {
            "proposal_id": proposal_id,
            "section_count": len(sections),
            "avg_score": round(avg_score, 4),
            "avg_confidence": round(avg_confidence, 4) if confidences else None,
            "ensemble_applied_count": ensemble_applied_count,
            "ensemble_application_rate_pct": round(ensemble_rate, 2),
            "feedback_triggered_count": feedback_triggered_count,
            "feedback_trigger_rate_pct": round(
                (feedback_triggered_count / len(sections) * 100) if sections else 0.0, 2
            ),
        }

        logger.info(
            f"✅ 제안 메트릭 기록 완료: {proposal_id}\n"
            f"  섹션: {len(sections)}\n"
            f"  평균점수: {avg_score:.1%}\n"
            f"  평균신뢰: {avg_confidence:.2f}" + (
                f"\n  앙상블율: {ensemble_rate:.1f}%"
                if ensemble_rate > 0 else ""
            ) + f"\n  피드백: {feedback_triggered_count}회"
        )

        return {
            "current_step": "metrics_recorded",
            "metrics_summary": summary,
        }

    except Exception as e:
        logger.error(f"제안 메트릭 기록 실패: {e}")
        return {
            "current_step": "metrics_recorded",
            "error": f"메트릭 기록 실패: {e}",
        }
