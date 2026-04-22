"""
공고 → 제안 결정 전체 워크플로우 통합 테스트

테스트 실행:
  # live 마커 포함 실행
  pytest tests/integration/ tests/integration/live/ -m live -v --timeout=120

시나리오 3,4,5,8 커버
"""

import asyncio
import time

import pytest

from tests.conftest import AI_ANALYSIS_TIMEOUT, POLL_INTERVAL


# ─────────────────────────────────────────────
# 시나리오 3: 제안결정 (Go Decision) — Happy Path
# ─────────────────────────────────────────────

@pytest.mark.live
async def test_go_decision_full_flow(
    staging_api_client,
    real_bid_no,
    cleanup_test_proposals,
):
    """
    전체 Go Decision 흐름:
    1. PUT /api/bids/{bid_no}/status → "제안결정"
    2. DB 검증: verdict = "Go", proposal_status = "제안결정"
    3. POST /api/proposals/from-bid → 제안 프로젝트 생성
    4. GET /api/proposals/{id} → status="initialized", go_decision=True, source_bid_no 확인

    기대값:
    - Step 1: HTTP 200, status="제안결정"
    - Step 3: HTTP 201, proposal_id 반환
    - Step 4: status="initialized", go_decision=True, source_bid_no=real_bid_no
    """
    # ── Step 1: 공고 상태 "제안결정"으로 변경 ──
    status_response = await staging_api_client.put(
        f"/api/bids/{real_bid_no}/status",
        json={"status": "제안결정"},
    )

    assert status_response.status_code == 200, (
        f"상태 변경 실패: {status_response.status_code} — {status_response.text[:200]}"
    )

    status_data = status_response.json()
    inner = status_data.get("data") or status_data
    assert inner.get("status") == "제안결정", (
        f"status 불일치: {inner.get('status')}"
    )
    assert inner.get("bid_no") == real_bid_no

    # ── Step 2: API 응답에서 verdict 간접 검증 ──
    # (DB 직접 조회가 없으면 분석 API로 확인)
    analysis_response = await staging_api_client.get(
        f"/api/bids/{real_bid_no}/analysis"
    )
    if analysis_response.status_code == 200:
        analysis_data = analysis_response.json().get("data") or {}
        # verdict가 "Go"로 설정되어 있거나 분석이 완료된 경우에만 검증
        if analysis_data.get("status") == "analyzed":
            assert analysis_data.get("verdict") == "Go", (
                f"verdict 불일치: {analysis_data.get('verdict')} (제안결정 후 Go 기대)"
            )

    # ── Step 3: 제안 프로젝트 생성 ──
    proposal_response = await staging_api_client.post(
        "/api/proposals/from-bid",
        json={"bid_no": real_bid_no},
    )

    assert proposal_response.status_code == 201, (
        f"제안 생성 실패: {proposal_response.status_code} — {proposal_response.text[:300]}"
    )

    proposal_data = proposal_response.json()
    proposal_id = proposal_data.get("proposal_id")
    assert proposal_id, "proposal_id 없음"

    # teardown 등록
    cleanup_test_proposals.append(proposal_id)

    # ── Step 4: 제안 프로젝트 검증 ──
    await asyncio.sleep(1.0)  # DB 반영 대기

    detail_response = await staging_api_client.get(
        f"/api/proposals/{proposal_id}"
    )
    assert detail_response.status_code == 200, (
        f"제안 상세 조회 실패: {detail_response.status_code}"
    )

    detail = detail_response.json()
    if isinstance(detail, dict) and "data" in detail:
        detail = detail["data"]

    assert detail.get("status") == "in_progress", (
        f"workflow 시작 후 status 불일치: {detail.get('status')} (in_progress 기대)"
    )
    assert detail.get("go_decision") is True, (
        f"go_decision 불일치: {detail.get('go_decision')}"
    )
    assert detail.get("source_bid_no") == real_bid_no, (
        f"source_bid_no 불일치: {detail.get('source_bid_no')}"
    )


