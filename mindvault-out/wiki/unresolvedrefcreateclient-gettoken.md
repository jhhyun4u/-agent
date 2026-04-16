# __unresolved__::ref::create_client & _get_token
Cohesion: 0.67 | Nodes: 4

## Key Nodes
- **__unresolved__::ref::create_client** () -- 3 connections
  - <- calls <- [[diagnose]]
  - <- calls <- [[gettoken]]
  - <- calls <- [[gettoken]]
- **_get_token** (C:\project\tenopa proposer\scripts\e2e_interrupt_test.py) -- 3 connections
  - -> calls -> [[unresolvedrefcreateclient]]
  - -> calls -> [[unresolvedrefsigninwithpassword]]
  - <- contains <- [[e2einterrupttest]]
- **_get_token** (C:\project\tenopa proposer\scripts\e2e_workflow_test.py) -- 3 connections
  - -> calls -> [[unresolvedrefcreateclient]]
  - -> calls -> [[unresolvedrefsigninwithpassword]]
  - <- contains <- [[e2eworkflowtest]]
- **__unresolved__::ref::sign_in_with_password** () -- 2 connections
  - <- calls <- [[gettoken]]
  - <- calls <- [[gettoken]]

## Internal Relationships
- _get_token -> calls -> __unresolved__::ref::create_client [EXTRACTED]
- _get_token -> calls -> __unresolved__::ref::sign_in_with_password [EXTRACTED]
- _get_token -> calls -> __unresolved__::ref::create_client [EXTRACTED]
- _get_token -> calls -> __unresolved__::ref::sign_in_with_password [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 __unresolved__::ref::create_client, _get_token, _get_token를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 e2e_interrupt_test.py, e2e_workflow_test.py이다.

### Key Facts
- async def _get_token(): """Supabase 로그인으로 토큰 발급.""" from supabase._async.client import create_client url = "https://inuuyaxddgbxexljfykg.supabase.co" key = ( "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."…
- async def _get_token(): """Supabase 로그인으로 새 토큰 발급.""" from supabase._async.client import create_client url = 'https://inuuyaxddgbxexljfykg.supabase.co' key =…
