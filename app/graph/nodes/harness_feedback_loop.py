"""
하네스 피드백 루프 (§26: Harness Engineering Iteration)

평가 결과 → 프롬프트 개선 → 재생성의 자동화

프로세스:
1. Analyzer: 평가 결과 분석 (약점 식별)
2. Suggester: 프롬프트 개선안 제시
3. Refiner: 개선된 프롬프트 생성
4. Verifier: 개선 효과 확인

반복 조건:
- score < 0.75 (불통과)
- max_iterations: 3회 (비용 제어)
"""

import logging
from dataclasses import dataclass

from app.services.core.claude_client import claude_generate

logger = logging.getLogger(__name__)


@dataclass
class FeedbackAnalysis:
    """평가 결과 분석"""

    weak_areas: list[str]  # ["hallucination", "persuasiveness", ...]
    improvement_priority: str  # "critical" | "high" | "medium" | "low"
    suggested_changes: str  # 개선 제안 텍스트
    refactoring_needed: bool  # 근본적 구조 변경 필요 여부


@dataclass
class ImprovedPrompt:
    """개선된 프롬프트"""

    original: str
    improved: str
    reasoning: str  # 변경 이유
    focus_areas: list[str]  # 중점 개선 영역


class HarnessFeedbackAnalyzer:
    """평가 결과 분석 및 개선 제안 생성"""

    async def analyze_evaluation(
        self,
        evaluation_detail: dict,
        section_type: str,
        variant_name: str,
    ) -> FeedbackAnalysis:
        """
        평가 결과 분석 → 약점 식별 + 개선안 제시

        Args:
            evaluation_detail: {
                "overall": 0.5,
                "hallucination": 0.4,
                "persuasiveness": 0.6,
                "completeness": 0.5,
                "clarity": 0.7,
                "feedback": "신뢰성 부족 - 출처/근거 명시"
            }
            section_type: 섹션 타입
            variant_name: 변형 이름

        Returns:
            FeedbackAnalysis 객체
        """
        logger.info(f"분석 중: {section_type} ({variant_name})")

        weak_areas = []
        threshold = 0.65

        # 약점 식별
        metrics = {
            "hallucination": evaluation_detail.get("hallucination", 0.5),
            "persuasiveness": evaluation_detail.get("persuasiveness", 0.5),
            "completeness": evaluation_detail.get("completeness", 0.5),
            "clarity": evaluation_detail.get("clarity", 0.5),
        }

        for metric, score in metrics.items():
            if score < threshold:
                weak_areas.append(metric)

        # 우선순위 판정
        overall_score = evaluation_detail.get("overall", 0.5)
        if overall_score < 0.5:
            priority = "critical"
        elif overall_score < 0.65:
            priority = "high"
        elif overall_score < 0.75:
            priority = "medium"
        else:
            priority = "low"

        # 개선안 제시 (Claude 기반)
        analysis_prompt = f"""
평가 결과를 분석하고 프롬프트 개선안을 제시하세요.

섹션 타입: {section_type}
변형: {variant_name}
종합 점수: {overall_score:.1%}

평가 결과:
- 신뢰성 (hallucination): {metrics['hallucination']:.1%}
- 설득력 (persuasiveness): {metrics['persuasiveness']:.1%}
- 완전성 (completeness): {metrics['completeness']:.1%}
- 명확성 (clarity): {metrics['clarity']:.1%}

기존 피드백: {evaluation_detail.get('feedback', 'N/A')}

JSON 형식으로 응답:
{{
  "weak_areas_analysis": "약점 영역별 분석",
  "root_cause": "근본 원인",
  "suggested_improvements": "구체적 개선안",
  "refactoring_needed": true/false
}}
"""

        try:
            analysis_response = await claude_generate(
                prompt=analysis_prompt,
                response_format="json",
                step_name=f"feedback_analysis_{section_type}",
            )

            suggested_changes = analysis_response.get(
                "suggested_improvements", "개선안 없음"
            )
            refactoring = analysis_response.get("refactoring_needed", False)

        except Exception as e:
            logger.warning(f"Claude 분석 실패: {e}, 휴리스틱 사용")
            suggested_changes = self._heuristic_suggestions(weak_areas)
            refactoring = len(weak_areas) >= 3

        return FeedbackAnalysis(
            weak_areas=weak_areas,
            improvement_priority=priority,
            suggested_changes=suggested_changes,
            refactoring_needed=refactoring,
        )

    def _heuristic_suggestions(self, weak_areas: list[str]) -> str:
        """약점 영역별 휴리스틱 제안"""
        suggestions = []

        if "hallucination" in weak_areas:
            suggestions.append("- 구체적 수치·사례 추가 (최소 3개)")
            suggestions.append("- 출처 명시 및 검증 기준 강화")

        if "persuasiveness" in weak_areas:
            suggestions.append("- 논리적 구조 명확화 (문제→해결→효과)")
            suggestions.append("- 대상 고객 니즈와의 연결 강화")
            suggestions.append("- STAR 기법 활용 (Situation→Task→Action→Result)")

        if "completeness" in weak_areas:
            suggestions.append("- 필수 요소 체크리스트 적용")
            suggestions.append("- 섹션별 목차 구조 재검토")

        if "clarity" in weak_areas:
            suggestions.append("- 문장 길이 단순화 (15~25 단어/문장)")
            suggestions.append("- 불릿 포인트 활용")
            suggestions.append("- 단락 구분 명확화")

        return "\n".join(suggestions) if suggestions else "근본적 재작성 검토"


