"""
비딩 워크스페이스 서비스 (Stream 2)

기존 bid_handoff.py를 확장하여 워크플로 완료 후 가격 조정,
통합 비딩 현황, 시장 추적 요약을 제공.
"""

import json
import logging
from datetime import datetime, timezone

from app.utils.supabase_client import get_async_client

logger = logging.getLogger(__name__)


async def get_bidding_workspace(proposal_id: str) -> dict:
    """통합 비딩 현황 — 확정가, 시나리오, 이력, 투찰 상태를 하나로."""
    from app.services.bid_handoff import (
        get_bid_price_history,
        get_bid_submission_status,
    )

    status = await get_bid_submission_status(proposal_id)
    history = await get_bid_price_history(proposal_id)

    # 시나리오 데이터 (artifacts에서 가져오기)
    scenarios = await _get_bid_plan_scenarios(proposal_id)

    # 시장 추적 요약
    market_summary = await get_market_tracking_summary(proposal_id)

    return {
        "proposal_id": proposal_id,
        "bid_status": status,
        "scenarios": scenarios,
        "price_history": history,
        "market_summary": market_summary,
    }


async def update_bid_price_post_workflow(
    proposal_id: str,
    adjusted_price: int,
    reason: str,
    user_id: str,
    user_name: str = "",
) -> dict:
    """워크플로 완료 후 가격 조정.

    bid_plan 리뷰에서 확정된 후, 외부 정보 등으로 가격을 변경해야 할 때 사용.
    """
    client = await get_async_client()
    now = datetime.now(timezone.utc).isoformat()

    # 현재 확정가 조회
    prop = await (
        client.table("proposals")
        .select("bid_confirmed_price, bid_amount")
        .eq("id", proposal_id)
        .single()
        .execute()
    )
    if not prop.data:
        return {"success": False, "message": "제안서를 찾을 수 없습니다."}

    old_price = prop.data.get("bid_confirmed_price") or prop.data.get("bid_amount") or 0

    # proposals 업데이트
    await (
        client.table("proposals")
        .update({
            "bid_confirmed_price": adjusted_price,
            "bid_amount": adjusted_price,
            "updated_at": now,
        })
        .eq("id", proposal_id)
        .execute()
    )

    # 이력 기록
    await client.table("bid_price_history").insert({
        "proposal_id": proposal_id,
        "event_type": "adjusted",
        "price": adjusted_price,
        "reason": reason,
        "actor_id": user_id,
        "actor_name": user_name,
        "metadata": json.dumps({
            "previous_price": old_price,
            "adjustment_type": "post_workflow",
        }, ensure_ascii=False),
    }).execute()

    # Stream 2 진행률 갱신
    from app.services.stream_orchestrator import update_stream_progress
    await update_stream_progress(
        proposal_id, "bidding",
        current_phase="price_adjusted",
    )

    logger.info(
        f"가격 조정: proposal={proposal_id}, "
        f"{old_price:,} → {adjusted_price:,}원, reason={reason}"
    )

    return {
        "success": True,
        "new_price": adjusted_price,
        "event_type": "adjusted",
        "message": f"가격이 {adjusted_price:,}원으로 조정되었습니다.",
    }


async def get_market_tracking_summary(proposal_id: str) -> dict:
    """시장 추적 요약 — 유사과제 낙찰정보 + 경쟁 동향."""
    client = await get_async_client()

    # pricing_simulations에서 최신 시뮬레이션 결과 조회
    sim_res = await (
        client.table("pricing_simulations")
        .select("result_data")
        .eq("proposal_id", proposal_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )

    if sim_res.data and sim_res.data[0].get("result_data"):
        result = sim_res.data[0]["result_data"]
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except (json.JSONDecodeError, TypeError):
                result = {}
        return {
            "comparable_cases": result.get("comparable_cases", 0),
            "market_avg_ratio": result.get("market_context", {}).get("avg_bid_ratio"),
            "data_quality": result.get("data_quality", "unknown"),
            "win_probability": result.get("win_probability", 0),
        }

    return {
        "comparable_cases": 0,
        "market_avg_ratio": None,
        "data_quality": "no_data",
        "win_probability": 0,
    }


async def _get_bid_plan_scenarios(proposal_id: str) -> list[dict]:
    """bid_plan 산출물에서 시나리오 데이터 추출."""
    client = await get_async_client()
    res = await (
        client.table("artifacts")
        .select("content")
        .eq("proposal_id", proposal_id)
        .eq("step", "bid_plan")
        .order("version", desc=True)
        .limit(1)
        .execute()
    )
    if not res.data:
        return []

    content = res.data[0].get("content", "")
    if isinstance(content, str):
        try:
            content = json.loads(content)
        except (json.JSONDecodeError, TypeError):
            return []

    return content.get("scenarios", [])
