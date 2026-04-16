# _analyze_competition & _analyze_defence_offence_strategy
Cohesion: 0.17 | Nodes: 12

## Key Nodes
- **_analyze_competition** (C:\project\tenopa proposer\scripts\archive\strategy_planning_engine.py) -- 10 connections
  - -> calls -> [[unresolvedrefsearchg2bcompetitors]]
  - -> calls -> [[unresolvedrefcompetitiveanalysis]]
  - -> calls -> [[unresolvedrefjoin]]
  - -> calls -> [[unresolvedrefappend]]
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefany]]
  - -> calls -> [[unresolvedrefassesscompetitorstrength]]
  - -> calls -> [[unresolvedrefassesscompetitorweakness]]
  - -> calls -> [[unresolvedrefcreatedefaultcompetitoranalysis]]
  - <- contains <- [[strategyplanningengine]]
- **_analyze_defence_offence_strategy** (C:\project\tenopa proposer\scripts\archive\strategy_planning_engine.py) -- 7 connections
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefanalyzerelevantexperience]]
  - -> calls -> [[unresolvedrefcalculatetrackrecordstrength]]
  - -> calls -> [[unresolvedrefsearchg2bcompetitors]]
  - -> calls -> [[unresolvedrefanalyzecompetitorstrength]]
  - -> calls -> [[unresolvedrefcalculateexpertisematch]]
  - <- contains <- [[strategyplanningengine]]
- **_create_default_competitor_analysis** (C:\project\tenopa proposer\scripts\archive\strategy_planning_engine.py) -- 3 connections
  - -> calls -> [[unresolvedrefcompetitiveanalysis]]
  - -> calls -> [[unresolvedrefget]]
  - <- contains <- [[strategyplanningengine]]
- **__unresolved__::ref::_search_g2b_competitors** () -- 2 connections
  - <- calls <- [[analyzedefenceoffencestrategy]]
  - <- calls <- [[analyzecompetition]]
- **__unresolved__::ref::competitiveanalysis** () -- 2 connections
  - <- calls <- [[analyzecompetition]]
  - <- calls <- [[createdefaultcompetitoranalysis]]
- **__unresolved__::ref::_analyze_competitor_strength** () -- 1 connections
  - <- calls <- [[analyzedefenceoffencestrategy]]
- **__unresolved__::ref::_analyze_relevant_experience** () -- 1 connections
  - <- calls <- [[analyzedefenceoffencestrategy]]
- **__unresolved__::ref::_assess_competitor_strength** () -- 1 connections
  - <- calls <- [[analyzecompetition]]
- **__unresolved__::ref::_assess_competitor_weakness** () -- 1 connections
  - <- calls <- [[analyzecompetition]]
- **__unresolved__::ref::_calculate_expertise_match** () -- 1 connections
  - <- calls <- [[analyzedefenceoffencestrategy]]
- **__unresolved__::ref::_calculate_track_record_strength** () -- 1 connections
  - <- calls <- [[analyzedefenceoffencestrategy]]
- **__unresolved__::ref::_create_default_competitor_analysis** () -- 1 connections
  - <- calls <- [[analyzecompetition]]

## Internal Relationships
- _analyze_competition -> calls -> __unresolved__::ref::_search_g2b_competitors [EXTRACTED]
- _analyze_competition -> calls -> __unresolved__::ref::competitiveanalysis [EXTRACTED]
- _analyze_competition -> calls -> __unresolved__::ref::_assess_competitor_strength [EXTRACTED]
- _analyze_competition -> calls -> __unresolved__::ref::_assess_competitor_weakness [EXTRACTED]
- _analyze_competition -> calls -> __unresolved__::ref::_create_default_competitor_analysis [EXTRACTED]
- _analyze_defence_offence_strategy -> calls -> __unresolved__::ref::_analyze_relevant_experience [EXTRACTED]
- _analyze_defence_offence_strategy -> calls -> __unresolved__::ref::_calculate_track_record_strength [EXTRACTED]
- _analyze_defence_offence_strategy -> calls -> __unresolved__::ref::_search_g2b_competitors [EXTRACTED]
- _analyze_defence_offence_strategy -> calls -> __unresolved__::ref::_analyze_competitor_strength [EXTRACTED]
- _analyze_defence_offence_strategy -> calls -> __unresolved__::ref::_calculate_expertise_match [EXTRACTED]
- _create_default_competitor_analysis -> calls -> __unresolved__::ref::competitiveanalysis [EXTRACTED]

## Cross-Community Connections
- _analyze_competition -> calls -> __unresolved__::ref::join (-> [[unresolvedrefget-unresolvedrefexecute]])
- _analyze_competition -> calls -> __unresolved__::ref::append (-> [[unresolvedrefget-unresolvedrefexecute]])
- _analyze_competition -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedrefexecute]])
- _analyze_competition -> calls -> __unresolved__::ref::any (-> [[unresolvedrefget-unresolvedrefexecute]])
- _analyze_defence_offence_strategy -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedrefexecute]])
- _create_default_competitor_analysis -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 _analyze_competition, _analyze_defence_offence_strategy, _create_default_competitor_analysis를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 strategy_planning_engine.py이다.

### Key Facts
- 경쟁사 분석 competitors = await self._analyze_competition(rfp_analysis, market_analysis)
- Defence vs Offence 전략 분석 strategy_analysis = await self._analyze_defence_offence_strategy( rfp_analysis, company_profile, past_proposals )
- 3. 경쟁사가 없는 경우 기본 분석 if not competitors: competitors = [self._create_default_competitor_analysis(rfp_analysis)]
