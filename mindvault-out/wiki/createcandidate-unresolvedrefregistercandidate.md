# create_candidate & __unresolved__::ref::register_candidate
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **create_candidate** (C:\project\tenopa proposer\-agent-master\app\services\prompt_evolution.py) -- 2 connections
  - -> calls -> [[unresolvedrefregistercandidate]]
  - <- contains <- [[promptevolution]]
- **__unresolved__::ref::register_candidate** () -- 1 connections
  - <- calls <- [[createcandidate]]

## Internal Relationships
- create_candidate -> calls -> __unresolved__::ref::register_candidate [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 create_candidate, __unresolved__::ref::register_candidate를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 prompt_evolution.py이다.

### Key Facts
- async def create_candidate(prompt_id: str, text: str, reason: str) -> Optional[int]: """후보 프롬프트 등록 (레지스트리 위임).""" from app.services.prompt_registry import register_candidate return await register_candidate(prompt_id, text, reason)
