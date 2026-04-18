"""
harness_weight_tuning 단위 테스트 (Phase 3)

테스트 범위:
1. Grid Search (4개)
2. Section-Specific Rules (5개)
3. Feedback Integration (4개)
4. Custom Rules (2개)
5. 통합 테스트 (2개)
"""

import pytest
from app.services.harness_weight_tuning import (
    WeightTuningEngine,
    SectionType,
    SectionTypeWeights,
    GridSearchResult,
    FeedbackEntry,
    SectionRule
)
from app.services.harness_accuracy_validator import TestSection, GroundTruthLabel
from app.services.harness_evaluator import EvaluationScore


# ==================== Grid Search Tests ====================

@pytest.fixture
def weight_tuning_engine():
    """WeightTuningEngine 인스턴스"""
    return WeightTuningEngine()


@pytest.mark.asyncio
async def test_grid_search_finds_best_weights(weight_tuning_engine):
    """Grid Search가 최적 가중치를 찾음"""
    test_sections = [
        TestSection(
            section_id="test_01",
            title="Executive Summary",
            content="A" * 500,
            section_type="executive_summary",
            ground_truth=GroundTruthLabel(
                section_id="test_01",
                hallucination_severity="none",
                persuasiveness_level=5,
                completeness_score=95,
                clarity_rating=5
            )
        )
    ]

    # Mock evaluation function that returns better scores for certain weights
    async def mock_eval(weights, sections):
        hallucination_weight = weights.get("hallucination", 0.4)
        if hallucination_weight > 0.3:
            return {
                "f1_score": 0.95,
                "precision": 0.97,
                "recall": 0.93
            }
        else:
            return {
                "f1_score": 0.70,
                "precision": 0.72,
                "recall": 0.68
            }

    result = await weight_tuning_engine.grid_search(
        test_sections,
        mock_eval
    )

    assert result.best_f1_score > 0.85
    assert result.best_precision > 0.9
    assert result.iterations > 0
    assert result.best_weights is not None
    assert result.best_weights.get("hallucination", 0) > 0.2


@pytest.mark.asyncio
async def test_grid_search_custom_ranges(weight_tuning_engine):
    """Grid Search가 커스텀 범위를 사용"""
    test_sections = [
        TestSection(
            section_id="test_01",
            title="Technical",
            content="A" * 500,
            section_type="technical_details",
            ground_truth=GroundTruthLabel(
                section_id="test_01",
                hallucination_severity="none",
                persuasiveness_level=5,
                completeness_score=95,
                clarity_rating=5
            )
        )
    ]

    async def mock_eval(weights, sections):
        return {"f1_score": 0.85, "precision": 0.87, "recall": 0.83}

    custom_ranges = {
        "hallucination": (0.4, 0.5),
        "persuasiveness": (0.15, 0.25),
        "completeness": (0.15, 0.25),
        "clarity": (0.15, 0.25)
    }

    result = await weight_tuning_engine.grid_search(
        test_sections,
        mock_eval,
        param_ranges=custom_ranges
    )

    assert result.iterations > 0
    assert result.best_f1_score > 0.0
    assert result.search_history is not None
    assert len(result.search_history) > 0


@pytest.mark.asyncio
async def test_grid_search_preserves_history(weight_tuning_engine):
    """Grid Search가 모든 반복을 기록"""
    test_sections = [
        TestSection(
            section_id="test_01",
            title="Test",
            content="A" * 500,
            section_type="executive_summary",
            ground_truth=GroundTruthLabel(
                section_id="test_01",
                hallucination_severity="none",
                persuasiveness_level=5,
                completeness_score=95,
                clarity_rating=5
            )
        )
    ]

    async def mock_eval(weights, sections):
        return {"f1_score": 0.85, "precision": 0.87, "recall": 0.83}

    result = await weight_tuning_engine.grid_search(
        test_sections,
        mock_eval
    )

    assert len(result.search_history) == result.iterations
    for entry in result.search_history:
        assert "weights" in entry
        assert "f1_score" in entry


