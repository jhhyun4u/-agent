# StateMachine & __unresolved__::ref::transition
Cohesion: 0.25 | Nodes: 15

## Key Nodes
- **StateMachine** (C:\project\tenopa proposer\-agent-master\app\state_machine.py) -- 12 connections
  - -> contains -> [[init]]
  - -> contains -> [[startworkflow]]
  - -> contains -> [[completeproposal]]
  - -> contains -> [[submitproposal]]
  - -> contains -> [[markpresentation]]
  - -> contains -> [[closeproposal]]
  - -> contains -> [[holdproposal]]
  - -> contains -> [[resumeproposal]]
  - -> contains -> [[archiveproposal]]
  - -> contains -> [[expireproposal]]
  - -> contains -> [[transition]]
  - <- contains <- [[statemachine]]
- **__unresolved__::ref::transition** () -- 10 connections
  - <- calls <- [[startworkflow]]
  - <- calls <- [[completeproposal]]
  - <- calls <- [[submitproposal]]
  - <- calls <- [[markpresentation]]
  - <- calls <- [[closeproposal]]
  - <- calls <- [[holdproposal]]
  - <- calls <- [[resumeproposal]]
  - <- calls <- [[archiveproposal]]
  - <- calls <- [[expireproposal]]
  - <- calls <- [[transition]]
- **close_proposal** (C:\project\tenopa proposer\-agent-master\app\state_machine.py) -- 7 connections
  - -> calls -> [[unresolvedrefwinresult]]
  - -> calls -> [[unresolvedrefvalueerror]]
  - -> calls -> [[unresolvedrefbuildmetadata]]
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefinfo]]
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **__unresolved__::ref::_build_metadata** () -- 4 connections
  - <- calls <- [[completeproposal]]
  - <- calls <- [[submitproposal]]
  - <- calls <- [[markpresentation]]
  - <- calls <- [[closeproposal]]
- **complete_proposal** (C:\project\tenopa proposer\-agent-master\app\state_machine.py) -- 3 connections
  - -> calls -> [[unresolvedrefbuildmetadata]]
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **mark_presentation** (C:\project\tenopa proposer\-agent-master\app\state_machine.py) -- 3 connections
  - -> calls -> [[unresolvedrefbuildmetadata]]
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **resume_proposal** (C:\project\tenopa proposer\-agent-master\app\state_machine.py) -- 3 connections
  - -> calls -> [[unresolvedrefvalueerror]]
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **submit_proposal** (C:\project\tenopa proposer\-agent-master\app\state_machine.py) -- 3 connections
  - -> calls -> [[unresolvedrefbuildmetadata]]
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **archive_proposal** (C:\project\tenopa proposer\-agent-master\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **expire_proposal** (C:\project\tenopa proposer\-agent-master\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **hold_proposal** (C:\project\tenopa proposer\-agent-master\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **start_workflow** (C:\project\tenopa proposer\-agent-master\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **transition** (C:\project\tenopa proposer\-agent-master\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **__unresolved__::ref::winresult** () -- 1 connections
  - <- calls <- [[closeproposal]]
- **__init__** (C:\project\tenopa proposer\-agent-master\app\state_machine.py) -- 1 connections
  - <- contains <- [[statemachine]]

## Internal Relationships
- StateMachine -> contains -> __init__ [EXTRACTED]
- StateMachine -> contains -> start_workflow [EXTRACTED]
- StateMachine -> contains -> complete_proposal [EXTRACTED]
- StateMachine -> contains -> submit_proposal [EXTRACTED]
- StateMachine -> contains -> mark_presentation [EXTRACTED]
- StateMachine -> contains -> close_proposal [EXTRACTED]
- StateMachine -> contains -> hold_proposal [EXTRACTED]
- StateMachine -> contains -> resume_proposal [EXTRACTED]
- StateMachine -> contains -> archive_proposal [EXTRACTED]
- StateMachine -> contains -> expire_proposal [EXTRACTED]
- StateMachine -> contains -> transition [EXTRACTED]
- archive_proposal -> calls -> __unresolved__::ref::transition [EXTRACTED]
- close_proposal -> calls -> __unresolved__::ref::winresult [EXTRACTED]
- close_proposal -> calls -> __unresolved__::ref::_build_metadata [EXTRACTED]
- close_proposal -> calls -> __unresolved__::ref::transition [EXTRACTED]
- complete_proposal -> calls -> __unresolved__::ref::_build_metadata [EXTRACTED]
- complete_proposal -> calls -> __unresolved__::ref::transition [EXTRACTED]
- expire_proposal -> calls -> __unresolved__::ref::transition [EXTRACTED]
- hold_proposal -> calls -> __unresolved__::ref::transition [EXTRACTED]
- mark_presentation -> calls -> __unresolved__::ref::_build_metadata [EXTRACTED]
- mark_presentation -> calls -> __unresolved__::ref::transition [EXTRACTED]
- resume_proposal -> calls -> __unresolved__::ref::transition [EXTRACTED]
- start_workflow -> calls -> __unresolved__::ref::transition [EXTRACTED]
- submit_proposal -> calls -> __unresolved__::ref::_build_metadata [EXTRACTED]
- submit_proposal -> calls -> __unresolved__::ref::transition [EXTRACTED]
- transition -> calls -> __unresolved__::ref::transition [EXTRACTED]

## Cross-Community Connections
- close_proposal -> calls -> __unresolved__::ref::valueerror (-> [[unresolvedrefget-unresolvedreflen]])
- close_proposal -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- close_proposal -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedreflen]])
- resume_proposal -> calls -> __unresolved__::ref::valueerror (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 StateMachine, __unresolved__::ref::transition, close_proposal를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 state_machine.py이다.

### Key Facts
- StateMachine: StateValidator를 래핑한 비즈니스 친화적 상태 관리 - start_workflow()     → waiting → in_progress - complete_proposal()  → in_progress → completed - submit_proposal()    → completed → submitted - mark_presentation()  → submitted → presentation - close_proposal()     → * → closed  (win_result 필수) -…
- StateMachine: StateValidator를 래핑한 비즈니스 친화적 상태 관리 - start_workflow()     → waiting → in_progress - complete_proposal()  → in_progress → completed - submit_proposal()    → completed → submitted - mark_presentation()  → submitted → presentation - close_proposal()     → * → closed  (win_result 필수) -…
- StateMachine: StateValidator를 래핑한 비즈니스 친화적 상태 관리 - start_workflow()     → waiting → in_progress - complete_proposal()  → in_progress → completed - submit_proposal()    → completed → submitted - mark_presentation()  → submitted → presentation - close_proposal()     → * → closed  (win_result 필수) -…
- StateMachine: StateValidator를 래핑한 비즈니스 친화적 상태 관리 - start_workflow()     → waiting → in_progress - complete_proposal()  → in_progress → completed - submit_proposal()    → completed → submitted - mark_presentation()  → submitted → presentation - close_proposal()     → * → closed  (win_result 필수) -…
- StateMachine: StateValidator를 래핑한 비즈니스 친화적 상태 관리 - start_workflow()     → waiting → in_progress - complete_proposal()  → in_progress → completed - submit_proposal()    → completed → submitted - mark_presentation()  → submitted → presentation - close_proposal()     → * → closed  (win_result 필수) -…
