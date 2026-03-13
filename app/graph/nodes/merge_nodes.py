"""
병렬 노드 결과 병합 (§4-2)

plan_merge, proposal_merge, ppt_merge:
부분 재작업 시 기존 결과 보존 + 새 결과 덮어씌움.

v3.5: plan_merge에서 storylines 기반 dynamic_sections 동기화.
"""

import logging

from app.graph.state import ProposalPlan, ProposalState
from app.prompts.section_prompts import classify_section_type

logger = logging.getLogger(__name__)


def _sync_dynamic_sections(state: ProposalState, storylines: dict) -> dict:
    """storylines.sections 기반으로 dynamic_sections + section_type_map 동기화.

    스토리라인에 정의된 섹션 순서를 우선 적용하되,
    기존 dynamic_sections에만 있는 섹션은 뒤에 보존.
    """
    story_sections = storylines.get("sections", [])
    if not story_sections:
        return {}

    # 스토리라인 섹션 순서 추출
    new_order = []
    for s in story_sections:
        section_id = s.get("eval_item") or s.get("section_id", "")
        if section_id and section_id not in new_order:
            new_order.append(section_id)

    if not new_order:
        return {}

    # 기존 dynamic_sections에만 있는 항목은 뒤에 보존
    existing = state.get("dynamic_sections", [])
    for sid in existing:
        if sid not in new_order:
            new_order.append(sid)

    # 섹션 유형 자동 분류 갱신
    section_type_map = state.get("parallel_results", {}).get("_section_type_map", {})
    for sid in new_order:
        if sid not in section_type_map:
            section_type_map[sid] = classify_section_type(sid)

    logger.info(f"목차 동기화: {len(existing)}개 → {len(new_order)}개 섹션")
    return {
        "dynamic_sections": new_order,
        "parallel_results": {"_section_type_map": section_type_map},
    }


def plan_merge(state: ProposalState) -> dict:
    """STEP 3 병합: 부분 재작업 시 기존 plan 보존 + storylines 기반 목차 동기화."""
    new_results = state.get("parallel_results", {})
    existing_plan = state.get("plan")

    if existing_plan and state.get("rework_targets"):
        merged = existing_plan.model_dump() if hasattr(existing_plan, "model_dump") else dict(existing_plan)
        for key, value in new_results.items():
            merged[key] = value
        plan = ProposalPlan(**merged)
    else:
        # 최초 실행: parallel_results에서 조합
        defaults = {"team": [], "deliverables": [], "schedule": {}, "storylines": {}, "bid_price": {}}
        defaults.update(new_results)
        plan = ProposalPlan(**defaults)

    result = {"plan": plan, "rework_targets": []}

    # storylines 기반 dynamic_sections 동기화
    sync = _sync_dynamic_sections(state, plan.storylines if hasattr(plan, "storylines") else plan.model_dump().get("storylines", {}))
    result.update(sync)

    return result


def proposal_merge(state: ProposalState) -> dict:
    """STEP 4 병합: 섹션 결과 취합. 부분 재작업 시 기존 섹션 보존."""
    new_sections = state.get("parallel_results", {}).get("sections", [])
    existing_sections = list(state.get("proposal_sections", []))

    if state.get("rework_targets") and existing_sections:
        new_ids = {s.section_id if hasattr(s, "section_id") else s.get("section_id", "") for s in new_sections}
        kept = [s for s in existing_sections if (s.section_id if hasattr(s, "section_id") else s.get("section_id", "")) not in new_ids]
        return {"proposal_sections": kept + new_sections, "rework_targets": []}
    else:
        return {"proposal_sections": new_sections, "rework_targets": []}


def ppt_merge(state: ProposalState) -> dict:
    """STEP 5 병합: PPT 슬라이드 취합."""
    new_slides = state.get("parallel_results", {}).get("slides", [])
    existing_slides = list(state.get("ppt_slides", []))

    if state.get("rework_targets") and existing_slides:
        new_ids = {s.slide_id if hasattr(s, "slide_id") else s.get("slide_id", "") for s in new_slides}
        kept = [s for s in existing_slides if (s.slide_id if hasattr(s, "slide_id") else s.get("slide_id", "")) not in new_ids]
        return {"ppt_slides": kept + new_slides, "rework_targets": []}
    else:
        return {"ppt_slides": new_slides, "rework_targets": []}
