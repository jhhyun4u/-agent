"""
STEP 8 Review API Routes

Endpoints for STEP 8 (Node 8A-8F) proposal review and optimization.
Provides access to AI-powered issue flagging, version comparison, and approval workflow.
"""

import logging
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from app.api.deps import get_current_user, require_project_access, get_async_client
from app.exceptions import TenopAPIError, ResourceNotFoundError, InternalServiceError
from app.models.auth_schemas import CurrentUser

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/proposals", tags=["step8-review"])


# ============ Request/Response Models ============

class NodeStatusModel(BaseModel):
    """Status of a single STEP 8 node."""
    node_name: str = Field(..., description="Node name (8A-8F)")
    status: str = Field(..., description="pending|running|completed|failed")
    output_key: str = Field(..., description="Output artifact key")
    version: int = Field(default=0, description="Current version number")
    updated_at: str = Field(..., description="ISO datetime of last update")
    error: Optional[str] = Field(None, description="Error message if failed")


class Step8StatusResponse(BaseModel):
    """Overall STEP 8 workflow status."""
    proposal_id: str
    nodes: list[NodeStatusModel]
    overall_progress: int = Field(..., ge=0, le=100, description="0-100%")
    last_updated: str


class AIIssueFlagModel(BaseModel):
    """AI-detected issue in proposal."""
    issue_id: str
    section_id: str
    severity: str = Field(..., description="critical|major|minor")
    category: str = Field(..., description="compliance|clarity|consistency|style|strategy")
    description: str
    suggestion: str
    flagged_text: Optional[str] = None


class ReviewPanelDataResponse(BaseModel):
    """Data for AI-powered review panel."""
    proposal_id: str
    issues: list[AIIssueFlagModel]
    total_issues: int
    critical_count: int
    can_proceed: bool = Field(..., description="true if no critical issues")


class CustomerProfileModel(BaseModel):
    """Customer profile data from STEP 8A."""
    proposal_id: str
    client_name: str
    stakeholders: list[dict]
    decision_drivers: list[str]
    budget_authority: str
    pain_points: list[str]
    created_at: str


class ValidationReportModel(BaseModel):
    """Validation report from STEP 8B."""
    proposal_id: str
    pass_validation: bool
    quality_score: int = Field(..., ge=0, le=100)
    critical_issues_count: int
    major_issues_count: int
    minor_issues_count: int
    compliance_status: str
    created_at: str


class ConsolidatedProposalModel(BaseModel):
    """Consolidated proposal from STEP 8C."""
    proposal_id: str
    total_sections: int
    final_sections: list[str]
    executive_summary: str
    created_at: str


class MockEvalResultModel(BaseModel):
    """Mock evaluation result from STEP 8D."""
    proposal_id: str
    total_score: int = Field(..., ge=0, le=100)
    win_probability: float = Field(..., ge=0, le=1)
    dimensions: list[dict]
    created_at: str


class FeedbackSummaryModel(BaseModel):
    """Feedback summary from STEP 8E."""
    proposal_id: str
    key_findings: str
    critical_gaps: list[dict]
    quick_wins: list[dict]
    strategic_recommendations: list[str]
    score_improvement_projection: int = Field(..., ge=0, le=100)
    next_phase_guidance: str
    created_at: str


class RewriteHistoryModel(BaseModel):
    """Rewrite history from STEP 8F."""
    proposal_id: str
    current_section_index: int
    rewrite_iteration_count: int
    total_rewrites: int
    history: list[dict]
    created_at: str


class VersionMetadataModel(BaseModel):
    """Version metadata for an artifact."""
    version_id: str
    node_name: str
    version_number: int
    created_at: str
    created_by: str
    size_bytes: int
    description: Optional[str] = None
    change_summary: Optional[str] = None


class ApprovalRequestModel(BaseModel):
    """Request to approve proposal."""
    proposal_id: str
    approved_by: str


