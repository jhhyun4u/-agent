"""
공통 리뷰 게이트 노드 (§5)

Shipley Color Team 관점별 차별화된 리뷰.
interrupt()로 프론트엔드 /resume 대기.
빠른 승인, 결재선 다단계 승인, 포지셔닝 변경 지원.
"""

from langgraph.types import interrupt

from app.graph.state import (
    ApprovalChainEntry,
    ApprovalStatus,
    ProposalState,
)

# Shipley Color Team 관점 매핑
REVIEW_PERSPECTIVES = {
    "search": {
        "perspective": "영업 담당자 관점",
        "focus": "관심과제로 선정할 만한가? 우리 역량에 맞는가?",
    },
    "go_no_go": {
        "perspective": "의사결정자 관점",
        "focus": "이 입찰에 참여할 만한 가치가 있는가? 자원 투입 대비 수주 가능성은?",
    },
    "rfp": {
        "perspective": "Blue Team (분석 검증) 관점",
        "focus": "RFP 해석이 정확한가? 누락된 요건은 없는가?",
    },
    "strategy": {
        "perspective": "Blue Team (전략 검증) 관점",
        "focus": "이 전략으로 이길 수 있는가? 포지셔닝이 맞는가?",
    },
    "plan": {
        "perspective": "Pink Team (실행 검증) 관점",
        "focus": "이 계획대로 실행 가능한가? 일정은 현실적인가?",
    },
    "proposal": {
        "perspective": "Red Team (경쟁 관점) 관점",
        "focus": "경쟁사 대비 우위가 명확한가? 평가위원이 쉽게 점수를 줄 수 있는 구조인가?",
    },
    "ppt": {
        "perspective": "Gold Team (최종 품질) 관점",
        "focus": "형식·규격 완벽 준수? 메시지 일관성? 핵심이 3초 안에 전달되는가?",
    },
}


def review_node(step_name: str):
    """모든 단계에서 공통 리뷰 게이트. 단계별 관점 차별화 + 빠른 승인 지원."""

    def _review(state: ProposalState) -> dict:
        artifact = _get_artifact(state, step_name)
        perspective = REVIEW_PERSPECTIVES.get(step_name, {})

        # interrupt 데이터 구성
        interrupt_data = {
            "step": step_name,
            "artifact": artifact,
            "positioning": state.get("positioning", ""),
            "review_perspective": perspective,
            "message": f"[{perspective.get('perspective', '')}] {step_name} 산출물을 검토하세요.",
            "review_focus": perspective.get("focus", ""),
            "feedback_history": [
                f for f in state.get("feedback_history", [])
                if f.get("step") == step_name
            ],
        }

        # plan 리뷰: 목차 + 스토리라인 데이터를 함께 제공
        if step_name == "plan":
            interrupt_data.update(_build_plan_review_context(state))

        # interrupt: 프론트엔드 resume 대기
        human_input = interrupt(interrupt_data)

        # STEP 0: 공고 pick-up 특수 처리
        if step_name == "search":
            return _handle_search_review(state, human_input)

        # STEP 1-②: Go/No-Go 특수 처리
        if step_name == "go_no_go":
            return _handle_gng_review(state, human_input)

        # 전략 리뷰: 포지셔닝 변경 가능
        if step_name == "strategy":
            return _handle_strategy_review(state, human_input)

        # plan 리뷰: 목차 조정 처리
        if step_name == "plan":
            return _handle_plan_review(state, human_input)

        # 빠른 승인 (U-2)
        if human_input.get("quick_approve") or human_input.get("approved"):
            approval = ApprovalStatus(
                status="approved",
                approved_by=human_input.get("approved_by", "user"),
                approved_at=human_input.get("approved_at", ""),
            )
            # 결재선 단계 확인 (Go/No-Go, 제안서 최종만 해당)
            if step_name in ("go_no_go", "proposal"):
                chain_result = _check_approval_chain(state, step_name, human_input)
                if chain_result:
                    return chain_result
                existing = state.get("approval", {}).get(step_name, ApprovalStatus())
                approval.chain = existing.chain
            return {
                "approval": {step_name: approval},
                "current_step": f"{step_name}_approved",
                "rework_targets": [],
            }

        # 거부 + 부분 재작업
        feedback_entry = {
            "step": step_name,
            "feedback": human_input.get("feedback", ""),
            "comments": human_input.get("comments", {}),
            "rework_targets": human_input.get("rework_targets", []),
            "timestamp": human_input.get("timestamp", ""),
        }
        return {
            "approval": {step_name: ApprovalStatus(
                status="rejected",
                feedback=human_input.get("feedback", ""),
            )},
            "feedback_history": [feedback_entry],
            "current_step": f"{step_name}_rejected",
            "rework_targets": human_input.get("rework_targets", []),
        }

    return _review


