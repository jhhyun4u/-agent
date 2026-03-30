"""
Node 8E: mock_evaluation_feedback_processor

Process mock evaluation results into actionable feedback.

Input: mock_eval_result, proposal_sections
Output: feedback_summary (versioned artifact)

Purpose: Prioritize issues, generate rewrite guidance per section,
estimate effort and improvement potential.
"""

import logging
from uuid import UUID

from app.graph.state import ProposalState, FeedbackSummary
from app.services.version_manager import execute_node_and_create_version
from app.services.claude_client import claude_generate
from app.prompts.step8e import FEEDBACK_PROCESSING_PROMPT
from app.graph.nodes._constants import (
    SECTION_CONTENT_LIMIT_FEEDBACK,
    COMBINED_SECTIONS_LIMIT,
    normalize_proposal_section,
)

logger = logging.getLogger(__name__)


async def mock_evaluation_feedback_processor(state: ProposalState) -> dict:
    """
    Process mock evaluation results into actionable feedback.

    Input:
        - mock_eval_result: Mock evaluation scoring results
        - proposal_sections: Current proposal sections

    Output:
        - feedback_summary: Prioritized feedback for improvements (versioned)

    Returns:
        Updated state dict with feedback_summary and version info
    """
    try:
        # Step 1: Validate required inputs
        mock_eval_result = state.get("mock_eval_result")
        proposal_sections = state.get("proposal_sections", [])

        if not mock_eval_result:
            logger.warning(
                "No mock evaluation result available for feedback processing"
            )
            return {
                "feedback_summary": None,
                "node_errors": {
                    **state.get("node_errors", {}),
                    "mock_evaluation_feedback_processor": "Missing mock_eval_result input",
                },
            }

        if not proposal_sections:
            logger.warning("No proposal sections available for feedback")
            return {
                "feedback_summary": None,
                "node_errors": {
                    **state.get("node_errors", {}),
                    "mock_evaluation_feedback_processor": "No proposal sections available",
                },
            }

        # Step 2: Build feedback context
        rfp_analysis = state.get("rfp_analysis")

        # Build sections text for Claude
        sections_text = []
        for section in proposal_sections:
            section_dict = normalize_proposal_section(section)
            section_title = section_dict.get("title", "Untitled")
            section_content = section_dict.get("content", "")
            if len(section_content) > SECTION_CONTENT_LIMIT_FEEDBACK:
                logger.warning(
                    f"Section '{section_title}' truncated: "
                    f"{len(section_content)} → {SECTION_CONTENT_LIMIT_FEEDBACK} chars"
                )
            section_content = section_content[:SECTION_CONTENT_LIMIT_FEEDBACK]
            sections_text.append(f"## {section_title}\n{section_content}")

        sections_combined = "\n\n".join(sections_text)
        if len(sections_combined) > COMBINED_SECTIONS_LIMIT:
            logger.info(
                f"Combined sections text truncated: "
                f"{len(sections_combined)} → {COMBINED_SECTIONS_LIMIT} chars"
            )

        # Step 3: Call Claude for feedback processing

        prompt = FEEDBACK_PROCESSING_PROMPT.format(
            mock_eval_result=mock_eval_result.model_dump_json()
            if hasattr(mock_eval_result, "model_dump_json")
            else str(mock_eval_result),
            proposal_sections=sections_combined[:COMBINED_SECTIONS_LIMIT],
            rfp_analysis=rfp_analysis.model_dump_json()
            if rfp_analysis and hasattr(rfp_analysis, "model_dump_json")
            else "{}",
        )

        logger.info(
            f"Calling Claude for feedback processing (proposal {state.get('project_id')})"
        )

        response = await claude_generate(
            prompt=prompt,
            response_format="json",
            max_tokens=4000,
            step_name="mock_evaluation_feedback_processor",
        )

        # Step 4: Parse response into FeedbackSummary
        feedback_summary = FeedbackSummary(**response)

        logger.info(
            f"Feedback processing complete: {len(feedback_summary.critical_gaps)} critical gaps, "
            f"potential improvement: +{feedback_summary.estimated_score_improvement} points"
        )

        # Step 5: Create version artifact
        version_num, artifact_version = await execute_node_and_create_version(
            proposal_id=UUID(state["project_id"]),
            node_name="mock_evaluation_feedback_processor",
            output_key="feedback_summary",
            artifact_data=feedback_summary.model_dump(),
            user_id=UUID(state["created_by"]),
            state=state,
            parent_node_name="mock_evaluation_analysis",
        )

        logger.info(f"Created feedback_summary v{version_num}")

        # Step 6: Return state update
        return {
            "feedback_summary": feedback_summary,
            "artifact_versions": {"feedback_summary": [artifact_version]},
            "active_versions": {
                **state.get("active_versions", {}),
                "mock_evaluation_feedback_processor_feedback_summary": version_num,
            },
        }

    except Exception as e:
        logger.exception(f"Error in mock_evaluation_feedback_processor: {str(e)}")
        return {
            "feedback_summary": None,
            "node_errors": {
                **state.get("node_errors", {}),
                "mock_evaluation_feedback_processor": f"Feedback processing failed: {str(e)}",
            },
        }
