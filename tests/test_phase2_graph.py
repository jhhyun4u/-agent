"""Phase 2: 그래프 노드 + 프롬프트 import 검증."""
import pytest


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
    from app.graph.edges import (
        route_start,
        route_after_search_review,
        route_after_rfp_review,
        route_after_gng_review,
        route_after_strategy_review,
        route_after_plan_review,
        route_after_self_review,
        route_after_proposal_review,
        route_after_ppt_review,
    )


def test_node_imports():
    """모든 노드 함수 import 가능."""
    from app.graph.nodes.rfp_search import rfp_search
    from app.graph.nodes.rfp_fetch import rfp_fetch
    from app.graph.nodes.rfp_analyze import rfp_analyze
    from app.graph.nodes.research_gather import research_gather
    from app.graph.nodes.go_no_go import go_no_go
    from app.graph.nodes.review_node import review_node
    from app.graph.nodes.merge_nodes import plan_merge, proposal_merge, ppt_merge
    from app.graph.nodes.strategy_generate import strategy_generate
    from app.graph.nodes.plan_nodes import plan_team, plan_assign, plan_schedule, plan_story, plan_price
    from app.graph.nodes.proposal_nodes import proposal_section, self_review_with_auto_improve
    from app.graph.nodes.ppt_nodes import presentation_strategy, ppt_slide


def test_prompt_imports():
    """프롬프트 모듈 import 가능."""
    from app.prompts.strategy import STRATEGY_GENERATE_PROMPT, POSITIONING_STRATEGY_MATRIX
    from app.prompts.plan import PLAN_TEAM_PROMPT, PLAN_PRICE_PROMPT
    from app.prompts.proposal_prompts import (
        PROPOSAL_CASE_A_PROMPT,
        PROPOSAL_CASE_B_PROMPT,
        SELF_REVIEW_PROMPT,
        PPT_SLIDE_PROMPT,
        PRESENTATION_STRATEGY_PROMPT,
    )


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
