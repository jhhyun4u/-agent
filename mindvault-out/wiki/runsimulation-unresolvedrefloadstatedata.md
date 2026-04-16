# run_simulation & __unresolved__::ref::_load_state_data
Cohesion: 0.22 | Nodes: 9

## Key Nodes
- **run_simulation** (C:\project\tenopa proposer\app\services\prompt_simulator.py) -- 16 connections
  - -> calls -> [[unresolvedreftime]]
  - -> calls -> [[unresolvedrefgetactiveprompt]]
  - -> calls -> [[unresolvedrefsimulationresult]]
  - -> calls -> [[unresolvedrefloadstatedata]]
  - -> calls -> [[unresolvedrefsubstitutevariables]]
  - -> calls -> [[unresolvedrefclaudegenerate]]
  - -> calls -> [[unresolvedrefisinstance]]
  - -> calls -> [[unresolvedrefdumps]]
  - -> calls -> [[unresolvedrefint]]
  - -> calls -> [[unresolvedreflen]]
  - -> calls -> [[unresolvedrefvalidateoutputformat]]
  - -> calls -> [[unresolvedrefrunqualitycheck]]
  - -> calls -> [[unresolvedrefsavesimulation]]
  - -> calls -> [[unresolvedrefupdatequota]]
  - -> calls -> [[unresolvedrefcheckquota]]
  - <- contains <- [[promptsimulator]]
- **__unresolved__::ref::_load_state_data** () -- 1 connections
  - <- calls <- [[runsimulation]]
- **__unresolved__::ref::_run_quality_check** () -- 1 connections
  - <- calls <- [[runsimulation]]
- **__unresolved__::ref::_save_simulation** () -- 1 connections
  - <- calls <- [[runsimulation]]
- **__unresolved__::ref::_substitute_variables** () -- 1 connections
  - <- calls <- [[runsimulation]]
- **__unresolved__::ref::_update_quota** () -- 1 connections
  - <- calls <- [[runsimulation]]
- **__unresolved__::ref::_validate_output_format** () -- 1 connections
  - <- calls <- [[runsimulation]]
- **__unresolved__::ref::check_quota** () -- 1 connections
  - <- calls <- [[runsimulation]]
- **__unresolved__::ref::simulationresult** () -- 1 connections
  - <- calls <- [[runsimulation]]

## Internal Relationships
- run_simulation -> calls -> __unresolved__::ref::simulationresult [EXTRACTED]
- run_simulation -> calls -> __unresolved__::ref::_load_state_data [EXTRACTED]
- run_simulation -> calls -> __unresolved__::ref::_substitute_variables [EXTRACTED]
- run_simulation -> calls -> __unresolved__::ref::_validate_output_format [EXTRACTED]
- run_simulation -> calls -> __unresolved__::ref::_run_quality_check [EXTRACTED]
- run_simulation -> calls -> __unresolved__::ref::_save_simulation [EXTRACTED]
- run_simulation -> calls -> __unresolved__::ref::_update_quota [EXTRACTED]
- run_simulation -> calls -> __unresolved__::ref::check_quota [EXTRACTED]

## Cross-Community Connections
- run_simulation -> calls -> __unresolved__::ref::time (-> [[unresolvedrefbasemodel-unresolvedreflogging]])
- run_simulation -> calls -> __unresolved__::ref::get_active_prompt (-> [[unresolvedrefget-unresolvedrefexecute]])
- run_simulation -> calls -> __unresolved__::ref::claude_generate (-> [[unresolvedrefget-unresolvedrefexecute]])
- run_simulation -> calls -> __unresolved__::ref::isinstance (-> [[unresolvedrefget-unresolvedrefexecute]])
- run_simulation -> calls -> __unresolved__::ref::dumps (-> [[unresolvedrefget-unresolvedrefexecute]])
- run_simulation -> calls -> __unresolved__::ref::int (-> [[unresolvedrefget-unresolvedrefexecute]])
- run_simulation -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 run_simulation, __unresolved__::ref::_load_state_data, __unresolved__::ref::_run_quality_check를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 prompt_simulator.py이다.

### Key Facts
- async def run_simulation( prompt_id: str, req: SimulationRequest, user_id: str, ) -> SimulationResult: """시뮬레이션 메인 실행.""" start = time.time()
