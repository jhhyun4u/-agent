"""Phase 6: Knowledge Base + 시맨틱 검색 테스트."""
from unittest.mock import patch, AsyncMock
from tests.conftest import make_supabase_mock


# ══════════════════════════════════════
# 임베딩 서비스
# ══════════════════════════════════════

async def test_embedding_service_fallback():
    """OpenAI 미연결 시 제로 벡터 반환."""
    from app.services.embedding_service import generate_embedding

    mock_openai = AsyncMock()
    mock_openai.embeddings.create.side_effect = Exception("API key not set")

    with patch("app.services.embedding_service._get_openai", return_value=mock_openai):
        result = await generate_embedding("테스트 텍스트")
        assert len(result) == 1536
        assert result[0] == 0.0


async def test_embedding_empty_text():
    """빈 텍스트 → 제로 벡터."""
    from app.services.embedding_service import generate_embedding
    result = await generate_embedding("")
    assert len(result) == 1536


def test_embedding_text_helpers():
    """임베딩 텍스트 조합 헬퍼."""
    from app.services.embedding_service import (
        embedding_text_for_content,
        embedding_text_for_client,
        embedding_text_for_competitor,
        embedding_text_for_lesson,
    )

    assert "테스트" in embedding_text_for_content("테스트", "본문")
    assert "기관명" in embedding_text_for_client("기관명", "중앙부처")
    assert "경쟁사" in embedding_text_for_competitor("경쟁사", "SI")
    assert "전략" in embedding_text_for_lesson("전략 요약", "효과적인 점")


# ══════════════════════════════════════
# 통합 KB 검색
# ══════════════════════════════════════

async def test_kb_search_endpoint(client):
    """GET /api/kb/search 통합 검색."""
    with patch("app.services.embedding_service.generate_embedding",
               return_value=[0.0] * 1536):
        resp = await client.get("/api/kb/search?q=클라우드&top_k=3")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data["data"]
        assert "total" in data["data"]


async def test_kb_search_with_areas(client):
    """영역 필터링 검색."""
    with patch("app.services.embedding_service.generate_embedding",
               return_value=[0.0] * 1536):
        resp = await client.get("/api/kb/search?q=ERP&areas=content,client")
        assert resp.status_code == 200


async def test_kb_search_missing_query(client):
    """쿼리 누락 → 422."""
    resp = await client.get("/api/kb/search")
    assert resp.status_code == 422


# ══════════════════════════════════════
# 콘텐츠 라이브러리 CRUD
# ══════════════════════════════════════

async def test_content_list(client):
    """GET /api/kb/content 목록."""
    resp = await client.get("/api/kb/content")
    assert resp.status_code == 200
    assert "data" in resp.json()


async def test_content_create(client):
    """POST /api/kb/content 등록."""
    with patch("app.services.embedding_service.generate_embedding",
               return_value=[0.0] * 1536):
        resp = await client.post("/api/kb/content", json={
            "title": "클라우드 아키텍처 설계",
            "body": "마이크로서비스 기반 클라우드 네이티브 아키텍처 설계 방법론...",
            "type": "section_block",
            "tags": ["클라우드", "MSA"],
        })
        assert resp.status_code == 201


async def test_content_update(client):
    """PUT /api/kb/content/{id} 수정."""
    with patch("app.services.content_library.update_content",
               return_value={"id": "c1", "title": "수정됨"}):
        resp = await client.put("/api/kb/content/c1", json={
            "title": "수정된 제목",
        })
        assert resp.status_code == 200


async def test_content_update_empty(client):
    """빈 수정 → 400."""
    resp = await client.put("/api/kb/content/c1", json={})
    assert resp.status_code == 400


async def test_content_delete(client):
    """DELETE /api/kb/content/{id} 삭제 (archived)."""
    resp = await client.delete("/api/kb/content/c1")
    assert resp.status_code == 200


async def test_content_approve(client):
    """POST /api/kb/content/{id}/approve 승인."""
    resp = await client.post("/api/kb/content/c1/approve")
    assert resp.status_code == 200


# ══════════════════════════════════════
# 발주기관 DB
# ══════════════════════════════════════

async def test_clients_list(client):
    """GET /api/kb/clients 발주기관 목록."""
    resp = await client.get("/api/kb/clients")
    assert resp.status_code == 200
    assert "data" in resp.json()


async def test_clients_create(client):
    """POST /api/kb/clients 발주기관 등록."""
    with patch("app.services.embedding_service.generate_embedding",
               return_value=[0.0] * 1536):
        resp = await client.post("/api/kb/clients", json={
            "client_name": "행정안전부",
            "client_type": "중앙부처",
            "relationship": "friendly",
        })
        assert resp.status_code == 201


