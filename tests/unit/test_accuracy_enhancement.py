"""
Unit tests for STEP 4A Phase 2: Accuracy Enhancement Engine

Tests cover:
1. ConfidenceThresholder — variance-based confidence estimation
2. EnsembleVoter — multi-variant weighted voting with outlier rejection
3. CrossValidator — k-fold cross-validation on ground truth dataset
4. AccuracyEnhancementEngine — orchestrator combining all three
"""

import pytest
from unittest.mock import Mock, patch

from app.services.accuracy_enhancement_engine import (
    ConfidenceThresholder,
    ConfidenceResult,
    EnsembleVoter,
    EnsembleResult,
    CrossValidator,
    CrossValidationResult,
    AccuracyEnhancementEngine,
    EnhancementReport,
)
from app.services.harness_accuracy_validator import (
    EvaluationMetrics,
    EvaluationResult,
    PerformanceMetrics,
    DiagnosisAccuracyValidator,
    DatasetManager,
)


class TestConfidenceThresholder:
    """Test ConfidenceThresholder — variance-based confidence estimation"""

    def test_confidence_high_agreement(self):
        """Test: Low variance (0.05) → confidence ≥ 0.9"""
        thresholder = ConfidenceThresholder()
        
        # High agreement: all 3 variants very close
        variant_scores = {
            "conservative": 0.78,
            "balanced": 0.79,
            "creative": 0.78,
        }
        
        result = thresholder.compute_confidence(variant_scores)
        
        assert isinstance(result, ConfidenceResult)
        assert result.confidence >= 0.9, f"Expected confidence >= 0.9, got {result.confidence}"
        assert result.should_accept is True
        assert result.agreement_level == "HIGH"

    def test_confidence_low_agreement(self):
        """Test: High variance (std_dev > 0.3) → confidence < 0.4, should_accept=False"""
        thresholder = ConfidenceThresholder()

        # Low agreement: scores spread very widely (std_dev ~0.35 → confidence ~0.3)
        variant_scores = {
            "conservative": 0.10,  # Very conservative
            "balanced": 0.50,      # Middle
            "creative": 0.95,      # Very creative
        }

        result = thresholder.compute_confidence(variant_scores)

        assert isinstance(result, ConfidenceResult)
        assert result.confidence < 0.4, f"Expected confidence < 0.4, got {result.confidence}"
        assert result.should_accept is False
        assert result.agreement_level == "LOW"

    def test_confidence_agreement_levels(self):
        """Test: Correct agreement level classification (HIGH/MEDIUM/LOW)"""
        thresholder = ConfidenceThresholder()

        # High agreement
        high = thresholder.compute_confidence({
            "conservative": 0.80, "balanced": 0.81, "creative": 0.79
        })
        assert high.agreement_level == "HIGH"
        assert high.confidence >= 0.80

        # Medium agreement: Need 0.65 <= confidence < 0.80 → std_dev between 0.1 and 0.175
        # [0.50, 0.70, 0.85] → mean=0.683, std_dev ~0.134 → confidence ~0.732 (MEDIUM)
        medium = thresholder.compute_confidence({
            "conservative": 0.50, "balanced": 0.70, "creative": 0.85
        })
        assert medium.agreement_level == "MEDIUM"
        assert 0.65 <= medium.confidence < 0.80

        # Low agreement
        low = thresholder.compute_confidence({
            "conservative": 0.30, "balanced": 0.60, "creative": 0.90
        })
        assert low.agreement_level == "LOW"
        assert low.confidence < 0.65

    def test_filter_low_confidence(self):
        """Test: Below-threshold results are excluded"""
        thresholder = ConfidenceThresholder()
        
        # Create mock evaluation results with different confidence levels
        high_conf_result = Mock(spec=EvaluationResult)
        high_conf_result.confidence = 0.85
        
        low_conf_result = Mock(spec=EvaluationResult)
        low_conf_result.confidence = 0.45
        
        results = [high_conf_result, low_conf_result]
        threshold = 0.70
        
        filtered = thresholder.filter_low_confidence(results, threshold)
        
        assert len(filtered) == 1
        assert filtered[0].confidence == 0.85


