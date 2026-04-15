# _analyze_defence_offence_strategy & __unresolved__::ref::_search_g2b_competitors
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **_analyze_defence_offence_strategy** (C:\project\tenopa proposer\-agent-master\scripts\archive\strategy_planning_engine.py) -- 7 connections
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefanalyzerelevantexperience]]
  - -> calls -> [[unresolvedrefcalculatetrackrecordstrength]]
  - -> calls -> [[unresolvedrefsearchg2bcompetitors]]
  - -> calls -> [[unresolvedrefanalyzecompetitorstrength]]
  - -> calls -> [[unresolvedrefcalculateexpertisematch]]
  - <- contains <- [[strategyplanningengine]]
- **__unresolved__::ref::_search_g2b_competitors** () -- 2 connections
  - <- calls <- [[analyzedefenceoffencestrategy]]
  - <- calls <- [[analyzecompetition]]
- **__unresolved__::ref::_analyze_competitor_strength** () -- 1 connections
  - <- calls <- [[analyzedefenceoffencestrategy]]
- **__unresolved__::ref::_analyze_relevant_experience** () -- 1 connections
  - <- calls <- [[analyzedefenceoffencestrategy]]
- **__unresolved__::ref::_calculate_expertise_match** () -- 1 connections
  - <- calls <- [[analyzedefenceoffencestrategy]]
- **__unresolved__::ref::_calculate_track_record_strength** () -- 1 connections
  - <- calls <- [[analyzedefenceoffencestrategy]]

## Internal Relationships
- _analyze_defence_offence_strategy -> calls -> __unresolved__::ref::_analyze_relevant_experience [EXTRACTED]
- _analyze_defence_offence_strategy -> calls -> __unresolved__::ref::_calculate_track_record_strength [EXTRACTED]
- _analyze_defence_offence_strategy -> calls -> __unresolved__::ref::_search_g2b_competitors [EXTRACTED]
- _analyze_defence_offence_strategy -> calls -> __unresolved__::ref::_analyze_competitor_strength [EXTRACTED]
- _analyze_defence_offence_strategy -> calls -> __unresolved__::ref::_calculate_expertise_match [EXTRACTED]

## Cross-Community Connections
- _analyze_defence_offence_strategy -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 _analyze_defence_offence_strategy, __unresolved__::ref::_search_g2b_competitors, __unresolved__::ref::_analyze_competitor_strength를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 strategy_planning_engine.py이다.

### Key Facts
- Defence vs Offence 전략 분석 strategy_analysis = await self._analyze_defence_offence_strategy( rfp_analysis, company_profile, past_proposals )
