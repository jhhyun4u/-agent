# estimate & optimize_bid
Cohesion: 0.13 | Nodes: 18

## Key Nodes
- **estimate** (C:\project\tenopa proposer\app\services\bidding\pricing\cost_estimator.py) -- 9 connections
  - -> calls -> [[unresolvedrefcostbreakdowndetail]]
  - -> calls -> [[unresolvedrefnow]]
  - -> calls -> [[unresolvedrefloaddbrates]]
  - -> calls -> [[unresolvedrefgetrate]]
  - -> calls -> [[unresolvedrefint]]
  - -> calls -> [[unresolvedrefappend]]
  - -> calls -> [[unresolvedrefpersonnelcostdetail]]
  - -> calls -> [[unresolvedreffmt]]
  - <- contains <- [[enhancedcostestimator]]
- **optimize_bid** (C:\project\tenopa proposer\app\services\bidding\calculator.py) -- 7 connections
  - -> calls -> [[unresolvedrefint]]
  - -> calls -> [[unresolvedrefmax]]
  - -> calls -> [[unresolvedreffmt]]
  - -> calls -> [[unresolvedrefstr]]
  - -> calls -> [[unresolvedrefbidresult]]
  - -> calls -> [[unresolvedrefround]]
  - <- contains <- [[bidcalculator]]
- **calculate_cost** (C:\project\tenopa proposer\app\services\bidding\calculator.py) -- 6 connections
  - -> calls -> [[unresolvedrefgetmonthlyrate]]
  - -> calls -> [[unresolvedrefint]]
  - -> calls -> [[unresolvedrefappend]]
  - -> calls -> [[unresolvedreffmt]]
  - -> calls -> [[unresolvedrefcostbreakdown]]
  - <- contains <- [[bidcalculator]]
- **BidCalculator** (C:\project\tenopa proposer\app\services\bidding\calculator.py) -- 5 connections
  - -> contains -> [[getmonthlyrate]]
  - -> contains -> [[calculatecost]]
  - -> contains -> [[optimizebid]]
  - -> contains -> [[todict]]
  - <- contains <- [[calculator]]
- **EnhancedCostEstimator** (C:\project\tenopa proposer\app\services\bidding\pricing\cost_estimator.py) -- 5 connections
  - -> contains -> [[init]]
  - -> contains -> [[estimate]]
  - -> contains -> [[loaddbrates]]
  - -> contains -> [[getrate]]
  - <- contains <- [[costestimator]]
- **__unresolved__::ref::_fmt** () -- 4 connections
  - <- calls <- [[calculatecost]]
  - <- calls <- [[optimizebid]]
  - <- calls <- [[todict]]
  - <- calls <- [[estimate]]
- **__unresolved__::ref::bidcalculator** () -- 2 connections
  - <- calls <- [[phase3plan]]
  - <- calls <- [[init]]
- **__unresolved__::ref::get_monthly_rate** () -- 2 connections
  - <- calls <- [[calculatecost]]
  - <- calls <- [[getrate]]
- **get_monthly_rate** (C:\project\tenopa proposer\app\services\bidding\calculator.py) -- 2 connections
  - -> calls -> [[unresolvedrefget]]
  - <- contains <- [[bidcalculator]]
- **to_dict** (C:\project\tenopa proposer\app\services\bidding\calculator.py) -- 2 connections
  - -> calls -> [[unresolvedreffmt]]
  - <- contains <- [[bidcalculator]]
- **__init__** (C:\project\tenopa proposer\app\services\bidding\pricing\cost_estimator.py) -- 2 connections
  - -> calls -> [[unresolvedrefbidcalculator]]
  - <- contains <- [[enhancedcostestimator]]
- **_get_rate** (C:\project\tenopa proposer\app\services\bidding\pricing\cost_estimator.py) -- 2 connections
  - -> calls -> [[unresolvedrefgetmonthlyrate]]
  - <- contains <- [[enhancedcostestimator]]
- **__unresolved__::ref::_get_rate** () -- 1 connections
  - <- calls <- [[estimate]]
- **__unresolved__::ref::_load_db_rates** () -- 1 connections
  - <- calls <- [[estimate]]
- **__unresolved__::ref::bidresult** () -- 1 connections
  - <- calls <- [[optimizebid]]
- **__unresolved__::ref::costbreakdown** () -- 1 connections
  - <- calls <- [[calculatecost]]
- **__unresolved__::ref::costbreakdowndetail** () -- 1 connections
  - <- calls <- [[estimate]]
- **__unresolved__::ref::personnelcostdetail** () -- 1 connections
  - <- calls <- [[estimate]]

