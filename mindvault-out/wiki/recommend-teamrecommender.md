# recommend & TeamRecommender
Cohesion: 0.17 | Nodes: 12

## Key Nodes
- **recommend** (C:\project\tenopa proposer\scripts\team_recommender.py) -- 12 connections
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
- **TeamRecommender** (C:\project\tenopa proposer\scripts\team_recommender.py) -- 9 connections
  - -> contains -> [[init]]
  - -> contains -> [[classifydomain]]
  - -> contains -> [[scorespecialization]]
  - -> contains -> [[scoretrackrecord]]
  - -> contains -> [[scoredomain]]
  - -> contains -> [[confidence]]
  - -> contains -> [[buildreason]]
  - -> contains -> [[recommend]]
  - <- contains <- [[teamrecommender]]
- **classify_domain** (C:\project\tenopa proposer\scripts\team_recommender.py) -- 3 connections
  - -> calls -> [[unresolvedrefitems]]
  - -> calls -> [[unresolvedrefsum]]
  - <- contains <- [[teamrecommender]]
- **__init__** (C:\project\tenopa proposer\scripts\team_recommender.py) -- 2 connections
  - -> calls -> [[unresolvedrefpath]]
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
- **_confidence** (C:\project\tenopa proposer\scripts\team_recommender.py) -- 1 connections
  - <- contains <- [[teamrecommender]]

## Internal Relationships
- TeamRecommender -> contains -> __init__ [EXTRACTED]
- TeamRecommender -> contains -> classify_domain [EXTRACTED]
- TeamRecommender -> contains -> _confidence [EXTRACTED]
- TeamRecommender -> contains -> recommend [EXTRACTED]
- recommend -> calls -> __unresolved__::ref::classify_domain [EXTRACTED]
- recommend -> calls -> __unresolved__::ref::_score_specialization [EXTRACTED]
- recommend -> calls -> __unresolved__::ref::_score_track_record [EXTRACTED]
- recommend -> calls -> __unresolved__::ref::_score_domain [EXTRACTED]
- recommend -> calls -> __unresolved__::ref::teamrecommendation [EXTRACTED]
- recommend -> calls -> __unresolved__::ref::_confidence [EXTRACTED]
- recommend -> calls -> __unresolved__::ref::_build_reason [EXTRACTED]

## Cross-Community Connections
- TeamRecommender -> contains -> _score_specialization (-> [[unresolvedrefget-unresolvedrefexecute]])
- TeamRecommender -> contains -> _score_track_record (-> [[unresolvedrefget-unresolvedrefexecute]])
- TeamRecommender -> contains -> _score_domain (-> [[unresolvedrefget-unresolvedrefexecute]])
- TeamRecommender -> contains -> _build_reason (-> [[unresolvedrefget-unresolvedrefexecute]])
- __init__ -> calls -> __unresolved__::ref::path (-> [[unresolvedrefprint-unresolvedrefpath]])
- classify_domain -> calls -> __unresolved__::ref::items (-> [[unresolvedrefget-unresolvedrefexecute]])
- classify_domain -> calls -> __unresolved__::ref::sum (-> [[unresolvedrefget-unresolvedrefexecute]])
- recommend -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedrefexecute]])
- recommend -> calls -> __unresolved__::ref::round (-> [[unresolvedrefget-unresolvedrefexecute]])
- recommend -> calls -> __unresolved__::ref::append (-> [[unresolvedrefget-unresolvedrefexecute]])
- recommend -> calls -> __unresolved__::ref::sort (-> [[unresolvedrefreact-unresolvedreflibapi]])

## Context
이 커뮤니티는 recommend, TeamRecommender, classify_domain를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 team_recommender.py이다.

### Key Facts
- 사용법: # 모듈로 임포트 from scripts.team_recommender import TeamRecommender recommender = TeamRecommender() results = recommender.recommend("바이오빅데이터 활용 AI 기반 신규사업 기획")
- 사용법: # 모듈로 임포트 from scripts.team_recommender import TeamRecommender recommender = TeamRecommender() results = recommender.recommend("바이오빅데이터 활용 AI 기반 신규사업 기획")
- def classify_domain(self, title: str) -> tuple[str, int]: """공고 제목 → 사업영역 분류 + 매칭 키워드 수.""" best_domain = "" best_count = 0 for domain, keywords in DOMAIN_KEYWORDS.items(): count = sum(1 for kw in keywords if kw in title) if count > best_count: best_count = count best_domain = domain return…
- def __init__(self, team_path: str | Path | None = None, profile_path: str | Path | None = None): self.team_path = Path(team_path) if team_path else TEAM_PATH self.profile_path = Path(profile_path) if profile_path else PROFILE_PATH self._team_data: dict | None = None self._profile: dict | None = None
- def _confidence(self, score: int) -> str: if score >= 60: return "높음" elif score >= 35: return "보통" return "낮음"
