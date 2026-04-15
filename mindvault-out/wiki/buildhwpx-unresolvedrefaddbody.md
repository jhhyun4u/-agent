# build_hwpx & __unresolved__::ref::_add_body
Cohesion: 0.25 | Nodes: 8

## Key Nodes
- **build_hwpx** (C:\project\tenopa proposer\-agent-master\app\services\hwpx_builder.py) -- 12 connections
  - -> calls -> [[unresolvedrefnew]]
  - -> calls -> [[unresolvedrefsetupstyles]]
  - -> calls -> [[unresolvedrefdebug]]
  - -> calls -> [[unresolvedrefaddcover]]
  - -> calls -> [[unresolvedrefaddevaluationtable]]
  - -> calls -> [[unresolvedrefaddtoc]]
  - -> calls -> [[unresolvedrefaddbody]]
  - -> calls -> [[unresolvedrefmkdir]]
  - -> calls -> [[unresolvedrefsavetopath]]
  - -> calls -> [[unresolvedrefstr]]
  - -> calls -> [[unresolvedrefinfo]]
  - <- contains <- [[hwpxbuilder]]
- **__unresolved__::ref::_add_body** () -- 1 connections
  - <- calls <- [[buildhwpx]]
- **__unresolved__::ref::_add_cover** () -- 1 connections
  - <- calls <- [[buildhwpx]]
- **__unresolved__::ref::_add_evaluation_table** () -- 1 connections
  - <- calls <- [[buildhwpx]]
- **__unresolved__::ref::_add_toc** () -- 1 connections
  - <- calls <- [[buildhwpx]]
- **__unresolved__::ref::_setup_styles** () -- 1 connections
  - <- calls <- [[buildhwpx]]
- **__unresolved__::ref::new** () -- 1 connections
  - <- calls <- [[buildhwpx]]
- **__unresolved__::ref::save_to_path** () -- 1 connections
  - <- calls <- [[buildhwpx]]

## Internal Relationships
- build_hwpx -> calls -> __unresolved__::ref::new [EXTRACTED]
- build_hwpx -> calls -> __unresolved__::ref::_setup_styles [EXTRACTED]
- build_hwpx -> calls -> __unresolved__::ref::_add_cover [EXTRACTED]
- build_hwpx -> calls -> __unresolved__::ref::_add_evaluation_table [EXTRACTED]
- build_hwpx -> calls -> __unresolved__::ref::_add_toc [EXTRACTED]
- build_hwpx -> calls -> __unresolved__::ref::_add_body [EXTRACTED]
- build_hwpx -> calls -> __unresolved__::ref::save_to_path [EXTRACTED]

## Cross-Community Connections
- build_hwpx -> calls -> __unresolved__::ref::debug (-> [[unresolvedrefget-unresolvedreflen]])
- build_hwpx -> calls -> __unresolved__::ref::mkdir (-> [[unresolvedrefget-unresolvedreflen]])
- build_hwpx -> calls -> __unresolved__::ref::str (-> [[unresolvedrefget-unresolvedreflen]])
- build_hwpx -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 build_hwpx, __unresolved__::ref::_add_body, __unresolved__::ref::_add_cover를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 hwpx_builder.py이다.

### Key Facts
- --------------------------------------------------------------------------- 라이브러리 패치 ---------------------------------------------------------------------------
