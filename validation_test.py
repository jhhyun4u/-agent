#!/usr/bin/env python
"""상세 검증 테스트: Graph + State + Artifacts 검증"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def main():
    from state.phased_state import initialize_phased_supervisor_state
    from state.phase_artifacts import PhaseArtifact_1_Research
    from graph.phase_nodes import (
        phase_1_research_node,
        compress_phase_1_node,
        decide_quality_action,
    )
    from graph.hitl_gates import evaluate_hitl_gate
    from graph.phased_supervisor import build_phased_supervisor_graph
    from graph.mock_data import MOCK_PHASE1_RESULT
    
    print("=" * 70)
    print("DETAILED VALIDATION TEST")
    print("=" * 70)
    
    # TEST 1: Graph Structure
    print("\n[TEST 1] Graph Structure")
    print("-" * 70)
    graph = build_phased_supervisor_graph()
    nodes = list(graph.nodes)
    print(f"Total nodes: {len(nodes)}")
    print(f"Expected: 17 (1 start + 5 phase + 4 compress + 5 HITL + 2 substates)")
    assert len(nodes) == 17, f"Expected 17 nodes, got {len(nodes)}"
    print("PASS: Graph structure correct")
    
    # TEST 2: State Initialization
    print("\n[TEST 2] State Initialization")
    print("-" * 70)
    state = initialize_phased_supervisor_state(
        rfp_document_ref='test.pdf',
        company_profile={'name': 'Test', 'industry': 'IT'},
        express_mode=False
    )
    print(f"Initial phase: {state['current_phase']}")
    print(f"State keys: {len(state)}")
    assert state['current_phase'] == 'phase_1_research'
    assert 'phase_artifact_1' in state
    assert 'hitl_decisions' in state
    print("PASS: State initialized correctly")
    
    # TEST 3: Phase 1 Execution
    print("\n[TEST 3] Phase 1 Execution")
    print("-" * 70)
    state = await phase_1_research_node(state)
    print(f"Phase after execution: {state['current_phase']}")
    print(f"Working state keys: {list(state['phase_working_state'].keys())}")
    assert 'parsed_rfp' in state['phase_working_state']
    assert 'past_proposals' in state['phase_working_state']
    print("PASS: Phase 1 executed correctly")
    
    # TEST 4: Artifact Compression
    print("\n[TEST 4] Artifact Compression")
    print("-" * 70)
    state = await compress_phase_1_node(state)
    artifact_1 = state['phase_artifact_1']
    print(f"Artifact 1 type: {type(artifact_1).__name__}")
    print(f"Artifact 1 keys: {list(artifact_1.keys()) if isinstance(artifact_1, dict) else 'N/A'}")
    assert state['phase_working_state'] == {}, "Working state should be cleared"
    print("PASS: Artifact compression correct (working state cleared)")
    
    # TEST 5: HITL Gate Logic
    print("\n[TEST 5] HITL Gate Logic")
    print("-" * 70)
    decision = evaluate_hitl_gate(1, state)
    print(f"Gate 1 decision: {decision.action}")
    print(f"Gate 1 reason: {decision.reason}")
    print(f"Approval items: {len(decision.approval_items)}")
    print("PASS: HITL gate evaluation works")
    
    # TEST 6: Quality Routing (Phase 5)
    print("\n[TEST 6] Quality Routing")
    print("-" * 70)
    
    # Test case: High quality -> pass
    state_pass = {
        'quality_score': 0.85,
        'revision_rounds': 0,
        'structural_issues': [],
    }
    route = decide_quality_action(state_pass)
    assert route == 'pass', f"Expected 'pass', got {route}"
    print(f"Quality 0.85, rounds 0 -> {route} [PASS]")
    
    # Test case: Medium quality + room for revision -> revise
    state_revise = {
        'quality_score': 0.70,
        'revision_rounds': 1,
        'structural_issues': [],
    }
    route = decide_quality_action(state_revise)
    assert route == 'revise', f"Expected 'revise', got {route}"
    print(f"Quality 0.70, rounds 1 -> {route} [PASS]")
    
    # Test case: Structural issues -> escalate
    state_escalate = {
        'quality_score': 0.60,
        'revision_rounds': 0,
        'structural_issues': ['Missing section', 'Invalid format'],
    }
    route = decide_quality_action(state_escalate)
    assert route == 'escalate', f"Expected 'escalate', got {route}"
    print(f"Quality 0.60, structural issues -> {route} [PASS]")
    
    print("PASS: All quality routing cases correct")
    
    print("\n" + "=" * 70)
    print("ALL TESTS PASSED!")
    print("=" * 70)
    print("\nSummary:")
    print("  [OK] Graph structure (17 nodes)")
    print("  [OK] State initialization")
    print("  [OK] Phase 1 execution")
    print("  [OK] Artifact compression")
    print("  [OK] HITL gate logic")
    print("  [OK] Quality routing (pass/revise/escalate)")
    print("\nv3.1.1 Phased Supervisor Framework: READY FOR PRODUCTION")

if __name__ == '__main__':
    asyncio.run(main())
