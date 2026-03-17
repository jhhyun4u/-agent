# 리뷰 노드 (단계별 관점 차별화)

> **소속**: proposal-agent-v1 설계 문서 v3.5
> **관련 파일**: [03-graph-definition.md](03-graph-definition.md), [07-routing-edges.md](07-routing-edges.md)
> **원본 섹션**: §5, §32-7

---

## 5. 리뷰 노드 (단계별 관점 차별화) — D-2, D-8, U-2 해결

> **v1.3~v1.4 변경**:
> - STEP 0: 공고 검색 리뷰 → pick-up 선택 (승인 게이트 아닌 선택 행위)
> - STEP 0→1: `rfp_fetch`는 review_node가 아닌 자체 interrupt() 사용 (파일 업로드 게이트)
> - STEP 1: RFP 분석 확인 → Go/No-Go 의사결정 (2단계 게이트)
> - 모든 단계에서 **빠른 승인** 지원 (피드백 생략)
> - 전략 단계에서 **포지셔닝 변경** 가능 + 영향 범위 안내
> - 단계별 **리뷰 관점(Shipley)** 차별화
> - 부분 재작업 시 **rework_targets** 지정

```python
# app/graph/nodes/review_node.py
from langgraph.types import interrupt
from app.graph.state import ProposalState, ApprovalStatus

# Shipley Color Team 관점 매핑
REVIEW_PERSPECTIVES = {
    "search": {
        "perspective": "영업 담당자 관점",
        "focus": "관심과제로 선정할 만한가? 우리 역량에 맞는가? 기한은 충분한가? 경쟁 환경은?",
    },
    "go_no_go": {
        "perspective": "의사결정자 관점",
        "focus": "RFP 분석 결과를 보고, 이 입찰에 참여할 만한 가치가 있는가? 자원 투입 대비 수주 가능성은?",
    },
    "rfp": {
        "perspective": "Blue Team (분석 검증) 관점",
        "focus": "RFP 해석이 정확한가? 누락된 요건은 없는가? 배점표 분석이 맞는가?",
    },
    "strategy": {
        "perspective": "Blue Team (전략 검증) 관점",
        "focus": "이 전략으로 이길 수 있는가? 포지셔닝이 맞는가? Win Theme이 평가위원을 설득할 수 있는가?",
    },
    "plan": {
        "perspective": "Pink Team (실행 검증) 관점",
        "focus": "이 계획대로 실행 가능한가? 일정은 현실적인가? 팀 구성에 빈틈은?",
    },
    "proposal": {
        "perspective": "Red Team (경쟁 관점) 관점",
        "focus": "경쟁사 대비 우위가 명확한가? 평가위원이 쉽게 점수를 줄 수 있는 구조인가?",
    },
    "ppt": {
        "perspective": "Gold Team (최종 품질) 관점",
        "focus": "형식·규격 완벽 준수? 메시지 일관성? 발표 시 핵심이 3초 안에 전달되는가?",
    },
}


def review_node(step_name: str):
    """모든 단계에서 공통 리뷰 게이트. 단계별 관점 차별화 + 빠른 승인 지원."""

    def _review(state: ProposalState) -> dict:
        artifact = _get_artifact(state, step_name)
        perspective = REVIEW_PERSPECTIVES.get(step_name, {})

        # ── interrupt: 프론트엔드 resume 대기 ──
        human_input = interrupt({
            "step": step_name,
            "artifact": artifact,
            "positioning": state.get("positioning", ""),
            "review_perspective": perspective,
            "message": f"[{perspective.get('perspective','')}] {step_name} 산출물을 검토하세요.",
            "review_focus": perspective.get("focus", ""),
            "feedback_history": [
                f for f in state.get("feedback_history", [])
                if f["step"] == step_name
            ],
        })

        # ── STEP 0: 공고 pick-up 특수 처리 ──
        if step_name == "search":
            return _handle_search_review(state, human_input)

        # ── STEP 1-②: Go/No-Go 특수 처리 ──
        if step_name == "go_no_go":
            return _handle_gng_review(state, human_input)

        # ── 전략 리뷰: 포지셔닝 변경 가능 (D-2) ──
        if step_name == "strategy":
            return _handle_strategy_review(state, human_input)

        # ── 빠른 승인 (U-2) ──
        if human_input.get("quick_approve"):
            approval = ApprovalStatus(
                status="approved",
                approved_by=human_input.get("approved_by", "user"),
                approved_at=human_input.get("approved_at", ""),
            )
            # ★ v2.0: 결재선 단계 확인 (Go/No-Go, 제안서 최종만 해당)
            if step_name in ("go_no_go", "proposal"):
                chain_result = _check_approval_chain(state, step_name, human_input)
                if chain_result:  # 결재선 미완료 → 다음 승인자 대기
                    return chain_result
                approval.chain = state.get("approval", {}).get(step_name, ApprovalStatus()).chain
            return {
                "approval": {step_name: approval},
                "current_step": f"{step_name}_approved",
                "rework_targets": [],
            }

        # ── 승인 ──
        if human_input.get("approved"):
            approval = ApprovalStatus(
                status="approved",
                approved_by=human_input.get("approved_by", "user"),
                approved_at=human_input.get("approved_at", ""),
            )
            # ★ v2.0: 결재선 단계 확인
            if step_name in ("go_no_go", "proposal"):
                chain_result = _check_approval_chain(state, step_name, human_input)
                if chain_result:
                    return chain_result
                approval.chain = state.get("approval", {}).get(step_name, ApprovalStatus()).chain
            return {
                "approval": {step_name: approval},
                "current_step": f"{step_name}_approved",
                "rework_targets": [],
            }

        # ── 거부 + 부분 재작업 지정 (D-1) ──
        feedback_entry = {
            "step": step_name,
            "feedback": human_input["feedback"],
            "comments": human_input.get("comments", {}),
            "rework_targets": human_input.get("rework_targets", []),
            "timestamp": human_input.get("timestamp", ""),
        }
        return {
            "approval": {step_name: ApprovalStatus(
                status="rejected",
                feedback=human_input["feedback"],
            )},
            "feedback_history": [feedback_entry],
            "current_step": f"{step_name}_rejected",
            "rework_targets": human_input.get("rework_targets", []),
        }

    return _review


def _handle_search_review(state, human_input):
    """STEP 0: 관심과제 선정 처리. 승인 게이트 아닌 선택/종료 행위."""

    # ── 관심과제 선정 (pick-up) → STEP 1 진입 ──
    picked_bid = human_input.get("picked_bid_no")
    if picked_bid:
        return {
            "picked_bid_no": picked_bid,
            "current_step": "search_picked_up",
        }

    # ── 관심과제 없음 → 워크플로 종료 ──
    if human_input.get("no_interest"):
        return {
            "current_step": "search_no_interest",
            "feedback_history": [{
                "step": "search",
                "feedback": human_input.get("reason", "관심과제 없음"),
                "timestamp": human_input.get("timestamp", ""),
            }],
        }

    # ── 재검색 (검색 조건 변경) ──
    return {
        "current_step": "search_re_search",
        "feedback_history": [{
            "step": "search",
            "search_query": human_input.get("search_query", {}),  # ★ A-3: dict로 보존
            "feedback": f"재검색: {human_input.get('search_query', {})}",
            "timestamp": human_input.get("timestamp", ""),
        }],
    }


def _handle_gng_review(state, human_input):
    decision = human_input.get("decision", "go")  # "go" | "no_go" | "rejected"

    if decision == "go":
        result = {
            "approval": {"go_no_go": ApprovalStatus(
                status="approved",
                approved_by=human_input.get("approved_by", "user"),
                approved_at=human_input.get("approved_at", ""),
                feedback=human_input.get("feedback", ""),
            )},
            "current_step": "go_no_go_go",
        }
        # 포지셔닝 확정 (AI 추천 수용 또는 직접 변경)
        override = human_input.get("positioning_override")
        if override and override != state.get("positioning"):
            result["positioning"] = override
        return result

    elif decision == "no_go":
        return {
            "approval": {"go_no_go": ApprovalStatus(
                status="rejected",
                approved_by=human_input.get("approved_by", "user"),
                approved_at=human_input.get("approved_at", ""),
                feedback=human_input.get("feedback", ""),
            )},
            "current_step": "go_no_go_no_go",  # ★ route_after_gng_review에서 확인
            "feedback_history": [{
                "step": "go_no_go",
                "feedback": human_input.get("feedback", "No-Go 결정"),
                "no_go_reason": human_input.get("no_go_reason", ""),
                "timestamp": human_input.get("timestamp", ""),
            }],
        }

    else:
        # 재검토 요청 (Go/No-Go 평가서 재생성)
        return {
            "approval": {"go_no_go": ApprovalStatus(
                status="rejected",
                feedback=human_input.get("feedback", ""),
            )},
            "feedback_history": [{
                "step": "go_no_go",
                "feedback": human_input.get("feedback", ""),
                "timestamp": human_input.get("timestamp", ""),
            }],
            "current_step": "go_no_go_rejected",
        }


def _handle_strategy_review(state, human_input):
    """전략 리뷰: 포지셔닝 변경 가능, 전략 대안 선택 처리."""

    # ★ 포지셔닝 변경 (D-2)
    positioning_changed = False
    override = human_input.get("positioning_override")
    if override and override != state.get("positioning"):
        positioning_changed = True

    # 전략 대안 선택 (D-6)
    selected_alt = human_input.get("selected_alt_id", "")

    if human_input.get("approved") or human_input.get("quick_approve"):
        result = {
            "approval": {"strategy": ApprovalStatus(
                status="approved",
                approved_by=human_input.get("approved_by", "user"),
                approved_at=human_input.get("approved_at", ""),
            )},
            "current_step": "strategy_approved",
        }
        if selected_alt:
            result["strategy"] = _apply_selected_alternative(state["strategy"], selected_alt)
        return result

    elif positioning_changed:
        # 포지셔닝 변경 → 전략 재생성 (기존 STEP 3~5 승인 초기화)
        return {
            "positioning": override,
            "approval": {
                "strategy": ApprovalStatus(status="rejected", feedback="포지셔닝 변경"),
                "plan":     ApprovalStatus(status="pending"),
                "proposal": ApprovalStatus(status="pending"),
                "ppt":      ApprovalStatus(status="pending"),
            },
            "feedback_history": [{
                "step": "strategy",
                "feedback": f"포지셔닝 변경: {state.get('positioning')} → {override}",
                "timestamp": human_input.get("timestamp", ""),
            }],
            "current_step": "strategy_positioning_changed",
        }

    else:
        # 일반 거부
        return {
            "approval": {"strategy": ApprovalStatus(
                status="rejected",
                feedback=human_input.get("feedback", ""),
            )},
            "feedback_history": [{
                "step": "strategy",
                "feedback": human_input.get("feedback", ""),
                "comments": human_input.get("comments", {}),
                "timestamp": human_input.get("timestamp", ""),
            }],
            "current_step": "strategy_rejected",
        }


def _apply_selected_alternative(strategy, alt_id):
    """선택된 대안의 값을 Strategy 최상위 필드로 복사."""
    for alt in strategy.alternatives:
        if alt.alt_id == alt_id:
            strategy.selected_alt_id = alt_id
            strategy.ghost_theme = alt.ghost_theme
            strategy.win_theme = alt.win_theme
            strategy.action_forcing_event = alt.action_forcing_event
            strategy.key_messages = alt.key_messages
            strategy.price_strategy = alt.price_strategy
            return strategy
    return strategy


def _get_artifact(state, step_name):
    mapping = {
        "search":    state.get("search_results"),
        "rfp_fetch": state.get("bid_detail"),
        "go_no_go":  state.get("go_no_go"),
        "rfp":       state.get("rfp_analysis"),
        "strategy": state.get("strategy"),
        "plan":     state.get("plan"),
        "proposal": state.get("proposal_sections"),
        "ppt":      state.get("ppt_slides"),
    }
    return mapping.get(step_name)


# ── ★ v2.0: 결재선 승인 체크 ──

def _check_approval_chain(state, step_name, human_input):
    """
    결재선 기반 다단계 승인 처리 (Go/No-Go, 제안서 최종 승인에 적용).

    결재선 규칙 (요구사항 §2-4):
    - 예산 3억 미만: 팀장 단독 승인
    - 예산 3억~5억: 팀장 → 본부장 승인 필수
    - 예산 5억 이상: 팀장 → 본부장 → 경영진 승인 필수

    결재선이 미완료인 경우 interrupt 상태를 유지하여 다음 승인자를 대기.
    """
    budget = _extract_budget(state)
    approver_role = human_input.get("approver_role", "lead")

    existing_approval = state.get("approval", {}).get(step_name, ApprovalStatus())
    chain = list(existing_approval.chain) if existing_approval.chain else []

    # 현재 승인자 기록
    chain.append(ApprovalChainEntry(
        role=approver_role,
        user_id=human_input.get("approved_by", ""),
        user_name=human_input.get("approver_name", ""),
        status="approved",
        decided_at=human_input.get("approved_at", ""),
    ))

    # 결재선 완료 여부 판단
    required_roles = _get_required_roles(budget)
    approved_roles = {e.role for e in chain if e.status == "approved"}

    if not required_roles.issubset(approved_roles):
        # 결재선 미완료 → 다음 승인자 대기 (interrupt 상태 유지)
        next_role = next(r for r in ["lead", "director", "executive"]
                        if r in required_roles and r not in approved_roles)
        return {
            "approval": {step_name: ApprovalStatus(
                status="pending",
                chain=chain,
                feedback=f"결재 진행 중 — {next_role} 승인 대기",
            )},
            "current_step": f"{step_name}_chain_pending",
        }

    # 결재선 완료 → None 반환 (호출자가 최종 승인 처리)
    return None


def _get_required_roles(budget: int) -> set[str]:
    """예산 기준 필요 결재 역할."""
    if budget >= 500_000_000:
        return {"lead", "director", "executive"}
    elif budget >= 300_000_000:
        return {"lead", "director"}
    return {"lead"}


def _extract_budget(state) -> int:
    """State에서 예산 금액 추출 (bid_detail 또는 rfp_analysis에서)."""
    bid = state.get("bid_detail")
    if bid and hasattr(bid, "budget"):
        try:
            return int(bid.budget.replace(",", "").replace("원", "").replace("억", "0000_0000"))
        except (ValueError, AttributeError):
            pass
    return 0
```

