"""
LangGraph StateGraph 정의 (§4)

6 STEP 워크플로:
STEP 0: 공고 검색 → 관심과제 선정 → RFP 획득
STEP 1: RFP 분석 → 리서치 → Go/No-Go
STEP 2: 전략 수립
STEP 3: 실행 계획 (병렬)
STEP 4: 제안서 작성 (섹션별 순차 + 리뷰) → 자가진단
STEP 5: PPT 생성

v3.2: research_gather + presentation_strategy 노드 추가
v3.3: self_review 5방향 라우팅, plan 3방향 라우팅
v3.5: 제안서 섹션별 순차 작성 + 리뷰 루프
"""

import logging

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from app.graph.state import ProposalState

# 라우팅 함수
from app.graph.edges import (
    route_after_gng_review,
    route_after_plan_review,
    route_after_ppt_review,
    route_after_presentation_strategy,
    route_after_proposal_review,
    route_after_rfp_review,
    route_after_search_review,
    route_after_section_review,
    route_after_self_review,
    route_after_strategy_review,
    route_start,
)

# 실제 구현 노드
from app.graph.nodes.go_no_go import go_no_go
from app.graph.nodes.merge_nodes import plan_merge, ppt_merge
from app.graph.nodes.research_gather import research_gather
from app.graph.nodes.review_node import review_node, review_section_node
from app.graph.nodes.rfp_analyze import rfp_analyze
from app.graph.nodes.rfp_fetch import rfp_fetch
from app.graph.nodes.rfp_search import rfp_search

# Phase 2: 전략·계획·제안서·PPT 실제 구현
from app.graph.nodes.strategy_generate import strategy_generate
from app.graph.nodes.plan_nodes import (
    plan_assign,
    plan_price,
    plan_schedule,
    plan_story,
    plan_team,
)
from app.graph.nodes.proposal_nodes import (
    proposal_write_next,
    self_review_with_auto_improve,
)
from app.graph.nodes.ppt_nodes import (
    ppt_slide,
    presentation_strategy,
)

logger = logging.getLogger(__name__)


# ── 선택적 Fan-out (§4-1) ──

ALL_PLAN_NODES = ["plan_team", "plan_assign", "plan_schedule", "plan_story", "plan_price"]


def plan_selective_fan_out(state: ProposalState) -> list[Send]:
    """부분 재작업: rework_targets에 지정된 항목만 재실행."""
    targets = state.get("rework_targets", [])
    if not targets:
        nodes_to_run = ALL_PLAN_NODES
    else:
        nodes_to_run = [n for n in ALL_PLAN_NODES if n in targets]
    return [Send(node, state) for node in nodes_to_run]


def ppt_fan_out(state: ProposalState) -> list[Send]:
    """PPT 슬라이드 병렬 생성."""
    sections = state.get("proposal_sections", [])
    if not sections:
        return [Send("ppt_slide", state)]
    return [
        Send("ppt_slide", {
            **state,
            "_current_slide_id": s.section_id if hasattr(s, "section_id") else s.get("section_id", f"slide_{i}"),
        })
        for i, s in enumerate(sections)
    ]


def _passthrough(state: ProposalState) -> dict:
    """Fan-out 게이트용 패스스루 노드."""
    return {}


def _proposal_start_gate(state: ProposalState) -> dict:
    """섹션별 순차 작성 시작: current_section_index 초기화."""
    return {"current_section_index": 0}


# ── 그래프 빌드 ──

