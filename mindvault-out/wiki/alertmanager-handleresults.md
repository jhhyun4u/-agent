# AlertManager & handle_results
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **AlertManager** (C:\project\tenopa proposer\-agent-master\app\services\alert_manager.py) -- 6 connections
  - -> contains -> [[init]]
  - -> contains -> [[handleresults]]
  - -> contains -> [[logtodb]]
  - -> contains -> [[maybealert]]
  - -> contains -> [[sendteamsalert]]
  - <- contains <- [[alertmanager]]
- **handle_results** (C:\project\tenopa proposer\-agent-master\app\services\alert_manager.py) -- 3 connections
  - -> calls -> [[unresolvedreflogtodb]]
  - -> calls -> [[unresolvedrefmaybealert]]
  - <- contains <- [[alertmanager]]
- **__unresolved__::ref::_log_to_db** () -- 1 connections
  - <- calls <- [[handleresults]]
- **__unresolved__::ref::_maybe_alert** () -- 1 connections
  - <- calls <- [[handleresults]]
- **__init__** (C:\project\tenopa proposer\-agent-master\app\services\alert_manager.py) -- 1 connections
  - <- contains <- [[alertmanager]]

## Internal Relationships
- AlertManager -> contains -> __init__ [EXTRACTED]
- AlertManager -> contains -> handle_results [EXTRACTED]
- handle_results -> calls -> __unresolved__::ref::_log_to_db [EXTRACTED]
- handle_results -> calls -> __unresolved__::ref::_maybe_alert [EXTRACTED]

## Cross-Community Connections
- AlertManager -> contains -> _log_to_db (-> [[unresolvedrefget-unresolvedreflen]])
- AlertManager -> contains -> _maybe_alert (-> [[unresolvedrefget-unresolvedreflen]])
- AlertManager -> contains -> _send_teams_alert (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 AlertManager, handle_results, __unresolved__::ref::_log_to_db를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 alert_manager.py이다.

### Key Facts
- class AlertManager: """검증 결과 → 알림 + DB 로깅 + 중복 억제"""
- async def handle_results(self, results: list[HealthResult]) -> None: """결과 목록 처리: 모두 DB 로깅 + fail/fixed만 알림""" for r in results: await self._log_to_db(r) if r.status in ("fail", "fixed"): await self._maybe_alert(r)
- def __init__(self): self._recent_fails: dict[str, datetime] = {}
