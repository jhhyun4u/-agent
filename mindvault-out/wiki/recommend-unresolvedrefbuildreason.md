# recommend & __unresolved__::ref::_build_reason
Cohesion: 0.25 | Nodes: 8

## Key Nodes
- **recommend** (C:\project\tenopa proposer\-agent-master\scripts\team_recommender.py) -- 12 connections
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefclassifydomain]]
  - -> calls -> [[unresolvedrefscorespecialization]]
  - -> calls -> [[unresolvedrefscoretrackrecord]]
  - -> calls -> [[unresolvedrefscoredomain]]
  - -> calls -> [[unresolvedrefround]]
  - -> calls -> [[unresolvedrefteamrecommendation]]
  - -> calls -> [[unresolvedrefconfidence]]
  - -> calls -> [[unresolvedrefbuildreason]]
  - -> calls -> [[unresolvedrefappend]]
  - -> calls -> [[unresolvedrefsort]]
  - <- contains <- [[teamrecommender]]
- **__unresolved__::ref::_build_reason** () -- 1 connections
  - <- calls <- [[recommend]]
- **__unresolved__::ref::_confidence** () -- 1 connections
  - <- calls <- [[recommend]]
- **__unresolved__::ref::_score_domain** () -- 1 connections
  - <- calls <- [[recommend]]
- **__unresolved__::ref::_score_specialization** () -- 1 connections
  - <- calls <- [[recommend]]
- **__unresolved__::ref::_score_track_record** () -- 1 connections
  - <- calls <- [[recommend]]
- **__unresolved__::ref::classify_domain** () -- 1 connections
  - <- calls <- [[recommend]]
- **__unresolved__::ref::teamrecommendation** () -- 1 connections
  - <- calls <- [[recommend]]

## Internal Relationships
- recommend -> calls -> __unresolved__::ref::classify_domain [EXTRACTED]
- recommend -> calls -> __unresolved__::ref::_score_specialization [EXTRACTED]
- recommend -> calls -> __unresolved__::ref::_score_track_record [EXTRACTED]
- recommend -> calls -> __unresolved__::ref::_score_domain [EXTRACTED]
- recommend -> calls -> __unresolved__::ref::teamrecommendation [EXTRACTED]
- recommend -> calls -> __unresolved__::ref::_confidence [EXTRACTED]
- recommend -> calls -> __unresolved__::ref::_build_reason [EXTRACTED]

## Cross-Community Connections
- recommend -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- recommend -> calls -> __unresolved__::ref::round (-> [[unresolvedrefget-unresolvedreflen]])
- recommend -> calls -> __unresolved__::ref::append (-> [[unresolvedrefget-unresolvedreflen]])
- recommend -> calls -> __unresolved__::ref::sort (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 recommend, __unresolved__::ref::_build_reason, __unresolved__::ref::_confidence를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 team_recommender.py이다.

### Key Facts
- 사용법: # 모듈로 임포트 from scripts.team_recommender import TeamRecommender recommender = TeamRecommender() results = recommender.recommend("바이오빅데이터 활용 AI 기반 신규사업 기획")