class FeedbackRequestModel(BaseModel):
    """Request to submit feedback."""
    feedback_text: str
    issue_ids: Optional[list[str]] = []


class RewriteRequestModel(BaseModel):
    """Request to trigger rewrite."""
    section_ids: Optional[list[str]] = None


# ============ Helper Functions ============

async def get_proposal_artifacts(db, proposal_id: str) -> dict:
    """Fetch all STEP 8 artifacts for a proposal."""
    try:
        result = await db.table("proposals").select("*").eq("id", proposal_id).single().execute()
        if not result.data:
            raise ResourceNotFoundError("Proposal", proposal_id)
        return result.data
    except Exception as e:
        logger.error(f"Error fetching proposal artifacts: {e}")
        raise InternalServiceError(f"Failed to fetch proposal: {str(e)}")


def build_node_status(node_data: dict, output_key: str) -> NodeStatusModel:
    """Build NodeStatusModel from artifact data."""
    return NodeStatusModel(
        node_name=node_data.get("node_name", "unknown"),
        status=node_data.get("status", "pending"),
        output_key=output_key,
        version=node_data.get("version", 0),
        updated_at=node_data.get("updated_at", datetime.utcnow().isoformat()),
        error=node_data.get("error"),
    )


# ============ API Endpoints ============

@router.get("/{proposal_id}/step8/status")
async def get_step8_status(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
    _=Depends(require_project_access),
) -> Step8StatusResponse:
    """
    GET /api/proposals/{id}/step8/status

    Get overall STEP 8 workflow status with all 6 node statuses.

    Returns:
        Step8StatusResponse with nodes array and overall progress percentage
    """
    try:
        artifacts = await get_proposal_artifacts(db, proposal_id)

        # Map artifact keys to nodes
        node_map = {
            "customer_profile": "step_8a",
            "validation_report": "step_8b",
            "consolidated_proposal": "step_8c",
            "mock_eval_result": "step_8d",
            "feedback_summary": "step_8e",
            "rewrite_history": "step_8f",
        }

        nodes = []
        for artifact_key, node_name in node_map.items():
            artifact = artifacts.get(artifact_key)
            status_str = "completed" if artifact else "pending"
            version = artifact.get("version", 0) if artifact else 0

            nodes.append(NodeStatusModel(
                node_name=node_name,
                status=status_str,
                output_key=artifact_key,
                version=version,
                updated_at=artifact.get("updated_at", datetime.utcnow().isoformat()) if artifact else datetime.utcnow().isoformat(),
                error=None,
            ))

        completed = sum(1 for n in nodes if n.status == "completed")
        overall_progress = int((completed / len(nodes)) * 100)

        return Step8StatusResponse(
            proposal_id=proposal_id,
            nodes=nodes,
            overall_progress=overall_progress,
            last_updated=datetime.utcnow().isoformat(),
        )
    except TenopAPIError:
        raise
    except Exception as e:
        logger.exception(f"Error getting STEP 8 status: {e}")
        raise InternalServiceError(f"Failed to get STEP 8 status: {str(e)}")


@router.get("/{proposal_id}/step8/customer-profile")
async def get_customer_profile(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
    _=Depends(require_project_access),
) -> CustomerProfileModel:
    """GET /api/proposals/{id}/step8/customer-profile"""
    try:
        artifacts = await get_proposal_artifacts(db, proposal_id)
        profile = artifacts.get("customer_profile")

        if not profile:
            raise ResourceNotFoundError("Customer Profile", proposal_id)

        return CustomerProfileModel(
            proposal_id=proposal_id,
            client_name=profile.get("client_name", "Unknown"),
            stakeholders=profile.get("stakeholders", []),
            decision_drivers=profile.get("decision_drivers", []),
            budget_authority=profile.get("budget_authority", ""),
            pain_points=profile.get("pain_points", []),
            created_at=profile.get("created_at", datetime.utcnow().isoformat()),
        )
    except TenopAPIError:
        raise
    except Exception as e:
        logger.exception(f"Error getting customer profile: {e}")
        raise InternalServiceError(f"Failed to get customer profile: {str(e)}")


