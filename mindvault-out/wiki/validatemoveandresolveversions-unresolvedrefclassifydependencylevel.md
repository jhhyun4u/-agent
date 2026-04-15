# validate_move_and_resolve_versions & __unresolved__::ref::_classify_dependency_level
Cohesion: 0.20 | Nodes: 16

## Key Nodes
- **validate_move_and_resolve_versions** (C:\project\tenopa proposer\-agent-master\app\services\version_manager.py) -- 9 connections
  - -> calls -> [[unresolvedrefgetnodedependencies]]
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefappend]]
  - -> calls -> [[unresolvedrefversionconflict]]
  - -> calls -> [[unresolvedrefclassifydependencylevel]]
  - -> calls -> [[unresolvedrefgetdownstreamnodes]]
  - -> calls -> [[unresolvedrefgeneratevalidationmessage]]
  - -> calls -> [[unresolvedrefmovevalidationresult]]
  - <- contains <- [[versionmanager]]
- **__unresolved__::ref::_classify_dependency_level** () -- 5 connections
  - <- calls <- [[validatemoveandresolveversions]]
  - <- calls <- [[testnoconflictsclassification]]
  - <- calls <- [[testmissinginputclassification]]
  - <- calls <- [[testmultipleversionsclassification]]
  - <- calls <- [[testmixedconflictscriticalwins]]
- **__unresolved__::ref::versionconflict** () -- 5 connections
  - <- calls <- [[validatemoveandresolveversions]]
  - <- calls <- [[testnoconflictsclassification]]
  - <- calls <- [[testmissinginputclassification]]
  - <- calls <- [[testmultipleversionsclassification]]
  - <- calls <- [[testmixedconflictscriticalwins]]
- **TestDependencyClassification** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 5 connections
  - -> contains -> [[testnoconflictsclassification]]
  - -> contains -> [[testmissinginputclassification]]
  - -> contains -> [[testmultipleversionsclassification]]
  - -> contains -> [[testmixedconflictscriticalwins]]
  - <- contains <- [[testartifactversioning]]
- **__unresolved__::ref::_get_node_dependencies** () -- 4 connections
  - <- calls <- [[validatemoveandresolveversions]]
  - <- calls <- [[testproposalwritenextdependencies]]
  - <- calls <- [[testunknownnodedependencies]]
  - <- calls <- [[teststrategygeneratedependencies]]
- **TestNodeDependencies** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 4 connections
  - -> contains -> [[testproposalwritenextdependencies]]
  - -> contains -> [[testunknownnodedependencies]]
  - -> contains -> [[teststrategygeneratedependencies]]
  - <- contains <- [[testartifactversioning]]
- **test_missing_input_classification** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 3 connections
  - -> calls -> [[unresolvedrefversionconflict]]
  - -> calls -> [[unresolvedrefclassifydependencylevel]]
  - <- contains <- [[testdependencyclassification]]
- **test_mixed_conflicts_critical_wins** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 3 connections
  - -> calls -> [[unresolvedrefversionconflict]]
  - -> calls -> [[unresolvedrefclassifydependencylevel]]
  - <- contains <- [[testdependencyclassification]]
- **test_multiple_versions_classification** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 3 connections
  - -> calls -> [[unresolvedrefversionconflict]]
  - -> calls -> [[unresolvedrefclassifydependencylevel]]
  - <- contains <- [[testdependencyclassification]]
- **test_no_conflicts_classification** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 3 connections
  - -> calls -> [[unresolvedrefversionconflict]]
  - -> calls -> [[unresolvedrefclassifydependencylevel]]
  - <- contains <- [[testdependencyclassification]]
- **test_proposal_write_next_dependencies** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 2 connections
  - -> calls -> [[unresolvedrefgetnodedependencies]]
  - <- contains <- [[testnodedependencies]]
- **test_strategy_generate_dependencies** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 2 connections
  - -> calls -> [[unresolvedrefgetnodedependencies]]
  - <- contains <- [[testnodedependencies]]
- **test_unknown_node_dependencies** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 2 connections
  - -> calls -> [[unresolvedrefgetnodedependencies]]
  - <- contains <- [[testnodedependencies]]
- **__unresolved__::ref::_generate_validation_message** () -- 1 connections
  - <- calls <- [[validatemoveandresolveversions]]
