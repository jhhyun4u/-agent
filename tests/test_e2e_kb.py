"""E2E Knowledge Base 통합 테스트.

KB 전체 CRUD 라이프사이클 + 검색 + 크로스도메인 연동 + 에러 케이스 + 응답 스키마 검증.
기존 conftest.py 인프라 활용 (MockQueryBuilder + Supabase mock).
"""
import io
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from tests.conftest import make_supabase_mock, MockQueryBuilder


# ══════════════════════════════════════════════
# Helper: 데이터가 있는 Supabase mock 생성
# ══════════════════════════════════════════════

def _mock_with_data(table_data: dict):
    """특정 테이블에 데이터를 넣은 supabase mock."""
    return make_supabase_mock(table_data)


def _make_client_with_data(app, mock_user, table_data: dict | None = None):
    """테이블 데이터 주입 가능한 테스트 클라이언트 팩토리."""
    from app.api.deps import get_current_user, get_rls_client, require_project_access
    supabase_mock = _mock_with_data(table_data or {})

    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_rls_client] = lambda: supabase_mock
    app.dependency_overrides[require_project_access] = lambda: {
        "id": "test-id", "title": "테스트", "status": "initialized",
    }
    return supabase_mock


# ══════════════════════════════════════════════
# 1. 콘텐츠 라이브러리 — 전체 라이프사이클
# ══════════════════════════════════════════════

class TestContentLifecycle:
    """콘텐츠: Create → List → Get → Update → Approve → Delete."""

    async def test_create_returns_201(self, client):
        """콘텐츠 생성 시 201 + body 포함."""
        with patch("app.services.embedding_service.generate_embedding",
                   return_value=[0.0] * 1536):
            resp = await client.post("/api/kb/content", json={
                "title": "마이크로서비스 아키텍처 설계",
                "body": "MSA 기반 설계 방법론: 도메인 분리, API Gateway, 서비스 메시...",
                "type": "section_block",
                "tags": ["MSA", "클라우드"],
                "industry": "IT",
                "tech_area": "클라우드",
            })
        assert resp.status_code == 201

    async def test_create_missing_title_returns_422(self, client):
        """title 누락 → 422 Validation Error."""
        resp = await client.post("/api/kb/content", json={
            "body": "본문만 있음",
        })
        assert resp.status_code == 422

    async def test_create_missing_body_returns_422(self, client):
        """body 누락 → 422."""
        resp = await client.post("/api/kb/content", json={
            "title": "제목만 있음",
        })
        assert resp.status_code == 422

    async def test_list_returns_items_and_total(self, client):
        """목록 조회 → items + total 필드."""
        resp = await client.get("/api/kb/content")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "meta" in data
        assert "total" in data["meta"]
        assert isinstance(data["data"], list)

    async def test_list_filter_by_status(self, client):
        """status 필터 쿼리 파라미터."""
        resp = await client.get("/api/kb/content?status=published")
        assert resp.status_code == 200

    async def test_list_filter_by_type(self, client):
        """type 필터 쿼리 파라미터."""
        resp = await client.get("/api/kb/content?type=section_block")
        assert resp.status_code == 200

    async def test_get_detail_not_found(self, client):
        """존재하지 않는 콘텐츠 상세 → 404."""
        resp = await client.get("/api/kb/content/nonexistent-id")
        assert resp.status_code == 404

    async def test_update_returns_200(self, client):
        """수정 → 200."""
        with patch("app.services.content_library.update_content",
                   return_value={"id": "c1", "title": "수정됨"}):
            resp = await client.put("/api/kb/content/c1", json={
                "title": "수정된 제목",
                "body": "수정된 본문 내용",
            })
        assert resp.status_code == 200

    async def test_update_empty_body_returns_400(self, client):
        """빈 수정 요청 → 400."""
        resp = await client.put("/api/kb/content/c1", json={})
        assert resp.status_code == 400

    async def test_approve_returns_200(self, client):
        """승인 → 200."""
        resp = await client.post("/api/kb/content/c1/approve")
        assert resp.status_code == 200

    async def test_delete_returns_200(self, client):
        """삭제 (archived 처리) → 200."""
        resp = await client.delete("/api/kb/content/c1")
        assert resp.status_code == 200


