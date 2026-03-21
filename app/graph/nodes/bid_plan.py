"""
STEP 2.5: 입찰가격계획 수립 노드

전략 확정 후, 팀 구성 전에 입찰가를 결정한다.

2단계 시장 조사 전략:
1. 기존 market_price_data에 유사과제 데이터가 충분하면 그대로 활용
2. 부족하면 G2B 크롤링으로 보강 후 PricingEngine 실행

PricingEngine.simulate()를 호출하여 3 시나리오 + 민감도 곡선 + 수주확률을 제공하고,
사용자가 리뷰(review_bid_plan)에서 시나리오를 선택하면
bid_budget_constraint가 확정되어 plan_* 노드의 제약조건이 된다.
"""

import logging

from app.graph.state import BidPlanResult, ProposalState

logger = logging.getLogger(__name__)


async def bid_plan(state: ProposalState) -> dict:
    """STEP 2.5: 입찰가격계획 수립."""
    # 1. RFP에서 핵심 정보 추출
    rfp = state.get("rfp_analysis")
    rfp_dict = {}
    if rfp:
        rfp_dict = rfp.model_dump() if hasattr(rfp, "model_dump") else (
            rfp if isinstance(rfp, dict) else {}
        )

    budget_str = rfp_dict.get("budget", "")
    eval_method = rfp_dict.get("eval_method", "종합심사")
    domain = rfp_dict.get("domain", "SI/SW개발")
    tech_price_ratio = rfp_dict.get("tech_price_ratio", {"tech": 80, "price": 20})
    project_name = rfp_dict.get("project_name", "")
    hot_buttons = rfp_dict.get("hot_buttons", [])

    # 2. Strategy에서 positioning 추출
    positioning = state.get("positioning", "defensive")

    # 예산 파싱 (한 번만 수행)
    budget_val = None
    try:
        from app.services.bid_calculator import parse_budget_string
        budget_val = parse_budget_string(budget_str) if budget_str else None
    except Exception:
        pass

    # 3. 시장 조사: 유사과제 낙찰정보 확인 + 부족하면 G2B 크롤링
    market_research = {}
    if budget_val and budget_val > 0:
        try:
            from app.services.bid_market_research import ensure_market_data
            market_research = await ensure_market_data(
                domain=domain,
                evaluation_method=eval_method,
                budget=budget_val,
                project_name=project_name,
                client_name=rfp_dict.get("client", ""),
                hot_buttons=hot_buttons,
            )
            logger.info(
                f"시장 조사 결과: {market_research.get('data_quality', 'unknown')} "
                f"(기존 {market_research.get('existing_count', 0)}건 "
                f"+ 크롤링 {market_research.get('crawled_count', 0)}건)"
            )
        except Exception as e:
            logger.warning(f"시장 조사 실패 (PricingEngine fallback): {e}")

    # 4. PricingEngine.simulate() 호출 (보강된 데이터 기반)
    result = BidPlanResult()
    try:
        from app.services.pricing import PricingEngine, PricingSimulationRequest

        if budget_val and budget_val > 0:
            engine = PricingEngine()
            sim = await engine.simulate(PricingSimulationRequest(
                budget=budget_val,
                domain=domain,
                evaluation_method=eval_method,
                tech_price_ratio=tech_price_ratio,
                positioning=positioning,
                competitor_count=5,
                personnel=[],  # 팀 구성 전이므로 인력 없음
                client_name=rfp_dict.get("client"),
                proposal_id=state.get("project_id"),
            ))

            result.recommended_bid = sim.recommended_bid
            result.recommended_ratio = sim.recommended_ratio
            result.win_probability = sim.win_probability
            result.data_quality = sim.data_quality

            # 시나리오를 dict로 변환
            result.scenarios = [s.model_dump() for s in sim.scenarios]

            # 민감도 곡선
            result.sensitivity_curve = [p.model_dump() for p in sim.sensitivity_curve]

            # 원가 정보
            if sim.cost_breakdown:
                result.cost_breakdown = sim.cost_breakdown.model_dump()

            # 시장 컨텍스트 (크롤링 보강 정보 병합)
            if sim.market_context:
                mc = sim.market_context.model_dump()
                mc["market_research"] = {
                    "existing_count": market_research.get("existing_count", 0),
                    "crawled_count": market_research.get("crawled_count", 0),
                    "search_keywords": market_research.get("search_keywords", []),
                }
                result.market_context = mc
    except Exception as e:
        logger.warning(f"PricingEngine 분석 실패: {e}")

    # 5. balanced 시나리오 기반 기본 bid_budget_constraint 계산
    constraint = _build_constraint(result, "balanced")

    return {
        "bid_plan": result,
        "bid_budget_constraint": constraint,
        "current_step": "bid_plan_complete",
    }


def _build_constraint(bid_plan: BidPlanResult, scenario_name: str) -> dict:
    """선택된 시나리오 기반으로 plan_* 노드용 예산 제약을 계산."""
    # 시나리오에서 입찰가 찾기
    bid_price = bid_plan.recommended_bid
    bid_ratio = bid_plan.recommended_ratio
    for s in bid_plan.scenarios:
        if s.get("name") == scenario_name:
            bid_price = int(s.get("bid_price", bid_price))
            bid_ratio = float(s.get("bid_ratio", bid_ratio))
            break

    if bid_price <= 0:
        return {}

    # 직접인건비 한도: 입찰가의 ~62% (SW사업 일반적 비율)
    labor_budget = int(bid_price * 0.62)

    # 평균 월단가 (KOSA 중급 기준 ~6,800,000원)
    avg_monthly_rate = 6_800_000
    max_team_mm = round(labor_budget / avg_monthly_rate, 1) if avg_monthly_rate > 0 else 0

    cost_standard = "KOSA"
    if bid_plan.cost_breakdown:
        cost_standard = bid_plan.cost_breakdown.get("cost_standard", "KOSA") or "KOSA"

    return {
        "total_bid_price": bid_price,
        "bid_ratio": bid_ratio,
        "labor_budget": labor_budget,
        "max_team_mm": max_team_mm,
        "scenario_name": scenario_name,
        "cost_standard": cost_standard,
    }
