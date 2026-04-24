"""
Test suite for FeedbackAnalyzer service.

포괄적인 테스트 커버리지를 제공합니다:
- Unit Tests: 단일 메서드 테스트
- Integration Tests: 전체 워크플로우 테스트
- Edge Cases: 경계 조건 및 특수 시나리오
"""

import pytest
from datetime import datetime
from typing import Dict, List

from app.services.domains.proposal.feedback_analyzer import (
    FeedbackAnalyzer,
    FeedbackStats,
    WeightRecommendation,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def analyzer():
    """FeedbackAnalyzer 인스턴스를 생성합니다."""
    return FeedbackAnalyzer()


@pytest.fixture
def sample_feedback_entries() -> List[Dict]:
    """
    테스트용 샘플 피드백 데이터.

    여러 섹션(문제정의, 제안전략, 비용)에 대한 다양한 피드백을 포함합니다.
    """
    return [
        # 문제정의 섹션 (높은 승인률)
        {
            "section_type": "문제정의",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 4.5,
                "persuasiveness": 4.0,
                "completeness": 4.2,
                "clarity": 4.1,
            },
        },
        {
            "section_type": "문제정의",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 4.3,
                "persuasiveness": 4.1,
                "completeness": 4.0,
                "clarity": 4.0,
            },
        },
        {
            "section_type": "문제정의",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 4.2,
                "persuasiveness": 3.9,
                "completeness": 4.3,
                "clarity": 4.2,
            },
        },
        # 제안전략 섹션 (중간 승인률)
        {
            "section_type": "제안전략",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 3.5,
                "persuasiveness": 3.2,
                "completeness": 3.0,
                "clarity": 3.1,
            },
        },
        {
            "section_type": "제안전략",
            "decision": "REJECT",
            "ratings": {
                "hallucination": 2.8,
                "persuasiveness": 2.5,
                "completeness": 2.7,
                "clarity": 2.6,
            },
        },
        {
            "section_type": "제안전략",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 3.6,
                "persuasiveness": 3.4,
                "completeness": 3.2,
                "clarity": 3.3,
            },
        },
        # 비용 섹션 (낮은 승인률)
        {
            "section_type": "비용",
            "decision": "REJECT",
            "ratings": {
                "hallucination": 2.2,
                "persuasiveness": 2.0,
                "completeness": 2.1,
                "clarity": 2.0,
            },
        },
        {
            "section_type": "비용",
            "decision": "REJECT",
            "ratings": {
                "hallucination": 2.0,
                "persuasiveness": 1.9,
                "completeness": 2.0,
                "clarity": 1.8,
            },
        },
    ]


@pytest.fixture
def empty_feedback() -> List[Dict]:
    """빈 피드백 리스트."""
    return []


@pytest.fixture
def feedback_with_missing_ratings() -> List[Dict]:
    """일부 평점이 없는 피드백."""
    return [
        {
            "section_type": "문제정의",
            "decision": "APPROVE",
            # ratings 필드 없음
        },
        {
            "section_type": "문제정의",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 3.5,
                # 다른 평점은 없음
            },
        },
        {
            "section_type": "제안전략",
            "decision": "REJECT",
            # ratings 필드 없음
        },
    ]


@pytest.fixture
def feedback_with_missing_decision() -> List[Dict]:
    """decision 필드가 없는 피드백."""
    return [
        {
            "section_type": "문제정의",
            "ratings": {
                "hallucination": 4.0,
                "persuasiveness": 3.8,
                "completeness": 3.9,
                "clarity": 3.9,
            },
            # decision 필드 없음
        },
        {
            "section_type": "제안전략",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 3.5,
                "persuasiveness": 3.4,
                "completeness": 3.5,
                "clarity": 3.5,
            },
        },
    ]


@pytest.fixture
def feedback_high_ratings() -> List[Dict]:
    """높은 평점을 가진 피드백."""
    return [
        {
            "section_type": "문제정의",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 4.8,
                "persuasiveness": 4.7,
                "completeness": 4.8,
                "clarity": 4.7,
            },
        },
        {
            "section_type": "문제정의",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 4.9,
                "persuasiveness": 4.8,
                "completeness": 4.9,
                "clarity": 4.8,
            },
        },
    ]


