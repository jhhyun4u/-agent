"""
Node 8B: proposal_section_validator

Quality gate validation for proposal sections.

Input: dynamic_sections (current proposal content)
Output: validation_report (versioned artifact)

Purpose: Perform compliance, style, consistency, and clarity checks.
"""

import logging
from uuid import UUID

from app.graph.state import ProposalState
from app.models.step8_schemas import ValidationReport, ValidationIssue
from app.services.version_manager import execute_node_and_create_version
from app.services.claude_client import claude_generate
from app.prompts.step8b import PROPOSAL_VALIDATION_PROMPT

logger = logging.getLogger(__name__)


async def proposal_section_validator(state: ProposalState) -> dict:
    """
    Validate proposal sections for compliance, style, consistency, clarity.

    Input:
        - dynamic_sections: Current proposal sections with content

    Output:
        - validation_report: Structured validation results (versioned)

    Returns:
        Updated state dict with validation_report and version info
    """
    try:
        # Step 1: Validate required inputs
        sections = state.get("dynamic_sections", [])
        if not sections:
            logger.warning("No sections available for validation")
            return {
                "validation_report": None,
                "node_errors": {
                    **state.get("node_errors", {}),
                    "proposal_section_validator": "No sections to validate",
                },
            }

        # Step 2: Prepare content for validation
        sections_text = "\n\n".join(
            [
                f"### {sec.get('title', 'Untitled')}\n{sec.get('content', '')}"
                for sec in sections[:20]
            ]
        )

        # Step 3: Call Claude for validation analysis
        prompt = PROPOSAL_VALIDATION_PROMPT.format(
            proposal_content=sections_text,
            total_sections=len(sections),
        )

        logger.info(
            f"Validating {len(sections)} sections for proposal {state.get('project_id')}"
        )

        response = await claude_generate(
            prompt=prompt,
            response_format="json",
            max_tokens=4000,
            step_name="proposal_section_validator",
        )

        # Step 4: Parse issues and calculate metrics
        issues_data = response.get("issues", [])
        issues = [ValidationIssue(**issue) for issue in issues_data]

        critical_count = sum(1 for i in issues if i.severity == "critical")
        major_count = sum(1 for i in issues if i.severity == "major")
        minor_count = sum(1 for i in issues if i.severity == "minor")

        quality_score = max(0, 100 - (critical_count * 20 + major_count * 5 + minor_count * 1))

        # Step 5: Create validation report
        validation_report = ValidationReport(
            proposal_id=state["project_id"],
            pass_validation=(critical_count == 0),
            quality_score=quality_score,
            issues=issues,
            critical_issues_count=critical_count,
            major_issues_count=major_count,
            minor_issues_count=minor_count,
            compliance_status=response.get("compliance_status", "unknown"),
            style_consistency=response.get("style_consistency", 50.0),
            recommendations_for_improvement=response.get("recommendations", [])[:3],
            next_steps=response.get("next_steps", []),
        )

        logger.info(
            f"Validation complete: {quality_score:.0f}/100, "
            f"{critical_count} critical, {major_count} major issues"
        )

        # Step 6: Create version artifact
        version_num, artifact_version = await execute_node_and_create_version(
            proposal_id=UUID(state["project_id"]),
            node_name="proposal_section_validator",
            output_key="validation_report",
            artifact_data=validation_report.model_dump(),
            user_id=UUID(state["created_by"]),
            state=state,
            parent_node_name="proposal_write_next_v2",
        )

        logger.info(
            f"Created validation_report v{version_num} for proposal {state['project_id']}"
        )

        return {
            "validation_report": validation_report,
            "artifact_versions": {"validation_report": [artifact_version]},
            "active_versions": {
                "proposal_section_validator_validation_report": version_num
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
