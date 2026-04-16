# go_no_go & __unresolved__::ref::_ai_strategic_assessment
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **go_no_go** (C:\project\tenopa proposer\app\graph\nodes\go_no_go.py) -- 8 connections
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefrfptodict]]
  - -> calls -> [[unresolvedrefscoresimilarperformance]]
  - -> calls -> [[unresolvedrefscorequalification]]
  - -> calls -> [[unresolvedrefscorecompetition]]
  - -> calls -> [[unresolvedrefaistrategicassessment]]
  - -> calls -> [[unresolvedrefgonogoresult]]
  - <- contains <- [[gonogo]]
- **__unresolved__::ref::_ai_strategic_assessment** () -- 1 connections
  - <- calls <- [[gonogo]]
- **__unresolved__::ref::gonogoresult** () -- 1 connections
  - <- calls <- [[gonogo]]
- **__unresolved__::ref::score_competition** () -- 1 connections
  - <- calls <- [[gonogo]]
- **__unresolved__::ref::score_qualification** () -- 1 connections
  - <- calls <- [[gonogo]]
- **__unresolved__::ref::score_similar_performance** () -- 1 connections
  - <- calls <- [[gonogo]]

## Internal Relationships
- go_no_go -> calls -> __unresolved__::ref::score_similar_performance [EXTRACTED]
- go_no_go -> calls -> __unresolved__::ref::score_qualification [EXTRACTED]
- go_no_go -> calls -> __unresolved__::ref::score_competition [EXTRACTED]
- go_no_go -> calls -> __unresolved__::ref::_ai_strategic_assessment [EXTRACTED]
- go_no_go -> calls -> __unresolved__::ref::gonogoresult [EXTRACTED]

## Cross-Community Connections
- go_no_go -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedrefexecute]])
- go_no_go -> calls -> __unresolved__::ref::rfp_to_dict (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 go_no_go, __unresolved__::ref::_ai_strategic_assessment, __unresolved__::ref::gonogoresult를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 go_no_go.py이다.

### Key Facts
- async def go_no_go(state: ProposalState) -> dict: """STEP 1-②: Go/No-Go 4축 정량 스코어링."""