@pytest.fixture
def feedback_low_ratings() -> List[Dict]:
    """낮은 평점을 가진 피드백."""
    return [
        {
            "section_type": "비용",
            "decision": "REJECT",
            "ratings": {
                "hallucination": 1.5,
                "persuasiveness": 1.6,
                "completeness": 1.4,
                "clarity": 1.5,
            },
        },
        {
            "section_type": "비용",
            "decision": "REJECT",
            "ratings": {
                "hallucination": 2.0,
                "persuasiveness": 1.8,
                "completeness": 1.9,
                "clarity": 2.0,
            },
        },
    ]


# ============================================================================
# Unit Tests: _group_by_section
# ============================================================================


@pytest.mark.unit
def test_group_by_section_basic(analyzer, sample_feedback_entries):
    """섹션별로 피드백이 올바르게 그룹화되는지 확인합니다."""
    grouped = analyzer._group_by_section(sample_feedback_entries)

    assert "문제정의" in grouped
    assert "제안전략" in grouped
    assert "비용" in grouped
    assert len(grouped["문제정의"]) == 3
    assert len(grouped["제안전략"]) == 3
    assert len(grouped["비용"]) == 2


@pytest.mark.unit
def test_group_by_section_empty(analyzer, empty_feedback):
    """빈 피드백 리스트를 그룹화하면 빈 딕셔너리가 반환됩니다."""
    grouped = analyzer._group_by_section(empty_feedback)
    assert grouped == {}


@pytest.mark.unit
def test_group_by_section_single_section(analyzer):
    """단일 섹션만 있는 피드백을 그룹화합니다."""
    entries = [
        {"section_type": "섹션A", "decision": "APPROVE"},
        {"section_type": "섹션A", "decision": "REJECT"},
    ]
    grouped = analyzer._group_by_section(entries)

    assert len(grouped) == 1
    assert grouped["섹션A"] == entries


@pytest.mark.unit
def test_group_by_section_unknown_type(analyzer):
    """section_type이 없는 항목은 'unknown'으로 분류됩니다."""
    entries = [
        {"decision": "APPROVE"},  # section_type 없음
        {"section_type": "섹션A", "decision": "REJECT"},
    ]
    grouped = analyzer._group_by_section(entries)

    assert "unknown" in grouped
    assert "섹션A" in grouped
    assert len(grouped["unknown"]) == 1


# ============================================================================
# Unit Tests: _calculate_stats
# ============================================================================


@pytest.mark.unit
def test_calculate_stats_basic(analyzer):
    """기본 통계 계산을 확인합니다."""
    entries = [
        {
            "section_type": "테스트",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 4.0,
                "persuasiveness": 3.5,
                "completeness": 3.8,
                "clarity": 3.9,
            },
        },
        {
            "section_type": "테스트",
            "decision": "REJECT",
            "ratings": {
                "hallucination": 2.0,
                "persuasiveness": 2.5,
                "completeness": 2.2,
                "clarity": 2.1,
            },
        },
    ]

    stats = analyzer._calculate_stats("테스트", entries)

    assert stats.section_type == "테스트"
    assert stats.total_feedback == 2
    assert stats.approved == 1
    assert stats.rejected == 1
    assert stats.approval_rate == 0.5
    assert stats.avg_hallucination_rating == 3.0  # (4.0 + 2.0) / 2
    assert stats.avg_persuasiveness_rating == 3.0  # (3.5 + 2.5) / 2


@pytest.mark.unit
def test_calculate_stats_all_approved(analyzer):
    """모든 피드백이 승인된 경우."""
    entries = [
        {
            "decision": "APPROVE",
            "ratings": {"hallucination": 4.5, "persuasiveness": 4.0, "completeness": 4.2, "clarity": 4.1},
        },
        {
            "decision": "APPROVE",
            "ratings": {"hallucination": 4.3, "persuasiveness": 4.1, "completeness": 4.0, "clarity": 4.0},
        },
    ]

    stats = analyzer._calculate_stats("섹션", entries)

    assert stats.approved == 2
    assert stats.rejected == 0
    assert stats.approval_rate == 1.0


@pytest.mark.unit
def test_calculate_stats_all_rejected(analyzer):
    """모든 피드백이 거부된 경우."""
    entries = [
        {
            "decision": "REJECT",
            "ratings": {"hallucination": 1.5, "persuasiveness": 1.5, "completeness": 1.5, "clarity": 1.5},
        },
        {
            "decision": "REJECT",
            "ratings": {"hallucination": 2.0, "persuasiveness": 2.0, "completeness": 2.0, "clarity": 2.0},
        },
    ]

    stats = analyzer._calculate_stats("섹션", entries)

    assert stats.approved == 0
    assert stats.rejected == 2
    assert stats.approval_rate == 0.0