# ══════════════════════════════════════════════
# 2. 발주기관 DB — 전체 라이프사이클
# ══════════════════════════════════════════════

class TestClientIntelligenceLifecycle:
    """발주기관: Create → List → Get(+bid_history) → Update → Delete."""

    async def test_create_with_all_fields(self, client):
        """발주기관 등록 (전체 필드)."""
        with patch("app.services.embedding_service.generate_embedding",
                   return_value=[0.0] * 1536):
            resp = await client.post("/api/kb/clients", json={
                "client_name": "행정안전부",
                "client_type": "중앙부처",
                "scale": "대형",
                "parent_ministry": "국무총리실",
                "location": "세종시",
                "relationship": "friendly",
                "eval_tendency": "기술 중시",
                "notes": "디지털 정부 혁신 관련 과제 다수",
            })
        assert resp.status_code == 201

    async def test_create_minimal_fields(self, client):
        """최소 필드만으로 발주기관 등록."""
        with patch("app.services.embedding_service.generate_embedding",
                   return_value=[0.0] * 1536):
            resp = await client.post("/api/kb/clients", json={
                "client_name": "한국정보화진흥원",
            })
        assert resp.status_code == 201

    async def test_create_missing_name_returns_422(self, client):
        """client_name 누락 → 422."""
        resp = await client.post("/api/kb/clients", json={
            "client_type": "공공기관",
        })
        assert resp.status_code == 422

    async def test_list_returns_items(self, client):
        """발주기관 목록 → items + total."""
        resp = await client.get("/api/kb/clients")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "total" in data["meta"]

    async def test_list_filter_by_relationship(self, client):
        """관계 필터링."""
        resp = await client.get("/api/kb/clients?relationship=friendly")
        assert resp.status_code == 200

    async def test_list_filter_by_client_type(self, client):
        """기관 유형 필터링."""
        resp = await client.get("/api/kb/clients?client_type=중앙부처")
        assert resp.status_code == 200

    async def test_get_detail_not_found(self, client):
        """존재하지 않는 발주기관 → 404."""
        resp = await client.get("/api/kb/clients/nonexistent-id")
        assert resp.status_code == 404

    async def test_update_returns_200(self, client):
        """발주기관 수정."""
        resp = await client.put("/api/kb/clients/cli-001", json={
            "relationship": "close",
            "notes": "최근 사업 수주 성공",
        })
        assert resp.status_code == 200

    async def test_update_empty_returns_400(self, client):
        """빈 수정 → 400."""
        resp = await client.put("/api/kb/clients/cli-001", json={})
        assert resp.status_code == 400

    async def test_delete_returns_200(self, client):
        """발주기관 삭제."""
        resp = await client.delete("/api/kb/clients/cli-001")
        assert resp.status_code == 200


# ══════════════════════════════════════════════
# 3. 경쟁사 DB — 전체 라이프사이클
# ══════════════════════════════════════════════

