"""pytest 공통 설정 및 fixtures — 외부 의존성 mock"""
import pytest
import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from app.models.auth_schemas import CurrentUser


# ── 이벤트 루프 ──

@pytest.fixture(scope="session")
def event_loop():
    """세션 전체에서 사용할 이벤트 루프"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ── 출력 디렉토리 ──

@pytest.fixture
def output_dir(tmp_path) -> Path:
    output = tmp_path / "output"
    output.mkdir(exist_ok=True)
    return output


# ── Mock 사용자 ──

@pytest.fixture
def mock_user():
    """기본 admin 사용자."""
    return CurrentUser(
        id="user-001",
        email="admin@tenopa.com",
        name="관리자",
        role="admin",
        team_id="team-001",
        division_id="div-001",
        org_id="org-001",
        status="active",
    )


@pytest.fixture
def mock_member_user():
    """일반 멤버 사용자."""
    return CurrentUser(
        id="user-002",
        email="member@tenopa.com",
        name="팀원",
        role="member",
        team_id="team-001",
        division_id="div-001",
        org_id="org-001",
        status="active",
    )


@pytest.fixture
def mock_lead_user():
    """팀장 사용자."""
    return CurrentUser(
        id="user-003",
        email="lead@tenopa.com",
        name="팀장",
        role="lead",
        team_id="team-001",
        division_id="div-001",
        org_id="org-001",
        status="active",
    )


# ── Supabase Mock ──

class MockQueryBuilder:
    """Supabase 쿼리 빌더 체이닝 mock."""

    def __init__(self, data=None, count=None):
        self._data = data or []
        self._count = count
        self._is_single = False
        self._filters = []  # [(key, value, op), ...]

    def _chain(self):
        return self

    # 체이닝 메서드
    select = property(lambda self: lambda *a, **kw: self._chain())
    insert = property(lambda self: lambda *a, **kw: self._chain())
    update = property(lambda self: lambda *a, **kw: self._chain())
    delete = property(lambda self: lambda *a, **kw: self._chain())
    upsert = property(lambda self: lambda *a, **kw: self._chain())

    def eq(self, key, value):
        """필터 추가: key == value"""
        self._filters.append((key, value, "=="))
        return self

    neq = property(lambda self: lambda *a, **kw: self._chain())
    gt = property(lambda self: lambda *a, **kw: self._chain())
    gte = property(lambda self: lambda *a, **kw: self._chain())
    lt = property(lambda self: lambda *a, **kw: self._chain())
    lte = property(lambda self: lambda *a, **kw: self._chain())
    ilike = property(lambda self: lambda *a, **kw: self._chain())
    in_ = property(lambda self: lambda *a, **kw: self._chain())
    is_ = property(lambda self: lambda *a, **kw: self._chain())
    or_ = property(lambda self: lambda *a, **kw: self._chain())
    contains = property(lambda self: lambda *a, **kw: self._chain())
    not_ = property(lambda self: MagicMock(is_=lambda *a, **kw: self._chain()))
    order = property(lambda self: lambda *a, **kw: self._chain())
    limit = property(lambda self: lambda *a, **kw: self._chain())
    range = property(lambda self: lambda *a, **kw: self._chain())

    def single(self):
        """단일 레코드 조회 (있으면 반환, 없으면 error)"""
        self._is_single = True
        return self

    def maybe_single(self):
        """단일 레코드 조회 (있으면 반환, 없으면 None)"""
        self._is_single = True
        return self

    def _apply_filters(self, data):
        """필터 적용 헬퍼"""
        if not self._filters:
            return data

        if isinstance(data, list):
            filtered = data
            for key, value, op in self._filters:
                if op == "==":
                    filtered = [item for item in filtered if isinstance(item, dict) and item.get(key) == value]
            return filtered
        elif isinstance(data, dict):
            for key, value, op in self._filters:
                if op == "==" and data.get(key) != value:
                    return None
            return data
        return data

    async def execute(self):
        result = MagicMock()
        # 필터 적용
        filtered_data = self._apply_filters(self._data)

        # single/maybe_single 호출 시 첫 원소만 반환
        if self._is_single:
            if isinstance(filtered_data, list):
                result.data = filtered_data[0] if filtered_data else None
            else:
                result.data = filtered_data
        else:
            result.data = filtered_data
        result.count = self._count
        return result


def make_supabase_mock(table_data=None):
    """Supabase 클라이언트 mock 생성.

    table_data: {"proposals": [...], "users": [...]} 형태로 테이블별 데이터 설정.
    """
    table_data = table_data or {}
    mock_client = AsyncMock()

    def _table(name):
        data = table_data.get(name, [])
        return MockQueryBuilder(data)

    mock_client.table = _table

    # rpc mock
    rpc_mock = AsyncMock()
    rpc_result = MagicMock()
    rpc_result.data = None
    rpc_mock.execute = AsyncMock(return_value=rpc_result)
    mock_client.rpc = MagicMock(return_value=rpc_mock)

    # auth mock
    mock_client.auth = AsyncMock()

    # storage mock
    mock_client.storage = AsyncMock()
    mock_client.storage.create_bucket = AsyncMock()

    return mock_client


# ── 테스트용 FastAPI 앱 ──

_test_app = None


def _get_test_app():
    """테스트용 FastAPI app (lifespan mock 적용)."""
    global _test_app
    if _test_app is not None:
        return _test_app

    # 모듈을 먼저 import해서 patch 경로가 해석 가능하도록
    import app.utils.supabase_client  # noqa: F401
    import app.api.deps  # noqa: F401
    import app.services.session_manager  # noqa: F401

    supabase_mock = make_supabase_mock()
    session_mock = MagicMock()
    session_mock.startup_load = AsyncMock(return_value=0)
    session_mock.get_session_count = MagicMock(return_value=0)

    with patch("app.utils.supabase_client.get_async_client", return_value=supabase_mock), \
         patch("app.services.session_manager.session_manager", session_mock):
        from app.main import app
        _test_app = app
    return _test_app


# 모듈 로드 시 미리 app을 import (patch 경로가 해석 가능하도록)
_get_test_app()


# ── httpx AsyncClient fixture ──

@pytest.fixture
async def client(mock_user):
    """FastAPI 테스트 클라이언트 (인증 mock + Supabase mock)."""
    from httpx import AsyncClient, ASGITransport
    from app.api.deps import get_current_user, get_rls_client, require_project_access

    app = _get_test_app()

    # 테스트용 문서 데이터
    test_document = {
        "id": "test-doc-001",
        "org_id": "org-001",
        "title": "Test Document",
        "processing_status": "completed",
        "storage_path": "documents/test-doc.pdf",
    }

    supabase_mock = make_supabase_mock(
        table_data={
            "intranet_documents": [test_document],
        }
    )

    # FastAPI dependency override — 모든 엔드포인트에서 인증 우회
    app.dependency_overrides[get_current_user] = lambda: mock_user
    app.dependency_overrides[get_rls_client] = lambda: supabase_mock
    app.dependency_overrides[require_project_access] = lambda: {"id": "test-id", "title": "테스트", "status": "initialized"}

    # Patch get_async_client at usage location (must patch where it's imported, not where it's defined)
    # For test_create_from_bid, we need to patch routes_proposal
    with patch("app.api.routes_proposal.get_async_client", return_value=supabase_mock), \
         patch("app.utils.supabase_client.get_async_client", return_value=supabase_mock):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            ac._supabase_mock = supabase_mock
            yield ac

    # cleanup
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_rls_client, None)
    app.dependency_overrides.pop(require_project_access, None)


# ── 기존 fixtures 유지 ──

@pytest.fixture
def mock_rfp_document() -> str:
    return """제안요청서
사업명: 클라우드 기반 ERP 시스템 구축
발주기관: ABC 주식회사
예산: 5억원
기간: 6개월"""


@pytest.fixture
def skip_if_no_api_key():
    import os
    if not os.getenv("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