@pytest.mark.unit
def test_calculate_stats_missing_ratings(analyzer, feedback_with_missing_ratings):
    """일부 항목에 ratings이 없는 경우 기본값(3.0)을 사용합니다."""
    entries = analyzer._group_by_section(feedback_with_missing_ratings)["문제정의"]
    stats = analyzer._calculate_stats("문제정의", entries)

    # 첫 번째 항목: ratings 없음 (기본값 3.0 사용)
    # 두 번째 항목: hallucination 3.5, 나머지 기본값 3.0
    # 평균: hallucination = (3.0 + 3.5) / 2 = 3.25
    assert stats.total_feedback == 2
    assert stats.avg_hallucination_rating == 3.25


@pytest.mark.unit
def test_calculate_stats_no_ratings(analyzer):
    """ratings이 전혀 없는 항목들의 경우 모든 평점이 3.0 기본값입니다."""
    entries = [
        {"decision": "APPROVE"},
        {"decision": "REJECT"},
    ]

    stats = analyzer._calculate_stats("섹션", entries)

    assert stats.avg_hallucination_rating == 3.0
    assert stats.avg_persuasiveness_rating == 3.0
    assert stats.avg_completeness_rating == 3.0
    assert stats.avg_clarity_rating == 3.0


# ============================================================================
# Unit Tests: _generate_recommendations
# ============================================================================


@pytest.mark.unit
def test_generate_recommendations_high_approval(analyzer, feedback_high_ratings):
    """높은 승인률(>90%)에서는 최소 조정만 권장됩니다."""
    entries = analyzer._group_by_section(feedback_high_ratings)["문제정의"]
    stats = analyzer._calculate_stats("문제정의", entries)

    recommendations = analyzer._generate_recommendations([stats])

    assert len(recommendations) == 1
    rec = recommendations[0]
    assert "Minimal adjustment needed - High approval rate" in rec.expected_impact
    assert rec.section_type == "문제정의"
    assert rec.hallucination == 0.85  # 높은 평점이므로 완화된 가중치


@pytest.mark.unit
def test_generate_recommendations_low_approval(analyzer, feedback_low_ratings):
    """낮은 승인률(<70%)에서는 중요한 개선 가능성이 제시됩니다."""
    entries = analyzer._group_by_section(feedback_low_ratings)["비용"]
    stats = analyzer._calculate_stats("비용", entries)

    recommendations = analyzer._generate_recommendations([stats])

    assert len(recommendations) == 1
    rec = recommendations[0]
    assert "Significant improvement potential" in rec.expected_impact
    # 낮은 평점들이 여러 개이므로 여러 권장사항이 제시됨
    assert rec.reasoning is not None
    assert len(rec.reasoning) > 0


@pytest.mark.unit
def test_generate_recommendations_hallucination_low(analyzer):
    """낮은 hallucination 평점(<2.5)에서는 필터 강화를 권장합니다."""
    entries = [
        {
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 2.0,  # 낮음
                "persuasiveness": 3.5,
                "completeness": 3.5,
                "clarity": 3.5,
            },
        }
    ]
    stats = analyzer._calculate_stats("섹션", entries)

    recommendations = analyzer._generate_recommendations([stats])
    rec = recommendations[0]

    assert rec.hallucination == 0.95  # 더 엄격하게
    assert "Hallucination rating low" in rec.reasoning
    assert "increase filter strictness" in rec.reasoning


@pytest.mark.unit
def test_generate_recommendations_hallucination_high(analyzer):
    """높은 hallucination 평점(>4.0)에서는 필터 완화를 권장합니다."""
    entries = [
        {
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 4.5,  # 높음
                "persuasiveness": 3.0,
                "completeness": 3.0,
                "clarity": 3.0,
            },
        }
    ]
    stats = analyzer._calculate_stats("섹션", entries)

    recommendations = analyzer._generate_recommendations([stats])
    rec = recommendations[0]

    assert rec.hallucination == 0.85  # 완화
    assert "Hallucination rating high" in rec.reasoning
    assert "can relax filter" in rec.reasoning


