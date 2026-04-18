"""
STEP 4A Gap 3: Feedback Analysis & Weight Adjustment Tool

주간 피드백 검토를 위한 자동 분석 도구
- 피드백 수집 및 집계
- 섹션별 분석
- 가중치 조정 권장사항 생성
"""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from statistics import mean, stdev

logger = logging.getLogger(__name__)


@dataclass
class FeedbackStats:
    """피드백 통계"""
    section_type: str
    total_feedback: int
    approved: int
    rejected: int
    approval_rate: float
    avg_hallucination_rating: float
    avg_persuasiveness_rating: float
    avg_completeness_rating: float
    avg_clarity_rating: float

    def to_dict(self) -> Dict:
        return {
            "section_type": self.section_type,
            "total_feedback": self.total_feedback,
            "approved": self.approved,
            "rejected": self.rejected,
            "approval_rate": round(self.approval_rate, 2),
            "avg_hallucination": round(self.avg_hallucination_rating, 2),
            "avg_persuasiveness": round(self.avg_persuasiveness_rating, 2),
            "avg_completeness": round(self.avg_completeness_rating, 2),
            "avg_clarity": round(self.avg_clarity_rating, 2),
        }


@dataclass
class WeightRecommendation:
    """가중치 조정 권장사항"""
    section_type: str
    hallucination: Optional[float] = None
    persuasiveness: Optional[float] = None
    completeness: Optional[float] = None
    clarity: Optional[float] = None
    reasoning: Optional[str] = None
    expected_impact: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "section_type": self.section_type,
            "recommended_weights": {
                "hallucination": round(self.hallucination, 2) if self.hallucination else None,
                "persuasiveness": round(self.persuasiveness, 2) if self.persuasiveness else None,
                "completeness": round(self.completeness, 2) if self.completeness else None,
                "clarity": round(self.clarity, 2) if self.clarity else None,
            },
            "reasoning": self.reasoning,
            "expected_impact": self.expected_impact,
        }


