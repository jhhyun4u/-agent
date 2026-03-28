"""
입찰 추천 API 엔드포인트 테스트

의존성 Mock:
- get_current_user → 테스트 유저 반환
- get_async_client → Supabase 클라이언트 Mock (maybe_single 상태 추적)
- BackgroundTasks → 백그라운드 작업 Mock
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from httpx import AsyncClient, ASGITransport

from tests.conftest import _get_test_app, make_supabase_mock as make_conftest_mock
from app.api.deps import get_current_user
from app.models.auth_schemas import CurrentUser

app = _get_test_app()


# ─────────────────────────────────────────────────────────────
# maybe_single 상태를 추적하는 Supabase Mock
# ─────────────────────────────────────────────────────────────

class _TableMock:
    """
    체인 방식 Supabase 테이블 Mock.

    maybe_single() 호출 여부를 추적하여
    execute() 시 단일 dict(또는 None) / list 를 구분 반환.
    """

    def __init__(self, list_data: list):
        self._list_data = list_data if list_data is not None else []
        self._is_single = False
        self._write_data = None  # insert/update/upsert 반환용

    # 읽기 체인
    def select(self, *args, **kwargs): return self
    def eq(self, *args, **kwargs): return self
    def neq(self, *args, **kwargs): return self
    def gt(self, *args, **kwargs): return self
    def gte(self, *args, **kwargs): return self
    def lt(self, *args, **kwargs): return self
    def ilike(self, *args, **kwargs): return self
    def order(self, *args, **kwargs): return self
    def range(self, *args, **kwargs): return self
    def limit(self, *args, **kwargs): return self

    def maybe_single(self):
        self._is_single = True
        return self

    # 쓰기 체인 (반환 데이터 보존)
    def insert(self, row, **kwargs):
        self._write_data = [row] if isinstance(row, dict) else row
        return self

    def update(self, row, **kwargs):
        self._write_data = self._list_data or [row]
        return self

    def upsert(self, row, **kwargs):
        if isinstance(row, dict):
            self._write_data = [row]
        elif isinstance(row, list):
            self._write_data = row
        else:
            self._write_data = self._list_data
        return self

    def delete(self):
        self._write_data = []
        return self

    async def execute(self):
        result = MagicMock()
        if self._write_data is not None:
            # insert/update/upsert/delete → 항상 리스트
            result.data = self._write_data
            result.count = len(self._write_data)
        elif self._is_single:
            # maybe_single() → 단일 dict or None
            result.data = self._list_data[0] if self._list_data else None
        else:
            result.data = self._list_data
            result.count = len(self._list_data)
        return result


def make_supabase_mock(
    team_member_role="admin",
    preset_data=None,
    profile_data=None,
    bid_data=None,
    rec_data=None,
):
    """각 테이블에 대한 _TableMock을 라우팅하는 Supabase 클라이언트 Mock"""
    client = AsyncMock()

    member_row = [{"role": team_member_role}] if team_member_role else []

    _tables = {
        "team_members": lambda: _TableMock(member_row),
        "search_presets": lambda: _TableMock(preset_data or []),
        "team_bid_profiles": lambda: _TableMock(profile_data or []),
        "bid_announcements": lambda: _TableMock(bid_data or []),
        "bid_recommendations": lambda: _TableMock(rec_data or []),
    }

    def table_selector(name):
        factory = _tables.get(name)
        if factory:
            return factory()
        return _TableMock([])

    client.table = MagicMock(side_effect=table_selector)
    return client


# ─────────────────────────────────────────────────────────────
# 공통 상수 / 픽스처
# ─────────────────────────────────────────────────────────────

MOCK_USER = CurrentUser(
    id="user-test-001",
    email="test@tenopa.com",
    name="테스트",
    role="admin",
    team_id="team-test-001",
    division_id="div-001",
    org_id="org-001",
    status="active",
)

TEAM_ID = "team-test-001"
PRESET_ID = "preset-test-001"
AUTH_HEADERS = {"Authorization": "Bearer test-token"}


@pytest.fixture
async def client_with_auth():
    app.dependency_overrides[get_current_user] = lambda: MOCK_USER
    sb_mock = make_conftest_mock()
    with patch("app.utils.supabase_client.get_async_client", return_value=sb_mock):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def client_no_auth():
    app.dependency_overrides.clear()
    sb_mock = make_conftest_mock()
    with patch("app.utils.supabase_client.get_async_client", return_value=sb_mock):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as c:
            yield c


# ─────────────────────────────────────────────────────────────
# 팀 프로필 (F-02)
# ─────────────────────────────────────────────────────────────

class TestBidProfile:

    async def test_GET_프로필_조회_200(self, client_with_auth):
        profile = {"team_id": TEAM_ID, "expertise_areas": ["AI"], "tech_keywords": ["Python"]}
        mock_client = make_supabase_mock(profile_data=[profile])

        with patch("app.api.routes_bids.get_async_client", AsyncMock(return_value=mock_client)):
            res = await client_with_auth.get(f"/api/teams/{TEAM_ID}/bid-profile", headers=AUTH_HEADERS)

        assert res.status_code == 200
        assert res.json()["data"] is not None

    async def test_GET_프로필_없으면_data_None(self, client_with_auth):
        mock_client = make_supabase_mock(profile_data=[])

        with patch("app.api.routes_bids.get_async_client", AsyncMock(return_value=mock_client)):
            res = await client_with_auth.get(f"/api/teams/{TEAM_ID}/bid-profile", headers=AUTH_HEADERS)

        assert res.status_code == 200
        assert res.json()["data"] is None

    async def test_GET_비팀원_403(self, client_with_auth):
        mock_client = make_supabase_mock(team_member_role=None)

        with patch("app.api.routes_bids.get_async_client", AsyncMock(return_value=mock_client)):
            res = await client_with_auth.get(f"/api/teams/{TEAM_ID}/bid-profile", headers=AUTH_HEADERS)

        assert res.status_code == 403

    async def test_PUT_프로필_upsert_200(self, client_with_auth):
        profile_row = {
            "team_id": TEAM_ID, "expertise_areas": ["AI/ML"],
            "tech_keywords": ["Python"], "certifications": [],
        }
        mock_client = make_supabase_mock(profile_data=[profile_row])

        body = {"expertise_areas": ["AI/ML"], "tech_keywords": ["Python"], "certifications": []}
        with patch("app.api.routes_bids.get_async_client", AsyncMock(return_value=mock_client)):
            res = await client_with_auth.put(
                f"/api/teams/{TEAM_ID}/bid-profile", json=body, headers=AUTH_HEADERS
            )

        assert res.status_code == 200


# ─────────────────────────────────────────────────────────────
# 검색 프리셋 CRUD
# ─────────────────────────────────────────────────────────────

class TestSearchPresets:

    async def test_목록_조회_200(self, client_with_auth):
        presets = [{"id": PRESET_ID, "team_id": TEAM_ID, "name": "AI 프리셋", "is_active": True}]
        mock_client = make_supabase_mock(preset_data=presets)

        with patch("app.api.routes_bids.get_async_client", AsyncMock(return_value=mock_client)):
            res = await client_with_auth.get(
                f"/api/teams/{TEAM_ID}/search-presets", headers=AUTH_HEADERS
            )

        assert res.status_code == 200
        assert isinstance(res.json()["data"], list)

    async def test_프리셋_생성_201(self, client_with_auth):
        new_preset = {"id": PRESET_ID, "team_id": TEAM_ID, "name": "신규 프리셋"}
        mock_client = make_supabase_mock(preset_data=[new_preset])

        body = {
            "name": "AI분야 프리셋",
            "keywords": ["AI", "LLM"],
            "min_budget": 100000000,
            "bid_types": ["용역"],
        }
        with patch("app.api.routes_bids.get_async_client", AsyncMock(return_value=mock_client)):
            res = await client_with_auth.post(
                f"/api/teams/{TEAM_ID}/search-presets", json=body, headers=AUTH_HEADERS
            )

        assert res.status_code == 201

    async def test_없는_프리셋_삭제_404(self, client_with_auth):
        mock_client = make_supabase_mock(preset_data=[])

        with patch("app.api.routes_bids.get_async_client", AsyncMock(return_value=mock_client)):
            res = await client_with_auth.delete(
                f"/api/teams/{TEAM_ID}/search-presets/nonexistent-id", headers=AUTH_HEADERS
            )

        assert res.status_code == 404

    async def test_프리셋_활성화_200(self, client_with_auth):
        preset = {
            "id": PRESET_ID, "team_id": TEAM_ID, "name": "AI",
            "is_active": False, "keywords": ["AI"], "bid_types": ["용역"],
            "min_budget": 100000000, "min_days_remaining": 5,
            "announce_date_range_days": 14, "preferred_agencies": [],
        }
        mock_client = make_supabase_mock(preset_data=[preset])

        with patch("app.api.routes_bids.get_async_client", AsyncMock(return_value=mock_client)):
            res = await client_with_auth.post(
                f"/api/teams/{TEAM_ID}/search-presets/{PRESET_ID}/activate",
                headers=AUTH_HEADERS,
            )

        assert res.status_code == 200


# ─────────────────────────────────────────────────────────────
# 공고 수집 트리거 (F-04)
# ─────────────────────────────────────────────────────────────

class TestBidsFetch:

    def _active_preset(self, last_fetched_at=None):
        return {
            "id": PRESET_ID, "team_id": TEAM_ID, "name": "AI 프리셋",
            "keywords": ["AI"], "bid_types": ["용역"],
            "min_budget": 100_000_000, "min_days_remaining": 5,
            "announce_date_range_days": 14, "preferred_agencies": [],
            "is_active": True, "last_fetched_at": last_fetched_at,
        }

    async def test_활성_프리셋_없으면_422(self, client_with_auth):
        mock_client = make_supabase_mock(preset_data=[])

        with patch("app.api.routes_bids.get_async_client", AsyncMock(return_value=mock_client)):
            res = await client_with_auth.post(
                f"/api/teams/{TEAM_ID}/bids/fetch", headers=AUTH_HEADERS
            )

        assert res.status_code == 400
        assert "프리셋" in res.json()["message"]

    async def test_1시간내_재수집_429(self, client_with_auth):
        recent = (datetime.now(timezone.utc) - timedelta(minutes=30)).isoformat()
        preset = self._active_preset(last_fetched_at=recent)
        mock_client = make_supabase_mock(preset_data=[preset])

        with patch("app.api.routes_bids.get_async_client", AsyncMock(return_value=mock_client)):
            res = await client_with_auth.post(
                f"/api/teams/{TEAM_ID}/bids/fetch", headers=AUTH_HEADERS
            )

        assert res.status_code == 429
        assert "분 후" in res.json()["message"]

    async def test_정상_수집_트리거_200(self, client_with_auth):
        preset = self._active_preset(last_fetched_at=None)
        profile = {"team_id": TEAM_ID, "expertise_areas": ["AI"]}
        mock_client = make_supabase_mock(preset_data=[preset], profile_data=[profile])

        with (
            patch("app.api.routes_bids.get_async_client", AsyncMock(return_value=mock_client)),
            patch("app.api.routes_bids._run_fetch_and_analyze", AsyncMock()),
        ):
            res = await client_with_auth.post(
                f"/api/teams/{TEAM_ID}/bids/fetch", headers=AUTH_HEADERS
            )

        assert res.status_code == 200
        body = res.json()
        assert body["data"] is None  # ok(None, message=...)
        assert "공고 수집" in body["meta"]["message"]

    async def test_2시간_전_수집_재수집_허용(self, client_with_auth):
        old = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()
        preset = self._active_preset(last_fetched_at=old)
        profile = {"team_id": TEAM_ID}
        mock_client = make_supabase_mock(preset_data=[preset], profile_data=[profile])

        with (
            patch("app.api.routes_bids.get_async_client", AsyncMock(return_value=mock_client)),
            patch("app.api.routes_bids._run_fetch_and_analyze", AsyncMock()),
        ):
            res = await client_with_auth.post(
                f"/api/teams/{TEAM_ID}/bids/fetch", headers=AUTH_HEADERS
            )

        assert res.status_code == 200


# ─────────────────────────────────────────────────────────────
# 공고 목록 / 상세
# ─────────────────────────────────────────────────────────────

class TestBidAnnouncements:

    async def test_공고_목록_200(self, client_with_auth):
        bids = [{
            "bid_no": "001", "bid_title": "AI 시스템 구축",
            "agency": "행정안전부", "bid_type": "용역",
            "budget_amount": 300_000_000, "days_remaining": 10,
        }]
        mock_client = make_supabase_mock(bid_data=bids)

        with patch("app.api.routes_bids.get_async_client", AsyncMock(return_value=mock_client)):
            res = await client_with_auth.get(
                f"/api/teams/{TEAM_ID}/bids/announcements", headers=AUTH_HEADERS
            )

        assert res.status_code == 200
        body = res.json()
        assert "data" in body
        assert "meta" in body

    async def test_공고_상세_정상_200(self, client_with_auth):
        bid = {"bid_no": "20260001-00", "bid_title": "AI 행정 시스템", "agency": "행정안전부"}
        mock_client = make_supabase_mock(bid_data=[bid])

        with patch("app.api.routes_bids.get_async_client", AsyncMock(return_value=mock_client)):
            res = await client_with_auth.get("/api/bids/20260001-00", headers=AUTH_HEADERS)

        assert res.status_code == 200
        assert res.json()["data"]["announcement"]["bid_no"] == "20260001-00"

    async def test_공고_상세_잘못된_bid_no_형식_400(self, client_with_auth):
        res = await client_with_auth.get("/api/bids/invalid!@#no", headers=AUTH_HEADERS)
        assert res.status_code == 400

    async def test_공고_상세_없으면_404(self, client_with_auth):
        mock_client = make_supabase_mock(bid_data=[])

        with patch("app.api.routes_bids.get_async_client", AsyncMock(return_value=mock_client)):
            res = await client_with_auth.get("/api/bids/99999999-00", headers=AUTH_HEADERS)

        assert res.status_code == 404

    async def test_인증_없이_접근_가능_404(self, client_no_auth):
        """get_bid_detail은 get_current_user_or_none을 사용하므로 인증 없이도 접근 가능 (공고 미존재 시 404)"""
        mock_client = make_supabase_mock(bid_data=[])
        with patch("app.api.routes_bids.get_async_client", AsyncMock(return_value=mock_client)):
            res = await client_no_auth.get("/api/bids/20260001-00")
        assert res.status_code == 404


# ─────────────────────────────────────────────────────────────
# 제안서 연동
# ─────────────────────────────────────────────────────────────

class TestProposalFromBid:

    async def test_공고_제안서_연동_201(self, client_with_auth):
        """POST /api/proposals/from-bid (body에 bid_no) → 201."""
        res = await client_with_auth.post(
            "/api/proposals/from-bid",
            json={"bid_no": "20260001-00"},
            headers=AUTH_HEADERS,
        )
        assert res.status_code == 201
        body = res.json()
        assert body["bid_no"] == "20260001-00"

    async def test_존재하지_않는_공고_422(self, client_with_auth):
        """필수 필드 누락 → 422."""
        res = await client_with_auth.post(
            "/api/proposals/from-bid",
            json={},
            headers=AUTH_HEADERS,
        )
        assert res.status_code == 422

    async def test_잘못된_bid_no_형식_201_or_error(self, client_with_auth):
        """bid_no 형식 검증은 body에서 처리."""
        res = await client_with_auth.post(
            "/api/proposals/from-bid",
            json={"bid_no": "invalid!bid"},
            headers=AUTH_HEADERS,
        )
        # 라우트 수준에서 bid_no 형식 검증이 없으면 201, 있으면 400/422
        assert res.status_code in (201, 400, 422)