@pytest.mark.unit
def test_generate_recommendations_multiple_low_metrics(analyzer):
    """여러 평점이 낮을 때 여러 권장사항이 생성됩니다."""
    entries = [
        {
            "decision": "REJECT",
            "ratings": {
                "hallucination": 2.0,  # 낮음
                "persuasiveness": 2.0,  # 낮음
                "completeness": 2.0,  # 낮음
                "clarity": 2.0,  # 낮음
            },
        }
    ]
    stats = analyzer._calculate_stats("섹션", entries)

    recommendations = analyzer._generate_recommendations([stats])
    rec = recommendations[0]

    # 높은 가중치 (더 엄격함)
    assert rec.hallucination == 0.95
    assert rec.persuasiveness == 0.90
    assert rec.completeness == 0.93
    assert rec.clarity == 0.92

    # 여러 권고 사항이 포함됨
    reasoning_count = rec.reasoning.count(";") + 1
    assert reasoning_count >= 4


@pytest.mark.unit
def test_generate_recommendations_moderate_approval(analyzer, sample_feedback_entries):
    """중간 승인률(70~90%)에서는 적당한 조정이 권장됩니다."""
    grouped = analyzer._group_by_section(sample_feedback_entries)
    entries = grouped["제안전략"]
    stats = analyzer._calculate_stats("제안전략", entries)

    recommendations = analyzer._generate_recommendations([stats])
    rec = recommendations[0]

    assert "Moderate adjustment expected" in rec.expected_impact


# ============================================================================
# Unit Tests: _generate_summary
# ============================================================================


@pytest.mark.unit
def test_generate_summary_basic(analyzer, sample_feedback_entries):
    """기본 요약이 올바르게 생성되는지 확인합니다."""
    grouped = analyzer._group_by_section(sample_feedback_entries)
    stats = [
        analyzer._calculate_stats(section, entries)
        for section, entries in grouped.items()
    ]
    recommendations = analyzer._generate_recommendations(stats)

    summary = analyzer._generate_summary(stats, recommendations)

    assert summary["total_feedback_collected"] == 8
    assert "overall_approval_rate" in summary
    assert "sections_needing_attention" in summary
    assert "sections_performing_well" in summary
    assert "recommendations_count" in summary
    assert "next_action" in summary


@pytest.mark.unit
def test_generate_summary_overall_approval_high(analyzer, feedback_high_ratings):
    """높은 전체 승인률 요약."""
    grouped = analyzer._group_by_section(feedback_high_ratings)
    stats = [
        analyzer._calculate_stats(section, entries)
        for section, entries in grouped.items()
    ]
    recommendations = analyzer._generate_recommendations(stats)

    summary = analyzer._generate_summary(stats, recommendations)

    assert summary["overall_approval_rate"] == 1.0
    assert "Monitor next week" in summary["next_action"]


@pytest.mark.unit
def test_generate_summary_overall_approval_low(analyzer, feedback_low_ratings):
    """낮은 전체 승인률 요약."""
    grouped = analyzer._group_by_section(feedback_low_ratings)
    stats = [
        analyzer._calculate_stats(section, entries)
        for section, entries in grouped.items()
    ]
    recommendations = analyzer._generate_recommendations(stats)

    summary = analyzer._generate_summary(stats, recommendations)

    assert summary["overall_approval_rate"] == 0.0
    assert "Deploy weight adjustments" in summary["next_action"]


@pytest.mark.unit
def test_generate_summary_sections_needing_attention(analyzer, sample_feedback_entries):
    """90% 미만 승인률인 섹션이 주의 필요 섹션으로 표시됩니다."""
    grouped = analyzer._group_by_section(sample_feedback_entries)
    stats = [
        analyzer._calculate_stats(section, entries)
        for section, entries in grouped.items()
    ]
    recommendations = analyzer._generate_recommendations(stats)

    summary = analyzer._generate_summary(stats, recommendations)

    # 비용 섹션의 승인률은 0%이므로 주의 필요 섹션에 포함됨
    assert "비용" in summary["sections_needing_attention"]


@pytest.mark.unit
def test_generate_summary_sections_performing_well(analyzer, sample_feedback_entries):
    """90% 이상 승인률인 섹션이 우수 섹션으로 표시됩니다."""
    grouped = analyzer._group_by_section(sample_feedback_entries)
    stats = [
        analyzer._calculate_stats(section, entries)
        for section, entries in grouped.items()
    ]
    recommendations = analyzer._generate_recommendations(stats)

    summary = analyzer._generate_summary(stats, recommendations)

    # 문제정의 섹션의 승인률은 100%이므로 우수 섹션에 포함됨
    assert "문제정의" in summary["sections_performing_well"]


