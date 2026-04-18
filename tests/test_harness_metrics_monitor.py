"""
harness_metrics_monitor 단위 테스트 (Phase 4)

테스트 범위:
1. 메트릭 기록 및 조회 (3개)
2. 메트릭 집계 (3개)
3. 트렌드 분석 (3개)
4. 품질 보고서 (2개)
5. 성능 저하 감지 (3개)
6. 데이터 내보내기 (1개)
"""

import pytest
from datetime import datetime, timedelta
from app.services.harness_metrics_monitor import (
    MetricsMonitoringService,
    MetricSnapshot,
    MetricsAggregation,
    AccuracyTrend
)


# ==================== Metric Recording Tests ====================

@pytest.fixture
def metrics_service():
    """MetricsMonitoringService 인스턴스"""
    return MetricsMonitoringService()


def test_record_metric_basic(metrics_service):
    """기본 메트릭 기록"""
    snapshot = metrics_service.record_metric(
        phase="phase_1",
        precision=0.25,
        recall=0.50,
        f1_score=0.33,
        false_positive_rate=0.9429,
        avg_latency_ms=500.0,
        p95_latency_ms=800.0,
        total_evaluations=100,
        processing_volume=50
    )

    assert snapshot.phase == "phase_1"
    assert snapshot.precision == 0.25
    assert snapshot.false_positive_rate == 0.9429
    assert len(metrics_service.metric_history) == 1


def test_record_multiple_metrics(metrics_service):
    """여러 메트릭 순차 기록"""
    phases = ["phase_1", "phase_2", "phase_3", "phase_4"]
    precisions = [0.25, 0.60, 0.85, 0.97]

    for phase, precision in zip(phases, precisions):
        metrics_service.record_metric(
            phase=phase,
            precision=precision,
            recall=precision - 0.05,
            f1_score=precision - 0.02,
            false_positive_rate=1 - precision,
            avg_latency_ms=500.0,
            p95_latency_ms=800.0,
            total_evaluations=100 * len(phases),
            processing_volume=50 * len(phases)
        )

    assert len(metrics_service.metric_history) == 4
    assert metrics_service.metric_history[0].phase == "phase_1"
    assert metrics_service.metric_history[-1].phase == "phase_4"


def test_get_phase_metrics(metrics_service):
    """Phase별 메트릭 조회"""
    metrics_service.record_metric(
        phase="phase_2",
        precision=0.60,
        recall=0.55,
        f1_score=0.57,
        false_positive_rate=0.40,
        avg_latency_ms=400.0,
        p95_latency_ms=650.0,
        total_evaluations=200,
        processing_volume=100
    )

    metric = metrics_service.get_phase_metrics("phase_2")

    assert metric is not None
    assert metric.phase == "phase_2"
    assert metric.precision == 0.60


# ==================== Metrics Aggregation Tests ====================

def test_aggregate_metrics_basic(metrics_service):
    """기본 메트릭 집계"""
    now = datetime.now()

    for i in range(3):
        metrics_service.record_metric(
            phase="phase_3",
            precision=0.85 + i * 0.01,
            recall=0.80 + i * 0.01,
            f1_score=0.82 + i * 0.01,
            false_positive_rate=0.15 - i * 0.02,
            avg_latency_ms=300.0,
            p95_latency_ms=500.0,
            total_evaluations=150,
            processing_volume=75
        )

    aggregation = metrics_service.aggregate_metrics(
        "daily",
        now - timedelta(hours=1),
        now + timedelta(hours=1)
    )

    assert len(aggregation.snapshots) == 3
    assert aggregation.get_avg_precision() > 0.85
    assert aggregation.get_total_volume() == 225


def test_aggregate_metrics_period_filtering(metrics_service):
    """기간별 메트릭 필터링"""
    now = datetime.now()

    # 과거 메트릭
    metrics_service.metric_history.append(MetricSnapshot(
        timestamp=now - timedelta(days=2),
        phase="phase_1",
        precision=0.25,
        recall=0.50,
        f1_score=0.33,
        false_positive_rate=0.9429,
        avg_latency_ms=500.0,
        p95_latency_ms=800.0,
        total_evaluations=100,
        processing_volume=50
    ))

    # 현재 메트릭
    metrics_service.record_metric(
        phase="phase_4",
        precision=0.97,
        recall=0.95,
        f1_score=0.96,
        false_positive_rate=0.08,
        avg_latency_ms=300.0,
        p95_latency_ms=500.0,
        total_evaluations=200,
        processing_volume=100
    )

    # 과거 1일 기간 집계
    agg_past = metrics_service.aggregate_metrics(
        "past",
        now - timedelta(days=3),
        now - timedelta(days=1)
    )

    # 현재 1시간 기간 집계
    agg_current = metrics_service.aggregate_metrics(
        "current",
        now - timedelta(hours=1),
        now + timedelta(hours=1)
    )

    assert len(agg_past.snapshots) == 1
    assert len(agg_current.snapshots) == 1
    assert agg_past.snapshots[0].phase == "phase_1"
    assert agg_current.snapshots[0].phase == "phase_4"


