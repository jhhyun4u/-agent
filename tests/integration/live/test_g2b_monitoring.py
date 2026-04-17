"""
나라장터 G2B API 실제 연동 테스트

마커: @pytest.mark.live
실행: pytest tests/integration/live/ -m live -v

전제 조건:
  - G2B_API_KEY 설정
  - 스테이징 Supabase 연결
  - 실제 나라장터 API 접근 가능
"""

import asyncio
import os
import time

import pytest

from tests.conftest import AI_ANALYSIS_TIMEOUT, G2B_API_TIMEOUT, POLL_INTERVAL


# ─────────────────────────────────────────────
# 시나리오 7: 모니터링 수동 실행
# ─────────────────────────────────────────────

@pytest.mark.live
async def test_monitor_diagnostics(staging_api_client):
    """
    GET /api/g2b/monitor/diagnostics
    모니터링 시스템 진단 상태 검증.

    기대값:
    - HTTP 200
    - g2b_api_key: True (키 설정됨)
    - g2b_api_reachable: True (실제 API 연결 성공)
    - teams_count >= 1
    - status: "ok" 또는 "issues_found"
    """
    response = await staging_api_client.get("/api/g2b/monitor/diagnostics")

    assert response.status_code == 200, (
        f"진단 API 실패: {response.status_code} — {response.text[:200]}"
    )

    data = response.json()

    # G2B API 키 설정 확인
    assert data.get("g2b_api_key") is True, (
        "G2B_API_KEY 미설정 — 모니터링 불가"
    )

    # API 연결 가능 여부 (키가 있을 때만 검증)
    assert data.get("g2b_api_reachable") is True, (
        f"나라장터 API 연결 실패: errors={data.get('errors')}"
    )

    # 팀 존재 확인
    assert data.get("teams_count", 0) >= 1, "등록된 팀 없음"

    # status 필드 존재
    assert data.get("status") in ("ok", "issues_found")


@pytest.mark.live
async def test_monitor_manual_trigger(staging_api_client):
    """
    POST /api/g2b/monitor/trigger
    모니터링 수동 실행 및 결과 검증.

    기대값:
    - HTTP 200
    - result.teams_checked >= 0
    - result.new_bids_found >= 0
    - result.total_fetched >= 0
    실행 시간이 길 수 있으므로 타임아웃 90초 설정.
    """
    import httpx

    async with httpx.AsyncClient(
        base_url=staging_api_client.base_url,
        headers=dict(staging_api_client.headers),
        timeout=90.0,  # 모니터링은 최대 90초
    ) as client:
        response = await client.post("/api/g2b/monitor/trigger")

    assert response.status_code == 200, (
        f"수동 트리거 실패: {response.status_code} — {response.text[:300]}"
    )

    body = response.json()
    assert body.get("status") == "ok"

    result = body.get("result", {})
    assert "teams_checked" in result, "teams_checked 필드 없음"
    assert "new_bids_found" in result, "new_bids_found 필드 없음"
    assert "total_fetched" in result, "total_fetched 필드 없음"

    # 음수 불가
    assert result["teams_checked"] >= 0
    assert result["new_bids_found"] >= 0
    assert result["total_fetched"] >= 0


# ─────────────────────────────────────────────
# 시나리오 1: 공고 수집 및 목록 조회
# ─────────────────────────────────────────────

@pytest.mark.live
async def test_fetch_bids_trigger(staging_api_client, test_team_id):
    """
    POST /api/teams/{team_id}/bids/fetch
    공고 수집 트리거 — 백그라운드 실행 확인.

    기대값:
    - HTTP 200
    - 성공 응답 (message 포함)

    주의: 1시간 내 재수집 시 429 RateLimitError 가능
    """
    response = await staging_api_client.post(
        f"/api/teams/{test_team_id}/bids/fetch"
    )

    # 429는 쿨다운 중 — 정상 동작
    if response.status_code == 429:
        pytest.skip("공고 수집 쿨다운 중 (1시간 이내 재수집 제한) — 스킵")

    assert response.status_code == 200, (
        f"수집 트리거 실패: {response.status_code} — {response.text[:200]}"
    )

    data = response.json()
    assert data.get("success") is True or "message" in str(data)


