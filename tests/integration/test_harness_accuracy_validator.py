"""
STEP 4A Phase 1: Harness Accuracy Validator Integration Tests
12개 통합 테스트로 검증 엔진 동작 확인
"""

import pytest
import json
from pathlib import Path
from app.services.domains.proposal.harness_accuracy_validator import (
    DiagnosisAccuracyValidator,
    DatasetManager,
    EvaluationMetrics,
    TestCase,
    EvaluationResult,
    MetricCalculator,
    PerformanceMetrics,
)


class TestDatasetManager:
    """DatasetManager 테스트"""

    @pytest.fixture
    def dataset_path(self, tmp_path):
        """임시 데이터셋 경로"""
        return str(tmp_path / "test_dataset.json")

    @pytest.fixture
    def manager(self, dataset_path):
        """DatasetManager 인스턴스"""
        return DatasetManager(dataset_path)

    def test_dataset_manager_initialization(self, manager, dataset_path):
        """DatasetManager 초기화 확인"""
        assert manager.dataset_path == Path(dataset_path)
        assert isinstance(manager.test_cases, dict)

    def test_add_and_retrieve_test_case(self, manager):
        """테스트 케이스 추가 및 조회"""
        test_case = TestCase(
            id="test_001",
            section_type="executive_summary",
            content="Test content",
            ground_truth=EvaluationMetrics(0.1, 0.8, 0.8, 0.85),
            expected_score=0.8125
        )
        
        manager.add_test_case(test_case)
        retrieved = manager.get_test_case("test_001")
        
        assert retrieved is not None
        assert retrieved.id == "test_001"
        assert retrieved.section_type == "executive_summary"

    def test_get_test_cases_by_type(self, manager):
        """섹션 타입별 테스트 케이스 조회"""
        manager.add_test_case(TestCase(
            id="sec_001", section_type="executive_summary",
            content="Content 1",
            ground_truth=EvaluationMetrics(0.1, 0.8, 0.8, 0.85),
            expected_score=0.8125
        ))
        manager.add_test_case(TestCase(
            id="sec_002", section_type="technical_approach",
            content="Content 2",
            ground_truth=EvaluationMetrics(0.05, 0.9, 0.9, 0.92),
            expected_score=0.8925
        ))
        manager.add_test_case(TestCase(
            id="sec_003", section_type="executive_summary",
            content="Content 3",
            ground_truth=EvaluationMetrics(0.15, 0.7, 0.7, 0.75),
            expected_score=0.7
        ))
        
        exec_summary_cases = manager.get_test_cases_by_type("executive_summary")
        tech_cases = manager.get_test_cases_by_type("technical_approach")
        
        assert len(exec_summary_cases) == 2
        assert len(tech_cases) == 1

    def test_save_and_load_dataset(self, manager, dataset_path):
        """데이터셋 저장 및 로드"""
        manager.add_test_case(TestCase(
            id="sec_001", section_type="executive_summary",
            content="Content",
            ground_truth=EvaluationMetrics(0.1, 0.8, 0.8, 0.85),
            expected_score=0.8125
        ))
        
        manager.save_dataset()
        assert Path(dataset_path).exists()
        
        # 새 매니저로 로드
        new_manager = DatasetManager(dataset_path)
        loaded_case = new_manager.get_test_case("sec_001")
        
        assert loaded_case is not None
        assert loaded_case.content == "Content"

    def test_get_statistics(self, manager):
        """데이터셋 통계"""
        manager.add_test_case(TestCase(
            id="sec_001", section_type="executive_summary",
            content="Content 1",
            ground_truth=EvaluationMetrics(0.1, 0.8, 0.8, 0.85),
            expected_score=0.8
        ))
        manager.add_test_case(TestCase(
            id="sec_002", section_type="executive_summary",
            content="Content 2",
            ground_truth=EvaluationMetrics(0.05, 0.9, 0.9, 0.92),
            expected_score=0.9
        ))
        manager.add_test_case(TestCase(
            id="sec_003", section_type="technical_approach",
            content="Content 3",
            ground_truth=EvaluationMetrics(0.15, 0.7, 0.7, 0.75),
            expected_score=0.7
        ))
        
        stats = manager.get_statistics()
        
        assert stats["total_cases"] == 3
        assert stats["by_type"]["executive_summary"] == 2
        assert stats["by_type"]["technical_approach"] == 1
        assert stats["avg_expected_score"] == pytest.approx(0.8, abs=0.01)


