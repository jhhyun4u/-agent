"""
STEP 0: RFP 공고 검색 노드 (§6)

G2B 공고 검색 + AI 적합도 평가 + 추천 리스트 생성 (최대 5건).
"""

import logging

from app.graph.state import ProposalState, RfpRecommendation
from app.services.claude_client import claude_generate

logger = logging.getLogger(__name__)

MAX_RECOMMENDATIONS = 5


async def rfp_search(state: ProposalState) -> dict:
    """STEP 0: G2B 공고 검색 + AI 적합도 평가."""

    # 검색 조건 결정 (초기 query > 재검색 피드백 > project_name)
    query_params = state.get("search_query", {})

    feedback_history = state.get("feedback_history", [])
    if feedback_history:
        last = feedback_history[-1]
        if last.get("step") == "search":
            raw_query = last.get("search_query", {})
            if isinstance(raw_query, dict):
                query_params = {**query_params, **raw_query}
            else:
                query_params["keywords"] = str(raw_query)

    search_keywords = query_params.get("keywords", "") or state.get("project_name", "")
    mode = state.get("mode", "full")

    # G2B 공고 검색
    from app.services.g2b_service import search_bids
    raw_results = await search_bids(
        keywords=search_keywords,
        budget_min=query_params.get("budget_min"),
        region=query_params.get("region"),
    )

    if not raw_results:
        return {
            "search_results": [],
            "current_step": "search_complete",
        }

    # AI 적합도 평가
    capabilities_text = ""
    if mode == "full":
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        org_id = state.get("org_id", "")
        if org_id:
            caps = await client.table("capabilities").select("type, title, detail, keywords").eq("org_id", org_id).execute()
            capabilities_text = "\n".join(
                f"- [{c['type']}] {c['title']}: {c['detail']}" for c in (caps.data or [])
            )

    prompt = f"""다음 G2B 공고 목록에서 최대 {MAX_RECOMMENDATIONS}건을 적합도 순으로 추천하세요.

## 검색 결과
{_format_bids(raw_results)}

## 자사 역량
{capabilities_text or "역량 DB 없음 (Lite 모드)"}

## 출력 형식 (JSON 배열)
[
  {{
    "bid_no": "공고번호",
    "project_name": "사업명",
    "client": "발주기관",
    "budget": "예산",
    "deadline": "마감일",
    "project_summary": "사업 개요 요약 (2~3문장)",
    "key_requirements": ["주요 요구사항 3~5개"],
    "eval_method": "평가 방식 요약",
    "competition_level": "경쟁 강도 예측 (높음/보통/낮음 + 근거)",
    "fit_score": 85,
    "fit_rationale": "적합도 판단 근거",
    "expected_positioning": "defensive|offensive|adjacent",
    "brief_analysis": "종합 한줄 분석"
  }}
]
"""

    result = await claude_generate(prompt)
    recommendations = result if isinstance(result, list) else result.get("recommendations", [result])

    sorted_recs = sorted(recommendations, key=lambda r: r.get("fit_score", 0), reverse=True)

    return {
        "search_results": [
            RfpRecommendation(**r) for r in sorted_recs[:MAX_RECOMMENDATIONS]
            if "bid_no" in r
        ],
        "current_step": "search_complete",
    }


def _format_bids(bids: list[dict]) -> str:
    lines = []
    for i, b in enumerate(bids[:20], 1):
        lines.append(
            f"{i}. [{b.get('bid_no', '')}] {b.get('project_name', '')} | "
            f"{b.get('client', '')} | {b.get('budget', '')} | {b.get('deadline', '')}"
        )
    return "\n".join(lines)
