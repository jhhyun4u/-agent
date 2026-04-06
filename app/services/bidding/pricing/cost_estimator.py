"""
DB 기반 원가 산정 — BidCalculator 래핑 + DB 노임단가 우선

기존 bid_calculator.py의 BidCalculator를 내부적으로 재사용하며,
DB(labor_rates)에 해당 연도 데이터가 있으면 DB 단가를 우선 적용한다.
"""

import logging
from datetime import datetime

from app.services.bidding.calculator import (
    BidCalculator,
    _fmt,
)
from app.services.bidding.pricing.models import (
    CostBreakdownDetail,
    PersonnelCostDetail,
    PersonnelInput,
)

logger = logging.getLogger(__name__)


class EnhancedCostEstimator:
    """DB 기반 원가 산정기. BidCalculator를 내부 래핑."""

    INDIRECT_RATE = BidCalculator.INDIRECT_RATE
    TECH_FEE_RATE = BidCalculator.TECH_FEE_RATE
    VAT_RATE = BidCalculator.VAT_RATE

    def __init__(self):
        self._calculator = BidCalculator()

    async def estimate(
        self,
        personnel: list[PersonnelInput],
        cost_standard: str = "KOSA",
        year: int | None = None,
    ) -> CostBreakdownDetail:
        """인력 목록 → 원가 상세 계산. DB 단가 우선, 없으면 하드코딩 fallback."""
        if not personnel:
            return CostBreakdownDetail(
                direct_labor=0, direct_labor_fmt="0원",
                indirect_cost=0, indirect_fmt="0원",
                technical_fee=0, tech_fee_fmt="0원",
                subtotal=0, subtotal_fmt="0원",
                vat=0, vat_fmt="0원",
                total_cost=0, total_cost_fmt="0원",
            )

        year = year or datetime.now().year
        db_rates = await self._load_db_rates(cost_standard, year)

        detail: list[PersonnelCostDetail] = []
        total_labor = 0

        for p in personnel:
            rate = self._get_rate(p.grade, p.labor_type, db_rates)
            amount = int(rate * p.person_months)
            total_labor += amount
            detail.append(PersonnelCostDetail(
                role=p.role,
                grade=p.grade,
                monthly_rate=rate,
                person_months=p.person_months,
                amount=amount,
                amount_fmt=_fmt(amount),
            ))

        indirect = int(total_labor * self.INDIRECT_RATE)
        tech_fee = int((total_labor + indirect) * self.TECH_FEE_RATE)
        subtotal = total_labor + indirect + tech_fee
        vat = int(subtotal * self.VAT_RATE)
        total = subtotal + vat

        return CostBreakdownDetail(
            direct_labor=total_labor,
            direct_labor_fmt=_fmt(total_labor),
            indirect_cost=indirect,
            indirect_fmt=_fmt(indirect),
            technical_fee=tech_fee,
            tech_fee_fmt=_fmt(tech_fee),
            subtotal=subtotal,
            subtotal_fmt=_fmt(subtotal),
            vat=vat,
            vat_fmt=_fmt(vat),
            total_cost=total,
            total_cost_fmt=_fmt(total),
            personnel_detail=detail,
        )

    async def _load_db_rates(self, cost_standard: str, year: int) -> dict[str, int]:
        """DB labor_rates에서 해당 연도 단가 로드. 실패 시 빈 dict."""
        try:
            from app.utils.supabase_client import get_async_client
            client = await get_async_client()

            for y in [year, year - 1]:
                query = client.table("labor_rates").select("grade, monthly_rate")
                if cost_standard:
                    query = query.eq("standard", cost_standard)
                result = await query.eq("year", y).execute()

                if result.data:
                    return {r["grade"]: r["monthly_rate"] for r in result.data}
        except Exception as e:
            logger.debug(f"DB 노임단가 로드 실패 (fallback 사용): {e}")
        return {}

    def _get_rate(self, grade: str, labor_type: str, db_rates: dict[str, int]) -> int:
        """DB 단가 우선, 없으면 BidCalculator 하드코딩 단가."""
        if grade in db_rates:
            return db_rates[grade]
        return self._calculator.get_monthly_rate(grade, labor_type)