class TestCompetitorLifecycle:
    """경쟁사: Create → List → Get(+competition_history) → Update → Delete."""

    async def test_create_full_fields(self, client):
        """경쟁사 등록 (전체 필드)."""
        with patch("app.services.embedding_service.generate_embedding",
                   return_value=[0.0] * 1536):
            resp = await client.post("/api/kb/competitors", json={
                "company_name": "삼성SDS",
                "scale": "대기업",
                "primary_area": "SI/SW개발",
                "strengths": "대규모 사업 수행 경험, 인력 풀",
                "weaknesses": "가격 경쟁력 낮음",
                "price_pattern": "conservative",
                "notes": "관공서 SI 분야 강세",
            })
        assert resp.status_code == 201

    async def test_create_minimal(self, client):
        """최소 필드 경쟁사 등록."""
        with patch("app.services.embedding_service.generate_embedding",
                   return_value=[0.0] * 1536):
            resp = await client.post("/api/kb/competitors", json={
                "company_name": "경쟁사B",
            })
        assert resp.status_code == 201

    async def test_create_missing_name_returns_422(self, client):
        """company_name 누락 → 422."""
        resp = await client.post("/api/kb/competitors", json={
            "scale": "중견",
        })
        assert resp.status_code == 422

    async def test_list_returns_items(self, client):
        """경쟁사 목록."""
        resp = await client.get("/api/kb/competitors")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data

    async def test_list_filter_by_scale(self, client):
        """규모 필터링."""
        resp = await client.get("/api/kb/competitors?scale=중견")
        assert resp.status_code == 200

    async def test_get_detail_not_found(self, client):
        """존재하지 않는 경쟁사 → 404."""
        resp = await client.get("/api/kb/competitors/nonexistent-id")
        assert resp.status_code == 404

    async def test_update_fields(self, client):
        """경쟁사 수정."""
        resp = await client.put("/api/kb/competitors/comp-001", json={
            "avg_win_rate": 0.45,
            "price_pattern": "aggressive",
        })
        assert resp.status_code == 200

    async def test_update_empty_returns_400(self, client):
        """빈 수정 → 400."""
        resp = await client.put("/api/kb/competitors/comp-001", json={})
        assert resp.status_code == 400

    async def test_delete_returns_200(self, client):
        """경쟁사 삭제."""
        resp = await client.delete("/api/kb/competitors/comp-001")
        assert resp.status_code == 200


# ══════════════════════════════════════════════
# 4. 교훈 아카이브 — CRUD + 회고 워크시트
# ══════════════════════════════════════════════

class TestLessonsLifecycle:
    """교훈: Create → List → Get → Filter + Retrospect."""

    async def test_create_full(self, client):
        """교훈 등록 (전체 필드)."""
        with patch("app.services.embedding_service.generate_embedding",
                   return_value=[0.0] * 1536):
            resp = await client.post("/api/kb/lessons", json={
                "proposal_id": "proj-001",
                "strategy_summary": "가격 경쟁력 + 기술 차별화 전략",
                "effective_points": "사전 발주기관 미팅으로 요구사항 정확 파악",
                "weak_points": "인력 투입 계획 부족",
                "improvements": "유사 사업 수행 실적 DB 구축",
                "failure_category": "tech",
                "failure_detail": "기술 점수 부족",
                "positioning": "offensive",
                "client_name": "행정안전부",
                "industry": "전자정부",
                "result": "lost",
            })
        assert resp.status_code == 201

    async def test_list_returns_items(self, client):
        """교훈 목록."""
        resp = await client.get("/api/kb/lessons")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "total" in data["meta"]

    async def test_list_filter_by_result(self, client):
        """결과 필터 (수주/패찰)."""
        resp = await client.get("/api/kb/lessons?result=won")
        assert resp.status_code == 200

    async def test_list_filter_by_positioning(self, client):
        """포지셔닝 필터."""
        resp = await client.get("/api/kb/lessons?positioning=defensive")
        assert resp.status_code == 200

    async def test_get_detail_not_found(self, client):
        """존재하지 않는 교훈 → 404."""
        resp = await client.get("/api/kb/lessons/nonexistent-id")
        assert resp.status_code == 404

    async def test_retrospect_submit_project_not_found(self, client):
        """존재하지 않는 프로젝트 회고 → 404."""
        with patch("app.services.embedding_service.generate_embedding",
                   return_value=[0.0] * 1536):
            resp = await client.post("/api/kb/retrospect/nonexistent", json={
                "strategy_summary": "공격형 전략으로 기술 차별화",
                "effective_points": "클라우드 네이티브 역량 어필 효과적",
                "weak_points": "실적 증빙 부족",
                "improvements": "유사 사업 레퍼런스 확보 필요",
            })
        assert resp.status_code == 404


# ══════════════════════════════════════════════
# 5. 노임단가 — CRUD + CSV 임포트
# ══════════════════════════════════════════════

