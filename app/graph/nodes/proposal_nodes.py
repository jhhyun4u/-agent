"""
STEP 4: 제안서 섹션별 순차 작성 + 자가진단 (§9, §8)

v3.5: 섹션별 순차 작성 + 섹션별 human 리뷰 + 유형별 전문 프롬프트.
proposal_write_next: 현재 인덱스의 섹션 1개를 유형별 프롬프트로 작성.
self_review_with_auto_improve: 전체 섹션 완성 후 4축 평가.
"""

import asyncio
import logging
from uuid import UUID

from app.graph.state import ProposalSection, ProposalState
from app.graph.context_helpers import (
    build_prev_sections_context,
    extract_credible_research,
    get_strategy_dict,
    rfp_to_dict,
)
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
from app.services import prompt_registry, prompt_tracker
# NOTE: version_manager import moved to function level to avoid supabase hang on import

logger = logging.getLogger(__name__)

MAX_AUTO_IMPROVE = 2


async def _persist_node_result(
    table: str,
    proposal_id: str,
    created_by: str,
    payload: dict,
    log_msg: str = "",
) -> None:
    """DB에 노드 실행 결과 저장 (공통 헬퍼)."""
    if not proposal_id or not created_by:
        return

    try:
        from app.utils.supabase_client import get_async_client

        db = await get_async_client()
        await db.table(table).insert(payload).execute()
        if log_msg:
            logger.info(log_msg)
    except Exception as e:
        logger.warning(f"Failed to save {table}: {e}")


def _get_sections_to_write(state: ProposalState) -> list[str]:
    """현재 작성 대상 섹션 목록 반환 (rework_targets가 있으면 해당 섹션만)."""
    sections = state.get("dynamic_sections", [])
    targets = state.get("rework_targets", [])
    if targets:
        return [s for s in sections if s in targets]
    return sections


