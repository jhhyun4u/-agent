"""Live MCP 도구 호출 테스트 — MCP-06~07.

실제 외부 API 연결 필요.
pytest -m live 로 실행.
"""

import pytest


pytestmark = pytest.mark.live


# ── MCP-06: SearXNG 실제 호출 ──

@pytest.mark.asyncio
async def test_searxng_live_search(require_searxng):
    """SearXNG Docker 인스턴스에 실제 검색 요청."""
    import aiohttp

    url = require_searxng
    params = {"q": "클라우드 ERP 구축", "format": "json", "categories": "general"}

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{url}/search", params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            assert resp.status == 200, f"SearXNG 응답 실패: {resp.status}"
            data = await resp.json()

    results = data.get("results", [])
    assert len(results) >= 1, "SearXNG 검색 결과 없음"
    assert "title" in results[0], "결과에 title 필드 없음"
    assert "url" in results[0], "결과에 url 필드 없음"


# ── MCP-07: G2B API 실제 호출 ──

@pytest.mark.asyncio
async def test_g2b_api_live_search(require_g2b_key):
    """나라장터 API 실제 호출 — 입찰공고 검색."""
    from app.services.g2b_service import G2BService

    async with G2BService() as g2b:
        results = await g2b.search_bid_announcements(
            keyword="시스템 구축",
            num_of_rows=5,
        )

    assert isinstance(results, list), f"결과가 list가 아님: {type(results)}"
    # 결과가 없을 수도 있으므로 (시기에 따라) 타입만 확인
    if results:
        first = results[0]
        # G2B 응답 필드 존재 확인
        assert any(k in first for k in ("bidNtceNm", "bidNtceNo", "ntceInsttNm")), \
            f"G2B 응답 구조 불일치: {list(first.keys())[:5]}"
