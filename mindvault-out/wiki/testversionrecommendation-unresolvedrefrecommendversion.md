# TestVersionRecommendation & __unresolved__::ref::_recommend_version
Cohesion: 0.60 | Nodes: 5

## Key Nodes
- **TestVersionRecommendation** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 4 connections
  - -> contains -> [[testrecommendactiveversion]]
  - -> contains -> [[testrecommendlatestversion]]
  - -> contains -> [[testrecommendfirstversion]]
  - <- contains <- [[testartifactversioning]]
- **__unresolved__::ref::_recommend_version** () -- 3 connections
  - <- calls <- [[testrecommendactiveversion]]
  - <- calls <- [[testrecommendlatestversion]]
  - <- calls <- [[testrecommendfirstversion]]
- **test_recommend_active_version** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 2 connections
  - -> calls -> [[unresolvedrefrecommendversion]]
  - <- contains <- [[testversionrecommendation]]
- **test_recommend_first_version** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 2 connections
  - -> calls -> [[unresolvedrefrecommendversion]]
  - <- contains <- [[testversionrecommendation]]
- **test_recommend_latest_version** (C:\project\tenopa proposer\-agent-master\tests\test_artifact_versioning.py) -- 2 connections
  - -> calls -> [[unresolvedrefrecommendversion]]
  - <- contains <- [[testversionrecommendation]]

## Internal Relationships
- TestVersionRecommendation -> contains -> test_recommend_active_version [EXTRACTED]
- TestVersionRecommendation -> contains -> test_recommend_latest_version [EXTRACTED]
- TestVersionRecommendation -> contains -> test_recommend_first_version [EXTRACTED]
- test_recommend_active_version -> calls -> __unresolved__::ref::_recommend_version [EXTRACTED]
- test_recommend_first_version -> calls -> __unresolved__::ref::_recommend_version [EXTRACTED]
- test_recommend_latest_version -> calls -> __unresolved__::ref::_recommend_version [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 TestVersionRecommendation, __unresolved__::ref::_recommend_version, test_recommend_active_version를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 test_artifact_versioning.py이다.

### Key Facts
- class TestVersionRecommendation: """Test smart version recommendation logic."""
- def test_recommend_active_version(self, mock_state): """Should recommend active version if in available list.""" mock_state["active_versions"] = {"test_key": 2} available = [1, 2, 3]
- def test_recommend_first_version(self, mock_state): """Should recommend first version if nothing else available.""" mock_state["active_versions"] = {} available = [5]
- def test_recommend_latest_version(self, mock_state): """Should recommend latest version if active not available.""" mock_state["active_versions"] = {} available = [1, 2, 3]
