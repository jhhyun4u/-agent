"""
통합 Supervisor - Sub-agent들을 연결한 완전한 시스템

v3.0 Multi-Agent 아키텍처:
- Supervisor: 전체 워크플로우 오케스트레이션
- 5개 Sub-agent: RFP 분석, 전략, 섹션 생성, 품질, 문서
- HITL Gates: Human-in-the-Loop 승인 프로세스
"""

from langgraph.checkpoint.memory import MemorySaver

from graph.supervisor import build_supervisor_graph
from agents import (
    build_rfp_analysis_graph,
    build_strategy_graph,
    build_section_generation_graph,
    build_quality_graph,
    build_document_graph,
)


def build_integrated_supervisor():
    """
    Sub-agent들을 포함한 완전한 Supervisor 그래프 구축

    Returns:
        CompiledGraph: 메모리 체크포인터를 가진 컴파일된 그래프
    """

    # 1. 모든 Sub-agent 그래프 빌드
    print("[BUILD] Sub-agent 그래프 빌드 중...")

    rfp_agent = build_rfp_analysis_graph()
    print("  [OK] RFP 분석 에이전트")

    strategy_agent = build_strategy_graph()
    print("  [OK] 전략 수립 에이전트")

    section_agent = build_section_generation_graph()
    print("  [OK] 섹션 생성 에이전트")

    quality_agent = build_quality_graph()
    print("  [OK] 품질 관리 에이전트")

    document_agent = build_document_graph()
    print("  [OK] 문서 출력 에이전트")

    # 2. Sub-agent 딕셔너리 생성
    subgraphs = {
        "rfp_analysis_agent": rfp_agent,
        "strategy_agent": strategy_agent,
        "section_gen_agent": section_agent,
        "quality_agent": quality_agent,
        "document_agent": document_agent,
    }

    # 3. 메모리 체크포인터 준비
    print("\n[BUILD] 메모리 체크포인터 준비 중...")
    memory = MemorySaver()
    print("  [OK] 체크포인트 시스템")

    # 4. Supervisor 그래프 빌드 (Sub-agent + 체크포인터 포함)
    print("\n[BUILD] Supervisor 그래프 구축 중...")
    compiled_graph = build_supervisor_graph(subgraphs=subgraphs, checkpointer=memory)
    print("  [OK] Supervisor 오케스트레이터")
    print("  [OK] HITL 게이트 통합")

    print("\n[SUCCESS] 통합 Supervisor 시스템 준비 완료!")
    print(f"   - Sub-agent: 5개")
    print(f"   - HITL Gate: 3개")
    print(f"   - 체크포인트: 활성화")

    return compiled_graph


def get_supervisor_status(graph) -> dict:
    """
    Supervisor 시스템 상태 조회

    Args:
        graph: 컴파일된 Supervisor 그래프

    Returns:
        시스템 상태 정보
    """
    # 그래프 노드 수집
    nodes = []
    try:
        # LangGraph의 내부 구조에서 노드 정보 추출
        if hasattr(graph, 'nodes'):
            nodes = list(graph.nodes.keys())
    except:
        pass

    return {
        "status": "operational",
        "nodes": len(nodes),
        "subagents": 5,
        "hitl_gates": 3,
        "checkpointer": "memory",
    }


def create_initial_state(rfp_document: str, company_profile: dict = None, proposal_id: str = None) -> dict:
    """
    Supervisor 초기 상태 생성

    Args:
        rfp_document: RFP 문서 텍스트 또는 파일 경로
        company_profile: 회사 프로필 정보
        proposal_id: 제안서 고유 ID (optional, 자동 생성)

    Returns:
        초기화된 SupervisorState
    """
    from state import initialize_supervisor_state, initialize_proposal_state
    import uuid

    # 기본 회사 프로필
    if company_profile is None:
        company_profile = {
            "name": "우리 회사",
            "strengths": ["기술력", "경험", "인력"],
            "experience_years": 10,
        }

    # 고유 ID 생성
    if proposal_id is None:
        proposal_id = f"proposal_{uuid.uuid4().hex[:8]}"

    # ProposalState 초기화
    proposal_state = initialize_proposal_state(
        proposal_id=proposal_id,
        rfp_document=rfp_document,
        company_profile=company_profile
    )

    # SupervisorState 초기화
    state = initialize_supervisor_state(proposal_state)

    return state