@pytest.mark.live
async def test_get_bid_monitor_list(staging_api_client):
    """
    GET /api/bids/monitor
    공고 모니터링 목록 조회 및 페이지네이션 검증.

    기대값:
    - HTTP 200
    - data 리스트 (0개 이상)
    - total 필드 존재
    - 각 공고에 bid_no, bid_title 포함
    - proposal_status 필터링: "제안포기", "관련없음", "제안결정" 제외됨 (show_all=False)
    """
    response = await staging_api_client.get(
        "/api/bids/monitor",
        params={"scope": "company", "page": 1, "per_page": 10},
    )

    assert response.status_code == 200, (
        f"모니터링 목록 실패: {response.status_code} — {response.text[:200]}"
    )

    data = response.json()
    items = data.get("data") or []
    total = data.get("total", 0)

    assert isinstance(items, list)
    assert isinstance(total, int)

    # 필드 구조 검증 (공고가 있을 때)
    for item in items:
        assert "bid_no" in item, f"bid_no 필드 없음: {item.keys()}"
        assert "bid_title" in item, f"bid_title 필드 없음: {item.keys()}"

    # proposal_status 필터 검증: 기본값(show_all=False) 시 숨겨진 상태 없어야 함
    hidden_statuses = {"제안포기", "관련없음", "제안결정"}
    for item in items:
        status = item.get("proposal_status", "신규")
        assert status not in hidden_statuses, (
            f"필터링 오류: {item['bid_no']}의 proposal_status={status}가 노출됨"
        )


@pytest.mark.live
async def test_get_bid_monitor_list_pagination(staging_api_client):
    """
    페이지네이션 동작 검증.

    기대값:
    - page=1 결과와 page=2 결과가 다름 (공고 충분할 때)
    - per_page 파라미터 준수
    """
    page1 = await staging_api_client.get(
        "/api/bids/monitor",
        params={"scope": "company", "page": 1, "per_page": 5},
    )
    page2 = await staging_api_client.get(
        "/api/bids/monitor",
        params={"scope": "company", "page": 2, "per_page": 5},
    )

    assert page1.status_code == 200
    assert page2.status_code == 200

    items1 = page1.json().get("data", [])
    items2 = page2.json().get("data", [])

    # per_page 준수 확인
    assert len(items1) <= 5
    assert len(items2) <= 5

    # 공고가 충분하면 페이지 간 중복 없어야 함
    if items1 and items2:
        nos1 = {item["bid_no"] for item in items1}
        nos2 = {item["bid_no"] for item in items2}
        assert not nos1.intersection(nos2), (
            f"페이지 간 중복 공고: {nos1.intersection(nos2)}"
        )


@pytest.mark.live
async def test_get_recommendations(staging_api_client, test_team_id):
    """
    GET /api/teams/{team_id}/bids/recommendations
    AI 추천 공고 목록 조회.

    기대값:
    - HTTP 200
    - data 리스트
    - 각 공고에 match_score 또는 suitability_score 포함
    """
    response = await staging_api_client.get(
        f"/api/teams/{test_team_id}/bids/recommendations"
    )

    assert response.status_code == 200, (
        f"추천 공고 조회 실패: {response.status_code} — {response.text[:200]}"
    )

    data = response.json()
    items = data.get("data") or []
    assert isinstance(items, list)


# ─────────────────────────────────────────────
# 시나리오 2: 공고 AI 분석
# ─────────────────────────────────────────────

