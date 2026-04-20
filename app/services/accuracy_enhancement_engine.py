"""
STEP 4A Phase 2: Accuracy Enhancement Engine
섹션 진단 정확도 향상을 위한 3가지 개선 전략: 신뢰도 임계값, 앙상블 투표, 교차 검증
"""

import logging
import statistics
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from app.services.harness_accuracy_validator import (
    DiagnosisAccuracyValidator,
    EvaluationMetrics,
    EvaluationResult,
    PerformanceMetrics,
    MetricCalculator,
    TestCase,
)

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceResult:
    """신뢰도 계산 결과"""
    confidence: float       # 0-1: 신뢰도
    should_accept: bool     # confidence >= threshold
    std_dev: float          # 변형 점수의 표준편차
    variance: float         # 분산
    agreement_level: str    # "HIGH" | "MEDIUM" | "LOW"

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class EnsembleResult:
    """앙상블 투표 결과"""
    aggregated_metrics: EvaluationMetrics
    aggregated_score: float
    variant_weights: Dict[str, float]   # conservative/balanced/creative 가중치, 합=1.0
    outliers_removed: List[str]         # 이상치로 제거된 변형

    def to_dict(self) -> Dict:
        return {
            "aggregated_metrics": self.aggregated_metrics.to_dict(),
            "aggregated_score": self.aggregated_score,
            "variant_weights": self.variant_weights,
            "outliers_removed": self.outliers_removed
        }


@dataclass
class FoldResult:
    """k-fold 검증 결과 (한 폴드)"""
    fold_id: int
    test_case_ids: List[str]
    metrics: PerformanceMetrics

    def to_dict(self) -> Dict:
        return {
            "fold_id": self.fold_id,
            "test_case_count": len(self.test_case_ids),
            "metrics": self.metrics.to_dict()
        }


@dataclass
class CrossValidationResult:
    """k-fold 교차 검증 전체 결과"""
    k: int
    folds: List[FoldResult]
    mean_precision: float
    mean_recall: float
    mean_f1: float
    std_f1: float
    stability_score: float   # 1 - (std_f1 / mean_f1), 0-1 범위

    def to_dict(self) -> Dict:
        return {
            "k": self.k,
            "fold_count": len(self.folds),
            "mean_precision": round(self.mean_precision, 4),
            "mean_recall": round(self.mean_recall, 4),
            "mean_f1": round(self.mean_f1, 4),
            "std_f1": round(self.std_f1, 4),
            "stability_score": round(self.stability_score, 4)
        }


@dataclass
class EnhancementReport:
    """개선 보고서"""
    original_accuracy: float
    enhanced_accuracy: float
    improvement: float           # enhanced - original
    confidence_filtered_count: int
    ensemble_applied: bool
    cross_validation: Optional[CrossValidationResult]
    recommendations: List[str]

    def to_dict(self) -> Dict:
        return {
            "original_accuracy": round(self.original_accuracy, 4),
            "enhanced_accuracy": round(self.enhanced_accuracy, 4),
            "improvement": round(self.improvement, 4),
            "confidence_filtered_count": self.confidence_filtered_count,
            "ensemble_applied": self.ensemble_applied,
            "cross_validation": self.cross_validation.to_dict() if self.cross_validation else None,
            "recommendations": self.recommendations
        }


class ConfidenceThresholder:
    """신뢰도 임계값 기반 필터링"""

    def __init__(self, threshold: float = 0.65):
        """
        Args:
            threshold: 신뢰도 기준값 (0-1). 이 이상만 수용.
        """
        self.threshold = threshold

    def compute_confidence(self, variant_scores: Dict[str, float]) -> ConfidenceResult:
        """
        변형 점수 간의 차이로부터 신뢰도 계산
        
        Args:
            variant_scores: {"conservative": float, "balanced": float, "creative": float}
        
        Returns:
            ConfidenceResult: 신뢰도 및 판정
        """
        scores = list(variant_scores.values())
        
        if not scores:
            return ConfidenceResult(
                confidence=0.0,
                should_accept=False,
                std_dev=0.0,
                variance=0.0,
                agreement_level="LOW"
            )
        
        if len(scores) == 1:
            return ConfidenceResult(
                confidence=0.9,
                should_accept=True,
                std_dev=0.0,
                variance=0.0,
                agreement_level="HIGH"
            )
        
        # 표준편차 계산
        mean_score = statistics.mean(scores)
        variance = sum((x - mean_score) ** 2 for x in scores) / len(scores)
        std_dev = variance ** 0.5
        
        # 신뢰도 공식: 1 - (std_dev / max_std)
        # 점수 범위가 0-1이므로 최대 std_dev는 약 0.5 (극단값 0과 1)
        max_std = 0.5
        confidence = max(0.0, 1.0 - (std_dev / max_std))
        confidence = min(1.0, confidence)
        
        # 동의 수준 판정
        if confidence >= 0.80:
            agreement_level = "HIGH"
        elif confidence >= 0.65:
            agreement_level = "MEDIUM"
        else:
            agreement_level = "LOW"
        
        return ConfidenceResult(
            confidence=round(confidence, 3),
            should_accept=confidence >= self.threshold,
            std_dev=round(std_dev, 3),
            variance=round(variance, 3),
            agreement_level=agreement_level
        )

    def filter_low_confidence(
        self,
        results: List[EvaluationResult],
        threshold: Optional[float] = None
    ) -> List[EvaluationResult]:
        """
        신뢰도가 낮은 평가 결과 제거
        
        Args:
            results: 평가 결과 리스트
            threshold: 사용할 임계값 (None이면 self.threshold 사용)
        
        Returns:
            필터링된 결과 리스트
        """
        thresh = threshold if threshold is not None else self.threshold
        # 주어진 EvaluationResult에는 confidence 필드가 있음
        return [r for r in results if r.confidence >= thresh]