def test_aggregation_metric_calculations(metrics_service):
    """집계 메트릭 계산 검증"""
    now = datetime.now()

    metrics_service.record_metric(
        phase="phase_2",
        precision=0.60,
        recall=0.55,
        f1_score=0.57,
        false_positive_rate=0.40,
        avg_latency_ms=400.0,
        p95_latency_ms=650.0,
        total_evaluations=200,
        processing_volume=100
    )

    metrics_service.record_metric(
        phase="phase_2",
        precision=0.62,
        recall=0.57,
        f1_score=0.59,
        false_positive_rate=0.38,
        avg_latency_ms=420.0,
        p95_latency_ms=670.0,
        total_evaluations=210,
        processing_volume=110
    )

    agg = metrics_service.aggregate_metrics(
        "test",
        now - timedelta(hours=1),
        now + timedelta(hours=1)
    )

    assert agg.get_avg_precision() == pytest.approx(0.61, abs=0.01)
    assert agg.get_avg_recall() == pytest.approx(0.56, abs=0.01)
    assert agg.get_total_volume() == 210


# ==================== Accuracy Trend Tests ====================

def test_analyze_trend_improvement(metrics_service):
    """정확도 개선 트렌드 분석"""
    metrics_service.record_metric(
        phase="phase_3",
        precision=0.85,
        recall=0.82,
        f1_score=0.83,
        false_positive_rate=0.15,
        avg_latency_ms=300.0,
        p95_latency_ms=500.0,
        total_evaluations=150,
        processing_volume=75
    )

    trend = metrics_service.analyze_accuracy_trend("phase_3")

    assert trend is not None
    assert trend.phase == "phase_3"
    assert trend.improvement_percent > 0  # 기본값(0.85)과 비교해서 개선
    assert trend.trend_direction == "improving"


def test_analyze_trend_degradation(metrics_service):
    """정확도 저하 트렌드 분석"""
    metrics_service.record_metric(
        phase="phase_4",
        precision=0.90,  # 기본값 0.97 대비 감소
        recall=0.88,
        f1_score=0.89,
        false_positive_rate=0.10,  # 기본값 0.08 대비 증가
        avg_latency_ms=300.0,
        p95_latency_ms=500.0,
        total_evaluations=200,
        processing_volume=100
    )

    trend = metrics_service.analyze_accuracy_trend("phase_4")

    assert trend is not None
    assert trend.improvement_percent < 0  # 기본값보다 낮음
    assert trend.trend_direction == "degrading"


def test_trend_baseline_comparison(metrics_service):
    """트렌드 기본값 비교"""
    metrics_service.record_metric(
        phase="phase_1",
        precision=0.35,  # 기본값: 0.25
        recall=0.40,
        f1_score=0.37,
        false_positive_rate=0.85,  # 기본값: 0.9429
        avg_latency_ms=500.0,
        p95_latency_ms=800.0,
        total_evaluations=100,
        processing_volume=50
    )

    trend = metrics_service.analyze_accuracy_trend("phase_1")

    assert trend.baseline_precision == 0.25
    assert trend.current_precision == 0.35
    assert trend.improvement_percent > 0


# ==================== Quality Report Tests ====================

def test_quality_report_generation(metrics_service):
    """품질 보고서 생성"""
    # 각 Phase에 메트릭 추가
    phases = {
        "phase_1": {"precision": 0.25, "fpr": 0.9429},
        "phase_2": {"precision": 0.60, "fpr": 0.40},
        "phase_3": {"precision": 0.85, "fpr": 0.15},
        "phase_4": {"precision": 0.97, "fpr": 0.08}
    }

    for phase, metrics_dict in phases.items():
        metrics_service.record_metric(
            phase=phase,
            precision=metrics_dict["precision"],
            recall=metrics_dict["precision"] - 0.05,
            f1_score=metrics_dict["precision"] - 0.02,
            false_positive_rate=metrics_dict["fpr"],
            avg_latency_ms=300.0,
            p95_latency_ms=500.0,
            total_evaluations=100,
            processing_volume=50
        )

    report = metrics_service.get_quality_report()

    assert "timestamp" in report
    assert "total_evaluations" in report
    assert "overall_status" in report
    assert report["overall_status"] == "READY_FOR_PRODUCTION"


