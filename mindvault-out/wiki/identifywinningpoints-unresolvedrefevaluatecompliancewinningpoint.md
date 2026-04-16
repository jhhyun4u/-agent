# _identify_winning_points & __unresolved__::ref::_evaluate_compliance_winning_point
Cohesion: 0.29 | Nodes: 7

## Key Nodes
- **_identify_winning_points** (C:\project\tenopa proposer\scripts\archive\strategy_planning_engine.py) -- 8 connections
  - -> calls -> [[unresolvedrefevaluatetechnicalwinningpoint]]
  - -> calls -> [[unresolvedrefappend]]
  - -> calls -> [[unresolvedrefevaluateperformancewinningpoint]]
  - -> calls -> [[unresolvedrefevaluatepricewinningpoint]]
  - -> calls -> [[unresolvedrefevaluateinnovationwinningpoint]]
  - -> calls -> [[unresolvedrefevaluaterelationshipwinningpoint]]
  - -> calls -> [[unresolvedrefevaluatecompliancewinningpoint]]
  - <- contains <- [[strategyplanningengine]]
- **__unresolved__::ref::_evaluate_compliance_winning_point** () -- 1 connections
  - <- calls <- [[identifywinningpoints]]
- **__unresolved__::ref::_evaluate_innovation_winning_point** () -- 1 connections
  - <- calls <- [[identifywinningpoints]]
- **__unresolved__::ref::_evaluate_performance_winning_point** () -- 1 connections
  - <- calls <- [[identifywinningpoints]]
- **__unresolved__::ref::_evaluate_price_winning_point** () -- 1 connections
  - <- calls <- [[identifywinningpoints]]
- **__unresolved__::ref::_evaluate_relationship_winning_point** () -- 1 connections
  - <- calls <- [[identifywinningpoints]]
- **__unresolved__::ref::_evaluate_technical_winning_point** () -- 1 connections
  - <- calls <- [[identifywinningpoints]]

## Internal Relationships
- _identify_winning_points -> calls -> __unresolved__::ref::_evaluate_technical_winning_point [EXTRACTED]
- _identify_winning_points -> calls -> __unresolved__::ref::_evaluate_performance_winning_point [EXTRACTED]
- _identify_winning_points -> calls -> __unresolved__::ref::_evaluate_price_winning_point [EXTRACTED]
- _identify_winning_points -> calls -> __unresolved__::ref::_evaluate_innovation_winning_point [EXTRACTED]
- _identify_winning_points -> calls -> __unresolved__::ref::_evaluate_relationship_winning_point [EXTRACTED]
- _identify_winning_points -> calls -> __unresolved__::ref::_evaluate_compliance_winning_point [EXTRACTED]

## Cross-Community Connections
- _identify_winning_points -> calls -> __unresolved__::ref::append (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 _identify_winning_points, __unresolved__::ref::_evaluate_compliance_winning_point, __unresolved__::ref::_evaluate_innovation_winning_point를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 strategy_planning_engine.py이다.

### Key Facts
- 승점 분석 (전략 타입에 따라 조정) winning_points = await self._identify_winning_points( rfp_analysis, company_profile, competitors, past_proposals, strategy_analysis )
