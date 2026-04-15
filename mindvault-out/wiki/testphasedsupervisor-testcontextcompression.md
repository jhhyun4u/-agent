# test_phased_supervisor & test_context_compression
Cohesion: 0.19 | Nodes: 14

## Key Nodes
- **test_phased_supervisor** (C:\project\tenopa proposer\-agent-master\tests\integration\test_phased_supervisor.py) -- 10 connections
  - -> contains -> [[testphasedgraphstructure]]
  - -> contains -> [[testphasestatetransitions]]
  - -> contains -> [[testhitllogic]]
  - -> contains -> [[testphase5qualityloop]]
  - -> contains -> [[testcontextcompression]]
  - -> contains -> [[main]]
  - -> imports -> [[unresolvedrefasyncio]]
  - -> imports -> [[unresolvedrefphasedstate]]
  - -> imports -> [[unresolvedrefphasedsupervisor]]
  - -> imports -> [[unresolvedrefhitlgates]]
- **test_context_compression** (C:\project\tenopa proposer\-agent-master\tests\integration\test_phased_supervisor.py) -- 9 connections
  - -> calls -> [[unresolvedrefprint]]
  - -> calls -> [[unresolvedrefcreatemockartifact1]]
  - -> calls -> [[unresolvedrefcreatemockartifact2]]
  - -> calls -> [[unresolvedrefcreatemockartifact3]]
  - -> calls -> [[unresolvedrefcreatemockartifact4]]
  - -> calls -> [[unresolvedrefenumerate]]
  - -> calls -> [[unresolvedrefstr]]
  - -> calls -> [[unresolvedreflen]]
  - <- contains <- [[testphasedsupervisor]]
- **test_hitl_logic** (C:\project\tenopa proposer\-agent-master\tests\integration\test_phased_supervisor.py) -- 7 connections
  - -> calls -> [[unresolvedrefprint]]
  - -> calls -> [[unresolvedrefinitializephasedsupervisorstate]]
  - -> calls -> [[unresolvedrefcreatemockartifact1]]
  - -> calls -> [[unresolvedrefcreatemockartifact2]]
  - -> calls -> [[unresolvedrefevaluatehitlgate]]
  - -> calls -> [[unresolvedrefcreatemockartifact3]]
  - <- contains <- [[testphasedsupervisor]]
- **test_phase5_quality_loop** (C:\project\tenopa proposer\-agent-master\tests\integration\test_phased_supervisor.py) -- 4 connections
  - -> calls -> [[unresolvedrefprint]]
  - -> calls -> [[unresolvedrefinitializephasedsupervisorstate]]
  - -> calls -> [[unresolvedrefdecidequalityaction]]
  - <- contains <- [[testphasedsupervisor]]
- **__unresolved__::ref::initialize_phased_supervisor_state** () -- 3 connections
  - <- calls <- [[testphasestatetransitions]]
  - <- calls <- [[testhitllogic]]
  - <- calls <- [[testphase5qualityloop]]
- **__unresolved__::ref::create_mock_artifact_1** () -- 2 connections
  - <- calls <- [[testhitllogic]]
  - <- calls <- [[testcontextcompression]]
- **__unresolved__::ref::create_mock_artifact_2** () -- 2 connections
  - <- calls <- [[testhitllogic]]
  - <- calls <- [[testcontextcompression]]
- **__unresolved__::ref::create_mock_artifact_3** () -- 2 connections
  - <- calls <- [[testhitllogic]]
  - <- calls <- [[testcontextcompression]]
- **__unresolved__::ref::create_mock_artifact_4** () -- 1 connections
  - <- calls <- [[testcontextcompression]]
- **__unresolved__::ref::decide_quality_action** () -- 1 connections
  - <- calls <- [[testphase5qualityloop]]
- **__unresolved__::ref::evaluate_hitl_gate** () -- 1 connections
  - <- calls <- [[testhitllogic]]
- **__unresolved__::ref::hitl_gates** () -- 1 connections
  - <- imports <- [[testphasedsupervisor]]
- **__unresolved__::ref::phased_state** () -- 1 connections
  - <- imports <- [[testphasedsupervisor]]
- **__unresolved__::ref::phased_supervisor** () -- 1 connections
  - <- imports <- [[testphasedsupervisor]]

