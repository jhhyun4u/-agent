"""
비딩 가격 시뮬레이션 API

POST /api/pricing/simulate          — 풀 시뮬레이션
POST /api/pricing/quick-estimate    — 경량 견적
GET  /api/pricing/simulations       — 시뮬레이션 이력
GET  /api/pricing/simulations/{id}  — 시뮬레이션 상세
GET  /api/pricing/market-analysis   — 도메인별 시장 분석
POST /api/pricing/sensitivity       — 단독 민감도 분석
GET  /api/pricing/prediction-accuracy — 예측 정확도 리포트
"""

import logging

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.exceptions import TenopAPIError
from app.services.pricing import (
    PricingEngine,
    PricingSimulationRequest,
    QuickEstimateRequest,
)
from app.services.pricing.models import PersonnelInput
from app.services.pricing.sensitivity import SensitivityAnalyzer
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
    user=Depends(get_current_user),
):
    """풀 시뮬레이션 — 원가 + 수주확률 + 민감도 + 시나리오."""
    result = await _engine.simulate(body)

    # 이력 저장
    try:
        client = await get_async_client()
        org_id = user.get("org_id", user.get("team_id", ""))
        sim_row = {
            "org_id": org_id,
            "created_by": user.get("id"),
            "proposal_id": body.proposal_id,
            "params": body.model_dump(mode="json"),
            "result": result.model_dump(mode="json"),
        }
        await client.table("pricing_simulations").insert(sim_row).execute()
    except Exception as e:
        logger.warning(f"시뮬레이션 이력 저장 실패 (무시): {e}")

    return result.model_dump(mode="json")


# ════════════════════════════════════════
# 경량 견적
# ════════════════════════════════════════

@router.post("/quick-estimate")
async def quick_estimate(
    body: QuickEstimateRequest,
    user=Depends(get_current_user),
):
    """경량 견적 — 원가 없이 추천 비율 + 확률만."""
    result = await _engine.quick_estimate(body)
    return result.model_dump(mode="json")


# ════════════════════════════════════════
# 시뮬레이션 이력
# ════════════════════════════════════════

@router.get("/simulations")
async def list_simulations(
    proposal_id: str | None = Query(None),
    skip: int = 0,
    limit: int = 20,
    user=Depends(get_current_user),
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

    return {"items": items, "total": len(items)}


@router.get("/simulations/{simulation_id}")
async def get_simulation(simulation_id: str, user=Depends(get_current_user)):
    """시뮬레이션 상세 조회."""
    client = await get_async_client()
    result = await client.table("pricing_simulations").select("*").eq(
        "id", simulation_id
    ).single().execute()

    if not result.data:
        raise TenopAPIError("PRICING_001", "시뮬레이션을 찾을 수 없습니다.", 404)

    return result.data


# ════════════════════════════════════════
# 시장 분석
# ════════════════════════════════════════

@router.get("/market-analysis")
async def market_analysis(
    domain: str = Query("SI/SW개발"),
    evaluation_method: str | None = Query(None),
    user=Depends(get_current_user),
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
        return {
            "domain": domain,
            "total_cases": 0,
            "avg_bid_ratio": None,
            "avg_num_bidders": None,
            "distribution": [],
        }

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

    return {
        "domain": domain,
        "total_cases": len(data),
        "avg_bid_ratio": round(sum(ratios) / len(ratios), 4) if ratios else None,
        "avg_num_bidders": round(sum(bidders) / len(bidders), 1) if bidders else None,
        "distribution": [{"bucket": k, "count": v} for k, v in sorted(buckets.items())],
        "yearly_trend": yearly_trend,
    }


# ════════════════════════════════════════
# 단독 민감도 분석
# ════════════════════════════════════════

from pydantic import BaseModel


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
    user=Depends(get_current_user),
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

    return {
        "points": [p.model_dump() for p in result["points"]],
        "optimal_ratio": result["optimal_ratio"],
        "optimal_payoff": result["optimal_payoff"],
    }


# ════════════════════════════════════════
# 예측 정확도 리포트
# ════════════════════════════════════════

@router.get("/prediction-accuracy")
async def prediction_accuracy(user=Depends(get_current_user)):
    """예측 정확도 리포트 — 해소된 prediction 기반 통계."""
    client = await get_async_client()

    resolved = await client.table("pricing_predictions").select(
        "predicted_ratio, predicted_win_prob, actual_ratio, actual_result, prediction_error"
    ).not_.is_("resolved_at", "null").order("resolved_at", desc=True).limit(100).execute()

    data = resolved.data or []
    if not data:
        return {"total_resolved": 0, "avg_error": None, "accuracy_by_result": {}}

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

    return {
        "total_resolved": len(data),
        "avg_error": avg_error,
        "accuracy_by_result": accuracy_by_result,
    }
