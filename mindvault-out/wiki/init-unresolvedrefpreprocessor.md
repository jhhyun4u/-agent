# __init__ & __unresolved__::ref::preprocessor
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **__init__** (C:\project\tenopa proposer\app\services\bidding\monitor\__init__.py) -- 5 connections
  - -> imports -> [[unresolvedreffetcher]]
  - -> imports -> [[unresolvedrefscorer]]
  - -> imports -> [[unresolvedrefpreprocessor]]
  - -> imports -> [[unresolvedrefcleanup]]
  - -> imports -> [[unresolvedrefrecommender]]
- **__unresolved__::ref::preprocessor** () -- 2 connections
  - <- imports <- [[recommender]]
  - <- imports <- [[init]]
- **__unresolved__::ref::cleanup** () -- 1 connections
  - <- imports <- [[init]]
- **__unresolved__::ref::fetcher** () -- 1 connections
  - <- imports <- [[init]]
- **__unresolved__::ref::recommender** () -- 1 connections
  - <- imports <- [[init]]
- **__unresolved__::ref::scorer** () -- 1 connections
  - <- imports <- [[init]]

## Internal Relationships
- __init__ -> imports -> __unresolved__::ref::fetcher [EXTRACTED]
- __init__ -> imports -> __unresolved__::ref::scorer [EXTRACTED]
- __init__ -> imports -> __unresolved__::ref::preprocessor [EXTRACTED]
- __init__ -> imports -> __unresolved__::ref::cleanup [EXTRACTED]
- __init__ -> imports -> __unresolved__::ref::recommender [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 __init__, __unresolved__::ref::preprocessor, __unresolved__::ref::cleanup를 중심으로 imports 관계로 연결되어 있다. 주요 소스 파일은 __init__.py이다.
