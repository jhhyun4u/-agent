# _register_all & __unresolved__::ref::_reg
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **_register_all** (C:\project\tenopa proposer\-agent-master\app\services\health_checker.py) -- 2 connections
  - -> calls -> [[unresolvedrefreg]]
  - <- contains <- [[healthcheckrunner]]
- **__unresolved__::ref::_reg** () -- 1 connections
  - <- calls <- [[registerall]]

## Internal Relationships
- _register_all -> calls -> __unresolved__::ref::_reg [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 _register_all, __unresolved__::ref::_reg를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 health_checker.py이다.

### Key Facts
- def __init__(self): self._checks: dict[str, tuple[CheckCategory, Callable]] = {} self._register_all()