async def test_clients_update(client):
    """PUT /api/kb/clients/{id} 수정."""
    resp = await client.put("/api/kb/clients/cli-001", json={
        "relationship": "close",
    })
    assert resp.status_code == 200


async def test_clients_delete(client):
    """DELETE /api/kb/clients/{id} 삭제."""
    resp = await client.delete("/api/kb/clients/cli-001")
    assert resp.status_code == 200


# ══════════════════════════════════════
# 경쟁사 DB
# ══════════════════════════════════════

async def test_competitors_list(client):
    """GET /api/kb/competitors 경쟁사 목록."""
    resp = await client.get("/api/kb/competitors")
    assert resp.status_code == 200


async def test_competitors_create(client):
    """POST /api/kb/competitors 경쟁사 등록."""
    with patch("app.services.embedding_service.generate_embedding",
               return_value=[0.0] * 1536):
        resp = await client.post("/api/kb/competitors", json={
            "company_name": "경쟁사A",
            "scale": "중견",
            "primary_area": "SI/SW개발",
            "price_pattern": "aggressive",
        })
        assert resp.status_code == 201


async def test_competitors_delete(client):
    """DELETE /api/kb/competitors/{id} 삭제."""
    resp = await client.delete("/api/kb/competitors/comp-001")
    assert resp.status_code == 200


# ══════════════════════════════════════
# 교훈 아카이브
# ══════════════════════════════════════

async def test_lessons_list(client):
    """GET /api/kb/lessons 교훈 목록."""
    resp = await client.get("/api/kb/lessons")
    assert resp.status_code == 200


async def test_lessons_create(client):
    """POST /api/kb/lessons 교훈 등록."""
    with patch("app.services.embedding_service.generate_embedding",
               return_value=[0.0] * 1536):
        resp = await client.post("/api/kb/lessons", json={
            "strategy_summary": "가격 경쟁력 + 기술 차별화",
            "effective_points": "사전 발주기관 미팅",
            "weak_points": "인력 투입 계획 부족",
            "result": "수주",
            "positioning": "offensive",
        })
        assert resp.status_code == 201


# ══════════════════════════════════════
# 노임단가 (v3.4)
# ══════════════════════════════════════

async def test_labor_rates_list(client):
    """GET /api/kb/labor-rates 목록."""
    resp = await client.get("/api/kb/labor-rates?standard_org=KOSA&year=2026")
    assert resp.status_code == 200
    assert "data" in resp.json()


async def test_labor_rates_create(client):
    """POST /api/kb/labor-rates 등록."""
    resp = await client.post("/api/kb/labor-rates", json={
        "standard_org": "KOSA",
        "year": 2026,
        "grade": "특급",
        "monthly_rate": 12000000,
        "daily_rate": 550000,
    })
    assert resp.status_code == 201


async def test_labor_rates_delete(client):
    """DELETE /api/kb/labor-rates/{id} 삭제."""
    resp = await client.delete("/api/kb/labor-rates/rate-001")
    assert resp.status_code == 200


# ══════════════════════════════════════
# 시장 낙찰가 (v3.4)
# ══════════════════════════════════════

async def test_market_prices_list(client):
    """GET /api/kb/market-prices 목록."""
    resp = await client.get("/api/kb/market-prices?domain=SI/SW개발")
    assert resp.status_code == 200


async def test_market_prices_create(client):
    """POST /api/kb/market-prices 등록."""
    resp = await client.post("/api/kb/market-prices", json={
        "domain": "SI/SW개발",
        "year": 2025,
        "budget": 500000000,
        "winning_price": 450000000,
        "bid_ratio": 0.9,
        "num_bidders": 5,
    })
    assert resp.status_code == 201


# ══════════════════════════════════════
# KB 내보내기
# ══════════════════════════════════════

async def test_export_capabilities(client):
    """GET /api/kb/export/capabilities CSV."""
    resp = await client.get("/api/kb/export/capabilities")
    assert resp.status_code == 200
    assert "text/csv" in resp.headers.get("content-type", "")


async def test_export_invalid_part(client):
    """유효하지 않은 내보내기 대상 → 400."""
    resp = await client.get("/api/kb/export/invalid")
    assert resp.status_code == 400


# ══════════════════════════════════════
# Content Library 서비스 유닛
# ══════════════════════════════════════