class EnsembleVoter:
    """앙상블 투표: 3개 변형의 가중 평균"""

    def __init__(self):
        self.thresholder = ConfidenceThresholder()

    def vote(
        self,
        variant_scores: Dict[str, float],
        variant_details: Dict[str, EvaluationMetrics]
    ) -> EnsembleResult:
        """
        3개 변형의 메트릭을 가중 평균으로 통합
        
        Args:
            variant_scores: {"conservative": float, "balanced": float, "creative": float}
            variant_details: {"conservative": EvaluationMetrics, ...}
        
        Returns:
            EnsembleResult: 통합된 메트릭 및 점수
        """
        variant_names = ["conservative", "balanced", "creative"]
        scores = [variant_scores.get(name, 0.5) for name in variant_names]
        
        # 각 변형의 신뢰도 계산 (3개 variant 모두를 함께 고려하여 신뢰도 계산)
        conf_result = self.thresholder.compute_confidence(variant_scores)
        base_confidence = conf_result.confidence

        # 이상치 가중치 조정을 위한 개별 신뢰도 계산
        confidences = {}
        for name in variant_names:
            # 기본 신뢰도에서 개별 점수의 편차를 반영
            score_diff = abs(variant_scores.get(name, 0.5) - statistics.mean(scores))
            variant_confidence = max(0.3, base_confidence - (score_diff * 0.5))
            confidences[name] = variant_confidence
        
        # 이상치 감지: Z-score > 1.5
        mean_score = statistics.mean(scores)
        std_dev = (sum((x - mean_score) ** 2 for x in scores) / len(scores)) ** 0.5
        
        outliers = []
        base_weights = {}
        
        for i, name in enumerate(variant_names):
            if std_dev > 0:
                z_score = abs(scores[i] - mean_score) / std_dev
            else:
                z_score = 0.0
            
            if z_score > 1.5:
                outliers.append(name)
                base_weights[name] = 0.0
            else:
                # 신뢰도 기반 가중치
                base_weights[name] = confidences[name]
        
        # 가중치 정규화 (합=1.0)
        total_weight = sum(base_weights.values())
        if total_weight > 0:
            variant_weights = {k: v / total_weight for k, v in base_weights.items()}
        else:
            variant_weights = {name: 1.0 / len(variant_names) for name in variant_names}
        
        # 메트릭별 가중 평균
        agg_hallucination = sum(
            variant_details.get(name, EvaluationMetrics(0, 0, 0, 0)).hallucination * variant_weights.get(name, 0)
            for name in variant_names
        )
        agg_persuasiveness = sum(
            variant_details.get(name, EvaluationMetrics(0, 0, 0, 0)).persuasiveness * variant_weights.get(name, 0)
            for name in variant_names
        )
        agg_completeness = sum(
            variant_details.get(name, EvaluationMetrics(0, 0, 0, 0)).completeness * variant_weights.get(name, 0)
            for name in variant_names
        )
        agg_clarity = sum(
            variant_details.get(name, EvaluationMetrics(0, 0, 0, 0)).clarity * variant_weights.get(name, 0)
            for name in variant_names
        )
        
        aggregated_metrics = EvaluationMetrics(
            hallucination=round(agg_hallucination, 3),
            persuasiveness=round(agg_persuasiveness, 3),
            completeness=round(agg_completeness, 3),
            clarity=round(agg_clarity, 3)
        )
        
        # 통합 점수 계산 (harness_evaluator의 가중치와 동일)
        aggregated_score = (
            (1 - aggregated_metrics.hallucination) * 0.35 +
            aggregated_metrics.persuasiveness * 0.25 +
            aggregated_metrics.completeness * 0.25 +
            aggregated_metrics.clarity * 0.15
        )
        aggregated_score = round(aggregated_score, 3)
        
        return EnsembleResult(
            aggregated_metrics=aggregated_metrics,
            aggregated_score=aggregated_score,
            variant_weights=variant_weights,
            outliers_removed=outliers
        )