def _handle_search_review(state, human_input):
    """STEP 0: 관심과제 선정 / 재검색 / 종료."""
    picked_bid = human_input.get("picked_bid_no")
    if picked_bid:
        return {
            "picked_bid_no": picked_bid,
            "current_step": "search_picked_up",
        }
    if human_input.get("no_interest"):
        return {
            "current_step": "search_no_interest",
            "feedback_history": [{
                "step": "search",
                "feedback": human_input.get("reason", "관심과제 없음"),
                "timestamp": human_input.get("timestamp", ""),
            }],
        }
    # 재검색
    return {
        "current_step": "search_re_search",
        "search_query": human_input.get("search_query", {}),
        "feedback_history": [{
            "step": "search",
            "search_query": human_input.get("search_query", {}),
            "feedback": f"재검색: {human_input.get('search_query', {})}",
            "timestamp": human_input.get("timestamp", ""),
        }],
    }


def _handle_gng_review(state, human_input):
    """STEP 1-②: Go / No-Go / 재검토."""
    decision = human_input.get("decision", "go")

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
        override = human_input.get("positioning_override")
        if override and override != state.get("positioning"):
            result["positioning"] = override
        # 결재선 확인
        chain_result = _check_approval_chain(state, "go_no_go", human_input)
        if chain_result:
            return chain_result
        return result

    elif decision == "no_go":
        return {
            "approval": {"go_no_go": ApprovalStatus(
                status="rejected",
                approved_by=human_input.get("approved_by", "user"),
                feedback=human_input.get("feedback", ""),
            )},
            "current_step": "go_no_go_no_go",
            "feedback_history": [{
                "step": "go_no_go",
                "feedback": human_input.get("feedback", "No-Go 결정"),
                "no_go_reason": human_input.get("no_go_reason", ""),
                "timestamp": human_input.get("timestamp", ""),
            }],
        }

    else:
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
    """전략 리뷰: 포지셔닝 변경 가능, 대안 선택."""
    positioning_changed = False
    override = human_input.get("positioning_override")
    if override and override != state.get("positioning"):
        positioning_changed = True

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
        if selected_alt and state.get("strategy"):
            result["strategy"] = _apply_selected_alternative(state["strategy"], selected_alt)
        return result

    elif positioning_changed:
        return {
            "positioning": override,
            "approval": {
                "strategy": ApprovalStatus(status="rejected", feedback="포지셔닝 변경"),
                "plan": ApprovalStatus(status="pending"),
                "proposal": ApprovalStatus(status="pending"),
                "ppt": ApprovalStatus(status="pending"),
            },
            "feedback_history": [{
                "step": "strategy",
                "feedback": f"포지셔닝 변경: {state.get('positioning')} → {override}",
                "timestamp": human_input.get("timestamp", ""),
            }],
            "current_step": "strategy_positioning_changed",
        }

    else:
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


def _check_approval_chain(state, step_name, human_input):
    """결재선 기반 다단계 승인 처리."""
    budget = _extract_budget(state)
    approver_role = human_input.get("approver_role", "lead")

    existing_approval = state.get("approval", {}).get(step_name, ApprovalStatus())
    chain = list(existing_approval.chain) if existing_approval.chain else []

    chain.append(ApprovalChainEntry(
        role=approver_role,
        user_id=human_input.get("approved_by", ""),
        user_name=human_input.get("approver_name", ""),
        status="approved",
        decided_at=human_input.get("approved_at", ""),
    ))

    required_roles = _get_required_roles(budget)
    approved_roles = {e.role for e in chain if e.status == "approved"}

    if not required_roles.issubset(approved_roles):
        next_role = next(
            r for r in ["lead", "director", "executive"]
            if r in required_roles and r not in approved_roles
        )
        return {
            "approval": {step_name: ApprovalStatus(
                status="pending",
                chain=chain,
                feedback=f"결재 진행 중 — {next_role} 승인 대기",
            )},
            "current_step": f"{step_name}_chain_pending",
        }

    return None


