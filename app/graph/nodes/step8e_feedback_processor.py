"""
Node 8E: mock_evaluation_feedback_processor

Process mock evaluation feedback and generate improvement recommendations.

Input: mock_evaluation_result
Output: feedback_summary (versioned artifact)

Purpose: Convert evaluation results into actionable improvement plan.
"""

import logging
from uuid import UUID

from app.graph.state import ProposalState, FeedbackSummary, FeedbackItem
from app.services.version_manager import execute_node_and_create_version
from app.services.claude_client import claude_generate
from app.prompts.step8e import FEEDBACK_PROCESSOR_PROMPT

logger = logging.getLogger(__name__)


def _convert_priority_to_int(priority_str: str) -> int:
    """Convert priority string to 1-10 integer scale."""
    priority_map = {
        "critical": 10,
        "high": 8,
        "medium": 5,
        "low": 2,
    }
    return priority_map.get(priority_str.lower(), 5)


async def mock_evaluation_feedback_processor(state: ProposalState) -> dict:
    """
    Process mock evaluation feedback into improvement plan.

    Input:
        - mock_evaluation_result: Evaluation scores and feedback

    Output:
        - feedback_summary: Actionable improvements (versioned)

    Returns:
        Updated state dict with feedback_summary and version info
    """
    try:
        eval_result = state.get("mock_eval_result")
        if not eval_result:
            logger.warning("No evaluation result for feedback processing")
            return {
                "feedback_summary": None,
                "node_errors": {
                    **state.get("node_errors", {}),
                    "mock_evaluation_feedback_processor": "No evaluation to process",
                },
            }

        eval_content = (
            eval_result.model_dump_json()
            if hasattr(eval_result, "model_dump_json")
            else str(eval_result)
        )

        prompt = FEEDBACK_PROCESSOR_PROMPT.format(
            evaluation_result=eval_content,
            current_score=eval_result.estimated_percentage,
        )

        logger.info(f"Processing feedback from evaluation (score: {eval_result.estimated_percentage:.1f}%)")

        response = await claude_generate(
            prompt=prompt,
            response_format="json",
            max_tokens=4000,
            step_name="mock_evaluation_feedback_processor",
        )

        # Parse improvement actions into FeedbackItems
        actions_data = response.get("improvement_actions", [])
        actions = []
        for action in actions_data:
            try:
                # Map response fields to FeedbackItem fields
                feedback_item = FeedbackItem(
                    section_id=action.get("target_section", action.get("section_id", "unknown")),
                    section_title=action.get("section_title", action.get("target_section", "Unknown")),
                    issue_category=action.get("issue_category", "improvement"),
                    priority=_convert_priority_to_int(action.get("priority", "medium")),
                    issue_description=action.get("action", action.get("issue_description", "")),
                    rewrite_guidance=action.get("improvement_guidance", action.get("rewrite_guidance", "")),
                    example_improvement=action.get("example", action.get("example_improvement")),
                    estimated_effort=action.get("effort_estimate", action.get("estimated_effort", "medium")),
                )
                actions.append(feedback_item)
            except Exception as e:
                logger.warning(f"Failed to parse feedback item: {e}")

        # Separate actions into critical gaps and improvement opportunities
        critical_gaps = [a for a in actions if a.issue_category == "critical_gap"]
        improvement_opportunities = [a for a in actions if a.issue_category == "improvement"]

        # Add missing fields for state.py FeedbackSummary
        from datetime import datetime
        feedback = FeedbackSummary(
            proposal_id=state["project_id"],
            critical_gaps=critical_gaps,
            improvement_opportunities=improvement_opportunities,
            section_feedback=response.get("section_feedback", {}),
            highest_impact_issues=response.get("key_findings", [])[:5],
            rewrite_strategy=response.get("rewrite_strategy", ""),
            affected_sections=response.get("affected_sections", []),
            estimated_total_effort=response.get("estimated_effort", "medium"),
            critical_path_effort=response.get("critical_effort", "medium"),
            estimated_score_improvement=int(response.get("estimated_improvement", 0)),
            estimated_new_score=int(eval_result.estimated_total_score + response.get("estimated_improvement", 0)),
            estimated_new_rank=response.get("estimated_new_rank", ""),
            recommended_timeline=response.get("timeline", ""),
            processed_at=datetime.utcnow().isoformat(),
        )

        logger.info(
            f"Generated {len(actions)} improvement actions "
            f"({len(critical_gaps)} critical_gap, "
            f"{len(improvement_opportunities)} improvement)"
        )

        version_num, artifact_version = await execute_node_and_create_version(
            proposal_id=UUID(state["project_id"]),
            node_name="mock_evaluation_feedback_processor",
            output_key="feedback_summary",
            artifact_data=feedback.model_dump(),
            user_id=UUID(state["created_by"]),
            state=state,
            parent_node_name="mock_evaluation_analysis",
        )

        logger.info(f"Created feedback_summary v{version_num}")

        return {
            "feedback_summary": feedback,
            "artifact_versions": {"feedback_summary": [artifact_version]},
            "active_versions": {
                "mock_evaluation_feedback_processor_feedback_summary": version_num
            },
        }

    except Exception as e:
        logger.exception(f"Error in mock_evaluation_feedback_processor: {str(e)}")
        return {
            "feedback_summary": None,
            "node_errors": {
                **state.get("node_errors", {}),
                "mock_evaluation_feedback_processor": f"Processing failed: {str(e)}",
            },
        }
