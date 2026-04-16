# _classify_g2b_error & __unresolved__::ref::g2bexternalerror
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **_classify_g2b_error** (C:\project\tenopa proposer\app\api\routes_g2b.py) -- 4 connections
  - -> calls -> [[unresolvedrefstr]]
  - -> calls -> [[unresolvedrefg2bexternalerror]]
  - -> calls -> [[unresolvedrefg2bserviceerror]]
  - <- contains <- [[routesg2b]]
- **__unresolved__::ref::g2bexternalerror** () -- 1 connections
  - <- calls <- [[classifyg2berror]]
- **__unresolved__::ref::g2bserviceerror** () -- 1 connections
  - <- calls <- [[classifyg2berror]]

## Internal Relationships
- _classify_g2b_error -> calls -> __unresolved__::ref::g2bexternalerror [EXTRACTED]
- _classify_g2b_error -> calls -> __unresolved__::ref::g2bserviceerror [EXTRACTED]

## Cross-Community Connections
- _classify_g2b_error -> calls -> __unresolved__::ref::str (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 _classify_g2b_error, __unresolved__::ref::g2bexternalerror, __unresolved__::ref::g2bserviceerror를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 routes_g2b.py이다.

### Key Facts
- def _classify_g2b_error(e: RuntimeError) -> TenopAPIError: """RuntimeError 메시지 기반 G2B 에러 분류.""" msg = str(e) if "타임아웃" in msg or "시간 초과" in msg: return G2BExternalError("나라장터 API 응답 시간 초과") if "클라이언트 오류" in msg: return G2BExternalError(msg) if "연결 실패" in msg: return G2BExternalError("나라장터 API 서버 연결…