@pytest.mark.live
async def test_go_decision_proposal_appears_in_list(
    staging_api_client,
    real_bid_no,
    cleanup_test_proposals,
):
    """
    제안 생성 후 GET /api/proposals 목록에서 확인.

    기대값:
    - 생성된 proposal_id가 목록에 포함됨
    - source_bid_no = real_bid_no
    """
    # 제안 생성
    proposal_response = await staging_api_client.post(
        "/api/proposals/from-bid",
        json={"bid_no": real_bid_no},
    )
    if proposal_response.status_code != 201:
        pytest.skip(f"제안 생성 실패: {proposal_response.status_code}")

    proposal_id = proposal_response.json().get("proposal_id")
    cleanup_test_proposals.append(proposal_id)

    await asyncio.sleep(1.0)

    # 목록 조회
    list_response = await staging_api_client.get("/api/proposals")
    assert list_response.status_code == 200

    list_data = list_response.json()
    proposals = list_data.get("data") or []

    # 생성된 제안 확인
    found = next(
        (p for p in proposals if p.get("id") == proposal_id),
        None,
    )
    assert found is not None, (
        f"제안 {proposal_id}가 목록에 없음 (총 {len(proposals)}개)"
    )
    assert found.get("source_bid_no") == real_bid_no


# ─────────────────────────────────────────────
# 시나리오 4: No-Go 결정 — Happy Path
# ─────────────────────────────────────────────

@pytest.mark.live
async def test_no_go_decision_abandon(staging_api_client, real_bid_no):
    """
    공고 상태를 "제안포기"로 변경 후 No-Go 의사결정 기록.

    기대값:
    - PUT /api/bids/{bid_no}/status → HTTP 200, status="제안포기"
    - POST /api/proposals/bids/decision → HTTP 200, decision_type_ko="제안포기"
    - 이후 모니터링 목록에서 해당 공고 제외 (show_all=False 기본)
    """
    # Step 1: 상태 변경
    status_response = await staging_api_client.put(
        f"/api/bids/{real_bid_no}/status",
        json={"status": "제안포기"},
    )

    assert status_response.status_code == 200
    inner = status_response.json().get("data") or status_response.json()
    assert inner.get("status") == "제안포기"

    # Step 2: No-Go 의사결정 기록
    # bid_announcements에 해당 공고가 있어야 하므로 실패 시 skip
    decision_response = await staging_api_client.post(
        "/api/proposals/bids/decision",
        json={
            "bid_no": real_bid_no,
            "decision_type": "abandon",
            "comment": "테스트: 예산 범위 밖",
        },
    )

    if decision_response.status_code == 404:
        pytest.skip(f"bid_announcements에 {real_bid_no} 없음 — 스킵")

    assert decision_response.status_code == 200, (
        f"No-Go 기록 실패: {decision_response.status_code} — {decision_response.text[:200]}"
    )

    decision_data = decision_response.json()
    assert decision_data.get("decision_type") == "abandon"
    assert decision_data.get("decision_type_ko") == "제안포기"

    # Step 3: 모니터링 목록에서 제외 확인 (기본 show_all=False)
    await asyncio.sleep(0.5)
    monitor_response = await staging_api_client.get(
        "/api/bids/monitor",
        params={"scope": "company", "page": 1, "per_page": 100},
    )
    if monitor_response.status_code == 200:
        items = monitor_response.json().get("data", [])
        # "제안포기" 공고는 기본 목록에서 보이지 않아야 함
        shown_bid_nos = {item["bid_no"] for item in items}
        assert real_bid_no not in shown_bid_nos, (
            f"제안포기 공고 {real_bid_no}가 모니터링 목록에 여전히 보임"
        )