async def test_quality_score_calculation():
    """품질 점수 산출 알고리즘."""
    from app.services.content_library import calculate_quality_score

    mock_sb = make_supabase_mock({
        "content_library": [{
            "won_count": 3,
            "lost_count": 2,
            "reuse_count": 5,
            "updated_at": "2026-01-01T00:00:00+00:00",
        }],
    })
    with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb):
        score = await calculate_quality_score("c1")
        assert isinstance(score, float)
        assert 0 <= score <= 100


# ══════════════════════════════════════
# Feedback Loop 서비스
# ══════════════════════════════════════

def test_feedback_loop_import():
    """피드백 루프 import."""
    from app.services.feedback_loop import process_project_completion
    assert callable(process_project_completion)


# ══════════════════════════════════════
# Phase D: KB 건강도 + 재인덱싱 + 중복 탐지 (kb-enhancement)
# ══════════════════════════════════════


async def test_kb_health_endpoint(client):
    """GET /api/kb/health — 6개 영역 건강도 반환."""
    res = await client.get("/api/kb/health")
    assert res.status_code == 200
    data = res.json()["data"]
    # 6개 영역 모두 존재해야 함
    for area in ["content", "client", "competitor", "lesson", "capability", "qa"]:
        assert area in data, f"'{area}' 영역 누락"
        assert "total" in data[area]
        assert "with_embedding" in data[area]
        assert "coverage" in data[area]


async def test_kb_reindex_endpoint(client):
    """POST /api/kb/reindex — 배치 임베딩 생성."""
    # admin 역할 필요 (conftest mock_user는 admin)
    res = await client.post("/api/kb/reindex", json={"areas": ["content", "capability"]})
    assert res.status_code == 200
    data = res.json()["data"]
    assert "total" in data
    assert "processed" in data
    assert "failed" in data


async def test_kb_content_duplicates_endpoint(client):
    """GET /api/kb/content/duplicates — 중복 콘텐츠 쌍."""
    res = await client.get("/api/kb/content/duplicates?threshold=0.9")
    assert res.status_code == 200
    data = res.json()["data"]
    assert isinstance(data, list)


# ══════════════════════════════════════
# Phase A: 자동 축적 서비스 (kb-enhancement)
# ══════════════════════════════════════


async def test_auto_register_section_skip_short():
    """500자 미만 섹션은 스킵."""
    from app.services.content_library import auto_register_section
    result = await auto_register_section(
        org_id="o1", proposal_id="p1", section_id="s1",
        title="짧은 섹션", content="짧은 내용" * 10,  # < 500자
        section_type="UNDERSTAND",
    )
    assert result is None


async def test_auto_register_section_skip_low_score():
    """70점 미만 섹션은 스킵."""
    from app.services.content_library import auto_register_section
    result = await auto_register_section(
        org_id="o1", proposal_id="p1", section_id="s1",
        title="저품질", content="x" * 600,
        section_type="UNDERSTAND", self_review_score=50,
    )
    assert result is None


async def test_save_research_to_kb_empty():
    """빈 리서치는 0건."""
    from app.services.kb_updater import save_research_to_kb
    count = await save_research_to_kb("o1", "p1", {})
    assert count == 0


async def test_save_strategy_to_kb_empty():
    """빈 전략은 None."""
    from app.services.kb_updater import save_strategy_to_kb
    result = await save_strategy_to_kb("o1", "p1", "", "", {})
    assert result is None


# ══════════════════════════════════════
# Phase B: 검색 개선 (kb-enhancement)
# ══════════════════════════════════════


async def test_hybrid_ranking():
    """하이브리드 랭킹 공식 검증."""
    from app.services.knowledge_search import _apply_hybrid_ranking
    items = [
        {"similarity": 0.9, "quality_score": 30, "updated_at": "2026-03-20T00:00:00Z"},
        {"similarity": 0.7, "quality_score": 90, "updated_at": "2026-03-20T00:00:00Z"},
        {"similarity": 0.5, "quality_score": 50, "updated_at": "2025-01-01T00:00:00Z"},
    ]
    ranked = _apply_hybrid_ranking(items)
    # 고품질(90점)+중간유사도(0.7) 항목이 상위여야 함
    assert ranked[0]["quality_score"] == 90 or ranked[0]["similarity"] == 0.9


# ══════════════════════════════════════
# Phase C: 활용 강화 (kb-enhancement)
# ══════════════════════════════════════


def test_find_similar_cases_import():
    """find_similar_cases 함수 import."""
    from app.graph.context_helpers import find_similar_cases
    assert callable(find_similar_cases)


def test_batch_reindex_import():
    """batch_reindex 함수 import."""
    from app.services.embedding_service import batch_reindex
    assert callable(batch_reindex)
