"""
STEP 4: 제안서 섹션별 순차 작성 + 자가진단 (§9, §8)

v3.5: 섹션별 순차 작성 + 섹션별 human 리뷰 + 유형별 전문 프롬프트.
proposal_write_next: 현재 인덱스의 섹션 1개를 유형별 프롬프트로 작성.
self_review_with_auto_improve: 전체 섹션 완성 후 4축 평가.
"""

import logging

from app.graph.state import ProposalSection, ProposalState
from app.prompts.proposal_prompts import SELF_REVIEW_PROMPT
from app.prompts.section_prompts import (
    SECTION_PROMPT_CASE_B,
    SECTION_TYPE_GUIDES,
    classify_section_type,
    get_recommended_pages,
    get_section_prompt,
)
from app.prompts.strategy import POSITIONING_STRATEGY_MATRIX
from app.services.claude_client import claude_generate

logger = logging.getLogger(__name__)

MAX_AUTO_IMPROVE = 2


def _get_sections_to_write(state: ProposalState) -> list[str]:
    """현재 작성 대상 섹션 목록 반환 (rework_targets가 있으면 해당 섹션만)."""
    sections = state.get("dynamic_sections", [])
    targets = state.get("rework_targets", [])
    if targets:
        return [s for s in sections if s in targets]
    return sections


def _build_context(state: ProposalState, section_id: str, section_type: str) -> dict:
    """섹션 작성에 필요한 컨텍스트를 유형별로 조립."""
    rfp = state.get("rfp_analysis")
    rfp_dict = {}
    if rfp:
        rfp_dict = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})

    strategy = state.get("strategy")
    s_dict = {}
    if strategy:
        s_dict = strategy.model_dump() if hasattr(strategy, "model_dump") else (strategy if isinstance(strategy, dict) else {})

    positioning = state.get("positioning", "defensive")
    pos_guide = POSITIONING_STRATEGY_MATRIX.get(positioning, POSITIONING_STRATEGY_MATRIX["defensive"])

    # ── RFP 요약 ──
    rfp_summary = f"""사업명: {rfp_dict.get('project_name', '')}
발주기관: {rfp_dict.get('client', '')}
핫버튼: {rfp_dict.get('hot_buttons', [])}
평가항목: {[item.get('item', '') for item in rfp_dict.get('eval_items', [])]}
필수요건: {rfp_dict.get('mandatory_reqs', [])}
분량규격: {rfp_dict.get('volume_spec', {})}"""

    # ── 리서치 결과 ──
    research = state.get("research_brief") or {}
    research_context = "(선행 리서치 없음)"
    if research:
        topics = research.get("research_topics", [])
        if topics:
            parts = []
            for t in topics[:5]:
                parts.append(f"- **{t.get('topic', '')}**: {', '.join(t.get('findings', [])[:3])}")
            research_context = "\n".join(parts)
        elif research.get("summary"):
            research_context = research["summary"]

    # ── KB 참조 (인력, 실적, 역량) ──
    kb_refs = state.get("kb_references", [])
    kb_context = "(KB 참조 없음)"
    if kb_refs:
        kb_parts = []
        for ref in kb_refs[:5]:
            kb_parts.append(f"- [{ref.get('type', '')}] {ref.get('title', '')}: {ref.get('summary', '')[:100]}")
        kb_context = "\n".join(kb_parts)

    # ── 스토리라인 컨텍스트 (plan_story 결과) ──
    plan = state.get("plan")
    storyline_context = ""
    if plan:
        plan_dict = plan.model_dump() if hasattr(plan, "model_dump") else (plan if isinstance(plan, dict) else {})
        storylines = plan_dict.get("storylines", {})
        if storylines:
            # 전체 내러티브
            parts = []
            if storylines.get("overall_narrative"):
                parts.append(f"**전체 스토리**: {storylines['overall_narrative']}")
            if storylines.get("opening_hook"):
                parts.append(f"**도입부 핵심**: {storylines['opening_hook']}")

            # 해당 섹션 스토리라인
            for s in storylines.get("sections", []):
                s_id = s.get("eval_item") or s.get("section_id", "")
                if s_id == section_id:
                    parts.append(f"\n### 이 섹션의 스토리라인")
                    if s.get("key_message"):
                        parts.append(f"- **핵심 주장 (Assertion Title)**: {s['key_message']}")
                    if s.get("narrative_arc"):
                        parts.append(f"- **내러티브 구조**: {s['narrative_arc']}")
                    if s.get("supporting_points"):
                        parts.append(f"- **논거**: {', '.join(s['supporting_points'])}")
                    if s.get("evidence"):
                        parts.append(f"- **근거 데이터**: {', '.join(s['evidence'])}")
                    if s.get("win_theme_connection"):
                        parts.append(f"- **Win Theme 연결**: {s['win_theme_connection']}")
                    if s.get("transition_to_next"):
                        parts.append(f"- **다음 섹션 연결고리**: {s['transition_to_next']}")
                    if s.get("tone"):
                        parts.append(f"- **톤**: {s['tone']}")
                    break

            if parts:
                storyline_context = "\n\n## 스토리라인 가이드 (반드시 반영)\n" + "\n".join(parts)

    # ── 이전 섹션 컨텍스트 ──
    existing_sections = state.get("proposal_sections", [])
    prev_context = ""
    if existing_sections:
        prev_parts = []
        for s in existing_sections:
            sd = s.model_dump() if hasattr(s, "model_dump") else (s if isinstance(s, dict) else {})
            prev_parts.append(f"### {sd.get('section_id', '')}: {sd.get('title', '')}\n{sd.get('content', '')[:300]}...")
        prev_context = f"\n\n## 이전에 작성된 섹션 (참고하여 일관성 유지)\n" + "\n\n".join(prev_parts)

    # ── 이전 리뷰 피드백 ──
    feedback_history = state.get("feedback_history", [])
    section_feedback = [
        f for f in feedback_history
        if f.get("step") == "section" and f.get("section_id") == section_id
    ]
    feedback_context = ""
    if section_feedback:
        latest = section_feedback[-1]
        feedback_context = f"\n\n## 이전 리뷰 피드백 (반드시 반영)\n{latest.get('feedback', '')}"

    # ── 평가 배점 + 세부항목 ──
    eval_weight = 0
    eval_item_detail = "(해당 섹션의 평가항목 정보 없음)"
    for item in rfp_dict.get("eval_items", []):
        if item.get("item") == section_id:
            eval_weight = item.get("weight", 0)
            sub_items = item.get("sub_items", [])
            parts = [f"- 평가항목: {item.get('item', '')} (배점: {eval_weight}점)"]
            if sub_items:
                parts.append("- 세부항목:")
                for si in sub_items:
                    parts.append(f"  · {si}")
            eval_item_detail = "\n".join(parts)
            break

    total_pages = rfp_dict.get("volume_spec", {}).get("max_pages", 100)

    return {
        "section_id": section_id,
        "rfp_summary": rfp_summary,
        "positioning": positioning,
        "win_theme": s_dict.get("win_theme", ""),
        "key_messages": s_dict.get("key_messages", []),
        "ghost_theme": s_dict.get("ghost_theme", ""),
        "positioning_guide": f"{pos_guide['label']}: {pos_guide['core_message']} / 톤: {pos_guide['tone']}",
        "research_context": research_context,
        "kb_context": kb_context,
        "hot_buttons": rfp_dict.get("hot_buttons", []),
        "storyline_context": storyline_context,
        "prev_sections_context": prev_context,
        "feedback_context": feedback_context,
        "eval_weight": eval_weight,
        "eval_item_detail": eval_item_detail,
        "recommended_pages": get_recommended_pages(eval_weight, total_pages),
        "volume_spec": str(rfp_dict.get("volume_spec", {})),
        # 케이스 B 전용
        "template_structure": "",
        "section_type_name": "",
        "section_type_guide": "",
    }