## Internal Relationships
- test_context_compression -> calls -> __unresolved__::ref::create_mock_artifact_1 [EXTRACTED]
- test_context_compression -> calls -> __unresolved__::ref::create_mock_artifact_2 [EXTRACTED]
- test_context_compression -> calls -> __unresolved__::ref::create_mock_artifact_3 [EXTRACTED]
- test_context_compression -> calls -> __unresolved__::ref::create_mock_artifact_4 [EXTRACTED]
- test_hitl_logic -> calls -> __unresolved__::ref::initialize_phased_supervisor_state [EXTRACTED]
- test_hitl_logic -> calls -> __unresolved__::ref::create_mock_artifact_1 [EXTRACTED]
- test_hitl_logic -> calls -> __unresolved__::ref::create_mock_artifact_2 [EXTRACTED]
- test_hitl_logic -> calls -> __unresolved__::ref::evaluate_hitl_gate [EXTRACTED]
- test_hitl_logic -> calls -> __unresolved__::ref::create_mock_artifact_3 [EXTRACTED]
- test_phase5_quality_loop -> calls -> __unresolved__::ref::initialize_phased_supervisor_state [EXTRACTED]
- test_phase5_quality_loop -> calls -> __unresolved__::ref::decide_quality_action [EXTRACTED]
- test_phased_supervisor -> contains -> test_hitl_logic [EXTRACTED]
- test_phased_supervisor -> contains -> test_phase5_quality_loop [EXTRACTED]
- test_phased_supervisor -> contains -> test_context_compression [EXTRACTED]
- test_phased_supervisor -> imports -> __unresolved__::ref::phased_state [EXTRACTED]
- test_phased_supervisor -> imports -> __unresolved__::ref::phased_supervisor [EXTRACTED]
- test_phased_supervisor -> imports -> __unresolved__::ref::hitl_gates [EXTRACTED]

## Cross-Community Connections
- test_context_compression -> calls -> __unresolved__::ref::print (-> [[unresolvedrefget-unresolvedreflen]])
- test_context_compression -> calls -> __unresolved__::ref::enumerate (-> [[unresolvedrefget-unresolvedreflen]])
- test_context_compression -> calls -> __unresolved__::ref::str (-> [[unresolvedrefget-unresolvedreflen]])
- test_context_compression -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedreflen]])
- test_hitl_logic -> calls -> __unresolved__::ref::print (-> [[unresolvedrefget-unresolvedreflen]])
- test_phase5_quality_loop -> calls -> __unresolved__::ref::print (-> [[unresolvedrefget-unresolvedreflen]])
- test_phased_supervisor -> contains -> test_phased_graph_structure (-> [[unresolvedrefget-unresolvedreflen]])
- test_phased_supervisor -> contains -> test_phase_state_transitions (-> [[unresolvedrefget-unresolvedreflen]])
- test_phased_supervisor -> contains -> main (-> [[unresolvedrefget-unresolvedreflen]])
- test_phased_supervisor -> imports -> __unresolved__::ref::asyncio (-> [[unresolvedrefbasemodel-unresolvedreflogging]])

## Context
이 커뮤니티는 test_phased_supervisor, test_context_compression, test_hitl_logic를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 test_phased_supervisor.py이다.

### Key Facts
- async def test_context_compression(): """ 테스트 5: Phase 경계 컨텍스트 압축 (C-2) 각 Phase 완료 후: - Artifact로 압축 (8K~15K 토큰) - phase_working_state = {} (비움) - proposal_state에만 보관 (v3.0 호환) """ print("\n" + "=" * 60) print("🧪 테스트 5: 컨텍스트 압축 (Phase 경계)") print("=" * 60)
- async def test_hitl_logic(): """ 테스트 3: HITL 게이트 조건부 로직 검증 Gate #1, #2, #4: 조건부 (auto_pass 가능) Gate #3, #5: ★필수 (require_human) """ print("\n" + "=" * 60) print("🧪 테스트 3: HITL 게이트 조건부 로직") print("=" * 60)
- async def test_phase5_quality_loop(): """ 테스트 4: Phase 5 품질 루프 (C-3 Fix) critique → [라우팅] → revise | pass | escalate """ print("\n" + "=" * 60) print("🧪 테스트 4: Phase 5 품질 루프 라우팅") print("=" * 60)
