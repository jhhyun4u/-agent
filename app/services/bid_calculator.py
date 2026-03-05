from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
import re

SW_LABOR_RATES = {
    '\uae30\uc220\uc0ac':     8_940_000,
    '\ud2b9\uae09':       8_120_000,
    '\uace0\uae09':       6_720_000,
    '\uc911\uae09':       5_170_000,
    '\ucd08\uae09':       3_510_000,
    '\uace0\uae09\uae30\ub2a5\uc0ac': 4_630_000,
    '\uc911\uae09\uae30\ub2a5\uc0ac': 3_720_000,
    '\ucd08\uae09\uae30\ub2a5\uc0ac': 2_830_000,
}

ENG_LABOR_RATES = {
    '\uae30\uc220\uc0ac': 9_120_000,
    '\ud2b9\uae09':   7_890_000,
    '\uace0\uae09':   6_450_000,
    '\uc911\uae09':   5_020_000,
    '\ucd08\uae09':   3_380_000,
}

ROLE_GRADE_MAP = {
    'PM': '\ud2b9\uae09', 'PL': '\uace0\uae09', '\ud300\uc7a5': '\ud2b9\uae09',
    '\uc218\uc11d': '\ud2b9\uae09', '\uccb4\uc784': '\uace0\uae09', '\uc120\uc784': '\uc911\uae09', '\uc8fc\uc784': '\uc911\uae09',
}

class ProcurementMethod(str, Enum):
    LOWEST_PRICE    = '\ucd5c\uc800\uac00'
    ADEQUATE_REVIEW = '\uc801\uaca9\uc2ec\uc0ac'
    COMPREHENSIVE   = '\uc885\ud569\ud3c9\uac00'
    NEGOTIATED      = '\uc218\uc758\uacc4\uc57d'

@dataclass
class PersonnelInput:
    role: str
    grade: str
    person_months: float
    labor_type: str = 'SW'

@dataclass
class CostBreakdown:
    direct_labor:     int
    indirect_cost:    int
    technical_fee:    int
    subtotal:         int
    vat:              int
    total_cost:       int
    personnel_detail: list = field(default_factory=list)

@dataclass
class BidResult:
    cost_breakdown:                CostBreakdown
    budget:                        Optional[int]
    estimated_price:               Optional[int]
    procurement_method:            ProcurementMethod
    recommended_bid:               int
    recommended_ratio:             float
    bid_range_min:                 int
    bid_range_max:                 int
    strategy_summary:              str
    price_competitiveness_message: str
    win_probability_note:          str

def _fmt(amount: int) -> str:
    if amount >= 100_000_000:
        return f"{amount/100_000_000:.1f}" + '\uc5b5\uc6d0'
    elif amount >= 10_000:
        return f"{amount/10_000:,.0f}" + '\ub9cc\uc6d0'
    return f"{amount:,}" + '\uc6d0'

def parse_budget_string(s: Optional[str]) -> Optional[int]:
    if not s:
        return None
    s = s.replace(",", "").replace(" ", "")
    for pat, mul in [
        (r"([\d.]+)\uc5b5([\d.]+)?\ub9cc?\uc6d0?", None),
        (r"([\d.]+)\uc5b5\uc6d0?", 100_000_000),
        (r"([\d.]+)\uc2dc\ub9cc\uc6d0?", 10_000_000),
        (r"([\d.]+)\ub9cc\uc6d0?", 10_000),
        (r"(\d+)$", 1),
    ]:
        m = re.match(pat, s)
        if m:
            if mul is None:
                return int(float(m.group(1))*100_000_000 + (float(m.group(2))*10_000_000 if m.group(2) else 0))
            return int(float(m.group(1)) * mul)
    return None

