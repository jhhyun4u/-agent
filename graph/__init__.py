"""LangGraph 그래프 모듈

v3.1.1 (Phased Supervisor) 지원 + MCP 통합
"""

# v3.1.1 Phased Supervisor (현재)
from .phased_supervisor import build_phased_supervisor_graph
from .phase_nodes import (
    phase_1_research_node,
    compress_phase_1_node,
    phase_2_analysis_node,
    compress_phase_2_node,
    phase_3_plan_node,
    compress_phase_3_node,
    phase_4_implement_node,
    compress_phase_4_node,
    phase_5_critique_node,
    phase_5_revise_node,
    phase_5_finalize_node,
    decide_quality_action,
)
from .hitl_gates import (
    HITLDecision,
    evaluate_hitl_gate,
    make_hitl_gate,
)
from .mock_data import (
    MOCK_PHASE1_RESULT,
    MOCK_PHASE2_RESULT,
    MOCK_PHASE3_RESULT,
    MOCK_PHASE4_RESULT,
    MOCK_PHASE5_RESULT,
)

__all__ = [
    # v3.0 (레거시)
    "SupervisorNode",
    "build_supervisor_graph",
    "hitl_strategy_gate",
    "hitl_personnel_gate",
    "hitl_final_gate",
    # v3.1.1 (현재)
    "build_phased_supervisor_graph",
    "phase_1_research_node",
    "compress_phase_1_node",
    "phase_2_analysis_node",
    "compress_phase_2_node",
    "phase_3_plan_node",
    "compress_phase_3_node",
    "phase_4_implement_node",
    "compress_phase_4_node",
    "phase_5_critique_node",
    "phase_5_revise_node",
    "phase_5_finalize_node",
    "decide_quality_action",
    "HITLDecision",
    "evaluate_hitl_gate",
    "make_hitl_gate",
    "MOCK_PHASE1_RESULT",
    "MOCK_PHASE2_RESULT",
    "MOCK_PHASE3_RESULT",
    "MOCK_PHASE4_RESULT",
    "MOCK_PHASE5_RESULT",
]