- **__unresolved__::ref::_get_downstream_nodes** () -- 1 connections
  - <- calls <- [[validatemoveandresolveversions]]
- **__unresolved__::ref::movevalidationresult** () -- 1 connections
  - <- calls <- [[validatemoveandresolveversions]]

## Internal Relationships
- validate_move_and_resolve_versions -> calls -> __unresolved__::ref::_get_node_dependencies [EXTRACTED]
- validate_move_and_resolve_versions -> calls -> __unresolved__::ref::versionconflict [EXTRACTED]
- validate_move_and_resolve_versions -> calls -> __unresolved__::ref::_classify_dependency_level [EXTRACTED]
- validate_move_and_resolve_versions -> calls -> __unresolved__::ref::_get_downstream_nodes [EXTRACTED]
- validate_move_and_resolve_versions -> calls -> __unresolved__::ref::_generate_validation_message [EXTRACTED]
- validate_move_and_resolve_versions -> calls -> __unresolved__::ref::movevalidationresult [EXTRACTED]
- TestDependencyClassification -> contains -> test_no_conflicts_classification [EXTRACTED]
- TestDependencyClassification -> contains -> test_missing_input_classification [EXTRACTED]
- TestDependencyClassification -> contains -> test_multiple_versions_classification [EXTRACTED]
- TestDependencyClassification -> contains -> test_mixed_conflicts_critical_wins [EXTRACTED]
- TestNodeDependencies -> contains -> test_proposal_write_next_dependencies [EXTRACTED]
- TestNodeDependencies -> contains -> test_unknown_node_dependencies [EXTRACTED]
- TestNodeDependencies -> contains -> test_strategy_generate_dependencies [EXTRACTED]
- test_missing_input_classification -> calls -> __unresolved__::ref::versionconflict [EXTRACTED]
- test_missing_input_classification -> calls -> __unresolved__::ref::_classify_dependency_level [EXTRACTED]
- test_mixed_conflicts_critical_wins -> calls -> __unresolved__::ref::versionconflict [EXTRACTED]
- test_mixed_conflicts_critical_wins -> calls -> __unresolved__::ref::_classify_dependency_level [EXTRACTED]
- test_multiple_versions_classification -> calls -> __unresolved__::ref::versionconflict [EXTRACTED]
- test_multiple_versions_classification -> calls -> __unresolved__::ref::_classify_dependency_level [EXTRACTED]
- test_no_conflicts_classification -> calls -> __unresolved__::ref::versionconflict [EXTRACTED]
- test_no_conflicts_classification -> calls -> __unresolved__::ref::_classify_dependency_level [EXTRACTED]
- test_proposal_write_next_dependencies -> calls -> __unresolved__::ref::_get_node_dependencies [EXTRACTED]
- test_strategy_generate_dependencies -> calls -> __unresolved__::ref::_get_node_dependencies [EXTRACTED]
- test_unknown_node_dependencies -> calls -> __unresolved__::ref::_get_node_dependencies [EXTRACTED]

## Cross-Community Connections
- validate_move_and_resolve_versions -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- validate_move_and_resolve_versions -> calls -> __unresolved__::ref::append (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 validate_move_and_resolve_versions, __unresolved__::ref::_classify_dependency_level, __unresolved__::ref::versionconflict를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 test_artifact_versioning.py, version_manager.py이다.

### Key Facts
- async def validate_move_and_resolve_versions( proposal_id: UUID, target_node: str, state: ProposalState, ) -> MoveValidationResult: """ 노드 이동 검증 및 버전 충돌 감지.
- class TestDependencyClassification: """Test version conflict severity classification."""
- class TestNodeDependencies: """Test node dependency map lookups."""
- def test_missing_input_classification(self): """Missing critical input should be CRITICAL level.""" conflicts = [ VersionConflict(input_key="required", status="MISSING") ] level = _classify_dependency_level(conflicts, "test_node") assert level == DependencyLevel.CRITICAL
- def test_mixed_conflicts_critical_wins(self): """CRITICAL level should override others.""" conflicts = [ VersionConflict(input_key="required", status="MISSING"), VersionConflict(input_key="optional", versions=[1, 2], status="MULTIPLE"), ] level = _classify_dependency_level(conflicts, "test_node")…
