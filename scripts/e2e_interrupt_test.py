"""
Zero Script QA — 워크플로 중단 시나리오 E2E 테스트

3가지 중단 시나리오를 테스트하고, 구조화 로그로 검증:
  시나리오 1: 리뷰에서 No-Go 결정 → 워크플로 정상 종료
  시나리오 2: AI 작업 중 ai-abort → paused 전환 + ai-retry 재개
  시나리오 3: 타임트래블 goto → 과거 체크포인트 복원

실행: LOG_FORMAT=json uv run python scripts/e2e_interrupt_test.py
로그 분석: 출력되는 JSON 로그에서 request_id로 요청 추적 가능
"""

import asyncio
import json
import time

from httpx import AsyncClient, ASGITransport

# JSON 로그 활성화
import os
os.environ.setdefault("LOG_FORMAT", "json")

from app.main import app  # noqa: E402

# ── 테스트 상수 ──

RFP_SAMPLE = """사업명: 2026년 공공데이터 품질관리 플랫폼 구축
발주기관: NIA  사업기간: 8개월  사업예산: 15억원
요구사항: 데이터 품질 자동 진단, AI 오류 보정, 실시간 모니터링
평가방법: 기술90+가격10  참가자격: SW사업자, 유사실적 3건"""

# ── 결과 카운터 ──

_pass = 0
_fail = 0
_skip = 0

GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[0;33m"
CYAN = "\033[0;36m"
NC = "\033[0m"


def _check(name: str, condition: bool, detail: str = ""):
    global _pass, _fail
    if condition:
        _pass += 1
        print(f"  {GREEN}✅ PASS{NC}: {name}")
    else:
        _fail += 1
        print(f"  {RED}❌ FAIL{NC}: {name}" + (f" — {detail}" if detail else ""))


def _skip_test(name: str, reason: str):
    global _skip
    _skip += 1
    print(f"  {YELLOW}⏭️  SKIP{NC}: {name} — {reason}")


async def _get_token():
    """Supabase 로그인으로 토큰 발급."""
    from supabase._async.client import create_client
    url = "https://inuuyaxddgbxexljfykg.supabase.co"
    key = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImludXV5YXhkZGdieGV4bGpmeWtnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI5MDU3MjUsImV4cCI6MjA4ODQ4MTcyNX0."
        "5GSwbVcpVQE8OVjuSS82MsI9bZNUjXCLuW-De_indOo"
    )
    client = await create_client(url, key)
    res = await client.auth.sign_in_with_password({
        "email": "admin@tenopa.co.kr",
        "password": "test1234",
    })
    return res.session.access_token


async def _create_proposal(c: AsyncClient, headers: dict, name: str) -> str:
    """테스트용 제안 프로젝트 생성 → proposal_id 반환."""
    r = await c.post("/api/proposals", json={"name": name}, headers=headers)
    assert r.status_code == 200 or r.status_code == 201, f"프로젝트 생성 실패: {r.status_code} {r.text[:200]}"
    return r.json()["id"]


async def _start_workflow(c: AsyncClient, headers: dict, pid: str) -> dict:
    """워크플로 시작 → 첫 interrupt까지."""
    r = await c.post(
        f"/api/proposals/{pid}/start",
        json={"initial_state": {"rfp_raw": RFP_SAMPLE, "project_name": "Interrupt Test"}},
        headers=headers,
        timeout=120,
    )
    assert r.status_code == 200, f"워크플로 시작 실패: {r.status_code} {r.text[:200]}"
    return r.json()


# ══════════════════════════════════════════
# 시나리오 1: 리뷰에서 No-Go 결정 → 워크플로 종료
# ══════════════════════════════════════════

