# Conditional Edge 라우팅

> **소속**: proposal-agent-v1 설계 문서 v3.5
> **관련 파일**: [03-graph-definition.md](03-graph-definition.md), [04-review-nodes.md](04-review-nodes.md)
> **원본 섹션**: §11 (+ §32-4 merged)

---

## 11. Conditional Edge 라우팅

```python
# app/graph/edges.py

def route_start(state: ProposalState) -> str:
    """★ B-1 + U-1 + U-6: 3가지 진입 경로 분기.
    - rfp_raw 존재 → STEP 1 직접 진입 (from-rfp)
    - picked_bid_no 존재 → rfp_fetch (from-search)
    - 그 외 → STEP 0 검색 (lite/full 모두)
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

def route_after_gng_review(state: ProposalState) -> str:
    """★ A-1 수정: current_step 기반 라우팅 (feedback 문자열 비교 제거)."""
    step = state.get("current_step", "")
    if step == "go_no_go_go":
        return "go"
    elif step == "go_no_go_no_go":
        return "no_go"
    return "rejected"  # go_no_go_rejected → 재생성

def route_after_rfp_review(state: ProposalState) -> str:
    """STEP 1-①: RFP 분석 확인 → 리서치 조사 진행 또는 재분석. ★ v3.2: research_gather 경유."""
    return "approved" if state["approval"]["rfp"].status == "approved" else "rejected"

def route_after_strategy_review(state: ProposalState) -> str:
    """★ 포지셔닝 변경 라우팅 추가."""
    if state.get("current_step") == "strategy_positioning_changed":
        return "positioning_changed"
    return "approved" if state["approval"]["strategy"].status == "approved" else "rejected"

def route_after_plan_review(state: ProposalState) -> str:
    """★ v3.3: 전략-예산 상호조정 분기 추가 (ProposalForge strategy_budget_sync 반영)."""
    if state["approval"]["plan"].status == "approved":
        return "approved"
    # 피드백에 '전략 재수립' 키워드가 포함되면 strategy_generate로 루프백
    feedback = state.get("feedback_history", [])
    latest = feedback[-1] if feedback else {}
    rework_targets = latest.get("rework_targets", [])
    if "strategy_generate" in rework_targets:
        return "rework_with_strategy"
    return "rework"

def route_after_proposal_review(state: ProposalState) -> str:
    """★ v3.2: approved → presentation_strategy 경유 (기존: ppt_fan_out_gate 직행)."""
    return "approved" if state["approval"]["proposal"].status == "approved" else "rework"

def route_after_presentation_strategy(state: ProposalState) -> str:
    """★ v3.2: 발표전략 조건부 실행. 서류심사(document_only)이면 건너뛰기."""
    eval_method = state.get("rfp_analysis", {})
    if hasattr(eval_method, "eval_method"):
        eval_method = eval_method.eval_method
    else:
        eval_method = eval_method.get("eval_method", "") if isinstance(eval_method, dict) else ""
    if "document_only" in str(eval_method).lower():
        return "document_only"
    return "proceed"

def route_after_ppt_review(state: ProposalState) -> str:
    return "approved" if state["approval"]["ppt"].status == "approved" else "rework"
```

---

### 11-1. route_after_section_review (v3.5 신규, §32-4 merged)

```python
def route_after_section_review(state: ProposalState) -> str:
    """섹션 리뷰 후 3방향 분기.

    Returns:
        - "next_section": 승인 → index 증가 → 다음 섹션 작성
        - "rewrite": 반려 → 같은 인덱스 재작성
        - "all_done": 모든 섹션 완료 → self_review 진입
    """
    step = state.get("current_step", "")
    if step == "sections_complete":
        return "all_done"
    elif step == "section_approved":
        return "next_section"
    else:
        return "rewrite"
```

| 조건 | current_step 값 | 라우팅 |
|---|---|---|
| 섹션 승인 + 남은 섹션 있음 | `section_approved` | `next_section` → `proposal_write_next` |
| 모든 섹션 완료 | `sections_complete` | `all_done` → `self_review` |
| 섹션 반려 | 기타 | `rewrite` → `proposal_write_next` (같은 index) |
