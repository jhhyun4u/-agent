# run_comparison & __unresolved__::ref::_get_prompt_by_version
Cohesion: 0.50 | Nodes: 4

## Key Nodes
- **run_comparison** (C:\project\tenopa proposer\app\services\prompt_simulator.py) -- 7 connections
  - -> calls -> [[unresolvedrefgetpromptbyversion]]
  - -> calls -> [[unresolvedrefsimulationrequest]]
  - -> calls -> [[unresolvedrefrunsimulation]]
  - -> calls -> [[unresolvedrefabs]]
  - -> calls -> [[unresolvedrefmodeldump]]
  - -> calls -> [[unresolvedrefround]]
  - <- contains <- [[promptsimulator]]
- **__unresolved__::ref::_get_prompt_by_version** () -- 1 connections
  - <- calls <- [[runcomparison]]
- **__unresolved__::ref::run_simulation** () -- 1 connections
  - <- calls <- [[runcomparison]]
- **__unresolved__::ref::simulationrequest** () -- 1 connections
  - <- calls <- [[runcomparison]]

## Internal Relationships
- run_comparison -> calls -> __unresolved__::ref::_get_prompt_by_version [EXTRACTED]
- run_comparison -> calls -> __unresolved__::ref::simulationrequest [EXTRACTED]
- run_comparison -> calls -> __unresolved__::ref::run_simulation [EXTRACTED]

## Cross-Community Connections
- run_comparison -> calls -> __unresolved__::ref::abs (-> [[unresolvedrefreact-unresolvedreflibapi]])
- run_comparison -> calls -> __unresolved__::ref::model_dump (-> [[unresolvedrefget-unresolvedrefexecute]])
- run_comparison -> calls -> __unresolved__::ref::round (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 run_comparison, __unresolved__::ref::_get_prompt_by_version, __unresolved__::ref::run_simulation를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 prompt_simulator.py이다.

### Key Facts
- async def run_comparison( prompt_id: str, version_a: Optional[int], text_a: Optional[str], version_b: Optional[int], text_b: Optional[str], data_source: str, data_source_id: Optional[str], run_quality_check: bool, user_id: str, ) -> dict: """A vs B 비교 시뮬레이션.""" # version → text 변환 if not text_a and…
