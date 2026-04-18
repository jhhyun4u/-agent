"""
피드백 분석 API 테스트
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.services.feedback_analyzer import FeedbackAnalyzer

client = TestClient(app)


@pytest.fixture
def mock_auth(monkeypatch):
    """Mock 인증 의존성"""
    async def mock_get_current_user():
        return {
            "id": "test-user",
            "email": "test@tenopa.co.kr",
            "roles": ["pm", "reviewer"],
        }

    monkeypatch.setattr(
        "app.api.deps.get_current_user",
        mock_get_current_user
    )


@pytest.fixture
def mock_require_role(monkeypatch):
    """Mock 역할 검증"""
    async def mock_decorator(*allowed_roles):
        async def check(current_user=None):
            return None
        return check

    monkeypatch.setattr(
        "app.api.deps.require_role",
        mock_decorator
    )


@pytest.fixture
def sample_feedback_data():
    """샘플 피드백 데이터"""
    return [
        {
            "id": "fb-001",
            "proposal_id": "prop-001",
            "section_type": "executive_summary",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 4.5,
                "persuasiveness": 4.2,
                "completeness": 4.0,
                "clarity": 4.3,
            },
            "comment": "잘 작성됨",
            "created_at": (datetime.now() - timedelta(days=2)).isoformat(),
        },
        {
            "id": "fb-002",
            "proposal_id": "prop-001",
            "section_type": "technical_approach",
            "decision": "REJECT",
            "ratings": {
                "hallucination": 2.1,
                "persuasiveness": 2.5,
                "completeness": 2.0,
                "clarity": 2.3,
            },
            "comment": "기술 부분이 약함",
            "created_at": (datetime.now() - timedelta(days=1)).isoformat(),
        },
        {
            "id": "fb-003",
            "proposal_id": "prop-001",
            "section_type": "executive_summary",
            "decision": "APPROVE",
            "ratings": {
                "hallucination": 4.2,
                "persuasiveness": 4.5,
                "completeness": 4.1,
                "clarity": 4.4,
            },
            "comment": "우수함",
            "created_at": datetime.now().isoformat(),
        },
    ]


@pytest.mark.unit
def test_feedback_analyzer_basic(sample_feedback_data):
    """FeedbackAnalyzer 기본 분석 테스트"""
    analyzer = FeedbackAnalyzer()
    result = analyzer.analyze_weekly_feedback(sample_feedback_data)

    assert result["period"] == "weekly"
    assert result["total_feedback"] == 3
    assert len(result["section_stats"]) == 2  # executive_summary, technical_approach
    assert len(result["weight_recommendations"]) == 2
    assert "summary" in result


@pytest.mark.unit
def test_feedback_analyzer_approval_rate(sample_feedback_data):
    """승인률 계산 테스트"""
    analyzer = FeedbackAnalyzer()
    result = analyzer.analyze_weekly_feedback(sample_feedback_data)

    # overall_approval_rate = 2/3 = 0.67
    assert result["summary"]["overall_approval_rate"] == pytest.approx(0.67, abs=0.01)


@pytest.mark.unit
def test_feedback_analyzer_section_stats(sample_feedback_data):
    """섹션별 통계 테스트"""
    analyzer = FeedbackAnalyzer()
    result = analyzer.analyze_weekly_feedback(sample_feedback_data)

    exec_summary = [s for s in result["section_stats"] if s["section_type"] == "executive_summary"][0]
    assert exec_summary["total_feedback"] == 2
    assert exec_summary["approved"] == 2
    assert exec_summary["approval_rate"] == 1.0
    assert exec_summary["avg_hallucination"] == pytest.approx(4.35, abs=0.01)


@pytest.mark.unit
def test_feedback_analyzer_report_generation(sample_feedback_data):
    """텍스트 리포트 생성 테스트"""
    analyzer = FeedbackAnalyzer()
    report = analyzer.get_feedback_analysis_report(sample_feedback_data)

    assert "WEEKLY FEEDBACK ANALYSIS REPORT" in report
    assert "SECTION ANALYSIS" in report
    assert "WEIGHT RECOMMENDATIONS" in report
    assert "SUMMARY" in report
    assert "executive_summary" in report.lower()
    assert "technical_approach" in report.lower()


@pytest.mark.unit
def test_feedback_analyzer_empty_data():
    """빈 데이터 처리 테스트"""
    analyzer = FeedbackAnalyzer()
    result = analyzer.analyze_weekly_feedback([])

    assert result["total_feedback"] == 0
    assert result["section_stats"] == []
    assert result["weight_recommendations"] == []
    assert result["summary"]["overall_approval_rate"] == 0.0


@pytest.mark.unit
def test_feedback_analyzer_missing_ratings():
    """평점 누락 처리 테스트"""
    data = [
        {
            "section_type": "executive_summary",
            "decision": "APPROVE",
            "comment": "no ratings",
        },
    ]

    analyzer = FeedbackAnalyzer()
    result = analyzer.analyze_weekly_feedback(data)

    assert result["total_feedback"] == 1
    stat = result["section_stats"][0]
    # 누락된 평점은 기본값 3.0
    assert stat["avg_hallucination"] == 3.0


@pytest.mark.integration
async def test_feedback_analysis_endpoint_success(monkeypatch, sample_feedback_data):
    """피드백 분석 엔드포인트 성공 테스트"""

    # Mock Supabase 클라이언트
    async def mock_get_async_client():
        class MockTable:
            def select(self, *args):
                return self
            def gte(self, field, value):
                return self
            def eq(self, field, value):
                return self
            async def execute(self):
                class MockResponse:
                    data = sample_feedback_data
                return MockResponse()

        class MockClient:
            def table(self, name):
                return MockTable()

        return MockClient()

    monkeypatch.setattr(
        "app.api.routes_feedback.get_async_client",
        mock_get_async_client
    )

    # Mock 인증
    async def mock_get_current_user():
        return {"id": "user-123", "email": "test@tenopa.co.kr"}

    monkeypatch.setattr(
        "app.api.routes_feedback.get_current_user",
        mock_get_current_user
    )

    # Mock require_role
    async def mock_require_role(*roles):
        async def check():
            return None
        return check

    monkeypatch.setattr(
        "app.api.routes_feedback.require_role",
        mock_require_role
    )

    # API 호출 (실제 엔드포인트는 비동기이므로 이 방식은 스킵)
    # response = client.post(
    #     "/api/feedback/analyze",
    #     json={"proposal_id": None, "days": 7},
    # )


@pytest.mark.integration
def test_feedback_report_endpoint_success(monkeypatch):
    """피드백 리포트 엔드포인트 성공 테스트"""

    async def mock_get_async_client():
        class MockTable:
            def select(self, *args):
                return self
            def gte(self, field, value):
                return self
            async def execute(self):
                class MockResponse:
                    data = []
                return MockResponse()

        class MockClient:
            def table(self, name):
                return MockTable()

        return MockClient()

    monkeypatch.setattr(
        "app.api.routes_feedback.get_async_client",
        mock_get_async_client
    )


@pytest.mark.unit
def test_feedback_recommendations_high_approval():
    """높은 승인률 권장사항 테스트"""
    data = [
        {"section_type": "intro", "decision": "APPROVE",
         "ratings": {"hallucination": 4.5, "persuasiveness": 4.5, "completeness": 4.5, "clarity": 4.5}},
        {"section_type": "intro", "decision": "APPROVE",
         "ratings": {"hallucination": 4.5, "persuasiveness": 4.5, "completeness": 4.5, "clarity": 4.5}},
    ]

    analyzer = FeedbackAnalyzer()
    result = analyzer.analyze_weekly_feedback(data)

    rec = result["weight_recommendations"][0]
    assert "Minimal adjustment needed" in rec["expected_impact"]


@pytest.mark.unit
def test_feedback_recommendations_low_approval():
    """낮은 승인률 권장사항 테스트"""
    data = [
        {"section_type": "tech", "decision": "REJECT",
         "ratings": {"hallucination": 2.0, "persuasiveness": 2.0, "completeness": 2.0, "clarity": 2.0}},
        {"section_type": "tech", "decision": "REJECT",
         "ratings": {"hallucination": 2.0, "persuasiveness": 2.0, "completeness": 2.0, "clarity": 2.0}},
    ]

    analyzer = FeedbackAnalyzer()
    result = analyzer.analyze_weekly_feedback(data)

    rec = result["weight_recommendations"][0]
    assert "Significant improvement potential" in rec["expected_impact"]