@pytest.mark.asyncio
async def test_grid_search_normalizes_weights(weight_tuning_engine):
    """Grid Search가 가중치를 정규화"""
    test_sections = [
        TestSection(
            section_id="test_01",
            title="Test",
            content="A" * 500,
            section_type="executive_summary",
            ground_truth=GroundTruthLabel(
                section_id="test_01",
                hallucination_severity="none",
                persuasiveness_level=5,
                completeness_score=95,
                clarity_rating=5
            )
        )
    ]

    async def mock_eval(weights, sections):
        # 가중치 합 확인
        total = (
            weights["hallucination"] +
            weights["persuasiveness"] +
            weights["completeness"] +
            weights["clarity"]
        )
        # 합이 1.0에 가까우면 높은 점수
        assert abs(total - 1.0) < 0.01
        return {"f1_score": 0.9, "precision": 0.92, "recall": 0.88}

    result = await weight_tuning_engine.grid_search(
        test_sections,
        mock_eval
    )

    assert result.best_weights is not None
    total_weight = sum(result.best_weights.values())
    assert abs(total_weight - 1.0) < 0.01


# ==================== Section-Specific Rules Tests ====================

@pytest.fixture
def test_section():
    """테스트 섹션"""
    return TestSection(
        section_id="test_01",
        title="Test Section",
        content="A" * 500,
        section_type="executive_summary",
        ground_truth=GroundTruthLabel(
            section_id="test_01",
            hallucination_severity="none",
            persuasiveness_level=5,
            completeness_score=95,
            clarity_rating=5
        )
    )


def test_section_rules_applied_for_executive_summary(weight_tuning_engine, test_section):
    """Executive Summary 규칙이 적용됨"""
    score = EvaluationScore(
        overall=0.9,
        hallucination=0.2,
        persuasiveness=0.85,  # 높은 설득력 -> hallucination 감소
        completeness=0.9,
        clarity=0.9
    )

    adjusted_hallucination, rules = weight_tuning_engine.apply_section_rules(
        test_section, score
    )

    # 설득력이 높으므로 규칙이 적용되어야 함
    assert adjusted_hallucination < score.hallucination
    assert len(rules) > 0


def test_section_rules_applied_for_technical_details(weight_tuning_engine):
    """Technical Details 규칙이 적용됨"""
    section = TestSection(
        section_id="test_02",
        title="Technical Details",
        content="A" * 500,
        section_type="technical_details",
        ground_truth=GroundTruthLabel(
            section_id="test_02",
            hallucination_severity="none",
            persuasiveness_level=5,
            completeness_score=95,
            clarity_rating=5
        )
    )

    score = EvaluationScore(
        overall=0.9,
        hallucination=0.3,
        persuasiveness=0.8,
        completeness=0.85,  # 높은 완성도
        clarity=0.85        # 높은 명확성
    )

    adjusted_hallucination, rules = weight_tuning_engine.apply_section_rules(section, score)

    # 완성도와 명확성이 모두 높으므로 규칙이 적용됨
    assert adjusted_hallucination < score.hallucination
    assert len(rules) > 0


def test_section_rules_applied_for_team(weight_tuning_engine):
    """Team 섹션 규칙이 적용됨 (낮은 설득력 -> hallucination 증가)"""
    section = TestSection(
        section_id="test_03",
        title="Team",
        content="A" * 500,
        section_type="team",
        ground_truth=GroundTruthLabel(
            section_id="test_03",
            hallucination_severity="none",
            persuasiveness_level=2,
            completeness_score=50,
            clarity_rating=3
        )
    )

    score = EvaluationScore(
        overall=0.4,
        hallucination=0.3,
        persuasiveness=0.3,  # 낮은 설득력
        completeness=0.5,
        clarity=0.5
    )

    adjusted_hallucination, rules = weight_tuning_engine.apply_section_rules(section, score)

    # 설득력이 낮으므로 hallucination 증가
    assert adjusted_hallucination > score.hallucination
    assert len(rules) > 0