class TestLaborRatesLifecycle:
    """노임단가: Create → List → Update → Import CSV → Delete."""

    async def test_create(self, client):
        """노임단가 등록."""
        resp = await client.post("/api/kb/labor-rates", json={
            "standard_org": "KOSA",
            "year": 2026,
            "grade": "특급",
            "monthly_rate": 12000000,
            "daily_rate": 550000,
            "effective_date": "2026-01-01",
            "source_url": "https://kosa.or.kr/rate/2026",
        })
        assert resp.status_code == 201

    async def test_create_missing_required_returns_422(self, client):
        """필수 필드 누락 → 422."""
        resp = await client.post("/api/kb/labor-rates", json={
            "standard_org": "KOSA",
            # year, grade, monthly_rate 누락
        })
        assert resp.status_code == 422

    async def test_list(self, client):
        """노임단가 목록 조회."""
        resp = await client.get("/api/kb/labor-rates")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "total" in data["meta"]

    async def test_list_filter_by_org_and_year(self, client):
        """기관 + 연도 필터."""
        resp = await client.get("/api/kb/labor-rates?standard_org=KOSA&year=2026")
        assert resp.status_code == 200

    async def test_list_filter_by_grade(self, client):
        """등급 필터."""
        resp = await client.get("/api/kb/labor-rates?grade=특급")
        assert resp.status_code == 200

    async def test_update(self, client):
        """노임단가 수정."""
        resp = await client.put("/api/kb/labor-rates/rate-001", json={
            "standard_org": "KOSA",
            "year": 2026,
            "grade": "특급",
            "monthly_rate": 12500000,
            "daily_rate": 570000,
        })
        assert resp.status_code == 200

    async def test_csv_import(self, client):
        """CSV 일괄 임포트."""
        csv_content = (
            "standard_org,year,grade,monthly_rate,daily_rate\n"
            "KOSA,2026,특급,12000000,550000\n"
            "KOSA,2026,고급,9500000,435000\n"
            "KEA,2026,특급,11000000,500000\n"
        )
        resp = await client.post(
            "/api/kb/labor-rates/import",
            files={"file": ("rates.csv", csv_content.encode("utf-8-sig"), "text/csv")},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"]["imported"] == 3

    async def test_csv_import_empty_returns_400(self, client):
        """빈 CSV → 400."""
        csv_content = "standard_org,year,grade,monthly_rate,daily_rate\n"
        resp = await client.post(
            "/api/kb/labor-rates/import",
            files={"file": ("empty.csv", csv_content.encode("utf-8-sig"), "text/csv")},
        )
        assert resp.status_code == 400

    async def test_csv_import_invalid_format_returns_400(self, client):
        """잘못된 CSV 컬럼 → 400."""
        csv_content = "wrong_col1,wrong_col2\nval1,val2\n"
        resp = await client.post(
            "/api/kb/labor-rates/import",
            files={"file": ("bad.csv", csv_content.encode("utf-8-sig"), "text/csv")},
        )
        assert resp.status_code == 400

    async def test_delete(self, client):
        """노임단가 삭제."""
        resp = await client.delete("/api/kb/labor-rates/rate-001")
        assert resp.status_code == 200


# ══════════════════════════════════════════════
# 6. 시장 낙찰가 — CRUD
# ══════════════════════════════════════════════

class TestMarketPricesLifecycle:
    """시장 낙찰가: Create → List → Update → Delete."""

    async def test_create_full(self, client):
        """시장 낙찰가 등록 (전체 필드)."""
        resp = await client.post("/api/kb/market-prices", json={
            "project_title": "차세대 행정정보시스템 구축",
            "client_org": "행정안전부",
            "domain": "SI/SW개발",
            "budget": 5000000000,
            "winning_price": 4500000000,
            "bid_ratio": 0.9,
            "num_bidders": 7,
            "tech_price_ratio": "70:30",
            "evaluation_method": "협상에 의한 계약",
            "year": 2025,
            "source": "나라장터",
        })
        assert resp.status_code == 201

    async def test_create_minimal(self, client):
        """최소 필드로 등록."""
        resp = await client.post("/api/kb/market-prices", json={
            "domain": "정책연구",
            "year": 2025,
        })
        assert resp.status_code == 201

    async def test_create_missing_domain_returns_422(self, client):
        """domain 누락 → 422."""
        resp = await client.post("/api/kb/market-prices", json={
            "year": 2025,
        })
        assert resp.status_code == 422

    async def test_list(self, client):
        """시장 낙찰가 목록."""
        resp = await client.get("/api/kb/market-prices")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data

    async def test_list_filter_by_domain(self, client):
        """도메인 필터."""
        resp = await client.get("/api/kb/market-prices?domain=SI/SW개발")
        assert resp.status_code == 200

    async def test_list_filter_by_year(self, client):
        """연도 필터."""
        resp = await client.get("/api/kb/market-prices?year=2025")
        assert resp.status_code == 200

    async def test_list_filter_by_budget_range(self, client):
        """예산 범위 필터."""
        resp = await client.get("/api/kb/market-prices?budget_min=1000000000&budget_max=5000000000")
        assert resp.status_code == 200

    async def test_update(self, client):
        """시장 낙찰가 수정."""
        resp = await client.put("/api/kb/market-prices/mp-001", json={
            "domain": "SI/SW개발",
            "year": 2025,
            "bid_ratio": 0.88,
        })
        assert resp.status_code == 200

    async def test_delete(self, client):
        """시장 낙찰가 삭제."""
        resp = await client.delete("/api/kb/market-prices/mp-001")
        assert resp.status_code == 200


# ══════════════════════════════════════════════
# 7. 통합 KB 검색
# ══════════════════════════════════════════════

class TestKbSearch:
    """통합 KB 검색: 시맨틱 + 키워드 하이브리드."""

    async def test_search_returns_results_and_total(self, client):
        """검색 결과 구조: query, total, results."""
        with patch("app.services.embedding_service.generate_embedding",
                   return_value=[0.0] * 1536):
            resp = await client.get("/api/kb/search?q=클라우드")
        assert resp.status_code == 200
        data = resp.json()
        assert "query" in data["data"]
        assert "total" in data["data"]
        assert "results" in data["data"]
        assert data["data"]["query"] == "클라우드"

    async def test_search_with_area_filter(self, client):
        """영역 필터링 (content, client)."""
        with patch("app.services.embedding_service.generate_embedding",
                   return_value=[0.0] * 1536):
            resp = await client.get("/api/kb/search?q=ERP&areas=content,client")
        assert resp.status_code == 200

    async def test_search_with_top_k(self, client):
        """top_k 파라미터."""
        with patch("app.services.embedding_service.generate_embedding",
                   return_value=[0.0] * 1536):
            resp = await client.get("/api/kb/search?q=설계&top_k=3")
        assert resp.status_code == 200

    async def test_search_missing_query_returns_422(self, client):
        """쿼리 누락 → 422."""
        resp = await client.get("/api/kb/search")
        assert resp.status_code == 422

    async def test_search_empty_query_returns_422(self, client):
        """빈 쿼리 → 422."""
        resp = await client.get("/api/kb/search?q=")
        assert resp.status_code == 422

    async def test_search_top_k_out_of_range(self, client):
        """top_k > 20 → 422."""
        resp = await client.get("/api/kb/search?q=test&top_k=50")
        assert resp.status_code == 422

    async def test_search_top_k_zero(self, client):
        """top_k < 1 → 422."""
        resp = await client.get("/api/kb/search?q=test&top_k=0")
        assert resp.status_code == 422

    async def test_search_all_areas(self, client):
        """전체 영역 검색 (areas 미지정)."""
        with patch("app.services.embedding_service.generate_embedding",
                   return_value=[0.0] * 1536):
            resp = await client.get("/api/kb/search?q=아키텍처")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data["data"]["results"], dict)


