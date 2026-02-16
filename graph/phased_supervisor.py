"""
v3.1.1 Phased Supervisor 그래프 (직선 구조)

C-1 Fix: 자기 참조 엣지 제거, interrupt() 기반 HITL
C-3 Fix: Phase 5 내 critique ↔ revise 루프를 조건부 엣지로 구현

그래프 구조:
START
  ↓
Phase 1 (Research) → Compress 1 → HITL Gate 1
  ↓
Phase 2 (Analysis) → Compress 2 → HITL Gate 2
  ↓
Phase 3 (Plan) → Compress 3 → HITL Gate 3 (★필수)
  ↓
Phase 4 (Implement) → Compress 4 → HITL Gate 4
  ↓
Phase 5a (Critique) → [조건부] → Phase 5b (Revise) ↔ Phase 5a 루프
              ↓
         [pass] → Phase 5c (Finalize) → HITL Gate 5 (★필수)
  ↓
END
"""

import sys
import os
from pathlib import Path

# Add project root to path
_project_root = str(Path(__file__).parent.parent)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from typing import Literal

from state.phased_state import PhasedSupervisorState
from graph.phase_nodes import (
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
from graph.hitl_gates import make_hitl_gate


def build_phased_supervisor_graph():
    """
    v3.1.1 Phased Supervisor 그래프 구축
    
    C-1 Fix: 직선 구조, HITL 노드 내부에서 interrupt() 호출
    C-3 Fix: Phase 5 품질 루프를 조건부 엣지로 구현
    
    Returns:
        CompiledGraph: 메모리 체크포인트를 가진 컴파일된 그래프
    """

    builder = StateGraph(PhasedSupervisorState)

    # ── Phase 1: Research ──
    builder.add_node("phase_1_research", phase_1_research_node)
    builder.add_node("compress_1", compress_phase_1_node)
    builder.add_node("hitl_gate_1", make_hitl_gate(1))

    # ── Phase 2: Analysis ──
    builder.add_node("phase_2_analysis", phase_2_analysis_node)
    builder.add_node("compress_2", compress_phase_2_node)
    builder.add_node("hitl_gate_2", make_hitl_gate(2))

    # ── Phase 3: Plan ──
    builder.add_node("phase_3_plan", phase_3_plan_node)
    builder.add_node("compress_3", compress_phase_3_node)
    builder.add_node("hitl_gate_3", make_hitl_gate(3))

    # ── Phase 4: Implement ──
    builder.add_node("phase_4_implement", phase_4_implement_node)
    builder.add_node("compress_4", compress_phase_4_node)
    builder.add_node("hitl_gate_4", make_hitl_gate(4))

    # ── Phase 5: Test (3개 노드, C-3 Fix) ──
    builder.add_node("phase_5_critique", phase_5_critique_node)
    builder.add_node("phase_5_revise", phase_5_revise_node)
    builder.add_node("phase_5_finalize", phase_5_finalize_node)
    builder.add_node("hitl_gate_5", make_hitl_gate(5))

    # ═══ 직선 에지 (Phase → Compress → HITL) ═══

    # Phase 1
    builder.add_edge(START, "phase_1_research")
    builder.add_edge("phase_1_research", "compress_1")
    builder.add_edge("compress_1", "hitl_gate_1")
    builder.add_edge("hitl_gate_1", "phase_2_analysis")

    # Phase 2
    builder.add_edge("phase_2_analysis", "compress_2")
    builder.add_edge("compress_2", "hitl_gate_2")
    builder.add_edge("hitl_gate_2", "phase_3_plan")

    # Phase 3
    builder.add_edge("phase_3_plan", "compress_3")
    builder.add_edge("compress_3", "hitl_gate_3")
    builder.add_edge("hitl_gate_3", "phase_4_implement")

    # Phase 4
    builder.add_edge("phase_4_implement", "compress_4")
    builder.add_edge("compress_4", "hitl_gate_4")
    builder.add_edge("hitl_gate_4", "phase_5_critique")

    # ═══ Phase 5 품질 루프 (C-3 Fix: 조건부 엣지) ═══
    # critique → [라우팅] → revise | pass
    # revise → critique (루프)
    # pass → finalize

    builder.add_conditional_edges(
        "phase_5_critique",
        decide_quality_action,
        {
            "revise": "phase_5_revise",  # 수정 필요
            "pass": "phase_5_finalize",  # 품질 통과
            "escalate": "hitl_gate_5",  # 구조적 문제 → 사람 판단
        },
    )
    builder.add_edge("phase_5_revise", "phase_5_critique")  # 재평가 루프
    builder.add_edge("phase_5_finalize", "hitl_gate_5")
    builder.add_edge("hitl_gate_5", END)

    # ── 메모리 체크포인트 (Phase 롤백용) ──
    memory = MemorySaver()

    # ── 컴파일 ──
    graph = builder.compile(checkpointer=memory)
    return graph


if __name__ == "__main__":
    # 그래프 구조 시각화 및 검증
    print("🏗️ v3.1.1 Phased Supervisor 그래프 검증\n")

    graph = build_phased_supervisor_graph()

    print("✅ 그래프 구축 완료")
    print(f"   노드: {len(graph.nodes)}")
    print(f"   엣지: {len(graph.edges)}")

    # 노드 목록 출력
    print("\n📍 노드 목록:")
    for node in sorted(graph.nodes.keys()):
        print(f"   • {node}")

    print("\n✅ Phase 기반 직선 구조 그래프 정상 구성")
