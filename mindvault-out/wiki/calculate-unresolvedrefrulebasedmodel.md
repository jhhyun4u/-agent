# calculate & __unresolved__::ref::_rule_based_model
Cohesion: 0.50 | Nodes: 4

## Key Nodes
- **calculate** (C:\project\tenopa proposer\-agent-master\app\services\bidding\pricing\win_probability.py) -- 5 connections
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

## Internal Relationships
- calculate -> calls -> __unresolved__::ref::_query_comparable [EXTRACTED]
- calculate -> calls -> __unresolved__::ref::_statistical_model [EXTRACTED]
- calculate -> calls -> __unresolved__::ref::_rule_based_model [EXTRACTED]

## Cross-Community Connections
- calculate -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 calculate, __unresolved__::ref::_rule_based_model, __unresolved__::ref::_query_comparable를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 win_probability.py이다.

### Key Facts
- async def calculate( self, bid_ratio: float, domain: str, evaluation_method: str, budget_tier: str | None, tech_price_ratio: dict | None = None, competitor_count: int = 5, positioning: str | None = None, ) -> dict: """ 수주확률 계산.