class TestMetricCalculator:
    """MetricCalculator 테스트"""

    def test_calculate_metrics_basic(self):
        """기본 메트릭 계산"""
        # 테스트 데이터 생성: 10개 결과, 7개 TP, 2개 FP, 1개 FN
        results = []
        
        # TP: 7개 (예측 >= 0.5, 예상 >= 0.5)
        for i in range(7):
            results.append(EvaluationResult(
                test_case_id=f"tc_{i}",
                predicted_metrics=EvaluationMetrics(0.05, 0.85, 0.85, 0.90),
                predicted_score=0.85,
                confidence=0.95,
                ground_truth=EvaluationMetrics(0.05, 0.85, 0.85, 0.90),
                expected_score=0.85
            ))
        
        # FP: 2개 (예측 >= 0.5, 예상 < 0.5)
        for i in range(2):
            results.append(EvaluationResult(
                test_case_id=f"tc_{7+i}",
                predicted_metrics=EvaluationMetrics(0.30, 0.60, 0.55, 0.65),
                predicted_score=0.60,
                confidence=0.70,
                ground_truth=EvaluationMetrics(0.40, 0.55, 0.50, 0.60),
                expected_score=0.40
            ))
        
        # FN: 1개 (예측 < 0.5, 예상 >= 0.5)
        results.append(EvaluationResult(
            test_case_id="tc_9",
            predicted_metrics=EvaluationMetrics(0.25, 0.65, 0.65, 0.70),
            predicted_score=0.43,  # < 0.5
            confidence=0.65,
            ground_truth=EvaluationMetrics(0.05, 0.82, 0.82, 0.88),
            expected_score=0.82  # >= 0.5
        ))
        
        metrics = MetricCalculator.calculate_metrics(results, score_threshold=0.5)
        
        # 검증: TP=7, FP=2, FN=1, TN=0
        assert metrics.true_positives == 7
        assert metrics.false_positives == 2
        assert metrics.false_negatives == 1
        assert metrics.true_negatives == 0
        
        # Precision = TP / (TP + FP) = 7 / 9 = 0.777...
        assert metrics.precision == pytest.approx(7/9, abs=0.01)
        
        # Recall = TP / (TP + FN) = 7 / 8 = 0.875
        assert metrics.recall == pytest.approx(7/8, abs=0.01)

    def test_calculate_metrics_perfect_predictions(self):
        """완벽한 예측 (모두 TP)"""
        results = []
        for i in range(5):
            results.append(EvaluationResult(
                test_case_id=f"tc_{i}",
                predicted_metrics=EvaluationMetrics(0.05, 0.85, 0.85, 0.90),
                predicted_score=0.85,
                confidence=0.99,
                ground_truth=EvaluationMetrics(0.05, 0.85, 0.85, 0.90),
                expected_score=0.85
            ))
        
        metrics = MetricCalculator.calculate_metrics(results, score_threshold=0.5)
        
        assert metrics.precision == 1.0
        assert metrics.recall == 1.0
        assert metrics.f1_score == 1.0
        assert metrics.accuracy == 1.0

    def test_calculate_metrics_median_confidence(self):
        """신뢰도 중앙값 계산"""
        results = []
        confidences = [0.6, 0.7, 0.8, 0.85, 0.9]
        
        for i, conf in enumerate(confidences):
            results.append(EvaluationResult(
                test_case_id=f"tc_{i}",
                predicted_metrics=EvaluationMetrics(0.1, 0.8, 0.8, 0.85),
                predicted_score=0.8,
                confidence=conf,
                ground_truth=EvaluationMetrics(0.1, 0.8, 0.8, 0.85),
                expected_score=0.8
            ))
        
        metrics = MetricCalculator.calculate_metrics(results)
        
        # 중앙값 = 0.8 (정렬했을 때 가운데값)
        assert metrics.median_confidence == 0.8

    def test_calculate_metrics_mae_computation(self):
        """Mean Absolute Error 계산"""
        results = []
        
        # hallucination 오차: |0.10 - 0.05| = 0.05
        results.append(EvaluationResult(
            test_case_id="tc_0",
            predicted_metrics=EvaluationMetrics(0.10, 0.8, 0.8, 0.85),
            predicted_score=0.78,
            confidence=0.85,
            ground_truth=EvaluationMetrics(0.05, 0.8, 0.8, 0.85),
            expected_score=0.8
        ))
        
        # hallucination 오차: |0.15 - 0.10| = 0.05
        results.append(EvaluationResult(
            test_case_id="tc_1",
            predicted_metrics=EvaluationMetrics(0.15, 0.85, 0.85, 0.88),
            predicted_score=0.83,
            confidence=0.90,
            ground_truth=EvaluationMetrics(0.10, 0.85, 0.85, 0.88),
            expected_score=0.84
        ))
        
        metrics = MetricCalculator.calculate_metrics(results)
        
        # hallucination MAE = (0.05 + 0.05) / 2 = 0.05
        assert metrics.hallucination_mae == pytest.approx(0.05, abs=0.001)


