"""E2E 워크플로 단계별 테스트 스크립트"""
import asyncio, time
from httpx import AsyncClient, ASGITransport
from app.main import app


async def _get_token():
    """Supabase 로그인으로 새 토큰 발급."""
    from supabase._async.client import create_client
    url = 'https://inuuyaxddgbxexljfykg.supabase.co'
    key = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImludXV5YXhkZGdieGV4bGpmeWtnIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzI5MDU3MjUsImV4cCI6MjA4ODQ4MTcyNX0.5GSwbVcpVQE8OVjuSS82MsI9bZNUjXCLuW-De_indOo'
    client = await create_client(url, key)
    res = await client.auth.sign_in_with_password({'email': 'admin@tenopa.co.kr', 'password': 'test1234'})
    return res.session.access_token

RFP = """사업명: 2026년 공공데이터 품질관리 플랫폼 구축
발주기관: NIA  사업기간: 8개월  사업예산: 15억원
요구사항: 데이터 품질 자동 진단, AI 오류 보정, 실시간 모니터링
평가방법: 기술90+가격10  참가자격: SW사업자, 유사실적 3건"""

import logging
logging.basicConfig(level=logging.WARNING)


async def main():
    TOKEN = await _get_token()
    HEADERS = {'Authorization': f'Bearer {TOKEN}', 'Content-Type': 'application/json'}
    print(f'Token acquired: ...{TOKEN[-20:]}')

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url='http://test') as c:
        t0 = time.time()
        step_num = 0

        def log(msg):
            nonlocal step_num
            step_num += 1
            elapsed = time.time() - t0
            print(f'[{step_num:2d}] ({elapsed:5.1f}s) {msg}', flush=True)

        # 1. 생성
        r = await c.post('/api/proposals', json={'name': 'Full E2E'}, headers=HEADERS)
        pid = r.json()['id']
        log(f'프로젝트 생성 -> {pid[:12]}...')

        # 2. 시작
        r = await c.post(
            f'/api/proposals/{pid}/start',
            json={'initial_state': {'rfp_raw': RFP, 'project_name': 'Full E2E'}},
            headers=HEADERS, timeout=120,
        )
        d = r.json()
        log(f'워크플로 시작 -> {d["current_step"]}')

        # 3~N. 순차 resume
        for i in range(25):
            r = await c.post(
                f'/api/proposals/{pid}/resume',
                json={'quick_approve': True, 'approved_by': 'admin', 'decision': 'go'},
                headers=HEADERS, timeout=180,
            )
            if r.status_code != 200:
                log(f'ERROR {r.status_code}: {r.text[:200]}')
                break

            d = r.json()
            step = d.get('current_step', '?')
            interrupted = d.get('interrupted', False)
            log(f'resume -> {step} (interrupted={interrupted})')

            if not interrupted:
                log('워크플로 완료!')
                break

        print(f'\n{"=" * 50}')
        print(f'전체 {step_num} steps, 소요시간 {time.time()-t0:.1f}s')


asyncio.run(main())
