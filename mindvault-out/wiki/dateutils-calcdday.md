# date_utils & calc_dday
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **date_utils** (C:\project\tenopa proposer\-agent-master\app\utils\date_utils.py) -- 6 connections
  - -> contains -> [[calcdday]]
  - -> contains -> [[calcprogress]]
  - -> contains -> [[calcbudgetrate]]
  - -> contains -> [[deadlinealertlevel]]
  - -> contains -> [[todate]]
  - -> imports -> [[unresolvedrefdatetime]]
- **calc_dday** (C:\project\tenopa proposer\-agent-master\app\utils\date_utils.py) -- 4 connections
  - -> calls -> [[unresolvedreftodate]]
  - -> calls -> [[unresolvedrefdate]]
  - -> calls -> [[unresolvedrefnow]]
  - <- contains <- [[dateutils]]
- **calc_budget_rate** (C:\project\tenopa proposer\-agent-master\app\utils\date_utils.py) -- 2 connections
  - -> calls -> [[unresolvedrefround]]
  - <- contains <- [[dateutils]]
- **calc_progress** (C:\project\tenopa proposer\-agent-master\app\utils\date_utils.py) -- 2 connections
  - -> calls -> [[unresolvedrefround]]
  - <- contains <- [[dateutils]]
- **__unresolved__::ref::_to_date** () -- 1 connections
  - <- calls <- [[calcdday]]
- **deadline_alert_level** (C:\project\tenopa proposer\-agent-master\app\utils\date_utils.py) -- 1 connections
  - <- contains <- [[dateutils]]

## Internal Relationships
- calc_dday -> calls -> __unresolved__::ref::_to_date [EXTRACTED]
- date_utils -> contains -> calc_dday [EXTRACTED]
- date_utils -> contains -> calc_progress [EXTRACTED]
- date_utils -> contains -> calc_budget_rate [EXTRACTED]
- date_utils -> contains -> deadline_alert_level [EXTRACTED]

## Cross-Community Connections
- calc_budget_rate -> calls -> __unresolved__::ref::round (-> [[unresolvedrefget-unresolvedreflen]])
- calc_dday -> calls -> __unresolved__::ref::date (-> [[unresolvedrefget-unresolvedreflen]])
- calc_dday -> calls -> __unresolved__::ref::now (-> [[unresolvedrefget-unresolvedreflen]])
- calc_progress -> calls -> __unresolved__::ref::round (-> [[unresolvedrefget-unresolvedreflen]])
- date_utils -> contains -> _to_date (-> [[unresolvedrefget-unresolvedreflen]])
- date_utils -> imports -> __unresolved__::ref::datetime (-> [[unresolvedrefbasemodel-unresolvedreflogging]])

## Context
이 커뮤니티는 date_utils, calc_dday, calc_budget_rate를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 date_utils.py이다.

### Key Facts
- def calc_dday( deadline: str | date | datetime, base: str | date | datetime | None = None, ) -> int: """마감일까지 잔여일 계산 (D-day).
- def calc_budget_rate(total: int | float, used: int | float) -> float: """예산 집행률 계산 (%).
- def calc_progress(total: int, completed: int) -> float: """진도율 계산 (%).
- def deadline_alert_level(days_left: int) -> str | None: """잔여일 기반 알림 등급 결정.