@pytest.mark.live
async def test_no_go_decision_hold(staging_api_client, real_bid_no):
    """
    공고 상태를 "제안유보"로 변경.

    기대값:
    - HTTP 200
    - 유효한 BidProposalStatus 값 반환
    """
    response = await staging_api_client.put(
        f"/api/bids/{real_bid_no}/status",
        json={"status": "제안유보"},
    )

    assert response.status_code == 200
    inner = response.json().get("data") or response.json()
    assert inner.get("status") == "제안유보"


# ─────────────────────────────────────────────
# 시나리오 5: Edge Cases
# ─────────────────────────────────────────────

@pytest.mark.live
async def test_duplicate_proposal_from_same_bid(
    staging_api_client,
    real_bid_no,
    cleanup_test_proposals,
):
    """
    동일 공고에서 제안 프로젝트 중복 생성 시도.

    기대값 (현재 코드 동작 기준):
    - 첫 번째 생성: HTTP 201 (성공)
    - 두 번째 생성: HTTP 201 (또 다른 제안 생성) 또는 HTTP 409 (중복 방지)
    """
    # 첫 번째 제안 생성
    first_response = await staging_api_client.post(
        "/api/proposals/from-bid",
        json={"bid_no": real_bid_no},
    )
    assert first_response.status_code == 201
    first_id = first_response.json().get("proposal_id")
    cleanup_test_proposals.append(first_id)

    # 두 번째 제안 생성 (동일 bid_no)
    second_response = await staging_api_client.post(
        "/api/proposals/from-bid",
        json={"bid_no": real_bid_no},
    )

    if second_response.status_code == 409:
        # 중복 방지 구현된 경우 — 올바른 동작
        pass
    elif second_response.status_code == 201:
        # 현재 코드 동작: 중복 허용
        second_id = second_response.json().get("proposal_id")
        cleanup_test_proposals.append(second_id)
        # 두 제안 모두 다른 ID여야 함
        assert first_id != second_id, "동일한 ID로 생성됨"
    else:
        pytest.fail(
            f"예상치 못한 응답: {second_response.status_code} — {second_response.text[:200]}"
        )


@pytest.mark.skip(reason="Requires updated staging server with budget filtering")
@pytest.mark.live
async def test_bid_with_budget_below_threshold(staging_api_client):
    """
    예산 3,000만원 미만 공고 처리.

    기대값:
    - 모니터링 목록의 공고 중 budget_amount가 3천만원 미만인 것 없어야 함
    """
    response = await staging_api_client.get(
        "/api/bids/monitor",
        params={"scope": "company", "page": 1, "per_page": 50, "show_all": "true"},
    )

    if response.status_code != 200:
        pytest.skip(f"모니터링 목록 조회 실패: {response.status_code}")

    items = response.json().get("data", [])

    for item in items:
        budget = item.get("budget_amount", 0)
        if budget and budget > 0:
            assert budget >= 30_000_000, (
                f"저예산 공고 발견: {item['bid_no']}, budget={budget:,}원"
            )


@pytest.mark.live
async def test_bid_expired_not_shown(staging_api_client):
    """
    마감일 3일 이내 공고 처리.

    기대값:
    - show_all=False (기본) 시 days_remaining < 3 공고 제외
    """
    response = await staging_api_client.get(
        "/api/bids/monitor",
        params={"scope": "company", "page": 1, "per_page": 50},
    )

    if response.status_code != 200:
        pytest.skip(f"모니터링 목록 조회 실패: {response.status_code}")

    items = response.json().get("data", [])

    for item in items:
        days = item.get("days_remaining")
        if days is not None:
            try:
                days_int = int(days)
                assert days_int >= 3, (
                    f"마감 임박 공고 필터링 오류: {item['bid_no']}, days_remaining={days_int}"
                )
            except (ValueError, TypeError):
                pass  # days_remaining 파싱 불가 → 무시


# ─────────────────────────────────────────────
# 시나리오 8: 전체 E2E 흐름
# ─────────────────────────────────────────────

