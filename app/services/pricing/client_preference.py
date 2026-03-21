"""
발주기관 가격 성향 분석

market_price_data에서 특정 발주기관의 낙찰 패턴을 분석.
"""

import logging

from app.services.pricing.models import ClientPricingPreference

logger = logging.getLogger(__name__)


class ClientPreferenceAnalyzer:
    """발주기관 가격 성향 분석기."""

    async def analyze(self, client_name: str | None = None) -> ClientPricingPreference | None:
        """발주기관의 과거 낙찰 패턴 분석."""
        if not client_name:
            return None

        try:
            from app.utils.supabase_client import get_async_client
            client = await get_async_client()

            results = await client.table("market_price_data").select(
                "bid_ratio, budget, evaluation_method, winning_price"
            ).ilike("client_org", f"%{client_name}%").not_.is_(
                "bid_ratio", "null"
            ).order("year", desc=True).limit(50).execute()

            data = results.data or []
            if not data:
                return None

            ratios = [r["bid_ratio"] for r in data if r.get("bid_ratio")]
            budgets = [r["budget"] for r in data if r.get("budget")]
            methods = [r["evaluation_method"] for r in data if r.get("evaluation_method")]

            avg_ratio = sum(ratios) / len(ratios) if ratios else None
            avg_budget = int(sum(budgets) / len(budgets)) if budgets else None
            preferred_method = max(set(methods), key=methods.count) if methods else None

            return ClientPricingPreference(
                client_name=client_name,
                avg_winning_ratio=round(avg_ratio, 4) if avg_ratio else None,
                preferred_evaluation_method=preferred_method,
                total_projects=len(data),
                avg_budget=avg_budget,
            )

        except Exception as e:
            logger.debug(f"발주기관 성향 분석 실패: {e}")
            return None
