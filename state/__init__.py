"""State 모듈 - v3.0 + v3.1.1 State 스키마"""

# v3.0 State (레거시)
from .proposal_state import (
    ProposalState,
    SectionDraft,
    EvaluationCriterion,
    PersonnelAssignment,
    initialize_proposal_state,
)

from .supervisor_state import (
    SupervisorState,
    WorkflowPlan,
    AgentStatusUpdate,
    DynamicDecision,
    initialize_supervisor_state,
)

from .agent_states import (
    RFPAnalysisState,
    StrategyState,
    SectionGenerationState,
    QualityState,
    DocumentState,
    RFPAnalysisOutput,
    StrategyOutput,
    QualityOutput,
)

# v3.1.1 State (현재, Phase 기반)
from .phased_state import (
    PhasedSupervisorState,
    initialize_phased_supervisor_state,
)

from .phase_artifacts import (
    PhaseArtifact_1_Research,
    PhaseArtifact_2_Analysis,
    PhaseArtifact_3_Plan,
    PhaseArtifact_4_Implement,
    PhaseResult,
)

__all__ = [
    # v3.0 ProposalState
    "ProposalState",
    "SectionDraft",
    "EvaluationCriterion",
    "PersonnelAssignment",
    "initialize_proposal_state",
    # v3.0 SupervisorState
    "SupervisorState",
    "WorkflowPlan",
    "AgentStatusUpdate",
    "DynamicDecision",
    "initialize_supervisor_state",
    # v3.0 Agent States
    "RFPAnalysisState",
    "StrategyState",
    "SectionGenerationState",
    "QualityState",
    "DocumentState",
    "RFPAnalysisOutput",
    "StrategyOutput",
    "QualityOutput",
    # v3.1.1 PhasedSupervisorState
    "PhasedSupervisorState",
    "initialize_phased_supervisor_state",
    # v3.1.1 Phase Artifacts
    "PhaseArtifact_1_Research",
    "PhaseArtifact_2_Analysis",
    "PhaseArtifact_3_Plan",
    "PhaseArtifact_4_Implement",
    "PhaseResult",
]