def test_quality_report_in_progress(metrics_service):
    """진행 중 품질 보고서"""
    # Phase 1만 추가 (다른 Phase는 없음)
    metrics_service.record_metric(
        phase="phase_1",
        precision=0.35,
        recall=0.40,
        f1_score=0.37,
        false_positive_rate=0.85,
        avg_latency_ms=500.0,
        p95_latency_ms=800.0,
        total_evaluations=100,
        processing_volume=50
    )

    report = metrics_service.get_quality_report()

    # Phase 1만 있으므로 IN_PROGRESS
    assert "phase_1" in report["phases"]
    assert "phase_4" not in report["phases"]  # Phase 4는 아직 없음


# ==================== Performance Degradation Detection Tests ====================

def test_detect_precision_degradation(metrics_service):
    """정밀도 저하 감지"""
    # 높은 정밀도로 시작
    for i in range(3):
        metrics_service.record_metric(
            phase="phase_4",
            precision=0.95,
            recall=0.93,
            f1_score=0.94,
            false_positive_rate=0.08,
            avg_latency_ms=300.0,
            p95_latency_ms=500.0,
            total_evaluations=200,
            processing_volume=100
        )

    # 정밀도 저하
    for i in range(2):
        metrics_service.record_metric(
            phase="phase_4",
            precision=0.88,  # 95% 미만
            recall=0.85,
            f1_score=0.86,
            false_positive_rate=0.12,
            avg_latency_ms=300.0,
            p95_latency_ms=500.0,
            total_evaluations=200,
            processing_volume=100
        )

    alerts = metrics_service.detect_performance_degradation()

    # 저하 감지되어야 함
    assert len(alerts) > 0
    assert any("Precision degradation" in alert for alert in alerts)


def test_detect_fpr_increase(metrics_service):
    """False Positive Rate 증가 감지"""
    # 낮은 FPR로 시작
    for i in range(3):
        metrics_service.record_metric(
            phase="phase_4",
            precision=0.95,
            recall=0.93,
            f1_score=0.94,
            false_positive_rate=0.08,
            avg_latency_ms=300.0,
            p95_latency_ms=500.0,
            total_evaluations=200,
            processing_volume=100
        )

    # FPR 증가
    for i in range(2):
        metrics_service.record_metric(
            phase="phase_4",
            precision=0.90,
            recall=0.88,
            f1_score=0.89,
            false_positive_rate=0.12,  # 8% -> 12% 증가
            avg_latency_ms=300.0,
            p95_latency_ms=500.0,
            total_evaluations=200,
            processing_volume=100
        )

    alerts = metrics_service.detect_performance_degradation()

    assert len(alerts) > 0
    assert any("False Positive Rate" in alert for alert in alerts)


def test_detect_latency_increase(metrics_service):
    """레이턴시 증가 감지"""
    # 낮은 레이턴시로 시작
    for i in range(3):
        metrics_service.record_metric(
            phase="phase_4",
            precision=0.95,
            recall=0.93,
            f1_score=0.94,
            false_positive_rate=0.08,
            avg_latency_ms=300.0,
            p95_latency_ms=500.0,
            total_evaluations=200,
            processing_volume=100
        )

    # 레이턴시 증가
    for i in range(2):
        metrics_service.record_metric(
            phase="phase_4",
            precision=0.95,
            recall=0.93,
            f1_score=0.94,
            false_positive_rate=0.08,
            avg_latency_ms=330.0,  # 300ms -> 330ms 증가
            p95_latency_ms=550.0,
            total_evaluations=200,
            processing_volume=100
        )

    alerts = metrics_service.detect_performance_degradation()

    assert len(alerts) > 0
    assert any("Latency increase" in alert for alert in alerts)


# ==================== Data Export Tests ====================

def test_export_metrics_to_dict(metrics_service):
    """메트릭 데이터 내보내기"""
    metrics_service.record_metric(
        phase="phase_2",
        precision=0.60,
        recall=0.55,
        f1_score=0.57,
        false_positive_rate=0.40,
        avg_latency_ms=400.0,
        p95_latency_ms=650.0,
        total_evaluations=200,
        processing_volume=100
    )

    exported = metrics_service.export_metrics_to_dict()

    assert exported["total_snapshots"] == 1
    assert len(exported["history"]) == 1
    assert exported["history"][0]["phase"] == "phase_2"
    assert exported["history"][0]["precision"] == 0.60