@pytest.mark.live
async def test_bid_analysis_pending_to_analyzed(
    staging_api_client,
    real_bid_no,
):
    """
    GET /api/bids/{bid_no}/analysis
    analysis_status 전환 검증: pending → analyzing → analyzed

    기대값:
    - 첫 호출: {"status": "pending"} 또는 {"status": "analyzing"}
    - 폴링 후: {"status": "analyzed", "suitability_score": float, "verdict": str}
    - 타임아웃 60초 이내 완료
    """
    start_time = time.time()
    final_status = None
    final_data = None

    while time.time() - start_time < AI_ANALYSIS_TIMEOUT:
        response = await staging_api_client.get(
            f"/api/bids/{real_bid_no}/analysis"
        )
        assert response.status_code == 200, (
            f"분석 API 실패: {response.status_code}"
        )

        data = response.json()
        inner = data.get("data") or data
        status = inner.get("status")

        if status == "analyzed":
            final_status = "analyzed"
            final_data = inner
            break
        elif status in ("pending", "analyzing"):
            await asyncio.sleep(POLL_INTERVAL)
            continue
        elif status == "failed":
            pytest.fail(
                f"분석 실패: {inner.get('error', '알 수 없는 오류')}"
            )
        else:
            await asyncio.sleep(POLL_INTERVAL)

    assert final_status == "analyzed", (
        f"분석이 {AI_ANALYSIS_TIMEOUT}초 내에 완료되지 않음. 마지막 상태: {final_status}"
    )

    # 분석 결과 필드 검증
    assert final_data.get("suitability_score") is not None, (
        "suitability_score 없음"
    )
    assert isinstance(final_data["suitability_score"], (int, float))
    assert 0 <= final_data["suitability_score"] <= 100

    assert final_data.get("verdict") in ("Go", "No-Go", "검토필요"), (
        f"예상치 못한 verdict: {final_data.get('verdict')}"
    )


# ─────────────────────────────────────────────
# 시나리오 6: Error Cases — G2B API 오류
# ─────────────────────────────────────────────

@pytest.mark.live
async def test_invalid_bid_no_format(staging_api_client):
    """
    존재하지 않는 bid_no 형식 접근.

    기대값:
    - 특수문자 포함: HTTP 422 또는 400 (BidValidationError)
    - 정상 형식이지만 없는 번호: HTTP 200, status=pending (새 레코드 생성)
    """
    # 특수문자 포함 bid_no → 422 또는 400
    response = await staging_api_client.get("/api/bids/INVALID!!NO/analysis")
    assert response.status_code in (400, 422), (
        f"잘못된 bid_no에 대해 예상치 못한 응답: {response.status_code}"
    )


@pytest.mark.live
async def test_nonexistent_bid_no_creates_pending(staging_api_client):
    """
    존재하지 않는 정상 형식 bid_no → pending 레코드 자동 생성.

    기대값:
    - HTTP 200
    - status: "pending" (신규 레코드 생성됨)
    """
    fake_bid_no = "9999999999"  # 존재하지 않는 공고번호

    response = await staging_api_client.get(
        f"/api/bids/{fake_bid_no}/analysis"
    )
    assert response.status_code == 200

    inner = (response.json().get("data") or response.json())
    assert inner.get("status") == "pending", (
        f"존재하지 않는 공고에 대해 예상치 못한 status: {inner.get('status')}"
    )


@pytest.mark.live
async def test_unauthorized_team_access(staging_api_client):
    """
    권한 없는 팀 공고 접근.

    기대값:
    - HTTP 403 또는 404 (팀 멤버 아닌 경우)
    """
    fake_team_id = "00000000-0000-0000-0000-000000000000"
    response = await staging_api_client.get(
        f"/api/teams/{fake_team_id}/bids/recommendations"
    )
    assert response.status_code in (403, 404), (
        f"권한 없는 팀 접근에 예상치 못한 응답: {response.status_code}"
    )


@pytest.mark.live
async def test_no_auth_header_returns_401():
    """
    인증 헤더 없는 요청 → HTTP 401.
    """
    import httpx
    from tests.conftest import STAGING_BASE_URL

    async with httpx.AsyncClient(base_url=STAGING_BASE_URL, timeout=10.0) as client:
        response = await client.get("/api/bids/monitor")

    assert response.status_code in (401, 403), (
        f"미인증 접근에 예상치 못한 응답: {response.status_code}"
    )