@router.get("/{proposal_id}/step8/validation-report")
async def get_validation_report(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
    _=Depends(require_project_access),
) -> ValidationReportModel:
    """GET /api/proposals/{id}/step8/validation-report"""
    try:
        artifacts = await get_proposal_artifacts(db, proposal_id)
        report = artifacts.get("validation_report")

        if not report:
            raise ResourceNotFoundError("Validation Report", proposal_id)

        return ValidationReportModel(
            proposal_id=proposal_id,
            pass_validation=report.get("pass_validation", True),
            quality_score=report.get("quality_score", 0),
            critical_issues_count=report.get("critical_issues_count", 0),
            major_issues_count=report.get("major_issues_count", 0),
            minor_issues_count=report.get("minor_issues_count", 0),
            compliance_status=report.get("compliance_status", "Unknown"),
            created_at=report.get("created_at", datetime.utcnow().isoformat()),
        )
    except TenopAPIError:
        raise
    except Exception as e:
        logger.exception(f"Error getting validation report: {e}")
        raise InternalServiceError(f"Failed to get validation report: {str(e)}")


@router.get("/{proposal_id}/step8/consolidated-proposal")
async def get_consolidated_proposal(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
    _=Depends(require_project_access),
) -> ConsolidatedProposalModel:
    """GET /api/proposals/{id}/step8/consolidated-proposal"""
    try:
        artifacts = await get_proposal_artifacts(db, proposal_id)
        proposal = artifacts.get("consolidated_proposal")

        if not proposal:
            raise ResourceNotFoundError("Consolidated Proposal", proposal_id)

        return ConsolidatedProposalModel(
            proposal_id=proposal_id,
            total_sections=proposal.get("total_sections", 0),
            final_sections=proposal.get("final_sections", []),
            executive_summary=proposal.get("executive_summary", ""),
            created_at=proposal.get("created_at", datetime.utcnow().isoformat()),
        )
    except TenopAPIError:
        raise
    except Exception as e:
        logger.exception(f"Error getting consolidated proposal: {e}")
        raise InternalServiceError(f"Failed to get consolidated proposal: {str(e)}")


@router.get("/{proposal_id}/step8/mock-eval")
async def get_mock_eval_result(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
    _=Depends(require_project_access),
) -> MockEvalResultModel:
    """GET /api/proposals/{id}/step8/mock-eval"""
    try:
        artifacts = await get_proposal_artifacts(db, proposal_id)
        result = artifacts.get("mock_eval_result")

        if not result:
            raise ResourceNotFoundError("Mock Evaluation Result", proposal_id)

        return MockEvalResultModel(
            proposal_id=proposal_id,
            total_score=result.get("total_score", 0),
            win_probability=result.get("win_probability", 0.0),
            dimensions=result.get("dimensions", []),
            created_at=result.get("created_at", datetime.utcnow().isoformat()),
        )
    except TenopAPIError:
        raise
    except Exception as e:
        logger.exception(f"Error getting mock evaluation: {e}")
        raise InternalServiceError(f"Failed to get mock evaluation: {str(e)}")


@router.get("/{proposal_id}/step8/feedback-summary")
async def get_feedback_summary(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
    _=Depends(require_project_access),
) -> FeedbackSummaryModel:
    """GET /api/proposals/{id}/step8/feedback-summary"""
    try:
        artifacts = await get_proposal_artifacts(db, proposal_id)
        summary = artifacts.get("feedback_summary")

        if not summary:
            raise ResourceNotFoundError("Feedback Summary", proposal_id)

        return FeedbackSummaryModel(
            proposal_id=proposal_id,
            key_findings=summary.get("key_findings", ""),
            critical_gaps=summary.get("critical_gaps", []),
            quick_wins=summary.get("quick_wins", []),
            strategic_recommendations=summary.get("strategic_recommendations", []),
            score_improvement_projection=summary.get("score_improvement_projection", 0),
            next_phase_guidance=summary.get("next_phase_guidance", ""),
            created_at=summary.get("created_at", datetime.utcnow().isoformat()),
        )
    except TenopAPIError:
        raise
    except Exception as e:
        logger.exception(f"Error getting feedback summary: {e}")
        raise InternalServiceError(f"Failed to get feedback summary: {str(e)}")