# ============================================================================
# Integration Tests: analyze_weekly_feedback
# ============================================================================


@pytest.mark.integration
def test_analyze_weekly_feedback_full_flow(analyzer, sample_feedback_entries):
    """전체 분석 워크플로우를 테스트합니다."""
    result = analyzer.analyze_weekly_feedback(sample_feedback_entries)

    assert result["period"] == "weekly"
    assert "analysis_date" in result
    assert result["total_feedback"] == 8
    assert len(result["section_stats"]) == 3  # 3개 섹션
    assert len(result["weight_recommendations"]) == 3
    assert "summary" in result


@pytest.mark.integration
def test_analyze_weekly_feedback_empty(analyzer, empty_feedback):
    """빈 피드백 리스트로 분석하면 적절한 메시지가 반환됩니다."""
    result = analyzer.analyze_weekly_feedback(empty_feedback)

    assert result["message"] == "No feedback data for analysis"
    assert result["stats"] == []
    assert result["recommendations"] == []


@pytest.mark.integration
def test_analyze_weekly_feedback_with_missing_ratings(analyzer, feedback_with_missing_ratings):
    """일부 평점이 없는 데이터를 분석합니다."""
    result = analyzer.analyze_weekly_feedback(feedback_with_missing_ratings)

    assert result["total_feedback"] == 3
    assert len(result["section_stats"]) == 2
    assert len(result["weight_recommendations"]) == 2


@pytest.mark.integration
def test_analyze_weekly_feedback_with_missing_decision(analyzer, feedback_with_missing_decision):
    """decision이 없는 항목을 거부된 것으로 계산합니다."""
    result = analyzer.analyze_weekly_feedback(feedback_with_missing_decision)

    # decision이 없으면 REJECT로 취급됨 (approved가 아님)
    section_stats = result["section_stats"]

    # 문제정의: decision 없음(REJECT) + APPROVE 1개 = 승인률 50%
    problem_def_stat = next(s for s in section_stats if s["section_type"] == "문제정의")
    assert problem_def_stat["approved"] == 0  # decision 없음 = REJECT
    assert problem_def_stat["rejected"] == 1


@pytest.mark.integration
def test_analyze_weekly_feedback_result_structure(analyzer, sample_feedback_entries):
    """결과 구조가 정확한지 확인합니다."""
    result = analyzer.analyze_weekly_feedback(sample_feedback_entries)

    # 최상위 키
    assert set(result.keys()) >= {
        "period",
        "analysis_date",
        "total_feedback",
        "section_stats",
        "weight_recommendations",
        "summary",
    }

    # section_stats 구조
    for stat in result["section_stats"]:
        assert "section_type" in stat
        assert "total_feedback" in stat
        assert "approved" in stat
        assert "rejected" in stat
        assert "approval_rate" in stat
        assert "avg_hallucination" in stat
        assert "avg_persuasiveness" in stat
        assert "avg_completeness" in stat
        assert "avg_clarity" in stat

    # weight_recommendations 구조
    for rec in result["weight_recommendations"]:
        assert "section_type" in rec
        assert "recommended_weights" in rec
        assert "reasoning" in rec
        assert "expected_impact" in rec


# ============================================================================
# Integration Tests: get_feedback_analysis_report
# ============================================================================


@pytest.mark.integration
def test_get_feedback_analysis_report_basic(analyzer, sample_feedback_entries):
    """텍스트 리포트가 올바르게 생성되는지 확인합니다."""
    report = analyzer.get_feedback_analysis_report(sample_feedback_entries)

    assert isinstance(report, str)
    assert "WEEKLY FEEDBACK ANALYSIS REPORT" in report
    assert "SECTION ANALYSIS" in report
    assert "WEIGHT RECOMMENDATIONS" in report
    assert "SUMMARY" in report
    assert "=" * 80 in report


@pytest.mark.integration
def test_get_feedback_analysis_report_sections_included(analyzer, sample_feedback_entries):
    """리포트에 모든 섹션이 포함되어 있습니다."""
    report = analyzer.get_feedback_analysis_report(sample_feedback_entries)

    assert "문제정의" in report.upper()
    assert "제안전략" in report.upper()
    assert "비용" in report.upper()


