"""
Node 8C: proposal_sections_consolidation

Merge and consolidate proposal sections, resolve conflicts.

Input: dynamic_sections, validation_report
Output: consolidated_proposal (versioned artifact)

Purpose: Merge parallel sections, resolve conflicts, ensure coherence.
"""

import logging
from uuid import UUID

from app.graph.state import ProposalState, ConsolidatedProposal
from app.models.step8_schemas import ConsolidatedSection
from app.services.version_manager import execute_node_and_create_version
from app.services.claude_client import claude_generate
from app.prompts.step8c import CONSOLIDATION_PROMPT

logger = logging.getLogger(__name__)


async def proposal_sections_consolidation(state: ProposalState) -> dict:
    """
    Consolidate and merge proposal sections.

    Input:
        - dynamic_sections: Proposal sections
        - validation_report: Validation findings

    Output:
        - consolidated_proposal: Merged proposal (versioned)

    Returns:
        Updated state dict with consolidated_proposal and version info
    """
    try:
        sections = state.get("dynamic_sections", [])
        if not sections:
            logger.warning("No sections to consolidate")
            return {
                "consolidated_proposal": None,
                "node_errors": {
                    **state.get("node_errors", {}),
                    "proposal_sections_consolidation": "No sections available",
                },
            }

        sections_text = "\n\n".join(
            [f"## {sec.get('title')}\n{sec.get('content', '')}" for sec in sections[:20]]
        )

        prompt = CONSOLIDATION_PROMPT.format(
            proposal_sections=sections_text,
            total_sections=len(sections),
        )

        logger.info(f"Consolidating {len(sections)} sections")

        response = await claude_generate(
            prompt=prompt,
            response_format="json",
            max_tokens=5000,
            step_name="proposal_sections_consolidation",
        )

        # Parse consolidated sections
        final_sections_list = response.get("sections", [])
        total_words = sum(sec.get("word_count", 0) for sec in final_sections_list)

        # Extract quality metrics
        quality_data = response.get("quality_metrics", {})
        completeness = int(quality_data.get("completeness_score", 75))
        consistency = int(quality_data.get("consistency_score", 75))
        compliance = int(quality_data.get("compliance_score", 75))

        # Extract conflict resolution info
        conflicts = response.get("resolved_conflicts", [])
        lineage_data = response.get("section_lineage", [])
        section_lineage = []
        for item in lineage_data:
            try:
                from app.graph.state import SectionLineage
                sl = SectionLineage(
                    section_id=item.get("section_id", ""),
                    original_version=item.get("original_version", 1),
                    selected_version=item.get("selected_version", 1),
                    change_notes=item.get("change_notes"),
                )
                section_lineage.append(sl)
            except Exception as e:
                logger.warning(f"Failed to parse section lineage: {e}")

        # Create consolidated proposal
        from datetime import datetime
        consolidated_proposal = ConsolidatedProposal(
            proposal_id=state["project_id"],
            final_sections=final_sections_list,
            section_count=len(final_sections_list),
            total_word_count=total_words,
            section_lineage=section_lineage,
            resolved_conflicts=conflicts,
            merge_notes=response.get("merge_notes"),
            quality_metrics=quality_data,
            completeness_score=completeness,
            consistency_score=consistency,
            compliance_score=compliance,
            submission_ready=(completeness >= 70 and consistency >= 70),
            blockers=response.get("blockers", []),
            warnings=response.get("warnings", []),
            consolidated_at=datetime.utcnow().isoformat(),
        )

        logger.info(f"Consolidated {total_words} words across {len(final_sections_list)} sections")

        version_num, artifact_version = await execute_node_and_create_version(
            proposal_id=UUID(state["project_id"]),
            node_name="proposal_sections_consolidation",
            output_key="consolidated_proposal",
            artifact_data=consolidated_proposal.model_dump(),
            user_id=UUID(state["created_by"]),
            state=state,
            parent_node_name="proposal_section_validator",
        )

        logger.info(f"Created consolidated_proposal v{version_num}")

        return {
            "consolidated_proposal": consolidated_proposal,
            "artifact_versions": {"consolidated_proposal": [artifact_version]},
            "active_versions": {
                "proposal_sections_consolidation_consolidated_proposal": version_num
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