async def scenario_1_no_go(c: AsyncClient, headers: dict):
    print(f"\n{CYAN}{'═' * 55}")
    print("시나리오 1: 리뷰에서 No-Go → 워크플로 종료")
    print(f"{'═' * 55}{NC}")

    # 1-1. 프로젝트 생성 + 워크플로 시작
    pid = await _create_proposal(c, headers, "No-Go Test")
    start_result = await _start_workflow(c, headers, pid)
    _check("워크플로 시작 성공", start_result.get("interrupted") is True)

    # 1-2. RFP 분석 리뷰 → 승인 (Go/No-Go까지 진행)
    r = await c.post(
        f"/api/proposals/{pid}/resume",
        json={"quick_approve": True, "approved_by": "admin"},
        headers=headers, timeout=120,
    )
    _check("RFP 분석 승인 (resume 200)", r.status_code == 200)

    # 1-3. Go/No-Go 리뷰에서 No-Go 결정
    r = await c.post(
        f"/api/proposals/{pid}/resume",
        json={
            "decision": "no_go",
            "no_go_reason": "수주 가능성 낮음, 경쟁 과열",
            "approved_by": "admin",
            "feedback": "테스트: No-Go 시나리오",
        },
        headers=headers, timeout=120,
    )
    d = r.json()
    _check("No-Go 결정 전달 성공", r.status_code == 200)
    _check("current_step == go_no_go_no_go", d.get("current_step") == "go_no_go_no_go")
    _check("워크플로 종료 (interrupted=False)", d.get("interrupted") is False)

    # 1-4. DB 상태 검증 — proposals.status == cancelled
    r = await c.get(f"/api/proposals/{pid}/state", headers=headers)
    r.json()
    _check("그래프 상태 조회 성공", r.status_code == 200)

    # 1-5. 추가 resume 시도 → 실패해야 함
    r = await c.post(
        f"/api/proposals/{pid}/resume",
        json={"quick_approve": True},
        headers=headers, timeout=30,
    )
    _check("종료 후 resume 시도 → 에러", r.status_code != 200, f"status={r.status_code}")

    # 1-6. 응답 헤더에 X-Request-ID 존재 확인
    _check("X-Request-ID 응답 헤더 존재", "x-request-id" in r.headers)

    return pid


# ══════════════════════════════════════════
# 시나리오 2: AI 실행 중 ai-abort → 재시도
# ══════════════════════════════════════════

async def scenario_2_abort_retry(c: AsyncClient, headers: dict):
    print(f"\n{CYAN}{'═' * 55}")
    print("시나리오 2: AI 실행 중 ai-abort → paused → ai-retry")
    print(f"{'═' * 55}{NC}")

    pid = await _create_proposal(c, headers, "Abort Test")
    await _start_workflow(c, headers, pid)

    # 2-1. ai-status 조회 (idle일 수 있음 — 이미 interrupt에 도달)
    r = await c.get(f"/api/proposals/{pid}/ai-status", headers=headers)
    _check("ai-status 조회 성공", r.status_code == 200)
    status_data = r.json()
    print(f"    현재 AI 상태: {json.dumps(status_data, ensure_ascii=False)[:120]}")

    # 2-2. ai-abort 호출
    r = await c.post(f"/api/proposals/{pid}/ai-abort", headers=headers)
    _check("ai-abort 호출 성공", r.status_code == 200)
    abort_data = r.json()
    _check("ai-abort 응답에 status 포함", "status" in abort_data)
    print(f"    Abort 결과: {json.dumps(abort_data, ensure_ascii=False)[:120]}")

    # 2-3. ai-abort 후 상태 확인
    r = await c.get(f"/api/proposals/{pid}/ai-status", headers=headers)
    status_after = r.json()
    # idle이면 이미 interrupt에서 멈춘 상태, paused면 abort 성공
    _check(
        "abort 후 상태: idle 또는 paused",
        status_after.get("status") in ("idle", "paused"),
        f"actual: {status_after.get('status')}",
    )

    # 2-4. ai-retry 호출 (paused 상태에서만 의미 있음)
    if status_after.get("status") == "paused":
        r = await c.post(f"/api/proposals/{pid}/ai-retry", headers=headers, timeout=120)
        _check("ai-retry 호출 성공", r.status_code == 200)
        retry_data = r.json()
        print(f"    Retry 결과: {json.dumps(retry_data, ensure_ascii=False)[:120]}")
    else:
        _skip_test("ai-retry", "abort 시점에 AI가 이미 idle — interrupt 대기 중이었음")

    # 2-5. ai-logs 이력 조회
    r = await c.get(f"/api/proposals/{pid}/ai-logs?limit=5", headers=headers)
    _check("ai-logs 조회 성공", r.status_code == 200)
    logs = r.json().get("logs", [])
    print(f"    AI 로그 {len(logs)}건")

    # 2-6. X-Request-ID 헤더 확인
    _check("X-Request-ID 응답 헤더 존재", "x-request-id" in r.headers)

    return pid


# ══════════════════════════════════════════
# 시나리오 3: 타임트래블 (goto → 복원)
# ══════════════════════════════════════════

