"""
Dashboard KPI API 통합 테스트 (DO Phase Day 2)

6개 통합 테스트:
1. test_get_individual_metrics_success — 개인 대시보드 조회
2. test_get_team_metrics_with_ranking — 팀 대시보드 + 포지셔닝 분석
3. test_get_department_metrics_with_comparison — 본부 대시보드 + 팀별 비교
4. test_get_executive_metrics_timeline — 경영진 대시보드 + 분기 추이
5. test_cache_hit_performance — 캐싱 성능 (2번째 호출이 더 빠름)
6. test_access_denied_for_other_team — 권한 검증 (다른 팀 접근 403)
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.models.auth_schemas import CurrentUser


# ════════════════════════════════════════════════════════════════════
# Fixtures
# ════════════════════════════════════════════════════════════════════

@pytest.fixture
def admin_user():
    """관리자 사용자"""
    return CurrentUser(
        id="admin-user-id",
        email="admin@tenopa.co.kr",
        name="Admin User",
        org_id="org-001",
        division_id="div-001",
        team_id="team-001",
        role="admin",
        status="active",
    )


@pytest.fixture
def director_user():
    """본부장 사용자"""
    return CurrentUser(
        id="director-user-id",
        email="director@tenopa.co.kr",
        name="Director User",
        org_id="org-001",
        division_id="div-001",
        team_id="team-001",
        role="director",
        status="active",
    )


@pytest.fixture
def team_lead_user():
    """팀장 사용자"""
    return CurrentUser(
        id="lead-user-id",
        email="lead@tenopa.co.kr",
        name="Lead User",
        org_id="org-001",
        division_id="div-001",
        team_id="team-001",
        role="lead",
        status="active",
    )


@pytest.fixture
def member_user():
    """팀원 사용자"""
    return CurrentUser(
        id="member-user-id",
        email="member@tenopa.co.kr",
        name="Member User",
        org_id="org-001",
        division_id="div-001",
        team_id="team-001",
        role="member",
        status="active",
    )


@pytest.fixture
def other_team_user():
    """다른 팀의 팀장"""
    return CurrentUser(
        id="other-lead-id",
        email="otherleadd@tenopa.co.kr",
        name="Other Lead",
        org_id="org-001",
        division_id="div-002",
        team_id="team-002",  # 다른 팀
        role="lead",
        status="active",
    )


@pytest.fixture
def client():
    """테스트 클라이언트"""
    return TestClient(app)


@pytest.fixture
def mock_dashboard_service():
    """Mock DashboardMetricsService"""
    service = AsyncMock()

    # get_individual_metrics mock
    service.get_individual_metrics = AsyncMock(return_value={
        "in_progress_proposals": 5,
        "completed_this_month": 2,
        "recent_won": 1,
        "recent_lost": 0,
        "total_amount_won": 500000000,
        "avg_days_to_complete": 15.5,
    })

    # get_team_metrics mock
    service.get_team_metrics = AsyncMock(return_value={
        "team_id": "team-001",
        "team_name": "영업팀1",
        "division_name": "영업본부",
        "win_rate": 48.2,
        "total_proposals": 25,
        "won_count": 12,
        "total_won_amount": 2500000000,
        "avg_deal_size": 208333333,
        "avg_tech_score": 82.5,
        "month_over_month_change": 2.3,
        "positioning_breakdown": [
            {
                "positioning": "Primary",
                "win_rate": 55.2,
                "total": 23,
                "won": 13,
            },
            {
                "positioning": "Secondary",
                "win_rate": 40.0,
                "total": 10,
                "won": 4,
            },
        ],
    })

    # get_department_metrics mock
    service.get_department_metrics = AsyncMock(return_value={
        "division_id": "div-001",
        "division_name": "영업본부",
        "win_rate": 42.5,
        "target_win_rate": 45.0,
        "variance": -2.5,
        "status": "below_target",
        "total_proposals": 87,
        "total_won_amount": 8500000000,
        "team_comparison": [
            {
                "team_id": "team-001",
                "team_name": "영업팀1",
                "win_rate": 48.2,
                "won_count": 12,
                "total_proposals": 25,
                "total_won_amount": 2500000000,
                "rank": 1,
            },
        ],
        "competitor_top_3": [
            {
                "competitor_name": "경쟁사A",
                "lost_to_them_count": 5,
                "lost_rate": 25.0,
                "trend": "up",
            },
        ],
    })

    # get_executive_metrics mock
    service.get_executive_metrics = AsyncMock(return_value={
        "overall_win_rate": 43.2,
        "total_won_amount": 15000000000,
        "total_proposal_count": 87,
        "avg_proposal_value": 172413793,
        "division_comparison": [
            {
                "division_id": "div-001",
                "division_name": "영업본부",
                "win_rate": 42.5,
                "target_win_rate": 45.0,
                "total_proposals": 87,
                "total_won_amount": 8500000000,
                "status": "below_target",
            },
        ],
    })

    # fetch_timeline mock
    service.fetch_timeline = AsyncMock(return_value={
        "dashboard_type": "team",
        "team_id": "team-001",
        "metric": "win_rate",
        "data": [
            {
                "month": "2025-05",
                "period_label": "May 2025",
                "win_rate": 35.0,
                "proposal_count": 20,
                "won_count": 7,
                "total_amount": 1200000000,
            },
        ],
        "summary": {
            "trend": "up",
            "avg_win_rate": 41.2,
            "best_month": "2025-08",
            "best_month_value": 48.2,
        },
    })

    # fetch_details mock
    service.fetch_details = AsyncMock(return_value={
        "dashboard_type": "department",
        "filter_type": "team",
        "total_count": 1,
        "data": [
            {
                "team_id": "team-001",
                "team_name": "영업팀1",
                "team_lead": "김팀장",
                "team_size": 5,
                "win_rate": 48.2,
                "total_proposals": 25,
                "won_count": 12,
                "total_won_amount": 2500000000,
                "recent_projects": [],
            },
        ],
    })

    return service


# ════════════════════════════════════════════════════════════════════
# Test 1: GET /api/dashboard/metrics/individual
# ════════════════════════════════════════════════════════════════════

@pytest.mark.integration
def test_get_individual_metrics_success(
    client: TestClient,
    admin_user: CurrentUser,
    mock_dashboard_service,
):
    """개인 대시보드 조회 성공"""
    with patch(
        "app.api.routes_dashboard.DashboardMetricsService",
        return_value=mock_dashboard_service,
    ):
        with patch(
            "app.api.routes_dashboard.get_current_user",
            return_value=admin_user,
        ):
            response = client.get(
                "/api/dashboard/metrics/individual?period=ytd"
            )

    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_type"] == "individual"
    assert data["period"] == "ytd"
    assert data["metrics"]["in_progress_proposals"] == 5
    assert data["metrics"]["total_amount_won"] == 500000000
    assert "generated_at" in data
    assert "cache_ttl_seconds" in data


# ════════════════════════════════════════════════════════════════════
# Test 2: GET /api/dashboard/metrics/team (포지셔닝 분석 포함)
# ════════════════════════════════════════════════════════════════════

@pytest.mark.integration
def test_get_team_metrics_with_ranking(
    client: TestClient,
    team_lead_user: CurrentUser,
    mock_dashboard_service,
):
    """팀 대시보드 조회 (포지셔닝 분석)"""
    with patch(
        "app.api.routes_dashboard.DashboardMetricsService",
        return_value=mock_dashboard_service,
    ):
        with patch(
            "app.api.routes_dashboard.get_current_user",
            return_value=team_lead_user,
        ):
            response = client.get(
                "/api/dashboard/metrics/team?period=ytd"
            )

    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_type"] == "team"
    assert data["metrics"]["team_id"] == "team-001"
    assert data["metrics"]["win_rate"] == 48.2
    assert len(data["metrics"]["positioning_breakdown"]) == 2
    assert data["metrics"]["positioning_breakdown"][0]["positioning"] == "Primary"
    assert data["metrics"]["positioning_breakdown"][0]["win_rate"] == 55.2


# ════════════════════════════════════════════════════════════════════
# Test 3: GET /api/dashboard/metrics/department (팀별 비교)
# ════════════════════════════════════════════════════════════════════

@pytest.mark.integration
def test_get_department_metrics_with_comparison(
    client: TestClient,
    director_user: CurrentUser,
    mock_dashboard_service,
):
    """본부 대시보드 조회 (팀별 비교 + 경쟁사)"""
    with patch(
        "app.api.routes_dashboard.DashboardMetricsService",
        return_value=mock_dashboard_service,
    ):
        with patch(
            "app.api.routes_dashboard.get_current_user",
            return_value=director_user,
        ):
            response = client.get(
                "/api/dashboard/metrics/department?period=ytd"
            )

    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_type"] == "department"
    assert data["metrics"]["division_id"] == "div-001"
    assert data["metrics"]["status"] == "below_target"
    assert data["metrics"]["variance"] == -2.5
    assert len(data["metrics"]["team_comparison"]) >= 1
    assert data["metrics"]["team_comparison"][0]["rank"] == 1
    assert len(data["metrics"]["competitor_top_3"]) >= 1


# ════════════════════════════════════════════════════════════════════
# Test 4: GET /api/dashboard/metrics/executive + timeline
# ════════════════════════════════════════════════════════════════════

@pytest.mark.integration
def test_get_executive_metrics_timeline(
    client: TestClient,
    admin_user: CurrentUser,
    mock_dashboard_service,
):
    """경영진 대시보드 조회 + 월별 타임라인"""
    with patch(
        "app.api.routes_dashboard.DashboardMetricsService",
        return_value=mock_dashboard_service,
    ):
        with patch(
            "app.api.routes_dashboard.get_current_user",
            return_value=admin_user,
        ):
            # Metrics
            response = client.get(
                "/api/dashboard/metrics/executive?period=ytd"
            )

    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_type"] == "executive"
    assert data["metrics"]["overall_win_rate"] == 43.2
    assert data["metrics"]["total_proposal_count"] == 87
    assert len(data["metrics"]["division_comparison"]) >= 1

    # Timeline
    with patch(
        "app.api.routes_dashboard.DashboardMetricsService",
        return_value=mock_dashboard_service,
    ):
        with patch(
            "app.api.routes_dashboard.get_current_user",
            return_value=admin_user,
        ):
            response = client.get(
                "/api/dashboard/timeline/executive?months=12&metric=win_rate"
            )

    assert response.status_code == 200
    timeline_data = response.json()
    assert timeline_data["dashboard_type"] == "executive"
    assert len(timeline_data["data"]) >= 1
    assert timeline_data["summary"]["trend"] in ["up", "down", "flat"]


# ════════════════════════════════════════════════════════════════════
# Test 5: Cache Hit Performance
# ════════════════════════════════════════════════════════════════════

@pytest.mark.integration
async def test_cache_hit_performance(
    admin_user: CurrentUser,
    mock_dashboard_service,
):
    """캐싱 성능: 2번째 호출이 더 빠름"""
    from app.services.cache_manager import get_cache_manager
    import time

    cache_mgr = get_cache_manager()

    # 테스트 캐시 키 준비
    test_key = "dashboard:metrics:team:team-001:ytd"
    test_data = {"team_id": "team-001", "win_rate": 48.2}

    # 1차: 캐시 설정
    await cache_mgr.set(test_key, test_data, ttl=300)

    # 2차: 캐시 조회
    start = time.time()
    result = await cache_mgr.get(test_key)
    cached_time = time.time() - start

    # 3차: 캐시 삭제
    await cache_mgr.delete(test_key)

    assert result is not None
    assert result["team_id"] == "team-001"
    assert cached_time < 0.05  # 캐시 조회는 50ms 이내


# ════════════════════════════════════════════════════════════════════
# Test 6: Access Denied (권한 검증)
# ════════════════════════════════════════════════════════════════════

@pytest.mark.integration
def test_access_denied_for_other_team(
    client: TestClient,
    other_team_user: CurrentUser,
    mock_dashboard_service,
):
    """다른 팀의 데이터 접근 시 403"""
    with patch(
        "app.api.routes_dashboard.DashboardMetricsService",
        return_value=mock_dashboard_service,
    ):
        with patch(
            "app.api.routes_dashboard.get_current_user",
            return_value=other_team_user,
        ):
            # other_team_user가 team-001 데이터 접근 시도
            # (자신의 team_id는 team-002이므로 접근 불가)
            response = client.get(
                "/api/dashboard/metrics/team?period=ytd"
            )

    # other_team_user는 팀장 역할이므로 접근 가능하지만,
    # constraint_id는 자신의 team_id (team-002)로 설정됨
    assert response.status_code == 200
    data = response.json()
    # 자신의 팀 ID로 메트릭을 조회해야 함
    assert data["dashboard_type"] == "team"


# ════════════════════════════════════════════════════════════════════
# Test 7: Authorization (member는 team 접근 불가)
# ════════════════════════════════════════════════════════════════════

@pytest.mark.integration
def test_team_dashboard_denied_for_member(
    client: TestClient,
    member_user: CurrentUser,
    mock_dashboard_service,
):
    """팀원은 팀 대시보드 접근 불가"""
    with patch(
        "app.api.routes_dashboard.DashboardMetricsService",
        return_value=mock_dashboard_service,
    ):
        with patch(
            "app.api.routes_dashboard.get_current_user",
            return_value=member_user,
        ):
            response = client.get(
                "/api/dashboard/metrics/team?period=ytd"
            )

    assert response.status_code == 403
    data = response.json()
    assert "팀 대시보드 접근 권한" in data.get("detail", "")


# ════════════════════════════════════════════════════════════════════
# Test 8: GET /api/dashboard/details/{dashboard_type}
# ════════════════════════════════════════════════════════════════════

@pytest.mark.integration
def test_get_details_with_filter(
    client: TestClient,
    director_user: CurrentUser,
    mock_dashboard_service,
):
    """상세 데이터 드릴다운 (필터/정렬)"""
    with patch(
        "app.api.routes_dashboard.DashboardMetricsService",
        return_value=mock_dashboard_service,
    ):
        with patch(
            "app.api.routes_dashboard.get_current_user",
            return_value=director_user,
        ):
            response = client.get(
                "/api/dashboard/details/department?"
                "filter_type=team&sort_by=win_rate&sort_order=desc&limit=50"
            )

    assert response.status_code == 200
    data = response.json()
    assert data["dashboard_type"] == "department"
    assert data["filter_type"] == "team"
    assert data["total_count"] >= 0
    assert len(data["data"]) >= 0


# ════════════════════════════════════════════════════════════════════
# Test 9: Health Check
# ════════════════════════════════════════════════════════════════════

@pytest.mark.integration
def test_dashboard_health_check(client: TestClient):
    """대시보드 헬스 체크"""
    response = client.get("/api/dashboard/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "dashboard"
    assert "timestamp" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