@pytest.mark.live
async def test_full_e2e_workflow(
    staging_api_client,
    test_team_id,
    real_bid_no,
    cleanup_test_proposals,
):
    """
    전체 워크플로우 E2E 테스트:
    수집 → 분석 → 추천 확인 → 제안결정 → 프로젝트 목록에서 확인

    타임아웃: AI 분석 포함 최대 120초
    """
    # ── Step 1: 모니터링 목록 조회 (공고 수집 전제) ──
    monitor_response = await staging_api_client.get(
        "/api/bids/monitor",
        params={"scope": "company", "page": 1, "per_page": 5},
    )
    assert monitor_response.status_code == 200
    items = monitor_response.json().get("data", [])
    assert len(items) > 0, "모니터링 목록 비어있음 — 수동 크롤링 필요"

    # ── Step 2: AI 분석 요청 및 완료 대기 ──
    start_time = time.time()
    analysis_done = False

    while time.time() - start_time < AI_ANALYSIS_TIMEOUT:
        analysis_response = await staging_api_client.get(
            f"/api/bids/{real_bid_no}/analysis"
        )
        assert analysis_response.status_code == 200

        inner = analysis_response.json().get("data") or analysis_response.json()
        if inner.get("status") == "analyzed":
            analysis_done = True
            break
        await asyncio.sleep(POLL_INTERVAL)

    # 분석 미완료 시에도 워크플로우 계속 진행 (분석은 비동기)

    # ── Step 3: 추천 목록 확인 ──
    rec_response = await staging_api_client.get(
        f"/api/teams/{test_team_id}/bids/recommendations"
    )
    assert rec_response.status_code == 200

    # ── Step 4: 제안결정 ──
    status_response = await staging_api_client.put(
        f"/api/bids/{real_bid_no}/status",
        json={"status": "제안결정"},
    )
    assert status_response.status_code == 200

    # ── Step 5: 제안 프로젝트 생성 ──
    proposal_response = await staging_api_client.post(
        "/api/proposals/from-bid",
        json={"bid_no": real_bid_no},
    )
    assert proposal_response.status_code == 201
    proposal_id = proposal_response.json().get("proposal_id")
    assert proposal_id
    cleanup_test_proposals.append(proposal_id)

    # ── Step 6: 제안 목록 확인 ──
    await asyncio.sleep(1.0)
    list_response = await staging_api_client.get("/api/proposals")
    assert list_response.status_code == 200

    proposals = list_response.json().get("data", [])
    found = next(
        (p for p in proposals if p.get("id") == proposal_id),
        None,
    )
    assert found is not None, f"전체 E2E: 제안 {proposal_id}가 목록에 없음"
    assert found.get("go_decision") is True
    assert found.get("source_bid_no") == real_bid_no

    # ── 결과 요약 ──
    print(
        f"\n[E2E 완료] bid_no={real_bid_no}, proposal_id={proposal_id}, "
        f"analysis_done={analysis_done}"
    )


# ─────────────────────────────────────────────
# 시나리오 6 (Error): 상태 값 유효성
# ─────────────────────────────────────────────

@pytest.mark.live
async def test_invalid_bid_no_status_update(staging_api_client):
    """
    유효하지 않은 공고번호 형식으로 상태 변경 시도.

    기대값:
    - HTTP 400 또는 422 (BidValidationError)
    """
    response = await staging_api_client.put(
        "/api/bids/INVALID!!NO/status",
        json={"status": "제안결정"},
    )
    assert response.status_code in (400, 422), (
        f"유효하지 않은 bid_no에 예상치 못한 응답: {response.status_code}"
    )


@pytest.mark.live
async def test_invalid_proposal_status_value(staging_api_client, real_bid_no):
    """
    유효하지 않은 proposal_status 값 전송.

    기대값:
    - HTTP 422 (Pydantic 유효성 검사 오류)
    """
    response = await staging_api_client.put(
        f"/api/bids/{real_bid_no}/status",
        json={"status": "잘못된상태값"},
    )
    assert response.status_code == 422, (
        f"유효하지 않은 status에 예상치 못한 응답: {response.status_code}"
    )
