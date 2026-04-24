"""
STEP 4A Phase 1: Harness Accuracy Validator
섹션 진단 정확도 향상을 위한 베이스라인 계산 및 검증 엔진
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from typing import Optional, List, Dict, Tuple
from pathlib import Path
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AccuracyMetric(str, Enum):
    """정확도 지표 타입"""
    HALLUCINATION = "hallucination"  # 0-1: 낮을수록 좋음 (환각 최소화)
    PERSUASIVENESS = "persuasiveness"  # 0-1: 높을수록 좋음 (설득력 강함)
    COMPLETENESS = "completeness"  # 0-1: 높을수록 좋음 (내용 완전함)
    CLARITY = "clarity"  # 0-1: 높을수록 좋음 (표현 명확함)


@dataclass
class EvaluationMetrics:
    """섹션별 평가 지표 (Ground Truth)"""
    hallucination: float  # 0-1: 환각 비율 (0이 최고)
    persuasiveness: float  # 0-1: 설득력 (1이 최고)
    completeness: float  # 0-1: 내용 완결성 (1이 최고)
    clarity: float  # 0-1: 표현 명확도 (1이 최고)

    def to_dict(self) -> Dict[str, float]:
        return asdict(self)

    @staticmethod
    def from_dict(data: Dict[str, float]) -> "EvaluationMetrics":
        return EvaluationMetrics(
            hallucination=data.get("hallucination", 0.0),
            persuasiveness=data.get("persuasiveness", 0.5),
            completeness=data.get("completeness", 0.5),
            clarity=data.get("clarity", 0.5)
        )


@dataclass
class GroundTruthLabel:
    """섹션 평가 라벨: 인간이 부여한 Gold Standard"""
    section_id: str
    hallucination_severity: str  # "none", "minor", "major"
    persuasiveness_level: int  # 1-5: Likert scale
    completeness_score: int  # 0-100: 백분율
    clarity_rating: int  # 1-5: Likert scale

    def to_metrics(self) -> EvaluationMetrics:
        """라벨을 EvaluationMetrics로 변환"""
        hallucination_map = {"none": 0.0, "minor": 0.3, "major": 0.7}
        return EvaluationMetrics(
            hallucination=hallucination_map.get(self.hallucination_severity, 0.0),
            persuasiveness=self.persuasiveness_level / 5.0,
            completeness=self.completeness_score / 100.0,
            clarity=self.clarity_rating / 5.0
        )


@dataclass
class TestSection:
    """테스트용 섹션: 평가 대상"""
    section_id: str
    title: str
    content: str
    section_type: str  # "executive_summary", "technical_details", etc.
    ground_truth: GroundTruthLabel  # 인간이 부여한 라벨


@dataclass
class TestCase:
    """테스트 케이스: 섹션 평가 데이터"""
    id: str  # e.g., "sec_001"
    section_type: str  # e.g., "executive_summary", "technical_approach"
    content: str  # 섹션 본문
    ground_truth: EvaluationMetrics  # 인간이 평가한 Gold Standard
    expected_score: float  # 0-1: 예상 종합 점수 (4개 지표 평균)

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "section_type": self.section_type,
            "content": self.content,
            "ground_truth": self.ground_truth.to_dict(),
            "expected_score": self.expected_score
        }

    @staticmethod
    def from_dict(data: Dict) -> "TestCase":
        return TestCase(
            id=data["id"],
            section_type=data["section_type"],
            content=data["content"],
            ground_truth=EvaluationMetrics.from_dict(data["ground_truth"]),
            expected_score=data["expected_score"]
        )


@dataclass
class EvaluationResult:
    """평가 결과: 예측 vs Ground Truth 비교"""
    test_case_id: str
    predicted_metrics: EvaluationMetrics
    predicted_score: float  # 0-1: 예측 종합 점수
    confidence: float  # 0-1: 예측 신뢰도
    ground_truth: EvaluationMetrics
    expected_score: float
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "test_case_id": self.test_case_id,
            "predicted_metrics": self.predicted_metrics.to_dict(),
            "predicted_score": self.predicted_score,
            "confidence": self.confidence,
            "ground_truth": self.ground_truth.to_dict(),
            "expected_score": self.expected_score,
            "timestamp": self.timestamp
        }


@dataclass
class PerformanceMetrics:
    """전체 성능 지표 (정확도, 재현율, F1 등)"""
    precision: float = 0.0  # TP / (TP + FP)
    recall: float = 0.0  # TP / (TP + FN)
    f1_score: float = 0.0  # 2 * (precision * recall) / (precision + recall)
    accuracy: float = 0.0  # (TP + TN) / (TP + FP + TN + FN)
    
    # 혼동 행렬
    true_positives: int = 0  # 올바르게 예측 (점수 >= threshold)
    true_negatives: int = 0  # 올바르게 거부 (점수 < threshold)
    false_positives: int = 0  # 잘못 수용 (예측 > 실제)
    false_negatives: int = 0  # 잘못 거부 (예측 < 실제)
    
    # 지표별 상세 오차
    false_negative_rate: float = 0.0  # FN / (FN + TP)
    false_positive_rate: float = 0.0  # FP / (FP + TN)
    
    # 성능
    avg_latency_ms: float = 0.0  # 평균 평가 시간
    median_confidence: float = 0.0  # 신뢰도 중앙값
    
    # 지표별 오차
    hallucination_mae: float = 0.0  # Mean Absolute Error
    persuasiveness_mae: float = 0.0
    completeness_mae: float = 0.0
    clarity_mae: float = 0.0

    def to_dict(self) -> Dict:
        return asdict(self)


class MetricCalculator:
    """Precision, Recall, F1 등 성능 지표 계산"""

    @staticmethod
    def calculate_metrics(
        results: List[EvaluationResult],
        score_threshold: float = 0.5
    ) -> PerformanceMetrics:
        """
        평가 결과로부터 성능 지표 계산
        
        Args:
            results: EvaluationResult 리스트
            score_threshold: 긍정/부정 판정 기준 (0-1)
        
        Returns:
            PerformanceMetrics: 정확도, 재현율, F1 등 종합 지표
        """
        if not results:
            return PerformanceMetrics()

        tp = fp = tn = fn = 0
        latencies = []
        confidences = []
        
        # 지표별 오차 누적
        hallucination_errors = []
        persuasiveness_errors = []
        completeness_errors = []
        clarity_errors = []

        for result in results:
            # 예측 vs 기대값 비교 (이진 분류: 통과/실패)
            pred_pass = result.predicted_score >= score_threshold
            expected_pass = result.expected_score >= score_threshold

            if pred_pass and expected_pass:
                tp += 1
            elif pred_pass and not expected_pass:
                fp += 1
            elif not pred_pass and expected_pass:
                fn += 1
            else:
                tn += 1

            # 신뢰도, 레이턴시 기록
            confidences.append(result.confidence)

            # 지표별 오차 (MAE)
            hallucination_errors.append(
                abs(result.predicted_metrics.hallucination - result.ground_truth.hallucination)
            )
            persuasiveness_errors.append(
                abs(result.predicted_metrics.persuasiveness - result.ground_truth.persuasiveness)
            )
            completeness_errors.append(
                abs(result.predicted_metrics.completeness - result.ground_truth.completeness)
            )
            clarity_errors.append(
                abs(result.predicted_metrics.clarity - result.ground_truth.clarity)
            )

        # Precision, Recall, F1 계산
        total = tp + fp + tn + fn
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
        accuracy = (tp + tn) / total if total > 0 else 0.0
        
        # 오류율
        false_negative_rate = fn / (fn + tp) if (fn + tp) > 0 else 0.0
        false_positive_rate = fp / (fp + tn) if (fp + tn) > 0 else 0.0

        # 신뢰도 중앙값
        median_confidence = sorted(confidences)[len(confidences) // 2] if confidences else 0.0

        # 지표별 MAE 계산
        hallucination_mae = sum(hallucination_errors) / len(hallucination_errors) if hallucination_errors else 0.0
        persuasiveness_mae = sum(persuasiveness_errors) / len(persuasiveness_errors) if persuasiveness_errors else 0.0
        completeness_mae = sum(completeness_errors) / len(completeness_errors) if completeness_errors else 0.0
        clarity_mae = sum(clarity_errors) / len(clarity_errors) if clarity_errors else 0.0

        return PerformanceMetrics(
            precision=precision,
            recall=recall,
            f1_score=f1,
            accuracy=accuracy,
            true_positives=tp,
            true_negatives=tn,
            false_positives=fp,
            false_negatives=fn,
            false_negative_rate=false_negative_rate,
            false_positive_rate=false_positive_rate,
            avg_latency_ms=0.0,  # 별도 계산 필요
            median_confidence=median_confidence,
            hallucination_mae=hallucination_mae,
            persuasiveness_mae=persuasiveness_mae,
            completeness_mae=completeness_mae,
            clarity_mae=clarity_mae
        )


class DatasetManager:
    """테스트 데이터셋 로드/저장"""

    def __init__(self, dataset_path: str = "data/test_datasets/harness_test_50_sections.json"):
        self.dataset_path = Path(dataset_path)
        self.dataset_path.parent.mkdir(parents=True, exist_ok=True)
        self.test_cases: Dict[str, TestCase] = {}
        self._load_or_init()

    def _load_or_init(self):
        """기존 데이터셋 로드 또는 초기화"""
        if self.dataset_path.exists():
            try:
                with open(self.dataset_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.test_cases = {
                        tc_id: TestCase.from_dict(tc_data)
                        for tc_id, tc_data in data.get("test_cases", {}).items()
                    }
                logger.info(f"Loaded {len(self.test_cases)} test cases from {self.dataset_path}")
            except Exception as e:
                logger.error(f"Failed to load dataset: {e}")
                self.test_cases = {}
        else:
            logger.info(f"Dataset not found at {self.dataset_path}, initializing empty")
            self.test_cases = {}

    def save_dataset(self):
        """데이터셋을 JSON 파일로 저장"""
        data = {
            "metadata": {
                "created": datetime.now().isoformat(),
                "total_test_cases": len(self.test_cases)
            },
            "test_cases": {
                tc_id: tc.to_dict()
                for tc_id, tc in self.test_cases.items()
            }
        }
        try:
            with open(self.dataset_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Saved {len(self.test_cases)} test cases to {self.dataset_path}")
        except Exception as e:
            logger.error(f"Failed to save dataset: {e}")

    def add_test_case(self, test_case: TestCase) -> None:
        """테스트 케이스 추가"""
        self.test_cases[test_case.id] = test_case

    def get_test_case(self, tc_id: str) -> Optional[TestCase]:
        """ID로 테스트 케이스 조회"""
        return self.test_cases.get(tc_id)

    def get_all_test_cases(self) -> List[TestCase]:
        """모든 테스트 케이스 반환"""
        return list(self.test_cases.values())

    def get_test_cases_by_type(self, section_type: str) -> List[TestCase]:
        """섹션 타입별 테스트 케이스 조회"""
        return [tc for tc in self.test_cases.values() if tc.section_type == section_type]

    def get_statistics(self) -> Dict:
        """데이터셋 통계"""
        if not self.test_cases:
            return {
                "total_cases": 0,
                "by_type": {},
                "score_distribution": {}
            }

        by_type = {}
        scores = []
        
        for tc in self.test_cases.values():
            section_type = tc.section_type
            if section_type not in by_type:
                by_type[section_type] = 0
            by_type[section_type] += 1
            scores.append(tc.expected_score)

        return {
            "total_cases": len(self.test_cases),
            "by_type": by_type,
            "avg_expected_score": sum(scores) / len(scores) if scores else 0.0,
            "min_expected_score": min(scores) if scores else 0.0,
            "max_expected_score": max(scores) if scores else 0.0
        }


class DiagnosisAccuracyValidator:
    """STEP 4A 진단 정확도 검증 엔진"""

    def __init__(self, dataset_path: str = "data/test_datasets/harness_test_50_sections.json"):
        self.dataset_manager = DatasetManager(dataset_path)
        self.evaluation_results: List[EvaluationResult] = []
        self.baseline_metrics: Optional[PerformanceMetrics] = None

    def evaluate_section(
        self,
        test_case_id: str,
        predicted_metrics: EvaluationMetrics,
        predicted_score: float,
        confidence: float = 0.8
    ) -> Optional[EvaluationResult]:
        """
        단일 섹션 평가 (실제 vs 예측)
        
        Args:
            test_case_id: 테스트 케이스 ID
            predicted_metrics: 모델이 예측한 메트릭
            predicted_score: 모델이 예측한 종합 점수
            confidence: 신뢰도 (0-1)
        
        Returns:
            EvaluationResult: 평가 결과 (비교 데이터 포함)
        """
        test_case = self.dataset_manager.get_test_case(test_case_id)
        if not test_case:
            logger.warning(f"Test case {test_case_id} not found")
            return None

        result = EvaluationResult(
            test_case_id=test_case_id,
            predicted_metrics=predicted_metrics,
            predicted_score=predicted_score,
            confidence=confidence,
            ground_truth=test_case.ground_truth,
            expected_score=test_case.expected_score
        )
        
        self.evaluation_results.append(result)
        return result

    def calculate_baseline(self) -> PerformanceMetrics:
        """
        현재 평가 결과로부터 베이스라인 메트릭 계산
        (모든 평가를 기반으로 Precision, Recall, F1, Accuracy 등 산출)
        """
        if not self.evaluation_results:
            logger.warning("No evaluation results to calculate baseline")
            return PerformanceMetrics()

        self.baseline_metrics = MetricCalculator.calculate_metrics(
            self.evaluation_results,
            score_threshold=0.5
        )
        
        logger.info(
            f"Baseline calculated: "
            f"Accuracy={self.baseline_metrics.accuracy:.3f}, "
            f"F1={self.baseline_metrics.f1_score:.3f}, "
            f"Precision={self.baseline_metrics.precision:.3f}, "
            f"Recall={self.baseline_metrics.recall:.3f}"
        )
        
        return self.baseline_metrics

    def get_report(self) -> Dict:
        """
        진단 정확도 보고서 생성
        
        Returns:
            Dict: 평가 결과, 성능 지표, 권장사항 포함
        """
        if not self.baseline_metrics:
            self.calculate_baseline()

        return {
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_evaluations": len(self.evaluation_results),
                "dataset_stats": self.dataset_manager.get_statistics()
            },
            "performance_metrics": self.baseline_metrics.to_dict() if self.baseline_metrics else {},
            "status": self._get_status(),
            "evaluation_results": [r.to_dict() for r in self.evaluation_results[:10]]  # 처음 10개
        }

    def _get_status(self) -> Dict[str, str]:
        """현재 상태 판정"""
        if not self.baseline_metrics:
            return {"overall": "NOT_EVALUATED"}

        f1 = self.baseline_metrics.f1_score
        
        if f1 >= 0.90:
            status = "EXCELLENT"
        elif f1 >= 0.80:
            status = "GOOD"
        elif f1 >= 0.70:
            status = "ACCEPTABLE"
        else:
            status = "NEEDS_IMPROVEMENT"

        return {
            "overall": status,
            "f1_threshold": f1,
            "target": "0.97 (97%)"
        }

    def clear_results(self):
        """평가 결과 초기화"""
        self.evaluation_results = []
        self.baseline_metrics = None
