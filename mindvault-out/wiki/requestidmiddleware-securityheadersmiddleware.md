# RequestIdMiddleware & SecurityHeadersMiddleware
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **RequestIdMiddleware** (C:\project\tenopa proposer\app\middleware\request_id.py) -- 3 connections
  - -> extends -> [[unresolvedrefbasehttpmiddleware]]
  - -> contains -> [[dispatch]]
  - <- contains <- [[requestid]]
- **SecurityHeadersMiddleware** (C:\project\tenopa proposer\app\middleware\security_headers.py) -- 3 connections
  - -> extends -> [[unresolvedrefbasehttpmiddleware]]
  - -> contains -> [[dispatch]]
  - <- contains <- [[securityheaders]]
- **__unresolved__::ref::basehttpmiddleware** () -- 2 connections
  - <- extends <- [[requestidmiddleware]]
  - <- extends <- [[securityheadersmiddleware]]
- **__unresolved__::ref::call_next** () -- 2 connections
  - <- calls <- [[dispatch]]
  - <- calls <- [[dispatch]]
- **dispatch** (C:\project\tenopa proposer\app\middleware\security_headers.py) -- 2 connections
  - -> calls -> [[unresolvedrefcallnext]]
  - <- contains <- [[securityheadersmiddleware]]

## Internal Relationships
- RequestIdMiddleware -> extends -> __unresolved__::ref::basehttpmiddleware [EXTRACTED]
- SecurityHeadersMiddleware -> extends -> __unresolved__::ref::basehttpmiddleware [EXTRACTED]
- SecurityHeadersMiddleware -> contains -> dispatch [EXTRACTED]
- dispatch -> calls -> __unresolved__::ref::call_next [EXTRACTED]

## Cross-Community Connections
- RequestIdMiddleware -> contains -> dispatch (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 RequestIdMiddleware, SecurityHeadersMiddleware, __unresolved__::ref::basehttpmiddleware를 중심으로 extends 관계로 연결되어 있다. 주요 소스 파일은 request_id.py, security_headers.py이다.

### Key Facts
- class RequestIdMiddleware(BaseHTTPMiddleware): """X-Request-ID 생성·전파·로깅 미들웨어."""
- class SecurityHeadersMiddleware(BaseHTTPMiddleware): """HSTS + X-Content-Type-Options + X-Frame-Options 등 보안 헤더 추가."""
- async def dispatch(self, request: Request, call_next) -> Response: response = await call_next(request)
