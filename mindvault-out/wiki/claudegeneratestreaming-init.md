# claude_generate_streaming & __init__
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **claude_generate_streaming** (C:\project\tenopa proposer\-agent-master\app\services\claude_client.py) -- 5 connections
  - -> calls -> [[unresolvedrefgetclient]]
  - -> calls -> [[unresolvedrefstream]]
  - -> calls -> [[unresolvedrefwarning]]
  - -> calls -> [[unresolvedreferror]]
  - <- contains <- [[claudeclient]]
- **__init__** (C:\project\tenopa proposer\-agent-master\app\services\bidding\submission\__init__.py) -- 3 connections
  - -> imports -> [[unresolvedrefhandoff]]
  - -> imports -> [[unresolvedrefstream]]
  - -> imports -> [[unresolvedrefmarketresearch]]
- **__unresolved__::ref::_get_client** () -- 2 connections
  - <- calls <- [[claudegenerate]]
  - <- calls <- [[claudegeneratestreaming]]
- **__unresolved__::ref::stream** () -- 2 connections
  - <- calls <- [[claudegeneratestreaming]]
  - <- imports <- [[init]]
- **__unresolved__::ref::handoff** () -- 1 connections
  - <- imports <- [[init]]
- **__unresolved__::ref::market_research** () -- 1 connections
  - <- imports <- [[init]]

## Internal Relationships
- __init__ -> imports -> __unresolved__::ref::handoff [EXTRACTED]
- __init__ -> imports -> __unresolved__::ref::stream [EXTRACTED]
- __init__ -> imports -> __unresolved__::ref::market_research [EXTRACTED]
- claude_generate_streaming -> calls -> __unresolved__::ref::_get_client [EXTRACTED]
- claude_generate_streaming -> calls -> __unresolved__::ref::stream [EXTRACTED]

## Cross-Community Connections
- claude_generate_streaming -> calls -> __unresolved__::ref::warning (-> [[unresolvedrefget-unresolvedreflen]])
- claude_generate_streaming -> calls -> __unresolved__::ref::error (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 claude_generate_streaming, __init__, __unresolved__::ref::_get_client를 중심으로 imports 관계로 연결되어 있다. 주요 소스 파일은 __init__.py, claude_client.py이다.

### Key Facts
- async def claude_generate_streaming( prompt: str, system_prompt: str = "", model: str | None = None, max_tokens: int | None = None, ): """Claude API 스트리밍 호출 — SSE 이벤트 생성기.""" client = _get_client() model = model or settings.claude_model max_tokens = max_tokens or settings.max_output_tokens