@router.get("/{proposal_id}/step8/rewrite-history")
async def get_rewrite_history(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
    _=Depends(require_project_access),
) -> RewriteHistoryModel:
    """GET /api/proposals/{id}/step8/rewrite-history"""
    try:
        artifacts = await get_proposal_artifacts(db, proposal_id)
        history = artifacts.get("rewrite_history")

        if not history:
            raise ResourceNotFoundError("Rewrite History", proposal_id)

        return RewriteHistoryModel(
            proposal_id=proposal_id,
            current_section_index=history.get("current_section_index", 0),
            rewrite_iteration_count=history.get("rewrite_iteration_count", 0),
            total_rewrites=history.get("total_rewrites", 0),
            history=history.get("history", []),
            created_at=history.get("created_at", datetime.utcnow().isoformat()),
        )
    except TenopAPIError:
        raise
    except Exception as e:
        logger.exception(f"Error getting rewrite history: {e}")
        raise InternalServiceError(f"Failed to get rewrite history: {str(e)}")


@router.get("/{proposal_id}/step8/review-panel")
async def get_review_panel_data(
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
    _=Depends(require_project_access),
) -> ReviewPanelDataResponse:
    """GET /api/proposals/{id}/step8/review-panel - AI issue flagging data"""
    try:
        artifacts = await get_proposal_artifacts(db, proposal_id)
        issues_data = artifacts.get("ai_issues", {})

        issues = [
            AIIssueFlagModel(
                issue_id=issue.get("issue_id", ""),
                section_id=issue.get("section_id", ""),
                severity=issue.get("severity", "minor"),
                category=issue.get("category", "style"),
                description=issue.get("description", ""),
                suggestion=issue.get("suggestion", ""),
                flagged_text=issue.get("flagged_text"),
            )
            for issue in issues_data.get("issues", [])
        ]

        critical_count = sum(1 for i in issues if i.severity == "critical")
        can_proceed = critical_count == 0

        return ReviewPanelDataResponse(
            proposal_id=proposal_id,
            issues=issues,
            total_issues=len(issues),
            critical_count=critical_count,
            can_proceed=can_proceed,
        )
    except TenopAPIError:
        raise
    except Exception as e:
        logger.exception(f"Error getting review panel data: {e}")
        raise InternalServiceError(f"Failed to get review panel data: {str(e)}")


