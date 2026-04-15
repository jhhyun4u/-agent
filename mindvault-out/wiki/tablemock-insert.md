# _TableMock & insert
Cohesion: 0.12 | Nodes: 17

## Key Nodes
- **_TableMock** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 18 connections
  - -> contains -> [[init]]
  - -> contains -> [[select]]
  - -> contains -> [[eq]]
  - -> contains -> [[neq]]
  - -> contains -> [[gt]]
  - -> contains -> [[gte]]
  - -> contains -> [[lt]]
  - -> contains -> [[ilike]]
  - -> contains -> [[order]]
  - -> contains -> [[range]]
  - -> contains -> [[limit]]
  - -> contains -> [[maybesingle]]
  - -> contains -> [[insert]]
  - -> contains -> [[update]]
  - -> contains -> [[upsert]]
  - -> contains -> [[delete]]
  - -> contains -> [[execute]]
  - <- contains <- [[testbidsendpoints]]
- **insert** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 2 connections
  - -> calls -> [[unresolvedrefisinstance]]
  - <- contains <- [[tablemock]]
- **upsert** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 2 connections
  - -> calls -> [[unresolvedrefisinstance]]
  - <- contains <- [[tablemock]]
- **__init__** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 1 connections
  - <- contains <- [[tablemock]]
- **delete** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 1 connections
  - <- contains <- [[tablemock]]
- **eq** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 1 connections
  - <- contains <- [[tablemock]]
- **gt** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 1 connections
  - <- contains <- [[tablemock]]
- **gte** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 1 connections
  - <- contains <- [[tablemock]]
- **ilike** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 1 connections
  - <- contains <- [[tablemock]]
- **limit** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 1 connections
  - <- contains <- [[tablemock]]
- **lt** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 1 connections
  - <- contains <- [[tablemock]]
- **maybe_single** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 1 connections
  - <- contains <- [[tablemock]]
- **neq** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 1 connections
  - <- contains <- [[tablemock]]
- **order** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 1 connections
  - <- contains <- [[tablemock]]
- **range** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 1 connections
  - <- contains <- [[tablemock]]
- **select** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 1 connections
  - <- contains <- [[tablemock]]
- **update** (C:\project\tenopa proposer\-agent-master\tests\api\test_bids_endpoints.py) -- 1 connections
  - <- contains <- [[tablemock]]

## Internal Relationships
- _TableMock -> contains -> __init__ [EXTRACTED]
- _TableMock -> contains -> select [EXTRACTED]
- _TableMock -> contains -> eq [EXTRACTED]
- _TableMock -> contains -> neq [EXTRACTED]
- _TableMock -> contains -> gt [EXTRACTED]
- _TableMock -> contains -> gte [EXTRACTED]
- _TableMock -> contains -> lt [EXTRACTED]
- _TableMock -> contains -> ilike [EXTRACTED]
- _TableMock -> contains -> order [EXTRACTED]
- _TableMock -> contains -> range [EXTRACTED]
- _TableMock -> contains -> limit [EXTRACTED]
- _TableMock -> contains -> maybe_single [EXTRACTED]
- _TableMock -> contains -> insert [EXTRACTED]
- _TableMock -> contains -> update [EXTRACTED]
- _TableMock -> contains -> upsert [EXTRACTED]
- _TableMock -> contains -> delete [EXTRACTED]

## Cross-Community Connections
- _TableMock -> contains -> execute (-> [[unresolvedrefget-unresolvedreflen]])
- insert -> calls -> __unresolved__::ref::isinstance (-> [[unresolvedrefget-unresolvedreflen]])
- upsert -> calls -> __unresolved__::ref::isinstance (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 _TableMock, insert, upsert를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 test_bids_endpoints.py이다.

### Key Facts
- class _TableMock: """ 체인 방식 Supabase 테이블 Mock.
- def __init__(self, list_data: list): self._list_data = list_data if list_data is not None else [] self._is_single = False self._write_data = None  # insert/update/upsert 반환용
- def __init__(self, list_data: list): self._list_data = list_data if list_data is not None else [] self._is_single = False self._write_data = None  # insert/update/upsert 반환용
- def __init__(self, list_data: list): self._list_data = list_data if list_data is not None else [] self._is_single = False self._write_data = None  # insert/update/upsert 반환용
- def delete(self): self._write_data = [] return self
