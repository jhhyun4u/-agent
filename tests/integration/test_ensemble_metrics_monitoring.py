"""
Integration tests for STEP 4A Phase 3 Task 6: Ensemble Metrics Monitoring

Tests cover:
1. Metrics collection (confidence, feedback, ensemble application)
2. Dashboard generation
3. Alert and recommendation logic
4. Export and reporting
"""

import json
import pytest
from pathlib import Path

from app.services.domains.proposal.ensemble_metrics_monitor import (
    EnsembleMetricsMonitor,
    ConfidenceDistribution,
    FeedbackLoopMetrics,
    EnsembleApplicationMetrics,
    get_global_monitor,
    reset_monitor,
)
from app.services.domains.vault.metrics_dashboard import MetricsDashboard


class TestMetricsCollection:
    """메트릭 수집 테스트"""

    def test_section_metrics_recording(self):
        """섹션 메트릭 기록 확인"""
        monitor = EnsembleMetricsMonitor()

        monitor.record_section(
            proposal_id="prop_001",
            section_id="sec_001",
            confidence=0.85,
            score=0.80,
            ensemble_applied=True,
        )

        assert len(monitor.section_metrics) == 1
        assert monitor.section_metrics[0]["proposal_id"] == "prop_001"
        assert monitor.section_metrics[0]["confidence"] == 0.85

    def test_confidence_distribution(self):
        """신뢰도 분포 추적 확인"""
        monitor = EnsembleMetricsMonitor()

        # High confidence
        for i in range(5):
            monitor.record_section(
                proposal_id="prop_001",
                section_id=f"sec_{i}",
                confidence=0.85,
                score=0.80,
                ensemble_applied=True,
            )

        # Medium confidence
        for i in range(3):
            monitor.record_section(
                proposal_id="prop_001",
                section_id=f"sec_{i+5}",
                confidence=0.70,
                score=0.75,
                ensemble_applied=True,
            )

        # Low confidence
        for i in range(2):
            monitor.record_section(
                proposal_id="prop_001",
                section_id=f"sec_{i+8}",
                confidence=0.50,
                score=0.60,
                ensemble_applied=True,
            )

        assert monitor.confidence_dist.total_count == 10
        assert monitor.confidence_dist.high_count == 5
        assert monitor.confidence_dist.medium_count == 3
        assert monitor.confidence_dist.low_count == 2
        assert round(monitor.confidence_dist.high_percentage, 0) == 50.0

    def test_feedback_loop_metrics(self):
        """피드백 루프 메트릭 기록 확인"""
        monitor = EnsembleMetricsMonitor()

        # Feedback triggered and improved
        monitor.record_section(
            proposal_id="prop_001",
            section_id="sec_001",
            confidence=0.50,
            score=0.60,
            ensemble_applied=True,
            feedback_triggered=True,
            feedback_improved=True,
        )

        # Feedback triggered but not improved
        monitor.record_section(
            proposal_id="prop_001",
            section_id="sec_002",
            confidence=0.55,
            score=0.65,
            ensemble_applied=True,
            feedback_triggered=True,
            feedback_improved=False,
        )

        # No feedback
        monitor.record_section(
            proposal_id="prop_001",
            section_id="sec_003",
            confidence=0.85,
            score=0.80,
            ensemble_applied=True,
            feedback_triggered=False,
        )

        assert monitor.feedback_metrics.triggered_count == 2
        assert monitor.feedback_metrics.improved_count == 1
        assert monitor.feedback_metrics.not_triggered_count == 1

    def test_ensemble_application_tracking(self):
        """앙상블 적용 추적 확인"""
        monitor = EnsembleMetricsMonitor()

        # Ensemble applied
        for i in range(7):
            monitor.record_section(
                proposal_id="prop_001",
                section_id=f"sec_{i}",
                confidence=0.75,
                score=0.70,
                ensemble_applied=True,
            )

        # Fallback to argmax
        for i in range(3):
            monitor.record_section(
                proposal_id="prop_001",
                section_id=f"sec_{i+7}",
                confidence=0.60,
                score=0.65,
                ensemble_applied=False,  # Fallback
            )

        assert monitor.ensemble_metrics.total_sections == 10
        assert monitor.ensemble_metrics.applied_count == 7
        assert monitor.ensemble_metrics.fallback_count == 3
        assert round(monitor.ensemble_metrics.application_rate, 0) == 70.0