---

## 5-1. 리뷰 노드 v3.5 변경 (§32-7 merged)

### 5-1-1. review_section_node (신규)

```python
def review_section_node(state: ProposalState) -> dict:
    """섹션별 human 리뷰 게이트.

    방금 작성된 섹션 1개를 human에게 제시하고 interrupt()로 대기.

    interrupt 데이터:
      - section_id: 현재 섹션 ID
      - section_content: 작성된 본문
      - section_index: 현재 인덱스
      - total_sections: 전체 섹션 수
      - self_check: 자가진단 결과

    human_input 처리:
      - approved=True, next=True → current_section_index++, current_step="section_approved"
      - approved=True, finish=True → current_step="sections_complete"
      - approved=False → feedback 저장, current_step="section_rejected"
    """
```

### 5-1-2. plan 리뷰 강화 (_build_plan_review_context)

plan 리뷰 시 기존 plan 데이터에 추가로 스토리라인 컨텍스트를 제공:

```python
def _build_plan_review_context(state: ProposalState) -> dict:
    """plan 리뷰 interrupt에 포함할 목차+스토리라인 데이터.

    Returns:
        toc_with_storylines: [{section_id, key_message, weight, tone, narrative_arc}, ...]
        overall_narrative: 전체 서사
        opening_hook: 도입 전략
        closing_impact: 마무리 전략
        review_instructions: "목차 순서 변경, 섹션 추가/삭제, 스토리라인 수정 가능"
    """
```

### 5-1-3. plan 리뷰 핸들러 (_handle_plan_review)

```python
def _handle_plan_review(state: ProposalState, human_input: dict) -> dict:
    """plan 리뷰 human 응답 처리.

    human_input 옵션:
      - sections_reorder: [섹션ID 리스트] → dynamic_sections 재정렬
      - storyline_feedback: {section_id: "피드백"} → plan.storylines 갱신
      - approved=True → "approved"
      - approved=False → rework_targets 설정
    """
```

---
