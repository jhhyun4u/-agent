"""
STEP 8A-8F: Artifact Versioning Node Schemas

Single canonical definitions live in app.graph.state.
This module re-exports them for backward compatibility.
"""

# Re-export canonical models from state
from app.graph.state import (
    Stakeholder,
    CustomerProfile,
    ValidationIssue,
    ValidationReport,
    SectionLineage,
    ConsolidatedProposal,
    ScoreComponent,
    MockEvalResult as MockEvaluationResult,
    FeedbackItem,
    FeedbackSummary,
    ArtifactVersion,
    VersionSelection,
)

# Aliases kept for tests that import step8_schemas directly
StakeholderProfile = Stakeholder
WriteNextV2Output = None  # Removed duplicate; use proposal_sections in state


# ============================================
# Additional helper models not in state
# ============================================
from typing import List, Optional  # noqa: E402

from pydantic import BaseModel, Field  # noqa: E402


class ConsolidatedSection(BaseModel):
    """Single consolidated section after merging."""
    section_name: str = Field(..., description="Section name")
    content: str = Field(..., description="Consolidated content (Markdown)")
    source_sections: List[str] = Field(
        default=[],
        description="Original sections merged to create this"
    )
    word_count: int = Field(default=0, description="Content word count")
    conflicts_resolved: int = Field(
        default=0,
        description="Number of conflicts resolved during consolidation"
    )
    quality_notes: Optional[str] = Field(
        default=None,
        description="Quality assessment notes"
    )


class EvaluationDimension(BaseModel):
    """Single evaluation dimension scoring."""
    dimension_name: str = Field(..., description="Evaluation dimension")
    max_points: float = Field(..., description="Maximum possible points")
    awarded_points: float = Field(
        ...,
        description="Points awarded by mock evaluator",
        ge=0.0
    )
    rationale: Optional[str] = Field(
        default=None,
        description="Evaluator rationale for score"
    )
    improvement_areas: List[str] = Field(
        default=[],
        description="Areas suggested for improvement"
    )


class ImprovementAction(BaseModel):
    """Single improvement action from mock evaluation feedback."""
    priority: str = Field(
        ...,
        description="Priority level (high/medium/low)",
        pattern="^(high|medium|low)$"
    )
    target_section: str = Field(..., description="Section to improve")
    action: str = Field(..., description="Specific improvement action")
    expected_impact: str = Field(
        ...,
        description="Expected impact on score",
        pattern="^(critical|significant|moderate|minor)$"
    )
    effort_estimate: Optional[str] = Field(
        default=None,
        description="Estimated effort (quick/medium/extensive)"
    )


__all__ = [
    # Re-exports from state
    "Stakeholder",
    "StakeholderProfile",
    "CustomerProfile",
    "ValidationIssue",
    "ValidationReport",
    "SectionLineage",
    "ConsolidatedProposal",
    "ScoreComponent",
    "MockEvaluationResult",
    "FeedbackItem",
    "FeedbackSummary",
    "ArtifactVersion",
    "VersionSelection",
    # Local helpers
    "ConsolidatedSection",
    "EvaluationDimension",
    "ImprovementAction",
]
