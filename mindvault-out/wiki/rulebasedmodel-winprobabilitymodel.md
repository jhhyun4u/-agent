# _rule_based_model & WinProbabilityModel
Cohesion: 0.29 | Nodes: 7

## Key Nodes
- **_rule_based_model** (C:\project\tenopa proposer\app\services\bidding\pricing\win_probability.py) -- 7 connections
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefabs]]
  - -> calls -> [[unresolvedrefexp]]
  - -> calls -> [[unresolvedrefmax]]
  - -> calls -> [[unresolvedrefmin]]
  - -> calls -> [[unresolvedrefround]]
  - <- contains <- [[winprobabilitymodel]]
- **WinProbabilityModel** (C:\project\tenopa proposer\app\services\bidding\pricing\win_probability.py) -- 5 connections
  - -> contains -> [[calculate]]
  - -> contains -> [[rulebasedmodel]]
  - -> contains -> [[statisticalmodel]]
  - -> contains -> [[querycomparable]]
  - <- contains <- [[winprobability]]
- **calculate** (C:\project\tenopa proposer\app\services\bidding\pricing\win_probability.py) -- 5 connections
  - -> calls -> [[unresolvedrefquerycomparable]]
  - -> calls -> [[unresolvedreflen]]
  - -> calls -> [[unresolvedrefstatisticalmodel]]
  - -> calls -> [[unresolvedrefrulebasedmodel]]
  - <- contains <- [[winprobabilitymodel]]
- **__unresolved__::ref::_rule_based_model** () -- 2 connections
  - <- calls <- [[calculate]]
  - <- calls <- [[statisticalmodel]]
- **__unresolved__::ref::_query_comparable** () -- 1 connections
  - <- calls <- [[calculate]]
- **__unresolved__::ref::_statistical_model** () -- 1 connections
  - <- calls <- [[calculate]]
- **__unresolved__::ref::exp** () -- 1 connections
  - <- calls <- [[rulebasedmodel]]

## Internal Relationships
- WinProbabilityModel -> contains -> calculate [EXTRACTED]
- WinProbabilityModel -> contains -> _rule_based_model [EXTRACTED]
- _rule_based_model -> calls -> __unresolved__::ref::exp [EXTRACTED]
- calculate -> calls -> __unresolved__::ref::_query_comparable [EXTRACTED]
- calculate -> calls -> __unresolved__::ref::_statistical_model [EXTRACTED]
- calculate -> calls -> __unresolved__::ref::_rule_based_model [EXTRACTED]

## Cross-Community Connections
- WinProbabilityModel -> contains -> _statistical_model (-> [[unresolvedrefget-unresolvedrefexecute]])
- WinProbabilityModel -> contains -> _query_comparable (-> [[unresolvedrefget-unresolvedrefexecute]])
- _rule_based_model -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedrefexecute]])
- _rule_based_model -> calls -> __unresolved__::ref::abs (-> [[unresolvedrefreact-unresolvedreflibapi]])
- _rule_based_model -> calls -> __unresolved__::ref::max (-> [[unresolvedrefget-unresolvedrefexecute]])
- _rule_based_model -> calls -> __unresolved__::ref::min (-> [[unresolvedrefget-unresolvedrefexecute]])
- _rule_based_model -> calls -> __unresolved__::ref::round (-> [[unresolvedrefget-unresolvedrefexecute]])
- calculate -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 _rule_based_model, WinProbabilityModel, calculate를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 win_probability.py이다.

### Key Facts
- if len(cases) >= self.MIN_CASES_FOR_STATS: return self._statistical_model(bid_ratio, cases, tech_price_ratio, competitor_count, positioning) else: return self._rule_based_model( bid_ratio, evaluation_method, tech_price_ratio, competitor_count, positioning, len(cases) )
- class WinProbabilityModel: """수주확률 계산 모델. 데이터 양에 따라 규칙/통계 자동 전환."""
- async def calculate( self, bid_ratio: float, domain: str, evaluation_method: str, budget_tier: str | None, tech_price_ratio: dict | None = None, competitor_count: int = 5, positioning: str | None = None, ) -> dict: """ 수주확률 계산.
