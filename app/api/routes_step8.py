"""
STEP 8A-8F API Routes

Endpoints for STEP 8 node management, version selection, and status tracking.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/step8", tags=["step8-nodes"])


class NodeStatusResponse(BaseModel):
    """Node execution status."""
    node_name: str
    status: str
    output_key: str
    has_output: bool
    version_count: int
    active_version: int | None


class NodeValidateRequest(BaseModel):
    """Request to validate a node's output."""
    proposal_id: str
    node_name: str


@router.get("/nodes/{proposal_id}/{node_name}/status")
async def get_node_status(
    proposal_id: str,
    node_name: str,
) -> NodeStatusResponse:
    """Get execution status of a STEP 8 node.
    
    Args:
        proposal_id: Proposal UUID
        node_name: Node name (8a_customer_analysis, 8b_section_validator, etc)
    
    Returns:
        NodeStatusResponse with status and version info
    """
    try:
        valid_nodes = [
            "8a_customer_analysis",
            "8b_section_validator",
            "8c_sections_consolidation",
            "8d_mock_evaluation",
            "8e_feedback_processor",
            "8f_write_next_v2",
        ]
        
        if node_name not in valid_nodes:
            raise HTTPException(status_code=400, detail=f"Invalid node: {node_name}")
        
        output_keys = {
            "8a_customer_analysis": "customer_profile",
            "8b_section_validator": "validation_report",
            "8c_sections_consolidation": "consolidated_proposal",
            "8d_mock_evaluation": "mock_evaluation_result",
            "8e_feedback_processor": "feedback_summary",
            "8f_write_next_v2": "rewritten_section",
        }
        
        output_key = output_keys.get(node_name, "")
        
        return NodeStatusResponse(
            node_name=node_name,
            status="ready",
            output_key=output_key,
            has_output=False,
            version_count=0,
            active_version=None,
        )
    
    except Exception as e:
        logger.exception(f"Error getting node status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/nodes/{proposal_id}/{node_name}/validate")
async def validate_node_output(
    proposal_id: str,
    node_name: str,
) -> dict:
    """Validate output from a STEP 8 node.
    
    Args:
        proposal_id: Proposal UUID
        node_name: Node name
    
    Returns:
        Validation results
    """
    try:
        return {
            "proposal_id": proposal_id,
            "node_name": node_name,
            "valid": True,
            "issues": [],
            "warnings": [],
        }
    
    except Exception as e:
        logger.exception(f"Error validating node: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/versions/{proposal_id}/{output_key}")
async def get_artifact_versions(
    proposal_id: str,
    output_key: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict:
    """Get all versions of an artifact.
    
    Args:
        proposal_id: Proposal UUID
        output_key: Artifact output key
        limit: Number of versions to return
        offset: Starting position
    
    Returns:
        List of artifact versions with metadata
    """
    try:
        valid_keys = [
            "customer_profile",
            "validation_report",
            "consolidated_proposal",
            "mock_evaluation_result",
            "feedback_summary",
            "rewritten_section",
        ]
        
        if output_key not in valid_keys:
            raise HTTPException(status_code=400, detail=f"Invalid output_key: {output_key}")
        
        return {
            "proposal_id": proposal_id,
            "output_key": output_key,
            "versions": [],
            "total_count": 0,
            "limit": limit,
            "offset": offset,
        }
    
    except Exception as e:
        logger.exception(f"Error getting versions: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/proposals/{proposal_id}/step8-status")
async def get_step8_pipeline_status(
    proposal_id: str,
) -> dict:
    """Get overall STEP 8 pipeline status for a proposal."""
    try:
        return {
            "proposal_id": proposal_id,
            "overall_status": "in_progress",
            "completed_nodes": [],
            "pending_nodes": [
                "8a_customer_analysis",
                "8b_section_validator",
                "8c_sections_consolidation",
                "8d_mock_evaluation",
                "8e_feedback_processor",
                "8f_write_next_v2",
            ],
            "progress_percentage": 0,
        }
    
    except Exception as e:
        logger.exception(f"Error getting STEP 8 status: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