class TestProposalMetrics:
    """제안 메트릭 테스트"""

    def test_proposal_recording(self):
        """제안 메트릭 기록 확인"""
        monitor = EnsembleMetricsMonitor()

        confidences = [0.85, 0.80, 0.75, 0.70]
        scores = [0.80, 0.78, 0.75, 0.72]

        monitor.record_proposal(
            proposal_id="prop_001",
            section_count=4,
            confidences=confidences,
            scores=scores,
            ensemble_applied=True,
            feedback_triggered_count=1,
        )

        assert len(monitor.proposal_history) == 1
        proposal = monitor.proposal_history[0]
        assert proposal.proposal_id == "prop_001"
        assert proposal.section_count == 4
        assert proposal.confidence_avg == sum(confidences) / len(confidences)

    def test_get_proposal_details(self):
        """제안 상세 조회 확인"""
        monitor = EnsembleMetricsMonitor()

        monitor.record_proposal(
            proposal_id="prop_001",
            section_count=2,
            confidences=[0.85, 0.80],
            scores=[0.80, 0.78],
            ensemble_applied=True,
        )

        details = monitor.get_proposal_details("prop_001")
        assert details is not None
        assert details["proposal_id"] == "prop_001"
        assert details["section_count"] == 2


class TestDashboard:
    """대시보드 생성 테스트"""

    def test_dashboard_generation(self, tmp_path):
        """대시보드 생성 확인"""
        dashboard = MetricsDashboard(output_dir=str(tmp_path))

        # Add some metrics
        for i in range(5):
            dashboard.monitor.record_section(
                proposal_id="prop_001",
                section_id=f"sec_{i}",
                confidence=0.75 + (i * 0.02),
                score=0.70 + (i * 0.02),
                ensemble_applied=True,
            )

        dashboard_data = dashboard.generate_comprehensive_dashboard()

        assert "confidence_report" in dashboard_data
        assert "feedback_report" in dashboard_data
        assert "ensemble_report" in dashboard_data
        assert dashboard_data["confidence_report"]["overall_statistics"]["total_sections"] == 5

    def test_confidence_recommendations(self):
        """신뢰도 권장사항 생성 확인"""
        dashboard = MetricsDashboard()

        # High proportion of low confidence
        for i in range(40):
            confidence = 0.50 if i < 35 else 0.85
            dashboard.monitor.record_section(
                proposal_id="prop_001",
                section_id=f"sec_{i}",
                confidence=confidence,
                score=0.70,
                ensemble_applied=True,
            )

        report = dashboard.generate_confidence_report()
        recommendations = report["recommendations"]

        # Should have recommendation for high low-confidence
        assert any("30" in rec for rec in recommendations)

    def test_feedback_recommendations(self):
        """피드백 권장사항 생성 확인"""
        dashboard = MetricsDashboard()

        # Record proposals with high feedback trigger rate
        for i in range(10):
            dashboard.monitor.record_proposal(
                proposal_id=f"prop_{i}",
                section_count=1,
                confidences=[0.50],  # Low confidence
                scores=[0.60],
                ensemble_applied=True,
                feedback_triggered_count=1,  # Always triggers
            )

        report = dashboard.generate_feedback_report()
        recommendations = report["recommendations"]

        # Should have high trigger rate warning
        assert len(recommendations) > 0

    def test_ensemble_recommendations(self):
        """앙상블 권장사항 생성 확인"""
        reset_monitor()
        dashboard = MetricsDashboard()

        # Record many sections with fallback
        for i in range(10):
            ensemble_applied = i < 6  # 60% ensemble, 40% fallback
            dashboard.monitor.record_section(
                proposal_id="prop_001",
                section_id=f"sec_{i}",
                confidence=0.75,
                score=0.70,
                ensemble_applied=ensemble_applied,
            )

        report = dashboard.generate_ensemble_report()

        assert report["overall_statistics"]["ensemble_applied"] == 6
        assert report["overall_statistics"]["fallback_to_argmax"] == 4

    def test_dashboard_save_json(self, tmp_path):
        """대시보드 JSON 저장 확인"""
        reset_monitor()
        dashboard = MetricsDashboard(output_dir=str(tmp_path))

        dashboard.monitor.record_section(
            proposal_id="prop_001",
            section_id="sec_001",
            confidence=0.85,
            score=0.80,
            ensemble_applied=True,
        )

        filepath = dashboard.save_dashboard_json()

        assert filepath.exists()
        with open(filepath, encoding='utf-8') as f:
            data = json.load(f)
        assert "confidence_report" in data

    def test_text_report_generation(self):
        """텍스트 리포트 생성 확인"""
        dashboard = MetricsDashboard()

        for i in range(5):
            dashboard.monitor.record_section(
                proposal_id="prop_001",
                section_id=f"sec_{i}",
                confidence=0.75,
                score=0.70,
                ensemble_applied=True,
            )

        report = dashboard.generate_text_report()

        assert "ENSEMBLE VOTING METRICS DASHBOARD" in report
        assert "Confidence" in report
        assert "Feedback Loop" in report
        assert "Ensemble Voting" in report


