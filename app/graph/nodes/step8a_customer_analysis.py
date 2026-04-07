"""
Node 8A: proposal_customer_analysis

Deep client intelligence analysis for proposal strategy.

Input: rfp_analysis, strategy, kb_refs
Output: customer_profile (versioned artifact)

Purpose: Extract and synthesize customer decision-making patterns,
budget authority, pain points, and stakeholder analysis.
"""

import logging
from uuid import UUID

from app.graph.state import ProposalState, CustomerProfile
from app.services.version_manager import execute_node_and_create_version
from app.services.claude_client import claude_generate
from app.prompts.step8a import CUSTOMER_INTELLIGENCE_PROMPT

logger = logging.getLogger(__name__)


async def proposal_customer_analysis(state: ProposalState) -> dict:
    """
    Deep client intelligence analysis.

    Input:
        - rfp_analysis: RFP analysis results
        - strategy: Proposal strategy
        - kb_references: Knowledge base references

    Output:
        - customer_profile: Structured customer profile (versioned)

    Returns:
        Updated state dict with customer_profile and version info
    """
    try:
        # Step 1: Validate required inputs exist
        rfp_analysis = state.get("rfp_analysis")
        if not rfp_analysis:
            logger.warning("No RFP analysis available for proposal_customer_analysis")
            return {
                "customer_profile": None,
                "node_errors": {
                    **state.get("node_errors", {}),
                    "proposal_customer_analysis": "Missing rfp_analysis input",
                },
            }

        # Step 2: Gather context data
        strategy = state.get("strategy")
        kb_refs = state.get("kb_references", [])
        competitor_refs = state.get("competitor_refs", [])

        # Build context for Claude
        kb_context = []
        if kb_refs:
            kb_context.extend(
                [
                    f"- {ref.get('title', 'Reference')}: {ref.get('summary', '')}"
                    for ref in kb_refs[:5]
                ]
            )  # Limit to 5 refs
        if competitor_refs:
            kb_context.extend(
                [
                    f"- Competitor: {ref.get('name', 'Unknown')}"
                    for ref in competitor_refs[:3]
                ]
            )

        # Step 3: Call Claude for analysis
        prompt = CUSTOMER_INTELLIGENCE_PROMPT.format(
            rfp_analysis=rfp_analysis.model_dump_json()
            if hasattr(rfp_analysis, "model_dump_json")
            else str(rfp_analysis),
            strategy=strategy.model_dump_json()
            if strategy and hasattr(strategy, "model_dump_json")
            else "{}",
            kb_references="\n".join(kb_context)
            if kb_context
            else "No KB references available",
        )

        logger.info(
            f"Calling Claude for customer analysis (proposal {state.get('project_id')})"
        )

        response = await claude_generate(
            prompt=prompt,
            response_format="json",
            max_tokens=3500,
            step_name="proposal_customer_analysis",
        )

        # Step 4: Parse response into Pydantic model
        customer_profile = CustomerProfile(**response)

        logger.info(f"Generated customer profile for {customer_profile.client_org}")

        # Step 5: Create version artifact
        version_num, artifact_version = await execute_node_and_create_version(
            proposal_id=UUID(state["project_id"]),
            node_name="proposal_customer_analysis",
            output_key="customer_profile",
            artifact_data=customer_profile.model_dump(),
            user_id=UUID(state["created_by"]),
            state=state,
            parent_node_name="strategy_generate",
        )

        logger.info(
            f"Created customer_profile v{version_num} for proposal {state['project_id']}"
        )

        # Step 6: Return state update
        return {
            "customer_profile": customer_profile,
            "artifact_versions": {"customer_profile": [artifact_version]},
            "active_versions": {
                "proposal_customer_analysis_customer_profile": version_num
            },
        }

    except Exception as e:
        logger.exception(f"Error in proposal_customer_analysis: {str(e)}")
        return {
            "customer_profile": None,
            "node_errors": {
                **state.get("node_errors", {}),
                "proposal_customer_analysis": f"Analysis failed: {str(e)}",
            },
        }
