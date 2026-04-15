# _load_state_data & __unresolved__::ref::_load_project_state
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **_load_state_data** (C:\project\tenopa proposer\-agent-master\app\services\prompt_simulator.py) -- 3 connections
  - -> calls -> [[unresolvedrefloadsampledata]]
  - -> calls -> [[unresolvedrefloadprojectstate]]
  - <- contains <- [[promptsimulator]]
- **__unresolved__::ref::_load_project_state** () -- 1 connections
  - <- calls <- [[loadstatedata]]
- **__unresolved__::ref::_load_sample_data** () -- 1 connections
  - <- calls <- [[loadstatedata]]

## Internal Relationships
- _load_state_data -> calls -> __unresolved__::ref::_load_sample_data [EXTRACTED]
- _load_state_data -> calls -> __unresolved__::ref::_load_project_state [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 _load_state_data, __unresolved__::ref::_load_project_state, __unresolved__::ref::_load_sample_data를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 prompt_simulator.py이다.

### Key Facts
- 2. state 데이터 로드 state_data = await _load_state_data( req.data_source, req.data_source_id, req.custom_variables, )