@router.get("/{proposal_id}/step8/versions/{node_id}")
async def get_version_history(
    proposal_id: str,
    node_id: str,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
    _=Depends(require_project_access),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> dict:
    """GET /api/proposals/{id}/step8/versions/{node_id} - Version history"""
    try:
        # Fetch version history from database
        result = await db.table("artifact_versions").select("*").eq(
            "proposal_id", proposal_id
        ).eq("node_id", node_id).order("version", desc=True).limit(limit).offset(offset).execute()

        versions = [
            VersionMetadataModel(
                version_id=v.get("version_id", ""),
                node_name=v.get("node_name", ""),
                version_number=v.get("version", 0),
                created_at=v.get("created_at", ""),
                created_by=v.get("created_by", "system"),
                size_bytes=v.get("size_bytes", 0),
                description=v.get("description"),
                change_summary=v.get("change_summary"),
            )
            for v in result.data or []
        ]

        return {
            "proposal_id": proposal_id,
            "node_id": node_id,
            "versions": [v.model_dump() for v in versions],
            "total_count": len(versions),
            "limit": limit,
            "offset": offset,
        }
    except TenopAPIError:
        raise
    except Exception as e:
        logger.exception(f"Error getting version history: {e}")
        raise InternalServiceError(f"Failed to get version history: {str(e)}")


@router.post("/{proposal_id}/step8/validate/{node_id}")
async def validate_node(
    proposal_id: str,
    node_id: str,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
    _=Depends(require_project_access),
) -> dict:
    """POST /api/proposals/{id}/step8/validate/{node_id} - Trigger node validation"""
    try:
        # Trigger validation in background
        # TODO: Queue validation job with background task queue

        return {
            "status": "success",
            "node_id": node_id,
            "proposal_id": proposal_id,
            "message": f"Validation triggered for {node_id}",
            "job_id": f"validate-{proposal_id}-{node_id}",
        }
    except TenopAPIError:
        raise
    except Exception as e:
        logger.exception(f"Error validating node: {e}")
        raise InternalServiceError(f"Failed to validate node: {str(e)}")


@router.post("/{proposal_id}/step8/approve")
async def approve_proposal(
    proposal_id: str,
    request: ApprovalRequestModel,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
    _=Depends(require_project_access),
) -> dict:
    """POST /api/proposals/{id}/step8/approve - Approve STEP 8 review"""
    try:
        # Update proposal status
        await db.table("proposals").update({
            "step8_approved": True,
            "step8_approved_at": datetime.utcnow().isoformat(),
            "step8_approved_by": request.approved_by,
        }).eq("id", proposal_id).execute()

        logger.info(f"Proposal {proposal_id} approved by {request.approved_by}")

        return {
            "status": "approved",
            "proposal_id": proposal_id,
            "approved_by": request.approved_by,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except TenopAPIError:
        raise
    except Exception as e:
        logger.exception(f"Error approving proposal: {e}")
        raise InternalServiceError(f"Failed to approve proposal: {str(e)}")


@router.post("/{proposal_id}/step8/feedback")
async def submit_feedback(
    proposal_id: str,
    request: FeedbackRequestModel,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
    _=Depends(require_project_access),
) -> dict:
    """POST /api/proposals/{id}/step8/feedback - Submit review feedback"""
    try:
        # Save feedback record
        feedback_data = {
            "proposal_id": proposal_id,
            "feedback_text": request.feedback_text,
            "issue_ids": request.issue_ids or [],
            "submitted_by": user.id,
            "submitted_at": datetime.utcnow().isoformat(),
        }

        result = await db.table("step8_feedback").insert([feedback_data]).execute()

        logger.info(f"Feedback submitted for proposal {proposal_id}")

        return {
            "status": "success",
            "feedback_id": result.data[0].get("id", "") if result.data else "",
            "proposal_id": proposal_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    except TenopAPIError:
        raise
    except Exception as e:
        logger.exception(f"Error submitting feedback: {e}")
        raise InternalServiceError(f"Failed to submit feedback: {str(e)}")


@router.post("/{proposal_id}/step8/rewrite")
async def trigger_rewrite(
    proposal_id: str,
    request: RewriteRequestModel,
    user: CurrentUser = Depends(get_current_user),
    db=Depends(get_async_client),
    _=Depends(require_project_access),
) -> dict:
    """POST /api/proposals/{id}/step8/rewrite - Trigger rewrite"""
    try:
        # Trigger rewrite job
        # TODO: Queue rewrite job with background task queue

        return {
            "status": "queued",
            "proposal_id": proposal_id,
            "job_id": f"rewrite-{proposal_id}",
            "section_ids": request.section_ids or [],
            "message": "Rewrite job queued",
        }
    except TenopAPIError:
        raise
    except Exception as e:
        logger.exception(f"Error triggering rewrite: {e}")
        raise InternalServiceError(f"Failed to trigger rewrite: {str(e)}")
