"""
비딩 가격 시뮬레이션 API

POST /api/pricing/simulate          — 풀 시뮬레이션
POST /api/pricing/quick-estimate    — 경량 견적
GET  /api/pricing/simulations       — 시뮬레이션 이력
GET  /api/pricing/simulations/{id}  — 시뮬레이션 상세
POST /api/pricing/simulations/{id}/apply/{proposal_id} — 프로젝트에 적용
GET  /api/pricing/market-analysis   — 도메인별 시장 분석
POST /api/pricing/sensitivity       — 단독 민감도 분석
GET  /api/pricing/prediction-accuracy — 예측 정확도 리포트
"""

import logging

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.api.response import ok, ok_list
from app.exceptions import TenopAPIError
from app.models.auth_schemas import CurrentUser
from app.services.bidding.pricing import (
    PricingEngine,
    PricingSimulationRequest,
    QuickEstimateRequest,
)
from app.services.bidding.pricing.sensitivity import SensitivityAnalyzer
from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/pricing", tags=["pricing"])

_engine = PricingEngine()
_sensitivity = SensitivityAnalyzer()


# ════════════════════════════════════════
# 풀 시뮬레이션
# ════════════════════════════════════════

@router.post("/simulate")
async def simulate_pricing(
    body: PricingSimulationRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """풀 시뮬레이션 — 원가 + 수주확률 + 민감도 + 시나리오."""
    result = await _engine.simulate(body)

    # 이력 저장
    try:
        client = await get_async_client()
        org_id = user.org_id or user.team_id or ""
        sim_row = {
            "org_id": org_id,
            "created_by": user.id,
            "proposal_id": body.proposal_id,
            "params": body.model_dump(mode="json"),
            "result": result.model_dump(mode="json"),
        }
        await client.table("pricing_simulations").insert(sim_row).execute()
    except Exception as e:
        logger.warning(f"시뮬레이션 이력 저장 실패 (무시): {e}")

    return ok(result.model_dump(mode="json"))


# ════════════════════════════════════════
# 경량 견적
# ════════════════════════════════════════

@router.post("/quick-estimate")
async def quick_estimate(
    body: QuickEstimateRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """경량 견적 — 원가 없이 추천 비율 + 확률만."""
    result = await _engine.quick_estimate(body)
    return ok(result.model_dump(mode="json"))


# ════════════════════════════════════════
# 시뮬레이션 이력
# ════════════════════════════════════════

@router.get("/simulations")
async def list_simulations(
    proposal_id: str | None = Query(None),
    skip: int = 0,
    limit: int = 20,
    user: CurrentUser = Depends(get_current_user),
):
    """시뮬레이션 이력 조회."""
    client = await get_async_client()
    query = client.table("pricing_simulations").select(
        "id, proposal_id, params, created_at, selected_scenario"
    ).order("created_at", desc=True).range(skip, skip + limit - 1)

    if proposal_id:
        query = query.eq("proposal_id", proposal_id)

    result = await query.execute()
    items = []
    for r in (result.data or []):
        params = r.get("params", {})
        items.append({
            "id": r["id"],
            "proposal_id": r.get("proposal_id"),
            "budget": params.get("budget", 0),
            "domain": params.get("domain", ""),
            "evaluation_method": params.get("evaluation_method", ""),
            "positioning": params.get("positioning", ""),
            "selected_scenario": r.get("selected_scenario"),
            "created_at": r.get("created_at"),
        })

    return ok_list(items, total=len(items), offset=skip, limit=limit)


@router.get("/simulations/{simulation_id}")
async def get_simulation(simulation_id: str, user: CurrentUser = Depends(get_current_user)):
    """시뮬레이션 상세 조회."""
    client = await get_async_client()
    result = await client.table("pricing_simulations").select("*").eq(
        "id", simulation_id
    ).single().execute()

    if not result.data:
        raise TenopAPIError("PRICING_001", "시뮬레이션을 찾을 수 없습니다.", 404)

    return ok(result.data)


# ════════════════════════════════════════
# 시장 분석
# ════════════════════════════════════════

@router.get("/market-analysis")
async def market_analysis(
    domain: str = Query("SI/SW개발"),
    evaluation_method: str | None = Query(None),
    user: CurrentUser = Depends(get_current_user),
):
    """도메인별 시장 분석."""
    client = await get_async_client()
    query = client.table("market_price_data").select(
        "bid_ratio, num_bidders, budget, evaluation_method, budget_tier, year, client_org, winner_name"
    ).eq("domain", domain).not_.is_("bid_ratio", "null").order("year", desc=True).limit(200)

    if evaluation_method:
        query = query.eq("evaluation_method", evaluation_method)

    result = await query.execute()
    data = result.data or []

    if not data:
        return ok({
            "domain": domain,
            "total_cases": 0,
            "avg_bid_ratio": None,
            "avg_num_bidders": None,
            "distribution": [],
        })

    ratios = [r["bid_ratio"] for r in data if r.get("bid_ratio")]
    bidders = [r["num_bidders"] for r in data if r.get("num_bidders")]

    # 히스토그램 (5% 구간)
    buckets: dict[str, int] = {}
    for ratio in ratios:
        pct = ratio * 100 if ratio < 1.5 else ratio
        bucket = f"{int(pct // 5 * 5)}-{int(pct // 5 * 5 + 5)}"
        buckets[bucket] = buckets.get(bucket, 0) + 1

    # 연도별 추이
    by_year: dict[int, list[float]] = {}
    for r in data:
        y = r.get("year")
        if y and r.get("bid_ratio"):
            by_year.setdefault(y, []).append(r["bid_ratio"])

    yearly_trend = [
        {"year": y, "avg_ratio": round(sum(rs) / len(rs), 4), "count": len(rs)}
        for y, rs in sorted(by_year.items())
    ]

    return ok({
        "domain": domain,
        "total_cases": len(data),
        "avg_bid_ratio": round(sum(ratios) / len(ratios), 4) if ratios else None,
        "avg_num_bidders": round(sum(bidders) / len(bidders), 1) if bidders else None,
        "distribution": [{"bucket": k, "count": v} for k, v in sorted(buckets.items())],
        "yearly_trend": yearly_trend,
    })


# ════════════════════════════════════════
# 단독 민감도 분석
# ════════════════════════════════════════


class SensitivityRequest(BaseModel):
    budget: int
    total_cost: int = 0
    domain: str = "SI/SW개발"
    evaluation_method: str = "종합심사"
    tech_price_ratio: dict | None = None
    competitor_count: int = 5
    positioning: str = "defensive"
    center_ratio: float | None = None
    range_pct: float = 10.0
    steps: int = 21


@router.post("/sensitivity")
async def sensitivity_analysis(
    body: SensitivityRequest,
    user: CurrentUser = Depends(get_current_user),
):
    """단독 민감도 분석."""
    total_cost = body.total_cost or int(body.budget * 0.80)
    budget_tier = "<500M" if body.budget < 500_000_000 else ("500M-1B" if body.budget < 1_000_000_000 else ">1B")

    result = await _sensitivity.analyze(
        budget=body.budget,
        total_cost=total_cost,
        domain=body.domain,
        evaluation_method=body.evaluation_method,
        budget_tier=budget_tier,
        tech_price_ratio=body.tech_price_ratio,
        competitor_count=body.competitor_count,
        positioning=body.positioning,
        center_ratio=body.center_ratio,
        range_pct=body.range_pct,
        steps=body.steps,
    )

    return ok({
        "points": [p.model_dump() for p in result["points"]],
        "optimal_ratio": result["optimal_ratio"],
        "optimal_payoff": result["optimal_payoff"],
    })


# ════════════════════════════════════════
# 예측 정확도 리포트
# ════════════════════════════════════════

@router.get("/prediction-accuracy")
async def prediction_accuracy(user: CurrentUser = Depends(get_current_user)):
    """예측 정확도 리포트 — 해소된 prediction 기반 통계."""
    client = await get_async_client()

    resolved = await client.table("pricing_predictions").select(
        "predicted_ratio, predicted_win_prob, actual_ratio, actual_result, prediction_error"
    ).not_.is_("resolved_at", "null").order("resolved_at", desc=True).limit(100).execute()

    data = resolved.data or []
    if not data:
        return ok({"total_resolved": 0, "avg_error": None, "accuracy_by_result": {}})

    errors = [abs(r["prediction_error"]) for r in data if r.get("prediction_error") is not None]
    avg_error = round(sum(errors) / len(errors), 4) if errors else None

    by_result: dict[str, dict] = {}
    for r in data:
        result_type = r.get("actual_result", "unknown")
        if result_type not in by_result:
            by_result[result_type] = {"count": 0, "errors": []}
        by_result[result_type]["count"] += 1
        if r.get("prediction_error") is not None:
            by_result[result_type]["errors"].append(abs(r["prediction_error"]))

    accuracy_by_result = {}
    for result_type, stats in by_result.items():
        errs = stats["errors"]
        accuracy_by_result[result_type] = {
            "count": stats["count"],
            "avg_error": round(sum(errs) / len(errs), 4) if errs else None,
        }

    return ok({
        "total_resolved": len(data),
        "avg_error": avg_error,
        "accuracy_by_result": accuracy_by_result,
    })


# ════════════════════════════════════════
# 시뮬레이션 → 프로젝트 적용
# ════════════════════════════════════════

@router.post("/simulations/{simulation_id}/apply/{proposal_id}")
async def apply_simulation_to_proposal(
    simulation_id: str,
    proposal_id: str,
    user: CurrentUser = Depends(get_current_user),
):
    """시뮬레이션 결과를 프로젝트 bid_plan 상태에 적용."""
    client = await get_async_client()

    # 1. 시뮬레이션 조회
    sim_res = await client.table("pricing_simulations").select("*").eq(
        "id", simulation_id
    ).single().execute()
    if not sim_res.data:
        raise TenopAPIError("PRICING_001", "시뮬레이션을 찾을 수 없습니다.", 404)

    sim_result = sim_res.data.get("result", {})

    # 2. 그래프 상태에 bid_plan 업데이트
    from app.api.routes_workflow import _get_graph

    graph = await _get_graph()
    config = {"configurable": {"thread_id": proposal_id}}

    snapshot = await graph.aget_state(config)
    if not snapshot:
        raise TenopAPIError("PROPOSAL_001", "프로젝트를 찾을 수 없습니다.", 404)

    # bid_plan 형태로 매핑
    bid_plan = {
        "recommended_bid": sim_result.get("recommended_bid", 0),
        "recommended_ratio": sim_result.get("recommended_ratio", 0),
        "scenarios": sim_result.get("scenarios", []),
        "selected_scenario": "balanced",
        "cost_breakdown": sim_result.get("cost_breakdown"),
        "sensitivity_curve": sim_result.get("sensitivity_curve", []),
        "win_probability": sim_result.get("win_probability", 0),
        "market_context": sim_result.get("market_context"),
        "data_quality": sim_result.get("data_quality", "rule_based"),
        "score_simulation": sim_result.get("score_simulation", []),
        "user_override_price": None,
        "user_override_reason": "",
        "source": "pricing_simulator",
        "simulation_id": simulation_id,
    }

    # bid_budget_constraint (계획 수립 시 예산 상한)
    budget_constraint = {
        "max_bid": sim_result.get("recommended_bid", 0),
        "source": "pricing_simulator",
    }

    await graph.aupdate_state(config, {
        "bid_plan": bid_plan,
        "bid_budget_constraint": budget_constraint,
    })

    # 3. pricing_simulations에 proposal_id 연결
    await client.table("pricing_simulations").update({
        "proposal_id": proposal_id,
    }).eq("id", simulation_id).execute()

    logger.info(
        f"시뮬레이션 적용: simulation={simulation_id} → proposal={proposal_id}, "
        f"user={user.id}"
    )

    return ok({
        "applied": True,
        "proposal_id": proposal_id,
        "simulation_id": simulation_id,
        "recommended_bid": bid_plan["recommended_bid"],
    })
