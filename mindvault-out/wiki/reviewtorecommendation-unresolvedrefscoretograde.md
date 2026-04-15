# _review_to_recommendation & __unresolved__::ref::_score_to_grade
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **_review_to_recommendation** (C:\project\tenopa proposer\-agent-master\app\services\bidding\monitor\recommender.py) -- 6 connections
  - -> calls -> [[unresolvedrefrecommendationreason]]
  - -> calls -> [[unresolvedrefriskfactor]]
  - -> calls -> [[unresolvedrefbidrecommendation]]
  - -> calls -> [[unresolvedrefscoretograde]]
  - -> calls -> [[unresolvedrefget]]
  - <- contains <- [[bidrecommender]]
- **__unresolved__::ref::_score_to_grade** () -- 1 connections
  - <- calls <- [[reviewtorecommendation]]
- **__unresolved__::ref::bidrecommendation** () -- 1 connections
  - <- calls <- [[reviewtorecommendation]]
- **__unresolved__::ref::recommendationreason** () -- 1 connections
  - <- calls <- [[reviewtorecommendation]]
- **__unresolved__::ref::riskfactor** () -- 1 connections
  - <- calls <- [[reviewtorecommendation]]

## Internal Relationships
- _review_to_recommendation -> calls -> __unresolved__::ref::recommendationreason [EXTRACTED]
- _review_to_recommendation -> calls -> __unresolved__::ref::riskfactor [EXTRACTED]
- _review_to_recommendation -> calls -> __unresolved__::ref::bidrecommendation [EXTRACTED]
- _review_to_recommendation -> calls -> __unresolved__::ref::_score_to_grade [EXTRACTED]

## Cross-Community Connections
- _review_to_recommendation -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 _review_to_recommendation, __unresolved__::ref::_score_to_grade, __unresolved__::ref::bidrecommendation를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 recommender.py이다.

### Key Facts
- Stage 2: TENOPA 리뷰어 평가 results: list[BidRecommendation] = [] for i in range(0, len(bids), self.REVIEW_BATCH_SIZE): batch = bids[i : i + self.REVIEW_BATCH_SIZE] try: reviews = await self._call_tenopa_review(batch, summaries) converted = [self._review_to_recommendation(r) for r in reviews]…
