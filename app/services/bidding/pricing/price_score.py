"""
가격점수 산출기 — 한국 공공조달 가격평가 공식 기반

RFP에 가격점수 산식이 명시되어 있으면 해당 공식을 사용하고,
없으면 평가방식별 표준 공식을 적용한다.

■ 표준 공식 (조달청 기준)

1. 종합심사 (가장 일반적)
   가격점수 = 가격배점 × (최저입찰가 / 당사입찰가)

2. 적격심사
   87.745% 이상이면 합격, 합격자 중 최저가 낙찰
   가격점수 개념 없음 (pass/fail + 순위)

3. 최저가
   가격이 곧 순위 (가격점수 = 100% 비중)
   가격점수 = 배점 × (최저입찰가 / 당사입찰가)

4. 협상에 의한 계약 (수의계약)
   가격점수 = 배점 × (추정가격 / 입찰가격)
   또는 고정 비율 적용
"""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class PriceScoreResult:
    """가격점수 산출 결과."""
    price_score: float           # 가격점수 (배점 내)
    price_weight: float          # 가격 배점 (만점)
    score_ratio: float           # 득점률 (price_score / price_weight)
    formula_used: str            # 적용된 공식 설명
    estimated_min_bid: int       # 추정 최저입찰가 (시뮬레이션 기준)
    bid_price: int               # 당사 입찰가
    is_disqualified: bool = False  # 탈락 여부 (적격심사 하한 미달 등)
    disqualification_reason: str = ""


