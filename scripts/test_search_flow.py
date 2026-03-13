"""공고 검색 → AI 적합도 평가 흐름 테스트.

G2B API 장애/키 미설정 시 mock 데이터로 자동 대체.

사용법:
    uv run python scripts/test_search_flow.py
    uv run python scripts/test_search_flow.py --live    # G2B 실제 호출 시도
"""
import asyncio
import sys
import json

sys.path.insert(0, ".")

from app.services.claude_client import claude_generate
from app.config import settings


# ── Mock 공고 데이터 (G2B API 대체용) ──

MOCK_BIDS = [
    {
        "bid_no": "20260312-001",
        "project_name": "2026년 공공기관 AI 기반 행정업무 자동화 시스템 구축",
        "client": "행정안전부",
        "budget": "2,500,000,000",
        "deadline": "2026-04-15 18:00",
    },
    {
        "bid_no": "20260310-042",
        "project_name": "클라우드 기반 통합 데이터 분석 플랫폼 구축 용역",
        "client": "한국지능정보사회진흥원(NIA)",
        "budget": "1,800,000,000",
        "deadline": "2026-04-10 18:00",
    },
    {
        "bid_no": "20260308-015",
        "project_name": "지능형 민원응대 챗봇 고도화 사업",
        "client": "서울특별시",
        "budget": "950,000,000",
        "deadline": "2026-04-05 18:00",
    },
    {
        "bid_no": "20260307-088",
        "project_name": "2026년 정보시스템 운영 및 유지보수",
        "client": "국토교통부",
        "budget": "3,200,000,000",
        "deadline": "2026-03-28 18:00",
    },
    {
        "bid_no": "20260305-023",
        "project_name": "빅데이터 기반 교통정보 분석체계 구축",
        "client": "한국교통안전공단",
        "budget": "1,200,000,000",
        "deadline": "2026-04-20 18:00",
    },
    {
        "bid_no": "20260304-077",
        "project_name": "차세대 전자조달시스템 ISP 수립",
        "client": "조달청",
        "budget": "800,000,000",
        "deadline": "2026-04-08 18:00",
    },
    {
        "bid_no": "20260303-019",
        "project_name": "AI 활용 보안관제 지능화 시스템 구축",
        "client": "한국인터넷진흥원(KISA)",
        "budget": "2,100,000,000",
        "deadline": "2026-04-12 18:00",
    },
]


# ── 자사 역량 (mock) ──

MOCK_CAPABILITIES = """- [track_record] 클라우드 ERP 시스템 구축: A공공기관 ERP 클라우드 전환 (2024, 10억원, 6개월)
- [track_record] AI 민원분석 시스템: B지자체 민원 자동분류 시스템 구축 (2025, 8억원)
- [tech] AI/ML 파이프라인: LangGraph 멀티에이전트, RAG, Python/FastAPI
- [tech] 클라우드 아키텍처: AWS/Azure 기반 MSA 설계 및 구축
- [personnel] PMP 보유 PM 5명: 공공SI 평균 경력 10년
- [personnel] AI 전문인력 8명: 석사 이상 4명, 관련 자격증 보유"""


def _format_bids(bids: list[dict]) -> str:
    lines = []
    for i, b in enumerate(bids, 1):
        lines.append(
            f"{i}. [{b['bid_no']}] {b['project_name']} | "
            f"{b['client']} | {b['budget']} | {b['deadline']}"
        )
    return "\n".join(lines)


async def test_with_live_g2b(keyword: str):
    """G2B 실제 API 호출 시도."""
    from app.services.g2b_service import search_bids
    print(f"\n[G2B Live] '{keyword}' 검색 중...")
    results = await search_bids(keywords=keyword)
    if results:
        print(f"  {len(results)}건 조회됨")
        return results
    else:
        print("  결과 없음 (API 장애 또는 키 오류)")
        return None


async def test_ai_recommendation(bids: list[dict], capabilities: str):
    """AI 적합도 평가 (실제 Claude API 호출)."""
    prompt = f"""다음 G2B 공고 목록에서 최대 3건을 적합도 순으로 추천하세요.

## 검색 결과
{_format_bids(bids)}

## 자사 역량
{capabilities}

## 출력 형식 (JSON 배열)
[
  {{
    "bid_no": "공고번호",
    "project_name": "사업명",
    "client": "발주기관",
    "budget": "예산",
    "deadline": "마감일",
    "fit_score": 85,
    "fit_rationale": "적합도 판단 근거 (2~3문장)",
    "expected_positioning": "defensive|offensive|adjacent",
    "brief_analysis": "종합 한줄 분석"
  }}
]

반드시 JSON 배열만 출력하세요.
"""

    print("\n[AI] Claude 적합도 평가 중...")
    result = await claude_generate(prompt)

    if isinstance(result, list):
        recommendations = result
    elif isinstance(result, dict):
        recommendations = result.get("recommendations", [result])
    else:
        print(f"  예상치 못한 응답 형식: {type(result)}")
        return

    # 결과 출력
    sorted_recs = sorted(recommendations, key=lambda r: r.get("fit_score", 0), reverse=True)

    print(f"\n{'='*60}")
    print(f"  AI 추천 결과 ({len(sorted_recs)}건)")
    print(f"{'='*60}")

    for i, rec in enumerate(sorted_recs, 1):
        score = rec.get("fit_score", 0)
        grade = "S" if score >= 90 else "A" if score >= 80 else "B" if score >= 70 else "C"
        pos = rec.get("expected_positioning", "?")
        pos_label = {"defensive": "수성", "offensive": "공격", "adjacent": "인접"}.get(pos, pos)

        print(f"\n  #{i} [{grade}등급] 적합도 {score}점 - {pos_label} 포지셔닝")
        print(f"  사업명:   {rec.get('project_name', '')}")
        print(f"  발주기관: {rec.get('client', '')}")
        print(f"  예산:     {rec.get('budget', '')}")
        print(f"  마감:     {rec.get('deadline', '')}")
        print(f"  판단근거: {rec.get('fit_rationale', '')}")
        print(f"  종합분석: {rec.get('brief_analysis', '')}")

    print(f"\n{'='*60}")


async def main():
    use_live = "--live" in sys.argv

    print("=" * 60)
    print("  공고 검색 + AI 적합도 평가 테스트")
    print("=" * 60)

    bids = None

    if use_live:
        bids = await test_with_live_g2b("인공지능")

    if not bids:
        print("\n[Mock] G2B mock 공고 7건 사용")
        bids = MOCK_BIDS

    # 공고 목록 출력
    print(f"\n--- 공고 목록 ({len(bids)}건) ---")
    for i, b in enumerate(bids, 1):
        print(f"  {i}. {b['project_name'][:45]}  |  {b['client']}  |  {b['budget']}")

    # Claude API 키 확인
    if not settings.anthropic_api_key:
        print("\n[SKIP] ANTHROPIC_API_KEY 미설정 — AI 평가 건너뜀")
        return

    await test_ai_recommendation(bids, MOCK_CAPABILITIES)


if __name__ == "__main__":
    asyncio.run(main())
