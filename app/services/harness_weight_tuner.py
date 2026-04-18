"""Phase 3: 알고리즘 개선 - Weight Tuning + Feedback"""

from dataclasses import dataclass
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class WeightConfig:
    """가중치 설정"""
    hallucination_weight: float = 0.35
    persuasiveness_weight: float = 0.25
    completeness_weight: float = 0.25
    clarity_weight: float = 0.15
    section_type: Optional[str] = None


class WeightTuningEngine:
    """가중치 튜닝 엔진"""

    DEFAULT_WEIGHTS = {
        "hallucination": 0.35,
        "persuasiveness": 0.25,
        "completeness": 0.25,
        "clarity": 0.15
    }

    SECTION_SPECIFIC_WEIGHTS = {
        "executive_summary": {
            "hallucination": 0.40,
            "persuasiveness": 0.30,
            "completeness": 0.20,
            "clarity": 0.10
        },
        "technical_details": {
            "hallucination": 0.40,
            "persuasiveness": 0.20,
            "completeness": 0.25,
            "clarity": 0.15
        }
    }

    async def grid_search_optimal_weights(
        self,
        train_dataset: List[Dict]
    ) -> WeightConfig:
        """Grid Search로 최적 가중치 찾기"""
        candidates = self._generate_weight_candidates()
        results = []

        for weights in candidates:
            f1_score = await self._evaluate_weights(weights, train_dataset)
            results.append({"weights": weights, "f1_score": f1_score})

        best = max(results, key=lambda r: r["f1_score"])
        return WeightConfig(
            hallucination_weight=best["weights"]["hallucination"],
            persuasiveness_weight=best["weights"]["persuasiveness"],
            completeness_weight=best["weights"]["completeness"],
            clarity_weight=best["weights"]["clarity"],
        )

    def _generate_weight_candidates(self) -> List[Dict]:
        """기본 가중치 ±5% 범위에서 조합 생성"""
        base = self.DEFAULT_WEIGHTS
        candidates = []
        adjustments = [-0.05, -0.025, 0, 0.025, 0.05]

        for hal_adj in adjustments:
            for per_adj in adjustments:
                for com_adj in adjustments:
                    for cla_adj in adjustments:
                        weights = {
                            "hallucination": base["hallucination"] + hal_adj,
                            "persuasiveness": base["persuasiveness"] + per_adj,
                            "completeness": base["completeness"] + com_adj,
                            "clarity": base["clarity"] + cla_adj
                        }
                        total = sum(weights.values())
                        weights = {k: v/total for k, v in weights.items()}
                        candidates.append(weights)

        return candidates[:100]

    async def _evaluate_weights(self, weights: Dict, dataset: List[Dict]) -> float:
        """가중치별 F1 점수 계산"""
        # Mock 구현 - 실제로는 데이터셋 평가
        return 0.90 + sum(weights.values()) * 0.01

    def integrate_user_feedback(
        self,
        feedback_list: List[Dict],
        current_weights: WeightConfig
    ) -> WeightConfig:
        """사용자 피드백 기반 가중치 조정"""
        if len(feedback_list) < 50:
            return current_weights

        false_positives = [f for f in feedback_list if f.get("user_decision") == "rejected"]
        false_negatives = [f for f in feedback_list if f.get("user_decision") == "approved"]

        adjusted = {
            "hallucination": current_weights.hallucination_weight,
            "persuasiveness": current_weights.persuasiveness_weight,
            "completeness": current_weights.completeness_weight,
            "clarity": current_weights.clarity_weight,
        }

        if len(false_positives) > len(false_negatives):
            adjusted["hallucination"] *= 0.95

        if len(false_negatives) > len(false_positives):
            adjusted["hallucination"] *= 1.05

        total = sum(adjusted.values())
        adjusted = {k: v/total for k, v in adjusted.items()}

        return WeightConfig(
            hallucination_weight=adjusted["hallucination"],
            persuasiveness_weight=adjusted["persuasiveness"],
            completeness_weight=adjusted["completeness"],
            clarity_weight=adjusted["clarity"],
        )

    def apply_section_specific_rules(
        self,
        section_type: str,
        general_weights: WeightConfig
    ) -> WeightConfig:
        """섹션별 특화 가중치 적용"""
        if section_type in self.SECTION_SPECIFIC_WEIGHTS:
            weights = self.SECTION_SPECIFIC_WEIGHTS[section_type]
            return WeightConfig(
                hallucination_weight=weights["hallucination"],
                persuasiveness_weight=weights["persuasiveness"],
                completeness_weight=weights["completeness"],
                clarity_weight=weights["clarity"],
                section_type=section_type
            )
        return general_weights
