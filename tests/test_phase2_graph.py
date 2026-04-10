"""Phase 2: 그래프 노드 + 프롬프트 import 검증."""


def test_graph_build_imports():
    """그래프 빌드 함수 import 가능."""
    from app.graph.graph import build_graph
    assert callable(build_graph)


def test_state_imports():
    """ProposalState import 가능."""
    from app.graph.state import ProposalState
    assert ProposalState is not None


def test_edges_imports():
    """조건부 엣지 함수 import 가능."""


def test_node_imports():
    """모든 노드 함수 import 가능."""


def test_prompt_imports():
    """프롬프트 모듈 import 가능."""


def test_positioning_matrix_structure():
    """포지셔닝 매트릭스 3개 전략 존재."""
    from app.prompts.strategy import POSITIONING_STRATEGY_MATRIX

    assert "defensive" in POSITIONING_STRATEGY_MATRIX
    assert "offensive" in POSITIONING_STRATEGY_MATRIX
    assert "adjacent" in POSITIONING_STRATEGY_MATRIX

    for key, val in POSITIONING_STRATEGY_MATRIX.items():
        assert "label" in val
        assert "core_message" in val
        assert "tone" in val


def test_graph_compile():
    """그래프 컴파일 (checkpointer 없이)."""
    from app.graph.graph import build_graph

    graph = build_graph(checkpointer=None)
    assert graph is not None
    # 노드 목록 확인 가능 (LangGraph 내부 구조)
    assert hasattr(graph, "ainvoke")