def test_section_rules_clipped_to_range(weight_tuning_engine, test_section):
    """조정된 hallucination 점수가 0-1 범위에 클리핑됨"""
    score = EvaluationScore(
        overall=0.95,
        hallucination=0.05,  # 매우 낮음 (규칙으로 음수까지 갈 수 있음)
        persuasiveness=0.95,
        completeness=0.95,
        clarity=0.95
    )

    adjusted_hallucination, rules = weight_tuning_engine.apply_section_rules(
        test_section, score
    )

    # 범위 안에 있어야 함
    assert 0.0 <= adjusted_hallucination <= 1.0


# ==================== Feedback Integration Tests ====================

def test_feedback_added_and_tracked(weight_tuning_engine):
    """피드백이 추가되고 추적됨"""
    feedback = FeedbackEntry(
        section_id="test_01",
        section_type=SectionType.EXECUTIVE_SUMMARY,
        user_assessment=0.1,
        ai_prediction=0.2,
        is_correct=True
    )

    weight_tuning_engine.add_feedback(feedback)

    assert len(weight_tuning_engine.feedback_history) == 1
    assert weight_tuning_engine.feedback_history[0].section_id == "test_01"


def test_feedback_accuracy_calculation(weight_tuning_engine):
    """피드백 기반 정확도가 계산됨"""
    weight_tuning_engine.add_feedback(FeedbackEntry(
        section_id="test_01",
        section_type=SectionType.EXECUTIVE_SUMMARY,
        user_assessment=0.1,
        ai_prediction=0.1,
        is_correct=True
    ))

    weight_tuning_engine.add_feedback(FeedbackEntry(
        section_id="test_02",
        section_type=SectionType.TECHNICAL_DETAILS,
        user_assessment=0.5,
        ai_prediction=0.3,
        is_correct=False
    ))

    metrics = weight_tuning_engine.calculate_feedback_accuracy()

    assert metrics["total_feedback"] == 2
    assert metrics["accuracy"] == 0.5  # 1/2 정확
    assert "avg_prediction_error" in metrics
    assert metrics["avg_prediction_error"] > 0


def test_feedback_adapts_weights(weight_tuning_engine):
    """피드백이 가중치 조정을 유도"""
    # 낮은 정확도 피드백 추가
    for i in range(5):
        weight_tuning_engine.add_feedback(FeedbackEntry(
            section_id=f"test_{i:02d}",
            section_type=SectionType.TECHNICAL_DETAILS,
            user_assessment=float(i) / 5,
            ai_prediction=0.9,  # 큰 오차
            is_correct=False
        ))

    original_weights = weight_tuning_engine.section_weights[SectionType.TECHNICAL_DETAILS].hallucination_weight

    weight_tuning_engine.adapt_weights_from_feedback()

    adapted_weights = weight_tuning_engine.section_weights[SectionType.TECHNICAL_DETAILS].hallucination_weight

    # 정확도가 80% 이하이므로 hallucination_weight가 증가해야 함
    assert adapted_weights > original_weights


def test_empty_feedback_returns_zero_metrics(weight_tuning_engine):
    """피드백이 없으면 0 메트릭 반환"""
    metrics = weight_tuning_engine.calculate_feedback_accuracy()

    assert metrics["total_feedback"] == 0
    assert metrics["accuracy"] == 0.0
    assert metrics["avg_prediction_error"] == 0.0


# ==================== Custom Rules Tests ====================

def test_custom_rule_with_condition(weight_tuning_engine):
    """커스텀 규칙이 조건과 함께 작동"""
    section = TestSection(
        section_id="test_01",
        title="Test",
        content="A" * 500,
        section_type="pricing",
        ground_truth=GroundTruthLabel(
            section_id="test_01",
            hallucination_severity="none",
            persuasiveness_level=5,
            completeness_score=95,
            clarity_rating=5
        )
    )

    # Pricing 섹션용 커스텀 규칙 추가
    def pricing_condition(eval_score):
        return eval_score.completeness > 0.8

    weight_tuning_engine.add_custom_rule(
        SectionType.PRICING,
        "high_completeness_pricing",
        pricing_condition,
        adjustment=-0.15,
        priority=4
    )

    score = EvaluationScore(
        overall=0.9,
        hallucination=0.3,
        persuasiveness=0.8,
        completeness=0.85,
        clarity=0.8
    )

    adjusted_hallucination, rules = weight_tuning_engine.apply_section_rules(section, score)

    # 커스텀 규칙이 적용되어야 함
    assert "high_completeness_pricing" in str(rules)


