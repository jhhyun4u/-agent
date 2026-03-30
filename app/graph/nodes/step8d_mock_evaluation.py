"""
Node 8D: mock_evaluation_analysis

Simulate evaluator perspective and scoring.

Input: proposal_sections, rfp_analysis, strategy
Output: mock_eval_result (versioned artifact)

Purpose: Predict evaluation score, identify strengths/weaknesses,
estimate win probability, provide improvement recommendations.
"""

import logging
from uuid import UUID

from app.graph.state import ProposalState, MockEvalResult
from app.services.version_manager import execute_node_and_create_version
from app.services.claude_client import claude_generate
from app.prompts.step8d import MOCK_EVALUATION_PROMPT
from app.graph.nodes._constants import (
    SECTION_CONTENT_LIMIT_EVALUATION,
    COMBINED_SECTIONS_LIMIT,
    normalize_proposal_section,
)

logger = logging.getLogger(__name__)


async def mock_evaluation_analysis(state: ProposalState) -> dict:
    """
    Simulate evaluator perspective and scoring.

    Input:
        - proposal_sections: Final proposal sections
        - rfp_analysis: RFP evaluation criteria
        - strategy: Proposal strategy and positioning

    Output:
        - mock_eval_result: Mock evaluation with scores (versioned)

    Returns:
        Updated state dict with mock_eval_result and version info
    """
    try:
        # Step 1: Validate required inputs
        proposal_sections = state.get("proposal_sections", [])
        rfp_analysis = state.get("rfp_analysis")

        if not proposal_sections:
            logger.warning("No proposal sections available for mock evaluation")
            return {
                "mock_eval_result": None,
                "node_errors": {
                    **state.get("node_errors", {}),
                    "mock_evaluation_analysis": "No proposal sections to evaluate",
                },
            }

        if not rfp_analysis:
            logger.warning("No RFP analysis available for mock evaluation")
            return {
                "mock_eval_result": None,
                "node_errors": {
                    **state.get("node_errors", {}),
                    "mock_evaluation_analysis": "Missing rfp_analysis input",
                },
            }

        # Step 2: Build evaluation context
        strategy = state.get("strategy")

        # Extract evaluation criteria from RFP
        eval_items = getattr(rfp_analysis, "eval_items", [])
        if isinstance(eval_items, list):
            criteria_text = "\n".join(
                [
                    f"- {item.get('name', 'Criterion')}: {item.get('description', '')} "
                    f"({item.get('points', 0)} points)"
                    for item in eval_items
                ]
            )
        else:
            criteria_text = str(eval_items)

        # Build sections text for Claude
        sections_text = []
        for section in proposal_sections:
            section_dict = normalize_proposal_section(section)
            section_title = section_dict.get("title", "Untitled")
            section_content = section_dict.get("content", "")
            if len(section_content) > SECTION_CONTENT_LIMIT_EVALUATION:
                logger.warning(
                    f"Section '{section_title}' truncated: "
                    f"{len(section_content)} → {SECTION_CONTENT_LIMIT_EVALUATION} chars"
                )
            section_content = section_content[:SECTION_CONTENT_LIMIT_EVALUATION]
            sections_text.append(f"## {section_title}\n{section_content}")

        sections_combined = "\n\n".join(sections_text)
        if len(sections_combined) > COMBINED_SECTIONS_LIMIT:
            logger.info(
                f"Combined sections text truncated: "
                f"{len(sections_combined)} → {COMBINED_SECTIONS_LIMIT} chars"
            )

        # Determine evaluator persona based on proposal positioning
        evaluator_persona = "standard"  # Default to standard evaluator

        # Step 3: Call Claude for mock evaluation

        prompt = MOCK_EVALUATION_PROMPT.format(
            evaluation_criteria=criteria_text[:2000],
            proposal_sections=sections_combined[:COMBINED_SECTIONS_LIMIT],
            strategy=strategy.model_dump_json()
            if strategy and hasattr(strategy, "model_dump_json")
            else "{}",
            evaluator_type=evaluator_persona,
        )

        logger.info(
            f"Calling Claude for mock evaluation (proposal {state.get('project_id')})"
        )

        response = await claude_generate(
            prompt=prompt,
            response_format="json",
            max_tokens=4500,
            step_name="mock_evaluation_analysis",
        )

        # Step 4: Parse response into MockEvalResult
        mock_eval_result = MockEvalResult(**response)

        logger.info(
            f"Mock evaluation complete: score={mock_eval_result.estimated_total_score}, "
            f"win_probability={mock_eval_result.win_probability}"
        )

        # Step 5: Create version artifact
        version_num, artifact_version = await execute_node_and_create_version(
            proposal_id=UUID(state["project_id"]),
            node_name="mock_evaluation_analysis",
            output_key="mock_eval_result",
            artifact_data=mock_eval_result.model_dump(),
            user_id=UUID(state["created_by"]),
            state=state,
            parent_node_name="proposal_sections_consolidation",
        )

        logger.info(f"Created mock_eval_result v{version_num}")

        # Step 6: Return state update
        return {
            "mock_eval_result": mock_eval_result,
            "artifact_versions": {"mock_eval_result": [artifact_version]},
            "active_versions": {
                **state.get("active_versions", {}),
                "mock_evaluation_analysis_mock_eval_result": version_num,
            },
        }

    except Exception as e:
        logger.exception(f"Error in mock_evaluation_analysis: {str(e)}")
        return {
            "mock_eval_result": None,
            "node_errors": {
                **state.get("node_errors", {}),
                "mock_evaluation_analysis": f"Mock evaluation failed: {str(e)}",
            },
        }
