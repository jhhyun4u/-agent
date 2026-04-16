# _call_qualification & __unresolved__::ref::_format_bids_for_qualification
Cohesion: 0.50 | Nodes: 4

## Key Nodes
- **_call_qualification** (C:\project\tenopa proposer\app\services\bidding\monitor\recommender.py) -- 6 connections
  - -> calls -> [[unresolvedrefformatprofile]]
  - -> calls -> [[unresolvedrefformatbidsforqualification]]
  - -> calls -> [[unresolvedreflen]]
  - -> calls -> [[unresolvedrefcreate]]
  - -> calls -> [[unresolvedrefparsequalificationresponse]]
  - <- contains <- [[bidrecommender]]
- **__unresolved__::ref::_format_bids_for_qualification** () -- 1 connections
  - <- calls <- [[callqualification]]
- **__unresolved__::ref::_format_profile** () -- 1 connections
  - <- calls <- [[callqualification]]
- **__unresolved__::ref::_parse_qualification_response** () -- 1 connections
  - <- calls <- [[callqualification]]

## Internal Relationships
- _call_qualification -> calls -> __unresolved__::ref::_format_profile [EXTRACTED]
- _call_qualification -> calls -> __unresolved__::ref::_format_bids_for_qualification [EXTRACTED]
- _call_qualification -> calls -> __unresolved__::ref::_parse_qualification_response [EXTRACTED]

## Cross-Community Connections
- _call_qualification -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedrefexecute]])
- _call_qualification -> calls -> __unresolved__::ref::create (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 _call_qualification, __unresolved__::ref::_format_bids_for_qualification, __unresolved__::ref::_format_profile를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 recommender.py이다.

### Key Facts
- for i in range(0, len(bids), self.QUAL_BATCH_SIZE): batch = bids[i : i + self.QUAL_BATCH_SIZE] try: batch_results = await self._call_qualification(team_profile, batch) results.extend(batch_results) except Exception as e: logger.error(f"자격 판정 배치 {i//self.QUAL_BATCH_SIZE+1} 실패: {e}") for b in batch:…