def _get_required_roles(budget: int) -> set[str]:
    if budget >= 500_000_000:
        return {"lead", "director", "executive"}
    elif budget >= 300_000_000:
        return {"lead", "director"}
    return {"lead"}


def _extract_budget(state) -> int:
    bid = state.get("bid_detail")
    if bid and hasattr(bid, "budget"):
        try:
            return int(bid.budget.replace(",", "").replace("원", "").replace("억", "00000000"))
        except (ValueError, AttributeError):
            pass
    return 0


def review_section_node(state: ProposalState) -> dict:
    """섹션별 리뷰 게이트: 방금 작성된 섹션 1개를 사람이 검토.

    승인 → 다음 섹션 또는 자가진단.
    반려 → 같은 섹션 재작성 (피드백 포함).
    """
    from app.graph.nodes.proposal_nodes import _get_sections_to_write

    sections_to_write = _get_sections_to_write(state)
    index = state.get("current_section_index", 0)

    # 현재 작성된 섹션 찾기
    current_section_id = sections_to_write[index] if index < len(sections_to_write) else ""
    current_section = None
    for s in state.get("proposal_sections", []):
        sid = s.section_id if hasattr(s, "section_id") else s.get("section_id", "")
        if sid == current_section_id:
            current_section = s
            break

    artifact = current_section.model_dump() if current_section and hasattr(current_section, "model_dump") else (
        current_section if isinstance(current_section, dict) else {}
    )

    human_input = interrupt({
        "step": "section",
        "section_id": current_section_id,
        "section_index": index,
        "total_sections": len(sections_to_write),
        "artifact": artifact,
        "positioning": state.get("positioning", ""),
        "review_perspective": {
            "perspective": "섹션 작성자 관점",
            "focus": f"[{index + 1}/{len(sections_to_write)}] '{current_section_id}' 섹션이 RFP 요구사항과 전략에 부합하는가?",
        },
        "message": f"[섹션 {index + 1}/{len(sections_to_write)}] '{current_section_id}' 섹션을 검토하세요.",
        "sections_written": [
            s.section_id if hasattr(s, "section_id") else s.get("section_id", "")
            for s in state.get("proposal_sections", [])
        ],
    })

    if human_input.get("approved") or human_input.get("quick_approve"):
        new_index = index + 1
        if new_index >= len(sections_to_write):
            return {
                "current_section_index": new_index,
                "current_step": "sections_complete",
                "rework_targets": [],
            }
        return {
            "current_section_index": new_index,
            "current_step": "section_approved",
        }

    # 반려 → 피드백 기록, 같은 인덱스 유지
    feedback_entry = {
        "step": "section",
        "section_id": current_section_id,
        "feedback": human_input.get("feedback", ""),
        "comments": human_input.get("comments", {}),
        "timestamp": human_input.get("timestamp", ""),
    }
    return {
        "feedback_history": [feedback_entry],
        "current_step": "section_rejected",
    }


