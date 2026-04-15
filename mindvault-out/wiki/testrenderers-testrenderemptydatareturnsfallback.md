# TestRenderers & test_render_empty_data_returns_fallback
Cohesion: 0.10 | Nodes: 22

## Key Nodes
- **TestRenderers** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 12 connections
  - -> contains -> [[testrenderrfpanalysis]]
  - -> contains -> [[testrendercompliancematrix]]
  - -> contains -> [[testrendergonogo]]
  - -> contains -> [[testrenderstrategy]]
  - -> contains -> [[testrenderbidplan]]
  - -> contains -> [[testrenderproposalsections]]
  - -> contains -> [[testrenderpptslides]]
  - -> contains -> [[testrenderfeedbackhistory]]
  - -> contains -> [[testrenderemptydatareturnsfallback]]
  - -> contains -> [[testrenderplansection]]
  - -> contains -> [[testrenderstoryline]]
  - <- contains <- [[testprojectarchive]]
- **test_render_empty_data_returns_fallback** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 3 connections
  - -> calls -> [[unresolvedrefrenderproposalsections]]
  - -> calls -> [[unresolvedrefrenderpptslides]]
  - <- contains <- [[testrenderers]]
- **__unresolved__::ref::_render_ppt_slides** () -- 2 connections
  - <- calls <- [[testrenderpptslides]]
  - <- calls <- [[testrenderemptydatareturnsfallback]]
- **__unresolved__::ref::_render_proposal_sections** () -- 2 connections
  - <- calls <- [[testrenderproposalsections]]
  - <- calls <- [[testrenderemptydatareturnsfallback]]
- **test_render_bid_plan** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 2 connections
  - -> calls -> [[unresolvedrefrenderbidplan]]
  - <- contains <- [[testrenderers]]
- **test_render_compliance_matrix** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 2 connections
  - -> calls -> [[unresolvedrefrendercompliancematrix]]
  - <- contains <- [[testrenderers]]
- **test_render_feedback_history** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 2 connections
  - -> calls -> [[unresolvedrefrenderfeedbackhistory]]
  - <- contains <- [[testrenderers]]
- **test_render_go_no_go** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 2 connections
  - -> calls -> [[unresolvedrefrendergonogo]]
  - <- contains <- [[testrenderers]]
- **test_render_plan_section** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 2 connections
  - -> calls -> [[unresolvedrefrenderplansection]]
  - <- contains <- [[testrenderers]]
- **test_render_ppt_slides** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 2 connections
  - -> calls -> [[unresolvedrefrenderpptslides]]
  - <- contains <- [[testrenderers]]
- **test_render_proposal_sections** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 2 connections
  - -> calls -> [[unresolvedrefrenderproposalsections]]
  - <- contains <- [[testrenderers]]
- **test_render_rfp_analysis** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 2 connections
  - -> calls -> [[unresolvedrefrenderrfpanalysis]]
  - <- contains <- [[testrenderers]]
- **test_render_storyline** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 2 connections
  - -> calls -> [[unresolvedrefrenderstoryline]]
  - <- contains <- [[testrenderers]]
- **test_render_strategy** (C:\project\tenopa proposer\-agent-master\tests\test_project_archive.py) -- 2 connections
  - -> calls -> [[unresolvedrefrenderstrategy]]
  - <- contains <- [[testrenderers]]
- **__unresolved__::ref::_render_bid_plan** () -- 1 connections
  - <- calls <- [[testrenderbidplan]]
- **__unresolved__::ref::_render_compliance_matrix** () -- 1 connections
  - <- calls <- [[testrendercompliancematrix]]
- **__unresolved__::ref::_render_feedback_history** () -- 1 connections
  - <- calls <- [[testrenderfeedbackhistory]]
- **__unresolved__::ref::_render_go_no_go** () -- 1 connections
  - <- calls <- [[testrendergonogo]]
- **__unresolved__::ref::_render_plan_section** () -- 1 connections
  - <- calls <- [[testrenderplansection]]
