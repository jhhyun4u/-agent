"""
공통 리뷰 게이트 노드 (§5)

Shipley Color Team 관점별 차별화된 리뷰.
interrupt()로 프론트엔드 /resume 대기.
빠른 승인, 결재선 다단계 승인, 포지셔닝 변경 지원.
"""

import asyncio
import logging

from langgraph.types import interrupt

from app.graph.state import (
    ApprovalChainEntry,
    ApprovalStatus,
    ProposalState,
)

logger = logging.getLogger(__name__)

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
    "bid_plan": {
        "perspective": "가격결정 위원회 관점",
        "focus": "어떤 가격으로 입찰할 것인가? 수주확률과 마진의 최적 균형점은?",
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
    # v4.0: 분기 워크플로 신규 노드
    "submission_plan": {
        "perspective": "제출관리 담당자 관점",
        "focus": "제출서류 목록이 빠짐없는가? 준비 일정은 현실적인가?",
    },
    "cost_sheet": {
        "perspective": "원가관리 전문가 관점",
        "focus": "산출내역서가 정확한가? 노임단가 기준에 맞는가?",
    },
    "submission_checklist": {
        "perspective": "품질관리 담당자 관점",
        "focus": "모든 필수 서류가 준비되었는가? 누락 항목은 없는가?",
    },
    "mock_evaluation": {
        "perspective": "Red Team (모의 평가) 관점",
        "focus": "평가위원이 이 제안서에 높은 점수를 줄 것인가? 약점은?",
    },
    "eval_result": {
        "perspective": "프로젝트 관리자 관점",
        "focus": "실제 평가결과와 모의평가 대비 차이는? 교훈은?",
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

        # PSM-16: PPT 리뷰 시 Q&A 입력 안내
        if step_name == "ppt":
            interrupt_data["qa_reminder"] = (
                "발표 완료 후, 프로젝트 상세 → Q&A 탭에서 "
                "질의응답 기록을 등록하면 향후 제안에 활용됩니다."
            )

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

        # 입찰가격계획 리뷰: 시나리오 선택 + 수동 오버라이드
        if step_name == "bid_plan":
            return _handle_bid_plan_review(state, human_input)

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
            result["feedback_history"] = [{
                "step": "go_no_go",
                "feedback": f"포지셔닝 오버라이드: {state.get('positioning')} → {override}",
                "override_reason": human_input.get("positioning_override_reason", ""),
                "original_positioning": state.get("positioning"),
                "new_positioning": override,
                "timestamp": human_input.get("timestamp", ""),
            }]
        # 결재선 확인
        chain_result = _check_approval_chain(state, "go_no_go", human_input)
        if chain_result:
            return chain_result

        # ── 3-Stream 초기화: Go 결정 시 스트림 레코드 생성 + 제출서류 추출 ──
        _fire_stream_initialization(state)

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
        override_reason = human_input.get("positioning_override_reason", "")
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
                "override_reason": override_reason,
                "original_positioning": state.get("positioning"),
                "new_positioning": override,
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
        # 승인된 섹션 → content_library 자동 등록 (자가학습 루프)
        if current_section:
            try:
                _auto_register_to_content_library(state, current_section, current_section_id)
            except Exception:
                pass  # 콘텐츠 등록 실패는 워크플로 차단하지 않음

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
    state.get("feedback_history", [])
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


def _auto_register_to_content_library(state: ProposalState, section, section_id: str) -> None:
    """승인된 섹션을 content_library에 자동 등록 (비동기 fire-and-forget).

    사람이 리뷰하고 승인한 섹션 = 높은 품질 → 다음 제안서에서 재활용 가능.
    """

    sd = section.model_dump() if hasattr(section, "model_dump") else (section if isinstance(section, dict) else {})
    content_text = sd.get("content", "")
    if not content_text or len(content_text) < 100:
        return  # 너무 짧은 섹션은 스킵

    rfp = state.get("rfp_analysis")
    rfp_dict = {}
    if rfp:
        rfp_dict = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})

    from app.prompts.section_prompts import classify_section_type
    section_type = classify_section_type(section_id, sd.get("title", ""))

    async def _register():
        try:
            from app.utils.supabase_client import get_async_client
            client = await get_async_client()
            org_id = state.get("org_id", "")
            if not org_id:
                return

            # 중복 체크 (같은 proposal_id + section_id)
            existing = await (
                client.table("content_library")
                .select("id")
                .eq("proposal_id", state.get("project_id", ""))
                .eq("section_type", section_type)
                .eq("title", sd.get("title", section_id))
                .limit(1)
                .execute()
            )
            if existing.data:
                return  # 이미 등록됨

            await client.table("content_library").insert({
                "org_id": org_id,
                "type": "sections",
                "title": sd.get("title", section_id),
                "content": content_text[:50000],
                "section_type": section_type,
                "proposal_id": state.get("project_id", ""),
                "client_name": rfp_dict.get("client", ""),
                "industry": rfp_dict.get("industry", ""),
                "positioning": state.get("positioning", ""),
                "quality_score": sd.get("self_review_score", {}).get("depth_score", {}).get("evidence_count", 0) if isinstance(sd.get("self_review_score"), dict) else 0,
                "change_source": "human_approved_section",
                "status": "draft",
            }).execute()
        except Exception:
            pass  # fire-and-forget

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_register())
    except RuntimeError:
        pass  # 이벤트 루프 없으면 스킵


