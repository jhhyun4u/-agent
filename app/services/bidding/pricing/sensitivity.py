"""
민감도 분석 — 입찰 비율 범위별 수주확률·기대수익 곡선

X축: 낙찰률 (bid_ratio)
Y축: 수주확률, 기대수익(= win_prob * margin)
최적점: 기대수익 극대화 비율
"""

import logging

from app.services.bidding.pricing.models import SensitivityPoint
from app.services.bidding.pricing.win_probability import WinProbabilityModel

logger = logging.getLogger(__name__)


class SensitivityAnalyzer:
    """민감도 분석기. 입찰 비율 범위를 스윕하며 최적점을 찾는다."""

    def __init__(self):
        self._model = WinProbabilityModel()

    async def analyze(
        self,
        budget: int,
        total_cost: int,
        domain: str,
        evaluation_method: str,
        budget_tier: str | None,
        tech_price_ratio: dict | None = None,
        competitor_count: int = 5,
        positioning: str | None = None,
        range_pct: float = 10.0,
        steps: int = 21,
        center_ratio: float | None = None,
    ) -> dict:
        """
        민감도 분석 수행.

        Args:
            budget: 예산 (원)
            total_cost: 총원가 (원)
            center_ratio: 중심 비율 (%). None이면 90% 기본
            range_pct: ±범위 (%)
            steps: 포인트 수

        Returns:
            {"points": [...], "optimal_ratio": float, "optimal_payoff": int}
        """
        center = center_ratio or 90.0
        min_ratio = max(center - range_pct, 70.0)
        max_ratio = min(center + range_pct, 100.0)
        step_size = (max_ratio - min_ratio) / max(steps - 1, 1)

        points: list[SensitivityPoint] = []
        best_payoff = -float("inf")
        best_ratio = center

        for i in range(steps):
            ratio = min_ratio + i * step_size
            bid_price = int(budget * ratio / 100.0)
            margin = bid_price - total_cost

            result = await self._model.calculate(
                bid_ratio=ratio,
                domain=domain,
                evaluation_method=evaluation_method,
                budget_tier=budget_tier,
                tech_price_ratio=tech_price_ratio,
                competitor_count=competitor_count,
                positioning=positioning,
            )

            win_prob = result["win_probability"]
            expected_payoff = int(win_prob * margin) if margin > 0 else int(win_prob * margin)

            points.append(SensitivityPoint(
                ratio=round(ratio, 2),
                bid_price=bid_price,
                win_prob=round(win_prob, 4),
                expected_payoff=expected_payoff,
            ))

            if expected_payoff > best_payoff:
                best_payoff = expected_payoff
                best_ratio = ratio

        return {
            "points": points,
            "optimal_ratio": round(best_ratio, 2),
            "optimal_payoff": int(best_payoff),
        }
