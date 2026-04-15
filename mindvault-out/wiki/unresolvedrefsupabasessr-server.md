# __unresolved__::ref::__supabase_ssr_ & server
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **__unresolved__::ref::__supabase_ssr_** () -- 3 connections
  - <- imports <- [[middleware]]
  - <- imports <- [[client]]
  - <- imports <- [[server]]
- **server** (C:\project\tenopa proposer\-agent-master\frontend\lib\supabase\server.ts) -- 2 connections
  - -> imports -> [[unresolvedrefsupabasessr]]
  - -> imports -> [[unresolvedrefnextheaders]]
- **middleware** (C:\project\tenopa proposer\-agent-master\frontend\middleware.ts) -- 2 connections
  - -> imports -> [[unresolvedrefsupabasessr]]
  - -> imports -> [[unresolvedrefnextserver]]
- **__unresolved__::ref::_next_headers_** () -- 1 connections
  - <- imports <- [[server]]
- **__unresolved__::ref::_next_server_** () -- 1 connections
  - <- imports <- [[middleware]]
- **client** (C:\project\tenopa proposer\-agent-master\frontend\lib\supabase\client.ts) -- 1 connections
  - -> imports -> [[unresolvedrefsupabasessr]]

## Internal Relationships
- client -> imports -> __unresolved__::ref::__supabase_ssr_ [EXTRACTED]
- server -> imports -> __unresolved__::ref::__supabase_ssr_ [EXTRACTED]
- server -> imports -> __unresolved__::ref::_next_headers_ [EXTRACTED]
- middleware -> imports -> __unresolved__::ref::__supabase_ssr_ [EXTRACTED]
- middleware -> imports -> __unresolved__::ref::_next_server_ [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 __unresolved__::ref::__supabase_ssr_, server, middleware를 중심으로 imports 관계로 연결되어 있다. 주요 소스 파일은 client.ts, middleware.ts, server.ts이다.

### Key Facts
- import { createServerClient } from "@supabase/ssr"; import { cookies } from "next/headers";
- export async function middleware(request: NextRequest) {
- import { createBrowserClient } from "@supabase/ssr";
