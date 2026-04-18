"""
Phase 4 Integration Tests: Metrics Monitoring in Harness

메트릭 모니터링의 하네스 통합을 검증하는 테스트
"""

import pytest
from uuid import uuid4

from app.graph.state import ProposalState
from app.models.schemas import ProposalSection
from app.services.ensemble_metrics_monitor import (
    get_global_monitor,
    reset_monitor,
)


class TestHarnessMetricsIntegration:
    """하네스-메트릭 통합 테스트"""

    def setup_method(self):
        """각 테스트 전에 모니터 리셋"""
        reset_monitor()

    def _create_sample_state(self) -> dict:
        """샘플 ProposalState 생성"""
        return {
            "project_id": f"prop_{uuid4().hex[:8]}",
            "proposal_sections": [
                ProposalSection(
                    section_id="introduction",
                    title="Introduction",
                    content="Sample content",
                    version=1,
                    case_type="A",
                    harness_score=0.85,
                    harness_variant="balanced",
                    harness_improved=False,
                ),
                ProposalSection(
                    section_id="approach",
                    title="Approach",
                    content="Sample content",
                    version=1,
                    case_type="A",
                    harness_score=0.75,
                    harness_variant="creative",
                    harness_improved=True,
                ),
                ProposalSection(
                    section_id="timeline",
                    title="Timeline",
                    content="Sample content",
                    version=1,
                    case_type="A",
                    harness_score=0.80,
                    harness_variant="balanced",
                    harness_improved=False,
                ),
            ],
            "harness_results": {
                "introduction": {
                    "score": 0.85,
                    "confidence": 0.90,
                    "confidence_agreement": "HIGH",
                    "variant": "balanced",
                    "improved": False,
                    "ensemble_applied": True,
                    "feedback_triggered": False,
                },
                "approach": {
                    "score": 0.75,
                    "confidence": 0.70,
                    "confidence_agreement": "MEDIUM",
                    "variant": "creative",
                    "improved": True,
                    "ensemble_applied": True,
                    "feedback_triggered": True,
                },
                "timeline": {
                    "score": 0.80,
                    "confidence": 0.85,
                    "confidence_agreement": "HIGH",
                    "variant": "balanced",
                    "improved": False,
                    "ensemble_applied": True,
                    "feedback_triggered": False,
                },
            },
        }

    def test_harness_section_metrics_recording(self):
        """하네스 섹션 메트릭 기록 검증"""
        monitor = get_global_monitor()
        state = self._create_sample_state()
        proposal_id = state["project_id"]

        # 각 섹션 메트릭 시뮬레이션 기록
        for section in state["proposal_sections"]:
            section_id = section.section_id
            result = state["harness_results"][section_id]

            monitor.record_section(
                proposal_id=proposal_id,
                section_id=section_id,
                confidence=result["confidence"],
                score=result["score"],
                ensemble_applied=result["ensemble_applied"],
                feedback_triggered=result["feedback_triggered"],
            )

        # 검증
        assert len(monitor.section_metrics) == 3
        assert monitor.confidence_dist.total_count == 3
        assert monitor.confidence_dist.high_count == 2  # 0.90, 0.85
        assert monitor.confidence_dist.medium_count == 1  # 0.70
        assert monitor.confidence_dist.low_count == 0

    def test_harness_proposal_completion_metrics(self):
        """제안 완료 후 제안 메트릭 기록 검증"""
        monitor = get_global_monitor()
        state = self._create_sample_state()
        proposal_id = state["project_id"]

        # 섹션별 메트릭 기록
        confidences = []
        scores = []
        feedback_triggered_count = 0

        for section in state["proposal_sections"]:
            section_id = section.section_id
            result = state["harness_results"][section_id]

            confidences.append(result["confidence"])
            scores.append(result["score"])
            if result["feedback_triggered"]:
                feedback_triggered_count += 1

            monitor.record_section(
                proposal_id=proposal_id,
                section_id=section_id,
                confidence=result["confidence"],
                score=result["score"],
                ensemble_applied=result["ensemble_applied"],
                feedback_triggered=result["feedback_triggered"],
            )

        # 제안 메트릭 기록
        monitor.record_proposal(
            proposal_id=proposal_id,
            section_count=len(state["proposal_sections"]),
            confidences=confidences,
            scores=scores,
            ensemble_applied=True,
            feedback_triggered_count=feedback_triggered_count,
        )

        # 검증
        assert len(monitor.proposal_history) == 1
        proposal = monitor.proposal_history[0]
        assert proposal.proposal_id == proposal_id
        assert proposal.section_count == 3
        assert proposal.confidence_avg == sum(confidences) / len(confidences)
        assert proposal.score_avg == sum(scores) / len(scores)
        assert proposal.ensemble_applied is True
        assert proposal.feedback_triggered is True
        assert proposal.feedback_triggered

    def test_ensemble_application_tracking(self):
        """앙상블 적용 추적 검증"""
        monitor = get_global_monitor()
        state = self._create_sample_state()
        proposal_id = state["project_id"]

        for section in state["proposal_sections"]:
            section_id = section.section_id
            result = state["harness_results"][section_id]

            monitor.record_section(
                proposal_id=proposal_id,
                section_id=section_id,
                confidence=result["confidence"],
                score=result["score"],
                ensemble_applied=result["ensemble_applied"],
                feedback_triggered=result["feedback_triggered"],
            )

        # 모두 앙상블 적용됨
        assert monitor.ensemble_metrics.applied_count == 3
        assert monitor.ensemble_metrics.fallback_count == 0
        assert monitor.ensemble_metrics.application_rate == 100.0

    def test_confidence_distribution_tracking(self):
        """신뢰도 분포 추적 검증"""
        monitor = get_global_monitor()
        state = self._create_sample_state()
        proposal_id = state["project_id"]

        # HIGH, HIGH, MEDIUM 순서로 기록
        for section in state["proposal_sections"]:
            section_id = section.section_id
            result = state["harness_results"][section_id]

            monitor.record_section(
                proposal_id=proposal_id,
                section_id=section_id,
                confidence=result["confidence"],
                score=result["score"],
                ensemble_applied=result["ensemble_applied"],
                feedback_triggered=result["feedback_triggered"],
            )

        # 검증: HIGH(0.90, 0.85), MEDIUM(0.70)
        assert monitor.confidence_dist.high_count == 2
        assert monitor.confidence_dist.medium_count == 1
        assert monitor.confidence_dist.low_count == 0
        assert monitor.confidence_dist.high_percentage == pytest.approx(66.67, abs=0.1)

    def test_feedback_trigger_tracking(self):
        """피드백 트리거 추적 검증"""
        monitor = get_global_monitor()
        state = self._create_sample_state()
        proposal_id = state["project_id"]

        for section in state["proposal_sections"]:
            section_id = section.section_id
            result = state["harness_results"][section_id]

            monitor.record_section(
                proposal_id=proposal_id,
                section_id=section_id,
                confidence=result["confidence"],
                score=result["score"],
                ensemble_applied=result["ensemble_applied"],
                feedback_triggered=result["feedback_triggered"],
            )

        # 1개만 피드백 트리거됨
        assert monitor.feedback_metrics.triggered_count == 1
        assert monitor.feedback_metrics.not_triggered_count == 2

    def test_metrics_summary_generation(self):
        """메트릭 요약 생성 검증"""
        monitor = get_global_monitor()
        state = self._create_sample_state()
        proposal_id = state["project_id"]

        for section in state["proposal_sections"]:
            section_id = section.section_id
            result = state["harness_results"][section_id]

            monitor.record_section(
                proposal_id=proposal_id,
                section_id=section_id,
                confidence=result["confidence"],
                score=result["score"],
                ensemble_applied=result["ensemble_applied"],
                feedback_triggered=result["feedback_triggered"],
            )

        summary = monitor.get_summary()

        assert summary["section_count"] == 3
        assert summary["proposal_count"] == 0  # 제안 메트릭은 별도 기록
        assert "confidence_distribution" in summary
        assert "feedback_loop" in summary
        assert "ensemble_application" in summary
        assert summary["confidence_distribution"]["total"] == 3

    def test_threshold_based_alerts(self):
        """임계값 기반 경고 생성 검증"""
        monitor = get_global_monitor()
        state = self._create_sample_state()
        proposal_id = state["project_id"]

        # 낮은 신뢰도 섹션 추가
        monitor.record_section(
            proposal_id=proposal_id,
            section_id="low_confidence_section",
            confidence=0.50,
            score=0.60,
            ensemble_applied=False,
            feedback_triggered=True,
        )

        # 신뢰도 경고 조회 (threshold=0.65)
        alerts = monitor.get_confidence_alerts(threshold=0.65)

        # 1개의 낮은 신뢰도 섹션이 감지되어야 함
        assert len(alerts) == 1
        assert alerts[0]["section_id"] == "low_confidence_section"
        assert alerts[0]["confidence"] == 0.50

    def test_multiple_proposals_tracking(self):
        """여러 제안에 대한 독립적 추적"""
        monitor = get_global_monitor()

        # 제안 1
        proposal_id_1 = "prop_001"
        monitor.record_section(
            proposal_id=proposal_id_1,
            section_id="sec_001",
            confidence=0.85,
            score=0.80,
            ensemble_applied=True,
        )

        # 제안 2
        proposal_id_2 = "prop_002"
        monitor.record_section(
            proposal_id=proposal_id_2,
            section_id="sec_001",
            confidence=0.50,
            score=0.60,
            ensemble_applied=False,
        )

        # 모두 집계되어야 함
        assert monitor.confidence_dist.total_count == 2
        assert monitor.confidence_dist.high_count == 1
        assert monitor.confidence_dist.low_count == 1
        assert len(monitor.section_metrics) == 2

    def test_confidence_thresholds(self):
        """신뢰도 임계값별 분류 검증"""
        monitor = get_global_monitor()

        test_cases = [
            (0.85, "HIGH"),   # >= 0.80
            (0.75, "MEDIUM"), # 0.65-0.80
            (0.50, "LOW"),    # < 0.65
        ]

        for confidence, expected_level in test_cases:
            monitor.record_section(
                proposal_id="test_prop",
                section_id=f"sec_{expected_level}",
                confidence=confidence,
                score=0.70,
                ensemble_applied=True,
            )

        assert monitor.confidence_dist.high_count == 1
        assert monitor.confidence_dist.medium_count == 1
        assert monitor.confidence_dist.low_count == 1