class HarnessPromptRefiner:
    """프롬프트 개선 및 재작성"""

    async def refine_prompt(
        self,
        original_prompt: str,
        analysis: FeedbackAnalysis,
        section_type: str,
        max_retries: int = 3,
    ) -> ImprovedPrompt:
        """
        피드백 기반 프롬프트 개선

        Args:
            original_prompt: 원본 프롬프트
            analysis: FeedbackAnalysis 객체
            section_type: 섹션 타입
            max_retries: 최대 재시도 횟수

        Returns:
            ImprovedPrompt 객체
        """
        logger.info(f"프롬프트 개선 중: {section_type}")

        refinement_prompt = f"""
다음 프롬프트를 개선하세요.

섹션 타입: {section_type}
약점: {', '.join(analysis.weak_areas)}
개선 우선순위: {analysis.improvement_priority}

개선 방향:
{analysis.suggested_changes}

원본 프롬프트:
---
{original_prompt}
---

개선된 프롬프트:
---
(여기에 개선된 프롬프트를 작성하세요. 본질적 의도는 유지하되, 약점 보완)
---

JSON 형식으로 응답:
{{
  "improved_prompt": "개선된 프롬프트",
  "changes_made": ["변경 항목 1", "변경 항목 2", ...],
  "expected_improvement": "기대 효과"
}}
"""

        try:
            response = await claude_generate(
                prompt=refinement_prompt,
                response_format="json",
                step_name=f"prompt_refinement_{section_type}",
            )

            improved = response.get("improved_prompt", original_prompt)
            changes = response.get("changes_made", [])
            expected = response.get("expected_improvement", "")

            logger.info(
                f"✓ 프롬프트 개선 완료: {len(changes)} 항목 수정, "
                f"기대 개선: {expected[:50]}..."
            )

            return ImprovedPrompt(
                original=original_prompt,
                improved=improved,
                reasoning=f"{analysis.improvement_priority}: {expected}",
                focus_areas=analysis.weak_areas,
            )

        except Exception as e:
            logger.error(f"프롬프트 개선 실패: {e}")
            return ImprovedPrompt(
                original=original_prompt,
                improved=original_prompt,
                reasoning=f"개선 실패: {e}",
                focus_areas=analysis.weak_areas,
            )


class HarnessFeedbackLoop:
    """통합 피드백 루프"""

    def __init__(self):
        self.analyzer = HarnessFeedbackAnalyzer()
        self.refiner = HarnessPromptRefiner()
        self.iteration_history: list[dict] = []

    async def iterate(
        self,
        prompt: str,
        evaluation_results: dict,
        section_type: str,
        current_iteration: int = 1,
        max_iterations: int = 3,
    ) -> dict:
        """
        단일 반복 사이클: 분석 → 개선 → 결과

        Args:
            prompt: 현재 프롬프트
            evaluation_results: {
                "conservative": {...},
                "balanced": {...},
                "creative": {...}
            }
            section_type: 섹션 타입
            current_iteration: 현재 반복 번호
            max_iterations: 최대 반복 횟수

        Returns:
            {
                "iteration": int,
                "should_continue": bool,
                "best_variant": str,
                "best_score": float,
                "improved_prompt": str,
                "analysis": FeedbackAnalysis,
            }
        """
        logger.info(f"피드백 루프 [반복 {current_iteration}/{max_iterations}]")

        # 최고 점수 변형 분석
        best_variant = max(
            evaluation_results.items(), key=lambda x: x[1].get("overall", 0)
        )
        best_variant_name, best_eval = best_variant
        best_score = best_eval.get("overall", 0)

        # 통과 판정
        should_continue = (
            best_score < 0.75 and current_iteration < max_iterations
        )

        # 분석
        analysis = await self.analyzer.analyze_evaluation(
            evaluation_detail=best_eval,
            section_type=section_type,
            variant_name=best_variant_name,
        )

        # 개선 (필요한 경우만)
        improved_prompt = prompt
        if should_continue:
            improved = await self.refiner.refine_prompt(
                original_prompt=prompt,
                analysis=analysis,
                section_type=section_type,
            )
            improved_prompt = improved.improved

        # 이력 기록
        history_entry = {
            "iteration": current_iteration,
            "best_variant": best_variant_name,
            "best_score": best_score,
            "weak_areas": analysis.weak_areas,
            "priority": analysis.improvement_priority,
            "prompt_improved": improved_prompt != prompt,
        }
        self.iteration_history.append(history_entry)

        logger.info(
            f"반복 {current_iteration} 완료: "
            f"{best_variant_name} {best_score:.1%}, "
            f"계속: {should_continue}"
        )

        return {
            "iteration": current_iteration,
            "should_continue": should_continue,
            "best_variant": best_variant_name,
            "best_score": best_score,
            "weak_areas": analysis.weak_areas,
            "priority": analysis.improvement_priority,
            "improved_prompt": improved_prompt,
            "analysis": analysis,
            "history": self.iteration_history,
        }

    def get_summary(self) -> dict:
        """반복 이력 요약"""
        if not self.iteration_history:
            return {"iterations": 0, "total_improvement": 0}

        first_score = self.iteration_history[0].get("best_score", 0)
        last_score = self.iteration_history[-1].get("best_score", 0)

        return {
            "iterations": len(self.iteration_history),
            "initial_score": first_score,
            "final_score": last_score,
            "total_improvement": last_score - first_score,
            "improved": last_score > first_score,
            "history": self.iteration_history,
        }
