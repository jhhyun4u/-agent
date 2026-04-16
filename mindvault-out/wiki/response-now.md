# response & _now
Cohesion: 0.50 | Nodes: 5

## Key Nodes
- **response** (C:\project\tenopa proposer\app\api\response.py) -- 5 connections
  - -> contains -> [[ok]]
  - -> contains -> [[oklist]]
  - -> contains -> [[now]]
  - -> imports -> [[unresolvedrefdatetime]]
  - -> imports -> [[unresolvedreftyping]]
- **_now** (C:\project\tenopa proposer\app\api\response.py) -- 3 connections
  - -> calls -> [[unresolvedrefisoformat]]
  - -> calls -> [[unresolvedrefnow]]
  - <- contains <- [[response]]
- **__unresolved__::ref::_now** () -- 2 connections
  - <- calls <- [[ok]]
  - <- calls <- [[oklist]]
- **ok** (C:\project\tenopa proposer\app\api\response.py) -- 2 connections
  - -> calls -> [[unresolvedrefnow]]
  - <- contains <- [[response]]
- **ok_list** (C:\project\tenopa proposer\app\api\response.py) -- 2 connections
  - -> calls -> [[unresolvedrefnow]]
  - <- contains <- [[response]]

## Internal Relationships
- ok -> calls -> __unresolved__::ref::_now [EXTRACTED]
- ok_list -> calls -> __unresolved__::ref::_now [EXTRACTED]
- response -> contains -> ok [EXTRACTED]
- response -> contains -> ok_list [EXTRACTED]
- response -> contains -> _now [EXTRACTED]

## Cross-Community Connections
- _now -> calls -> __unresolved__::ref::isoformat (-> [[unresolvedrefget-unresolvedrefexecute]])
- _now -> calls -> __unresolved__::ref::now (-> [[unresolvedrefget-unresolvedrefexecute]])
- response -> imports -> __unresolved__::ref::datetime (-> [[unresolvedrefbasemodel-unresolvedreflogging]])
- response -> imports -> __unresolved__::ref::typing (-> [[unresolvedrefbasemodel-unresolvedreflogging]])

## Context
이 커뮤니티는 response, _now, __unresolved__::ref::_now를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 response.py이다.

### Key Facts
- def ok(data: Any = None, *, message: str | None = None) -> dict: """단건 성공 응답.""" meta: dict[str, Any] = {"timestamp": _now()} if message: meta["message"] = message return {"data": data, "meta": meta}
- 단건:  return ok(data) 리스트: return ok_list(items, total=count, offset=offset, limit=limit) 작업:  return ok(None, message="삭제되었습니다.") """
- 단건:  return ok(data) 리스트: return ok_list(items, total=count, offset=offset, limit=limit) 작업:  return ok(None, message="삭제되었습니다.") """