def _handle_bid_plan_review(state: ProposalState, human_input: dict) -> dict:
    """STEP 2.5: 입찰가격계획 리뷰 — 시나리오 선택 + 수동 오버라이드 + 결재선 + DB persist."""
    from app.graph.nodes.bid_plan import _build_constraint

    if human_input.get("approved") or human_input.get("quick_approve"):
        bid_plan = state.get("bid_plan")
        selected = human_input.get("selected_scenario", "balanced")
        custom_price = human_input.get("custom_bid_price")
        custom_reason = human_input.get("custom_bid_reason", "")

        # bid_plan에 선택 결과 반영
        updates = {}
        if bid_plan:
            bp = bid_plan.model_copy() if hasattr(bid_plan, "model_copy") else bid_plan
            if hasattr(bp, "selected_scenario"):
                bp.selected_scenario = selected
            if custom_price:
                if hasattr(bp, "user_override_price"):
                    bp.user_override_price = int(custom_price)
                    bp.user_override_reason = custom_reason
            updates["bid_plan"] = bp

            # 선택된 시나리오 기반 constraint 재계산
            constraint = _build_constraint(bp, selected)

            # 수동 오버라이드 시 constraint 조정
            if custom_price:
                override_price = int(custom_price)
                # constraint가 빈 dict일 수 있으므로 기본 필드 보장
                constraint.setdefault("scenario_name", selected)
                constraint.setdefault("cost_standard", "KOSA")
                constraint["total_bid_price"] = override_price
                rfp = state.get("rfp_analysis")
                budget = 0
                if rfp:
                    rfp_d = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})
                    from app.services.bid_calculator import parse_budget_string
                    budget = parse_budget_string(rfp_d.get("budget", "")) or 0
                if budget > 0:
                    constraint["bid_ratio"] = round(override_price / budget * 100, 2)
                constraint["labor_budget"] = int(override_price * 0.62)
                avg_monthly = 6_800_000
                constraint["max_team_mm"] = round(constraint["labor_budget"] / avg_monthly, 1)

            updates["bid_budget_constraint"] = constraint

        # 결재선 다단계 승인 (고위험 의사결정)
        chain_result = _check_approval_chain(state, "bid_plan", human_input)
        if chain_result:
            # 결재 아직 미완 — state 업데이트는 하되 pending 상태
            updates.update(chain_result)
            return updates

        approval = ApprovalStatus(
            status="approved",
            approved_by=human_input.get("approved_by", "user"),
            approved_at=human_input.get("approved_at", ""),
        )
        # 결재선 기존 chain 보존
        existing = state.get("approval", {}).get("bid_plan", ApprovalStatus())
        approval.chain = existing.chain

        updates["approval"] = {"bid_plan": approval}
        updates["current_step"] = "bid_plan_approved"
        updates["rework_targets"] = []

        # ── DB persist + artifact + 알림 (fire-and-forget) ──
        _fire_bid_confirmation(state, updates, human_input)

        return updates

    # 거부: 전략으로 돌아가기 or 재시뮬레이션
    back_to_strategy = human_input.get("back_to_strategy", False)
    feedback_entry = {
        "step": "bid_plan",
        "feedback": human_input.get("feedback", ""),
        "back_to_strategy": back_to_strategy,
        "timestamp": human_input.get("timestamp", ""),
    }
    return {
        "approval": {"bid_plan": ApprovalStatus(
            status="rejected",
            feedback=human_input.get("feedback", ""),
        )},
        "feedback_history": [feedback_entry],
        "current_step": "bid_plan_rejected",
    }


