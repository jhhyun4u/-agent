"""
수주확률 모델 — 2단계 전략 (규칙 기반 → 통계 KDE)

데이터 30건 미만: 조달방식별 규칙 기반 (BidCalculator 로직 확장)
데이터 30건 이상: gaussian_kde 기반 낙찰률 분포 추정
"""

import logging
import math

from app.services.bid_calculator import BidCalculator, ProcurementMethod

logger = logging.getLogger(__name__)

# 조달방식 문자열 → ProcurementMethod 매핑
_METHOD_MAP = {
    "종합심사": ProcurementMethod.COMPREHENSIVE,
    "종합평가": ProcurementMethod.COMPREHENSIVE,
    "적격심사": ProcurementMethod.ADEQUATE_REVIEW,
    "최저가": ProcurementMethod.LOWEST_PRICE,
    "수의계약": ProcurementMethod.NEGOTIATED,
}


class WinProbabilityModel:
    """수주확률 계산 모델. 데이터 양에 따라 규칙/통계 자동 전환."""

    MIN_CASES_FOR_STATS = 30

    async def calculate(
        self,
        bid_ratio: float,
        domain: str,
        evaluation_method: str,
        budget_tier: str | None,
        tech_price_ratio: dict | None = None,
        competitor_count: int = 5,
        positioning: str | None = None,
    ) -> dict:
        """
        수주확률 계산.

        Returns:
            {
                "win_probability": 0.72,
                "confidence": "medium",
                "comparable_cases": 15,
                "data_quality": "rule_based" | "statistical",
                "method_detail": str,
            }
        """
        cases = await self._query_comparable(domain, evaluation_method, budget_tier)

        if len(cases) >= self.MIN_CASES_FOR_STATS:
            return self._statistical_model(bid_ratio, cases, tech_price_ratio, competitor_count, positioning)
        else:
            return self._rule_based_model(
                bid_ratio, evaluation_method, tech_price_ratio, competitor_count, positioning, len(cases)
            )

    def _rule_based_model(
        self,
        bid_ratio: float,
        evaluation_method: str,
        tech_price_ratio: dict | None,
        competitor_count: int,
        positioning: str | None,
        case_count: int,
    ) -> dict:
        """규칙 기반 수주확률 모델. BidCalculator 최적 구간 로직 확장."""
        method = _METHOD_MAP.get(evaluation_method, ProcurementMethod.COMPREHENSIVE)
        price_weight = (tech_price_ratio or {}).get("price", 20)

        # 조달방식별 최적 비율과 분포 폭
        if method == ProcurementMethod.ADEQUATE_REVIEW:
            # 적격심사: 87.745% 근처 집중
            optimal = 87.745
            sigma = 0.8
        elif method == ProcurementMethod.COMPREHENSIVE:
            # 종합심사: 가격 비중에 따라 최적점 이동
            if price_weight <= 20:
                optimal = 91.0
            elif price_weight <= 30:
                optimal = 88.5
            else:
                optimal = 86.0
            sigma = 3.0
        elif method == ProcurementMethod.LOWEST_PRICE:
            # 최저가: 원가+최소마진
            optimal = 95.0
            sigma = 2.0
        else:
            # 수의계약: 95% 수준 안정
            optimal = 95.0
            sigma = 4.0

        # 포지셔닝 보정
        if positioning == "offensive":
            optimal -= 3.0
        elif positioning == "defensive":
            optimal += 1.5

        # 정규분포 기반 확률 근사 (최적점에서의 거리)
        ratio_pct = bid_ratio * 100 if bid_ratio < 1.5 else bid_ratio
        distance = abs(ratio_pct - optimal)
        base_prob = math.exp(-(distance ** 2) / (2 * sigma ** 2))

        # 경쟁사 수 보정: 1/N 기반
        competition_factor = max(0.3, 1.0 / max(competitor_count, 1))
        # 기본 승률 20~80% 범위로 스케일
        win_prob = min(0.85, max(0.05, base_prob * (0.3 + 0.7 * competition_factor)))

        # 적격심사: 하한 아래면 탈락
        if method == ProcurementMethod.ADEQUATE_REVIEW and ratio_pct < 87.745:
            win_prob = 0.0

        confidence = "low" if case_count < 5 else "medium"

        return {
            "win_probability": round(win_prob, 4),
            "confidence": confidence,
            "comparable_cases": case_count,
            "data_quality": "rule_based",
            "method_detail": f"규칙 기반 (최적 {optimal:.1f}%, σ={sigma:.1f}, 경쟁사 {competitor_count}개)",
        }

    def _statistical_model(
        self,
        bid_ratio: float,
        cases: list[dict],
        tech_price_ratio: dict | None,
        competitor_count: int,
        positioning: str | None,
    ) -> dict:
        """통계 기반 수주확률 모델. KDE로 낙찰률 분포 추정."""
        ratios = [c["bid_ratio"] for c in cases if c.get("bid_ratio")]
        if not ratios:
            return self._rule_based_model(bid_ratio, "종합심사", tech_price_ratio, competitor_count, positioning, 0)

        try:
            from scipy.stats import gaussian_kde
            kde = gaussian_kde(ratios)
        except Exception:
            # scipy 없거나 KDE 실패 시 규칙 기반 fallback
            return self._rule_based_model(bid_ratio, "종합심사", tech_price_ratio, competitor_count, positioning, len(ratios))

        ratio_pct = bid_ratio * 100 if bid_ratio < 1.5 else bid_ratio
        ratio_dec = ratio_pct / 100.0

        # KDE 밀도 → 확률 변환
        # 자신의 비율이 실제 낙찰 분포에서 얼마나 높은 밀도인지
        density_at_point = float(kde(ratio_dec)[0])
        max_density = float(kde(ratios).max())

        if max_density > 0:
            relative_density = density_at_point / max_density
        else:
            relative_density = 0.5

        # 경쟁사 수 보정
        competition_factor = max(0.3, 1.0 / max(competitor_count, 1))
        win_prob = min(0.90, max(0.05, relative_density * (0.3 + 0.7 * competition_factor)))

        # 포지셔닝 미세 보정
        if positioning == "offensive":
            win_prob = min(0.90, win_prob * 1.08)
        elif positioning == "defensive":
            win_prob = win_prob * 0.95

        confidence = "high" if len(ratios) >= 100 else "medium"

        return {
            "win_probability": round(win_prob, 4),
            "confidence": confidence,
            "comparable_cases": len(ratios),
            "data_quality": "statistical",
            "method_detail": f"KDE 통계 모델 (유사 사례 {len(ratios)}건, 밀도 {relative_density:.2f})",
        }

    async def _query_comparable(
        self, domain: str, evaluation_method: str, budget_tier: str | None,
    ) -> list[dict]:
        """market_price_data에서 유사 사례 조회."""
        try:
            from app.utils.supabase_client import get_async_client
            client = await get_async_client()

            query = client.table("market_price_data").select(
                "bid_ratio, num_bidders, budget, evaluation_method, budget_tier, year"
            ).not_.is_("bid_ratio", "null")

            # 도메인 필터
            if domain:
                query = query.eq("domain", domain)

            # 평가방식 필터 (있으면)
            if evaluation_method:
                query = query.eq("evaluation_method", evaluation_method)

            # 예산 규모 필터 (있으면)
            if budget_tier:
                query = query.eq("budget_tier", budget_tier)

            result = await query.order("year", desc=True).limit(200).execute()
            return result.data or []

        except Exception as e:
            logger.debug(f"시장 데이터 조회 실패: {e}")
            return []
