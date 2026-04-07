"""
Node 8D: mock_evaluation_analysis

Simulate evaluator scoring and feedback.

Input: consolidated_proposal, customer_profile
Output: mock_evaluation_result (versioned artifact)

Purpose: Score proposal from multiple evaluator perspectives (technical, financial, etc).
"""

import logging
from uuid import UUID

from app.graph.state import ProposalState, MockEvalResult, ScoreComponent
from app.services.version_manager import execute_node_and_create_version
from app.services.claude_client import claude_generate
from app.prompts.step8d import MOCK_EVALUATION_PROMPT

logger = logging.getLogger(__name__)


async def mock_evaluation_analysis(state: ProposalState) -> dict:
    """
    Simulate evaluator scoring and feedback.

    Input:
        - consolidated_proposal: Final proposal content
        - customer_profile: Client intelligence

    Output:
        - mock_evaluation_result: Scoring and feedback (versioned)

    Returns:
        Updated state dict with mock_evaluation_result and version info
    """
    try:
        proposal = state.get("consolidated_proposal")
        if not proposal:
            logger.warning("No consolidated proposal for evaluation")
            return {
                "mock_evaluation_result": None,
                "node_errors": {
                    **state.get("node_errors", {}),
                    "mock_evaluation_analysis": "No proposal for evaluation",
                },
            }

        customer = state.get("customer_profile")
        proposal_content = (
            proposal.model_dump_json() if hasattr(proposal, "model_dump_json") else str(proposal)
        )

        prompt = MOCK_EVALUATION_PROMPT.format(
            proposal_content=proposal_content,
            customer_profile=customer.model_dump_json()
            if customer and hasattr(customer, "model_dump_json")
            else "Unknown",
        )

        logger.info(f"Running mock evaluation for proposal {state.get('project_id')}")

        response = await claude_generate(
            prompt=prompt,
            response_format="json",
            max_tokens=4500,
            step_name="mock_evaluation_analysis",
        )

        # Parse score components
        score_components = [
            ScoreComponent(**dim) for dim in response.get("dimensions", [])
        ]

        total_max = sum(d.max_points for d in score_components)
        total_score = sum(d.estimated_score for d in score_components)
        score_percentage = (total_score / total_max * 100) if total_max > 0 else 0

        # Add missing fields for state.py MockEvalResult
        from datetime import datetime
        mock_eval = MockEvalResult(
            proposal_id=state["project_id"],
            evaluation_method=response.get("evaluation_method", "A"),
            evaluator_persona=response.get("evaluator_persona", "standard"),
            total_max_points=total_max,
            estimated_total_score=total_score,
            estimated_percentage=score_percentage,
            score_components=score_components,
            estimated_rank=response.get("estimated_rank", "marginal"),
            win_probability=response.get("win_probability", 0.5),
            key_strengths=response.get("strengths", []),
            key_weaknesses=response.get("weaknesses", []),
            critical_gaps=response.get("critical_gaps", []),
            improvement_recommendations=response.get("improvements", []),
            analysis_at=datetime.utcnow().isoformat(),
        )

        logger.info(f"Mock evaluation complete: {score_percentage:.1f}% ({total_score}/{total_max})")

        version_num, artifact_version = await execute_node_and_create_version(
            proposal_id=UUID(state["project_id"]),
            node_name="mock_evaluation_analysis",
            output_key="mock_evaluation_result",
            artifact_data=mock_eval.model_dump(),
            user_id=UUID(state["created_by"]),
            state=state,
            parent_node_name="proposal_sections_consolidation",
        )

        logger.info(f"Created mock_evaluation_result v{version_num}")

        return {
            "mock_eval_result": mock_eval,
            "artifact_versions": {"mock_eval_result": [artifact_version]},
            "active_versions": {
                "mock_evaluation_analysis_mock_eval_result": version_num
            },
        }

    except Exception as e:
        logger.exception(f"Error in mock_evaluation_analysis: {str(e)}")
        return {
            "mock_evaluation_result": None,
            "node_errors": {
                **state.get("node_errors", {}),
                "mock_evaluation_analysis": f"Evaluation failed: {str(e)}",
            },
        }