# ══════════════════════════════════════════════
# 8. Q&A — CRUD + 검색
# ══════════════════════════════════════════════

class TestQALifecycle:
    """Q&A: Batch Create → List → Update → Search → Delete."""

    _rqa = "app.api.routes_qa"
    _mock_proj = {"id": "proj-001", "title": "테스트 프로젝트", "status": "initialized"}

    async def test_batch_create(self, client):
        """Q&A 일괄 등록."""
        with patch(f"{self._rqa}.require_project_access", new_callable=AsyncMock, return_value=self._mock_proj), \
             patch(f"{self._rqa}.save_qa_records", new_callable=AsyncMock,
                   return_value=[
                       {"id": "qa-1", "question": "기술 구현 방안?", "answer": "MSA 기반"},
                       {"id": "qa-2", "question": "일정 준수 방안?", "answer": "애자일 스프린트"},
                   ]):
            resp = await client.post("/api/proposals/proj-001/qa", json=[
                {
                    "question": "기술 구현 방안은 무엇인가요?",
                    "answer": "MSA 기반 클라우드 네이티브 아키텍처를 적용합니다.",
                    "category": "technical",
                    "evaluator_reaction": "positive",
                    "memo": "구체적 사례 요청",
                },
                {
                    "question": "일정 준수 방안은?",
                    "answer": "애자일 스프린트 2주 단위로 진행합니다.",
                    "category": "management",
                },
            ])
        assert resp.status_code == 201
        data = resp.json()
        assert "data" in data
        assert "count" in data
        assert data["count"] == 2

    async def test_list_by_proposal(self, client):
        """프로젝트별 Q&A 조회."""
        with patch(f"{self._rqa}.require_project_access", new_callable=AsyncMock, return_value=self._mock_proj), \
             patch(f"{self._rqa}.get_proposal_qa", new_callable=AsyncMock,
                   return_value=[
                       {"id": "qa-1", "proposal_id": "proj-001", "question": "Q1", "answer": "A1"},
                   ]):
            resp = await client.get("/api/proposals/proj-001/qa")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "count" in data

    async def test_update_qa(self, client):
        """개별 Q&A 수정."""
        with patch(f"{self._rqa}.require_project_access", new_callable=AsyncMock, return_value=self._mock_proj), \
             patch(f"{self._rqa}.update_qa_record", new_callable=AsyncMock,
                   return_value={"id": "qa-1", "question": "수정된 질문", "answer": "수정된 답변"}):
            resp = await client.put("/api/proposals/proj-001/qa/qa-1", json={
                "answer": "수정된 답변 내용입니다.",
            })
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data

    async def test_delete_qa(self, client):
        """개별 Q&A 삭제."""
        with patch(f"{self._rqa}.require_project_access", new_callable=AsyncMock, return_value=self._mock_proj), \
             patch(f"{self._rqa}.delete_qa_record", new_callable=AsyncMock, return_value=None):
            resp = await client.delete("/api/proposals/proj-001/qa/qa-1")
        assert resp.status_code == 204

    async def test_search_qa(self, client):
        """Q&A 검색."""
        with patch("app.services.qa_service.search_qa",
                   return_value=[
                       {"id": "qa-1", "question": "기술 질문", "answer": "기술 답변",
                        "similarity": 0.92, "proposal_name": "테스트", "client": "행정안전부"},
                   ]):
            resp = await client.get("/api/kb/qa/search?query=기술")
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert "count" in data

    async def test_search_qa_with_category(self, client):
        """카테고리 필터 Q&A 검색."""
        with patch("app.services.qa_service.search_qa", return_value=[]):
            resp = await client.get("/api/kb/qa/search?query=기술&category=technical&limit=5")
        assert resp.status_code == 200

    async def test_search_qa_missing_query_returns_422(self, client):
        """Q&A 검색 쿼리 누락 → 422."""
        resp = await client.get("/api/kb/qa/search")
        assert resp.status_code == 422