@pytest.mark.integration
def test_get_feedback_analysis_report_metrics_included(analyzer, sample_feedback_entries):
    """리포트에 메트릭이 포함되어 있습니다."""
    report = analyzer.get_feedback_analysis_report(sample_feedback_entries)

    assert "Approval Rate" in report
    assert "Hallucination" in report
    assert "Persuasiveness" in report
    assert "Completeness" in report
    assert "Clarity" in report
    assert "Overall Approval Rate" in report


@pytest.mark.integration
def test_get_feedback_analysis_report_empty(analyzer, empty_feedback):
    """빈 피드백으로 생성한 리포트."""
    report = analyzer.get_feedback_analysis_report(empty_feedback)

    assert "WEEKLY FEEDBACK ANALYSIS REPORT" in report
    assert "Total Feedback: 0" in report


@pytest.mark.integration
def test_get_feedback_analysis_report_structure(analyzer, sample_feedback_entries):
    """리포트 구조가 정확한지 확인합니다."""
    report = analyzer.get_feedback_analysis_report(sample_feedback_entries)

    lines = report.split("\n")

    # 헤더 확인
    assert any("WEEKLY FEEDBACK ANALYSIS REPORT" in line for line in lines)
    assert any("SECTION ANALYSIS" in line for line in lines)
    assert any("WEIGHT RECOMMENDATIONS" in line for line in lines)
    assert any("SUMMARY" in line for line in lines)


# ============================================================================
# Edge Cases
# ============================================================================


@pytest.mark.unit
def test_edge_case_single_feedback_entry(analyzer):
    """단일 피드백 항목 처리."""
    entries = [
        {
            "section_type": "섹션",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 3.5,
                "persuasiveness": 3.5,
                "completeness": 3.5,
                "clarity": 3.5,
            },
        }
    ]

    result = analyzer.analyze_weekly_feedback(entries)

    assert result["total_feedback"] == 1
    assert result["section_stats"][0]["approval_rate"] == 1.0


@pytest.mark.unit
def test_edge_case_extreme_ratings(analyzer):
    """극단적인 평점 값 처리."""
    entries = [
        {
            "section_type": "섹션",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 5.0,  # 최대값
                "persuasiveness": 0.0,  # 최소값 (이론적)
                "completeness": 2.5,  # 중간값
                "clarity": 1.0,  # 낮은 값
            },
        }
    ]

    result = analyzer.analyze_weekly_feedback(entries)
    stats = result["section_stats"][0]

    assert stats["avg_hallucination"] == 5.0
    assert stats["avg_persuasiveness"] == 0.0
    assert stats["avg_completeness"] == 2.5
    assert stats["avg_clarity"] == 1.0


@pytest.mark.unit
def test_edge_case_many_sections(analyzer):
    """많은 섹션을 처리합니다."""
    entries = []
    for i in range(10):
        entries.append({
            "section_type": f"섹션_{i}",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 3.5,
                "persuasiveness": 3.5,
                "completeness": 3.5,
                "clarity": 3.5,
            },
        })

    result = analyzer.analyze_weekly_feedback(entries)

    assert result["total_feedback"] == 10
    assert len(result["section_stats"]) == 10


@pytest.mark.unit
def test_edge_case_special_characters_in_section_type(analyzer):
    """특수 문자를 포함한 섹션 이름."""
    entries = [
        {
            "section_type": "섹션/테스트-1",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 3.5,
                "persuasiveness": 3.5,
                "completeness": 3.5,
                "clarity": 3.5,
            },
        }
    ]

    result = analyzer.analyze_weekly_feedback(entries)

    assert result["section_stats"][0]["section_type"] == "섹션/테스트-1"


@pytest.mark.unit
def test_edge_case_zero_approval_rate(analyzer):
    """승인률 0%인 경우."""
    entries = [
        {
            "section_type": "문제섹션",
            "decision": "REJECT",
            "ratings": {
                "hallucination": 1.0,
                "persuasiveness": 1.0,
                "completeness": 1.0,
                "clarity": 1.0,
            },
        },
        {
            "section_type": "문제섹션",
            "decision": "REJECT",
            "ratings": {
                "hallucination": 1.5,
                "persuasiveness": 1.5,
                "completeness": 1.5,
                "clarity": 1.5,
            },
        },
    ]

    result = analyzer.analyze_weekly_feedback(entries)
    stat = result["section_stats"][0]

    assert stat["approval_rate"] == 0.0
    assert stat["approved"] == 0
    assert stat["rejected"] == 2


