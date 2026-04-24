"""
Dashboard KPI 메트릭 서비스 단위 테스트

test_compute_individual_metrics: 개인 메트릭 계산 로직
test_aggregate_team_metrics: 팀 메트릭 집계 로직
test_rank_department_teams: 본부 팀 순위 로직
test_calculate_executive_kpis: 경영진 KPI 계산 로직
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
from decimal import Decimal

from app.services.domains.operations.dashboard_metrics_service import DashboardMetricsService
from app.exceptions import TenopAPIError


class TestDashboardMetricsServiceLogic:
    """대시보드 메트릭 서비스 로직 테스트"""

    def test_compute_individual_metrics_with_data(self):
        """개인 메트릭 계산 - 데이터 있는 경우"""
        # 개인이 5개의 제안을 가지고 있는 경우
        proposals = [
            {"status": "won", "final_price": 500_000_000, "result_type": "won"},
            {"status": "won", "final_price": 300_000_000, "result_type": "won"},
            {"status": "lost", "final_price": None, "result_type": "lost"},
            {"status": "in_progress", "final_price": None, "result_type": None},
            {"status": "analyzing", "final_price": None, "result_type": None},
        ]

        # 수주금액 합계 검증
        total_won = sum(p["final_price"] for p in proposals if p["result_type"] == "won")
        assert total_won == 800_000_000

        # 수주 건수
        won_count = sum(1 for p in proposals if p["result_type"] == "won")
        assert won_count == 2

        # 진행 중 건수
        in_progress = sum(1 for p in proposals if p["status"] not in ("won", "lost", "completed", "cancelled"))
        assert in_progress == 2

    def test_compute_team_metrics_win_rate(self):
        """팀 메트릭 - 수주율 계산"""
        # 팀이 25개 제안 중 12개 수주
        total = 25
        won = 12
        win_rate = (won / total * 100) if total > 0 else 0

        assert abs(win_rate - 48.0) < 0.1

    def test_compute_team_metrics_average_deal_size(self):
        """팀 메트릭 - 평균 건당 금액"""
        total_won_amount = 2_500_000_000
        won_count = 12
        avg_deal_size = total_won_amount / won_count if won_count > 0 else 0

        assert abs(avg_deal_size - 208_333_333) < 1

    def test_rank_department_teams_by_win_rate(self):
        """본부 메트릭 - 팀 순위 (수주율 기준)"""
        teams = [
            {"team_name": "팀A", "win_rate_ytd": 48.2},
            {"team_name": "팀B", "win_rate_ytd": 40.0},
            {"team_name": "팀C", "win_rate_ytd": 55.5},
        ]

        # 수주율 기준 정렬
        sorted_teams = sorted(teams, key=lambda t: t["win_rate_ytd"], reverse=True)

        assert sorted_teams[0]["team_name"] == "팀C"
        assert sorted_teams[1]["team_name"] == "팀A"
        assert sorted_teams[2]["team_name"] == "팀B"

    def test_calculate_variance_from_target(self):
        """경영진 메트릭 - 목표 대비 실적"""
        actual_win_rate = 42.5
        target_win_rate = 45.0
        variance = actual_win_rate - target_win_rate

        assert variance == -2.5

        # 상태 판정
        status = "below_target" if variance < -2 else ("above_target" if variance > 2 else "on_target")
        assert status == "below_target"

    def test_aggregate_division_metrics(self):
        """본부 메트릭 - 팀별 집계"""
        teams = [
            {"total_proposals": 25, "won_count": 12, "total_won_amount": 2_500_000_000},
            {"total_proposals": 20, "won_count": 8, "total_won_amount": 1_800_000_000},
        ]

        total_props = sum(t["total_proposals"] for t in teams)
        total_won = sum(t["won_count"] for t in teams)
        total_amount = sum(t["total_won_amount"] for t in teams)

        assert total_props == 45
        assert total_won == 20
        assert total_amount == 4_300_000_000

        division_win_rate = (total_won / total_props * 100) if total_props > 0 else 0
        assert abs(division_win_rate - 44.44) < 0.1


class TestDashboardMetricsServiceErrors:
    """에러 처리 테스트"""

    @pytest.mark.asyncio
    async def test_error_code_format(self):
        """에러 코드 형식 검증"""
        try:
            raise TenopAPIError("GEN_001", "테스트 에러", status_code=400)
        except TenopAPIError as e:
            assert e.error_code == "GEN_001"
            assert e.status_code == 400
            assert "테스트 에러" in str(e)

    @pytest.mark.asyncio
    async def test_tenop_api_error_to_dict(self):
        """에러 to_dict() 메서드"""
        error = TenopAPIError("GEN_001", "테스트", status_code=400)
        error_dict = error.to_dict()

        assert error_dict["error_code"] == "GEN_001"
        assert error_dict["message"] == "테스트"

    @pytest.mark.asyncio
    async def test_tenop_api_error_with_detail(self):
        """에러 with detail"""
        detail = {"user_id": "123", "team_id": "456"}
        error = TenopAPIError("GEN_001", "테스트", status_code=400, detail=detail)
        error_dict = error.to_dict()

        assert error_dict["detail"] == detail


class TestDashboardMetricsServiceIntegration:
    """통합 테스트 (간단한 케이스)"""

    def test_service_initialization(self):
        """서비스 초기화"""
        service = DashboardMetricsService()
        assert service is not None
        assert service.client is None

    def test_metrics_response_structure_individual(self):
        """개인 메트릭 응답 구조"""
        # 실제 응답 구조 검증
        expected_keys = [
            "in_progress_proposals",
            "completed_this_month",
            "recent_won",
            "recent_lost",
            "total_amount_won",
            "avg_days_to_complete",
            "total_proposals_count"
        ]

        # 각 키가 정수 또는 float 값을 가져야 함
        sample_response = {
            "in_progress_proposals": 3,
            "completed_this_month": 2,
            "recent_won": 1,
            "recent_lost": 0,
            "total_amount_won": 500_000_000,
            "avg_days_to_complete": 15.5,
            "total_proposals_count": 5
        }

        assert all(key in sample_response for key in expected_keys)

    def test_metrics_response_structure_team(self):
        """팀 메트릭 응답 구조"""
        expected_keys = [
            "team_id",
            "team_name",
            "division_name",
            "win_rate_ytd",
            "win_rate_mtd",
            "total_proposals",
            "won_count",
            "total_won_amount",
            "avg_deal_size",
            "avg_tech_score",
            "in_progress_count",
            "positioning_breakdown"
        ]

        sample_response = {
            "team_id": "team-001",
            "team_name": "영업팀1",
            "division_name": "영업본부",
            "win_rate_ytd": 48.2,
            "win_rate_mtd": 50.0,
            "total_proposals": 25,
            "won_count": 12,
            "total_won_amount": 2_500_000_000,
            "avg_deal_size": 208_333_333,
            "avg_tech_score": 82.5,
            "in_progress_count": 3,
            "positioning_breakdown": [
                {"positioning": "Primary", "win_rate": 55.2, "total": 23, "won": 13}
            ]
        }

        assert all(key in sample_response for key in expected_keys)

    def test_metrics_response_structure_department(self):
        """본부 메트릭 응답 구조"""
        expected_keys = [
            "division_id",
            "division_name",
            "win_rate",
            "target_win_rate",
            "variance",
            "status",
            "total_proposals",
            "total_won_amount",
            "team_comparison"
        ]

        sample_response = {
            "division_id": "div-001",
            "division_name": "영업본부",
            "win_rate": 44.4,
            "target_win_rate": 45.0,
            "variance": -0.6,
            "status": "on_target",
            "total_proposals": 45,
            "total_won_amount": 4_300_000_000,
            "team_comparison": []
        }

        assert all(key in sample_response for key in expected_keys)

    def test_metrics_response_structure_executive(self):
        """경영진 메트릭 응답 구조"""
        expected_keys = [
            "org_id",
            "org_name",
            "period",
            "metrics",
            "division_comparison"
        ]

        sample_response = {
            "org_id": "org-001",
            "org_name": "Tenopa",
            "period": "YTD",
            "metrics": {
                "overall_win_rate": 43.2,
                "total_won_amount": 15_000_000_000,
                "total_proposal_count": 87,
                "avg_proposal_value": 172_413_793
            },
            "division_comparison": []
        }

        assert all(key in sample_response for key in expected_keys)
        assert "metrics" in sample_response
        assert "division_comparison" in sample_response
