# _check_resources & __unresolved__::ref::cpu_percent
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **_check_resources** (C:\project\tenopa proposer\-agent-master\app\services\health_checker.py) -- 4 connections
  - -> calls -> [[unresolvedrefhealthresult]]
  - -> calls -> [[unresolvedrefvirtualmemory]]
  - -> calls -> [[unresolvedrefcpupercent]]
  - <- contains <- [[healthcheckrunner]]
- **__unresolved__::ref::cpu_percent** () -- 1 connections
  - <- calls <- [[checkresources]]
- **__unresolved__::ref::virtual_memory** () -- 1 connections
  - <- calls <- [[checkresources]]

## Internal Relationships
- _check_resources -> calls -> __unresolved__::ref::virtual_memory [EXTRACTED]
- _check_resources -> calls -> __unresolved__::ref::cpu_percent [EXTRACTED]

## Cross-Community Connections
- _check_resources -> calls -> __unresolved__::ref::healthresult (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 _check_resources, __unresolved__::ref::cpu_percent, __unresolved__::ref::virtual_memory를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 health_checker.py이다.

### Key Facts
- def _register_all(self): # 인프라 self._reg("I-1", "infra", self._check_db_connection) self._reg("I-2", "infra", self._check_storage) self._reg("I-3", "infra", self._check_resources) # 데이터 정합성 self._reg("D-1", "data", self._check_stale_days_remaining) self._reg("D-2", "data",…
