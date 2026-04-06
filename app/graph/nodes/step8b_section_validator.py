"""
Node 8B: proposal_section_validator

Quality gate validation for proposal sections.

Input: dynamic_sections (current proposal content)
Output: validation_report (versioned artifact)

Purpose: Perform compliance, style, consistency, and clarity checks.
"""

import logging
from uuid import UUID

from app.graph.state import ProposalState, ValidationReport, ValidationIssue
from app.services.version_manager import execute_node_and_create_version
from app.services.claude_client import claude_generate
from app.prompts.step8b import SECTION_VALIDATION_PROMPT

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
        prompt = SECTION_VALIDATION_PROMPT.format(
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

        # Step 4: Parse issues and categorize by severity
        issues_data = response.get("issues", [])

        # Map issues to ValidationIssue objects
        all_issues = []
        for issue in issues_data:
            try:
                validation_issue = ValidationIssue(
                    section_id=issue.get("section_id", issue.get("section", "unknown")),
                    issue_type=issue.get("category", "compliance"),
                    severity=issue.get("severity", "warning"),  # "error", "warning", "info"
                    description=issue.get("description", ""),
                    location=issue.get("line_reference"),
                    fix_guidance=issue.get("recommendation"),
                    estimated_fix_effort=issue.get("estimated_effort", "medium"),
                )
                all_issues.append(validation_issue)
            except Exception as e:
                logger.warning(f"Failed to parse issue: {e}")

        # Categorize by severity
        errors = [i for i in all_issues if i.severity == "error"]
        warnings = [i for i in all_issues if i.severity == "warning"]
        infos = [i for i in all_issues if i.severity == "info"]

        # Calculate section metrics
        total_sections = len(state.get("dynamic_sections", []))
        sections_with_issues = len(set(i.section_id for i in all_issues))

        quality_score = max(0, 100 - (len(errors) * 20 + len(warnings) * 5 + len(infos) * 1))

        # Step 5: Create validation report
        from datetime import datetime
        validation_report = ValidationReport(
            proposal_id=state["project_id"],
            total_sections=total_sections,
            sections_validated=total_sections,
            passed_sections=max(0, total_sections - sections_with_issues),
            failed_sections=len([s for s in state.get("dynamic_sections", [])
                                if any(e.section_id == s.get("section_id") for e in errors)]),
            warning_sections=len([s for s in state.get("dynamic_sections", [])
                                 if any(w.section_id == s.get("section_id") for w in warnings)]),
            errors=errors,
            warnings=warnings,
            info=infos,
            compliance_gaps=[i.description for i in errors if i.issue_type == "compliance"],
            style_issues=[i.description for i in warnings if i.issue_type == "style"],
            cross_section_conflicts=response.get("conflicts", []),
            quality_score=quality_score,
            is_ready_to_submit=(len(errors) == 0),
            primary_concern=response.get("primary_concern"),
            recommendations=response.get("recommendations", [])[:3],
            estimated_fix_time=response.get("estimated_fix_time", "medium"),
            validated_at=datetime.utcnow().isoformat(),
        )

        logger.info(
            f"Validation complete: {quality_score:.0f}/100, "
            f"{len(errors)} errors, {len(warnings)} warnings, {len(infos)} info"
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
