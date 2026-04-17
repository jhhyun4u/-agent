"""
공통 pytest fixture — 스테이징 환경 통합 테스트용

환경변수:
  STAGING_API_BASE_URL    스테이징 백엔드 URL (예: https://staging.tenopa.co.kr)
  E2E_USER_EMAIL          테스트 계정 이메일
  E2E_USER_PASSWORD       테스트 계정 비밀번호
  E2E_TEAM_ID             테스트용 팀 ID
  E2E_BID_NO              테스트용 실제 공고번호 (없으면 동적 검색)
  SUPABASE_URL            스테이징 Supabase URL
  SUPABASE_SERVICE_ROLE_KEY  서비스 롤 키 (teardown용)
"""

import os
from typing import AsyncGenerator
from pathlib import Path

import httpx
import pytest

# .env.test 파일 로드
from dotenv import load_dotenv
env_test_path = Path(__file__).parent.parent / ".env.test"
if env_test_path.exists():
    load_dotenv(env_test_path)


# ─────────────────────────────────────────────
# 환경변수 상수
# ─────────────────────────────────────────────

STAGING_BASE_URL = os.getenv("STAGING_API_BASE_URL", "http://localhost:8000")
E2E_USER_EMAIL = os.getenv("E2E_USER_EMAIL", "")
E2E_USER_PASSWORD = os.getenv("E2E_USER_PASSWORD", "")
E2E_TEAM_ID = os.getenv("E2E_TEAM_ID", "")
E2E_BID_NO = os.getenv("E2E_BID_NO", "")


# ─────────────────────────────────────────────
# 테스트 데이터 상수 (seed_test_data.py에서 생성)
# ─────────────────────────────────────────────

TEST_BIDS = {
    "standard": "E26BK00000001",      # 50M, 30일 (기준 충족)
    "high_budget": "E26BK00000002",   # 80M, 45일 (기준 초과)
    "low_budget": "E26BK00000003",    # 20M, 7일 (기준 미달)
    "expired": "E26BK00000004",       # 30M, 마감됨
}


# ─────────────────────────────────────────────
# 타임아웃 상수
# ─────────────────────────────────────────────

G2B_API_TIMEOUT = 30.0
AI_ANALYSIS_TIMEOUT = 60.0
POLL_INTERVAL = 3.0


# ─────────────────────────────────────────────
# 통합 인증 & 헤더 fixture (함수 scope)
# ─────────────────────────────────────────────

@pytest.fixture
def auth_headers() -> dict[str, str]:
    """인증 헤더 — DEV_MODE 자동 감지."""
    if os.getenv("DEV_MODE") == "true":
        token = os.getenv("DEV_USER_ID", "113a90c4-da41-4d60-8ca3-3f62c09325f3")
    elif E2E_USER_EMAIL and E2E_USER_PASSWORD:
        token = E2E_USER_EMAIL  # 기본값으로 이메일 사용
    else:
        pytest.skip("인증 정보 미설정 — E2E_USER_EMAIL/PASSWORD 또는 DEV_MODE 필요")

    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────────
# API 클라이언트 fixture
# ─────────────────────────────────────────────

@pytest.fixture
async def staging_api_client(auth_headers: dict[str, str]) -> AsyncGenerator[httpx.AsyncClient, None]:
    """스테이징 환경용 인증된 AsyncClient."""
    async with httpx.AsyncClient(
        base_url=STAGING_BASE_URL,
        headers=auth_headers,
        timeout=httpx.Timeout(G2B_API_TIMEOUT, read=AI_ANALYSIS_TIMEOUT),
    ) as client:
        yield client


# ─────────────────────────────────────────────
# 팀 ID fixture
# ─────────────────────────────────────────────

@pytest.fixture
async def test_team_id(staging_api_client: httpx.AsyncClient) -> str:
    """테스트용 팀 ID."""
    if E2E_TEAM_ID:
        return E2E_TEAM_ID

    if os.getenv("DEV_MODE") == "true":
        return os.getenv("DEV_USER_TEAM_ID", "00000000-0000-0000-0000-000000000002")

    response = await staging_api_client.get("/api/teams")
    if response.status_code != 200:
        pytest.skip(f"팀 조회 실패: {response.status_code}")

    data = response.json()
    teams = data.get("data", []) if isinstance(data, dict) else data if isinstance(data, list) else []
    if not teams:
        pytest.skip("테스트용 팀 없음")

    return teams[0]["id"]


# ─────────────────────────────────────────────
# 공고번호 fixture (다양한 시나리오)
# ─────────────────────────────────────────────

@pytest.fixture
async def real_bid_no(staging_api_client: httpx.AsyncClient, test_team_id: str) -> str:
    """실제 공고번호 확보 (폴백: 테스트 데이터 사용)."""
    # 1. 명시적으로 설정된 E2E_BID_NO 사용
    if E2E_BID_NO:
        return E2E_BID_NO

    # 2. API에서 실제 공고 조회 시도
    try:
        response = await staging_api_client.get(
            "/api/bids/monitor",
            params={"scope": "company", "page": 1, "per_page": 5},
        )

        if response.status_code == 200:
            data = response.json()
            items = data.get("data", [])
            if items:
                return items[0]["bid_no"]
    except Exception:
        # API 호출 실패 → 폴백 데이터 사용
        pass

    # 3. 폴백: 테스트 데이터 반환 (seed_test_data.py에서 생성됨)
    return TEST_BIDS["standard"]  # E2E_TEST_001 (50M, 기준 충족)


@pytest.fixture
def bid_no_by_scenario(request) -> str:
    """
    시나리오별 공고번호 반환.

    사용법:
      def test_something(bid_no_by_scenario):
          bid_no = bid_no_by_scenario  # E2E_TEST_001
    """
    scenario = request.param if hasattr(request, 'param') else "standard"
    return TEST_BIDS.get(scenario, TEST_BIDS["standard"])


# ─────────────────────────────────────────────
# 생성된 제안 정리 fixture
# ─────────────────────────────────────────────

@pytest.fixture
async def cleanup_test_proposals(staging_api_client: httpx.AsyncClient) -> AsyncGenerator[list, None]:
    """테스트 후 생성된 제안 정리."""
    created_ids = []
    yield created_ids

    if not created_ids:
        return

    for proposal_id in created_ids:
        try:
            await staging_api_client.delete(f"/api/proposals/{proposal_id}")
        except Exception:
            pass