async def proposal_write_next(state: ProposalState) -> dict:
    """STEP 4: 현재 인덱스의 섹션 1개를 유형별 전문 프롬프트로 작성.

    1. 섹션 유형 판별 (UNDERSTAND/STRATEGY/TECHNICAL 등)
    2. 유형에 맞는 전문 프롬프트 선택
    3. 리서치·KB·이전섹션·피드백 컨텍스트 주입
    4. 평가 배점 기반 분량 조절
    """
    index = state.get("current_section_index", 0)
    sections_to_write = _get_sections_to_write(state)

    if not sections_to_write or index >= len(sections_to_write):
        return {"current_step": "sections_complete"}

    section_id = sections_to_write[index]

    # 케이스 타입 판별
    rfp = state.get("rfp_analysis")
    rfp_dict = {}
    case_type = "A"
    if rfp:
        rfp_dict = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})
        case_type = rfp_dict.get("case_type", "A")

    # 섹션 유형 판별
    section_type_map = state.get("parallel_results", {}).get("_section_type_map", {})
    section_type = section_type_map.get(section_id) or classify_section_type(section_id)

    logger.info(f"섹션 작성: [{index + 1}/{len(sections_to_write)}] {section_id} (유형: {section_type}, 케이스: {case_type})")

    # 컨텍스트 조립
    ctx = _build_context(state, section_id, section_type)

    # 프롬프트 선택
    if case_type == "B":
        template_structure = rfp_dict.get("format_template", {}).get("structure", {}).get(section_id, {})
        ctx["template_structure"] = template_structure or "(서식 구조 없음)"
        ctx["section_type_name"] = section_type
        ctx["section_type_guide"] = SECTION_TYPE_GUIDES.get(section_type, "")
        prompt = SECTION_PROMPT_CASE_B.format(**ctx)
    else:
        prompt = get_section_prompt(section_type).format(**ctx)

    result = await claude_generate(prompt, max_tokens=6000)

    new_section = ProposalSection(
        section_id=result.get("section_id", section_id),
        title=result.get("title", section_id),
        content=result.get("content", ""),
        version=1,
        case_type=case_type,
        template_structure=result.get("template_structure") if case_type == "B" else None,
        self_review_score=result.get("self_check"),
    )

    # 기존 섹션 목록에서 같은 section_id가 있으면 교체, 없으면 추가
    existing_sections = list(state.get("proposal_sections", []))
    replaced = False
    for i, s in enumerate(existing_sections):
        sid = s.section_id if hasattr(s, "section_id") else s.get("section_id", "")
        if sid == section_id:
            existing_sections[i] = new_section
            replaced = True
            break
    if not replaced:
        existing_sections.append(new_section)

    return {
        "proposal_sections": existing_sections,
        "current_step": "section_written",
    }


