"""
STEP 4A Phase 3: Task 6 — Metrics Dashboard

대시보드 생성 및 리포트 서비스: 실시간 메트릭 시각화 및 분석
"""

import logging
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from app.services.ensemble_metrics_monitor import (
    get_global_monitor,
    EnsembleMetricsMonitor,
)

logger = logging.getLogger(__name__)


class MetricsDashboard:
    """
    메트릭 대시보드 생성 및 관리.
    실시간 모니터링 데이터를 시각화 가능한 형식으로 제공.
    """

    def __init__(self, output_dir: str = "metrics_reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.monitor = get_global_monitor()

    def generate_confidence_report(self) -> Dict:
        """신뢰도 분석 리포트 생성."""
        conf_dist = self.monitor.confidence_dist

        return {
            "title": "Confidence Distribution Report",
            "timestamp": datetime.now().isoformat(),
            "overall_statistics": {
                "total_sections": conf_dist.total_count,
                "high_confidence": {
                    "count": conf_dist.high_count,
                    "percentage": round(conf_dist.high_percentage, 2),
                    "threshold": ">= 0.80",
                },
                "medium_confidence": {
                    "count": conf_dist.medium_count,
                    "percentage": round(conf_dist.medium_percentage, 2),
                    "threshold": "0.65 - 0.80",
                },
                "low_confidence": {
                    "count": conf_dist.low_count,
                    "percentage": round(conf_dist.low_percentage, 2),
                    "threshold": "< 0.65",
                },
            },
            "alerts": {
                "total_low_confidence": conf_dist.low_count,
                "requires_attention": conf_dist.low_percentage > 20.0,
                "message": (
                    f"{conf_dist.low_count} sections ({round(conf_dist.low_percentage, 1)}%) "
                    f"have low confidence (< 0.65)"
                ) if conf_dist.low_count > 0 else "All sections have good confidence levels",
            },
            "recommendations": self._get_confidence_recommendations(conf_dist),
        }

    def _get_confidence_recommendations(self, conf_dist) -> List[str]:
        """신뢰도 기반 권장사항 생성."""
        recommendations = []

        low_pct = conf_dist.low_percentage
        if low_pct > 30.0:
            recommendations.append(
                "⚠️ High proportion of low-confidence predictions (>30%). "
                "Consider reviewing variant generation or increasing feedback loops."
            )
        elif low_pct > 20.0:
            recommendations.append(
                "📊 Significant low-confidence sections (20-30%). "
                "Monitor feedback loop effectiveness."
            )

        high_pct = conf_dist.high_percentage
        if high_pct > 70.0:
            recommendations.append(
                "✅ Strong confidence levels (>70% high confidence). "
                "System is operating with high agreement between variants."
            )

        if conf_dist.total_count == 0:
            recommendations.append("No data yet. Start generating proposals to populate metrics.")

        return recommendations

    def generate_feedback_report(self) -> Dict:
        """피드백 루프 효율성 리포트 생성."""
        fb_metrics = self.monitor.feedback_metrics

        return {
            "title": "Feedback Loop Report",
            "timestamp": datetime.now().isoformat(),
            "overall_statistics": {
                "total_proposals": fb_metrics.total_proposals,
                "feedback_triggered": fb_metrics.triggered_count,
                "trigger_rate_pct": round(fb_metrics.trigger_rate, 2),
                "feedback_improved": fb_metrics.improved_count,
                "feedback_not_improved": fb_metrics.not_improved_count,
                "improvement_rate_pct": round(fb_metrics.improvement_rate, 2),
            },
            "effectiveness_analysis": {
                "triggered_loops": fb_metrics.triggered_count,
                "successful_improvements": fb_metrics.improved_count,
                "effectiveness": round(fb_metrics.improvement_rate, 2),
                "message": (
                    f"Feedback loop improved {fb_metrics.improved_count}/{fb_metrics.triggered_count} cases "
                    f"({round(fb_metrics.improvement_rate, 1)}% success rate)"
                ) if fb_metrics.triggered_count > 0 else "Feedback loop has not been triggered yet",
            },
            "recommendations": self._get_feedback_recommendations(fb_metrics),
        }

    def _get_feedback_recommendations(self, fb_metrics) -> List[str]:
        """피드백 루프 기반 권장사항 생성."""
        recommendations = []

        if fb_metrics.total_proposals == 0:
            recommendations.append("No proposals generated yet. Metrics will appear after first proposal.")
            return recommendations

        trigger_rate = fb_metrics.trigger_rate
        if trigger_rate > 50.0:
            recommendations.append(
                f"⚠️ High feedback loop trigger rate ({trigger_rate:.1f}%). "
                "Many proposals are triggering feedback loops. "
                "Review variant generation quality or adjust confidence thresholds."
            )
        elif trigger_rate < 10.0:
            recommendations.append(
                f"✅ Low feedback trigger rate ({trigger_rate:.1f}%). "
                "Most proposals are confident. Consider slightly increasing sensitivity."
            )
        else:
            recommendations.append(
                f"📊 Moderate feedback rate ({trigger_rate:.1f}%). "
                "System is balanced between confidence and improvement."
            )

        if fb_metrics.triggered_count > 0:
            improve_rate = fb_metrics.improvement_rate
            if improve_rate > 75.0:
                recommendations.append(
                    f"✅ High feedback effectiveness ({improve_rate:.1f}%). "
                    "Feedback loops are successfully improving proposals."
                )
            elif improve_rate < 30.0:
                recommendations.append(
                    f"⚠️ Low feedback effectiveness ({improve_rate:.1f}%). "
                    "Consider reviewing feedback prompt or regeneration logic."
                )

        return recommendations

    def generate_ensemble_report(self) -> Dict:
        """앙상블 투표 적용 리포트 생성."""
        ens_metrics = self.monitor.ensemble_metrics

        return {
            "title": "Ensemble Voting Report",
            "timestamp": datetime.now().isoformat(),
            "overall_statistics": {
                "total_sections": ens_metrics.total_sections,
                "ensemble_applied": ens_metrics.applied_count,
                "application_rate_pct": round(ens_metrics.application_rate, 2),
                "fallback_to_argmax": ens_metrics.fallback_count,
            },
            "application_analysis": {
                "applied": ens_metrics.applied_count,
                "fallback": ens_metrics.fallback_count,
                "application_rate": round(ens_metrics.application_rate, 2),
                "message": (
                    f"Ensemble voting applied to {ens_metrics.applied_count}/{ens_metrics.total_sections} sections "
                    f"({round(ens_metrics.application_rate, 1)}%) - "
                    f"{ens_metrics.fallback_count} sections using argmax fallback"
                ) if ens_metrics.total_sections > 0 else "No sections processed yet",
            },
            "recommendations": self._get_ensemble_recommendations(ens_metrics),
        }

    def _get_ensemble_recommendations(self, ens_metrics) -> List[str]:
        """앙상블 투표 기반 권장사항 생성."""
        recommendations = []

        if ens_metrics.total_sections == 0:
            recommendations.append("No sections processed yet. Metrics will appear after first proposal.")
            return recommendations

        app_rate = ens_metrics.application_rate
        if app_rate < 80.0:
            recommendations.append(
                f"⚠️ Low ensemble application rate ({app_rate:.1f}%). "
                f"Many sections are falling back to argmax. "
                f"Review variant generation to ensure 3 variants with details are always provided."
            )
        else:
            recommendations.append(
                f"✅ High ensemble application rate ({app_rate:.1f}%). "
                f"System is successfully using ensemble voting."
            )

        return recommendations

    def generate_comprehensive_dashboard(self) -> Dict:
        """종합 대시보드 생성."""
        return {
            "report_generated": datetime.now().isoformat(),
            "confidence_report": self.generate_confidence_report(),
            "feedback_report": self.generate_feedback_report(),
            "ensemble_report": self.generate_ensemble_report(),
            "summary_metrics": self.monitor.get_summary(),
        }

    def save_dashboard_json(self, filename: str = "metrics_dashboard.json"):
        """대시보드를 JSON 파일로 저장."""
        dashboard = self.generate_comprehensive_dashboard()
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(dashboard, f, indent=2, ensure_ascii=False)

        logger.info(f"Dashboard saved: {filepath}")
        return filepath

    def save_detailed_export(self, filename: str = "metrics_detailed_export.json"):
        """상세 메트릭 내보내기."""
        export_data = self.monitor.export_metrics_json()
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        logger.info(f"Detailed export saved: {filepath}")
        return filepath

    def generate_text_report(self) -> str:
        """텍스트 형식 리포트 생성."""
        dashboard = self.generate_comprehensive_dashboard()

        lines = [
            "=" * 80,
            "ENSEMBLE VOTING METRICS DASHBOARD",
            "=" * 80,
            f"Generated: {dashboard['report_generated']}\n",
        ]

        # Confidence Report
        conf_report = dashboard["confidence_report"]
        lines.extend([
            f"\n{conf_report['title']}",
            "-" * 80,
            f"Total Sections: {conf_report['overall_statistics']['total_sections']}",
            f"High Confidence (>= 0.80): {conf_report['overall_statistics']['high_confidence']['count']} "
            f"({conf_report['overall_statistics']['high_confidence']['percentage']}%)",
            f"Medium Confidence (0.65-0.80): {conf_report['overall_statistics']['medium_confidence']['count']} "
            f"({conf_report['overall_statistics']['medium_confidence']['percentage']}%)",
            f"Low Confidence (< 0.65): {conf_report['overall_statistics']['low_confidence']['count']} "
            f"({conf_report['overall_statistics']['low_confidence']['percentage']}%)",
            f"\nAlerts: {conf_report['alerts']['message']}",
        ])

        # Feedback Report
        fb_report = dashboard["feedback_report"]
        lines.extend([
            f"\n{fb_report['title']}",
            "-" * 80,
            f"Total Proposals: {fb_report['overall_statistics']['total_proposals']}",
            f"Feedback Triggered: {fb_report['overall_statistics']['feedback_triggered']} "
            f"({fb_report['overall_statistics']['trigger_rate_pct']}%)",
            f"Feedback Improved: {fb_report['overall_statistics']['feedback_improved']} "
            f"({fb_report['overall_statistics']['improvement_rate_pct']}% of triggered)",
            f"\nMessage: {fb_report['effectiveness_analysis']['message']}",
        ])

        # Ensemble Report
        ens_report = dashboard["ensemble_report"]
        lines.extend([
            f"\n{ens_report['title']}",
            "-" * 80,
            f"Total Sections: {ens_report['overall_statistics']['total_sections']}",
            f"Ensemble Applied: {ens_report['overall_statistics']['ensemble_applied']} "
            f"({ens_report['overall_statistics']['application_rate_pct']}%)",
            f"Fallback to Argmax: {ens_report['overall_statistics']['fallback_to_argmax']}",
            f"\nMessage: {ens_report['application_analysis']['message']}",
        ])

        lines.append("\n" + "=" * 80)
        return "\n".join(lines)

    def print_dashboard(self):
        """대시보드를 콘솔에 출력."""
        print(self.generate_text_report())