- **__unresolved__::ref::_render_rfp_analysis** () -- 1 connections
  - <- calls <- [[testrenderrfpanalysis]]
- **__unresolved__::ref::_render_storyline** () -- 1 connections
  - <- calls <- [[testrenderstoryline]]
- **__unresolved__::ref::_render_strategy** () -- 1 connections
  - <- calls <- [[testrenderstrategy]]

## Internal Relationships
- TestRenderers -> contains -> test_render_rfp_analysis [EXTRACTED]
- TestRenderers -> contains -> test_render_compliance_matrix [EXTRACTED]
- TestRenderers -> contains -> test_render_go_no_go [EXTRACTED]
- TestRenderers -> contains -> test_render_strategy [EXTRACTED]
- TestRenderers -> contains -> test_render_bid_plan [EXTRACTED]
- TestRenderers -> contains -> test_render_proposal_sections [EXTRACTED]
- TestRenderers -> contains -> test_render_ppt_slides [EXTRACTED]
- TestRenderers -> contains -> test_render_feedback_history [EXTRACTED]
- TestRenderers -> contains -> test_render_empty_data_returns_fallback [EXTRACTED]
- TestRenderers -> contains -> test_render_plan_section [EXTRACTED]
- TestRenderers -> contains -> test_render_storyline [EXTRACTED]
- test_render_bid_plan -> calls -> __unresolved__::ref::_render_bid_plan [EXTRACTED]
- test_render_compliance_matrix -> calls -> __unresolved__::ref::_render_compliance_matrix [EXTRACTED]
- test_render_empty_data_returns_fallback -> calls -> __unresolved__::ref::_render_proposal_sections [EXTRACTED]
- test_render_empty_data_returns_fallback -> calls -> __unresolved__::ref::_render_ppt_slides [EXTRACTED]
- test_render_feedback_history -> calls -> __unresolved__::ref::_render_feedback_history [EXTRACTED]
- test_render_go_no_go -> calls -> __unresolved__::ref::_render_go_no_go [EXTRACTED]
- test_render_plan_section -> calls -> __unresolved__::ref::_render_plan_section [EXTRACTED]
- test_render_ppt_slides -> calls -> __unresolved__::ref::_render_ppt_slides [EXTRACTED]
- test_render_proposal_sections -> calls -> __unresolved__::ref::_render_proposal_sections [EXTRACTED]
- test_render_rfp_analysis -> calls -> __unresolved__::ref::_render_rfp_analysis [EXTRACTED]
- test_render_storyline -> calls -> __unresolved__::ref::_render_storyline [EXTRACTED]
- test_render_strategy -> calls -> __unresolved__::ref::_render_strategy [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 TestRenderers, test_render_empty_data_returns_fallback, __unresolved__::ref::_render_ppt_slides를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 test_project_archive.py이다.

### Key Facts
- class TestRenderers: """State → Markdown 렌더링 검증."""
- def test_render_empty_data_returns_fallback(self): from app.services.project_archive_service import _render_proposal_sections, _render_ppt_slides assert "(섹션 없음)" in _render_proposal_sections(None) assert "(슬라이드 없음)" in _render_ppt_slides(None)
- def test_render_bid_plan(self): from app.services.project_archive_service import _render_bid_plan data = { "recommended_bid": 450000000, "recommended_ratio": 0.9, "win_probability": 0.72, "data_quality": "market_based", "scenarios": [{"name": "보수적", "price": 460000000}], "cost_breakdown": {"인건비":…
- def test_render_compliance_matrix(self): from app.services.project_archive_service import _render_compliance_matrix data = [ {"req_id": "R-001", "content": "PM 10년 경력", "source_step": "rfp", "status": "충족", "proposal_section": "4.1"}, {"req_id": "R-002", "content": "보안 인증", "source_step": "rfp",…
- def test_render_feedback_history(self): from app.services.project_archive_service import _render_feedback_history data = [ {"step": "strategy", "color": "YELLOW", "feedback": "가격 전략 보완 필요"}, ] md = _render_feedback_history(data) assert "피드백 #1" in md assert "YELLOW" in md
