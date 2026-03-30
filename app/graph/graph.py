"""
LangGraph StateGraph 정의 (§4) — v4.0 분기 워크플로

1 → 2 → ┬─ 3A→4A→5A→6A ─┐→ 7 → 8
         └─ 3B→4B→5B→6B ─┘

Path A: 제안 계획 → 제안서 작성 → PPT → 모의 평가
Path B: 제출서류 계획 → 입찰가 결정 → 산출내역서 → 제출서류 확인
Tail:   평가결과 → Closing

v3.2~v3.8: 기존 변경사항 모두 보존
v4.0: 전략 승인 후 A/B 병렬 분기, 6A 모의평가 신규, 7-8 통합 경로
"""

import logging

from langgraph.graph import END, START, StateGraph

from app.graph.state import ProposalState

# 라우팅 함수
from app.graph.edges import (
    route_after_bid_plan_review,
    route_after_cost_sheet_review,
    route_after_eval_result_review,
    route_after_gng_review,
    route_after_mock_eval_review,
    route_after_plan_review,
    route_after_ppt_review,
    route_after_presentation_strategy,
    route_after_proposal_review,
    route_after_rfp_review,
    route_after_section_review,
    route_after_self_review,
    route_after_strategy_review,
    route_after_submission_checklist_review,
    route_after_submission_plan_review,
)

# 게이트 · Fan-out · 훅
from app.graph.nodes.gate_nodes import (
    ALL_PLAN_NODES,
    convergence_gate,
    fork_to_branches,
    passthrough,
    plan_selective_fan_out,
    proposal_start_gate,
    stream1_complete_hook,
)

# 노드
from app.graph.nodes.go_no_go import go_no_go
from app.graph.nodes.merge_nodes import plan_merge
from app.graph.nodes.research_gather import research_gather
from app.graph.nodes.review_node import review_node, review_section_node
from app.graph.nodes.rfp_analyze import rfp_analyze
from app.graph.nodes.bid_plan import bid_plan
from app.graph.nodes.strategy_generate import strategy_generate
from app.graph.nodes.plan_nodes import (
    plan_assign, plan_schedule, plan_story, plan_team,
)
from app.graph.nodes.proposal_nodes import (
    proposal_write_next, self_review_with_auto_improve,
)
from app.graph.nodes.ppt_nodes import (
    presentation_strategy, ppt_toc, ppt_visual_brief, ppt_storyboard_node,
)
from app.graph.nodes.submission_nodes import (
    submission_plan, cost_sheet_generate, submission_checklist,
)
from app.graph.nodes.evaluation_nodes import (
    mock_evaluation, eval_result_node, project_closing,
)

from app.graph.token_tracking import track_tokens

logger = logging.getLogger(__name__)


# ── 그래프 빌드 ──