class TestDiagnosisAccuracyValidator:
    """DiagnosisAccuracyValidator 테스트"""

    @pytest.fixture
    def validator(self, tmp_path):
        """검증 엔진 인스턴스"""
        dataset_path = str(tmp_path / "test_dataset.json")
        return DiagnosisAccuracyValidator(dataset_path)

    def test_validator_initialization(self, validator):
        """검증 엔진 초기화"""
        assert validator.evaluation_results == []
        assert validator.baseline_metrics is None

    def test_evaluate_section(self, validator):
        """섹션 평가"""
        # 테스트 케이스 추가
        test_case = TestCase(
            id="sec_001",
            section_type="executive_summary",
            content="Test content",
            ground_truth=EvaluationMetrics(0.05, 0.85, 0.85, 0.90),
            expected_score=0.8625
        )
        validator.dataset_manager.add_test_case(test_case)
        
        # 평가 실행
        result = validator.evaluate_section(
            test_case_id="sec_001",
            predicted_metrics=EvaluationMetrics(0.08, 0.83, 0.82, 0.88),
            predicted_score=0.8275,
            confidence=0.92
        )
        
        assert result is not None
        assert result.test_case_id == "sec_001"
        assert len(validator.evaluation_results) == 1

    def test_evaluate_section_not_found(self, validator):
        """존재하지 않는 섹션 평가"""
        result = validator.evaluate_section(
            test_case_id="nonexistent",
            predicted_metrics=EvaluationMetrics(0.1, 0.8, 0.8, 0.85),
            predicted_score=0.8,
            confidence=0.9
        )
        
        assert result is None
        assert len(validator.evaluation_results) == 0

    def test_calculate_baseline(self, validator):
        """베이스라인 메트릭 계산"""
        # 5개 테스트 케이스 추가
        test_cases = [
            TestCase(
                id=f"sec_{i:03d}",
                section_type="executive_summary",
                content=f"Content {i}",
                ground_truth=EvaluationMetrics(0.05 + i*0.02, 0.85, 0.85, 0.90),
                expected_score=0.85
            )
            for i in range(5)
        ]
        
        for tc in test_cases:
            validator.dataset_manager.add_test_case(tc)
        
        # 평가 실행 (모두 correct predictions)
        for i, tc in enumerate(test_cases):
            validator.evaluate_section(
                test_case_id=tc.id,
                predicted_metrics=tc.ground_truth,
                predicted_score=tc.expected_score,
                confidence=0.95
            )
        
        # 베이스라인 계산
        metrics = validator.calculate_baseline()
        
        assert metrics is not None
        assert metrics.precision > 0
        assert metrics.recall > 0
        assert metrics.f1_score > 0

    def test_get_report(self, validator):
        """진단 보고서 생성"""
        # 테스트 케이스 추가 및 평가
        test_case = TestCase(
            id="sec_001",
            section_type="executive_summary",
            content="Test content",
            ground_truth=EvaluationMetrics(0.05, 0.85, 0.85, 0.90),
            expected_score=0.8625
        )
        validator.dataset_manager.add_test_case(test_case)
        
        validator.evaluate_section(
            test_case_id="sec_001",
            predicted_metrics=test_case.ground_truth,
            predicted_score=test_case.expected_score,
            confidence=0.95
        )
        
        # 보고서 생성
        report = validator.get_report()
        
        assert "metadata" in report
        assert "performance_metrics" in report
        assert "status" in report
        assert "evaluation_results" in report
        assert report["metadata"]["total_evaluations"] == 1

    def test_get_status_excellent(self, validator):
        """상태: EXCELLENT (F1 >= 0.90)"""
        # 완벽한 예측으로 F1 = 1.0 달성
        for i in range(5):
            test_case = TestCase(
                id=f"sec_{i:03d}",
                section_type="executive_summary",
                content=f"Content {i}",
                ground_truth=EvaluationMetrics(0.1, 0.8, 0.8, 0.85),
                expected_score=0.8
            )
            validator.dataset_manager.add_test_case(test_case)
            validator.evaluate_section(
                test_case_id=test_case.id,
                predicted_metrics=test_case.ground_truth,
                predicted_score=test_case.expected_score,
                confidence=0.99
            )
        
        validator.calculate_baseline()
        status = validator._get_status()
        
        assert status["overall"] == "EXCELLENT"

    def test_clear_results(self, validator):
        """평가 결과 초기화"""
        # 평가 추가
        test_case = TestCase(
            id="sec_001",
            section_type="executive_summary",
            content="Content",
            ground_truth=EvaluationMetrics(0.1, 0.8, 0.8, 0.85),
            expected_score=0.8
        )
        validator.dataset_manager.add_test_case(test_case)
        validator.evaluate_section(
            test_case_id="sec_001",
            predicted_metrics=test_case.ground_truth,
            predicted_score=test_case.expected_score,
            confidence=0.9
        )
        
        assert len(validator.evaluation_results) == 1
        
        # 초기화
        validator.clear_results()
        
        assert len(validator.evaluation_results) == 0
        assert validator.baseline_metrics is None

    def test_batch_evaluation(self, validator):
        """배치 평가 (여러 섹션 한번에)"""
        # 10개 섹션 추가
        section_types = ["executive_summary", "technical_approach", "implementation"]
        
        for i in range(10):
            section_type = section_types[i % len(section_types)]
            test_case = TestCase(
                id=f"sec_{i:03d}",
                section_type=section_type,
                content=f"Content for section {i}",
                ground_truth=EvaluationMetrics(0.05 + (i % 3) * 0.05, 0.80 + (i % 3) * 0.05, 0.80 + (i % 3) * 0.05, 0.85 + (i % 3) * 0.05),
                expected_score=0.8 + (i % 3) * 0.05
            )
            validator.dataset_manager.add_test_case(test_case)
        
        # 배치 평가
        for i in range(10):
            test_case = validator.dataset_manager.get_test_case(f"sec_{i:03d}")
            # 약간의 오차를 포함한 예측 (realistic scenario)
            predicted = EvaluationMetrics(
                test_case.ground_truth.hallucination + 0.02,
                test_case.ground_truth.persuasiveness - 0.03,
                test_case.ground_truth.completeness - 0.02,
                test_case.ground_truth.clarity - 0.01
            )
            predicted_score = test_case.expected_score - 0.02
            
            validator.evaluate_section(
                test_case_id=test_case.id,
                predicted_metrics=predicted,
                predicted_score=predicted_score,
                confidence=0.85 + (i % 10) * 0.01
            )
        
        assert len(validator.evaluation_results) == 10
        
        # 베이스라인 계산
        metrics = validator.calculate_baseline()
        
        # 완벽하지는 않지만 일정 수준 이상의 성능 확인
        assert metrics.accuracy > 0
        assert metrics.f1_score > 0

    def test_load_real_dataset(self):
        """실제 50섹션 데이터셋 로드"""
        dataset_path = "data/test_datasets/harness_test_50_sections.json"
        
        # 파일이 존재하는지 확인
        if not Path(dataset_path).exists():
            pytest.skip("Dataset file not found")
        
        validator = DiagnosisAccuracyValidator(dataset_path)
        
        # 모든 50개 케이스 로드 확인
        all_cases = validator.dataset_manager.get_all_test_cases()
        assert len(all_cases) == 50
        
        # 섹션 타입 분포 확인
        stats = validator.dataset_manager.get_statistics()
        assert stats["total_cases"] == 50
        assert len(stats["by_type"]) == 5  # 5가지 섹션 타입


