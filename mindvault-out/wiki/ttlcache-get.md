# TTLCache & get
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **TTLCache** (C:\project\tenopa proposer\frontend\lib\api.ts) -- 5 connections
  - -> contains -> [[constructor]]
  - -> contains -> [[get]]
  - -> contains -> [[set]]
  - -> contains -> [[clear]]
  - <- contains <- [[api]]
- **get** (C:\project\tenopa proposer\frontend\lib\api.ts) -- 2 connections
  - -> calls -> [[unresolvedrefnow]]
  - <- contains <- [[ttlcache]]
- **set** (C:\project\tenopa proposer\frontend\lib\api.ts) -- 2 connections
  - -> calls -> [[unresolvedrefnow]]
  - <- contains <- [[ttlcache]]
- **clear** (C:\project\tenopa proposer\frontend\lib\api.ts) -- 1 connections
  - <- contains <- [[ttlcache]]
- **constructor** (C:\project\tenopa proposer\frontend\lib\api.ts) -- 1 connections
  - <- contains <- [[ttlcache]]

## Internal Relationships
- TTLCache -> contains -> constructor [EXTRACTED]
- TTLCache -> contains -> get [EXTRACTED]
- TTLCache -> contains -> set [EXTRACTED]
- TTLCache -> contains -> clear [EXTRACTED]

## Cross-Community Connections
- get -> calls -> __unresolved__::ref::now (-> [[unresolvedrefget-unresolvedrefexecute]])
- set -> calls -> __unresolved__::ref::now (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 TTLCache, get, set를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 api.ts이다.

### Key Facts
- /** TTL이 있는 캐시 매니저 */ class TTLCache<T> { private value: T | null = null; private expiresAt: number = 0;
- get(): T | null { if (!this.value || Date.now() > this.expiresAt) { return null; } return this.value; }
- /** 표준 API 응답 */ export interface ApiResponse<T> { data: T; meta: { total?: number; offset?: number; limit?: number; timestamp: string; message?: string; }; }
- clear(): void { this.value = null; this.expiresAt = 0; } }
- constructor(private ttlMs: number) {}
