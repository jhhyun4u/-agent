# StateMachine & __unresolved__::ref::transition
Cohesion: 0.24 | Nodes: 15

## Key Nodes
- **StateMachine** (C:\project\tenopa proposer\app\state_machine.py) -- 14 connections
  - -> contains -> [[init]]
  - -> contains -> [[startworkflow]]
  - -> contains -> [[decidego]]
  - -> contains -> [[decidenogo]]
  - -> contains -> [[submit]]
  - -> contains -> [[present]]
  - -> contains -> [[recordwin]]
  - -> contains -> [[recordloss]]
  - -> contains -> [[abandon]]
  - -> contains -> [[hold]]
  - -> contains -> [[resume]]
  - -> contains -> [[archive]]
  - -> contains -> [[markexpired]]
  - <- contains <- [[statemachine]]
- **__unresolved__::ref::transition** () -- 12 connections
  - <- calls <- [[startworkflow]]
  - <- calls <- [[decidego]]
  - <- calls <- [[decidenogo]]
  - <- calls <- [[submit]]
  - <- calls <- [[present]]
  - <- calls <- [[recordwin]]
  - <- calls <- [[recordloss]]
  - <- calls <- [[abandon]]
  - <- calls <- [[hold]]
  - <- calls <- [[resume]]
  - <- calls <- [[archive]]
  - <- calls <- [[markexpired]]
- **abandon** (C:\project\tenopa proposer\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **archive** (C:\project\tenopa proposer\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **decide_go** (C:\project\tenopa proposer\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **decide_no_go** (C:\project\tenopa proposer\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **hold** (C:\project\tenopa proposer\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **mark_expired** (C:\project\tenopa proposer\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **present** (C:\project\tenopa proposer\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **record_loss** (C:\project\tenopa proposer\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **record_win** (C:\project\tenopa proposer\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **resume** (C:\project\tenopa proposer\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **start_workflow** (C:\project\tenopa proposer\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **submit** (C:\project\tenopa proposer\app\state_machine.py) -- 2 connections
  - -> calls -> [[unresolvedreftransition]]
  - <- contains <- [[statemachine]]
- **__init__** (C:\project\tenopa proposer\app\state_machine.py) -- 1 connections
  - <- contains <- [[statemachine]]

## Internal Relationships
- StateMachine -> contains -> __init__ [EXTRACTED]
- StateMachine -> contains -> start_workflow [EXTRACTED]
- StateMachine -> contains -> decide_go [EXTRACTED]
- StateMachine -> contains -> decide_no_go [EXTRACTED]
- StateMachine -> contains -> submit [EXTRACTED]
- StateMachine -> contains -> present [EXTRACTED]
- StateMachine -> contains -> record_win [EXTRACTED]
- StateMachine -> contains -> record_loss [EXTRACTED]
- StateMachine -> contains -> abandon [EXTRACTED]
- StateMachine -> contains -> hold [EXTRACTED]
- StateMachine -> contains -> resume [EXTRACTED]
- StateMachine -> contains -> archive [EXTRACTED]
- StateMachine -> contains -> mark_expired [EXTRACTED]
- abandon -> calls -> __unresolved__::ref::transition [EXTRACTED]
- archive -> calls -> __unresolved__::ref::transition [EXTRACTED]
- decide_go -> calls -> __unresolved__::ref::transition [EXTRACTED]
- decide_no_go -> calls -> __unresolved__::ref::transition [EXTRACTED]
- hold -> calls -> __unresolved__::ref::transition [EXTRACTED]
- mark_expired -> calls -> __unresolved__::ref::transition [EXTRACTED]
- present -> calls -> __unresolved__::ref::transition [EXTRACTED]
- record_loss -> calls -> __unresolved__::ref::transition [EXTRACTED]
- record_win -> calls -> __unresolved__::ref::transition [EXTRACTED]
- resume -> calls -> __unresolved__::ref::transition [EXTRACTED]
- start_workflow -> calls -> __unresolved__::ref::transition [EXTRACTED]
- submit -> calls -> __unresolved__::ref::transition [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 StateMachine, __unresolved__::ref::transition, abandon를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 state_machine.py이다.

### Key Facts
- class StateMachine: """ Business-level state machine for proposals.
- async def abandon( self, user_id: str, reason: str = "", ) -> dict: """ Abandon proposal (any state → closed with win_result='abandoned').
- async def archive( self, user_id: Optional[str] = None, ) -> dict: """ Archive closed proposal (closed → archived).
- Wraps StateValidator to provide convenient methods for common transitions: - start_workflow() → in_progress - decide_go() → in_progress (from analyzing) - decide_no_go() → on_hold or closed - submit() → submitted - present() → presentation - record_win() → closed (won) - record_loss() → closed…
- Wraps StateValidator to provide convenient methods for common transitions: - start_workflow() → in_progress - decide_go() → in_progress (from analyzing) - decide_no_go() → on_hold or closed - submit() → submitted - present() → presentation - record_win() → closed (won) - record_loss() → closed…