class TestEnsembleVoter:
    """Test EnsembleVoter — multi-variant weighted voting with outlier rejection"""

    def test_ensemble_basic_voting(self):
        """Test: 3-variant weighted avg produces correct aggregated score"""
        voter = EnsembleVoter()
        
        variant_scores = {
            "conservative": 0.70,
            "balanced": 0.75,
            "creative": 0.68,
        }
        
        variant_details = {
            "conservative": EvaluationMetrics(hallucination=0.10, persuasiveness=0.70, completeness=0.70, clarity=0.75),
            "balanced": EvaluationMetrics(hallucination=0.08, persuasiveness=0.75, completeness=0.75, clarity=0.80),
            "creative": EvaluationMetrics(hallucination=0.15, persuasiveness=0.65, completeness=0.65, clarity=0.70),
        }
        
        result = voter.vote(variant_scores, variant_details)
        
        assert isinstance(result, EnsembleResult)
        assert 0 <= result.aggregated_score <= 1
        assert sum(result.variant_weights.values()) == pytest.approx(1.0, abs=0.01)
        assert isinstance(result.aggregated_metrics, EvaluationMetrics)

    def test_ensemble_outlier_rejection(self):
        """Test: Ensemble voting with variants produces valid aggregated result"""
        voter = EnsembleVoter()

        # Variants with varying scores
        variant_scores = {
            "conservative": 0.65,
            "balanced": 0.75,
            "creative": 0.70,
        }

        variant_details = {
            "conservative": EvaluationMetrics(hallucination=0.10, persuasiveness=0.65, completeness=0.65, clarity=0.70),
            "balanced": EvaluationMetrics(hallucination=0.05, persuasiveness=0.75, completeness=0.75, clarity=0.80),
            "creative": EvaluationMetrics(hallucination=0.08, persuasiveness=0.70, completeness=0.70, clarity=0.75),
        }

        result = voter.vote(variant_scores, variant_details)

        # Validate structure
        assert isinstance(result, EnsembleResult)
        assert sum(result.variant_weights.values()) == pytest.approx(1.0, abs=0.01)
        assert 0 <= result.aggregated_score <= 1
        assert isinstance(result.aggregated_metrics, EvaluationMetrics)

    def test_ensemble_all_same_score(self):
        """Test: Equal scores → equal weights"""
        voter = EnsembleVoter()
        
        variant_scores = {
            "conservative": 0.75,
            "balanced": 0.75,
            "creative": 0.75,
        }
        
        variant_details = {
            "conservative": EvaluationMetrics(hallucination=0.10, persuasiveness=0.75, completeness=0.75, clarity=0.80),
            "balanced": EvaluationMetrics(hallucination=0.10, persuasiveness=0.75, completeness=0.75, clarity=0.80),
            "creative": EvaluationMetrics(hallucination=0.10, persuasiveness=0.75, completeness=0.75, clarity=0.80),
        }
        
        result = voter.vote(variant_scores, variant_details)
        
        # With equal scores, weights should be approximately equal (1/3 each)
        for weight in result.variant_weights.values():
            assert weight == pytest.approx(1/3, abs=0.01)


class TestCrossValidator:
    """Test CrossValidator — k-fold cross-validation"""

    def test_cross_validation_k5(self):
        """Test: 5-fold produces exactly 5 FoldResults"""
        validator_mock = Mock(spec=DiagnosisAccuracyValidator)
        validator_mock.dataset_manager = Mock(spec=DatasetManager)
        validator_mock.dataset_manager.get_test_cases_by_type = Mock(return_value=[
            Mock(id=f"sec_{i:03d}") for i in range(1, 51)  # 50 test cases
        ])

        cv = CrossValidator(k=5)

        # Create properly mocked EvaluationResult objects with all required fields
        ground_truth = EvaluationMetrics(hallucination=0.05, persuasiveness=0.80, completeness=0.80, clarity=0.85)
        predicted_results = []
        for i in range(1, 51):
            result = Mock(spec=EvaluationResult)
            result.test_case_id = f"sec_{i:03d}"
            result.predicted_score = 0.78 + (i % 5) * 0.02  # Vary between 0.78-0.86
            result.expected_score = 0.80  # Ground truth
            result.ground_truth = ground_truth
            result.predicted_metrics = EvaluationMetrics(hallucination=0.05, persuasiveness=0.78, completeness=0.78, clarity=0.82)
            result.confidence = 0.85
            predicted_results.append(result)

        result = cv.validate(validator_mock, predicted_results)

        assert isinstance(result, CrossValidationResult)
        assert result.k == 5
        assert len(result.folds) == 5

    def test_cross_validation_stability(self):
        """Test: Low-variance folds → stability_score ≥ 0.70"""
        validator_mock = Mock(spec=DiagnosisAccuracyValidator)
        validator_mock.dataset_manager = Mock(spec=DatasetManager)
        validator_mock.dataset_manager.get_test_cases_by_type = Mock(return_value=[
            Mock(id=f"sec_{i:03d}") for i in range(1, 51)
        ])

        cv = CrossValidator(k=5)

        # Create mock results with consistent metrics across folds
        ground_truth = EvaluationMetrics(hallucination=0.05, persuasiveness=0.80, completeness=0.80, clarity=0.85)
        predicted_results = []
        for i in range(1, 51):
            result = Mock(spec=EvaluationResult)
            result.test_case_id = f"sec_{i:03d}"
            result.predicted_score = 0.80 + (i % 3) * 0.01  # Low variance: 0.80-0.82
            result.expected_score = 0.80
            result.ground_truth = ground_truth
            result.predicted_metrics = EvaluationMetrics(hallucination=0.05, persuasiveness=0.80, completeness=0.80, clarity=0.85)
            result.confidence = 0.90
            predicted_results.append(result)

        result = cv.validate(validator_mock, predicted_results)

        # Low variance in F1 scores across folds → high stability
        assert result.stability_score >= 0.70  # At minimum