class FeedbackAnalyzer:
    """
    주간 피드백 분석 및 가중치 권장사항 생성기.
    """

    def __init__(self):
        self.logger = logger

    def analyze_weekly_feedback(self, feedback_entries: List[Dict]) -> Dict:
        """
        주간 피드백 분석.

        Args:
            feedback_entries: 피드백 항목 리스트

        Returns:
            분석 결과
        """
        if not feedback_entries:
            return {
                "message": "No feedback data for analysis",
                "stats": [],
                "recommendations": [],
            }

        # 섹션별 그룹화
        by_section = self._group_by_section(feedback_entries)

        # 통계 계산
        stats = []
        for section_type, entries in by_section.items():
            stat = self._calculate_stats(section_type, entries)
            stats.append(stat)

        # 가중치 권장사항 생성
        recommendations = self._generate_recommendations(stats)

        return {
            "period": "weekly",
            "analysis_date": datetime.now().isoformat(),
            "total_feedback": len(feedback_entries),
            "section_stats": [s.to_dict() for s in stats],
            "weight_recommendations": [r.to_dict() for r in recommendations],
            "summary": self._generate_summary(stats, recommendations),
        }

    def _group_by_section(self, entries: List[Dict]) -> Dict[str, List[Dict]]:
        """섹션별로 피드백 그룹화."""
        grouped = {}
        for entry in entries:
            section_type = entry.get("section_type", "unknown")
            if section_type not in grouped:
                grouped[section_type] = []
            grouped[section_type].append(entry)
        return grouped

    def _calculate_stats(self, section_type: str, entries: List[Dict]) -> FeedbackStats:
        """섹션별 통계 계산."""
        approved = sum(1 for e in entries if e.get("decision") == "APPROVE")
        rejected = len(entries) - approved

        hallucination_ratings = [
            e.get("ratings", {}).get("hallucination", 3)
            for e in entries
            if "ratings" in e
        ]
        persuasiveness_ratings = [
            e.get("ratings", {}).get("persuasiveness", 3)
            for e in entries
            if "ratings" in e
        ]
        completeness_ratings = [
            e.get("ratings", {}).get("completeness", 3)
            for e in entries
            if "ratings" in e
        ]
        clarity_ratings = [
            e.get("ratings", {}).get("clarity", 3)
            for e in entries
            if "ratings" in e
        ]

        total = len(entries)
        approval_rate = approved / total if total > 0 else 0.0

        return FeedbackStats(
            section_type=section_type,
            total_feedback=total,
            approved=approved,
            rejected=rejected,
            approval_rate=approval_rate,
            avg_hallucination_rating=mean(hallucination_ratings) if hallucination_ratings else 3.0,
            avg_persuasiveness_rating=mean(persuasiveness_ratings) if persuasiveness_ratings else 3.0,
            avg_completeness_rating=mean(completeness_ratings) if completeness_ratings else 3.0,
            avg_clarity_rating=mean(clarity_ratings) if clarity_ratings else 3.0,
        )

    def _generate_recommendations(self, stats: List[FeedbackStats]) -> List[WeightRecommendation]:
        """가중치 조정 권장사항 생성."""
        recommendations = []

        for stat in stats:
            hallucination_weight = 0.90  # 기본값
            persuasiveness_weight = 0.85
            completeness_weight = 0.88
            clarity_weight = 0.87
            reasoning_parts = []
            impact = "Neutral"

            # Hallucination (Factual Accuracy) - 낮은 점수 = 더 엄격한 필터 필요
            if stat.avg_hallucination_rating < 2.5:  # Low factual accuracy
                hallucination_weight = 0.95
                reasoning_parts.append(
                    f"Hallucination rating low ({stat.avg_hallucination_rating:.1f}/5), "
                    "increase filter strictness"
                )
            elif stat.avg_hallucination_rating > 4.0:  # High factual accuracy
                hallucination_weight = 0.85
                reasoning_parts.append(
                    f"Hallucination rating high ({stat.avg_hallucination_rating:.1f}/5), "
                    "can relax filter"
                )

            # Persuasiveness - 낮은 점수 = 더 강한 주장 필요
            if stat.avg_persuasiveness_rating < 2.5:
                persuasiveness_weight = 0.90
                reasoning_parts.append(
                    f"Persuasiveness low ({stat.avg_persuasiveness_rating:.1f}/5), "
                    "increase focus on compelling arguments"
                )

            # Completeness - 낮은 점수 = 더 상세한 내용 필요
            if stat.avg_completeness_rating < 2.5:
                completeness_weight = 0.93
                reasoning_parts.append(
                    f"Completeness low ({stat.avg_completeness_rating:.1f}/5), "
                    "increase emphasis on thorough coverage"
                )

            # Clarity - 낮은 점수 = 더 명확한 표현 필요
            if stat.avg_clarity_rating < 2.5:
                clarity_weight = 0.92
                reasoning_parts.append(
                    f"Clarity low ({stat.avg_clarity_rating:.1f}/5), "
                    "improve readability and structure"
                )

            # 승인률 기반 전체 평가
            if stat.approval_rate > 0.90:
                impact = "Minimal adjustment needed - High approval rate"
            elif stat.approval_rate < 0.70:
                impact = "Significant improvement potential - Low approval rate"
            else:
                impact = "Moderate adjustment expected"

            if reasoning_parts:
                reasoning = "; ".join(reasoning_parts)
            else:
                reasoning = "Maintain current weights - Good overall performance"

            recommendation = WeightRecommendation(
                section_type=stat.section_type,
                hallucination=hallucination_weight,
                persuasiveness=persuasiveness_weight,
                completeness=completeness_weight,
                clarity=clarity_weight,
                reasoning=reasoning,
                expected_impact=impact,
            )
            recommendations.append(recommendation)

        return recommendations

    def _generate_summary(
        self, stats: List[FeedbackStats], recommendations: List[WeightRecommendation]
    ) -> Dict:
        """분석 요약 생성."""
        total_feedback = sum(s.total_feedback for s in stats)
        total_approved = sum(s.approved for s in stats)
        overall_approval_rate = total_approved / total_feedback if total_feedback > 0 else 0.0

        # 가장 문제가 있는 섹션
        worst_sections = sorted(stats, key=lambda s: s.approval_rate)[:3]
        worst_section_names = [s.section_type for s in worst_sections if s.approval_rate < 0.90]

        # 가장 잘된 섹션
        best_sections = sorted(stats, key=lambda s: s.approval_rate, reverse=True)[:3]
        best_section_names = [s.section_type for s in best_sections if s.approval_rate >= 0.90]

        return {
            "total_feedback_collected": total_feedback,
            "overall_approval_rate": round(overall_approval_rate, 2),
            "sections_needing_attention": worst_section_names,
            "sections_performing_well": best_section_names,
            "recommendations_count": len([r for r in recommendations if r.reasoning != "Maintain current weights - Good overall performance"]),
            "next_action": (
                "Deploy weight adjustments" if overall_approval_rate < 0.85
                else "Monitor next week" if overall_approval_rate > 0.90
                else "Minor adjustments recommended"
            ),
        }

    def get_feedback_analysis_report(self, feedback_entries: List[Dict]) -> str:
        """
        피드백 분석 텍스트 리포트 생성.

        Returns:
            텍스트 형식의 분석 리포트
        """
        analysis = self.analyze_weekly_feedback(feedback_entries)

        lines = [
            "=" * 80,
            "WEEKLY FEEDBACK ANALYSIS REPORT",
            "=" * 80,
            f"Date: {analysis['analysis_date']}",
            f"Total Feedback: {analysis['total_feedback']}",
            "",
            "SECTION ANALYSIS",
            "-" * 80,
        ]

        for stat_dict in analysis["section_stats"]:
            lines.extend([
                f"\n[{stat_dict['section_type'].upper()}]",
                f"  Total: {stat_dict['total_feedback']} "
                f"(Approved: {stat_dict['approved']}, Rejected: {stat_dict['rejected']})",
                f"  Approval Rate: {stat_dict['approval_rate']*100:.1f}%",
                f"  Ratings: Hallucination={stat_dict['avg_hallucination']}/5, "
                f"Persuasiveness={stat_dict['avg_persuasiveness']}/5, "
                f"Completeness={stat_dict['avg_completeness']}/5, "
                f"Clarity={stat_dict['avg_clarity']}/5",
            ])

        lines.extend([
            "",
            "WEIGHT RECOMMENDATIONS",
            "-" * 80,
        ])

        for rec_dict in analysis["weight_recommendations"]:
            lines.extend([
                f"\n[{rec_dict['section_type'].upper()}]",
                f"  Recommended Weights:",
                f"    Hallucination: {rec_dict['recommended_weights']['hallucination']}",
                f"    Persuasiveness: {rec_dict['recommended_weights']['persuasiveness']}",
                f"    Completeness: {rec_dict['recommended_weights']['completeness']}",
                f"    Clarity: {rec_dict['recommended_weights']['clarity']}",
                f"  Reasoning: {rec_dict['reasoning']}",
                f"  Expected Impact: {rec_dict['expected_impact']}",
            ])

        summary = analysis["summary"]
        lines.extend([
            "",
            "SUMMARY",
            "-" * 80,
            f"Overall Approval Rate: {summary['overall_approval_rate']*100:.1f}%",
        ])

        if summary["sections_needing_attention"]:
            lines.append(
                f"Sections Needing Attention: {', '.join(summary['sections_needing_attention'])}"
            )
        if summary["sections_performing_well"]:
            lines.append(
                f"Sections Performing Well: {', '.join(summary['sections_performing_well'])}"
            )

        lines.extend([
            f"Next Action: {summary['next_action']}",
            "",
            "=" * 80,
        ])

        return "\n".join(lines)
