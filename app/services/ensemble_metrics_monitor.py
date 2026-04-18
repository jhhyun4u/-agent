"""
STEP 4A Phase 3: Task 6 — Ensemble Metrics Monitor

모니터링 서비스: 앙상블 투표, 신뢰도, 피드백 루프 메트릭 추적
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class ConfidenceDistribution:
    """신뢰도 분포 추적"""
    high_count: int = 0      # confidence >= 0.80
    medium_count: int = 0    # 0.65 <= confidence < 0.80
    low_count: int = 0       # confidence < 0.65
    total_count: int = 0

    @property
    def high_percentage(self) -> float:
        return (self.high_count / self.total_count * 100) if self.total_count > 0 else 0.0

    @property
    def medium_percentage(self) -> float:
        return (self.medium_count / self.total_count * 100) if self.total_count > 0 else 0.0

    @property
    def low_percentage(self) -> float:
        return (self.low_count / self.total_count * 100) if self.total_count > 0 else 0.0

    def to_dict(self) -> Dict:
        return {
            "high": {"count": self.high_count, "percentage": round(self.high_percentage, 2)},
            "medium": {"count": self.medium_count, "percentage": round(self.medium_percentage, 2)},
            "low": {"count": self.low_count, "percentage": round(self.low_percentage, 2)},
            "total": self.total_count,
        }


@dataclass
class FeedbackLoopMetrics:
    """피드백 루프 트리거 메트릭"""
    triggered_count: int = 0
    not_triggered_count: int = 0
    improved_count: int = 0        # 피드백 후 개선된 경우
    not_improved_count: int = 0    # 피드백했지만 미개선
    total_proposals: int = 0

    @property
    def trigger_rate(self) -> float:
        return (self.triggered_count / self.total_proposals * 100) if self.total_proposals > 0 else 0.0

    @property
    def improvement_rate(self) -> float:
        return (self.improved_count / self.triggered_count * 100) if self.triggered_count > 0 else 0.0

    def to_dict(self) -> Dict:
        return {
            "triggered": self.triggered_count,
            "not_triggered": self.not_triggered_count,
            "trigger_rate_pct": round(self.trigger_rate, 2),
            "improved": self.improved_count,
            "not_improved": self.not_improved_count,
            "improvement_rate_pct": round(self.improvement_rate, 2),
            "total_proposals": self.total_proposals,
        }


@dataclass
class EnsembleApplicationMetrics:
    """앙상블 투표 적용 메트릭"""
    applied_count: int = 0       # 앙상블 투표 적용됨
    fallback_count: int = 0      # Argmax 폴백 (변형 부족 시)
    total_sections: int = 0

    @property
    def application_rate(self) -> float:
        return (self.applied_count / self.total_sections * 100) if self.total_sections > 0 else 0.0

    def to_dict(self) -> Dict:
        return {
            "applied": self.applied_count,
            "fallback": self.fallback_count,
            "application_rate_pct": round(self.application_rate, 2),
            "total_sections": self.total_sections,
        }


@dataclass
class LatencyMetrics:
    """섹션 생성 레이턴시 추적"""
    variant_generation_ms: float = 0.0    # 3변형 생성 시간
    ensemble_voting_ms: float = 0.0       # 앙상블 투표 시간
    feedback_loop_ms: float = 0.0         # 피드백 루프 시간
    total_section_ms: float = 0.0         # 전체 섹션 생성 시간

    def to_dict(self) -> Dict:
        return {
            "variant_generation_ms": round(self.variant_generation_ms, 2),
            "ensemble_voting_ms": round(self.ensemble_voting_ms, 2),
            "feedback_loop_ms": round(self.feedback_loop_ms, 2),
            "total_section_ms": round(self.total_section_ms, 2),
        }


@dataclass
class ProposalMetrics:
    """제안 별 메트릭"""
    proposal_id: str
    timestamp: str
    section_count: int
    confidence_avg: float              # 평균 신뢰도
    score_avg: float                   # 평균 점수
    ensemble_applied: bool             # 앙상블 사용 여부
    feedback_triggered: bool           # 피드백 루프 트리거 여부
    feedback_improved: bool            # 피드백으로 개선 여부
    avg_latency_ms: float = 0.0        # 평균 레이턴시 (ms)

    def to_dict(self) -> Dict:
        return {
            "proposal_id": self.proposal_id,
            "timestamp": self.timestamp,
            "section_count": self.section_count,
            "confidence_avg": round(self.confidence_avg, 4),
            "score_avg": round(self.score_avg, 4),
            "ensemble_applied": self.ensemble_applied,
            "feedback_triggered": self.feedback_triggered,
            "feedback_improved": self.feedback_improved,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
        }


@dataclass
class EnsembleMetricsMonitor:
    """
    앙상블 메트릭 모니터.
    실시간 제안 생성 중 메트릭을 수집하고 추적.
    """
    confidence_dist: ConfidenceDistribution = field(default_factory=ConfidenceDistribution)
    feedback_metrics: FeedbackLoopMetrics = field(default_factory=FeedbackLoopMetrics)
    ensemble_metrics: EnsembleApplicationMetrics = field(default_factory=EnsembleApplicationMetrics)
    proposal_history: List[ProposalMetrics] = field(default_factory=list)
    section_metrics: List[Dict] = field(default_factory=list)
    latency_history: List[Dict] = field(default_factory=list)  # 레이턴시 이력

    def record_section(
        self,
        proposal_id: str,
        section_id: str,
        confidence: float,
        score: float,
        ensemble_applied: bool,
        feedback_triggered: bool = False,
        feedback_improved: bool = False,
    ):
        """
        섹션 메트릭 기록.

        Args:
            proposal_id: 제안 ID
            section_id: 섹션 ID
            confidence: 신뢰도 (0-1)
            score: 최종 점수 (0-1)
            ensemble_applied: 앙상블 투표 사용 여부
            feedback_triggered: 피드백 루프 트리거 여부
            feedback_improved: 피드백으로 개선 여부
        """
        # 신뢰도 분포 업데이트
        self.confidence_dist.total_count += 1
        if confidence >= 0.80:
            self.confidence_dist.high_count += 1
        elif confidence >= 0.65:
            self.confidence_dist.medium_count += 1
        else:
            self.confidence_dist.low_count += 1

        # 피드백 루프 메트릭 업데이트
        if feedback_triggered:
            self.feedback_metrics.triggered_count += 1
            if feedback_improved:
                self.feedback_metrics.improved_count += 1
            else:
                self.feedback_metrics.not_improved_count += 1
        else:
            self.feedback_metrics.not_triggered_count += 1

        # 앙상블 적용 메트릭 업데이트
        self.ensemble_metrics.total_sections += 1
        if ensemble_applied:
            self.ensemble_metrics.applied_count += 1
        else:
            self.ensemble_metrics.fallback_count += 1

        # 섹션 메트릭 저장
        self.section_metrics.append({
            "proposal_id": proposal_id,
            "section_id": section_id,
            "timestamp": datetime.now().isoformat(),
            "confidence": round(confidence, 4),
            "score": round(score, 4),
            "ensemble_applied": ensemble_applied,
            "feedback_triggered": feedback_triggered,
            "feedback_improved": feedback_improved,
        })

    def record_proposal(
        self,
        proposal_id: str,
        section_count: int,
        confidences: List[float],
        scores: List[float],
        ensemble_applied: bool = True,
        feedback_triggered_count: int = 0,
    ):
        """
        제안 완료 메트릭 기록.

        Args:
            proposal_id: 제안 ID
            section_count: 섹션 수
            confidences: 각 섹션의 신뢰도 리스트
            scores: 각 섹션의 점수 리스트
            ensemble_applied: 이 제안에서 앙상블 사용 여부
            feedback_triggered_count: 피드백 루프 트리거된 섹션 수
        """
        self.feedback_metrics.total_proposals += 1

        confidence_avg = sum(confidences) / len(confidences) if confidences else 0.0
        score_avg = sum(scores) / len(scores) if scores else 0.0

        proposal_metric = ProposalMetrics(
            proposal_id=proposal_id,
            timestamp=datetime.now().isoformat(),
            section_count=section_count,
            confidence_avg=confidence_avg,
            score_avg=score_avg,
            ensemble_applied=ensemble_applied,
            feedback_triggered=feedback_triggered_count > 0,
            feedback_improved=False,  # Will be updated after feedback
        )

        self.proposal_history.append(proposal_metric)

        logger.info(
            f"Proposal {proposal_id}: sections={section_count}, "
            f"conf_avg={confidence_avg:.4f}, score_avg={score_avg:.4f}, "
            f"ensemble={ensemble_applied}, feedback_triggered={feedback_triggered_count}"
        )

    def record_latency(
        self,
        proposal_id: str,
        section_id: str,
        variant_generation_ms: float = 0.0,
        ensemble_voting_ms: float = 0.0,
        feedback_loop_ms: float = 0.0,
        total_section_ms: float = 0.0,
    ):
        """
        섹션 생성 레이턴시 기록.

        Args:
            proposal_id: 제안 ID
            section_id: 섹션 ID
            variant_generation_ms: 변형 생성 시간 (ms)
            ensemble_voting_ms: 앙상블 투표 시간 (ms)
            feedback_loop_ms: 피드백 루프 시간 (ms)
            total_section_ms: 전체 섹션 생성 시간 (ms)
        """
        latency_metric = {
            "proposal_id": proposal_id,
            "section_id": section_id,
            "timestamp": datetime.now().isoformat(),
            "variant_generation_ms": round(variant_generation_ms, 2),
            "ensemble_voting_ms": round(ensemble_voting_ms, 2),
            "feedback_loop_ms": round(feedback_loop_ms, 2),
            "total_section_ms": round(total_section_ms, 2),
        }
        self.latency_history.append(latency_metric)

        # 알림: >25초 (25,000ms) 레이턴시
        if total_section_ms > 25000:
            logger.warning(
                f"⚠️  높은 레이턴시 감지: {section_id} = {total_section_ms/1000:.1f}초 "
                f"(target: <21s)"
            )

    def get_latency_statistics(self) -> Dict:
        """
        레이턴시 통계 반환.
        """
        if not self.latency_history:
            return {
                "message": "No latency data yet",
                "total_sections": 0,
                "avg_total_ms": 0.0,
                "max_total_ms": 0.0,
                "min_total_ms": 0.0,
                "p95_total_ms": 0.0,
                "sections_over_25s": 0,
            }

        total_latencies = [m["total_section_ms"] for m in self.latency_history]
        variant_latencies = [m["variant_generation_ms"] for m in self.latency_history]
        ensemble_latencies = [m["ensemble_voting_ms"] for m in self.latency_history]

        # 상위 5% 레이턴시 계산
        sorted_total = sorted(total_latencies)
        p95_index = max(0, int(len(sorted_total) * 0.95) - 1)
        p95_latency = sorted_total[p95_index] if sorted_total else 0.0

        over_25s = sum(1 for l in total_latencies if l > 25000)

        return {
            "total_sections": len(self.latency_history),
            "avg_total_ms": round(sum(total_latencies) / len(total_latencies), 2),
            "max_total_ms": round(max(total_latencies), 2),
            "min_total_ms": round(min(total_latencies), 2),
            "p95_total_ms": round(p95_latency, 2),
            "avg_variant_generation_ms": round(sum(variant_latencies) / len(variant_latencies) if variant_latencies else 0, 2),
            "avg_ensemble_voting_ms": round(sum(ensemble_latencies) / len(ensemble_latencies) if ensemble_latencies else 0, 2),
            "sections_over_25s": over_25s,
            "target_under_21s": f"{len([l for l in total_latencies if l < 21000])} / {len(total_latencies)}",
        }

    def get_summary(self) -> Dict:
        """
        현재 메트릭 요약 반환.
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "confidence_distribution": self.confidence_dist.to_dict(),
            "feedback_loop": self.feedback_metrics.to_dict(),
            "ensemble_application": self.ensemble_metrics.to_dict(),
            "proposal_count": len(self.proposal_history),
            "section_count": len(self.section_metrics),
            "latency_statistics": self.get_latency_statistics(),
        }

    def get_proposal_details(self, proposal_id: str) -> Optional[Dict]:
        """
        특정 제안의 상세 메트릭 조회.
        """
        for proposal_metric in self.proposal_history:
            if proposal_metric.proposal_id == proposal_id:
                return proposal_metric.to_dict()
        return None

    def get_confidence_alerts(self, threshold: float = 0.65) -> List[Dict]:
        """
        신뢰도가 낮은 섹션 경고 목록 반환.

        Args:
            threshold: 경고 임계값 (기본: 0.65)

        Returns:
            신뢰도가 낮은 섹션 리스트
        """
        return [
            {
                "proposal_id": m["proposal_id"],
                "section_id": m["section_id"],
                "confidence": m["confidence"],
                "score": m["score"],
                "requires_feedback": m["feedback_triggered"],
            }
            for m in self.section_metrics
            if m["confidence"] < threshold
        ]

    def get_feedback_effectiveness(self) -> Dict:
        """
        피드백 루프 효율성 분석.
        """
        if self.feedback_metrics.triggered_count == 0:
            return {
                "feedback_triggered": 0,
                "feedback_improved": 0,
                "effectiveness": 0.0,
                "message": "No feedback loop triggered yet"
            }

        effectiveness = (
            self.feedback_metrics.improved_count / self.feedback_metrics.triggered_count * 100
        )

        return {
            "feedback_triggered": self.feedback_metrics.triggered_count,
            "feedback_improved": self.feedback_metrics.improved_count,
            "effectiveness_pct": round(effectiveness, 2),
            "message": (
                f"Feedback improved {self.feedback_metrics.improved_count}/{self.feedback_metrics.triggered_count} cases"
            )
        }

    def export_metrics_json(self) -> Dict:
        """
        전체 메트릭을 JSON 형식으로 내보내기.
        """
        return {
            "export_timestamp": datetime.now().isoformat(),
            "summary": self.get_summary(),
            "proposals": [p.to_dict() for p in self.proposal_history],
            "sections": self.section_metrics,
            "alerts": {
                "low_confidence": self.get_confidence_alerts(),
                "feedback_effectiveness": self.get_feedback_effectiveness(),
            }
        }


# 글로벌 모니터 인스턴스
_global_monitor: Optional[EnsembleMetricsMonitor] = None


def get_global_monitor() -> EnsembleMetricsMonitor:
    """글로벌 모니터 인스턴스 반환."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = EnsembleMetricsMonitor()
    return _global_monitor


def reset_monitor():
    """모니터 리셋 (테스트용)."""
    global _global_monitor
    _global_monitor = None