def _fire_bid_confirmation(state: ProposalState, updates: dict, human_input: dict) -> None:
    """bid_plan 승인 후 DB persist + artifact 저장 + 알림을 비동기 fire-and-forget."""

    constraint = updates.get("bid_budget_constraint", {})
    bid_price = constraint.get("total_bid_price", 0)
    bid_ratio = constraint.get("bid_ratio", 0)
    scenario_name = constraint.get("scenario_name", "balanced")
    proposal_id = state.get("project_id", "")
    user_id = human_input.get("approved_by", "")
    user_name = human_input.get("approver_name", "")
    custom_reason = human_input.get("custom_bid_reason", "")

    if not proposal_id or not bid_price:
        return

    bp = updates.get("bid_plan")
    bp_data = bp.model_dump() if hasattr(bp, "model_dump") else (bp if isinstance(bp, dict) else {})

    async def _persist():
        try:
            from app.services.bid_handoff import persist_bid_confirmation
            await persist_bid_confirmation(
                proposal_id=proposal_id,
                bid_price=bid_price,
                bid_ratio=bid_ratio,
                scenario_name=scenario_name,
                user_id=user_id,
                user_name=user_name,
                override_reason=custom_reason,
                bid_plan_data=bp_data,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"bid_plan DB persist 실패: {e}")

        try:
            from app.services.notification_service import notify_bid_confirmed
            team_id = state.get("team_id", "")
            await notify_bid_confirmed(
                proposal_id=proposal_id,
                bid_price=bid_price,
                scenario_name=scenario_name,
                team_id=team_id,
            )
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"bid_plan 알림 실패: {e}")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_persist())
    except RuntimeError:
        logger.warning("이벤트 루프 없음 — bid persist 스킵")


def _fire_stream_initialization(state: ProposalState) -> None:
    """Go 결정 시 3-Stream 초기화 + Stream 3(제출서류) 체크리스트 추출을 비동기 실행."""

    proposal_id = state.get("project_id", "")
    if not proposal_id:
        return

    async def _init():
        try:
            from app.services.stream_orchestrator import initialize_streams
            await initialize_streams(proposal_id)
        except Exception as e:
            logger.warning(f"3-Stream 초기화 실패: {e}")

        # Stream 3: RFP 텍스트가 있으면 제출서류 자동 추출
        try:
            rfp = state.get("rfp_analysis")
            rfp_dict = {}
            if rfp:
                rfp_dict = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})
            rfp_raw = state.get("rfp_raw", "")
            if rfp_raw or rfp_dict:
                from app.services.submission_docs_service import extract_checklist_from_rfp
                await extract_checklist_from_rfp(proposal_id, rfp_raw, rfp_dict)
        except Exception as e:
            logger.warning(f"제출서류 자동 추출 실패 (무시): {e}")

    try:
        loop = asyncio.get_running_loop()
        loop.create_task(_init())
    except RuntimeError:
        logger.warning("이벤트 루프 없음 — Stream 초기화 스킵")


def _get_artifact(state, step_name):
    mapping = {
        "search": state.get("search_results"),
        "rfp_fetch": state.get("bid_detail"),
        "go_no_go": state.get("go_no_go"),
        "rfp": state.get("rfp_analysis"),
        "strategy": state.get("strategy"),
        "bid_plan": state.get("bid_plan"),
        "plan": state.get("plan"),
        "proposal": state.get("proposal_sections"),
        "ppt": state.get("ppt_slides"),
        "submission_plan": state.get("submission_plan"),
        "cost_sheet": state.get("cost_sheet"),
        "submission_checklist": state.get("submission_checklist_result"),
        "mock_evaluation": state.get("mock_evaluation_result"),
        "eval_result": state.get("eval_result"),
    }
    return mapping.get(step_name)
