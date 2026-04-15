# __init__ & __unresolved__::ref::_register_all
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **__init__** (C:\project\tenopa proposer\-agent-master\app\services\health_checker.py) -- 2 connections
  - -> calls -> [[unresolvedrefregisterall]]
  - <- contains <- [[healthcheckrunner]]
- **__unresolved__::ref::_register_all** () -- 1 connections
  - <- calls <- [[init]]

## Internal Relationships
- __init__ -> calls -> __unresolved__::ref::_register_all [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 __init__, __unresolved__::ref::_register_all를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 health_checker.py이다.

### Key Facts
- def __init__(self): self._checks: dict[str, tuple[CheckCategory, Callable]] = {} self._register_all()
