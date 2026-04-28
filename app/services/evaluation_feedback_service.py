"""EvaluationFeedbackService — LLM-Wiki Sprint 1에서 실제 구현 예정. 현재 스텁."""
from typing import Any, Dict, Optional


class EvaluationFeedbackService:
    @staticmethod
    async def create_feedback(
        org_id: str,
        proposal_id: str,
        section_id: str,
        round: int,
        human_feedback: str = "",
        confidence_feedback: str = "",
        wiki_suggestion_accepted: Optional[bool] = None,
        wiki_suggestion_id: Optional[str] = None,
        metrics_before: Optional[Dict] = None,
        metrics_after: Optional[Dict] = None,
        created_by: str = "",
    ) -> Dict[str, Any]:
        return {
            "id": None,
            "org_id": org_id,
            "proposal_id": proposal_id,
            "section_id": section_id,
            "round": round,
            "wiki_suggestion_accepted": wiki_suggestion_accepted,
            "wiki_suggestion_id": wiki_suggestion_id,
            "metrics_before": metrics_before,
            "metrics_after": metrics_after,
        }
