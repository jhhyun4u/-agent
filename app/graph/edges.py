"""
Conditional Edge 라우팅 함수 (§11)

각 함수는 ProposalState를 받아 다음 노드 결정 문자열 반환.
"""

from app.graph.state import ProposalState


def route_start(state: ProposalState) -> str:
    """3가지 진입 경로 분기 (§11, B-1 + U-1 + U-6).

    - rfp_raw 존재 → STEP 1 직접 진입 (from-rfp)
    - picked_bid_no 존재 → rfp_fetch (from-search)
    - 그 외 → STEP 0 검색
    """
    if state.get("rfp_raw"):
        return "direct_rfp"
    if state.get("picked_bid_no"):
        return "direct_fetch"
    return "search"


def route_after_search_review(state: ProposalState) -> str:
    """STEP 0: 관심과제 선정 / 재검색 / 종료."""
    step = state.get("current_step", "")
    if step == "search_picked_up":
        return "picked_up"
    if step == "search_no_interest":
        return "no_interest"
    return "re_search"


def route_after_rfp_review(state: ProposalState) -> str:
    """STEP 1-①: RFP 분석 확인 → 리서치 조사 또는 재분석 (v3.2: research_gather 경유)."""
    approval = state.get("approval", {}).get("rfp")
    if approval and approval.status == "approved":
        return "approved"
    return "rejected"


def route_after_gng_review(state: ProposalState) -> str:
    """STEP 1-②: Go/No-Go 라우팅 (current_step 기반)."""
    step = state.get("current_step", "")
    if step == "go_no_go_go":
        return "go"
    elif step == "go_no_go_no_go":
        return "no_go"
    return "rejected"


def route_after_strategy_review(state: ProposalState) -> str:
    """전략 리뷰: 포지셔닝 변경 가능."""
    if state.get("current_step") == "strategy_positioning_changed":
        return "positioning_changed"
    approval = state.get("approval", {}).get("strategy")
    if approval and approval.status == "approved":
        return "approved"
    return "rejected"


def route_after_plan_review(state: ProposalState) -> str:
    """v3.3: 전략-예산 상호조정 분기 포함."""
    approval = state.get("approval", {}).get("plan")
    if approval and approval.status == "approved":
        return "approved"
    # 피드백에 '전략 재수립' 키워드 → strategy_generate 루프백
    feedback = state.get("feedback_history", [])
    latest = feedback[-1] if feedback else {}
    rework_targets = latest.get("rework_targets", [])
    if "strategy_generate" in rework_targets:
        return "rework_with_strategy"
    return "rework"


def route_after_self_review(state: ProposalState) -> str:
    """v3.3: 자가진단 5방향 라우팅."""
    step = state.get("current_step", "")
    if step == "self_review_pass":
        return "pass"
    elif step == "self_review_retry_research":
        return "retry_research"
    elif step == "self_review_retry_strategy":
        return "retry_strategy"
    elif step == "self_review_force_review":
        return "force_review"
    return "retry_sections"


def route_after_section_review(state: ProposalState) -> str:
    """v3.5: 섹션별 리뷰 → 다음 섹션 / 자가진단 / 재작성."""
    step = state.get("current_step", "")
    if step == "sections_complete":
        return "all_done"
    if step == "section_approved":
        return "next_section"
    return "rewrite"


def route_after_proposal_review(state: ProposalState) -> str:
    """v3.5: approved → presentation_strategy. rework → 섹션별 재작성 루프."""
    approval = state.get("approval", {}).get("proposal")
    if approval and approval.status == "approved":
        return "approved"
    return "rework"


def route_after_presentation_strategy(state: ProposalState) -> str:
    """v3.2: 발표전략 조건부. 서류심사이면 건너뛰기."""
    rfp = state.get("rfp_analysis")
    eval_method = ""
    if rfp:
        if hasattr(rfp, "eval_method"):
            eval_method = str(rfp.eval_method)
        elif isinstance(rfp, dict):
            eval_method = str(rfp.get("eval_method", ""))
    if "document_only" in eval_method.lower():
        return "document_only"
    return "proceed"


def route_after_ppt_review(state: ProposalState) -> str:
    approval = state.get("approval", {}).get("ppt")
    if approval and approval.status == "approved":
        return "approved"
    return "rework"
