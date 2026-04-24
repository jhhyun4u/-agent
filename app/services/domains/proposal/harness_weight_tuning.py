"""
가중치 조정 엔진 - STEP 4A Phase 3 (Weight Tuning, Section-Specific Rules, Feedback)

정확도 최적화를 위한 3가지 핵심 기법:
1. Weight Tuning - Grid Search로 최적 가중치 찾기
2. Section-Specific Rules - 섹션 유형별 맞춤 규칙
3. Feedback Integration - 사용자 피드백으로 지속 학습

성과 목표: Precision 97%+ 달성, False Positive < 8%
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime
import numpy as np
from enum import Enum
import logging

from app.services.domains.proposal.harness_evaluator import EvaluationScore
from app.services.domains.proposal.harness_accuracy_validator import TestSection

logger = logging.getLogger(__name__)


class SectionType(str, Enum):
    """섹션 타입 분류"""
    EXECUTIVE_SUMMARY = "executive_summary"
    TECHNICAL_DETAILS = "technical_details"
    TEAM = "team"
    PROJECT_PLAN = "project_plan"
    PRICING = "pricing"


@dataclass
class SectionTypeWeights:
    """섹션 타입별 메트릭 가중치"""
    section_type: SectionType
    hallucination_weight: float = 0.4  # 각 메트릭의 가중치 (합=1.0)
    persuasiveness_weight: float = 0.25
    completeness_weight: float = 0.2
    clarity_weight: float = 0.15

    def normalize(self):
        """가중치 정규화 (합=1.0)"""
        total = (
            self.hallucination_weight +
            self.persuasiveness_weight +
            self.completeness_weight +
            self.clarity_weight
        )
        if total > 0:
            self.hallucination_weight /= total
            self.persuasiveness_weight /= total
            self.completeness_weight /= total
            self.clarity_weight /= total


@dataclass
class GridSearchResult:
    """Grid Search 결과"""
    best_weights: Dict[str, float]
    best_f1_score: float
    best_precision: float
    best_recall: float
    search_history: List[Dict] = field(default_factory=list)
    iterations: int = 0


@dataclass
class FeedbackEntry:
    """사용자 피드백"""
    section_id: str
    section_type: SectionType
    user_assessment: float  # 0-1, 사용자가 판단한 hallucination 정도
    ai_prediction: float    # 0-1, AI가 예측한 hallucination
    is_correct: bool        # AI 예측이 맞았는지
    feedback_timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SectionRule:
    """섹션 유형별 규칙"""
    section_type: SectionType
    rule_name: str
    condition: Callable[[EvaluationScore], bool]  # 규칙 적용 조건
    adjustment: float  # hallucination 점수 조정값 (-0.2 ~ +0.2)
    priority: int = 1  # 우선순위 (1=낮음, 5=높음)


class WeightTuningEngine:
    """가중치 조정 엔진 - Phase 3 핵심"""

    def __init__(self):
        """초기화"""
        self.section_weights: Dict[SectionType, SectionTypeWeights] = {}
        self._initialize_default_weights()
        self.feedback_history: List[FeedbackEntry] = []
        self.section_rules: List[SectionRule] = []
        self._initialize_default_rules()

    def _initialize_default_weights(self):
        """기본 가중치 초기화"""
        for section_type in SectionType:
            self.section_weights[section_type] = SectionTypeWeights(
                section_type=section_type
            )

    def _initialize_default_rules(self):
        """기본 규칙 초기화"""
        # Executive Summary 규칙: 설득력이 높으면 hallucination 점수 감소
        self.section_rules.append(
            SectionRule(
                section_type=SectionType.EXECUTIVE_SUMMARY,
                rule_name="high_persuasiveness_reduces_hallucination",
                condition=lambda s: s.persuasiveness > 0.8,
                adjustment=-0.1,
                priority=3
            )
        )

        # Technical Details 규칙: 완성도가 높고 명확하면 hallucination 점수 감소
        self.section_rules.append(
            SectionRule(
                section_type=SectionType.TECHNICAL_DETAILS,
                rule_name="detailed_and_clear_reduces_hallucination",
                condition=lambda s: s.completeness > 0.8 and s.clarity > 0.8,
                adjustment=-0.15,
                priority=4
            )
        )

        # Team 규칙: 설득력이 낮으면 hallucination 점수 증가 (신뢰성 문제)
        self.section_rules.append(
            SectionRule(
                section_type=SectionType.TEAM,
                rule_name="low_persuasiveness_increases_hallucination",
                condition=lambda s: s.persuasiveness < 0.4,
                adjustment=+0.15,
                priority=3
            )
        )

        # Pricing 규칙: 완성도가 낮으면 hallucination 점수 증가
        self.section_rules.append(
            SectionRule(
                section_type=SectionType.PRICING,
                rule_name="incomplete_pricing_increases_hallucination",
                condition=lambda s: s.completeness < 0.6,
                adjustment=+0.12,
                priority=3
            )
        )

    async def grid_search(
        self,
        test_sections: List[TestSection],
        evaluation_func: Callable,
        param_ranges: Optional[Dict[str, Tuple[float, float]]] = None
    ) -> GridSearchResult:
        """
        Grid Search로 최적 가중치 찾기

        Args:
            test_sections: 테스트 섹션 리스트
            evaluation_func: 평가 함수 (점수 계산)
            param_ranges: 파라미터 범위 (예: {"hallucination": (0.3, 0.5)})

        Returns:
            최적 가중치와 성과
        """
        if param_ranges is None:
            # 기본 범위: 각 메트릭 가중치 0.1 ~ 0.5
            param_ranges = {
                "hallucination": (0.2, 0.6),
                "persuasiveness": (0.1, 0.4),
                "completeness": (0.1, 0.4),
                "clarity": (0.1, 0.3)
            }

        # Grid 생성 (step=0.05)
        step = 0.05
        weights_to_test = []

        hallucination_range = np.arange(
            param_ranges["hallucination"][0],
            param_ranges["hallucination"][1] + step,
            step
        )

        for h_weight in hallucination_range:
            for p_weight in np.arange(0.1, 0.4 + step, step):
                for c_weight in np.arange(0.1, 0.4 + step, step):
                    for cl_weight in np.arange(0.1, 0.3 + step, step):
                        # 정규화
                        total = h_weight + p_weight + c_weight + cl_weight
                        weights = {
                            "hallucination": h_weight / total,
                            "persuasiveness": p_weight / total,
                            "completeness": c_weight / total,
                            "clarity": cl_weight / total
                        }
                        weights_to_test.append(weights)

        logger.info(f"Grid Search: {len(weights_to_test)} weight combinations to test")

        # 각 가중치 조합 테스트
        best_f1 = 0
        best_weights = None
        best_precision = 0
        best_recall = 0
        search_history = []

        for idx, weights in enumerate(weights_to_test):
            # 평가 함수로 성과 계산
            result = await evaluation_func(weights, test_sections)

            search_history.append({
                "iteration": idx,
                "weights": weights,
                "f1_score": result.get("f1_score", 0),
                "precision": result.get("precision", 0),
                "recall": result.get("recall", 0)
            })

            if result.get("f1_score", 0) > best_f1:
                best_f1 = result["f1_score"]
                best_precision = result.get("precision", 0)
                best_recall = result.get("recall", 0)
                best_weights = weights

        return GridSearchResult(
            best_weights=best_weights or {},
            best_f1_score=best_f1,
            best_precision=best_precision,
            best_recall=best_recall,
            search_history=search_history,
            iterations=len(weights_to_test)
        )

    def apply_section_rules(
        self,
        section: TestSection,
        score: EvaluationScore
    ) -> Tuple[float, List[str]]:
        """
        섹션 유형별 규칙 적용

        Args:
            section: 섹션
            score: 평가 점수

        Returns:
            (조정된 hallucination 점수, 적용된 규칙 리스트)
        """
        adjusted_hallucination = score.hallucination
        applied_rules = []

        # 섹션 타입 매핑
        try:
            section_type = SectionType(section.section_type)
        except ValueError:
            return adjusted_hallucination, applied_rules

        # 해당 섹션 타입의 규칙 찾기
        for rule in self.section_rules:
            if rule.section_type == section_type:
                # 규칙 조건 확인
                if rule.condition(score):
                    adjusted_hallucination += rule.adjustment
                    applied_rules.append(f"{rule.rule_name} ({rule.adjustment:+.2f})")

        # 범위 클리핑 (0-1)
        adjusted_hallucination = max(0.0, min(1.0, adjusted_hallucination))

        return adjusted_hallucination, applied_rules

    def add_feedback(self, feedback: FeedbackEntry):
        """사용자 피드백 추가"""
        self.feedback_history.append(feedback)
        logger.info(
            f"Feedback added: {feedback.section_id} "
            f"(user: {feedback.user_assessment:.2f}, ai: {feedback.ai_prediction:.2f}, "
            f"correct: {feedback.is_correct})"
        )

    def calculate_feedback_accuracy(self) -> Dict[str, float]:
        """피드백 기반 정확도 계산"""
        if not self.feedback_history:
            return {
                "total_feedback": 0,
                "accuracy": 0.0,
                "avg_prediction_error": 0.0
            }

        correct_count = sum(1 for f in self.feedback_history if f.is_correct)
        errors = [
            abs(f.user_assessment - f.ai_prediction)
            for f in self.feedback_history
        ]

        return {
            "total_feedback": len(self.feedback_history),
            "accuracy": correct_count / len(self.feedback_history),
            "avg_prediction_error": np.mean(errors),
            "max_prediction_error": np.max(errors),
            "min_prediction_error": np.min(errors)
        }

    def adapt_weights_from_feedback(self) -> Dict[SectionType, SectionTypeWeights]:
        """피드백에서 가중치 학습"""
        if not self.feedback_history:
            return self.section_weights

        # 섹션 타입별 정확도 계산
        type_accuracies = {}
        for section_type in SectionType:
            type_feedbacks = [
                f for f in self.feedback_history
                if f.section_type == section_type
            ]
            if type_feedbacks:
                accuracy = sum(1 for f in type_feedbacks if f.is_correct) / len(
                    type_feedbacks
                )
                type_accuracies[section_type] = accuracy

        # 정확도가 낮은 섹션 타입의 가중치 조정
        for section_type, accuracy in type_accuracies.items():
            if accuracy < 0.8:  # 80% 이하면 조정
                # hallucination 가중치 증가
                self.section_weights[section_type].hallucination_weight += 0.05
                self.section_weights[section_type].persuasiveness_weight -= 0.02
                self.section_weights[section_type].normalize()
                logger.info(
                    f"Adapted weights for {section_type.value} "
                    f"(accuracy: {accuracy:.2f})"
                )

        return self.section_weights

    def add_custom_rule(
        self,
        section_type: SectionType,
        rule_name: str,
        condition: Callable[[EvaluationScore], bool],
        adjustment: float,
        priority: int = 2
    ):
        """커스텀 규칙 추가"""
        rule = SectionRule(
            section_type=section_type,
            rule_name=rule_name,
            condition=condition,
            adjustment=adjustment,
            priority=priority
        )
        self.section_rules.append(rule)
        logger.info(f"Custom rule added: {rule_name} for {section_type.value}")

    def get_section_specific_adjustment(
        self,
        section: TestSection,
        base_score: EvaluationScore
    ) -> Dict[str, any]:
        """섹션 특화 조정 계산"""
        hallucination_adjusted, rules_applied = self.apply_section_rules(
            section, base_score
        )

        adjustment = hallucination_adjusted - base_score.hallucination

        return {
            "original_hallucination": base_score.hallucination,
            "adjusted_hallucination": hallucination_adjusted,
            "adjustment": adjustment,
            "rules_applied": rules_applied,
            "rules_count": len(rules_applied)
        }
