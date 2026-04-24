"""
하네스 제안서 생성 노드 (§26: Harness Engineering)

Generator-Evaluator 루프:
1. Generator: 3개 프롬프트 변형(conservative/balanced/creative) 병렬 생성
2. Evaluator: 각 결과를 품질 점수로 평가
3. Selector: 최고 점수 선택

사용 사례:
- 제안 섹션 고품질 생성
- 다양한 관점 비교
- 자동 품질 관리
"""

import logging
from typing import Any

from app.graph.state import ProposalState
from app.services.core.claude_client import claude_generate_multiple_variants
from app.services.domains.proposal.harness_evaluator import SectionEvaluator

logger = logging.getLogger(__name__)


class HarnessProposalGenerator:
    """하네스 기반 제안서 섹션 생성기"""

    def __init__(self):
        self.evaluator = SectionEvaluator()

    async def generate_section(
        self,
        prompt_template: str,
        section_type: str,
        state: ProposalState,
        reference_materials: list[str] | None = None,
        system_prompt: str = "",
    ) -> dict[str, Any]:
        """
        섹션 3변형 생성 → 평가 → 최적 선택

        Args:
            prompt_template: 기본 프롬프트 (template format)
            section_type: 섹션 타입 (executive_summary, technical_approach, 등)
            state: ProposalState
            reference_materials: 검증용 참고 자료
            system_prompt: 추가 시스템 프롬프트

        Returns:
            {
                "section_type": str,
                "selected_variant": str,  # conservative/balanced/creative
                "content": str,  # 최고 점수 내용
                "score": float,  # 최고 점수
                "scores": {
                    "conservative": float,
                    "balanced": float,
                    "creative": float,
                },
                "details": {
                    "conservative": {...},  # 전체 평가 결과
                    "balanced": {...},
                    "creative": {...},
                },
                "reference_materials": list[str],  # 사용된 참고 자료
            }
        """
        logger.info(f"🔧 하네스 생성 시작: {section_type}")

        try:
            # Step 1: 3개 변형 병렬 생성
            variants = await claude_generate_multiple_variants(
                base_prompt=prompt_template,
                system_prompt=system_prompt,
                section_type=section_type,
                max_tokens=3000,
                step_name=f"harness_{section_type}",
            )

            if not variants:
                logger.error(f"변형 생성 실패: {section_type}")
                return self._empty_result(section_type)

            # Step 2: 각 변형 평가
            evaluation_results = {}
            scores = {}

            for variant in variants:
                variant_name = variant["variant"]
                content = variant.get("content", "")

                if not content:
                    logger.warning(f"빈 변형 감지: {variant_name}")
                    scores[variant_name] = 0.0
                    evaluation_results[variant_name] = {
                        "overall": 0.0,
                        "error": "Empty content",
                    }
                    continue

                try:
                    # 평가 수행
                    score = await self.evaluator.evaluate(
                        section_content=content,
                        section_type=section_type,
                        reference_materials=reference_materials,
                    )

                    scores[variant_name] = score.overall
                    evaluation_results[variant_name] = {
                        "overall": score.overall,
                        "hallucination": score.hallucination,
                        "persuasiveness": score.persuasiveness,
                        "completeness": score.completeness,
                        "clarity": score.clarity,
                        "feedback": score.feedback,
                        "passed": score.passed,
                    }

                    logger.info(
                        f"  {variant_name}: {score.overall:.1%} "
                        f"(신뢰 {score.hallucination:.1%}, "
                        f"설득 {score.persuasiveness:.1%}, "
                        f"완전 {score.completeness:.1%}, "
                        f"명확 {score.clarity:.1%})"
                    )

                except Exception as e:
                    logger.error(f"평가 실패 [{variant_name}]: {e}")
                    scores[variant_name] = 0.5
                    evaluation_results[variant_name] = {"overall": 0.5, "error": str(e)}

            # Step 3: 최고 점수 선택
            best_variant = max(scores, key=scores.get) if scores else None
            best_score = scores.get(best_variant, 0.0) if best_variant else 0.0

            if best_variant:
                best_content = next(
                    (v["content"] for v in variants if v["variant"] == best_variant),
                    "",
                )
            else:
                best_content = ""

            logger.info(
                f"✅ 최고 선택: {best_variant} ({best_score:.1%}) - {section_type}"
            )

            return {
                "section_type": section_type,
                "selected_variant": best_variant,
                "content": best_content,
                "score": best_score,
                "scores": scores,
                "details": evaluation_results,
                "reference_materials": reference_materials or [],
                "variant_count": len(variants),
            }

        except Exception as e:
            logger.error(f"하네스 생성 중 치명적 오류: {e}")
            return self._empty_result(section_type)

    def _empty_result(self, section_type: str) -> dict[str, Any]:
        """오류 발생 시 기본 응답"""
        return {
            "section_type": section_type,
            "selected_variant": None,
            "content": "",
            "score": 0.0,
            "scores": {"conservative": 0.0, "balanced": 0.0, "creative": 0.0},
            "details": {},
            "reference_materials": [],
            "error": True,
        }


async def harness_proposal_node(state: ProposalState) -> dict[str, Any]:
    """
    LangGraph 노드: 하네스 기반 제안서 섹션 생성

    현재는 제안 전략 확인 후 각 섹션별 하네스 실행 예정.
    (향후 proposal_nodes의 proposal_generate와 통합)

    Args:
        state: ProposalState

    Returns:
        {
            "harness_results": {
                "executive_summary": {...},
                "technical_approach": {...},
                ...
            }
        }
    """
    logger.info("🚀 하네스 제안서 생성 노드 시작")

    harness = HarnessProposalGenerator()
    results = {}

    # 예시: executive_summary 섹션 생성
    # 실제 운영에서는 동적으로 섹션 목록 반복
    if state.strategy:
        try:
            prompt_template = """
당신은 20년 경력의 제안서 작성 전문가입니다.

다음 정보를 바탕으로 Executive Summary를 작성하세요:
- 공고: {rfp_title}
- 우리의 포지셔닝: {positioning}
- 핵심 제안 가치: {key_value}

변형 지침:
{variant_hint}

Executive Summary (300-400 단어):
"""
            # 상태에서 필요 정보 추출
            rfp_title = state.rfp_title or "정부 용역과제"
            positioning = state.strategy.get("positioning", "") if state.strategy else ""
            key_value = state.strategy.get("key_value_proposition", "") if state.strategy else ""

            result = await harness.generate_section(
                prompt_template=prompt_template,
                section_type="executive_summary",
                state=state,
                reference_materials=[rfp_title, positioning],
                system_prompt="한국 정부 공고에 맞춘 전문적 제안서 작성",
            )

            results["executive_summary"] = result

            logger.info(
                f"✓ Executive Summary 생성 완료: "
                f"{result['selected_variant']} ({result['score']:.1%})"
            )

        except Exception as e:
            logger.error(f"Executive Summary 생성 실패: {e}")
            results["executive_summary"] = {"error": str(e)}

    logger.info(f"하네스 제안서 생성 완료: {len(results)} 섹션")

    return {"harness_results": results}