async def self_review_with_auto_improve(state: ProposalState) -> dict:
    """STEP 4: AI 자가진단 + 자동 개선 루프 (§8).

    4축 평가: 컴플라이언스(25) + 전략 일관성(25) + 품질(25) + 근거 신뢰성(25) = 100
    v3.3: 원인별 5방향 라우팅.
    """
    sections = state.get("proposal_sections", [])
    compliance = state.get("compliance_matrix", [])
    strategy = state.get("strategy")
    auto_improve_count = state.get("parallel_results", {}).get("_auto_improve_count", 0)

    if not sections:
        return {"current_step": "self_review_pass"}

    # 섹션 요약
    sections_summary = ""
    for s in sections:
        if hasattr(s, "model_dump"):
            sd = s.model_dump()
        elif isinstance(s, dict):
            sd = s
        else:
            continue
        sections_summary += f"\n### {sd.get('section_id', '')}: {sd.get('title', '')}\n{sd.get('content', '')[:500]}...\n"

    # 전략 필드
    s_dict = {}
    if strategy:
        s_dict = strategy.model_dump() if hasattr(strategy, "model_dump") else (strategy if isinstance(strategy, dict) else {})

    # RFP 요구사항
    rfp = state.get("rfp_analysis")
    rfp_dict = {}
    if rfp:
        rfp_dict = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})

    rfp_requirements = f"""필수요건: {rfp_dict.get('mandatory_reqs', [])}
평가항목: {rfp_dict.get('eval_items', [])}
핫버튼: {rfp_dict.get('hot_buttons', [])}"""

    # Compliance Matrix
    compliance_text = ""
    for c in compliance:
        cd = c.model_dump() if hasattr(c, "model_dump") else (c if isinstance(c, dict) else {})
        compliance_text += f"- [{cd.get('req_id', '')}] {cd.get('content', '')} → {cd.get('status', '미확인')}\n"

    prompt = SELF_REVIEW_PROMPT.format(
        sections_summary=sections_summary[:8000],
        rfp_requirements=rfp_requirements,
        positioning=state.get("positioning", "defensive"),
        win_theme=s_dict.get("win_theme", ""),
        key_messages=s_dict.get("key_messages", []),
        compliance_matrix=compliance_text or "(Compliance Matrix 없음)",
    )

    score = await claude_generate(prompt, max_tokens=4000)

    # 총점 계산
    total = score.get("total", 0)
    if not total:
        total = (
            score.get("compliance_score", 0)
            + score.get("strategy_score", 0)
            + score.get("quality_score", 0)
            + score.get("trustworthiness", {}).get("trustworthiness_score", 0)
        )

    result = {
        "parallel_results": {
            "_self_review_score": score,
            "_auto_improve_count": auto_improve_count,
        },
    }

    # v3.3: 원인별 재시도 횟수 추적
    retry_research_count = state.get("parallel_results", {}).get("_retry_research_count", 0)
    retry_strategy_count = state.get("parallel_results", {}).get("_retry_strategy_count", 0)

    if total >= 80:
        result["current_step"] = "self_review_pass"
    elif auto_improve_count < MAX_AUTO_IMPROVE:
        trustworthiness_score = score.get("trustworthiness", {}).get("trustworthiness_score", 25)
        strategy_score = score.get("strategy_score", 25)

        if trustworthiness_score < 12 and retry_research_count < 1:
            result["parallel_results"]["_retry_research_count"] = retry_research_count + 1
            result["parallel_results"]["_auto_improve_count"] = auto_improve_count + 1
            result["current_step"] = "self_review_retry_research"
        elif strategy_score < 15 and retry_strategy_count < 1:
            result["parallel_results"]["_retry_strategy_count"] = retry_strategy_count + 1
            result["parallel_results"]["_auto_improve_count"] = auto_improve_count + 1
            result["current_step"] = "self_review_retry_strategy"
        else:
            # 약한 섹션 + 분량 미달 섹션 재작성
            section_scores = score.get("section_scores", [])
            weak_sections = []
            for s in section_scores:
                is_weak = s.get("score", 100) < 70
                depth = s.get("depth_metrics", {})
                is_thin = depth.get("min_pages_met") is False or depth.get("evidence_count", 99) < 3
                if is_weak or is_thin:
                    weak_sections.append(s["section_id"])
            result["rework_targets"] = weak_sections
            result["current_section_index"] = 0
            result["parallel_results"]["_auto_improve_count"] = auto_improve_count + 1
            result["current_step"] = "self_review_retry_sections"
    else:
        result["current_step"] = "self_review_force_review"

    return result