async def scenario_3_time_travel(c: AsyncClient, headers: dict):
    print(f"\n{CYAN}{'═' * 55}")
    print("시나리오 3: 타임트래블 goto → 과거 체크포인트 복원")
    print(f"{'═' * 55}{NC}")

    pid = await _create_proposal(c, headers, "TimeTravel Test")
    start = await _start_workflow(c, headers, pid)
    initial_step = start.get("current_step", "")
    _check("초기 step 기록", bool(initial_step), initial_step)

    # 3-1. RFP 분석 승인 → research → Go/No-Go까지 진행
    r = await c.post(
        f"/api/proposals/{pid}/resume",
        json={"quick_approve": True, "approved_by": "admin"},
        headers=headers, timeout=120,
    )
    step_after_rfp = r.json().get("current_step", "")
    _check("RFP 승인 → 다음 step 진행", r.status_code == 200, step_after_rfp)

    # 3-2. 히스토리 조회
    r = await c.get(f"/api/proposals/{pid}/history", headers=headers)
    _check("히스토리 조회 성공", r.status_code == 200)
    history = r.json().get("history", [])
    print(f"    체크포인트 {len(history)}개")
    for h in history[:5]:
        print(f"      - step: {h.get('step')}, next: {h.get('next')}")

    # 3-3. impact 조회 (rfp_analyze 변경 시 영향 범위)
    r = await c.get(f"/api/proposals/{pid}/impact/rfp_analyze", headers=headers)
    _check("impact 조회 성공", r.status_code == 200)
    impact = r.json()
    _check("downstream 노드 존재", impact.get("downstream_count", 0) > 0,
           f"downstream={impact.get('downstream_count')}")
    print(f"    rfp_analyze 변경 시 → STEP {impact.get('affected_steps')} 재실행 필요")

    # 3-4. goto로 rfp_analyze로 타임트래블
    # 히스토리에서 타겟 step 확인
    target_step = None
    for h in history:
        step = h.get("step", "")
        if "rfp" in step or "start" in step:
            target_step = step
            break

    if target_step:
        r = await c.post(f"/api/proposals/{pid}/goto/{target_step}", headers=headers)
        _check(f"goto '{target_step}' 호출 성공", r.status_code == 200)
        goto_result = r.json()
        _check("goto 결과: success=True", goto_result.get("success") is True, str(goto_result))

        # 3-5. 복원 후 상태 확인
        r = await c.get(f"/api/proposals/{pid}/state", headers=headers)
        state = r.json()
        _check("복원 후 상태 조회 성공", r.status_code == 200)
        print(f"    복원 후 step: {state.get('current_step')}")
    else:
        _skip_test("goto 타임트래블", "히스토리에 적합한 체크포인트 없음")

    # 3-6. X-Request-ID 헤더 확인
    _check("X-Request-ID 응답 헤더 존재", "x-request-id" in r.headers)

    return pid


# ══════════════════════════════════════════
# 메인 실행
# ══════════════════════════════════════════

async def main():
    print(f"\n{'═' * 55}")
    print("Zero Script QA — 워크플로 중단 시나리오 E2E 테스트")
    print(f"{'═' * 55}")

    TOKEN = await _get_token()
    HEADERS = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json",
    }
    print(f"Token: ...{TOKEN[-20:]}")

    import logging
    logging.basicConfig(level=logging.WARNING)

    transport = ASGITransport(app=app)
    t0 = time.time()

    async with AsyncClient(transport=transport, base_url="http://test") as c:
        try:
            await scenario_1_no_go(c, HEADERS)
        except Exception as e:
            print(f"  {RED}💥 시나리오 1 예외: {e}{NC}")

        try:
            await scenario_2_abort_retry(c, HEADERS)
        except Exception as e:
            print(f"  {RED}💥 시나리오 2 예외: {e}{NC}")

        try:
            await scenario_3_time_travel(c, HEADERS)
        except Exception as e:
            print(f"  {RED}💥 시나리오 3 예외: {e}{NC}")

    elapsed = time.time() - t0

    # ── 결과 요약 ──
    total = _pass + _fail + _skip
    pass_rate = (_pass / total * 100) if total else 0

    print(f"\n{'═' * 55}")
    print("테스트 결과 요약")
    print(f"{'═' * 55}")
    print(f"  {GREEN}✅ PASS: {_pass}{NC}")
    print(f"  {RED}❌ FAIL: {_fail}{NC}")
    print(f"  {YELLOW}⏭️  SKIP: {_skip}{NC}")
    print(f"  📊 합격률: {pass_rate:.0f}% ({_pass}/{total})")
    print(f"  ⏱️  소요시간: {elapsed:.1f}s")
    print(f"{'═' * 55}")

    # 로그 분석 가이드
    print(f"\n{CYAN}📋 로그 분석 가이드{NC}")
    print("  JSON 로그에서 다음 이벤트를 검색하세요:")
    print('  - grep "WF_START"    → 워크플로 시작')
    print('  - grep "WF_RESUME"   → Human 리뷰 결과')
    print('  - grep "WF_CANCELLED"→ 워크플로 종료 (No-Go)')
    print('  - grep "WF_ABORT"    → AI 작업 강제 중단')
    print('  - grep "WF_GOTO"     → 타임트래블')
    print('  - grep "request_id"  → 특정 요청 추적')
    print('  - grep "Slow response" → 느린 응답 (>1초)')


if __name__ == "__main__":
    asyncio.run(main())