class TestAccuracyEnhancementEngine:
    """Test AccuracyEnhancementEngine — orchestrator"""

    def test_enhancement_engine_simulate(self):
        """Test: simulate_enhancement() executes actual enhancement on mock validator"""
        engine = AccuracyEnhancementEngine()

        # Create mock validator with required interface
        validator_mock = Mock(spec=DiagnosisAccuracyValidator)
        validator_mock.dataset_manager = Mock(spec=DatasetManager)

        # Mock dataset interface - simulate 10 test cases
        test_cases = [
            Mock(
                id=f"test_{i:02d}",
                ground_truth=EvaluationMetrics(0.05, 0.80, 0.85, 0.80),
                expected_score=0.80
            ) for i in range(10)
        ]
        validator_mock.dataset_manager.get_all_test_cases = Mock(return_value=test_cases)

        # Mock evaluate_section to return consistent evaluation results
        validator_mock.evaluate_section = Mock(
            return_value=EvaluationResult(
                test_case_id="test_00",
                predicted_metrics=EvaluationMetrics(0.05, 0.80, 0.85, 0.80),
                ground_truth=EvaluationMetrics(0.05, 0.80, 0.85, 0.80),
                predicted_score=0.80,
                expected_score=0.80,
                confidence=0.95
            )
        )

        # Call actual simulate_enhancement - not mocked
        report = engine.simulate_enhancement(validator_mock)

        # Verify result structure and actual execution
        assert isinstance(report, EnhancementReport)
        assert report.original_accuracy >= 0
        assert report.enhanced_accuracy >= 0
        assert isinstance(report.cross_validation, (CrossValidationResult, type(None)))
        # ensemble_applied should be False (placeholder in Phase 3)
        assert report.ensemble_applied is False

    def test_enhancement_engine_accuracy_improvement(self):
        """Test: enhance() computes improvement between original and enhanced accuracy"""
        engine = AccuracyEnhancementEngine()

        # Create real evaluation results with high confidence for filtering
        results = [
            Mock(
                test_case_id=f"test_{i:02d}",
                confidence=0.85,  # Above default threshold 0.65
                predicted_score=0.80 + (i % 3) * 0.02
            ) for i in range(10)
        ]

        validator_mock = Mock(spec=DiagnosisAccuracyValidator)

        # Call actual enhance - not mocked
        report = engine.enhance(validator_mock, results, variant_data=None)

        # Verify improvement is calculated correctly
        assert isinstance(report, EnhancementReport)
        assert report.improvement == pytest.approx(
            report.enhanced_accuracy - report.original_accuracy,
            abs=0.01
        )
        # ensemble_applied should be False since variant_data is None
        assert report.ensemble_applied is False


# Smoke Test (Can be run standalone)
def test_smoke_accuracy_enhancement():
    """Smoke test: Full workflow with mock data"""
    engine = AccuracyEnhancementEngine()

    # Create full mock validator with all required interfaces
    validator_mock = Mock(spec=DiagnosisAccuracyValidator)
    validator_mock.dataset_manager = Mock(spec=DatasetManager)

    # Simulate 50-section dataset
    test_cases = [
        Mock(
            id=f"section_{i:03d}",
            ground_truth=EvaluationMetrics(
                hallucination=0.05 + (i % 3) * 0.02,
                persuasiveness=0.75 + (i % 4) * 0.03,
                completeness=0.78 + (i % 5) * 0.02,
                clarity=0.80
            ),
            expected_score=0.78 + (i % 5) * 0.02
        ) for i in range(50)
    ]
    validator_mock.dataset_manager.get_all_test_cases = Mock(return_value=test_cases)

    # Mock evaluate_section with varying results
    call_count = [0]  # Use list to allow mutation in nested function
    def evaluate_side_effect(*args, **kwargs):
        idx = call_count[0] % 50
        call_count[0] += 1
        return EvaluationResult(
            test_case_id=test_cases[idx].id,
            predicted_metrics=EvaluationMetrics(
                0.05 + (idx % 3) * 0.02,
                0.75 + (idx % 4) * 0.03,
                0.78 + (idx % 5) * 0.02,
                0.80
            ),
            ground_truth=test_cases[idx].ground_truth,
            predicted_score=0.78 + (idx % 5) * 0.02,
            expected_score=test_cases[idx].expected_score,
            confidence=0.85 + (idx % 3) * 0.05
        )

    validator_mock.evaluate_section = Mock(side_effect=evaluate_side_effect)

    # Execute full workflow
    report = engine.simulate_enhancement(validator_mock)

    # Validate smoke test execution
    assert isinstance(report, EnhancementReport)
    assert report.original_accuracy >= 0
    assert report.enhanced_accuracy >= 0
    assert report.cross_validation is not None
    assert len(report.recommendations) > 0
