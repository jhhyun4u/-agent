"""
PricingEngine — 비딩 가격 산정 오케스트레이터

독립 모듈로 LangGraph 의존 없이 단독 사용 가능.
원가 산정 → 수주확률 → 민감도 분석 → 시나리오 → 시장 컨텍스트 통합.
"""

import logging

from app.services.bidding.pricing.client_preference import ClientPreferenceAnalyzer
from app.services.bidding.pricing.competitor_pricing import CompetitorPricingAnalyzer
from app.services.bidding.pricing.cost_estimator import EnhancedCostEstimator
from app.services.bidding.pricing.cost_standard_selector import CostStandardSelector
from app.services.bidding.pricing.models import (
    BidRange,
    MarketContext,
    PriceScoreDetail,
    PricingSimulationRequest,
    PricingSimulationResult,
    QuickEstimateRequest,
    QuickEstimateResult,
    Scenario,
)
from app.services.bidding.pricing.price_score import PriceScoreCalculator
from app.services.bidding.pricing.sensitivity import SensitivityAnalyzer
from app.services.bidding.pricing.win_probability import WinProbabilityModel

logger = logging.getLogger(__name__)


class PricingEngine:
    """비딩 가격 산정 엔진."""

    def __init__(self):
        self._cost_selector = CostStandardSelector()
        self._cost_estimator = EnhancedCostEstimator()
        self._win_model = WinProbabilityModel()
        self._sensitivity = SensitivityAnalyzer()
        self._competitor = CompetitorPricingAnalyzer()
        self._client_pref = ClientPreferenceAnalyzer()
        self._price_scorer = PriceScoreCalculator()

    async def simulate(self, req: PricingSimulationRequest) -> PricingSimulationResult:
        """풀 시뮬레이션 수행."""
        result = PricingSimulationResult()

        # 1. 비용 기준 선택
        if req.cost_standard:
            result.cost_standard_used = req.cost_standard
            result.cost_standard_reason = "사용자 지정"
        else:
            cs = await self._cost_selector.select(
                domain=req.domain,
                rfp_text=req.rfp_text,
                client_name=req.client_name,
            )
            result.cost_standard_used = cs.standard
            result.cost_standard_reason = cs.reason

        # 2. 원가 산정 (인력 정보 있을 때)
        total_cost = 0
        if req.personnel:
            cost = await self._cost_estimator.estimate(
                personnel=req.personnel,
                cost_standard=result.cost_standard_used,
            )
            result.cost_breakdown = cost
            total_cost = cost.total_cost
        else:
            # 인력 미지정 시 예산의 80%를 원가 추정치로 사용
            total_cost = int(req.budget * 0.80)

        # 3. budget_tier 계산
        budget_tier = _compute_budget_tier(req.budget)

        # 4. 추천 비율 계산 (규칙/통계 자동 선택)
        price_weight = req.tech_price_ratio.get("price", 20)
        rec_ratio = self._compute_recommended_ratio(
            req.evaluation_method, price_weight, req.positioning
        )
        rec_bid = int(req.budget * rec_ratio / 100.0)

        # 원가 이하 방지
        if rec_bid < total_cost and total_cost > 0:
            rec_bid = total_cost
            rec_ratio = round(rec_bid / req.budget * 100, 2) if req.budget > 0 else 0

        result.recommended_bid = rec_bid
        result.recommended_ratio = round(rec_ratio, 2)

        # 5. 수주확률 계산
        prob_result = await self._win_model.calculate(
            bid_ratio=rec_ratio,
            domain=req.domain,
            evaluation_method=req.evaluation_method,
            budget_tier=budget_tier,
            tech_price_ratio=req.tech_price_ratio,
            competitor_count=req.competitor_count,
            positioning=req.positioning,
        )
        result.win_probability = prob_result["win_probability"]
        result.win_probability_confidence = prob_result["confidence"]
        result.comparable_cases = prob_result["comparable_cases"]
        result.data_quality = prob_result["data_quality"]

        # 6. 입찰가 범위
        min_ratio = max(rec_ratio - 5, 70.0)
        max_ratio = min(rec_ratio + 5, 100.0)
        result.bid_range = BidRange(
            min_price=max(int(req.budget * min_ratio / 100), total_cost),
            max_price=int(req.budget * max_ratio / 100),
            min_ratio=round(min_ratio, 2),
            max_ratio=round(max_ratio, 2),
        )

        # 7. 민감도 분석
        sens = await self._sensitivity.analyze(
            budget=req.budget,
            total_cost=total_cost,
            domain=req.domain,
            evaluation_method=req.evaluation_method,
            budget_tier=budget_tier,
            tech_price_ratio=req.tech_price_ratio,
            competitor_count=req.competitor_count,
            positioning=req.positioning,
            center_ratio=rec_ratio,
            range_pct=8.0,
            steps=17,
        )
        result.sensitivity_curve = sens["points"]
        result.optimal_ratio = sens["optimal_ratio"]

        # 8. 3개 시나리오
        result.scenarios = await self._generate_scenarios(
            req, total_cost, budget_tier, rec_ratio
        )

        # 9. 시장 컨텍스트
        result.market_context = await self._get_market_context(req.domain)

        # 10. 가격점수 시뮬레이션
        price_weight = req.tech_price_ratio.get("price", 20)
        tech_weight = req.tech_price_ratio.get("tech", 80)
        assumed_tech = req.assumed_tech_score or (tech_weight * 0.85)  # 기본: 배점의 85%

        # 시나리오별 가격점수 부착
        for scenario in result.scenarios:
            ps = self._price_scorer.calculate(
                bid_price=scenario.bid_price,
                budget=req.budget,
                evaluation_method=req.evaluation_method,
                price_weight=price_weight,
                price_scoring_formula=req.price_scoring_formula,
                competitor_count=req.competitor_count,
            )
            scenario.price_score_detail = PriceScoreDetail(
                price_score=ps.price_score,
                price_weight=ps.price_weight,
                score_ratio=ps.score_ratio,
                total_score=round(assumed_tech + ps.price_score, 2),
                formula_used=ps.formula_used,
                estimated_min_bid=ps.estimated_min_bid,
                is_disqualified=ps.is_disqualified,
            )

        # 가격점수 시뮬레이션 테이블 (입찰가별)
        result.score_simulation = self._price_scorer.simulate_score_table(
            budget=req.budget,
            evaluation_method=req.evaluation_method,
            price_weight=price_weight,
            tech_score=assumed_tech,
            tech_weight=tech_weight,
            price_scoring_formula=req.price_scoring_formula,
            competitor_count=req.competitor_count,
        )

        # 11. 경쟁사/발주기관 분석
        if req.proposal_id:
            try:
                from app.utils.supabase_client import get_async_client
                client = await get_async_client()
                prop = await client.table("proposals").select("org_id").eq(
                    "id", req.proposal_id
                ).single().execute()
                if prop.data:
                    result.competitor_profiles = await self._competitor.analyze(prop.data["org_id"])
            except Exception:
                pass

        if req.client_name:
            result.client_preference = await self._client_pref.analyze(req.client_name)

        return result

    async def quick_estimate(self, req: QuickEstimateRequest) -> QuickEstimateResult:
        """경량 견적 — 원가 없이 시장 데이터 기반 추천 비율 + 확률만."""
        budget_tier = _compute_budget_tier(req.budget)
        price_weight = 20  # 기본값

        rec_ratio = self._compute_recommended_ratio(
            req.evaluation_method, price_weight, req.positioning
        )

        prob_result = await self._win_model.calculate(
            bid_ratio=rec_ratio,
            domain=req.domain,
            evaluation_method=req.evaluation_method,
            budget_tier=budget_tier,
            competitor_count=req.competitor_count,
            positioning=req.positioning,
        )

        # 시장 평균
        market = await self._get_market_context(req.domain)
        market_avg = market.avg_bid_ratio if market else None

        # 포지셔닝 조정 설명
        adj = ""
        if req.positioning == "offensive":
            adj = "공격적 포지셔닝: 낙찰률 하향 조정 (가격 경쟁력 강화)"
        elif req.positioning == "defensive":
            adj = "수성 포지셔닝: 안정적 낙찰률 유지"
        elif req.positioning == "adjacent":
            adj = "인접 포지셔닝: 균형 잡힌 가격 전략"

        return QuickEstimateResult(
            recommended_ratio=round(rec_ratio, 2),
            recommended_bid=int(req.budget * rec_ratio / 100.0),
            win_probability=prob_result["win_probability"],
            win_probability_confidence=prob_result["confidence"],
            comparable_cases=prob_result["comparable_cases"],
            data_quality=prob_result["data_quality"],
            market_avg_ratio=market_avg,
            positioning_adjustment=adj,
        )

    def _compute_recommended_ratio(
        self, evaluation_method: str, price_weight: int, positioning: str
    ) -> float:
        """조달방식 + 포지셔닝 기반 추천 낙찰률 계산."""
        # 조달방식별 기본 비율
        if "적격" in evaluation_method:
            base = 87.9  # 87.745% 하한 바로 위
        elif "최저" in evaluation_method:
            base = 95.0
        elif "수의" in evaluation_method:
            base = 95.0
        else:
            # 종합심사
            if price_weight <= 20:
                base = 91.0
            elif price_weight <= 30:
                base = 88.5
            else:
                base = 86.0

        # 포지셔닝 보정
        if positioning == "offensive":
            base -= 3.0
        elif positioning == "defensive":
            base += 1.5

        return round(max(70.0, min(base, 99.0)), 2)

    async def _generate_scenarios(
        self,
        req: PricingSimulationRequest,
        total_cost: int,
        budget_tier: str | None,
        center_ratio: float,
    ) -> list[Scenario]:
        """보수적/균형/공격적 3개 시나리오 생성."""
        configs = [
            ("conservative", "보수적", center_ratio + 3.0, "low"),
            ("balanced", "균형", center_ratio, "medium"),
            ("aggressive", "공격적", center_ratio - 4.0, "high"),
        ]

        scenarios = []
        for name, label, ratio, risk in configs:
            ratio = max(70.0, min(ratio, 99.0))
            bid_price = int(req.budget * ratio / 100.0)

            # 원가 이하 방지
            if bid_price < total_cost and total_cost > 0:
                bid_price = total_cost
                ratio = round(bid_price / req.budget * 100, 2) if req.budget > 0 else 0

            prob = await self._win_model.calculate(
                bid_ratio=ratio,
                domain=req.domain,
                evaluation_method=req.evaluation_method,
                budget_tier=budget_tier,
                tech_price_ratio=req.tech_price_ratio,
                competitor_count=req.competitor_count,
                positioning=req.positioning,
            )

            margin = bid_price - total_cost
            payoff = int(prob["win_probability"] * margin)

            scenarios.append(Scenario(
                name=name,
                label=label,
                bid_ratio=round(ratio, 2),
                bid_price=bid_price,
                win_probability=prob["win_probability"],
                expected_payoff=payoff,
                risk_level=risk,
            ))

        return scenarios

    async def _get_market_context(self, domain: str) -> MarketContext | None:
        """도메인별 시장 분석 데이터 조회."""
        try:
            from app.utils.supabase_client import get_async_client
            client = await get_async_client()

            result = await client.table("market_price_data").select(
                "bid_ratio, num_bidders, evaluation_method, budget_tier"
            ).eq("domain", domain).not_.is_("bid_ratio", "null").limit(200).execute()

            data = result.data or []
            if not data:
                return MarketContext(domain=domain)

            ratios = [r["bid_ratio"] for r in data if r.get("bid_ratio")]
            bidders = [r["num_bidders"] for r in data if r.get("num_bidders")]

            # 평가방식 분포
            method_dist: dict[str, int] = {}
            for r in data:
                m = r.get("evaluation_method", "")
                if m:
                    method_dist[m] = method_dist.get(m, 0) + 1

            # 예산 규모 분포
            tier_dist: dict[str, int] = {}
            for r in data:
                t = r.get("budget_tier", "")
                if t:
                    tier_dist[t] = tier_dist.get(t, 0) + 1

            return MarketContext(
                domain=domain,
                avg_bid_ratio=round(sum(ratios) / len(ratios), 4) if ratios else None,
                avg_num_bidders=round(sum(bidders) / len(bidders), 1) if bidders else None,
                total_cases=len(data),
                evaluation_method_distribution=method_dist,
                budget_tier_distribution=tier_dist,
            )

        except Exception as e:
            logger.debug(f"시장 컨텍스트 조회 실패: {e}")
            return MarketContext(domain=domain)


def _compute_budget_tier(budget: int) -> str:
    """예산 규모 구간 계산."""
    if budget < 500_000_000:
        return "<500M"
    elif budget < 1_000_000_000:
        return "500M-1B"
    else:
        return ">1B"