class CrossValidator:
    """k-fold 교차 검증"""

    def __init__(self, k: int = 5):
        """
        Args:
            k: fold 개수
        """
        self.k = k

    def validate(
        self,
        validator: DiagnosisAccuracyValidator,
        predicted_results: List[EvaluationResult]
    ) -> CrossValidationResult:
        """
        k-fold 교차 검증 수행
        
        Args:
            validator: DiagnosisAccuracyValidator 인스턴스
            predicted_results: 예측 결과 리스트
        
        Returns:
            CrossValidationResult: k-fold 결과 및 통계
        """
        if not predicted_results:
            logger.warning("No results to validate")
            return CrossValidationResult(
                k=self.k,
                folds=[],
                mean_precision=0.0,
                mean_recall=0.0,
                mean_f1=0.0,
                std_f1=0.0,
                stability_score=0.0
            )
        
        # 폴드 분할
        fold_size = len(predicted_results) // self.k
        folds = []
        
        for fold_id in range(self.k):
            start_idx = fold_id * fold_size
            if fold_id == self.k - 1:
                # 마지막 폴드는 나머지 모두 포함
                end_idx = len(predicted_results)
            else:
                end_idx = start_idx + fold_size
            
            fold_results = predicted_results[start_idx:end_idx]
            fold_test_case_ids = [r.test_case_id for r in fold_results]
            
            # 폴드별 메트릭 계산
            fold_metrics = MetricCalculator.calculate_metrics(fold_results)
            
            folds.append(FoldResult(
                fold_id=fold_id,
                test_case_ids=fold_test_case_ids,
                metrics=fold_metrics
            ))
        
        # 폴드별 메트릭 수집
        precisions = [f.metrics.precision for f in folds if f.metrics.precision > 0]
        recalls = [f.metrics.recall for f in folds if f.metrics.recall > 0]
        f1_scores = [f.metrics.f1_score for f in folds if f.metrics.f1_score > 0]
        
        mean_precision = statistics.mean(precisions) if precisions else 0.0
        mean_recall = statistics.mean(recalls) if recalls else 0.0
        mean_f1 = statistics.mean(f1_scores) if f1_scores else 0.0
        std_f1 = statistics.stdev(f1_scores) if len(f1_scores) > 1 else 0.0
        
        # 안정성 점수: 1 - (std / mean), clamped to 0-1
        if mean_f1 > 0:
            stability_score = max(0.0, 1.0 - (std_f1 / mean_f1))
        else:
            stability_score = 0.0
        stability_score = min(1.0, stability_score)
        
        return CrossValidationResult(
            k=self.k,
            folds=folds,
            mean_precision=round(mean_precision, 4),
            mean_recall=round(mean_recall, 4),
            mean_f1=round(mean_f1, 4),
            std_f1=round(std_f1, 4),
            stability_score=round(stability_score, 4)
        )


