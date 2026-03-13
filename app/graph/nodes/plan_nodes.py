"""
STEP 3: 실행 계획 5개 병렬 노드 (§4, §29-6)

plan_team, plan_assign, plan_schedule, plan_story, plan_price.
v3.3: plan_price에서 labor_rates, market_price_data DB 조회.
"""

import logging
from datetime import datetime

from app.graph.state import ProposalState
from app.prompts.plan import (
    BUDGET_DETAIL_FRAMEWORK,
    PLAN_ASSIGN_PROMPT,
    PLAN_PRICE_PROMPT,
    PLAN_SCHEDULE_PROMPT,
    PLAN_STORY_PROMPT,
    PLAN_TEAM_PROMPT,
)
from app.services.claude_client import claude_generate

logger = logging.getLogger(__name__)


def _get_rfp_summary(state: ProposalState) -> str:
    """RFP 분석 결과를 텍스트 요약."""
    rfp = state.get("rfp_analysis")
    if not rfp:
        return "(RFP 분석 없음)"
    d = rfp.model_dump() if hasattr(rfp, "model_dump") else (rfp if isinstance(rfp, dict) else {})
    return f"""사업명: {d.get('project_name', '')}
발주기관: {d.get('client', '')}
핫버튼: {d.get('hot_buttons', [])}
평가항목: {d.get('eval_items', [])}
필수요건: {d.get('mandatory_reqs', [])}"""


def _get_strategy_fields(state: ProposalState) -> dict:
    """전략 주요 필드 추출."""
    s = state.get("strategy")
    if not s:
        return {"win_theme": "", "ghost_theme": "", "key_messages": [], "action_forcing_event": "", "price_strategy": {}}
    if hasattr(s, "model_dump"):
        d = s.model_dump()
    elif isinstance(s, dict):
        d = s
    else:
        d = {}
    return {
        "win_theme": d.get("win_theme", ""),
        "ghost_theme": d.get("ghost_theme", ""),
        "key_messages": d.get("key_messages", []),
        "action_forcing_event": d.get("action_forcing_event", ""),
        "price_strategy": d.get("price_strategy", {}),
    }


async def plan_team(state: ProposalState) -> dict:
    """STEP 3: 팀 구성 계획."""
    rfp_summary = _get_rfp_summary(state)
    sf = _get_strategy_fields(state)

    # 역량 DB 조회
    capabilities_text = ""
    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        org_id = state.get("org_id", "")
        if org_id:
            caps = await client.table("capabilities").select("type, title, detail").eq("org_id", org_id).execute()
            capabilities_text = "\n".join(f"- [{c['type']}] {c['title']}: {c['detail']}" for c in (caps.data or []))
    except Exception:
        pass

    prompt = PLAN_TEAM_PROMPT.format(
        rfp_summary=rfp_summary,
        positioning=state.get("positioning", "defensive"),
        win_theme=sf["win_theme"],
        key_messages=sf["key_messages"],
        capabilities_text=capabilities_text or "(역량 DB 없음)",
    )

    result = await claude_generate(prompt)
    return {"parallel_results": {"team": result.get("team", [])}}


async def plan_assign(state: ProposalState) -> dict:
    """STEP 3: 산출물 + 역할 배분."""
    rfp_summary = _get_rfp_summary(state)
    team = state.get("parallel_results", {}).get("team", [])
    team_summary = "\n".join(f"- {t.get('role', '')}: {t.get('grade', '')}, {t.get('mm', 0)} M/M" for t in team) if team else "(팀 구성 미정)"

    prompt = PLAN_ASSIGN_PROMPT.format(
        rfp_summary=rfp_summary,
        team_summary=team_summary,
    )

    result = await claude_generate(prompt)
    return {"parallel_results": {"deliverables": result.get("deliverables", [])}}


async def plan_schedule(state: ProposalState) -> dict:
    """STEP 3: 추진 일정."""
    rfp_summary = _get_rfp_summary(state)
    rfp = state.get("rfp_analysis")
    deadline = ""
    if rfp:
        deadline = rfp.deadline if hasattr(rfp, "deadline") else (rfp.get("deadline", "") if isinstance(rfp, dict) else "")

    deliverables = state.get("parallel_results", {}).get("deliverables", [])
    deliverables_summary = "\n".join(f"- {d.get('name', '')}" for d in deliverables) if deliverables else "(산출물 미정)"

    prompt = PLAN_SCHEDULE_PROMPT.format(
        rfp_summary=rfp_summary,
        deadline=deadline,
        deliverables_summary=deliverables_summary,
    )

    result = await claude_generate(prompt)
    return {"parallel_results": {"schedule": result.get("schedule", {})}}


