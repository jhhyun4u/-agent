# PriceScoreCalculator & _calculate_rfp_formula
Cohesion: 0.29 | Nodes: 10

## Key Nodes
- **PriceScoreCalculator** (C:\project\tenopa proposer\-agent-master\app\services\bidding\pricing\price_score.py) -- 7 connections
  - -> contains -> [[calculate]]
  - -> contains -> [[calculaterfpformula]]
  - -> contains -> [[calculatestandard]]
  - -> contains -> [[estimateminbid]]
  - -> contains -> [[checkdisqualification]]
  - -> contains -> [[simulatescoretable]]
  - <- contains <- [[pricescore]]
- **_calculate_rfp_formula** (C:\project\tenopa proposer\-agent-master\app\services\bidding\pricing\price_score.py) -- 7 connections
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefmin]]
  - -> calls -> [[unresolvedrefcalculatestandard]]
  - -> calls -> [[unresolvedrefround]]
  - -> calls -> [[unresolvedrefcheckdisqualification]]
  - -> calls -> [[unresolvedrefpricescoreresult]]
  - <- contains <- [[pricescorecalculator]]
- **_calculate_standard** (C:\project\tenopa proposer\-agent-master\app\services\bidding\pricing\price_score.py) -- 6 connections
  - -> calls -> [[unresolvedrefcheckdisqualification]]
  - -> calls -> [[unresolvedrefstrip]]
  - -> calls -> [[unresolvedrefmin]]
  - -> calls -> [[unresolvedrefround]]
  - -> calls -> [[unresolvedrefpricescoreresult]]
  - <- contains <- [[pricescorecalculator]]
- **calculate** (C:\project\tenopa proposer\-agent-master\app\services\bidding\pricing\price_score.py) -- 6 connections
  - -> calls -> [[unresolvedrefpricescoreresult]]
  - -> calls -> [[unresolvedrefestimateminbid]]
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefcalculaterfpformula]]
  - -> calls -> [[unresolvedrefcalculatestandard]]
  - <- contains <- [[pricescorecalculator]]
- **__unresolved__::ref::pricescoreresult** () -- 3 connections
  - <- calls <- [[calculate]]
  - <- calls <- [[calculaterfpformula]]
  - <- calls <- [[calculatestandard]]
- **__unresolved__::ref::_calculate_standard** () -- 2 connections
  - <- calls <- [[calculate]]
  - <- calls <- [[calculaterfpformula]]
- **__unresolved__::ref::_check_disqualification** () -- 2 connections
  - <- calls <- [[calculaterfpformula]]
  - <- calls <- [[calculatestandard]]
- **__unresolved__::ref::_estimate_min_bid** () -- 2 connections
  - <- calls <- [[calculate]]
  - <- calls <- [[simulatescoretable]]
- **__unresolved__::ref::_calculate_rfp_formula** () -- 1 connections
  - <- calls <- [[calculate]]
- **_check_disqualification** (C:\project\tenopa proposer\-agent-master\app\services\bidding\pricing\price_score.py) -- 1 connections
  - <- contains <- [[pricescorecalculator]]

## Internal Relationships
- PriceScoreCalculator -> contains -> calculate [EXTRACTED]
- PriceScoreCalculator -> contains -> _calculate_rfp_formula [EXTRACTED]
- PriceScoreCalculator -> contains -> _calculate_standard [EXTRACTED]
- PriceScoreCalculator -> contains -> _check_disqualification [EXTRACTED]
- _calculate_rfp_formula -> calls -> __unresolved__::ref::_calculate_standard [EXTRACTED]
- _calculate_rfp_formula -> calls -> __unresolved__::ref::_check_disqualification [EXTRACTED]
- _calculate_rfp_formula -> calls -> __unresolved__::ref::pricescoreresult [EXTRACTED]
- _calculate_standard -> calls -> __unresolved__::ref::_check_disqualification [EXTRACTED]
- _calculate_standard -> calls -> __unresolved__::ref::pricescoreresult [EXTRACTED]
- calculate -> calls -> __unresolved__::ref::pricescoreresult [EXTRACTED]
- calculate -> calls -> __unresolved__::ref::_estimate_min_bid [EXTRACTED]
- calculate -> calls -> __unresolved__::ref::_calculate_rfp_formula [EXTRACTED]
- calculate -> calls -> __unresolved__::ref::_calculate_standard [EXTRACTED]

## Cross-Community Connections
- PriceScoreCalculator -> contains -> _estimate_min_bid (-> [[unresolvedrefget-unresolvedreflen]])
- PriceScoreCalculator -> contains -> simulate_score_table (-> [[unresolvedrefget-unresolvedreflen]])
- _calculate_rfp_formula -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- _calculate_rfp_formula -> calls -> __unresolved__::ref::min (-> [[unresolvedrefget-unresolvedreflen]])
- _calculate_rfp_formula -> calls -> __unresolved__::ref::round (-> [[unresolvedrefget-unresolvedreflen]])
- _calculate_standard -> calls -> __unresolved__::ref::strip (-> [[unresolvedrefget-unresolvedreflen]])
- _calculate_standard -> calls -> __unresolved__::ref::min (-> [[unresolvedrefget-unresolvedreflen]])
- _calculate_standard -> calls -> __unresolved__::ref::round (-> [[unresolvedrefget-unresolvedreflen]])
- calculate -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 PriceScoreCalculator, _calculate_rfp_formula, _calculate_standard를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 price_score.py이다.

### Key Facts
- class PriceScoreCalculator: """가격점수 산출기."""
- RFP 명시 산식이 있으면 사용 if price_scoring_formula and price_scoring_formula.get("formula_type"): return self._calculate_rfp_formula( bid_price, budget, price_weight, estimated_min_bid, price_scoring_formula, evaluation_method, )
- 표준 공식 적용 return self._calculate_standard( bid_price, budget, evaluation_method, price_weight, estimated_min_bid, )
- def calculate( self, bid_price: int, budget: int, evaluation_method: str, price_weight: float, price_scoring_formula: dict | None = None, estimated_min_bid: int | None = None, competitor_count: int = 5, ) -> PriceScoreResult: """ 가격점수 산출.
- 적격심사 탈락 체크 is_disq, disq_reason = self._check_disqualification(bid_price, budget, evaluation_method)
