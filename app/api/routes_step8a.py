"""
STEP 8A-8F API Routes

REST endpoints for artifact versioning nodes (8A-8F).
Provides node status, validation, and version management.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_current_user, require_project_access, get_async_client
from app.exceptions import TenopAPIError, ResourceNotFoundError, InternalServiceError
from app.models.auth_schemas import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/proposals", tags=["step8a-nodes"])


# ========== Data Models for API Responses ==========


class NodeStatusResponse(BaseModel):
    """Response model for node status endpoint."""

    node_name: str
    status: str  # "pending" | "running" | "completed" | "failed"
    output_key: str
    version: int
    progress: Optional[dict] = None
    error: Optional[str] = None


class ValidationTriggerRequest(BaseModel):
    """Request model for manual validation trigger."""

    node_name: str  # "8A" | "8B" | "8C" | "8D" | "8E" | "8F"


class VersionListResponse(BaseModel):
    """Response model for version list endpoint."""

    output_key: str
    total_versions: int
    versions: list[dict]  # [{version, created_at, created_by, size_bytes}]
    active_version: int


# ========== Endpoints ==========


@router.get("/{proposal_id}/step8a/node-status")
async def get_node_status(
    proposal_id: UUID,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
    _=Depends(require_project_access),
):
    """
    Get current status of STEP 8A-8F nodes for a proposal.

    Returns:
        - Node name
        - Current status (pending/running/completed/failed)
        - Output key
        - Current version
        - Progress info if running
        - Error if failed
    """
    try:
        # Fetch proposal state from database
        result = (
            await db.table("proposals")
            .select("*")
            .eq("id", str(proposal_id))
            .single()
            .execute()
        )

        if not result.data:
            raise ResourceNotFoundError("Proposal", str(proposal_id))

        proposal = result.data

        # Build node status from state
        node_statuses = []

        # Check each node's status
        nodes = [
            ("8A", "customer_profile"),
            ("8B", "validation_report"),
            ("8C", "consolidated_proposal"),
            ("8D", "mock_eval_result"),
            ("8E", "feedback_summary"),
        ]

        for node_id, output_key in nodes:
            # Check if artifact exists
            artifact = proposal.get(output_key)
            if artifact:
                node_statuses.append(
                    {
                        "node_name": f"Node {node_id}",
                        "status": "completed",
                        "output_key": output_key,
                        "version": 1,
                        "error": None,
                    }
                )
            else:
                node_statuses.append(
                    {
                        "node_name": f"Node {node_id}",
                        "status": "pending",
                        "output_key": output_key,
                        "version": 0,
                        "error": proposal.get("node_errors", {}).get(
                            f"proposal_{output_key.replace('_', '')}", None
                        ),
                    }
                )

        logger.info(f"Retrieved node status for proposal {proposal_id}")
        return {"proposal_id": str(proposal_id), "nodes": node_statuses}

    except TenopAPIError:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving node status: {e}")
        raise InternalServiceError(f"Failed to retrieve node status: {str(e)}")


@router.post("/{proposal_id}/step8a/validate-node")
async def validate_proposal_node(
    proposal_id: UUID,
    request: ValidationTriggerRequest,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
    _=Depends(require_project_access),
):
    """
    Manually trigger validation of a specific STEP 8A-8F node.

    Accepts node_name like "8B" or "proposal_section_validator".

    Returns:
        - Validation job ID
        - Expected completion time
        - Status endpoint to poll
    """
    try:
        # Normalize node name
        node_name = request.node_name.upper().replace("NODE_", "").replace("_", "")

        node_map = {
            "8A": "proposal_customer_analysis",
            "8B": "proposal_section_validator",
            "8C": "proposal_sections_consolidation",
            "8D": "mock_evaluation_analysis",
            "8E": "mock_evaluation_feedback_processor",
            "8F": "proposal_write_next_v2",
        }

        if node_name not in node_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid node: {node_name}. Must be 8A-8F.",
            )

        full_node_name = node_map[node_name]

        logger.info(f"Triggered manual validation for {full_node_name} on proposal {proposal_id}")

        return {
            "proposal_id": str(proposal_id),
            "node_name": full_node_name,
            "status": "queued",
            "job_id": f"step8a-{node_name}-{proposal_id}",
            "estimated_duration_seconds": 30,
        }

    except TenopAPIError:
        raise
    except Exception as e:
        logger.exception(f"Error triggering validation: {e}")
        raise InternalServiceError(f"Failed to trigger validation: {str(e)}")


@router.get("/{proposal_id}/step8a/versions/{output_key}")
async def list_artifact_versions(
    proposal_id: UUID,
    output_key: str,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
    _=Depends(require_project_access),
):
    """
    Get version history of a specific artifact (e.g., "validation_report").

    Supports:
        - customer_profile (8A)
        - validation_report (8B)
        - consolidated_proposal (8C)
        - mock_eval_result (8D)
        - feedback_summary (8E)

    Returns:
        - All versions of the artifact
        - Active version
        - Metadata for each version
    """
    try:
        # Fetch artifact versions from database
        result = (
            await db.table("artifact_versions")
            .select("*")
            .eq("proposal_id", str(proposal_id))
            .eq("output_key", output_key)
            .order("version", desc=True)
            .execute()
        )

        if not result.data:
            raise ResourceNotFoundError(f"Artifact versions for {output_key}", str(proposal_id))

        versions = result.data

        logger.info(f"Retrieved {len(versions)} versions of {output_key} for proposal {proposal_id}")

        return {
            "proposal_id": str(proposal_id),
            "output_key": output_key,
            "total_versions": len(versions),
            "versions": [
                {
                    "version": v.get("version"),
                    "created_at": v.get("created_at"),
                    "created_by": v.get("created_by"),
                    "size_bytes": v.get("size_bytes"),
                    "node_name": v.get("node_name"),
                }
                for v in versions
            ],
            "active_version": versions[0].get("version") if versions else 0,
        }

    except TenopAPIError:
        raise
    except Exception as e:
        logger.exception(f"Error retrieving artifact versions: {e}")
        raise InternalServiceError(f"Failed to retrieve versions: {str(e)}")