class BidCalculator:
    INDIRECT_RATE         = 1.10
    TECH_FEE_RATE         = 0.22
    VAT_RATE              = 0.10
    ADEQUATE_REVIEW_FLOOR = 0.87745

    def get_monthly_rate(self, grade: str, labor_type: str = 'SW') -> int:
        db = SW_LABOR_RATES if labor_type == 'SW' else ENG_LABOR_RATES
        return db.get(ROLE_GRADE_MAP.get(grade, grade), db.get('\uc911\uae09', 5_170_000))

    def calculate_cost(self, personnel: list) -> CostBreakdown:
        detail, total_labor = [], 0
        for p in personnel:
            rate = self.get_monthly_rate(p.grade, p.labor_type)
            amt  = int(rate * p.person_months)
            total_labor += amt
            detail.append({'role': p.role, 'grade': p.grade,
                           'monthly_rate': rate, 'person_months': p.person_months,
                           'amount': amt, 'amount_fmt': _fmt(amt)})
        indirect = int(total_labor * self.INDIRECT_RATE)
        tech     = int((total_labor + indirect) * self.TECH_FEE_RATE)
        sub      = total_labor + indirect + tech
        vat      = int(sub * self.VAT_RATE)
        return CostBreakdown(total_labor, indirect, tech, sub, vat, sub + vat, detail)
    def optimize_bid(self, cost, method, budget=None, price_weight=20, competitor_count=5):
        est = int(budget * 0.96) if budget else int(cost.total_cost * 1.05)
        if not budget:
            budget = est
        LP = ProcurementMethod.LOWEST_PRICE
        AR = ProcurementMethod.ADEQUATE_REVIEW
        CP = ProcurementMethod.COMPREHENSIVE
        if method == LP:
            margin = 0.02 if competitor_count > 7 else 0.05
            rec    = max(int(est * (1 - margin)), cost.total_cost)
            lo, hi = cost.total_cost, est
            strat  = ('\ucd5c\uc800\uac00: \uc6d0\uac00 ' + _fmt(cost.total_cost) +
                      ' \ud655\ubcf4 \ud6c4 \uc608\uc815\uac00\uaca9 \ub300\ube44 ' + str(int(margin*100)) + '% \ud560\uc778 \uc785\uc0f0 ' + _fmt(rec) +
                      '. \uacbd\uc7c1\uc0ac ' + str(competitor_count) + '\uac1c\uc0ac \ub300\ube44 \ucd5c\uc800\uac00 \uc120\uc810.')
            msg    = '\ub2f9\uc0ac \uc785\uc0f0\uac00\ub294 \uc6d0\uac00 \ud6a8\uc728\ud654\ub85c \uc0b0\ucd9c\ub41c \uacbd\uc7c1\ub825 \uc788\ub294 \uac00\uaca9\uc73c\ub85c, \ubc1c\uc8fc\uccab\uc758 \uc608\uc0b0 \uc808\uac10\uc5d0 \uae30\uc5ec\ud569\ub2c8\ub2e4.'
            note   = '\uacbd\uc7c1\uc0ac \ucd5c\uc800\uac00 \ud655\ubcf4 \uc2dc \ub099\ucc30 \ud655\ub960 \ub192\uc74c'
        elif method == AR:
            floor = int(est * self.ADEQUATE_REVIEW_FLOOR)
            lo    = max(floor, cost.total_cost)
            hi    = est
            rec   = max(int(floor * 1.003), cost.total_cost)
            strat = ('\uc801\uaca9\uc2ec\uc0ac: \ud558\ud55c\uc120 ' + _fmt(floor) +
                     '(87.745%) \ubc14\ub85c \uc704 ' + _fmt(rec) + '\uc73c\ub85c \uc785\uc0f0. \ud0c8\ub77d \ub9ac\uc2a4\ud06c \ucd5c\uc18c\ud654.')
            msg   = '\uc801\uaca9\uc2ec\uc0ac \uae30\uc900\uc744 \ucda9\uc871\ud558\ub294 \uc218\uc900\uc5d0\uc11c \ucd5c\uc801\ud654\ub41c \uc6d0\uac00 \uad6c\uc870\ub85c \uc608\uc0b0 \ud6a8\uc728\uc131\uc744 \ubcf4\uc7a5\ud569\ub2c8\ub2e4.'
            note  = '\uc801\uaca9\uc2ec\uc0ac \ud558\ud55c \ud1b5\uacfc + \ucd5c\uc800\uac00 \uad6c\uac04 \uc9d1\uc911 -- \ub099\ucc30 \ud655\ub960 \ucd5c\uace0'
        elif method == CP:
            ratio = 0.91 if price_weight <= 20 else (0.88 if price_weight <= 30 else 0.855)
            rec   = max(int(est * ratio), cost.total_cost)
            lo, hi = int(est * 0.85), int(est * 0.95)
            strat = ('\uc885\ud569\ud3c9\uac00(\uac00\uaca9 ' + str(price_weight) + '\uc810): \uae30\uc220 \uc6b0\uc704 \ud6c4 \uc608\uc815\uac00\uaca9\uc758 ' +
                     str(int(ratio*100)) + '%(' + _fmt(rec) + ')\ub85c \uc785\uc0f0. \uae30\uc220-\uac00\uaca9 \ucd1d\uc810 \ucd5c\ub300\ud654.')
            msg   = '\uae30\uc220 \uc5ed\ub7c9 \ub300\ube44 \ud569\ub9ac\uc801\uc778 \uac00\uaca9\uc744 \uc81c\uc548\ud558\uba70, \ucd1d\uc810 \uae30\uc900 \ucd5c\uace0 \uacbd\uc7c1\ub825\uc744 \ubcf4\uc720\ud569\ub2c8\ub2e4.'
            note  = '\uae30\uc220\uc810\uc218 \uc0c1\uc704 + \uac00\uaca9 \ubc30\uc810 \uad6c\uac04 \ucd5c\uc801\ud654 -> \ucd1d\uc810 \uacbd\uc7c1\ub825'
        else:
            rec   = max(int(est * 0.95), cost.total_cost)
            lo, hi = cost.total_cost, est
            strat = '\uc218\uc758\uacc4\uc57d: \uc6d0\uac00 \uae30\ubc18 \ud611\uc0c1 \ubaa9\ud45c\uac00 \uc81c\uc2dc.'
            msg   = '\ud569\ub9ac\uc801 \uc6d0\uac00 \uad6c\uc870\ub97c \ubc14\ud0d5\uc73c\ub85c \uc0c1\ud638 \uc774\uc775\uc774 \ub418\ub294 \uacc4\uc57d\uac00\ub97c \uc81c\uc548\ud569\ub2c8\ub2e4.'
            note  = '\uae30\uc220\ub825 \uc911\uc2ec \ud611\uc0c1'
        return BidResult(cost, budget, est, method, rec, round(rec/budget*100, 1), lo, hi, strat, msg, note)

    def to_dict(self, r) -> dict:
        c = r.cost_breakdown
        return {
            'cost_breakdown': {
                'direct_labor': c.direct_labor,
                'direct_labor_fmt': _fmt(c.direct_labor),
                'indirect_cost': c.indirect_cost,
                'indirect_fmt': _fmt(c.indirect_cost),
                'technical_fee': c.technical_fee,
                'tech_fee_fmt': _fmt(c.technical_fee),
                'subtotal': c.subtotal,
                'subtotal_fmt': _fmt(c.subtotal),
                'vat': c.vat,
                'vat_fmt': _fmt(c.vat),
                'total_cost': c.total_cost,
                'total_cost_fmt': _fmt(c.total_cost),
                'personnel_detail': c.personnel_detail,
            },
            'budget': r.budget,
            'budget_fmt': _fmt(r.budget) if r.budget else '\ubbf8\uc815',
            'estimated_price': r.estimated_price,
            'estimated_price_fmt': _fmt(r.estimated_price),
            'procurement_method': r.procurement_method.value,
            'recommended_bid': r.recommended_bid,
            'recommended_bid_fmt': _fmt(r.recommended_bid),
            'recommended_ratio': r.recommended_ratio,
            'bid_range_min': r.bid_range_min,
            'bid_range_min_fmt': _fmt(r.bid_range_min),
            'bid_range_max': r.bid_range_max,
            'bid_range_max_fmt': _fmt(r.bid_range_max),
            'strategy_summary': r.strategy_summary,
            'price_competitiveness_message': r.price_competitiveness_message,
            'win_probability_note': r.win_probability_note,
        }
