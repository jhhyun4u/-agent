# quick_estimate & ensure_market_data
Cohesion: 0.22 | Nodes: 9

## Key Nodes
- **quick_estimate** (C:\project\tenopa proposer\app\services\bidding\pricing\engine.py) -- 8 connections
  - -> calls -> [[unresolvedrefcomputebudgettier]]
  - -> calls -> [[unresolvedrefcomputerecommendedratio]]
  - -> calls -> [[unresolvedrefcalculate]]
  - -> calls -> [[unresolvedrefgetmarketcontext]]
  - -> calls -> [[unresolvedrefquickestimateresult]]
  - -> calls -> [[unresolvedrefround]]
  - -> calls -> [[unresolvedrefint]]
  - <- contains <- [[pricingengine]]
- **ensure_market_data** (C:\project\tenopa proposer\app\services\bidding\submission\market_research.py) -- 7 connections
  - -> calls -> [[unresolvedrefcomputebudgettier]]
  - -> calls -> [[unresolvedrefcountcomparable]]
  - -> calls -> [[unresolvedrefinfo]]
  - -> calls -> [[unresolvedrefbuildsearchkeywords]]
  - -> calls -> [[unresolvedrefcrawlbidresults]]
  - -> calls -> [[unresolvedrefwarning]]
  - <- contains <- [[marketresearch]]
- **__unresolved__::ref::_compute_budget_tier** () -- 4 connections
  - <- calls <- [[simulate]]
  - <- calls <- [[quickestimate]]
  - <- calls <- [[ensuremarketdata]]
  - <- calls <- [[crawlbidresults]]
- **__unresolved__::ref::_compute_recommended_ratio** () -- 2 connections
  - <- calls <- [[simulate]]
  - <- calls <- [[quickestimate]]
- **__unresolved__::ref::_get_market_context** () -- 2 connections
  - <- calls <- [[simulate]]
  - <- calls <- [[quickestimate]]
- **__unresolved__::ref::_build_search_keywords** () -- 1 connections
  - <- calls <- [[ensuremarketdata]]
- **__unresolved__::ref::_count_comparable** () -- 1 connections
  - <- calls <- [[ensuremarketdata]]
- **__unresolved__::ref::_crawl_bid_results** () -- 1 connections
  - <- calls <- [[ensuremarketdata]]
- **__unresolved__::ref::quickestimateresult** () -- 1 connections
  - <- calls <- [[quickestimate]]

## Internal Relationships
- quick_estimate -> calls -> __unresolved__::ref::_compute_budget_tier [EXTRACTED]
- quick_estimate -> calls -> __unresolved__::ref::_compute_recommended_ratio [EXTRACTED]
- quick_estimate -> calls -> __unresolved__::ref::_get_market_context [EXTRACTED]
- quick_estimate -> calls -> __unresolved__::ref::quickestimateresult [EXTRACTED]
- ensure_market_data -> calls -> __unresolved__::ref::_compute_budget_tier [EXTRACTED]
- ensure_market_data -> calls -> __unresolved__::ref::_count_comparable [EXTRACTED]
- ensure_market_data -> calls -> __unresolved__::ref::_build_search_keywords [EXTRACTED]
- ensure_market_data -> calls -> __unresolved__::ref::_crawl_bid_results [EXTRACTED]

## Cross-Community Connections
- quick_estimate -> calls -> __unresolved__::ref::calculate (-> [[unresolvedrefget-unresolvedrefexecute]])
- quick_estimate -> calls -> __unresolved__::ref::round (-> [[unresolvedrefget-unresolvedrefexecute]])
- quick_estimate -> calls -> __unresolved__::ref::int (-> [[unresolvedrefget-unresolvedrefexecute]])
- ensure_market_data -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- ensure_market_data -> calls -> __unresolved__::ref::warning (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 quick_estimate, ensure_market_data, __unresolved__::ref::_compute_budget_tier를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 engine.py, market_research.py이다.

### Key Facts
- async def quick_estimate(self, req: QuickEstimateRequest) -> QuickEstimateResult: """경량 견적 — 원가 없이 시장 데이터 기반 추천 비율 + 확률만.""" budget_tier = _compute_budget_tier(req.budget) price_weight = 20  # 기본값
- async def ensure_market_data( domain: str, evaluation_method: str, budget: int, project_name: str = "", client_name: str = "", hot_buttons: list[str] | None = None, ) -> dict: """ 유사과제 낙찰정보가 충분한지 확인하고, 부족하면 G2B 크롤링으로 보강.
