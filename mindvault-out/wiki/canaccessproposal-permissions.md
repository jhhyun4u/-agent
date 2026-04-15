# can_access_proposal & permissions
Cohesion: 0.48 | Nodes: 7

## Key Nodes
- **can_access_proposal** (C:\project\tenopa proposer\-agent-master\app\api\permissions.py) -- 10 connections
  - -> calls -> [[unresolvedrefexecute]]
  - -> calls -> [[unresolvedrefmaybesingle]]
  - -> calls -> [[unresolvedrefeq]]
  - -> calls -> [[unresolvedrefselect]]
  - -> calls -> [[unresolvedreftable]]
  - -> calls -> [[unresolvedrefpropnotfounderror]]
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefgetteammemberrole]]
  - -> calls -> [[unresolvedrefteamaccessdeniederror]]
  - <- contains <- [[permissions]]
- **permissions** (C:\project\tenopa proposer\-agent-master\app\api\permissions.py) -- 7 connections
  - -> contains -> [[getteammemberrole]]
  - -> contains -> [[requireteammember]]
  - -> contains -> [[requireteamadmin]]
  - -> contains -> [[getuserteamids]]
  - -> contains -> [[canaccessproposal]]
  - -> imports -> [[unresolvedreftyping]]
  - -> imports -> [[unresolvedrefexceptions]]
- **__unresolved__::ref::get_team_member_role** () -- 3 connections
  - <- calls <- [[requireteammember]]
  - <- calls <- [[requireteamadmin]]
  - <- calls <- [[canaccessproposal]]
- **__unresolved__::ref::propnotfounderror** () -- 3 connections
  - <- calls <- [[requireprojectaccess]]
  - <- calls <- [[canaccessproposal]]
  - <- calls <- [[getproposalor404]]
- **__unresolved__::ref::teamaccessdeniederror** () -- 3 connections
  - <- calls <- [[requireteammember]]
  - <- calls <- [[requireteamadmin]]
  - <- calls <- [[canaccessproposal]]
- **require_team_admin** (C:\project\tenopa proposer\-agent-master\app\api\permissions.py) -- 3 connections
  - -> calls -> [[unresolvedrefgetteammemberrole]]
  - -> calls -> [[unresolvedrefteamaccessdeniederror]]
  - <- contains <- [[permissions]]
- **require_team_member** (C:\project\tenopa proposer\-agent-master\app\api\permissions.py) -- 3 connections
  - -> calls -> [[unresolvedrefgetteammemberrole]]
  - -> calls -> [[unresolvedrefteamaccessdeniederror]]
  - <- contains <- [[permissions]]

## Internal Relationships
- can_access_proposal -> calls -> __unresolved__::ref::propnotfounderror [EXTRACTED]
- can_access_proposal -> calls -> __unresolved__::ref::get_team_member_role [EXTRACTED]
- can_access_proposal -> calls -> __unresolved__::ref::teamaccessdeniederror [EXTRACTED]
- require_team_admin -> calls -> __unresolved__::ref::get_team_member_role [EXTRACTED]
- require_team_admin -> calls -> __unresolved__::ref::teamaccessdeniederror [EXTRACTED]
- require_team_member -> calls -> __unresolved__::ref::get_team_member_role [EXTRACTED]
- require_team_member -> calls -> __unresolved__::ref::teamaccessdeniederror [EXTRACTED]
- permissions -> contains -> require_team_member [EXTRACTED]
- permissions -> contains -> require_team_admin [EXTRACTED]
- permissions -> contains -> can_access_proposal [EXTRACTED]

## Cross-Community Connections
- can_access_proposal -> calls -> __unresolved__::ref::execute (-> [[unresolvedrefget-unresolvedreflen]])
- can_access_proposal -> calls -> __unresolved__::ref::maybe_single (-> [[unresolvedrefget-unresolvedreflen]])
- can_access_proposal -> calls -> __unresolved__::ref::eq (-> [[unresolvedrefget-unresolvedreflen]])
- can_access_proposal -> calls -> __unresolved__::ref::select (-> [[unresolvedrefget-unresolvedreflen]])
- can_access_proposal -> calls -> __unresolved__::ref::table (-> [[unresolvedrefget-unresolvedreflen]])
- can_access_proposal -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- permissions -> contains -> get_team_member_role (-> [[unresolvedrefget-unresolvedreflen]])
- permissions -> contains -> get_user_team_ids (-> [[unresolvedrefget-unresolvedreflen]])
- permissions -> imports -> __unresolved__::ref::typing (-> [[unresolvedrefbasemodel-unresolvedreflogging]])
- permissions -> imports -> __unresolved__::ref::exceptions (-> [[unresolvedrefbasemodel-unresolvedreflogging]])

## Context
이 커뮤니티는 can_access_proposal, permissions, __unresolved__::ref::get_team_member_role를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 permissions.py이다.

### Key Facts
- async def can_access_proposal(client, proposal_id: str, user_id: str) -> dict: """소유자이거나 팀 멤버이면 제안서 dict 반환, 아니면 403.""" res = ( await client.table("proposals") .select("*") .eq("id", proposal_id) .maybe_single() .execute() ) if not res.data: raise PropNotFoundError(proposal_id) proposal = res.data…
- async def require_team_admin(client, team_id: str, user_id: str): """팀 관리자 확인. admin이 아니면 403.""" role = await get_team_member_role(client, team_id, user_id) if role != "admin": raise TeamAccessDeniedError("팀 관리자만 가능합니다.")
- async def require_team_member(client, team_id: str, user_id: str) -> str: """팀 멤버 확인. 미소속이면 403. 역할 문자열 반환.""" role = await get_team_member_role(client, team_id, user_id) if role is None: raise TeamAccessDeniedError() return role
