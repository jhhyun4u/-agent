"""
하네스 기반 섹션 작성 노드 (§26: Harness Engineering 그래프 통합)

기존 proposal_write_next를 하네스 엔지니어링으로 개선:
- 3변형 병렬 생성
- 자동 평가 및 선택
- 선택적 피드백 루프 (score < 0.75)

프로세스:
1. 섹션 정보 수집 (index, type, context)
2. 3변형 병렬 생성 (하네스)
3. 최고 점수 선택
4. 필요시 피드백 루프 1회 실행
5. 최종 섹션 저장
"""

import logging
import time
from uuid import UUID

from app.graph.context_helpers import PREV_SECTIONS_CONTENT_CHARS
from app.graph.nodes.harness_feedback_loop import HarnessFeedbackLoop
from app.graph.nodes.harness_proposal_node import HarnessProposalGenerator
from app.graph.state import ProposalState
from app.models.schemas import ProposalSection
from app.prompts.section_prompts import (
    SECTION_PROMPT_CASE_B,
    SECTION_TYPE_GUIDES,
    get_section_prompt,
    classify_section_type,
)
from app.services.core.claude_client import claude_generate
from app.services.domains.proposal.accuracy_enhancement_engine import (
    EnsembleVoter,
    ConfidenceThresholder,
)
from app.services.domains.proposal.harness_accuracy_validator import EvaluationMetrics
from app.services.domains.proposal.ensemble_metrics_monitor import get_global_monitor

logger = logging.getLogger(__name__)

# 의존성 (기존 proposal_nodes에서 복사)
try:
    from app.services.domains.proposal.prompt_registry import prompt_registry
except ImportError:
    prompt_registry = None

try:
    from app.services.domains.proposal.prompt_tracker import prompt_tracker
except ImportError:
    prompt_tracker = None


def _get_sections_to_write(state: ProposalState) -> list[str]:
    """작성할 섹션 목록 반환 (기존 로직 재사용)"""
    story = state.get("proposal_story")
    if not story:
        return []

    if isinstance(story, dict):
        sections_list = story.get("sections", [])
    else:
        sections_list = getattr(story, "sections", [])

    if not sections_list:
        return []

    # 섹션 ID 추출
    if isinstance(sections_list[0], dict):
        return [s.get("section_id") for s in sections_list]
    else:
        return [getattr(s, "section_id", "") for s in sections_list if getattr(s, "section_id")]


async def _build_context(
    state: ProposalState, section_id: str, section_type: str
) -> dict:
    """섹션 작성 컨텍스트 구성 (기존 로직 재사용)"""
    ctx = {
        "section_id": section_id,
        "section_type": section_type,
        "rfp_title": state.get("rfp_title", ""),
        "rfp_key_requirements": state.get("rfp_key_requirements", ""),
        "our_positioning": state.get("positioning_decision", ""),
        "customer_profile": str(state.get("customer_analysis", "")),
        "previous_sections_summary": "",
        "research_context": "",
        "kb_context": "",
        "style_guide": "",
    }

    # 이전 섹션 요약
    existing_sections = state.get("proposal_sections", [])
    if existing_sections:
        summaries = []
        for sec in existing_sections[-3:]:  # 최근 3개
            sec_id = sec.section_id if hasattr(sec, "section_id") else sec.get("section_id")
            sec_title = sec.title if hasattr(sec, "title") else sec.get("title")
            sec_content = (sec.content if hasattr(sec, "content") else sec.get("content")) or ""
            # 요약 (처음 N자 — context_helpers의 PREV_SECTIONS_CONTENT_CHARS 사용)
            summary = f"[{sec_id}] {sec_title}\n{sec_content[:PREV_SECTIONS_CONTENT_CHARS]}..."
            summaries.append(summary)
        ctx["previous_sections_summary"] = "\n---\n".join(summaries)

    # 리서치 컨텍스트
    research = state.get("research_results", {})
    if research:
        research_str = str(research).replace("'", '"')[:1000]
        ctx["research_context"] = f"관련 리서치:\n{research_str}"

    # KB 컨텍스트
    kb_items = state.get("kb_context", [])
    if kb_items:
        kb_str = "\n".join([str(item)[:200] for item in kb_items[:5]])
        ctx["kb_context"] = f"조직 KB:\n{kb_str}"

    return ctx