async def _build_context(state: ProposalState, section_id: str, section_type: str) -> dict:
    """섹션 작성에 필요한 컨텍스트를 유형별로 조립."""
    rfp_dict = rfp_to_dict(state.get("rfp_analysis"))
    s_dict = get_strategy_dict(state.get("strategy"))

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
    research_context = extract_credible_research(state.get("research_brief"), max_evidence=10) or "(선행 리서치 없음)"

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
                    parts.append("\n### 이 섹션의 스토리라인")
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

    # ── 이전 섹션 컨텍스트 (최근 3개만 content 포함, 이전은 title만) ──
    existing_sections = state.get("proposal_sections", [])
    prev_context = build_prev_sections_context(existing_sections)

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

    # ── Compliance Matrix (v3.9: 섹션별 요구사항 체크리스트 주입) ──
    compliance = state.get("compliance_matrix", [])
    compliance_context = ""
    if compliance:
        relevant = []
        for c in compliance:
            cd = c.model_dump() if hasattr(c, "model_dump") else (c if isinstance(c, dict) else {})
            status = cd.get("status", "미확인")
            if status != "충족":  # 미확인+미충족 항목만 표시
                relevant.append(f"- [{cd.get('req_id', '')}] {cd.get('content', '')} (상태: {status})")
        if relevant:
            compliance_context = "\n\n## Compliance 체크리스트 (이 섹션에서 커버 가능한 요구사항)\n" + "\n".join(relevant[:15])

    # ── 과거 교훈 (동일 발주기관/유사 섹션 유형) ──
    # 최적화: parallel_results에 캐시된 데이터 재사용 (N+1 쿼리 방지)
    lessons_context = ""
    try:
        parallel_results = state.get("parallel_results", {})
        cached_lessons = parallel_results.get("_cached_lessons")

        if cached_lessons is None:
            # 첫 번째 섹션: 캐시 없음 → DB에서 조회 후 캐시
            from app.utils.supabase_client import get_async_client as _get_db
            db = await _get_db()
            client_name = rfp_dict.get("client", "")
            lessons_data = []
            if client_name:
                lessons = await (
                    db.table("lessons_learned")
                    .select("title, result, effective_points, weak_points, improvements")
                    .ilike("client_name", f"%{client_name}%")
                    .order("created_at", desc=True)
                    .limit(3)
                    .execute()
                )
                lessons_data = lessons.data or []
            # 캐시에 저장 (이후 섹션은 여기서 조회)
            parallel_results["_cached_lessons"] = lessons_data
        else:
            # 이후 섹션: 캐시에서 조회
            lessons_data = cached_lessons

        if lessons_data:
            parts = []
            for ls in lessons_data:
                r = "수주" if ls.get("result") == "won" else "패찰"
                parts.append(
                    f"- [{r}] {ls.get('title', '')}: "
                    f"강점={ls.get('effective_points', '-')}, "
                    f"약점={ls.get('weak_points', '-')}, "
                    f"개선={ls.get('improvements', '-')}"
                )
            lessons_context = "\n\n## 과거 교훈 (이 발주기관에서의 경험, 반드시 참고)\n" + "\n".join(parts)
    except Exception as e:
        logger.debug(f"보조 데이터 조회 실패 (무시): {e}")
        pass

    # ── 평가 배점 + 세부항목 ──
    eval_weight = 0
    from app.prompts.section_prompts import EVAL_ITEM_FALLBACK
    eval_item_detail = EVAL_ITEM_FALLBACK
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

    # 유사 콘텐츠 자동 추천 (C-3)
    reference_content = ""
    try:
        from app.services.content_library import suggest_content_for_section
        suggestions = await suggest_content_for_section(
            section_topic=f"{section_id} {section_type}",
            org_id=state.get("org_id", ""),
            top_k=3,
        )
        if suggestions:
            parts = []
            for s in suggestions[:3]:
                excerpt = (s.get("body_excerpt") or s.get("body", ""))[:300]
                score = s.get("quality_score", 0)
                parts.append(f"- [{score}점] {s.get('title', '')}: {excerpt}")
            reference_content = "\n\n## 참고 콘텐츠 (KB 유사 콘텐츠, 참고하되 그대로 복사 금지)\n" + "\n".join(parts)
    except Exception as e:
        logger.debug(f"보조 데이터 조회 실패 (무시): {e}")
        pass

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
        "feedback_context": feedback_context + lessons_context + compliance_context,
        "eval_weight": eval_weight,
        "eval_item_detail": eval_item_detail,
        "recommended_pages": get_recommended_pages(eval_weight, total_pages),
        "volume_spec": str(rfp_dict.get("volume_spec", {})),
        "reference_content": reference_content,
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
    ctx = await _build_context(state, section_id, section_type)

    # 프롬프트 선택 (레지스트리 연동)
    prompt_id_str = "section_prompts.CASE_B" if case_type == "B" else f"section_prompts.{section_type}"
    proposal_id = state.get("project_id", "")

    try:
        text, ver, hash_ = await prompt_registry.get_prompt_for_experiment(
            prompt_id_str, proposal_id
        )
    except Exception as e:
        logger.debug(f"프롬프트 레지스트리 조회 실패 (무시): {e}")
        text, ver, hash_ = "", 0, ""

    if case_type == "B":
        template_structure = rfp_dict.get("format_template", {}).get("structure", {}).get(section_id, {})
        ctx["template_structure"] = template_structure or "(서식 구조 없음)"
        ctx["section_type_name"] = section_type
        ctx["section_type_guide"] = SECTION_TYPE_GUIDES.get(section_type, "")
        prompt = (text or SECTION_PROMPT_CASE_B).format(**ctx)
    else:
        prompt = (text or get_section_prompt(section_type)).format(**ctx)

    result = await claude_generate(prompt, max_tokens=6000, step_name="proposal_write_next")

    # 프롬프트 사용 기록
    if proposal_id and ver:
        try:
            await prompt_tracker.record_usage(
                proposal_id=proposal_id,
                artifact_step="proposal_write_next",
                section_id=section_id,
                prompt_id=prompt_id_str,
                prompt_version=ver,
                prompt_hash=hash_,
            )
        except Exception as e:
            logger.debug(f"프롬프트 사용 기록 실패 (무시): {e}")

    new_section = ProposalSection(
        section_id=result.get("section_id", section_id),
        title=result.get("title", section_id),
        content=result.get("content", ""),
        version=1,
        case_type=case_type,
        template_structure=result.get("template_structure") if case_type == "B" else None,
        self_review_score=result.get("self_check"),
    )

    # ── self_check 품질 게이트 ──
    self_check = result.get("self_check", {})
    depth = self_check.get("depth_score", {})
    evidence_count = depth.get("evidence_count", 0)
    tables_count = depth.get("tables_or_diagrams", 0)
    abstract_pct = depth.get("abstract_ratio_pct", 0)

    quality_issues = []
    if evidence_count < 3:
        quality_issues.append(f"근거 부족 ({evidence_count}/3)")
    if tables_count < 1:
        quality_issues.append("표/다이어그램 0개")
    if abstract_pct > 40:
        quality_issues.append(f"추상적 서술 비율 {abstract_pct}%")
    # eval_sub_items 미대응 체크
    if not self_check.get("eval_sub_items_all_addressed", True):
        quality_issues.append("평가 세부항목 미대응")

    if quality_issues:
        logger.warning(
            "[품질게이트] section=%s 품질 이슈: %s (재생성 권장)",
            section_id, quality_issues,
        )
        # state에 품질 경고 기록 (리뷰 노드에서 참조 가능)
        quality_warnings = list(state.get("quality_warnings", []))
        quality_warnings.append({
            "section_id": section_id,
            "issues": quality_issues,
            "depth_score": depth,
        })
        # 반환 dict에 quality_warnings 추가
        # (LangGraph Annotated reducer가 병합)

    # KB 자동 축적 (A-1: fire-and-forget)
    try:
        from app.services.content_library import auto_register_section
        await auto_register_section(
            org_id=state.get("org_id", ""),
            proposal_id=state.get("project_id", ""),
            section_id=section_id,
            title=new_section.title,
            content=new_section.content,
            section_type=section_type,
            rfp_keywords=rfp_dict.get("tech_keywords", []),
            industry=rfp_dict.get("domain", None),
        )
    except Exception as e:
        logger.debug(f"섹션 KB 자동 축적 실패 (무시): {e}")

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

    # Phase 1: Create artifact version for proposal_sections
    try:
        from app.services.version_manager import execute_node_and_create_version
        
        sections_data = [
            s.model_dump() if hasattr(s, "model_dump") else s
            for s in existing_sections
        ]
        version_num, artifact_version = await execute_node_and_create_version(
            proposal_id=UUID(state.get("project_id")),
            node_name="proposal_write_next",
            output_key="proposal_sections",
            artifact_data=sections_data,
            user_id=UUID(state.get("created_by")),
            state=state
        )
        logger.info(f"Proposal sections v{version_num} created for proposal {state.get('project_id')}")
    except Exception as e:
        logger.warning(f"Proposal sections versioning 실패 (계속 진행): {e}")

    update: dict = {
        "proposal_sections": existing_sections,
        "current_step": "section_written",
    }
    if quality_issues:
        update["quality_warnings"] = quality_warnings
    return update


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
    s_dict = get_strategy_dict(strategy)

    # RFP 요구사항
    rfp_dict = rfp_to_dict(state.get("rfp_analysis"))

    rfp_requirements = f"""필수요건: {rfp_dict.get('mandatory_reqs', [])}
평가항목: {rfp_dict.get('eval_items', [])}
핫버튼: {rfp_dict.get('hot_buttons', [])}"""

    # Compliance Matrix
    compliance_text = ""
    for c in compliance:
        cd = c.model_dump() if hasattr(c, "model_dump") else (c if isinstance(c, dict) else {})
        compliance_text += f"- [{cd.get('req_id', '')}] {cd.get('content', '')} → {cd.get('status', '미확인')}\n"

    # 레지스트리에서 진화된 프롬프트 조회
    proposal_id_for_exp = state.get("project_id", "")
    try:
        sr_text, _, _ = await prompt_registry.get_prompt_for_experiment(
            "proposal_prompts.SELF_REVIEW_PROMPT", proposal_id_for_exp
        )
    except Exception as e:
        logger.debug(f"프롬프트 레지스트리 조회 실패 (무시): {e}")
        sr_text = ""

    prompt = (sr_text or SELF_REVIEW_PROMPT).format(
        sections_summary=sections_summary[:8000],
        rfp_requirements=rfp_requirements,
        positioning=state.get("positioning", "defensive"),
        win_theme=s_dict.get("win_theme", ""),
        key_messages=s_dict.get("key_messages", []),
        compliance_matrix=compliance_text or "(Compliance Matrix 없음)",
    )

    score = await claude_generate(prompt, max_tokens=4000)

    # 프롬프트 사용 기록 (자가진단) + 섹션별 품질 점수 DB 저장
    proposal_id = state.get("project_id", "")
    if proposal_id:
        try:
            _, sr_ver, sr_hash = await prompt_registry.get_active_prompt("proposal_prompts.SELF_REVIEW_PROMPT")
            await prompt_tracker.record_usage(
                proposal_id=proposal_id,
                artifact_step="self_review",
                section_id=None,
                prompt_id="proposal_prompts.SELF_REVIEW_PROMPT",
                prompt_version=sr_ver,
                prompt_hash=sr_hash,
                quality_score=score.get("total", 0) or 0,
            )

            # 섹션별 품질 점수를 prompt_artifact_link에 업데이트 (병렬 처리)
            section_scores = score.get("section_scores", [])
            if section_scores:
                try:
                    from app.utils.supabase_client import get_async_client
                    db = await get_async_client()

                    # 최적화: 모든 섹션의 최신 링크 ID를 먼저 조회
                    sec_ids = [ss.get("section_id", "") for ss in section_scores if ss.get("section_id")]
                    if sec_ids:
                        links = await (
                            db.table("prompt_artifact_link")
                            .select("id, section_id")
                            .eq("proposal_id", proposal_id)
                            .in_("section_id", sec_ids)
                            .order("created_at", desc=True)
                            .execute()
                        )

                        # section_id → id 매핑 생성 (가장 최근 것)
                        id_map = {}
                        if links.data:
                            for link in links.data:
                                sec_id = link.get("section_id")
                                if sec_id and sec_id not in id_map:
                                    id_map[sec_id] = link.get("id")

                        # 모든 업데이트를 병렬로 수행
                        async def update_score(sec_id: str, sec_score: float) -> None:
                            link_id = id_map.get(sec_id)
                            if link_id:
                                try:
                                    await db.table("prompt_artifact_link").update(
                                        {"quality_score": sec_score}
                                    ).eq("id", link_id).execute()
                                except Exception as e:
                                    logger.debug(f"섹션 {sec_id} 점수 업데이트 실패: {e}")

                        updates = [
                            update_score(ss.get("section_id", ""), ss.get("score"))
                            for ss in section_scores
                            if ss.get("section_id") and ss.get("score") is not None
                        ]
                        if updates:
                            await asyncio.gather(*updates)
                except Exception as e:
                    logger.debug(f"섹션 점수 일괄 업데이트 실패 (무시): {e}")
        except Exception as e:
            logger.debug(f"콘텐츠 라이브러리 업데이트 실패 (무시): {e}")

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



