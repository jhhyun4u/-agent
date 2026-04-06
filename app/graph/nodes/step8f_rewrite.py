"""
Node 8F: proposal_write_next_v2

Iterative section rewriting based on feedback.

Input: feedback_summary, dynamic_sections, proposal_sections, current_section_index
Output: proposal_sections_v3 (versioned artifact)

Purpose: Rewrite sections following feedback guidance, maintain
consistency, support rework loop (return to 8B if needed).
"""

import logging
from uuid import UUID

from app.graph.state import ProposalState
from app.services.version_manager import execute_node_and_create_version
from app.services.claude_client import claude_generate
from app.prompts.step8f import WRITE_NEXT_V2_PROMPT
from app.graph.nodes._constants import (
    FEEDBACK_GUIDANCE_LIMIT,
    ORIGINAL_SECTION_LIMIT,
    MAX_REWRITE_ITERATIONS,
    normalize_proposal_section,
)

logger = logging.getLogger(__name__)


async def proposal_write_next_v2(state: ProposalState) -> dict:
    """
    Iterative section rewriting based on feedback.

    Input:
        - feedback_summary: Feedback with rewrite guidance
        - proposal_sections: Current proposal sections
        - dynamic_sections: Section ordering
        - current_section_index: Which section to rewrite (0-based)

    Output:
        - proposal_sections: Updated sections with rewritten content (versioned)

    Returns:
        Updated state dict with new proposal_sections version
    """
    try:
        # Step 1: Validate required inputs
        feedback_summary = state.get("feedback_summary")
        proposal_sections = state.get("proposal_sections", [])
        current_section_index = state.get("current_section_index", 0)

        if not proposal_sections:
            logger.warning("No proposal sections available for rewrite")
            return {
                "proposal_sections": None,
                "node_errors": {
                    **state.get("node_errors", {}),
                    "proposal_write_next_v2": "No proposal sections to rewrite",
                },
            }

        if not feedback_summary:
            logger.warning("No feedback summary available for rewrite")
            # Proceed with basic rewrite if no feedback available
            feedback_data = {}
        else:
            feedback_data = feedback_summary.model_dump()

        # Step 2: Check rewrite iteration limit
        rewrite_iteration_count = state.get("rewrite_iteration_count", 0)
        if rewrite_iteration_count >= MAX_REWRITE_ITERATIONS:
            logger.warning(
                f"Rewrite iteration limit ({MAX_REWRITE_ITERATIONS}) reached for section {current_section_index}. "
                f"Skipping to next section."
            )
            # Move to next section instead of rewriting again
            return {
                "proposal_sections": proposal_sections,
                "current_section_index": current_section_index + 1,
                "rewrite_iteration_count": 0,  # Reset for next section
            }

        # Step 4: Get section to rewrite
        if current_section_index >= len(proposal_sections):
            logger.warning(
                f"Section index {current_section_index} out of range ({len(proposal_sections)} sections)"
            )
            # Return as-is if index invalid
            return {
                "proposal_sections": proposal_sections,
                "current_section_index": current_section_index,
            }

        section_to_rewrite = proposal_sections[current_section_index]
        section_dict = normalize_proposal_section(section_to_rewrite)
        section_id = section_dict.get("section_id", "")
        section_title = section_dict.get("title", "Untitled")
        original_content = section_dict.get("content", "")

        logger.info(
            f"Rewriting section: {section_title} (index {current_section_index}, iteration {rewrite_iteration_count + 1}/{MAX_REWRITE_ITERATIONS})"
        )

        # Step 5: Get rewrite guidance for this section
        section_feedback = feedback_data.get("section_feedback", {})
        section_guidance = section_feedback.get(section_id, [])

        guidance_text = "No specific feedback available."
        if section_guidance:
            guidance_text = "\n".join(
                [
                    f"- {item.get('issue_description', '')} "
                    f"({item.get('estimated_effort', 'unknown')} effort)"
                    for item in section_guidance[:3]
                ]
            )

        # Step 6: Get strategy for context (used in prompt formatting below)
        # strategy = state.get("strategy")

        # Step 7: Call Claude for section rewrite

        prompt = WRITE_NEXT_V2_PROMPT.format(
            section_name=section_title,
            current_content=original_content[:ORIGINAL_SECTION_LIMIT],
            improvement_actions=guidance_text[:FEEDBACK_GUIDANCE_LIMIT],
            feedback=feedback_data.get("key_findings", ""),
        )

        logger.info(f"Calling Claude for section rewrite: {section_title}")

        response = await claude_generate(
            prompt=prompt,
            response_format="text",
            max_tokens=3500,
            step_name="proposal_write_next_v2",
        )
        response_text = (
            response.get("text", "") if isinstance(response, dict) else response
        )

        logger.info(f"Rewrite complete for {section_title}")

        # Step 8: Update section with rewritten content
        updated_sections = []
        for idx, section in enumerate(proposal_sections):
            if idx == current_section_index:
                # Update this section
                section_dict = normalize_proposal_section(section)
                section_dict["content"] = response_text
                section_dict["version"] = section_dict.get("version", 1) + 1
                updated_sections.append(section_dict)
            else:
                # Keep as-is
                updated_sections.append(normalize_proposal_section(section))

        # Step 9: Create version artifact
        version_num, artifact_version = await execute_node_and_create_version(
            proposal_id=UUID(state["project_id"]),
            node_name="proposal_write_next_v2",
            output_key="proposal_sections",
            artifact_data=updated_sections,
            user_id=UUID(state["created_by"]),
            state=state,
            parent_node_name="proposal_sections_consolidation",
        )

        logger.info(
            f"Created proposal_sections v{version_num} (rewrote section {current_section_index})"
        )

        # Step 10: Determine next state
        next_section_index = current_section_index + 1

        # Step 11: Return state update
        # Increment rewrite iteration count (reset if moving to next section)
        next_rewrite_iteration_count = rewrite_iteration_count + 1

        existing_sections_versions = state.get("artifact_versions", {}).get(
            "proposal_sections", []
        )

        return {
            "proposal_sections": updated_sections,
            "current_section_index": next_section_index,
            "rewrite_iteration_count": next_rewrite_iteration_count,
            "artifact_versions": {
                **state.get("artifact_versions", {}),
                "proposal_sections": existing_sections_versions + [artifact_version],
            },
            "active_versions": {
                **state.get("active_versions", {}),
                "proposal_write_next_v2_proposal_sections": version_num,
            },
        }

    except Exception as e:
        logger.exception(f"Error in proposal_write_next_v2: {str(e)}")
        return {
            "proposal_sections": None,
            "current_section_index": state.get("current_section_index", 0),
            "node_errors": {
                **state.get("node_errors", {}),
                "proposal_write_next_v2": f"Rewrite failed: {str(e)}",
            },
        }