async def harness_proposal_write_next(state: ProposalState) -> dict:
    """
    STEP 4A: 하네스 기반 섹션 작성 (v4.0 개선)

    기존 proposal_write_next와 호환되지만 하네스 엔지니어링으로 강화:
    1. 3변형 병렬 생성
    2. 자동 평가 및 최고 점수 선택
    3. 선택적 피드백 루프 (score < 0.75)
    4. 상세 결과 기록
    5. 레이턴시 추적

    Args:
        state: ProposalState

    Returns:
        {
            "proposal_sections": [...],
            "current_step": "section_written",
            "quality_warnings": [...],
            "harness_results": {...},  # 하네스 상세 결과
        }
    """
    # ── 레이턴시 추적 시작 ──
    section_start_time = time.time()
    variant_generation_time = 0.0
    ensemble_voting_time = 0.0
    feedback_loop_time = 0.0

    index = state.get("current_section_index", 0)
    sections_to_write = _get_sections_to_write(state)

    if not sections_to_write or index >= len(sections_to_write):
        return {"current_step": "sections_complete"}

    section_id = sections_to_write[index]

    # ── 섹션 정보 수집 ──
    rfp = state.get("rfp_analysis")
    rfp_dict = {}
    case_type = "A"
    if rfp:
        rfp_dict = (
            rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})
        )
        case_type = rfp_dict.get("case_type", "A")

    # 섹션 유형 판별 (section_id를 title로도 활용하여 한글 키워드 매칭 개선)
    section_type_map = state.get("parallel_results", {}).get("_section_type_map", {})
    section_type = section_type_map.get(section_id) or classify_section_type(section_id, section_id)

    logger.info(
        f"🔧 하네스 섹션 작성: [{index + 1}/{len(sections_to_write)}] "
        f"{section_id} (유형: {section_type}, 케이스: {case_type})"
    )

    # ── 컨텍스트 조립 ──
    ctx = await _build_context(state, section_id, section_type)

    # ── 프롬프트 선택 ──
    proposal_id = state.get("project_id", "")

    # 레지스트리에서 프롬프트 조회
    prompt_text = ""
    prompt_version = 0
    prompt_hash = ""

    if prompt_registry:
        try:
            prompt_id_str = "section_prompts.CASE_B" if case_type == "B" else f"section_prompts.{section_type}"
            prompt_text, prompt_version, prompt_hash = await prompt_registry.get_prompt_for_experiment(
                prompt_id_str, proposal_id
            )
        except Exception as e:
            logger.debug(f"프롬프트 레지스트리 조회 실패 (기본값 사용): {e}")

    # 프롬프트 템플릿 구성
    if case_type == "B":
        template_structure = rfp_dict.get("format_template", {}).get("structure", {}).get(section_id, {})
        ctx["template_structure"] = template_structure or "(서식 구조 없음)"
        ctx["section_type_name"] = section_type
        ctx["section_type_guide"] = SECTION_TYPE_GUIDES.get(section_type, "")
        base_prompt = prompt_text or SECTION_PROMPT_CASE_B
    else:
        base_prompt = prompt_text or get_section_prompt(section_type)

    # 변형 힌트 추가
    prompt_template = f"{base_prompt}\n\n변형 지침:\n{{variant_hint}}"

    # ── 하네스 생성 (3변형 → 평가 → 선택) ──
    harness = HarnessProposalGenerator()
    variant_start = time.time()

    try:
        harness_result = await harness.generate_section(
            prompt_template=prompt_template,
            section_type=section_type,
            state=state,
            reference_materials=[
                state.get("rfp_title", ""),
                state.get("positioning_decision", ""),
            ],
            system_prompt="한국 정부 공고 제안서 작성 전문가",
        )

        variant_generation_time = (time.time() - variant_start) * 1000  # ms로 변환

        logger.info(
            f"✅ 섹션 생성 완료: {harness_result['selected_variant']} "
            f"({harness_result['score']:.1%}) - {section_id} ({variant_generation_time:.1f}ms)"
        )

    except Exception as e:
        logger.error(f"하네스 생성 실패: {e}")
        return {
            "current_step": "section_error",
            "error": f"섹션 생성 실패: {e}",
        }

    # ── STEP 4A Phase 3: 앙상블 투표 적용 (정확도 개선) ──
    # 1. 변형 점수 및 상세 정보 추출
    variant_scores = harness_result.get("scores", {})  # {conservative, balanced, creative}
    variant_details_raw = harness_result.get("details", {})  # {variant: {overall, hallucination, ...}}

    # 2. variant_details_raw → Dict[str, EvaluationMetrics] 변환
    variant_details = {}
    for variant_name, detail in variant_details_raw.items():
        if isinstance(detail, dict):
            try:
                variant_details[variant_name] = EvaluationMetrics(
                    hallucination=detail.get("hallucination", 0.0),
                    persuasiveness=detail.get("persuasiveness", 0.5),
                    completeness=detail.get("completeness", 0.5),
                    clarity=detail.get("clarity", 0.5),
                )
            except Exception as e:
                logger.warning(f"EvaluationMetrics 변환 실패 [{variant_name}]: {e}")
                variant_details[variant_name] = EvaluationMetrics(0.0, 0.5, 0.5, 0.5)

    # 3. 앙상블 투표 적용 (3개 변형 모두 있을 경우)
    ensemble_applied = False
    ensemble_result = None
    ensemble_start = time.time()
    confidence_result = None

    if variant_scores and len(variant_scores) == 3 and variant_details:
        try:
            # 앙상블 투표
            voter = EnsembleVoter()
            ensemble_result = voter.vote(variant_scores, variant_details)

            # 신뢰도 추정
            thresholder = ConfidenceThresholder()
            confidence_result = thresholder.compute_confidence(variant_scores)

            # 앙상블 점수 사용
            best_score = ensemble_result.aggregated_score
            ensemble_applied = True
            ensemble_voting_time = (time.time() - ensemble_start) * 1000  # ms로 변환

            logger.info(
                f"✅ 앙상블 투표 적용: {best_score:.1%} "
                f"(신뢰: {confidence_result.confidence:.2f}, "
                f"합의: {confidence_result.agreement_level}, "
                f"시간: {ensemble_voting_time:.1f}ms)"
            )
        except Exception as e:
            logger.warning(f"앙상블 투표 실패, 초기 점수 사용: {e}")
            best_score = harness_result.get("score", 0.0)
            ensemble_voting_time = (time.time() - ensemble_start) * 1000
    else:
        # Fallback: 기존 argmax 로직
        logger.debug(f"변형 데이터 불완전 (scores={len(variant_scores)}, details={len(variant_details)}), argmax 사용")
        best_score = harness_result.get("score", 0.0)
        ensemble_voting_time = (time.time() - ensemble_start) * 1000

    # ── 선택적 피드백 루프 (신뢰도 기반 트리거 개선) ──
    best_content = harness_result.get("content", "")
    final_score = best_score
    improved = False
    
    # 피드백 루프 트리거: 점수 미흡 OR 낮은 신뢰도 + 낮은 점수
    should_run_feedback_loop = best_score < 0.75
    if confidence_result and confidence_result.agreement_level == "LOW" and best_score < 0.85:
        should_run_feedback_loop = True
        logger.info(f"⚠️ 낮은 신뢰도 감지 ({confidence_result.confidence:.2f}), 피드백 루프 트리거")

    if should_run_feedback_loop:
        confidence_val = confidence_result.confidence if confidence_result else "N/A"
        logger.info(f"⚠️  피드백 루프 실행: 점수={best_score:.1%}, 신뢰={confidence_val}")

        feedback_loop = HarnessFeedbackLoop()
        feedback_start = time.time()

        try:
            feedback_result = await feedback_loop.iterate(
                prompt=prompt_template,
                evaluation_results=harness_result["details"],
                section_type=section_type,
                current_iteration=1,
                max_iterations=1,  # HITL이 있으므로 1회만
            )

            if feedback_result.get("should_continue"):
                # 개선된 프롬프트로 재생성
                improved_prompt = feedback_result.get("improved_prompt", prompt_template)

                logger.info("🔄 프롬프트 개선, 재생성 시작...")

                harness_result_v2 = await harness.generate_section(
                    prompt_template=improved_prompt,
                    section_type=section_type,
                    state=state,
                )

                new_score = harness_result_v2.get("score", 0.0)

                if new_score > best_score:
                    best_content = harness_result_v2.get("content", "")
                    final_score = new_score
                    improved = True

                    logger.info(
                        f"✅ 개선 성공: {best_score:.1%} → {new_score:.1%} "
                        f"({harness_result_v2.get('selected_variant')})"
                    )
                else:
                    logger.info(f"⚠️  개선 미흡, 초안 유지 ({best_score:.1%})")

            else:
                logger.info("➜ 피드백 루프 완료, 계속 진행")

            feedback_loop_time = (time.time() - feedback_start) * 1000  # ms로 변환

        except Exception as e:
            logger.warning(f"피드백 루프 실패 (초안 유지): {e}")
            feedback_loop_time = (time.time() - feedback_start) * 1000

    # ── 빈 content 감지 및 fallback ──
    if not best_content or not best_content.strip():
        logger.error(f"하네스 변형 생성 실패 (빈 content) — 직접 생성 fallback: {section_id}")
        try:
            fallback_result = await claude_generate(prompt_template)
            if isinstance(fallback_result, dict):
                best_content = fallback_result.get("content", "")
            else:
                best_content = str(fallback_result)

            if best_content and best_content.strip():
                logger.info(f"✓ Fallback으로 섹션 생성 성공: {len(best_content)}자")
                final_score = 0.5  # Fallback이므로 낮은 점수
        except Exception as e:
            logger.error(f"Fallback 생성도 실패: {e}")
            best_content = f"[섹션 생성 실패] {section_id}\n\n생성 중 오류가 발생했습니다. 수동으로 작성해주세요."

    # ── Phase 4: 메트릭 모니터링 기록 ──
    # 총 섹션 생성 시간 계산
    total_section_time = (time.time() - section_start_time) * 1000  # ms로 변환

    try:
        monitor = get_global_monitor()
        proposal_id = state.get("project_id", "unknown")

        monitor.record_section(
            proposal_id=proposal_id,
            section_id=section_id,
            confidence=confidence_result.confidence if confidence_result else None,
            score=final_score,
            ensemble_applied=ensemble_applied,
            feedback_triggered=should_run_feedback_loop,
            feedback_improved=improved,
        )

        # 레이턴시 기록
        monitor.record_latency(
            proposal_id=proposal_id,
            section_id=section_id,
            variant_generation_ms=variant_generation_time,
            ensemble_voting_ms=ensemble_voting_time,
            feedback_loop_ms=feedback_loop_time,
            total_section_ms=total_section_time,
        )

        logger.debug(
            f"📊 모니터링 기록: {section_id} "
            f"(신뢰: {confidence_result.confidence:.2f if confidence_result else 'N/A'}, "
            f"점수: {final_score:.1%}, 앙상블: {ensemble_applied}, "
            f"시간: {total_section_time:.1f}ms)"
        )
    except Exception as e:
        logger.warning(f"모니터링 기록 실패 (계속 진행): {e}")

    # ── 섹션 생성 ──
    # 하네스 결과에서 content 파싱
    section_content = best_content

    # JSON 응답인 경우 content 필드 추출
    if isinstance(section_content, dict):
        section_content = section_content.get("content", str(section_content))

    new_section = ProposalSection(
        section_id=section_id,
        title=section_id.replace("_", " ").title(),  # section_id → Section Title
        content=section_content,
        version=1,
        case_type=case_type,
        harness_score=final_score,
        harness_variant=harness_result.get("selected_variant"),
        harness_improved=improved,
    )

    # ── 기존 섹션 목록 업데이트 ──
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

    # ── 프롬프트 사용 기록 ──
    if prompt_tracker and proposal_id and prompt_version:
        try:
            prompt_id_str = (
                "section_prompts.CASE_B" if case_type == "B" else f"section_prompts.{section_type}"
            )
            await prompt_tracker.record_usage(
                proposal_id=proposal_id,
                artifact_step="harness_proposal_write_next",
                section_id=section_id,
                prompt_id=prompt_id_str,
                prompt_version=prompt_version,
                prompt_hash=prompt_hash,
            )
        except Exception as e:
            logger.debug(f"프롬프트 사용 기록 실패 (무시): {e}")

    # ── KB 자동 축적 ──
    try:
        from app.services.domains.proposal.content_library import auto_register_section

        await auto_register_section(
            org_id=state.get("org_id", ""),
            proposal_id=proposal_id,
            section_id=section_id,
            title=new_section.title,
            content=new_section.content,
            section_type=section_type,
            rfp_keywords=rfp_dict.get("tech_keywords", []),
            industry=rfp_dict.get("domain", None),
        )
    except Exception as e:
        logger.debug(f"섹션 KB 자동 축적 실패 (무시): {e}")

    # ── 버전 관리 (선택사항) ──
    try:
        from app.services.core.version_manager import execute_node_and_create_version

        sections_data = [
            s.model_dump() if hasattr(s, "model_dump") else s for s in existing_sections
        ]

        version_num, artifact_version = await execute_node_and_create_version(
            proposal_id=UUID(proposal_id) if proposal_id else UUID("00000000-0000-0000-0000-000000000000"),
            node_name="harness_proposal_write_next",
            output_key="proposal_sections",
            artifact_data=sections_data,
            user_id=UUID(state.get("created_by")) if state.get("created_by") else UUID("00000000-0000-0000-0000-000000000000"),
            state=state,
        )

        logger.info(f"Proposal sections v{version_num} created")

    except Exception as e:
        logger.debug(f"버전 관리 실패 (계속 진행): {e}")

    # ── 결과 반환 ──
    quality_warnings = []

    # 점수가 낮은 경우 경고
    if final_score < 0.65:
        quality_warnings.append({
            "section_id": section_id,
            "issues": [f"하네스 점수 낮음 ({final_score:.1%})"],
            "harness_score": final_score,
            "harness_variant": harness_result.get("selected_variant"),
        })

    update = {
        "proposal_sections": existing_sections,
        "current_step": "section_written",
        "harness_results": {
            section_id: {
                "score": final_score,
                "ensemble_score": ensemble_result.aggregated_score if ensemble_applied and ensemble_result else None,
                "confidence": confidence_result.confidence if confidence_result else None,
                "confidence_agreement": confidence_result.agreement_level if confidence_result else None,
                "variant": harness_result.get("selected_variant"),
                "improved": improved,
                "variant_scores": variant_scores,
                "ensemble_applied": ensemble_applied,
            }
        },
    }

    if quality_warnings:
        update["quality_warnings"] = quality_warnings

    logger.info(
        f"섹션 완료: {section_id} (하네스: {harness_result.get('selected_variant')} "
        f"{final_score:.1%}" + ("→ 개선됨" if improved else "") + ")"
    )

    return update