# ══════════════════════════════════════════════
# 9. KB 내보내기
# ══════════════════════════════════════════════

class TestKbExport:
    """KB CSV 내보내기."""

    @pytest.mark.parametrize("part", ["capabilities", "clients", "competitors", "content", "lessons"])
    async def test_export_valid_parts(self, client, part):
        """유효한 5개 파트 내보내기 → CSV 응답."""
        resp = await client.get(f"/api/kb/export/{part}")
        assert resp.status_code == 200
        assert "text/csv" in resp.headers.get("content-type", "")
        assert "attachment" in resp.headers.get("content-disposition", "")

    async def test_export_invalid_part_returns_400(self, client):
        """잘못된 파트 → 400."""
        resp = await client.get("/api/kb/export/invalid_table")
        assert resp.status_code == 400

    async def test_export_csv_has_headers(self, client):
        """CSV에 헤더 행 포함."""
        resp = await client.get("/api/kb/export/content")
        assert resp.status_code == 200
        text = resp.text
        # CSV 헤더에 id, title 포함
        assert "id" in text
        assert "title" in text


# ══════════════════════════════════════════════
# 10. 임베딩 서비스 — 단위
# ══════════════════════════════════════════════

class TestEmbeddingService:
    """임베딩 서비스 유닛 테스트."""

    async def test_generate_embedding_returns_1536_dims(self):
        """정상 임베딩 → 1536차원."""
        from app.services.embedding_service import generate_embedding

        mock_openai = AsyncMock()
        embed_obj = MagicMock()
        embed_obj.embedding = [0.1] * 1536
        mock_resp = MagicMock()
        mock_resp.data = [embed_obj]
        mock_openai.embeddings.create = AsyncMock(return_value=mock_resp)

        with patch("app.services.embedding_service._get_openai", return_value=mock_openai):
            result = await generate_embedding("클라우드 아키텍처")
        assert len(result) == 1536
        assert result[0] == 0.1

    async def test_generate_embedding_fallback_on_error(self):
        """OpenAI 에러 시 제로 벡터 폴백."""
        from app.services.embedding_service import generate_embedding

        mock_openai = AsyncMock()
        mock_openai.embeddings.create.side_effect = Exception("API error")

        with patch("app.services.embedding_service._get_openai", return_value=mock_openai):
            result = await generate_embedding("테스트")
        assert len(result) == 1536
        assert all(v == 0.0 for v in result)

    async def test_empty_text_returns_zero_vector(self):
        """빈 텍스트 → 제로 벡터."""
        from app.services.embedding_service import generate_embedding
        result = await generate_embedding("")
        assert len(result) == 1536

    def test_text_helpers_combine_fields(self):
        """텍스트 조합 헬퍼 검증."""
        from app.services.embedding_service import (
            embedding_text_for_content,
            embedding_text_for_client,
            embedding_text_for_competitor,
            embedding_text_for_lesson,
        )
        assert "MSA" in embedding_text_for_content("MSA 설계", "본문")
        assert "행정안전부" in embedding_text_for_client("행정안전부", "중앙부처")
        assert "삼성SDS" in embedding_text_for_competitor("삼성SDS", "SI", "대규모 사업")
        assert "가격 전략" in embedding_text_for_lesson("가격 전략", "효과적")