class PriceScoreCalculator:
    """가격점수 산출기."""

    # 적격심사 하한율
    ADEQUATE_REVIEW_FLOOR = 87.745

    def calculate(
        self,
        bid_price: int,
        budget: int,
        evaluation_method: str,
        price_weight: float,
        price_scoring_formula: dict | None = None,
        estimated_min_bid: int | None = None,
        competitor_count: int = 5,
    ) -> PriceScoreResult:
        """
        가격점수 산출.

        Args:
            bid_price: 당사 입찰가 (원)
            budget: 사업 예산 / 예정가격 (원)
            evaluation_method: 평가방식
            price_weight: 가격 배점 (예: 20점)
            price_scoring_formula: RFP에서 추출한 가격점수 산식 (없으면 표준)
            estimated_min_bid: 추정 최저입찰가 (없으면 시장 평균으로 추정)
            competitor_count: 경쟁사 수 (최저가 추정에 사용)
        """
        if bid_price <= 0 or budget <= 0:
            return PriceScoreResult(
                price_score=0, price_weight=price_weight, score_ratio=0,
                formula_used="입력값 오류", estimated_min_bid=0, bid_price=bid_price,
            )

        # 최저입찰가 추정 (제공되지 않은 경우)
        if not estimated_min_bid:
            estimated_min_bid = self._estimate_min_bid(
                budget, evaluation_method, competitor_count
            )

        # RFP 명시 산식이 있으면 사용
        if price_scoring_formula and price_scoring_formula.get("formula_type"):
            return self._calculate_rfp_formula(
                bid_price, budget, price_weight,
                estimated_min_bid, price_scoring_formula,
                evaluation_method,
            )

        # 표준 공식 적용
        return self._calculate_standard(
            bid_price, budget, evaluation_method,
            price_weight, estimated_min_bid,
        )

    def _calculate_rfp_formula(
        self,
        bid_price: int,
        budget: int,
        price_weight: float,
        estimated_min_bid: int,
        formula: dict,
        evaluation_method: str,
    ) -> PriceScoreResult:
        """RFP에 명시된 산식으로 가격점수 산출."""
        ftype = formula.get("formula_type", "")
        params = formula.get("parameters", {})
        desc = formula.get("description", "")

        if ftype == "lowest_ratio":
            # 가격점수 = 배점 × (최저입찰가 / 당사입찰가)
            if bid_price > 0:
                score = price_weight * (estimated_min_bid / bid_price)
            else:
                score = 0
            formula_desc = f"RFP 명시: {desc}" if desc else "RFP 명시: 가격배점 × (최저입찰가/입찰가)"

        elif ftype == "budget_ratio":
            # 가격점수 = 배점 × (예정가격 / 입찰가) 또는 유사 변형
            base = params.get("base_price", budget)
            score = price_weight * (base / bid_price) if bid_price > 0 else 0
            score = min(score, price_weight)  # 만점 초과 방지
            formula_desc = f"RFP 명시: {desc}" if desc else "RFP 명시: 가격배점 × (예정가격/입찰가)"

        elif ftype == "fixed_rate":
            # 고정 비율 적용 (예: 예정가격의 X% 이내이면 만점)
            threshold = params.get("threshold_ratio", 1.0)
            ratio = bid_price / budget
            if ratio <= threshold:
                score = price_weight
            else:
                score = price_weight * (threshold / ratio)
            formula_desc = f"RFP 명시: {desc}" if desc else f"RFP 명시: 예정가격의 {threshold*100:.0f}% 이내 만점"

        elif ftype == "custom":
            # 커스텀 산식은 lowest_ratio로 폴백
            score = price_weight * (estimated_min_bid / bid_price) if bid_price > 0 else 0
            formula_desc = f"RFP 명시(custom → lowest_ratio 근사): {desc}"

        else:
            return self._calculate_standard(
                bid_price, budget, evaluation_method,
                price_weight, estimated_min_bid,
            )

        score = round(min(score, price_weight), 2)  # 만점 초과 방지

        # 적격심사 탈락 체크
        is_disq, disq_reason = self._check_disqualification(bid_price, budget, evaluation_method)

        return PriceScoreResult(
            price_score=score,
            price_weight=price_weight,
            score_ratio=round(score / price_weight, 4) if price_weight > 0 else 0,
            formula_used=formula_desc,
            estimated_min_bid=estimated_min_bid,
            bid_price=bid_price,
            is_disqualified=is_disq,
            disqualification_reason=disq_reason,
        )

    def _calculate_standard(
        self,
        bid_price: int,
        budget: int,
        evaluation_method: str,
        price_weight: float,
        estimated_min_bid: int,
    ) -> PriceScoreResult:
        """평가방식별 표준 공식으로 가격점수 산출."""

        is_disq, disq_reason = self._check_disqualification(bid_price, budget, evaluation_method)

        method = evaluation_method.strip()

        if "적격" in method:
            # 적격심사: 가격점수 개념 없음, pass/fail + 최저가 순위
            # 시뮬레이션에서는 "순위 점수"로 근사: 최저가에 가까울수록 높은 점수
            if is_disq:
                score = 0
            elif bid_price <= estimated_min_bid:
                score = price_weight  # 최저가이면 만점
            else:
                score = price_weight * (estimated_min_bid / bid_price)
            formula_desc = f"적격심사 표준: 하한 {self.ADEQUATE_REVIEW_FLOOR}% 이상 + 최저가 순위"

        elif "최저" in method:
            # 최저가: 가격점수 = 배점 × (최저입찰가 / 입찰가)
            score = price_weight * (estimated_min_bid / bid_price) if bid_price > 0 else 0
            formula_desc = "최저가 표준: 가격배점 × (최저입찰가/입찰가)"

        elif "수의" in method or "협상" in method:
            # 수의계약/협상: 가격점수 = 배점 × (예정가격 / 입찰가)
            score = price_weight * (budget / bid_price) if bid_price > 0 else 0
            score = min(score, price_weight)
            formula_desc = "협상/수의 표준: 가격배점 × (예정가격/입찰가), 만점 상한"

        else:
            # 종합심사 (기본): 가격점수 = 배점 × (최저입찰가 / 입찰가)
            score = price_weight * (estimated_min_bid / bid_price) if bid_price > 0 else 0
            formula_desc = "종합심사 표준: 가격배점 × (최저입찰가/입찰가)"

        score = round(min(score, price_weight), 2)

        return PriceScoreResult(
            price_score=score,
            price_weight=price_weight,
            score_ratio=round(score / price_weight, 4) if price_weight > 0 else 0,
            formula_used=formula_desc,
            estimated_min_bid=estimated_min_bid,
            bid_price=bid_price,
            is_disqualified=is_disq,
            disqualification_reason=disq_reason,
        )

    def _estimate_min_bid(
        self, budget: int, evaluation_method: str, competitor_count: int,
    ) -> int:
        """시장 데이터 없을 때 최저입찰가 추정.

        경쟁사가 많을수록 최저가가 낮아지는 경향 반영.
        """
        method = evaluation_method.strip()

        if "적격" in method:
            # 적격심사: 87.745% 바로 위에 몰림
            base_ratio = 0.878 + 0.001 * min(competitor_count, 5)
        elif "최저" in method:
            # 최저가: 더 공격적
            base_ratio = 0.85 - 0.005 * min(competitor_count, 10)
        elif "수의" in method:
            base_ratio = 0.93
        else:
            # 종합심사: 경쟁사 수에 따라 85~90%
            base_ratio = 0.90 - 0.008 * min(competitor_count, 8)

        base_ratio = max(0.70, min(base_ratio, 0.98))
        return int(budget * base_ratio)

    def _check_disqualification(
        self, bid_price: int, budget: int, evaluation_method: str,
    ) -> tuple[bool, str]:
        """탈락 조건 체크."""
        ratio = (bid_price / budget * 100) if budget > 0 else 0

        if "적격" in evaluation_method and ratio < self.ADEQUATE_REVIEW_FLOOR:
            return True, f"적격심사 하한 미달: {ratio:.2f}% < {self.ADEQUATE_REVIEW_FLOOR}%"

        return False, ""

    def simulate_score_table(
        self,
        budget: int,
        evaluation_method: str,
        price_weight: float,
        tech_score: float,
        tech_weight: float,
        price_scoring_formula: dict | None = None,
        competitor_count: int = 5,
        bid_ratios: list[float] | None = None,
    ) -> list[dict]:
        """입찰가별 가격점수·총점 시뮬레이션 테이블 생성.

        Args:
            tech_score: 예상 기술점수 (예: 75점)
            tech_weight: 기술 배점 (예: 90점)
            bid_ratios: 시뮬레이션할 낙찰률 목록 (%). 없으면 자동 생성.

        Returns:
            [{bid_ratio, bid_price, price_score, total_score, rank_note, ...}]
        """
        if not bid_ratios:
            # 70% ~ 98%, 2% 간격
            bid_ratios = [r / 10 for r in range(700, 990, 20)]

        estimated_min_bid = self._estimate_min_bid(budget, evaluation_method, competitor_count)
        results = []

        for ratio in bid_ratios:
            bid_price = int(budget * ratio / 100)
            ps = self.calculate(
                bid_price=bid_price,
                budget=budget,
                evaluation_method=evaluation_method,
                price_weight=price_weight,
                price_scoring_formula=price_scoring_formula,
                estimated_min_bid=estimated_min_bid,
                competitor_count=competitor_count,
            )

            total_score = tech_score + ps.price_score
            price_gain_per_point = 0
            if ps.price_score > 0 and price_weight > 0:
                # 가격점수 1점당 입찰가 변동폭
                next_bid = int(budget * (ratio - 1) / 100) if ratio > 71 else bid_price
                next_ps = self.calculate(
                    bid_price=next_bid, budget=budget,
                    evaluation_method=evaluation_method,
                    price_weight=price_weight,
                    price_scoring_formula=price_scoring_formula,
                    estimated_min_bid=estimated_min_bid,
                    competitor_count=competitor_count,
                )
                diff = next_ps.price_score - ps.price_score
                if diff > 0:
                    price_gain_per_point = int((bid_price - next_bid) / diff)

            results.append({
                "bid_ratio": ratio,
                "bid_price": bid_price,
                "bid_price_fmt": f"{bid_price:,}원",
                "price_score": ps.price_score,
                "price_weight": ps.price_weight,
                "tech_score": tech_score,
                "tech_weight": tech_weight,
                "total_score": round(total_score, 2),
                "total_weight": tech_weight + price_weight,
                "score_ratio": ps.score_ratio,
                "formula_used": ps.formula_used,
                "is_disqualified": ps.is_disqualified,
                "disqualification_reason": ps.disqualification_reason,
                "estimated_min_bid": estimated_min_bid,
                "price_gain_per_point": price_gain_per_point,
            })

        return results