def build_graph(checkpointer=None):
    """전체 StateGraph 구성 및 컴파일."""
    g = StateGraph(ProposalState)

    # STEP 0: 공고 검색/추천
    g.add_node("rfp_search", rfp_search)
    g.add_node("review_search", review_node("search"))
    g.add_node("rfp_fetch", rfp_fetch)

    # STEP 1-①: RFP 분석
    g.add_node("rfp_analyze", rfp_analyze)
    g.add_node("review_rfp", review_node("rfp"))

    # v3.2: 사전조사 (review 없이 자동 통과)
    g.add_node("research_gather", research_gather)

    # STEP 1-②: Go/No-Go
    g.add_node("go_no_go", go_no_go)
    g.add_node("review_gng", review_node("go_no_go"))

    # STEP 2: 전략
    g.add_node("strategy_generate", strategy_generate)
    g.add_node("review_strategy", review_node("strategy"))

    # STEP 3: 실행 계획 (병렬)
    g.add_node("plan_fan_out_gate", _passthrough)
    g.add_node("plan_team", plan_team)
    g.add_node("plan_assign", plan_assign)
    g.add_node("plan_schedule", plan_schedule)
    g.add_node("plan_story", plan_story)
    g.add_node("plan_price", plan_price)
    g.add_node("plan_merge", plan_merge)
    g.add_node("review_plan", review_node("plan"))

    # STEP 4: 제안서 (섹션별 순차 작성 + 리뷰)
    g.add_node("proposal_start_gate", _proposal_start_gate)
    g.add_node("proposal_write_next", proposal_write_next)
    g.add_node("review_section", review_section_node)
    g.add_node("self_review", self_review_with_auto_improve)
    g.add_node("review_proposal", review_node("proposal"))

    # v3.2: 발표전략
    g.add_node("presentation_strategy", presentation_strategy)

    # STEP 5: PPT
    g.add_node("ppt_fan_out_gate", _passthrough)
    g.add_node("ppt_slide", ppt_slide)
    g.add_node("ppt_merge", ppt_merge)
    g.add_node("review_ppt", review_node("ppt"))

    # ── 엣지 정의 ──

    # START → 3가지 진입 경로
    g.add_conditional_edges(START, route_start, {
        "search": "rfp_search",
        "direct_fetch": "rfp_fetch",
        "direct_rfp": "rfp_analyze",
    })

    # STEP 0
    g.add_edge("rfp_search", "review_search")
    g.add_conditional_edges("review_search", route_after_search_review, {
        "picked_up": "rfp_fetch",
        "re_search": "rfp_search",
        "no_interest": END,
    })
    g.add_edge("rfp_fetch", "rfp_analyze")

    # STEP 1-①
    g.add_edge("rfp_analyze", "review_rfp")
    g.add_conditional_edges("review_rfp", route_after_rfp_review, {
        "approved": "research_gather",
        "rejected": "rfp_analyze",
    })

    # v3.5: 리서치 → Go/No-Go
    g.add_edge("research_gather", "go_no_go")

    # STEP 1-②
    g.add_edge("go_no_go", "review_gng")
    g.add_conditional_edges("review_gng", route_after_gng_review, {
        "go": "strategy_generate",
        "no_go": END,
        "rejected": "go_no_go",
    })

    # STEP 2
    g.add_edge("strategy_generate", "review_strategy")
    g.add_conditional_edges("review_strategy", route_after_strategy_review, {
        "approved": "plan_fan_out_gate",
        "rejected": "strategy_generate",
        "positioning_changed": "strategy_generate",
    })

    # STEP 3: 선택적 병렬
    g.add_conditional_edges("plan_fan_out_gate", plan_selective_fan_out)
    for node in ALL_PLAN_NODES:
        g.add_edge(node, "plan_merge")
    g.add_edge("plan_merge", "review_plan")
    g.add_conditional_edges("review_plan", route_after_plan_review, {
        "approved": "proposal_start_gate",
        "rework": "plan_fan_out_gate",
        "rework_with_strategy": "strategy_generate",
    })

    # STEP 4: 섹션별 순차 작성 + 리뷰 루프
    #   proposal_start_gate → proposal_write_next → review_section
    #                          ↑                        ↓
    #                          └── (rewrite) ───────────┘
    #                          ↑                        ↓ (next_section)
    #                          └────────────────────────┘
    #                                                   ↓ (all_done)
    #                                              self_review → review_proposal
    g.add_edge("proposal_start_gate", "proposal_write_next")
    g.add_edge("proposal_write_next", "review_section")
    g.add_conditional_edges("review_section", route_after_section_review, {
        "next_section": "proposal_write_next",
        "all_done": "self_review",
        "rewrite": "proposal_write_next",
    })
    g.add_conditional_edges("self_review", route_after_self_review, {
        "pass": "review_proposal",
        "retry_research": "research_gather",
        "retry_strategy": "strategy_generate",
        "retry_sections": "proposal_start_gate",
        "force_review": "review_proposal",
    })
    g.add_conditional_edges("review_proposal", route_after_proposal_review, {
        "approved": "presentation_strategy",
        "rework": "proposal_start_gate",
    })

    # v3.2: 발표전략 → PPT
    g.add_conditional_edges("presentation_strategy", route_after_presentation_strategy, {
        "proceed": "ppt_fan_out_gate",
        "document_only": "ppt_fan_out_gate",
    })

    # STEP 5
    g.add_conditional_edges("ppt_fan_out_gate", ppt_fan_out)
    g.add_edge("ppt_slide", "ppt_merge")
    g.add_edge("ppt_merge", "review_ppt")
    g.add_conditional_edges("review_ppt", route_after_ppt_review, {
        "approved": END,
        "rework": "ppt_fan_out_gate",
    })

    return g.compile(checkpointer=checkpointer)