class AccuracyEnhancementEngine:
    """정확도 향상 엔진: 세 가지 개선 전략 통합"""

    def __init__(self, confidence_threshold: float = 0.65, k_folds: int = 5):
        """
        Args:
            confidence_threshold: 신뢰도 임계값
            k_folds: 교차 검증 폴드 수
        """
        self.thresholder = ConfidenceThresholder(confidence_threshold)
        self.voter = EnsembleVoter()
        self.cross_validator = CrossValidator(k_folds)

    def enhance(
        self,
        validator: DiagnosisAccuracyValidator,
        raw_results: List[EvaluationResult],
        variant_data: Optional[List[Dict]] = None
    ) -> EnhancementReport:
        """
        세 가지 개선 전략을 순차적으로 적용
        
        Args:
            validator: DiagnosisAccuracyValidator 인스턴스
            raw_results: 원본 평가 결과
            variant_data: 변형 데이터 (variant_scores + variant_details)
        
        Returns:
            EnhancementReport: 개선 결과 및 보고
        """
        # Step 1: 원본 정확도 계산
        original_metrics = MetricCalculator.calculate_metrics(raw_results)
        original_accuracy = original_metrics.accuracy
        
        # Step 2: 신뢰도 필터링
        filtered_results = self.thresholder.filter_low_confidence(raw_results)
        confidence_filtered_count = len(raw_results) - len(filtered_results)
        
        if not filtered_results:
            filtered_results = raw_results  # fallback: 모두 사용
        
        # Step 3: 앙상블 투표 (variant_data 제공 시)
        ensemble_applied = False
        if variant_data is not None and len(variant_data) > 0:
            # TODO: Phase 3에서 구현 - 현재는 신뢰도 필터링만 적용
            # Phase 3에서 다음 로직 추가 예정:
            # 1. self.voter.vote()로 각 variant의 가중 평균 계산
            # 2. 앙상블 투표 결과를 filtered_results에 반영
            # 3. 최종 정확도 재계산
            logger.debug(f"Ensemble voting placeholder: {len(variant_data)} variants prepared for Phase 3 integration")
        
        # Step 4: 개선된 정확도 계산
        enhanced_metrics = MetricCalculator.calculate_metrics(filtered_results)
        enhanced_accuracy = enhanced_metrics.accuracy
        improvement = enhanced_accuracy - original_accuracy
        
        # Step 5: 교차 검증
        cross_val_result = self.cross_validator.validate(validator, filtered_results)
        
        # Step 6: 추천 생성
        recommendations = self._generate_recommendations(
            original_accuracy, enhanced_accuracy, cross_val_result, confidence_filtered_count
        )
        
        logger.info(
            f"Enhancement complete: "
            f"Accuracy {original_accuracy:.3f} → {enhanced_accuracy:.3f} ({improvement:+.3f}), "
            f"Filtered {confidence_filtered_count} low-confidence results"
        )
        
        return EnhancementReport(
            original_accuracy=original_accuracy,
            enhanced_accuracy=enhanced_accuracy,
            improvement=improvement,
            confidence_filtered_count=confidence_filtered_count,
            ensemble_applied=ensemble_applied,
            cross_validation=cross_val_result,
            recommendations=recommendations
        )

    def simulate_enhancement(
        self,
        validator: DiagnosisAccuracyValidator
    ) -> EnhancementReport:
        """
        오프라인 시뮬레이션: 라이브 harness 없이 데이터셋만으로 개선 효과 측정

        Args:
            validator: DiagnosisAccuracyValidator 인스턴스 (데이터셋 포함)

        Returns:
            EnhancementReport: 개선 효과
        """
        # 50개 섹션에 대해 모두 evaluate
        # Try different methods to get all test cases
        all_test_cases = None
        if hasattr(validator.dataset_manager, 'get_all_test_cases'):
            all_test_cases = validator.dataset_manager.get_all_test_cases()
        elif hasattr(validator.dataset_manager, 'test_cases'):
            all_test_cases = validator.dataset_manager.test_cases
        else:
            # Fallback: try to get from data attribute if available
            try:
                all_test_cases = getattr(validator.dataset_manager, 'data', [])
            except Exception as e:
                logger.exception("Failed to fetch test cases from fallback attribute")
                all_test_cases = []

        if not all_test_cases:
            logger.warning("No test cases to simulate")
            return EnhancementReport(
                original_accuracy=0.0,
                enhanced_accuracy=0.0,
                improvement=0.0,
                confidence_filtered_count=0,
                ensemble_applied=False,
                cross_validation=None,
                recommendations=["No test cases available for simulation"]
            )
        
        # 모든 섹션 평가 (Ground Truth = Predicted)
        results = []
        for tc in all_test_cases:
            result = validator.evaluate_section(
                test_case_id=tc.id,
                predicted_metrics=tc.ground_truth,  # Simulated: perfect predictions
                predicted_score=tc.expected_score,
                confidence=0.95  # High confidence for perfect match
            )
            if result:
                results.append(result)
        
        # 개선 수행
        return self.enhance(validator, results, variant_data=None)

    def _generate_recommendations(
        self,
        original_accuracy: float,
        enhanced_accuracy: float,
        cross_val_result: Optional[CrossValidationResult],
        filtered_count: int
    ) -> List[str]:
        """추천 생성"""
        recommendations = []

        if enhanced_accuracy < 0.80:
            recommendations.append("Low accuracy (<0.80) - consider confidence threshold adjustment (try 0.60)")

        if enhanced_accuracy >= 0.80 and enhanced_accuracy < 0.90:
            recommendations.append("Good progress - continue with ensemble voting strategy")

        if cross_val_result and cross_val_result.stability_score < 0.80:
            recommendations.append(f"Stability score low ({cross_val_result.stability_score:.3f}) - check k-fold variance")

        # Check if filter rate is too high
        if cross_val_result and cross_val_result.folds and len(cross_val_result.folds) > 0:
            first_fold_size = len(cross_val_result.folds[0].test_case_ids)
            if filtered_count > first_fold_size * 0.5:
                recommendations.append(f"High filter rate ({filtered_count}) - consider threshold relaxation")

        if not recommendations:
            recommendations.append(f"Accuracy improved from {original_accuracy:.3f} to {enhanced_accuracy:.3f}")

        return recommendations