def _build_plan_review_context(state: ProposalState) -> dict:
    """plan 리뷰 시 목차 + 스토리라인 데이터를 interrupt에 포함."""
    dynamic_sections = state.get("dynamic_sections", [])
    plan = state.get("plan")

    storylines = {}
    if plan:
        plan_dict = plan.model_dump() if hasattr(plan, "model_dump") else (plan if isinstance(plan, dict) else {})
        storylines = plan_dict.get("storylines", {})

    # 목차 + 스토리라인 요약
    toc_with_storylines = []
    story_sections = {
        (s.get("eval_item") or s.get("section_id", "")): s
        for s in storylines.get("sections", [])
    }

    for i, section_id in enumerate(dynamic_sections):
        entry = {"index": i + 1, "section_id": section_id}
        story = story_sections.get(section_id, {})
        if story:
            entry["key_message"] = story.get("key_message", "")
            entry["weight"] = story.get("weight", 0)
            entry["tone"] = story.get("tone", "")
            entry["narrative_arc"] = story.get("narrative_arc", "")
        toc_with_storylines.append(entry)

    return {
        "toc_with_storylines": toc_with_storylines,
        "overall_narrative": storylines.get("overall_narrative", ""),
        "opening_hook": storylines.get("opening_hook", ""),
        "closing_impact": storylines.get("closing_impact", ""),
        "review_instructions": (
            "## 목차 + 스토리라인 검토\n"
            "1. 목차 순서와 구성을 확인하세요.\n"
            "   - 섹션 추가/삭제/순서변경이 필요하면 'sections_reorder'에 새 순서를 전달하세요.\n"
            "2. 각 섹션의 핵심 주장(key_message)이 Win Theme과 일관되는지 확인하세요.\n"
            "3. 스토리라인 수정이 필요하면 'storyline_feedback'에 섹션별 피드백을 전달하세요.\n"
            "4. 승인 시 이 목차와 스토리라인으로 제안서 섹션별 작성이 시작됩니다."
        ),
    }


def _handle_plan_review(state: ProposalState, human_input: dict) -> dict:
    """plan 리뷰: 목차 조정 + 스토리라인 피드백 + 기본 승인/거부 처리."""
    from app.prompts.section_prompts import classify_section_type

    result = {}

    # 목차 순서 조정 (sections_reorder가 있으면 dynamic_sections 업데이트)
    new_order = human_input.get("sections_reorder", [])
    if new_order and isinstance(new_order, list):
        section_type_map = state.get("parallel_results", {}).get("_section_type_map", {})
        for sid in new_order:
            if sid not in section_type_map:
                section_type_map[sid] = classify_section_type(sid)
        result["dynamic_sections"] = new_order
        result["parallel_results"] = {"_section_type_map": section_type_map}

    # 승인
    if human_input.get("quick_approve") or human_input.get("approved"):
        result["approval"] = {"plan": ApprovalStatus(
            status="approved",
            approved_by=human_input.get("approved_by", "user"),
            approved_at=human_input.get("approved_at", ""),
        )}
        result["current_step"] = "plan_approved"
        result["rework_targets"] = []
        return result

    # 거부 + 부분 재작업
    feedback = state.get("feedback_history", [])
    latest = human_input
    rework_targets = latest.get("rework_targets", [])

    # 전략-예산 상호조정 분기
    if "strategy_generate" in rework_targets:
        result.update({
            "approval": {"plan": ApprovalStatus(
                status="rejected",
                feedback=human_input.get("feedback", ""),
            )},
            "feedback_history": [{
                "step": "plan",
                "feedback": human_input.get("feedback", ""),
                "rework_targets": rework_targets,
                "storyline_feedback": human_input.get("storyline_feedback", {}),
                "timestamp": human_input.get("timestamp", ""),
            }],
            "current_step": "plan_rejected",
            "rework_targets": rework_targets,
        })
        return result

    # 일반 재작업
    feedback_entry = {
        "step": "plan",
        "feedback": human_input.get("feedback", ""),
        "comments": human_input.get("comments", {}),
        "rework_targets": rework_targets,
        "storyline_feedback": human_input.get("storyline_feedback", {}),
        "timestamp": human_input.get("timestamp", ""),
    }
    result.update({
        "approval": {"plan": ApprovalStatus(
            status="rejected",
            feedback=human_input.get("feedback", ""),
        )},
        "feedback_history": [feedback_entry],
        "current_step": "plan_rejected",
        "rework_targets": rework_targets,
    })
    return result


def _get_artifact(state, step_name):
    mapping = {
        "search": state.get("search_results"),
        "rfp_fetch": state.get("bid_detail"),
        "go_no_go": state.get("go_no_go"),
        "rfp": state.get("rfp_analysis"),
        "strategy": state.get("strategy"),
        "plan": state.get("plan"),
        "proposal": state.get("proposal_sections"),
        "ppt": state.get("ppt_slides"),
    }
    return mapping.get(step_name)
