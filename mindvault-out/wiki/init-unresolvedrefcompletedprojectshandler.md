# __init__ & __unresolved__::ref::completedprojectshandler
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **__init__** (C:\project\tenopa proposer\app\services\vault_handlers\__init__.py) -- 2 connections
  - -> imports -> [[unresolvedrefcompletedprojectshandler]]
  - -> imports -> [[unresolvedrefgovernmentguidelineshandler]]
- **__unresolved__::ref::completedprojectshandler** () -- 1 connections
  - <- imports <- [[init]]
- **__unresolved__::ref::governmentguidelineshandler** () -- 1 connections
  - <- imports <- [[init]]

## Internal Relationships
- __init__ -> imports -> __unresolved__::ref::completedprojectshandler [EXTRACTED]
- __init__ -> imports -> __unresolved__::ref::governmentguidelineshandler [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 __init__, __unresolved__::ref::completedprojectshandler, __unresolved__::ref::governmentguidelineshandler를 중심으로 imports 관계로 연결되어 있다. 주요 소스 파일은 __init__.py이다.
