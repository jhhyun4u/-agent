"""
Node 8B: proposal_section_validator

Quality assurance and compliance validation of proposal sections.

Input: proposal_sections, rfp_analysis, strategy
Output: validation_report (versioned artifact)

Purpose: Check compliance against RFP requirements, style consistency,
cross-section conflicts, and readiness for submission.
"""

import logging
from uuid import UUID

from app.graph.state import ProposalState, ValidationReport
from app.services.version_manager import execute_node_and_create_version
from app.services.claude_client import claude_generate
from app.prompts.step8b import PROPOSAL_VALIDATION_PROMPT
from app.graph.nodes._constants import (
    SECTION_CONTENT_LIMIT_VALIDATION,
    COMBINED_SECTIONS_LIMIT,
    normalize_proposal_section,
)

logger = logging.getLogger(__name__)


async def proposal_section_validator(state: ProposalState) -> dict:
    """
    Quality assurance and compliance validation.

    Input:
        - proposal_sections: List of proposal sections to validate
        - rfp_analysis: RFP analysis with requirements
        - strategy: Proposal strategy and positioning

    Output:
        - validation_report: Comprehensive validation report (versioned)

    Returns:
        Updated state dict with validation_report and version info
    """
    try:
        # Step 1: Validate required inputs
        proposal_sections = state.get("proposal_sections", [])
        rfp_analysis = state.get("rfp_analysis")

        if not proposal_sections:
            logger.warning("No proposal sections available for validation")
            return {
                "validation_report": None,
                "node_errors": {
                    **state.get("node_errors", {}),
                    "proposal_section_validator": "No proposal sections to validate",
                },
            }

        if not rfp_analysis:
            logger.warning("No RFP analysis available for validation")
            return {
                "validation_report": None,
                "node_errors": {
                    **state.get("node_errors", {}),
                    "proposal_section_validator": "Missing rfp_analysis input",
                },
            }

        # Step 2: Build validation context
        strategy = state.get("strategy")

        # Extract mandatory requirements from RFP
        mandatory_reqs = getattr(rfp_analysis, "mandatory_reqs", [])
        if isinstance(mandatory_reqs, list):
            mandatory_reqs_text = "\n".join([f"- {req}" for req in mandatory_reqs])
        else:
            mandatory_reqs_text = str(mandatory_reqs)

        # Build sections text for Claude
        sections_text = []
        for section in proposal_sections:
            section_dict = normalize_proposal_section(section)
            section_title = section_dict.get("title", "Untitled")
            section_content = section_dict.get("content", "")
            if len(section_content) > SECTION_CONTENT_LIMIT_VALIDATION:
                logger.warning(
                    f"Section '{section_title}' truncated: "
                    f"{len(section_content)} → {SECTION_CONTENT_LIMIT_VALIDATION} chars"
                )
            section_content = section_content[:SECTION_CONTENT_LIMIT_VALIDATION]
            sections_text.append(f"## {section_title}\n{section_content}")

        sections_combined = "\n\n".join(sections_text)
        if len(sections_combined) > COMBINED_SECTIONS_LIMIT:
            logger.info(
                f"Combined sections text truncated: "
                f"{len(sections_combined)} → {COMBINED_SECTIONS_LIMIT} chars"
            )

        # Step 3: Call Claude for validation

        prompt = PROPOSAL_VALIDATION_PROMPT.format(
            mandatory_requirements=mandatory_reqs_text,
            sections_text=sections_combined[:COMBINED_SECTIONS_LIMIT],
            positioning=strategy.model_dump_json()
            if strategy and hasattr(strategy, "model_dump_json")
            else "{}",
        )

        logger.info(
            f"Calling Claude for section validation (proposal {state.get('project_id')})"
        )

        response = await claude_generate(
            prompt=prompt,
            response_format="json",
            max_tokens=4000,
            step_name="proposal_section_validator",
        )

        # Step 4: Parse response into ValidationReport
        validation_report = ValidationReport(**response)

        logger.info(
            f"Validation complete: {validation_report.passed_sections}/{validation_report.total_sections} sections passed"
        )

        # Step 5: Create version artifact
        version_num, artifact_version = await execute_node_and_create_version(
            proposal_id=UUID(state["project_id"]),
            node_name="proposal_section_validator",
            output_key="validation_report",
            artifact_data=validation_report.model_dump(),
            user_id=UUID(state["created_by"]),
            state=state,
            parent_node_name="proposal_customer_analysis",
        )

        logger.info(
            f"Created validation_report v{version_num} (quality_score={validation_report.quality_score})"
        )

        # Step 6: Return state update
        return {
            "validation_report": validation_report,
            "artifact_versions": {"validation_report": [artifact_version]},
            "active_versions": {
                **state.get("active_versions", {}),
                "proposal_section_validator_validation_report": version_num,
            },
        }

    except Exception as e:
        logger.exception(f"Error in proposal_section_validator: {str(e)}")
        return {
            "validation_report": None,
            "node_errors": {
                **state.get("node_errors", {}),
                "proposal_section_validator": f"Validation failed: {str(e)}",
            },
        }
