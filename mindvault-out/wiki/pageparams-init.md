# PageParams & __init__
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **PageParams** (C:\project\tenopa proposer\app\utils\pagination.py) -- 3 connections
  - -> contains -> [[init]]
  - -> contains -> [[apply]]
  - <- contains <- [[pagination]]
- **__init__** (C:\project\tenopa proposer\app\utils\pagination.py) -- 2 connections
  - -> calls -> [[unresolvedrefquery]]
  - <- contains <- [[pageparams]]
- **apply** (C:\project\tenopa proposer\app\utils\pagination.py) -- 2 connections
  - -> calls -> [[unresolvedrefrange]]
  - <- contains <- [[pageparams]]
- **pagination** (C:\project\tenopa proposer\app\utils\pagination.py) -- 2 connections
  - -> contains -> [[pageparams]]
  - -> imports -> [[unresolvedreffastapi]]
- **__unresolved__::ref::query** () -- 1 connections
  - <- calls <- [[init]]

## Internal Relationships
- PageParams -> contains -> __init__ [EXTRACTED]
- PageParams -> contains -> apply [EXTRACTED]
- __init__ -> calls -> __unresolved__::ref::query [EXTRACTED]
- pagination -> contains -> PageParams [EXTRACTED]

## Cross-Community Connections
- apply -> calls -> __unresolved__::ref::range (-> [[unresolvedrefget-unresolvedrefexecute]])
- pagination -> imports -> __unresolved__::ref::fastapi (-> [[unresolvedrefbasemodel-unresolvedreflogging]])

## Context
이 커뮤니티는 PageParams, __init__, apply를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 pagination.py이다.

### Key Facts
- class PageParams: """FastAPI Depends()로 주입 가능한 페이지네이션 파라미터.
- def __init__( self, page: int = Query(1, ge=1, description="페이지 번호"), page_size: int = Query(20, ge=1, le=100, description="페이지 크기"), ): self.page = page self.page_size = page_size
- def apply(self, query): """Supabase 쿼리에 .range() 적용. 쿼리 빌더 반환.""" return query.range(self.offset, self.end)