# ══════════════════════════════════════════════
# 11. Content Library 서비스 — 품질 점수
# ══════════════════════════════════════════════

class TestContentLibraryService:
    """콘텐츠 라이브러리 서비스 유닛."""

    async def test_quality_score_range(self):
        """품질 점수 0~100 범위."""
        from app.services.content_library import calculate_quality_score

        mock_sb = make_supabase_mock({
            "content_library": [{
                "won_count": 5,
                "lost_count": 1,
                "reuse_count": 10,
                "updated_at": "2026-03-01T00:00:00+00:00",
            }],
        })
        with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb):
            score = await calculate_quality_score("c1")
        assert isinstance(score, float)
        assert 0 <= score <= 100

    async def test_quality_score_zero_usage(self):
        """사용 이력 없는 콘텐츠 → 낮은 점수."""
        from app.services.content_library import calculate_quality_score

        mock_sb = make_supabase_mock({
            "content_library": [{
                "won_count": 0,
                "lost_count": 0,
                "reuse_count": 0,
                "updated_at": "2020-01-01T00:00:00+00:00",
            }],
        })
        with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb):
            score = await calculate_quality_score("c1")
        assert score <= 50


# ══════════════════════════════════════════════
# 12. Knowledge Search 서비스 — 단위
# ══════════════════════════════════════════════

