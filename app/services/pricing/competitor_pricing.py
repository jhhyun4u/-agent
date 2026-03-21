"""
경쟁사 가격 패턴 분석

competitors 테이블 + market_price_data에서 경쟁사의 입찰 패턴을 분석.
"""

import logging

from app.services.pricing.models import CompetitorPricingProfile

logger = logging.getLogger(__name__)


class CompetitorPricingAnalyzer:
    """경쟁사 가격 패턴 분석기."""

    async def analyze(self, org_id: str | None = None) -> list[CompetitorPricingProfile]:
        """조직의 경쟁사 목록과 가격 패턴 조회."""
        if not org_id:
            return []

        try:
            from app.utils.supabase_client import get_async_client
            client = await get_async_client()

            comps = await client.table("competitors").select(
                "company_name, win_count, avg_bid_ratio, total_bids, preferred_positioning"
            ).eq("org_id", org_id).order("win_count", desc=True).limit(10).execute()

            profiles = []
            for c in (comps.data or []):
                profiles.append(CompetitorPricingProfile(
                    company_name=c.get("company_name", ""),
                    avg_bid_ratio=c.get("avg_bid_ratio"),
                    win_count=c.get("win_count", 0) or 0,
                    total_bids=c.get("total_bids", 0) or 0,
                    preferred_positioning=c.get("preferred_positioning"),
                ))

            return profiles

        except Exception as e:
            logger.debug(f"경쟁사 가격 분석 실패: {e}")
            return []