def build_graph(checkpointer=None):
    """전체 StateGraph 구성 및 컴파일."""
    g = StateGraph(ProposalState)

    # ═══════════════════════════════════════════
    # HEAD: 1 → 2 (공통)
    # ═══════════════════════════════════════════

    # STEP 1: RFP 분석
    g.add_node("rfp_analyze", track_tokens("rfp_analyze")(rfp_analyze))
    g.add_node("review_rfp", review_node("rfp"))
    g.add_node("research_gather", track_tokens("research_gather")(research_gather))
    g.add_node("go_no_go", track_tokens("go_no_go")(go_no_go))
    g.add_node("review_gng", review_node("go_no_go"))

    # STEP 2: 전략 수립
    g.add_node("strategy_generate", track_tokens("strategy_generate")(strategy_generate))
    g.add_node("review_strategy", review_node("strategy"))

    # 분기 게이트
    g.add_node("fork_gate", passthrough)

    # ═══════════════════════════════════════════
    # PATH A: 3A→4A→5A→6A (제안서 경로)
    # ═══════════════════════════════════════════

    # 3A: 제안 계획 (병렬 fan-out)
    g.add_node("plan_fan_out_gate", passthrough)
    g.add_node("plan_team", track_tokens("plan_team")(plan_team))
    g.add_node("plan_assign", track_tokens("plan_assign")(plan_assign))
    g.add_node("plan_schedule", track_tokens("plan_schedule")(plan_schedule))
    g.add_node("plan_story", track_tokens("plan_story")(plan_story))
    g.add_node("plan_merge", plan_merge)
    g.add_node("review_plan", review_node("plan"))

    # 4A: 제안서 작성
    g.add_node("proposal_start_gate", proposal_start_gate)
    g.add_node("proposal_write_next", track_tokens("proposal_write_next")(proposal_write_next))
    g.add_node("review_section", review_section_node)
    g.add_node("self_review", track_tokens("self_review")(self_review_with_auto_improve))
    g.add_node("review_proposal", review_node("proposal"))

    # 5A: PPT
    g.add_node("presentation_strategy", track_tokens("presentation_strategy")(presentation_strategy))
    g.add_node("ppt_toc", track_tokens("ppt_toc")(ppt_toc))
    g.add_node("ppt_visual_brief", track_tokens("ppt_visual_brief")(ppt_visual_brief))
    g.add_node("ppt_storyboard", track_tokens("ppt_storyboard")(ppt_storyboard_node))
    g.add_node("review_ppt", review_node("ppt"))

    # 6A: 모의 평가
    g.add_node("mock_evaluation", track_tokens("mock_evaluation")(mock_evaluation))
    g.add_node("review_mock_eval", review_node("mock_evaluation"))

    # ═══════════════════════════════════════════
    # PATH B: 3B→4B→5B→6B (입찰·제출 경로)
    # ═══════════════════════════════════════════

    # 3B: 제출서류 계획
    g.add_node("submission_plan", track_tokens("submission_plan")(submission_plan))
    g.add_node("review_submission_plan", review_node("submission_plan"))

    # 4B: 입찰가 결정
    g.add_node("bid_plan", track_tokens("bid_plan")(bid_plan))
    g.add_node("review_bid_plan", review_node("bid_plan"))

    # 5B: 산출내역서
    g.add_node("cost_sheet_generate", track_tokens("cost_sheet_generate")(cost_sheet_generate))
    g.add_node("review_cost_sheet", review_node("cost_sheet"))

    # 6B: 제출서류 확인
    g.add_node("submission_checklist", track_tokens("submission_checklist")(submission_checklist))
    g.add_node("review_submission", review_node("submission_checklist"))

    # ═══════════════════════════════════════════
    # TAIL: 7 → 8 (통합)
    # ═══════════════════════════════════════════

    g.add_node("convergence_gate", convergence_gate)
    g.add_node("eval_result", track_tokens("eval_result")(eval_result_node))
    g.add_node("review_eval_result", review_node("eval_result"))
    g.add_node("project_closing", track_tokens("project_closing")(project_closing))

    # Stream 완료 훅
    g.add_node("stream1_complete_hook", stream1_complete_hook)

    # ═══════════════════════════════════════════
    # EDGES
    # ═══════════════════════════════════════════

    # ── HEAD ──
    g.add_edge(START, "rfp_analyze")

    g.add_edge("rfp_analyze", "review_rfp")
    g.add_conditional_edges("review_rfp", route_after_rfp_review, {
        "approved": "research_gather",
        "rejected": "rfp_analyze",
    })

    g.add_edge("research_gather", "go_no_go")
    g.add_edge("go_no_go", "review_gng")
    g.add_conditional_edges("review_gng", route_after_gng_review, {
        "go": "strategy_generate",
        "no_go": END,
        "rejected": "go_no_go",
    })

    g.add_edge("strategy_generate", "review_strategy")
    g.add_conditional_edges("review_strategy", route_after_strategy_review, {
        "approved": "fork_gate",        # → 분기
        "rejected": "strategy_generate",
        "positioning_changed": "strategy_generate",
    })

    # ── FORK: 전략 승인 → A + B 동시 ──
    g.add_conditional_edges("fork_gate", fork_to_branches)

    # ── PATH A: 3A→4A→5A→6A ──

    g.add_conditional_edges("plan_fan_out_gate", plan_selective_fan_out)
    for node in ALL_PLAN_NODES:
        g.add_edge(node, "plan_merge")
    g.add_edge("plan_merge", "review_plan")
    g.add_conditional_edges("review_plan", route_after_plan_review, {
        "approved": "proposal_start_gate",
        "rework": "plan_fan_out_gate",
        "rework_with_strategy": "strategy_generate",
        "rework_bid_plan": "bid_plan",
    })

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

    g.add_conditional_edges("presentation_strategy", route_after_presentation_strategy, {
        "proceed": "ppt_toc",
        "document_only": "mock_evaluation",  # 서류심사 → PPT 건너뛰고 모의평가
    })
    g.add_edge("ppt_toc", "ppt_visual_brief")
    g.add_edge("ppt_visual_brief", "ppt_storyboard")
    g.add_edge("ppt_storyboard", "review_ppt")
    g.add_conditional_edges("review_ppt", route_after_ppt_review, {
        "approved": "mock_evaluation",  # PPT 완료 → 6A 모의평가
        "rework": "ppt_toc",
    })

    # 6A: 모의 평가
    g.add_edge("mock_evaluation", "review_mock_eval")
    g.add_conditional_edges("review_mock_eval", route_after_mock_eval_review, {
        "approved": "convergence_gate",  # → 통합
        "rejected": "mock_evaluation",
    })

    # ── PATH B: 3B→4B→5B→6B ──

    g.add_edge("submission_plan", "review_submission_plan")
    g.add_conditional_edges("review_submission_plan", route_after_submission_plan_review, {
        "approved": "bid_plan",
        "rejected": "submission_plan",
    })

    g.add_edge("bid_plan", "review_bid_plan")
    g.add_conditional_edges("review_bid_plan", route_after_bid_plan_review, {
        "approved": "cost_sheet_generate",
        "rejected": "bid_plan",
        "back_to_strategy": "strategy_generate",
    })

    g.add_edge("cost_sheet_generate", "review_cost_sheet")
    g.add_conditional_edges("review_cost_sheet", route_after_cost_sheet_review, {
        "approved": "submission_checklist",
        "rejected": "cost_sheet_generate",
    })

    g.add_edge("submission_checklist", "review_submission")
    g.add_conditional_edges("review_submission", route_after_submission_checklist_review, {
        "approved": "convergence_gate",  # → 통합
        "rejected": "submission_checklist",
    })

    # ── TAIL: 7 → 8 ──

    g.add_edge("convergence_gate", "eval_result")
    g.add_edge("eval_result", "review_eval_result")
    g.add_conditional_edges("review_eval_result", route_after_eval_result_review, {
        "approved": "project_closing",
        "rejected": "eval_result",
    })

    g.add_edge("project_closing", "stream1_complete_hook")
    g.add_edge("stream1_complete_hook", END)

    return g.compile(checkpointer=checkpointer)
