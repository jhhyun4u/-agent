# __unresolved__::ref::render_artifact & TestRenderArtifact
Cohesion: 0.53 | Nodes: 6

## Key Nodes
- **__unresolved__::ref::render_artifact** () -- 6 connections
  - <- calls <- [[rfpanalyze]]
  - <- calls <- [[snapshotfromstate]]
  - <- calls <- [[testrenderrfpraw]]
  - <- calls <- [[testrendermissingstatereturnsnone]]
  - <- calls <- [[testrenderplansubkey]]
  - <- calls <- [[testrenderalldefswithdata]]
- **TestRenderArtifact** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 5 connections
  - -> contains -> [[testrenderrfpraw]]
  - -> contains -> [[testrendermissingstatereturnsnone]]
  - -> contains -> [[testrenderplansubkey]]
  - -> contains -> [[testrenderalldefswithdata]]
  - <- contains <- [[testprojectarchive]]
- **test_render_all_defs_with_data** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 4 connections
  - -> calls -> [[unresolvedrefrenderartifact]]
  - -> calls -> [[unresolvedrefisinstance]]
  - -> calls -> [[unresolvedreflen]]
  - <- contains <- [[testrenderartifact]]
- **test_render_missing_state_returns_none** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 2 connections
  - -> calls -> [[unresolvedrefrenderartifact]]
  - <- contains <- [[testrenderartifact]]
- **test_render_plan_sub_key** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 2 connections
  - -> calls -> [[unresolvedrefrenderartifact]]
  - <- contains <- [[testrenderartifact]]
- **test_render_rfp_raw** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 2 connections
  - -> calls -> [[unresolvedrefrenderartifact]]
  - <- contains <- [[testrenderartifact]]

## Internal Relationships
- TestRenderArtifact -> contains -> test_render_rfp_raw [EXTRACTED]
- TestRenderArtifact -> contains -> test_render_missing_state_returns_none [EXTRACTED]
- TestRenderArtifact -> contains -> test_render_plan_sub_key [EXTRACTED]
- TestRenderArtifact -> contains -> test_render_all_defs_with_data [EXTRACTED]
- test_render_all_defs_with_data -> calls -> __unresolved__::ref::render_artifact [EXTRACTED]
- test_render_missing_state_returns_none -> calls -> __unresolved__::ref::render_artifact [EXTRACTED]
- test_render_plan_sub_key -> calls -> __unresolved__::ref::render_artifact [EXTRACTED]
- test_render_rfp_raw -> calls -> __unresolved__::ref::render_artifact [EXTRACTED]

## Cross-Community Connections
- test_render_all_defs_with_data -> calls -> __unresolved__::ref::isinstance (-> [[unresolvedrefget-unresolvedreflen]])
- test_render_all_defs_with_data -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 __unresolved__::ref::render_artifact, TestRenderArtifact, test_render_all_defs_with_data를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 test_project_archive.py이다.

### Key Facts
- class TestRenderArtifact: """ARCHIVE_DEFS + state → render_artifact 통합."""
- def test_render_all_defs_with_data(self): """모든 ARCHIVE_DEFS에 대해 데이터가 있을 때 렌더링 성공.""" from app.services.project_archive_service import render_artifact, ARCHIVE_DEFS
- def test_render_missing_state_returns_none(self): from app.services.project_archive_service import render_artifact, _DEF_MAP state = {} result = render_artifact(_DEF_MAP["rfp_raw_text"], state) assert result is None
- def test_render_plan_sub_key(self): from app.services.project_archive_service import render_artifact, _DEF_MAP state = {"plan": {"team": [{"name": "PM"}], "schedule": {}, "storylines": {}, "bid_price": {}}} result = render_artifact(_DEF_MAP["team_plan"], state) assert result is not None assert…
- def test_render_rfp_raw(self): from app.services.project_archive_service import render_artifact, _DEF_MAP state = {"rfp_raw": "RFP 원문 텍스트 내용입니다."} result = render_artifact(_DEF_MAP["rfp_raw_text"], state) assert "RFP 원문" in result