@pytest.mark.integration
class TestEndToEndValidationWorkflow:
    """엔드투엔드 검증 워크플로우 테스트"""

    def test_complete_validation_workflow(self, tmp_path):
        """완전한 검증 워크플로우"""
        dataset_path = str(tmp_path / "e2e_dataset.json")
        validator = DiagnosisAccuracyValidator(dataset_path)
        
        # Step 1: 테스트 케이스 생성 및 저장
        for i in range(20):
            test_case = TestCase(
                id=f"sec_{i:03d}",
                section_type=["executive_summary", "technical_approach", "implementation"][i % 3],
                content=f"Section {i} content",
                ground_truth=EvaluationMetrics(
                    0.05 + (i % 5) * 0.02,
                    0.80 + (i % 5) * 0.03,
                    0.80 + (i % 5) * 0.03,
                    0.85 + (i % 5) * 0.02
                ),
                expected_score=0.825 + (i % 5) * 0.025
            )
            validator.dataset_manager.add_test_case(test_case)
        
        validator.dataset_manager.save_dataset()
        
        # Step 2: 배치 평가 실행
        for test_case in validator.dataset_manager.get_all_test_cases()[:10]:
            # 실제 predictions (약간의 오차 포함)
            predicted = EvaluationMetrics(
                min(0.3, test_case.ground_truth.hallucination + 0.03),
                max(0, test_case.ground_truth.persuasiveness - 0.05),
                max(0, test_case.ground_truth.completeness - 0.03),
                max(0, test_case.ground_truth.clarity - 0.02)
            )
            predicted_score = test_case.expected_score - 0.04
            
            validator.evaluate_section(
                test_case_id=test_case.id,
                predicted_metrics=predicted,
                predicted_score=predicted_score,
                confidence=0.88
            )
        
        # Step 3: 베이스라인 계산
        metrics = validator.calculate_baseline()
        assert metrics.accuracy > 0
        
        # Step 4: 보고서 생성
        report = validator.get_report()
        assert report["metadata"]["total_evaluations"] == 10
        assert report["status"]["overall"] in ["EXCELLENT", "GOOD", "ACCEPTABLE", "NEEDS_IMPROVEMENT"]
        
        # Step 5: 결과 검증
        assert len(validator.evaluation_results) == 10
        assert validator.baseline_metrics is not None
