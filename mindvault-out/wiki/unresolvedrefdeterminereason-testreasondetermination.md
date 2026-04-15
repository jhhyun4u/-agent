# __unresolved__::ref::_determine_reason & TestReasonDetermination
Cohesion: 0.60 | Nodes: 5

## Key Nodes
- **__unresolved__::ref::_determine_reason** () -- 4 connections
  - <- calls <- [[executenodeandcreateversion]]
  - <- calls <- [[testfirstrunreason]]
  - <- calls <- [[testmanualrerunreason]]
  - <- calls <- [[testrerunafterchangereason]]
- **TestReasonDetermination** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 4 connections
  - -> contains -> [[testfirstrunreason]]
  - -> contains -> [[testmanualrerunreason]]
  - -> contains -> [[testrerunafterchangereason]]
  - <- contains <- [[testartifactversioning]]
- **test_first_run_reason** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 2 connections
  - -> calls -> [[unresolvedrefdeterminereason]]
  - <- contains <- [[testreasondetermination]]
- **test_manual_rerun_reason** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 2 connections
  - -> calls -> [[unresolvedrefdeterminereason]]
  - <- contains <- [[testreasondetermination]]
- **test_rerun_after_change_reason** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 2 connections
  - -> calls -> [[unresolvedrefdeterminereason]]
  - <- contains <- [[testreasondetermination]]

## Internal Relationships
- TestReasonDetermination -> contains -> test_first_run_reason [EXTRACTED]
- TestReasonDetermination -> contains -> test_manual_rerun_reason [EXTRACTED]
- TestReasonDetermination -> contains -> test_rerun_after_change_reason [EXTRACTED]
- test_first_run_reason -> calls -> __unresolved__::ref::_determine_reason [EXTRACTED]
- test_manual_rerun_reason -> calls -> __unresolved__::ref::_determine_reason [EXTRACTED]
- test_rerun_after_change_reason -> calls -> __unresolved__::ref::_determine_reason [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 __unresolved__::ref::_determine_reason, TestReasonDetermination, test_first_run_reason를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 test_artifact_versioning.py이다.

### Key Facts
- class TestReasonDetermination: """Test version creation reason classification."""
- def test_first_run_reason(self): """Version 1 should be marked as first_run.""" reason = _determine_reason("test_node", 1, None) assert reason == "first_run"
- def test_manual_rerun_reason(self, mock_state): """Version > 1 with active versions should be manual_rerun.""" mock_state["active_versions"] = {"test_node_output": 1} reason = _determine_reason("test_node", 2, mock_state) assert reason == "manual_rerun"
- def test_rerun_after_change_reason(self): """Version > 1 without state should be rerun_after_change.""" reason = _determine_reason("test_node", 2, None) assert reason == "rerun_after_change"
