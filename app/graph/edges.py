"""
Conditional Edge 라우팅 함수 (§11)

각 함수는 ProposalState를 받아 다음 노드 결정 문자열 반환.

단순 approved/rejected 패턴은 _approval_router 팩토리로 생성.
복잡한 다방향 라우팅은 개별 함수로 유지.
"""

from typing import Callable

from app.graph.state import ProposalState


def _approval_router(step_key: str, *, reject_label: str = "rejected") -> Callable:
    """단순 승인/거부 라우팅 팩토리."""
    def _route(state: ProposalState) -> str:
        approval = state.get("approval", {}).get(step_key)
        if approval and approval.status == "approved":
            return "approved"
        return reject_label
    _route.__doc__ = f"{step_key} 승인/거부 라우팅."
    _route.__name__ = f"route_after_{step_key}_review"
    return _route


# ── 단순 패턴 (팩토리 생성) ──

route_after_rfp_review = _approval_router("rfp")
route_after_proposal_review = _approval_router("proposal", reject_label="rework")
route_after_ppt_review = _approval_router("ppt", reject_label="rework")
route_after_submission_plan_review = _approval_router("submission_plan")
route_after_cost_sheet_review = _approval_router("cost_sheet")
route_after_submission_checklist_review = _approval_router("submission_checklist")
def route_after_mock_eval_review(state: ProposalState) -> str:
    """STEP 11A: 모의평가 리뷰 라우팅.

    - approved: 수주 가능성 높음 → 발표 준비 / 최종 결과 등록 진행
    - rework: 특정 섹션/항목 개선 필요 → 섹션 재작성 루프
    - rejected: 전략/구조 재검토 필요 → 전략 재수립
    """
    approval = state.get("approval", {}).get("mock_evaluation")
    if approval and approval.status == "approved":
        return "approved"

    # 피드백에서 재작업 대상 확인
    feedback = state.get("feedback_history", [])
    latest = feedback[-1] if feedback else {}
    rework_targets = latest.get("rework_targets", [])

    if "strategy_generate" in rework_targets:
        return "rework_strategy"
    if rework_targets:  # 특정 섹션 개선
        return "rework_sections"

    return "rejected"


route_after_eval_result_review = _approval_router("eval_result")


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


def route_after_bid_plan_review(state: ProposalState) -> str:
    """STEP 2.5: 입찰가격계획 리뷰 라우팅."""
    approval = state.get("approval", {}).get("bid_plan")
    if approval and approval.status == "approved":
        return "approved"
    # bid_plan 스텝의 가장 최신 피드백만 검사 (stale 방지)
    feedback = state.get("feedback_history", [])
    bid_feedbacks = [f for f in reversed(feedback) if f.get("step") == "bid_plan"]
    latest = bid_feedbacks[0] if bid_feedbacks else {}
    if latest.get("back_to_strategy"):
        return "back_to_strategy"
    return "rejected"


def route_after_plan_review(state: ProposalState) -> str:
    """v3.3: 전략-예산 상호조정 분기 포함. v3.8: bid_plan 루프백."""
    approval = state.get("approval", {}).get("plan")
    if approval and approval.status == "approved":
        return "approved"
    # 피드백에 '전략 재수립' 키워드 → strategy_generate 루프백
    feedback = state.get("feedback_history", [])
    latest = feedback[-1] if feedback else {}
    rework_targets = latest.get("rework_targets", [])
    if "strategy_generate" in rework_targets:
        return "rework_with_strategy"
    if "bid_plan" in rework_targets:
        return "rework_bid_plan"
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



def route_after_gap_analysis_review(state: ProposalState) -> str:
    """STEP 4A-⑥: 스토리라인 갭 분석 후 라우팅.
    
    - approved: 갭 분석 결과 승인, 추가 수정 불필요 → PPT 진행(presentation_strategy)
    - rework_section: 특정 섹션 갭 수정 필요 → proposal_start_gate (섹션 재작성)
    - rework_strategy: 스토리라인 자체 재설계 필요 → strategy_generate
    """
    approval = state.get("approval", {}).get("gap_analysis")
    if approval and approval.status == "approved":
        return "approved"

    # 피드백에서 재작업 대상 확인
    feedback = state.get("feedback_history", [])
    latest = feedback[-1] if feedback else {}

    if latest.get("rework_strategy"):
        return "rework_strategy"
    if latest.get("rework_targets"):
        return "rework_section"

    return "approved"


# ── 복잡한 다방향 라우팅 (개별 유지) ──
# route_after_gng_review, route_after_strategy_review, route_after_bid_plan_review,
# route_after_plan_review, route_after_self_review, route_after_section_review,
# route_after_presentation_strategy — 위에서 개별 정의됨