## Internal Relationships
- BidCalculator -> contains -> get_monthly_rate [EXTRACTED]
- BidCalculator -> contains -> calculate_cost [EXTRACTED]
- BidCalculator -> contains -> optimize_bid [EXTRACTED]
- BidCalculator -> contains -> to_dict [EXTRACTED]
- calculate_cost -> calls -> __unresolved__::ref::get_monthly_rate [EXTRACTED]
- calculate_cost -> calls -> __unresolved__::ref::_fmt [EXTRACTED]
- calculate_cost -> calls -> __unresolved__::ref::costbreakdown [EXTRACTED]
- optimize_bid -> calls -> __unresolved__::ref::_fmt [EXTRACTED]
- optimize_bid -> calls -> __unresolved__::ref::bidresult [EXTRACTED]
- to_dict -> calls -> __unresolved__::ref::_fmt [EXTRACTED]
- EnhancedCostEstimator -> contains -> __init__ [EXTRACTED]
- EnhancedCostEstimator -> contains -> estimate [EXTRACTED]
- EnhancedCostEstimator -> contains -> _get_rate [EXTRACTED]
- __init__ -> calls -> __unresolved__::ref::bidcalculator [EXTRACTED]
- _get_rate -> calls -> __unresolved__::ref::get_monthly_rate [EXTRACTED]
- estimate -> calls -> __unresolved__::ref::costbreakdowndetail [EXTRACTED]
- estimate -> calls -> __unresolved__::ref::_load_db_rates [EXTRACTED]
- estimate -> calls -> __unresolved__::ref::_get_rate [EXTRACTED]
- estimate -> calls -> __unresolved__::ref::personnelcostdetail [EXTRACTED]
- estimate -> calls -> __unresolved__::ref::_fmt [EXTRACTED]

## Cross-Community Connections
- calculate_cost -> calls -> __unresolved__::ref::int (-> [[unresolvedrefget-unresolvedrefexecute]])
- calculate_cost -> calls -> __unresolved__::ref::append (-> [[unresolvedrefget-unresolvedrefexecute]])
- get_monthly_rate -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedrefexecute]])
- optimize_bid -> calls -> __unresolved__::ref::int (-> [[unresolvedrefget-unresolvedrefexecute]])
- optimize_bid -> calls -> __unresolved__::ref::max (-> [[unresolvedrefget-unresolvedrefexecute]])
- optimize_bid -> calls -> __unresolved__::ref::str (-> [[unresolvedrefget-unresolvedrefexecute]])
- optimize_bid -> calls -> __unresolved__::ref::round (-> [[unresolvedrefget-unresolvedrefexecute]])
- EnhancedCostEstimator -> contains -> _load_db_rates (-> [[unresolvedrefget-unresolvedrefexecute]])
- estimate -> calls -> __unresolved__::ref::now (-> [[unresolvedrefget-unresolvedrefexecute]])
- estimate -> calls -> __unresolved__::ref::int (-> [[unresolvedrefget-unresolvedrefexecute]])
- estimate -> calls -> __unresolved__::ref::append (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 estimate, optimize_bid, calculate_cost를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 calculator.py, cost_estimator.py이다.

### Key Facts
- async def estimate( self, personnel: list[PersonnelInput], cost_standard: str = "KOSA", year: int | None = None, ) -> CostBreakdownDetail: """인력 목록 → 원가 상세 계산. DB 단가 우선, 없으면 하드코딩 fallback.""" if not personnel: return CostBreakdownDetail( direct_labor=0, direct_labor_fmt="0원", indirect_cost=0,…
- H_FEE_RATE) sub      = total_labor + indirect + tech vat      = int(sub * self.VAT_RATE) return CostBreakdown(total_labor, indirect, tech, sub, vat, sub + vat, detail) def optimize_bid(self, cost, method, budget=None, price_weight=20, competitor_count=5): est = int(budget * 0.96) if budget else…
- def calculate_cost(self, personnel: list) -> CostBreakdown: detail, total_labor = [], 0 for p in personnel: rate = self.get_monthly_rate(p.grade, p.labor_type) amt  = int(rate * p.person_months) total_labor += amt detail.append({'role': p.role, 'grade': p.grade, 'monthly_rate': rate,…
- __all__ = [ "SW_LABOR_RATES", "ENG_LABOR_RATES", "ROLE_GRADE_MAP", "ProcurementMethod", "PersonnelInput", "CostBreakdown", "BidResult", "_fmt", "parse_budget_string", "BidCalculator", ]
- class EnhancedCostEstimator: """DB 기반 원가 산정기. BidCalculator를 내부 래핑."""