async def section_quality_check(state: ProposalState) -> dict:
    """STEP 4A-②: 섹션 품질 진단 (4축 평가).
    
    현재 작성된 섹션의 품질을 AI가 4축으로 진단:
    1. 규격/요건 준수 (Compliance OK)
    2. 스토리라인 핵심 메시지 반영도
    3. 근거·데이터 충족도 (0-100)
    4. 경쟁 차별성 표현도 (0-100)
    
    출력: DiagnosisResult (종합점수, 이슈 목록, 권장조치)
    """
    from app.prompts.proposal_prompts import SECTION_QUALITY_CHECK_PROMPT
    
    # 현재 섹션 가져오기
    sections = state.get("proposal_sections", [])
    index = state.get("current_section_index", 0)
    
    if not sections or index >= len(sections):
        return {"diagnosis_result": None}
    
    current_section = sections[index]
    if hasattr(current_section, "model_dump"):
        section_dict = current_section.model_dump()
    else:
        section_dict = current_section if isinstance(current_section, dict) else {}
    
    section_id = section_dict.get("section_id", "")
    section_content = section_dict.get("content", "")
    section_title = section_dict.get("title", "")
    
    # 스토리라인 컨텍스트 추출
    plan = state.get("plan")
    storyline_for_section = ""
    if plan:
        plan_dict = plan.model_dump() if hasattr(plan, "model_dump") else (plan if isinstance(plan, dict) else {})
        storylines = plan_dict.get("storylines", {})
        if storylines:
            for s in storylines.get("sections", []):
                if s.get("eval_item") == section_id or s.get("section_id") == section_id:
                    storyline_for_section = f"""
- 핵심 주장: {s.get('key_message', '')}
- 논거: {', '.join(s.get('supporting_points', []))}
- 근거 데이터: {', '.join(s.get('evidence', []))}
- Win Theme 연결: {s.get('win_theme_connection', '')}
"""
                    break
    
    # RFP 요구사항
    rfp = state.get("rfp_analysis")
    rfp_dict = rfp_to_dict(rfp)
    
    # Compliance Matrix (해당 섹션의 요구사항)
    compliance = state.get("compliance_matrix", [])
    relevant_compliance = ""
    for c in compliance:
        cd = c.model_dump() if hasattr(c, "model_dump") else (c if isinstance(c, dict) else {})
        status = cd.get("status", "미확인")
        if status != "충족":  # 미확인, 미충족 항목만
            relevant_compliance += f"- [{cd.get('req_id', '')}] {cd.get('content', '')}\\n"
    
    # 전략 컨텍스트
    strategy = state.get("strategy")
    s_dict = get_strategy_dict(strategy)
    
    # 프롬프트 조립
    prompt = f"""## 섹션 품질 진단 (4축 평가)

### 섹션 정보
- ID: {section_id}
- 제목: {section_title}
- 내용:
```
{section_content[:2000]}
```

### 스토리라인 (반영 요구사항)
{storyline_for_section or "(스토리라인 없음)"}

### RFP 요구사항
- 필수요건: {rfp_dict.get('mandatory_reqs', [])}
- 핫버튼: {rfp_dict.get('hot_buttons', [])}

### Compliance 체크리스트
{relevant_compliance or "(해당 요구사항 없음)"}

### 제안 전략
- 포지셔닝: {state.get('positioning', 'defensive')}
- Win Theme: {s_dict.get('win_theme', '')}
- 핵심 메시지: {s_dict.get('key_messages', [])}

---

## 진단 항목

### 1. 규격/요건 준수 (Compliance OK)
- RFP 필수요건 모두 충족? (Yes/No)
- 미충족 항목이 있다면 명시

### 2. 스토리라인 핵심 메시지 반영도
- 위 스토리라인의 핵심 주장이 이 섹션에 명확히 반영되었는가? 
- 평가: 명확함(100) ~ 불명확(0)

### 3. 근거·데이터 충족도 (0-100)
- 수치 데이터, 실적, 사례 등의 근거가 충분한가?
- 각 주장이 구체적인 증거로 뒷받침되었는가?
- 평가: 충분(100) ~ 부족(0)

### 4. 경쟁 차별성 표현도 (0-100)
- 경쟁사 대비 우리의 차별화 포인트가 명확한가?
- Win Theme이 독특하고 설득력 있게 표현되었는가?
- 평가: 우수(100) ~ 미흡(0)

---

## 출력 형식 (JSON)

```json
{{
  "compliance_ok": true,  // RFP 필수요건 충족 여부
  "compliance_issues": ["미충족 항목1"],  // 있으면 명시, 없으면 []
  "storyline_gap": "핵심 메시지가 X 부분에서 잘 반영됨",  // 한 문장 평가
  "evidence_score": 75,  // 0-100
  "diff_score": 68,  // 0-100
  "overall_score": 71,  // (compliance_ok: 25점) + storyline_gap(0-25) + evidence(0-25) + diff(0-25) = 0-100
  "issues": [
    {{
      "type": "compliance",  // "compliance", "storyline", "evidence", "differentiation"
      "severity": "warning",  // "error", "warning", "info"
      "description": "구체적 지적사항",
      "fix_guidance": "개선 방안"
    }}
  ],
  "recommendation": "approve"  // "approve", "modify", "rework"
}}
```

생각해보기:
- 수치를 정확히 계산
- 실제 문제점을 정확히 파악
- 개선 방안은 구체적으로
"""
    
    diagnosis = await claude_generate(prompt, max_tokens=3000, step_name="section_quality_check")
    
    # DiagnosisResult 모델로 변환
    from app.graph.state import DiagnosisResult
    
    result = DiagnosisResult(
        compliance_ok=diagnosis.get("compliance_ok", False),
        storyline_gap=diagnosis.get("storyline_gap", ""),
        evidence_score=diagnosis.get("evidence_score", 0),
        diff_score=diagnosis.get("diff_score", 0),
        overall_score=diagnosis.get("overall_score", 0),
        issues=diagnosis.get("issues", []),
        recommendation=diagnosis.get("recommendation", "rework"),
    )
    
    # DB 저장: section_diagnostics 테이블에 진단 결과 기록
    await _persist_node_result(
        table="section_diagnostics",
        proposal_id=state.get("project_id"),
        created_by=state.get("created_by"),
        payload={
            "proposal_id": state.get("project_id"),
            "section_id": section_id,
            "section_title": section_title,
            "section_index": index,
            "compliance_ok": result.compliance_ok,
            "storyline_gap": result.storyline_gap,
            "evidence_score": float(result.evidence_score),
            "diff_score": float(result.diff_score),
            "overall_score": float(result.overall_score),
            "issues": result.issues,
            "recommendation": result.recommendation,
            "diagnosed_by": state.get("created_by"),
        },
        log_msg=f"Section diagnosis saved: {state.get('project_id')}/{section_id} (score: {result.overall_score})",
    )
    
    return {"diagnosis_result": result}


