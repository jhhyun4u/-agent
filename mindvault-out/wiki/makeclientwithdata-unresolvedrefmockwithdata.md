# _make_client_with_data & __unresolved__::ref::_mock_with_data
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **_make_client_with_data** (C:\project\tenopa proposer\-agent-master\tests\test_e2e_kb.py) -- 2 connections
  - -> calls -> [[unresolvedrefmockwithdata]]
  - <- contains <- [[teste2ekb]]
- **__unresolved__::ref::_mock_with_data** () -- 1 connections
  - <- calls <- [[makeclientwithdata]]

## Internal Relationships
- _make_client_with_data -> calls -> __unresolved__::ref::_mock_with_data [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 _make_client_with_data, __unresolved__::ref::_mock_with_data를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 test_e2e_kb.py이다.

### Key Facts
- def _make_client_with_data(app, mock_user, table_data: dict | None = None): """테이블 데이터 주입 가능한 테스트 클라이언트 팩토리.""" from app.api.deps import get_current_user, get_rls_client, require_project_access supabase_mock = _mock_with_data(table_data or {})
