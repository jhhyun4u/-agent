#!/usr/bin/env python
"""직접 테스트: Phase 1 ~ Phase 5 순차 실행"""

import sys
import asyncio
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).parent))

async def main():
    from state.phased_state import initialize_phased_supervisor_state
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
    )
    from graph.phased_supervisor import build_phased_supervisor_graph
    
    print("=" * 60)
    print("v3.1.1 Phased Supervisor Direct Test")
    print("=" * 60)
    
    # 1. 그래프 구축
    print("\n[1] Building graph...")
    graph = build_phased_supervisor_graph()
    nodes = list(graph.nodes)
    print(f"    [OK] Nodes: {len(nodes)}")
    for node_name in nodes:
        print(f"        - {node_name}")
    
    # 2. 초기 상태 생성
    print("\n[2] Creating initial state...")
    state = initialize_phased_supervisor_state(
        rfp_document_ref='test_rfp.pdf',
        company_profile={'name': 'TestCorp', 'industry': 'Technology'},
        express_mode=False
    )
    print(f"    [OK] Initial phase: {state['current_phase']}")
    
    # 3. Phase 1 실행
    print("\n[3] Running Phase 1...")
    state = await phase_1_research_node(state)
    print(f"    [OK] Phase: {state['current_phase']}")
    print(f"        Working state keys: {list(state.get('phase_working_state', {}).keys())}")
    
    # 4. Phase 1 압축
    print("\n[4] Compressing Phase 1...")
    state = await compress_phase_1_node(state)
    print(f"    [OK] Artifact 1 created")
    print(f"        Artifact type: {type(state['phase_artifact_1']).__name__}")
    
    # 5. Phase 2 실행
    print("\n[5] Running Phase 2...")
    state = await phase_2_analysis_node(state)
    print(f"    [OK] Phase: {state['current_phase']}")
    
    # 6. Phase 2 압축
    print("\n[6] Compressing Phase 2...")
    state = await compress_phase_2_node(state)
    print(f"    [OK] Artifact 2 created")
    
    # 7. Phase 3 실행
    print("\n[7] Running Phase 3...")
    state = await phase_3_plan_node(state)
    print(f"    [OK] Phase: {state['current_phase']}")
    
    # 8. Phase 3 압축
    print("\n[8] Compressing Phase 3...")
    state = await compress_phase_3_node(state)
    print(f"    [OK] Artifact 3 created")
    
    # 9. Phase 4 실행
    print("\n[9] Running Phase 4...")
    state = await phase_4_implement_node(state)
    print(f"    [OK] Phase: {state['current_phase']}")
    
    # 10. Phase 4 압축
    print("\n[10] Compressing Phase 4...")
    state = await compress_phase_4_node(state)
    print(f"    [OK] Artifact 4 created")
    
    # 11. Phase 5 실행
    print("\n[11] Running Phase 5 Critique...")
    state = await phase_5_critique_node(state)
    print(f"    [OK] Phase: {state['current_phase']}")
    print(f"        Quality Score: {state.get('quality_score')}")
    
    print("\n" + "=" * 60)
    print("SUCCESS: All phases executed successfully!")
    print("=" * 60)

if __name__ == '__main__':
    asyncio.run(main())