async def storyline_gap_analysis(state: ProposalState) -> dict:
    """STEP 4A-⑤: 스토리라인 vs 실제 작성 내용 갭 분석.
    
    plan_story 스토리라인 설계와 실제 proposal_sections의 내용을 비교하여:
    1. 빠진 핵심 포인트
    2. 논리 구멍 (연결고리 단절)
    3. 섹션간 전환(transition) 검증
    4. 메시지 일관성
    
    출력: GapReport (갭 목록, 권장 조치)
    """
    from app.graph.state import GapReport
    
    # 계획 스토리라인
    plan = state.get("plan")
    if not plan:
        return {"gap_report": None}
    
    plan_dict = plan.model_dump() if hasattr(plan, "model_dump") else (plan if isinstance(plan, dict) else {})
    storylines = plan_dict.get("storylines", {})
    
    if not storylines:
        return {"gap_report": None}
    
    # 실제 작성된 섹션들
    sections = state.get("proposal_sections", [])
    sections_text = ""
    section_summaries = []
    
    for i, s in enumerate(sections):
        if hasattr(s, "model_dump"):
            sd = s.model_dump()
        else:
            sd = s if isinstance(s, dict) else {}
        
        section_id = sd.get("section_id", "")
        title = sd.get("title", "")
        content = sd.get("content", "")[:1000]  # 처음 1000자만
        
        sections_text += f"\n### {i+1}. [{section_id}] {title}\n{content}\n"
        section_summaries.append({"id": section_id, "title": title})
    
    # 계획된 스토리라인 텍스트
    storyline_sections = storylines.get("sections", [])
    planned_text = f"""
## 계획된 내러티브 (Plan)
전체 스토리: {storylines.get('overall_narrative', '')}
도입부 핵심: {storylines.get('opening_hook', '')}
"""
    
    for s in storyline_sections:
        planned_text += f"""
### {s.get('eval_item', '')}
- 핵심 주장: {s.get('key_message', '')}
- 논거: {', '.join(s.get('supporting_points', []))}
- 근거 데이터: {', '.join(s.get('evidence', []))}
- Win Theme 연결: {s.get('win_theme_connection', '')}
- 다음 섹션 연결: {s.get('transition_to_next', '')}
"""
    
    planned_text += f"""
마무리 메시지: {storylines.get('closing_impact', '')}
"""
    
    # 갭 분석 프롬프트
    prompt = f"""## 스토리라인 갭 분석

### 계획된 스토리라인
{planned_text}

---

### 실제 작성된 섹션 내용
{sections_text}

---

## 분석 과제

1. **빠진 핵심 포인트**: 계획에는 있지만 실제 섹션에서 빠진 주요 메시지나 논거
2. **논리 구멍 (연결고리 단절)**: 섹션 간의 논리적 연결이 끊어진 부분
3. **약한 전환(Weak Transitions)**: 섹션 간 전환이 부자연스러운 부분
4. **메시지 일관성 문제**: Win Theme이나 핵심 메시지가 일관성 있게 반복되지 않는 부분

## 출력 형식 (JSON)

```json
{{
  "missing_points": [
    "계획에는 X 포인트가 있었으나 섹션에서 빠짐"
  ],
  "logic_gaps": [
    {{
      "section": "섹션ID",
      "issue": "논리 문제 설명",
      "impact": "이로 인한 영향"
    }}
  ],
  "weak_transitions": [
    {{
      "from_section": "섹션A",
      "to_section": "섹션B", 
      "issue": "연결 문제 설명"
    }}
  ],
  "inconsistencies": [
    "메시지 일관성 문제 설명"
  ],
  "overall_assessment": "전체 평가 (한 문장)",
  "recommended_actions": [
    "권장 조치 1",
    "권장 조치 2"
  ]
}}
```

주의:
- 실제 내용에 기반하여 정확히 분석
- 구체적인 섹션명과 내용을 인용
- 실행 가능한 개선안을 제시
"""
    
    gap_analysis = await claude_generate(prompt, max_tokens=3000, step_name="storyline_gap_analysis")
    
    # GapReport 모델로 변환
    result = GapReport(
        missing_points=gap_analysis.get("missing_points", []),
        logic_gaps=gap_analysis.get("logic_gaps", []),
        weak_transitions=gap_analysis.get("weak_transitions", []),
        inconsistencies=gap_analysis.get("inconsistencies", []),
        overall_assessment=gap_analysis.get("overall_assessment", ""),
        recommended_actions=gap_analysis.get("recommended_actions", []),
    )
    
    # DB 저장: proposal_gap_analyses 테이블에 갭 분석 결과 기록
    await _persist_node_result(
        table="proposal_gap_analyses",
        proposal_id=state.get("project_id"),
        created_by=state.get("created_by"),
        payload={
            "proposal_id": state.get("project_id"),
            "missing_points": result.missing_points,
            "logic_gaps": result.logic_gaps,
            "weak_transitions": result.weak_transitions,
            "inconsistencies": result.inconsistencies,
            "overall_assessment": result.overall_assessment,
            "recommended_actions": result.recommended_actions,
            "status": "pending",  # HITL 리뷰 대기
            "analyzed_by": state.get("created_by"),
        },
        log_msg=f"Gap analysis saved: {state.get('project_id')} (status: pending)",
    )
    
    return {"gap_report": result}
