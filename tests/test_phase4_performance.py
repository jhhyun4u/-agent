"""Phase 4: 성과 추적 + PPTX 빌더 + G2B 서비스 테스트."""


# ── 성과 API ──

async def test_team_performance(client):
    """GET /api/performance/team/{team_id} 팀 성과."""
    resp = await client.get("/api/performance/team/team-001")
    assert resp.status_code == 200


async def test_company_performance(client):
    """GET /api/performance/company 전사 성과."""
    resp = await client.get("/api/performance/company")
    assert resp.status_code == 200
    data = resp.json()
    assert "by_positioning" in data


async def test_performance_trends(client):
    """GET /api/performance/trends 추이."""
    resp = await client.get("/api/performance/trends?period=monthly&months=6")
    assert resp.status_code == 200
    data = resp.json()
    assert data["period"] == "monthly"


async def test_performance_trends_quarterly(client):
    """분기별 추이."""
    resp = await client.get("/api/performance/trends?period=quarterly")
    assert resp.status_code == 200


# ── 대시보드 API ──

async def test_my_projects(client):
    """GET /api/dashboard/my-projects 내 프로젝트."""
    resp = await client.get("/api/dashboard/my-projects")
    assert resp.status_code == 200
    data = resp.json()
    assert "created" in data
    assert "participating" in data


async def test_team_dashboard(client):
    """GET /api/dashboard/team 팀 파이프라인."""
    resp = await client.get("/api/dashboard/team")
    assert resp.status_code == 200
    data = resp.json()
    assert "step_distribution" in data


async def test_team_performance_summary(client):
    """GET /api/dashboard/team/performance 팀 성과 요약."""
    resp = await client.get("/api/dashboard/team/performance")
    assert resp.status_code == 200


# ── PPTX 빌더 ──

async def test_pptx_builder():
    """PPTX 빌더 기본 생성."""
    from app.services.pptx_builder import build_pptx

    slides = [
        {"title": "개요", "content": "프로젝트 개요 설명", "bullets": ["항목1", "항목2"]},
        {"title": "기술 접근", "body": "기술 접근 방법론\n상세 설명"},
    ]
    result = await build_pptx(slides, "테스트 제안서")
    assert isinstance(result, bytes)
    assert len(result) > 0
    # PPTX 매직 바이트 (PK zip)
    assert result[:2] == b"PK"


async def test_pptx_builder_empty_slides():
    """빈 슬라이드 리스트."""
    from app.services.pptx_builder import build_pptx

    result = await build_pptx([], "빈 제안서")
    assert isinstance(result, bytes)
    assert len(result) > 0


async def test_pptx_builder_with_strategy():
    """presentation_strategy 반영."""
    from app.services.pptx_builder import build_pptx

    slides = [{"title": "핵심", "bullets": ["요점"]}]
    strategy = {"key_message": "혁신적 클라우드 전환"}
    result = await build_pptx(slides, "전략 제안서", strategy)
    assert isinstance(result, bytes)


# ── G2B 서비스 ──

def test_g2b_service_imports():
    """G2B standalone 함수 import."""
    from app.services.g2b_service import search_bids, get_bid_detail, get_bid_result_info
    assert callable(search_bids)
    assert callable(get_bid_detail)
    assert callable(get_bid_result_info)