@pytest.mark.unit
def test_edge_case_perfect_approval_rate(analyzer, feedback_high_ratings):
    """승인률 100%인 경우."""
    result = analyzer.analyze_weekly_feedback(feedback_high_ratings)
    stat = result["section_stats"][0]

    assert stat["approval_rate"] == 1.0
    assert stat["approved"] == 2
    assert stat["rejected"] == 0


# ============================================================================
# Dataclass Tests
# ============================================================================


@pytest.mark.unit
def test_feedback_stats_to_dict():
    """FeedbackStats를 딕셔너리로 변환합니다."""
    stats = FeedbackStats(
        section_type="테스트",
        total_feedback=10,
        approved=8,
        rejected=2,
        approval_rate=0.8,
        avg_hallucination_rating=3.5,
        avg_persuasiveness_rating=3.6,
        avg_completeness_rating=3.7,
        avg_clarity_rating=3.8,
    )

    result = stats.to_dict()

    assert result["section_type"] == "테스트"
    assert result["total_feedback"] == 10
    assert result["approved"] == 8
    assert result["rejected"] == 2
    assert result["approval_rate"] == 0.8
    assert result["avg_hallucination"] == 3.5
    assert result["avg_persuasiveness"] == 3.6


@pytest.mark.unit
def test_weight_recommendation_to_dict():
    """WeightRecommendation을 딕셔너리로 변환합니다."""
    rec = WeightRecommendation(
        section_type="테스트",
        hallucination=0.95,
        persuasiveness=0.90,
        completeness=0.93,
        clarity=0.92,
        reasoning="Test reasoning",
        expected_impact="Significant improvement",
    )

    result = rec.to_dict()

    assert result["section_type"] == "테스트"
    assert result["recommended_weights"]["hallucination"] == 0.95
    assert result["reasoning"] == "Test reasoning"
    assert result["expected_impact"] == "Significant improvement"


@pytest.mark.unit
def test_weight_recommendation_none_values():
    """None 값이 있는 WeightRecommendation."""
    rec = WeightRecommendation(
        section_type="테스트",
        hallucination=0.95,
        persuasiveness=None,
        completeness=None,
        clarity=None,
    )

    result = rec.to_dict()

    assert result["recommended_weights"]["hallucination"] == 0.95
    assert result["recommended_weights"]["persuasiveness"] is None
    assert result["recommended_weights"]["completeness"] is None


# ============================================================================
# Parametrized Tests
# ============================================================================


@pytest.mark.unit
@pytest.mark.parametrize("approval_count,total,expected_rate", [
    (0, 1, 0.0),
    (1, 1, 1.0),
    (1, 2, 0.5),
    (3, 4, 0.75),
    (9, 10, 0.9),
])
def test_approval_rate_calculation(analyzer, approval_count, total, expected_rate):
    """다양한 승인률 계산을 테스트합니다."""
    entries = []
    for i in range(approval_count):
        entries.append({"decision": "APPROVE"})
    for i in range(total - approval_count):
        entries.append({"decision": "REJECT"})

    stats = analyzer._calculate_stats("섹션", entries)

    assert stats.approval_rate == expected_rate


@pytest.mark.unit
@pytest.mark.parametrize("rating,expected_hallucination_weight", [
    (1.5, 0.95),  # 낮음: 더 엄격
    (2.4, 0.95),  # 낮음
    (2.5, 0.90),  # 기본값
    (3.5, 0.90),  # 기본값
    (4.0, 0.85),  # 경계
    (4.5, 0.85),  # 높음: 완화
])
def test_hallucination_weight_recommendation(analyzer, rating, expected_hallucination_weight):
    """hallucination 평점에 따른 가중치 권장사항."""
    entries = [
        {
            "decision": "APPROVE",
            "ratings": {
                "hallucination": rating,
                "persuasiveness": 3.5,
                "completeness": 3.5,
                "clarity": 3.5,
            },
        }
    ]

    stats = analyzer._calculate_stats("섹션", entries)
    recommendations = analyzer._generate_recommendations([stats])
    rec = recommendations[0]

    assert rec.hallucination == expected_hallucination_weight
