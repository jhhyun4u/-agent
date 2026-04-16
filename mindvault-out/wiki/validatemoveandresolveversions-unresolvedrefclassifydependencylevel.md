# validate_move_and_resolve_versions & __unresolved__::ref::_classify_dependency_level
Cohesion: 0.29 | Nodes: 7

## Key Nodes
- **validate_move_and_resolve_versions** (C:\project\tenopa proposer\app\services\version_manager.py) -- 9 connections
  - -> calls -> [[unresolvedrefgetnodedependencies]]
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefappend]]
  - -> calls -> [[unresolvedrefversionconflict]]
  - -> calls -> [[unresolvedrefclassifydependencylevel]]
  - -> calls -> [[unresolvedrefgetdownstreamnodes]]
  - -> calls -> [[unresolvedrefgeneratevalidationmessage]]
  - -> calls -> [[unresolvedrefmovevalidationresult]]
  - <- contains <- [[versionmanager]]
- **__unresolved__::ref::_classify_dependency_level** () -- 1 connections
  - <- calls <- [[validatemoveandresolveversions]]
- **__unresolved__::ref::_generate_validation_message** () -- 1 connections
  - <- calls <- [[validatemoveandresolveversions]]
- **__unresolved__::ref::_get_downstream_nodes** () -- 1 connections
  - <- calls <- [[validatemoveandresolveversions]]
- **__unresolved__::ref::_get_node_dependencies** () -- 1 connections
  - <- calls <- [[validatemoveandresolveversions]]
- **__unresolved__::ref::movevalidationresult** () -- 1 connections
  - <- calls <- [[validatemoveandresolveversions]]
- **__unresolved__::ref::versionconflict** () -- 1 connections
  - <- calls <- [[validatemoveandresolveversions]]

## Internal Relationships
- validate_move_and_resolve_versions -> calls -> __unresolved__::ref::_get_node_dependencies [EXTRACTED]
- validate_move_and_resolve_versions -> calls -> __unresolved__::ref::versionconflict [EXTRACTED]
- validate_move_and_resolve_versions -> calls -> __unresolved__::ref::_classify_dependency_level [EXTRACTED]
- validate_move_and_resolve_versions -> calls -> __unresolved__::ref::_get_downstream_nodes [EXTRACTED]
- validate_move_and_resolve_versions -> calls -> __unresolved__::ref::_generate_validation_message [EXTRACTED]
- validate_move_and_resolve_versions -> calls -> __unresolved__::ref::movevalidationresult [EXTRACTED]

## Cross-Community Connections
- validate_move_and_resolve_versions -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedrefexecute]])
- validate_move_and_resolve_versions -> calls -> __unresolved__::ref::append (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 validate_move_and_resolve_versions, __unresolved__::ref::_classify_dependency_level, __unresolved__::ref::_generate_validation_message를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 version_manager.py이다.

### Key Facts
- async def validate_move_and_resolve_versions( proposal_id: UUID, target_node: str, state: ProposalState, ) -> MoveValidationResult: """ 노드 이동 검증 및 버전 충돌 감지.