class TestConfidenceAlerts:
    """신뢰도 경고 테스트"""

    def test_confidence_alerts(self):
        """낮은 신뢰도 경고 생성 확인"""
        monitor = EnsembleMetricsMonitor()

        # Add some low confidence sections
        monitor.record_section(
            proposal_id="prop_001",
            section_id="sec_001",
            confidence=0.50,
            score=0.60,
            ensemble_applied=True,
        )

        monitor.record_section(
            proposal_id="prop_001",
            section_id="sec_002",
            confidence=0.90,
            score=0.85,
            ensemble_applied=True,
        )

        dashboard = MetricsDashboard()
        dashboard.monitor = monitor

        alerts = dashboard.monitor.get_confidence_alerts(threshold=0.65)

        assert len(alerts) == 1
        assert alerts[0]["section_id"] == "sec_001"
        assert alerts[0]["confidence"] == 0.50


class TestFeedbackEffectiveness:
    """피드백 효율성 테스트"""

    def test_feedback_effectiveness(self):
        """피드백 효율성 분석 확인"""
        monitor = EnsembleMetricsMonitor()

        # Successful feedback
        for i in range(7):
            monitor.record_section(
                proposal_id="prop_001",
                section_id=f"sec_{i}",
                confidence=0.50,
                score=0.60,
                ensemble_applied=True,
                feedback_triggered=True,
                feedback_improved=True,
            )

        # Failed feedback
        for i in range(3):
            monitor.record_section(
                proposal_id="prop_001",
                section_id=f"sec_{i+7}",
                confidence=0.55,
                score=0.65,
                ensemble_applied=True,
                feedback_triggered=True,
                feedback_improved=False,
            )

        effectiveness = monitor.get_feedback_effectiveness()

        assert effectiveness["feedback_triggered"] == 10
        assert effectiveness["feedback_improved"] == 7
        assert round(effectiveness["effectiveness_pct"], 0) == 70.0


class TestGlobalMonitor:
    """글로벌 모니터 테스트"""

    def test_global_monitor(self):
        """글로벌 모니터 인스턴스 확인"""
        reset_monitor()

        monitor1 = get_global_monitor()
        monitor2 = get_global_monitor()

        # Should be same instance
        assert monitor1 is monitor2

        monitor1.record_section(
            proposal_id="prop_001",
            section_id="sec_001",
            confidence=0.85,
            score=0.80,
            ensemble_applied=True,
        )

        assert len(monitor2.section_metrics) == 1
