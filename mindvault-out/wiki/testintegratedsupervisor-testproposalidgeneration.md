# TestIntegratedSupervisor & test_proposal_id_generation
Cohesion: 0.21 | Nodes: 12

## Key Nodes
- **TestIntegratedSupervisor** (C:\project\tenopa proposer\-agent-master\tests\integration\test_integrated_supervisor.py) -- 6 connections
  - -> contains -> [[testbuildsupervisor]]
  - -> contains -> [[testsupervisorstatus]]
  - -> contains -> [[testcreateinitialstate]]
  - -> contains -> [[testproposalidgeneration]]
  - -> contains -> [[teststatestructure]]
  - <- contains <- [[testintegratedsupervisor]]
- **test_proposal_id_generation** (C:\project\tenopa proposer\-agent-master\tests\integration\test_integrated_supervisor.py) -- 4 connections
  - -> calls -> [[unresolvedrefcreateinitialstate]]
  - -> calls -> [[unresolvedrefstartswith]]
  - -> calls -> [[unresolvedreflen]]
  - <- contains <- [[testintegratedsupervisor]]
- **test_integrated_supervisor** (C:\project\tenopa proposer\-agent-master\tests\integration\test_integrated_supervisor.py) -- 4 connections
  - -> contains -> [[testintegratedsupervisor]]
  - -> contains -> [[testsubagents]]
  - -> imports -> [[unresolvedrefpytest]]
  - -> imports -> [[unresolvedrefintegratedsupervisor]]
- **__unresolved__::ref::create_initial_state** () -- 3 connections
  - <- calls <- [[testcreateinitialstate]]
  - <- calls <- [[testproposalidgeneration]]
  - <- calls <- [[teststatestructure]]
- **test_supervisor_status** (C:\project\tenopa proposer\-agent-master\tests\integration\test_integrated_supervisor.py) -- 3 connections
  - -> calls -> [[unresolvedrefbuildintegratedsupervisor]]
  - -> calls -> [[unresolvedrefgetsupervisorstatus]]
  - <- contains <- [[testintegratedsupervisor]]
- **__unresolved__::ref::build_integrated_supervisor** () -- 2 connections
  - <- calls <- [[testbuildsupervisor]]
  - <- calls <- [[testsupervisorstatus]]
- **test_build_supervisor** (C:\project\tenopa proposer\-agent-master\tests\integration\test_integrated_supervisor.py) -- 2 connections
  - -> calls -> [[unresolvedrefbuildintegratedsupervisor]]
  - <- contains <- [[testintegratedsupervisor]]
- **test_create_initial_state** (C:\project\tenopa proposer\-agent-master\tests\integration\test_integrated_supervisor.py) -- 2 connections
  - -> calls -> [[unresolvedrefcreateinitialstate]]
  - <- contains <- [[testintegratedsupervisor]]
- **test_state_structure** (C:\project\tenopa proposer\-agent-master\tests\integration\test_integrated_supervisor.py) -- 2 connections
  - -> calls -> [[unresolvedrefcreateinitialstate]]
  - <- contains <- [[testintegratedsupervisor]]
- **__unresolved__::ref::get_supervisor_status** () -- 1 connections
  - <- calls <- [[testsupervisorstatus]]
- **__unresolved__::ref::integrated_supervisor** () -- 1 connections
  - <- imports <- [[testintegratedsupervisor]]
- **TestSubAgents** (C:\project\tenopa proposer\-agent-master\tests\integration\test_integrated_supervisor.py) -- 1 connections
  - <- contains <- [[testintegratedsupervisor]]

## Internal Relationships
- TestIntegratedSupervisor -> contains -> test_build_supervisor [EXTRACTED]
- TestIntegratedSupervisor -> contains -> test_supervisor_status [EXTRACTED]
- TestIntegratedSupervisor -> contains -> test_create_initial_state [EXTRACTED]
- TestIntegratedSupervisor -> contains -> test_proposal_id_generation [EXTRACTED]
- TestIntegratedSupervisor -> contains -> test_state_structure [EXTRACTED]
- test_build_supervisor -> calls -> __unresolved__::ref::build_integrated_supervisor [EXTRACTED]
- test_create_initial_state -> calls -> __unresolved__::ref::create_initial_state [EXTRACTED]
- test_proposal_id_generation -> calls -> __unresolved__::ref::create_initial_state [EXTRACTED]
- test_state_structure -> calls -> __unresolved__::ref::create_initial_state [EXTRACTED]
- test_supervisor_status -> calls -> __unresolved__::ref::build_integrated_supervisor [EXTRACTED]
- test_supervisor_status -> calls -> __unresolved__::ref::get_supervisor_status [EXTRACTED]
- test_integrated_supervisor -> contains -> TestIntegratedSupervisor [EXTRACTED]
- test_integrated_supervisor -> contains -> TestSubAgents [EXTRACTED]
- test_integrated_supervisor -> imports -> __unresolved__::ref::integrated_supervisor [EXTRACTED]

## Cross-Community Connections
- test_proposal_id_generation -> calls -> __unresolved__::ref::startswith (-> [[unresolvedrefget-unresolvedreflen]])
- test_proposal_id_generation -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedreflen]])
- test_integrated_supervisor -> imports -> __unresolved__::ref::pytest (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 TestIntegratedSupervisor, test_proposal_id_generation, test_integrated_supervisor를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 test_integrated_supervisor.py이다.

### Key Facts
- class TestIntegratedSupervisor: """통합 Supervisor 테스트 클래스"""
- def test_proposal_id_generation(self, mock_rfp): """제안서 ID 자동 생성 테스트""" state = create_initial_state(rfp_document=mock_rfp) proposal_id = state["proposal_state"]["proposal_id"]
- def test_supervisor_status(self): """Supervisor 상태 확인 테스트""" graph = build_integrated_supervisor() status = get_supervisor_status(graph)
- def test_build_supervisor(self): """Supervisor 빌드 테스트""" graph = build_integrated_supervisor() assert graph is not None
- def test_create_initial_state(self, mock_rfp, mock_company_profile): """초기 상태 생성 테스트""" state = create_initial_state( rfp_document=mock_rfp, company_profile=mock_company_profile )
