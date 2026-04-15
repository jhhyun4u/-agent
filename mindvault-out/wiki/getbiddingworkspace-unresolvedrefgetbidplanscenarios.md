# get_bidding_workspace & __unresolved__::ref::_get_bid_plan_scenarios
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **get_bidding_workspace** (C:\project\tenopa proposer\-agent-master\app\services\bidding\submission\stream.py) -- 5 connections
  - -> calls -> [[unresolvedrefgetbidsubmissionstatus]]
  - -> calls -> [[unresolvedrefgetbidpricehistory]]
  - -> calls -> [[unresolvedrefgetbidplanscenarios]]
  - -> calls -> [[unresolvedrefgetmarkettrackingsummary]]
  - <- contains <- [[stream]]
- **__unresolved__::ref::_get_bid_plan_scenarios** () -- 1 connections
  - <- calls <- [[getbiddingworkspace]]
- **__unresolved__::ref::get_bid_price_history** () -- 1 connections
  - <- calls <- [[getbiddingworkspace]]
- **__unresolved__::ref::get_bid_submission_status** () -- 1 connections
  - <- calls <- [[getbiddingworkspace]]
- **__unresolved__::ref::get_market_tracking_summary** () -- 1 connections
  - <- calls <- [[getbiddingworkspace]]

## Internal Relationships
- get_bidding_workspace -> calls -> __unresolved__::ref::get_bid_submission_status [EXTRACTED]
- get_bidding_workspace -> calls -> __unresolved__::ref::get_bid_price_history [EXTRACTED]
- get_bidding_workspace -> calls -> __unresolved__::ref::_get_bid_plan_scenarios [EXTRACTED]
- get_bidding_workspace -> calls -> __unresolved__::ref::get_market_tracking_summary [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 get_bidding_workspace, __unresolved__::ref::_get_bid_plan_scenarios, __unresolved__::ref::get_bid_price_history를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 stream.py이다.

### Key Facts
- async def get_bidding_workspace(proposal_id: str) -> dict: """통합 비딩 현황 — 확정가, 시나리오, 이력, 투찰 상태를 하나로.""" from app.services.bidding.submission.handoff import ( get_bid_price_history, get_bid_submission_status, )
