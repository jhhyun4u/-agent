# test_technical_optimization & test_technical_optimization
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **test_technical_optimization** (C:\project\tenopa proposer\-agent-master\scripts\archive\test_technical_optimization.py) -- 6 connections
  - -> calls -> [[unresolvedrefrfpreviewengine]]
  - -> calls -> [[unresolvedrefanalyzetechnicalscoringoptimization]]
  - -> calls -> [[unresolvedrefprint]]
  - -> calls -> [[unresolvedrefenumerate]]
  - -> calls -> [[unresolvedrefprintexc]]
  - <- contains <- [[testtechnicaloptimization]]
- **test_technical_optimization** (C:\project\tenopa proposer\-agent-master\scripts\archive\test_technical_optimization.py) -- 3 connections
  - -> contains -> [[testtechnicaloptimization]]
  - -> imports -> [[unresolvedrefasyncio]]
  - -> imports -> [[unresolvedrefrfpreviewengine]]
- **__unresolved__::ref::analyze_technical_scoring_optimization** () -- 1 connections
  - <- calls <- [[testtechnicaloptimization]]
- **__unresolved__::ref::rfp_review_engine** () -- 1 connections
  - <- imports <- [[testtechnicaloptimization]]
- **__unresolved__::ref::rfpreviewengine** () -- 1 connections
  - <- calls <- [[testtechnicaloptimization]]

## Internal Relationships
- test_technical_optimization -> calls -> __unresolved__::ref::rfpreviewengine [EXTRACTED]
- test_technical_optimization -> calls -> __unresolved__::ref::analyze_technical_scoring_optimization [EXTRACTED]
- test_technical_optimization -> contains -> test_technical_optimization [EXTRACTED]
- test_technical_optimization -> imports -> __unresolved__::ref::rfp_review_engine [EXTRACTED]

## Cross-Community Connections
- test_technical_optimization -> calls -> __unresolved__::ref::print (-> [[unresolvedrefget-unresolvedreflen]])
- test_technical_optimization -> calls -> __unresolved__::ref::enumerate (-> [[unresolvedrefget-unresolvedreflen]])
- test_technical_optimization -> calls -> __unresolved__::ref::print_exc (-> [[unresolvedrefget-unresolvedreflen]])
- test_technical_optimization -> imports -> __unresolved__::ref::asyncio (-> [[unresolvedrefbasemodel-unresolvedreflogging]])

## Context
이 커뮤니티는 test_technical_optimization, test_technical_optimization, __unresolved__::ref::analyze_technical_scoring_optimization를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 test_technical_optimization.py이다.

### Key Facts
- async def test_technical_optimization(): engine = RFPReviewEngine() rfp = { 'basic_info': { 'title': '디지털 환경영향평가 연구사업', 'budget': 500000000, 'category': '환경평가' }, 'requirements': { 'technical_requirements': ['환경평가', '디지털화', '연구개발', 'AI', '데이터분석'] }, 'evaluation_criteria': { 'weights': {'기술성': 0.4,…
