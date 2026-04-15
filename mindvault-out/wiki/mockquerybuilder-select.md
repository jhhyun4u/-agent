# MockQueryBuilder & select
Cohesion: 0.20 | Nodes: 11

## Key Nodes
- **MockQueryBuilder** (C:\project\tenopa proposer\-agent-master\tests\conftest.py) -- 11 connections
  - -> contains -> [[init]]
  - -> contains -> [[chain]]
  - -> contains -> [[select]]
  - -> contains -> [[eq]]
  - -> contains -> [[in]]
  - -> contains -> [[range]]
  - -> contains -> [[single]]
  - -> contains -> [[maybesingle]]
  - -> contains -> [[applyfilters]]
  - -> contains -> [[execute]]
  - <- contains <- [[conftest]]
- **select** (C:\project\tenopa proposer\-agent-master\tests\conftest.py) -- 4 connections
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedreflen]]
  - -> calls -> [[unresolvedrefchain]]
  - <- contains <- [[mockquerybuilder]]
- **__unresolved__::ref::_chain** () -- 3 connections
  - <- calls <- [[select]]
  - <- calls <- [[range]]
  - <- calls <- [[makeadminmock]]
- **_apply_filters** (C:\project\tenopa proposer\-agent-master\tests\conftest.py) -- 3 connections
  - -> calls -> [[unresolvedrefisinstance]]
  - -> calls -> [[unresolvedrefget]]
  - <- contains <- [[mockquerybuilder]]
- **eq** (C:\project\tenopa proposer\-agent-master\tests\conftest.py) -- 2 connections
  - -> calls -> [[unresolvedrefappend]]
  - <- contains <- [[mockquerybuilder]]
- **in_** (C:\project\tenopa proposer\-agent-master\tests\conftest.py) -- 2 connections
  - -> calls -> [[unresolvedrefappend]]
  - <- contains <- [[mockquerybuilder]]
- **range** (C:\project\tenopa proposer\-agent-master\tests\conftest.py) -- 2 connections
  - -> calls -> [[unresolvedrefchain]]
  - <- contains <- [[mockquerybuilder]]
- **__init__** (C:\project\tenopa proposer\-agent-master\tests\conftest.py) -- 1 connections
  - <- contains <- [[mockquerybuilder]]
- **_chain** (C:\project\tenopa proposer\-agent-master\tests\conftest.py) -- 1 connections
  - <- contains <- [[mockquerybuilder]]
- **maybe_single** (C:\project\tenopa proposer\-agent-master\tests\conftest.py) -- 1 connections
  - <- contains <- [[mockquerybuilder]]
- **single** (C:\project\tenopa proposer\-agent-master\tests\conftest.py) -- 1 connections
  - <- contains <- [[mockquerybuilder]]

## Internal Relationships
- MockQueryBuilder -> contains -> __init__ [EXTRACTED]
- MockQueryBuilder -> contains -> _chain [EXTRACTED]
- MockQueryBuilder -> contains -> select [EXTRACTED]
- MockQueryBuilder -> contains -> eq [EXTRACTED]
- MockQueryBuilder -> contains -> in_ [EXTRACTED]
- MockQueryBuilder -> contains -> range [EXTRACTED]
- MockQueryBuilder -> contains -> single [EXTRACTED]
- MockQueryBuilder -> contains -> maybe_single [EXTRACTED]
- MockQueryBuilder -> contains -> _apply_filters [EXTRACTED]
- range -> calls -> __unresolved__::ref::_chain [EXTRACTED]
- select -> calls -> __unresolved__::ref::_chain [EXTRACTED]

## Cross-Community Connections
- MockQueryBuilder -> contains -> execute (-> [[unresolvedrefget-unresolvedreflen]])
- _apply_filters -> calls -> __unresolved__::ref::isinstance (-> [[unresolvedrefget-unresolvedreflen]])
- _apply_filters -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- eq -> calls -> __unresolved__::ref::append (-> [[unresolvedrefget-unresolvedreflen]])
- in_ -> calls -> __unresolved__::ref::append (-> [[unresolvedrefget-unresolvedreflen]])
- select -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedreflen]])
- select -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 MockQueryBuilder, select, __unresolved__::ref::_chain를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 conftest.py이다.

### Key Facts
- class MockQueryBuilder: """Supabase 쿼리 빌더 체이닝 mock."""
- 체이닝 메서드 def select(self, *args, **kwargs): """select 메서드 — count 파라미터 처리""" if kwargs.get("count"): self._count = len(self._data)  # 실제 데이터 개수로 count 설정 return self._chain() insert = property(lambda self: lambda *a, **kw: self._chain()) update = property(lambda self: lambda *a, **kw: self._chain())…
- def _apply_filters(self, data): """필터 적용 헬퍼""" if not self._filters: return data
- def eq(self, key, value): """필터 추가: key == value""" self._filters.append((key, value, "==")) return self
- def in_(self, key, values): """필터 추가: key in values""" self._filters.append((key, values, "in")) return self
