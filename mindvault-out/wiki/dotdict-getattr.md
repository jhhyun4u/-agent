# DotDict & __getattr__
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **DotDict** (C:\project\tenopa proposer\-agent-master\tests\test_phase8_misc_api.py) -- 3 connections
  - -> extends -> [[unresolvedrefdict]]
  - -> contains -> [[getattr]]
  - <- contains <- [[testphase8miscapi]]
- **__getattr__** (C:\project\tenopa proposer\-agent-master\tests\test_phase8_misc_api.py) -- 2 connections
  - -> calls -> [[unresolvedrefattributeerror]]
  - <- contains <- [[dotdict]]
- **__unresolved__::ref::attributeerror** () -- 1 connections
  - <- calls <- [[getattr]]

## Internal Relationships
- DotDict -> contains -> __getattr__ [EXTRACTED]
- __getattr__ -> calls -> __unresolved__::ref::attributeerror [EXTRACTED]

## Cross-Community Connections
- DotDict -> extends -> __unresolved__::ref::dict (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 DotDict, __getattr__, __unresolved__::ref::attributeerror를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 test_phase8_misc_api.py이다.

### Key Facts
- 레거시 라우트가 user.id (dot-access)를 사용하므로 DotDict mock 필요. """
- class DotDict(dict): """dict + attribute access.""" def __getattr__(self, key): try: return self[key] except KeyError: raise AttributeError(key)