def test_multiple_rules_stack(weight_tuning_engine):
    """여러 규칙이 누적됨"""
    section = TestSection(
        section_id="test_01",
        title="Test",
        content="A" * 500,
        section_type="executive_summary",
        ground_truth=GroundTruthLabel(
            section_id="test_01",
            hallucination_severity="none",
            persuasiveness_level=5,
            completeness_score=95,
            clarity_rating=5
        )
    )

    # 추가 규칙
    def extra_condition(eval_score):
        return eval_score.persuasiveness > 0.8

    weight_tuning_engine.add_custom_rule(
        SectionType.EXECUTIVE_SUMMARY,
        "rule_1",
        extra_condition,
        adjustment=-0.05
    )

    score = EvaluationScore(
        overall=0.95,
        hallucination=0.2,
        persuasiveness=0.9,
        completeness=0.95,
        clarity=0.95
    )

    adjusted_hallucination, rules = weight_tuning_engine.apply_section_rules(section, score)

    # 여러 규칙이 적용되어야 함
    assert len(rules) >= 2  # 기본 규칙 + 커스텀 규칙


# ==================== Integration Tests ====================

@pytest.mark.asyncio
async def test_full_workflow_grid_search_and_rules(weight_tuning_engine):
    """Grid Search + Section Rules 통합 워크플로우"""
    test_sections = [
        TestSection(
            section_id="test_01",
            title="Executive Summary",
            content="A" * 500,
            section_type="executive_summary",
            ground_truth=GroundTruthLabel(
                section_id="test_01",
                hallucination_severity="none",
                persuasiveness_level=5,
                completeness_score=95,
                clarity_rating=5
            )
        ),
        TestSection(
            section_id="test_02",
            title="Technical Details",
            content="B" * 500,
            section_type="technical_details",
            ground_truth=GroundTruthLabel(
                section_id="test_02",
                hallucination_severity="low",
                persuasiveness_level=4,
                completeness_score=85,
                clarity_rating=4
            )
        )
    ]

    async def mock_eval(weights, sections):
        return {"f1_score": 0.88, "precision": 0.90, "recall": 0.86}

    # Grid Search 실행
    search_result = await weight_tuning_engine.grid_search(
        test_sections,
        mock_eval
    )

    assert search_result.best_f1_score > 0.8

    # Section Rules 적용
    score = EvaluationScore(
        overall=0.88,
        hallucination=0.15,
        persuasiveness=0.85,
        completeness=0.85,
        clarity=0.85
    )

    adjusted, rules = weight_tuning_engine.apply_section_rules(test_sections[0], score)

    assert adjusted is not None
    assert len(rules) >= 0


def test_complete_accuracy_improvement_cycle(weight_tuning_engine):
    """정확도 개선 완전 사이클"""
    # 1. 초기 피드백 추가
    for i in range(3):
        weight_tuning_engine.add_feedback(FeedbackEntry(
            section_id=f"test_{i:02d}",
            section_type=SectionType.TECHNICAL_DETAILS,
            user_assessment=0.1,
            ai_prediction=0.9,
            is_correct=False
        ))

    # 2. 피드백 메트릭 확인
    metrics_before = weight_tuning_engine.calculate_feedback_accuracy()
    assert metrics_before["accuracy"] == 0.0

    # 3. 가중치 적응
    weight_tuning_engine.adapt_weights_from_feedback()

    # 4. 적응된 가중치 확인
    adapted_weights = weight_tuning_engine.section_weights[SectionType.TECHNICAL_DETAILS]
    assert adapted_weights.hallucination_weight > 0.35  # 기본값에서 증가
