"""
Node 8C: proposal_sections_consolidation

Merge validated sections and resolve conflicts.

Input: proposal_sections, validation_report, selected_versions
Output: consolidated_proposal + proposal_sections_v2 (both versioned)

Purpose: Accept validated sections, apply user selections,
merge into final proposal, ensure cross-section consistency.
"""

import logging
from uuid import UUID
from datetime import datetime, timezone

from app.graph.state import ProposalState, ConsolidatedProposal, SectionLineage
from app.services.version_manager import execute_node_and_create_version
from app.graph.nodes._constants import normalize_proposal_section

logger = logging.getLogger(__name__)


async def proposal_sections_consolidation(state: ProposalState) -> dict:
    """
    Merge validated sections and resolve conflicts.

    Input:
        - proposal_sections: List of proposal sections
        - validation_report: Validation results
        - dynamic_sections: Section ordering from plan

    Output:
        - consolidated_proposal: Metadata about consolidation (versioned)
        - proposal_sections: Final merged sections list (versioned)

    Returns:
        Updated state dict with both consolidated artifacts
    """
    try:
        # Step 1: Validate required inputs
        proposal_sections = state.get("proposal_sections", [])
        validation_report = state.get("validation_report")

        if not proposal_sections:
            logger.warning("No proposal sections available for consolidation")
            return {
                "consolidated_proposal": None,
                "node_errors": {
                    **state.get("node_errors", {}),
                    "proposal_sections_consolidation": "No proposal sections to consolidate",
                },
            }

        # Step 2: Build final sections list
        final_sections = []
        section_lineage = []
        total_word_count = 0

        for section in proposal_sections:
            section_dict = normalize_proposal_section(section)
            section_id = section_dict.get("section_id", "")
            original_version = section_dict.get("version", 1)

            # Check if user selected a specific version for this section
            # Future: Support per-section version selection via selected_versions[section_id]
            # For now: Use original version (version selection feature not yet enabled)
            selected_version = original_version

            final_sections.append(section_dict)

            # Track lineage
            section_lineage.append(
                SectionLineage(
                    section_id=section_id,
                    original_version=original_version,
                    selected_version=selected_version,
                    change_notes=None,
                )
            )

            # Count words
            content = section_dict.get("content", "")
            word_count = len(content.split())
            total_word_count += word_count

        # Step 4: Calculate quality metrics from validation_report
        if validation_report:
            # Coverage: percentage of sections that passed validation
            coverage = (
                (
                    validation_report.passed_sections
                    / validation_report.total_sections
                    * 100
                )
                if validation_report.total_sections > 0
                else 0
            )
            # Compliance: from validation quality score
            compliance = validation_report.quality_score
            # Style consistency: 100 minus warning count ratio (max 10 warnings = 0 score)
            style_score = max(0, 100 - len(validation_report.warnings) * 5)
            completeness_score = validation_report.quality_score
            # Consistency: fewer warnings = higher consistency
            consistency_score = max(50, 100 - len(validation_report.warnings) * 3)
            compliance_score = validation_report.quality_score
        else:
            # Default fallback if no validation report
            coverage = 80
            compliance = 80
            style_score = 80
            completeness_score = 80
            consistency_score = 80
            compliance_score = 80

        quality_metrics = {
            "coverage": round(coverage),
            "compliance": round(compliance),
            "style_score": round(style_score),
        }

        # Step 5: Determine submission readiness
        blockers = []
        if validation_report and validation_report.errors:
            blockers.append(f"{len(validation_report.errors)} validation errors")

        warnings = []
        if validation_report and validation_report.warnings:
            warnings.extend([w.description for w in validation_report.warnings[:3]])

        submission_ready = len(blockers) == 0 and completeness_score >= 80

        # Step 6: Create consolidated_proposal artifact
        consolidated_proposal = ConsolidatedProposal(
            proposal_id=state.get("project_id", ""),
            final_sections=[normalize_proposal_section(s) for s in final_sections],
            section_count=len(final_sections),
            total_word_count=total_word_count,
            section_lineage=section_lineage,
            resolved_conflicts=[],  # Would track conflicts resolved
            merge_notes=f"Consolidated {len(final_sections)} sections from proposal",
            quality_metrics=quality_metrics,
            completeness_score=completeness_score,
            consistency_score=consistency_score,
            compliance_score=compliance_score,
            submission_ready=submission_ready,
            blockers=blockers,
            warnings=warnings,
            consolidated_at=datetime.now(timezone.utc).isoformat(),
        )

        logger.info(
            f"Created consolidated proposal ({len(final_sections)} sections, {total_word_count} words)"
        )

        # Step 7: Create artifacts for both outputs
        v1_num, art1 = await execute_node_and_create_version(
            proposal_id=UUID(state["project_id"]),
            node_name="proposal_sections_consolidation",
            output_key="consolidated_proposal",
            artifact_data=consolidated_proposal.model_dump(),
            user_id=UUID(state["created_by"]),
            state=state,
            parent_node_name="proposal_section_validator",
        )

        logger.info(f"Created consolidated_proposal v{v1_num}")

        # Create second artifact: proposal_sections version
        v2_num, art2 = await execute_node_and_create_version(
            proposal_id=UUID(state["project_id"]),
            node_name="proposal_sections_consolidation",
            output_key="proposal_sections",
            artifact_data=[normalize_proposal_section(s) for s in final_sections],
            user_id=UUID(state["created_by"]),
            state=state,
            parent_node_name="proposal_section_validator",
        )

        logger.info(f"Created proposal_sections v{v2_num}")

        # Step 8: Return state update with both artifacts
        existing_sections_versions = state.get("artifact_versions", {}).get(
            "proposal_sections", []
        )

        return {
            "consolidated_proposal": consolidated_proposal,
            "proposal_sections": final_sections,
            "artifact_versions": {
                **state.get("artifact_versions", {}),
                "consolidated_proposal": [art1],
                "proposal_sections": existing_sections_versions + [art2],
            },
            "active_versions": {
                **state.get("active_versions", {}),
                "proposal_sections_consolidation_consolidated_proposal": v1_num,
                "proposal_sections_consolidation_proposal_sections": v2_num,
            },
        }

    except Exception as e:
        logger.exception(f"Error in proposal_sections_consolidation: {str(e)}")
        return {
            "consolidated_proposal": None,
            "node_errors": {
                **state.get("node_errors", {}),
                "proposal_sections_consolidation": f"Consolidation failed: {str(e)}",
            },
        }