async def plan_story(state: ProposalState) -> dict:
    """STEP 3: 목차 확정 + 섹션별 스토리라인 설계."""
    rfp_summary = _get_rfp_summary(state)
    sf = _get_strategy_fields(state)
    rfp = state.get("rfp_analysis")
    eval_items = []
    if rfp:
        eval_items = rfp.eval_items if hasattr(rfp, "eval_items") else (rfp.get("eval_items", []) if isinstance(rfp, dict) else [])

    # 현재 목차 (RFP 분석 기반 초안)
    current_sections = state.get("dynamic_sections", [])
    current_sections_text = "\n".join(f"  {i+1}. {s}" for i, s in enumerate(current_sections)) if current_sections else "(목차 미생성)"

    prompt = PLAN_STORY_PROMPT.format(
        rfp_summary=rfp_summary,
        current_sections=current_sections_text,
        positioning=state.get("positioning", "defensive"),
        win_theme=sf["win_theme"],
        ghost_theme=sf["ghost_theme"],
        key_messages=sf["key_messages"],
        action_forcing_event=sf["action_forcing_event"],
        eval_items=eval_items,
    )

    result = await claude_generate(prompt)
    return {"parallel_results": {"storylines": result.get("storylines", {})}}


async def plan_price(state: ProposalState) -> dict:
    """STEP 3: 예산산정 (v3.3: labor_rates + market_price_data DB 조회)."""
    rfp_summary = _get_rfp_summary(state)
    sf = _get_strategy_fields(state)
    rfp = state.get("rfp_analysis")
    budget = ""
    if rfp:
        budget = rfp.budget if hasattr(rfp, "budget") else (rfp.get("budget", "") if isinstance(rfp, dict) else "")

    team = state.get("parallel_results", {}).get("team", [])
    team_summary = "\n".join(f"- {t.get('role', '')}: {t.get('grade', '')}, {t.get('mm', 0)} M/M" for t in team) if team else "(팀 구성 미정)"

    # v3.3: 노임단가 + 시장 벤치마크 DB 조회
    labor_rates_table = "(노임단가 데이터 없음)"
    benchmark_summary = "(시장 벤치마크 없음)"
    cost_standard = "KOSA"  # 기본값

    try:
        from app.utils.supabase_client import get_async_client
        client = await get_async_client()
        current_year = datetime.now().year

        # 노임단가 조회 (올해 → 작년 fallback)
        for year in [current_year, current_year - 1]:
            rates = await client.table("labor_rates").select("grade, monthly_rate, daily_rate").eq("year", year).order("monthly_rate", desc=True).execute()
            if rates.data:
                labor_rates_table = "| 등급 | 월단가(원) | 일단가(원) |\n|------|-----------|----------|\n"
                for r in rates.data:
                    labor_rates_table += f"| {r['grade']} | {r['monthly_rate']:,} | {r['daily_rate']:,} |\n"
                break

        # 시장 벤치마크 조회
        market = await client.table("market_price_data").select("domain, bid_ratio, num_bidders, evaluation_method, year").order("year", desc=True).limit(20).execute()
        if market.data:
            avg_ratio = sum(r.get("bid_ratio", 0) for r in market.data) / len(market.data)
            avg_bidders = sum(r.get("num_bidders", 0) for r in market.data) / len(market.data)
            benchmark_summary = f"평균 낙찰률: {avg_ratio:.1f}% | 평균 참여 업체 수: {avg_bidders:.1f}개"
    except Exception as e:
        logger.warning(f"노임단가/벤치마크 조회 실패: {e}")

    budget_framework = BUDGET_DETAIL_FRAMEWORK.format(
        cost_standard=cost_standard,
        labor_rates_table=labor_rates_table,
        benchmark_summary=benchmark_summary,
    )

    prompt = PLAN_PRICE_PROMPT.format(
        rfp_summary=rfp_summary,
        budget=budget or "(예산 미정)",
        positioning=state.get("positioning", "defensive"),
        price_strategy=sf["price_strategy"],
        team_summary=team_summary,
        budget_framework=budget_framework,
    )

    result = await claude_generate(prompt, max_tokens=6000)
    bid_price = result.get("bid_price", result)

    return {
        "parallel_results": {"bid_price": bid_price},
        "budget_detail": bid_price,
    }
