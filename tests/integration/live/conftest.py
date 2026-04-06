"""Live 통합 테스트 fixture — Level 2.

실제 PostgreSQL, 실제 외부 API 연결.
pytest -m live 로 실행. 환경변수 필요.
"""

import os
import pytest


def pytest_collection_modifyitems(config, items):
    """live 마커가 없는 테스트는 이 디렉토리에서 자동 스킵."""
    pass  # 모든 테스트에 @pytest.mark.live가 붙어있으므로 별도 처리 불필요


@pytest.fixture(scope="session")
def require_live_env():
    """Live 테스트 환경변수 확인."""
    required = {
        "TEST_DATABASE_URL": os.getenv("TEST_DATABASE_URL"),
    }
    missing = [k for k, v in required.items() if not v]
    if missing:
        pytest.skip(f"Live 환경변수 누락: {', '.join(missing)}")
    return required


@pytest.fixture(scope="session")
async def pg_checkpointer(require_live_env):
    """실제 PostgreSQL AsyncPostgresSaver.

    테스트 완료 후 체크포인트 테이블은 유지 (재사용 가능).
    """
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

    db_url = require_live_env["TEST_DATABASE_URL"]
    checkpointer = AsyncPostgresSaver.from_conn_string(db_url)
    await checkpointer.setup()
    yield checkpointer


@pytest.fixture(scope="session")
async def live_supabase(require_live_env):
    """실제 Supabase 클라이언트 (테스트용)."""
    url = os.getenv("TEST_SUPABASE_URL") or os.getenv("SUPABASE_URL")
    key = os.getenv("TEST_SUPABASE_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        pytest.skip("Supabase 환경변수 누락")

    from supabase._async.client import create_client
    client = await create_client(url, key)
    yield client


@pytest.fixture
def require_g2b_key():
    """G2B API 키 확인."""
    key = os.getenv("G2B_API_KEY")
    if not key:
        pytest.skip("G2B_API_KEY 환경변수 누락")
    return key


@pytest.fixture
def require_searxng():
    """SearXNG URL 확인."""
    url = os.getenv("SEARXNG_URL")
    if not url:
        pytest.skip("SEARXNG_URL 환경변수 누락 (예: http://localhost:8080)")
    return url
