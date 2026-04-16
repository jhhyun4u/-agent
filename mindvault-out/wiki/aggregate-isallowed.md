# _aggregate & is_allowed
Cohesion: 0.18 | Nodes: 11

## Key Nodes
- **_aggregate** (C:\project\tenopa proposer\app\api\routes_stats.py) -- 12 connections
  - -> calls -> [[unresolvedreflen]]
  - -> calls -> [[unresolvedrefsum]]
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefdefaultdict]]
  - -> calls -> [[unresolvedrefagencystat]]
  - -> calls -> [[unresolvedrefcalcrate]]
  - -> calls -> [[unresolvedrefsorted]]
  - -> calls -> [[unresolvedrefitems]]
  - -> calls -> [[unresolvedrefmonthstat]]
  - -> calls -> [[unresolvedrefwinrateresponse]]
  - -> calls -> [[unresolvedrefoverallstat]]
  - <- contains <- [[routesstats]]
- **is_allowed** (C:\project\tenopa proposer\app\api\routes_vault_chat.py) -- 5 connections
  - -> calls -> [[unresolvedrefnow]]
  - -> calls -> [[unresolvedreftimedelta]]
  - -> calls -> [[unresolvedreflen]]
  - -> calls -> [[unresolvedrefappend]]
  - <- contains <- [[ratelimiter]]
- **__unresolved__::ref::defaultdict** () -- 3 connections
  - <- calls <- [[aggregate]]
  - <- calls <- [[init]]
  - <- calls <- [[importfromexcel]]
- **RateLimiter** (C:\project\tenopa proposer\app\api\routes_vault_chat.py) -- 3 connections
  - -> contains -> [[init]]
  - -> contains -> [[isallowed]]
  - <- contains <- [[routesvaultchat]]
- **__init__** (C:\project\tenopa proposer\app\api\routes_vault_chat.py) -- 3 connections
  - -> calls -> [[unresolvedrefdefaultdict]]
  - -> calls -> [[unresolvedreflock]]
  - <- contains <- [[ratelimiter]]
- **__unresolved__::ref::_calc_rate** () -- 1 connections
  - <- calls <- [[aggregate]]
- **__unresolved__::ref::agencystat** () -- 1 connections
  - <- calls <- [[aggregate]]
- **__unresolved__::ref::lock** () -- 1 connections
  - <- calls <- [[init]]
- **__unresolved__::ref::monthstat** () -- 1 connections
  - <- calls <- [[aggregate]]
- **__unresolved__::ref::overallstat** () -- 1 connections
  - <- calls <- [[aggregate]]
- **__unresolved__::ref::winrateresponse** () -- 1 connections
  - <- calls <- [[aggregate]]

## Internal Relationships
- _aggregate -> calls -> __unresolved__::ref::defaultdict [EXTRACTED]
- _aggregate -> calls -> __unresolved__::ref::agencystat [EXTRACTED]
- _aggregate -> calls -> __unresolved__::ref::_calc_rate [EXTRACTED]
- _aggregate -> calls -> __unresolved__::ref::monthstat [EXTRACTED]
- _aggregate -> calls -> __unresolved__::ref::winrateresponse [EXTRACTED]
- _aggregate -> calls -> __unresolved__::ref::overallstat [EXTRACTED]
- RateLimiter -> contains -> __init__ [EXTRACTED]
- RateLimiter -> contains -> is_allowed [EXTRACTED]
- __init__ -> calls -> __unresolved__::ref::defaultdict [EXTRACTED]
- __init__ -> calls -> __unresolved__::ref::lock [EXTRACTED]

## Cross-Community Connections
- _aggregate -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedrefexecute]])
- _aggregate -> calls -> __unresolved__::ref::sum (-> [[unresolvedrefget-unresolvedrefexecute]])
- _aggregate -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedrefexecute]])
- _aggregate -> calls -> __unresolved__::ref::sorted (-> [[unresolvedrefget-unresolvedrefexecute]])
- _aggregate -> calls -> __unresolved__::ref::items (-> [[unresolvedrefget-unresolvedrefexecute]])
- is_allowed -> calls -> __unresolved__::ref::now (-> [[unresolvedrefget-unresolvedrefexecute]])
- is_allowed -> calls -> __unresolved__::ref::timedelta (-> [[unresolvedrefget-unresolvedrefexecute]])
- is_allowed -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedrefexecute]])
- is_allowed -> calls -> __unresolved__::ref::append (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 _aggregate, is_allowed, __unresolved__::ref::defaultdict를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 routes_stats.py, routes_vault_chat.py이다.

### Key Facts
- def _aggregate(records: list) -> WinRateResponse: """레코드 목록에서 전체·기관별·월별 통계 계산""" total = len(records) won_total = sum(1 for r in records if r.get("win_result") == "won")
- class RateLimiter: """Simple in-memory rate limiter for API endpoints""" def __init__(self, max_requests: int = 30, window_seconds: int = 60): self.max_requests = max_requests self.window_seconds = window_seconds self.requests: dict = defaultdict(list)  # user_id -> list of timestamps…
- class RateLimiter: """Simple in-memory rate limiter for API endpoints""" def __init__(self, max_requests: int = 30, window_seconds: int = 60): self.max_requests = max_requests self.window_seconds = window_seconds self.requests: dict = defaultdict(list)  # user_id -> list of timestamps…
- class RateLimiter: """Simple in-memory rate limiter for API endpoints""" def __init__(self, max_requests: int = 30, window_seconds: int = 60): self.max_requests = max_requests self.window_seconds = window_seconds self.requests: dict = defaultdict(list)  # user_id -> list of timestamps…