class TestKnowledgeSearchService:
    """통합 검색 서비스."""

    async def test_unified_search_returns_dict(self):
        """unified_search → dict 형태."""
        from app.services.knowledge_search import unified_search

        mock_sb = make_supabase_mock()
        with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb), \
             patch("app.services.embedding_service.generate_embedding",
                   return_value=[0.0] * 1536):
            results = await unified_search("클라우드", "org-001")
        assert isinstance(results, dict)

    async def test_unified_search_with_area_filter(self):
        """영역 필터 적용."""
        from app.services.knowledge_search import unified_search

        mock_sb = make_supabase_mock()
        with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb), \
             patch("app.services.embedding_service.generate_embedding",
                   return_value=[0.0] * 1536):
            results = await unified_search(
                "ERP", "org-001",
                filters={"areas": ["content", "client"]},
            )
        assert isinstance(results, dict)


# ══════════════════════════════════════════════
# 13. KB Updater 서비스 — 성과 기반 자동 업데이트
# ══════════════════════════════════════════════

class TestKbUpdater:
    """성과 기반 KB 자동 업데이트."""

    async def test_trigger_kb_update_on_win(self):
        """수주 시 역량 후보 등록 호출."""
        from app.services.kb_updater import trigger_kb_update

        mock_sb = make_supabase_mock({
            "proposals": [{
                "id": "p1", "org_id": "org-001",
                "project_name": "클라우드 구축",
                "positioning": "offensive",
                "dynamic_sections": [],
            }],
        })
        with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb):
            # 에러 없이 실행되면 성공
            await trigger_kb_update("p1", "won")

    async def test_trigger_kb_update_on_loss(self):
        """패찰 시 경쟁사 정보 업데이트 호출."""
        from app.services.kb_updater import trigger_kb_update

        mock_sb = make_supabase_mock({
            "proposals": [{
                "id": "p1", "org_id": "org-001",
                "project_name": "AI 플랫폼 구축",
                "positioning": "defensive",
                "dynamic_sections": [],
            }],
        })
        with patch("app.utils.supabase_client.get_async_client", return_value=mock_sb):
            await trigger_kb_update("p1", "lost")

    def test_import_feedback_loop(self):
        """feedback_loop 모듈 import 가능."""
        from app.services.feedback_loop import process_project_completion
        assert callable(process_project_completion)


# ══════════════════════════════════════════════
# 14. 페이지네이션 + 정렬
# ══════════════════════════════════════════════

class TestPagination:
    """목록 API 페이지네이션 및 정렬."""

    async def test_content_pagination(self, client):
        """콘텐츠 목록 skip/limit."""
        resp = await client.get("/api/kb/content?skip=10&limit=5")
        assert resp.status_code == 200

    async def test_clients_pagination(self, client):
        """발주기관 목록 skip/limit."""
        resp = await client.get("/api/kb/clients?skip=0&limit=10")
        assert resp.status_code == 200

    async def test_competitors_pagination(self, client):
        """경쟁사 목록 skip/limit."""
        resp = await client.get("/api/kb/competitors?skip=5&limit=5")
        assert resp.status_code == 200

    async def test_lessons_pagination(self, client):
        """교훈 목록 skip/limit."""
        resp = await client.get("/api/kb/lessons?skip=0&limit=50")
        assert resp.status_code == 200

    async def test_market_prices_pagination(self, client):
        """시장 낙찰가 skip/limit."""
        resp = await client.get("/api/kb/market-prices?skip=0&limit=20")
        assert resp.status_code == 200
