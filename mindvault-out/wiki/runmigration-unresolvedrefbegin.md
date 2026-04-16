# run_migration & __unresolved__::ref::begin
Cohesion: 0.50 | Nodes: 4

## Key Nodes
- **run_migration** (C:\project\tenopa proposer\scripts\run_master_projects_migration.py) -- 9 connections
  - -> calls -> [[unresolvedrefreplace]]
  - -> calls -> [[unresolvedrefcreateasyncengine]]
  - -> calls -> [[unresolvedrefinfo]]
  - -> calls -> [[unresolvedrefbegin]]
  - -> calls -> [[unresolvedrefexecute]]
  - -> calls -> [[unresolvedreftext]]
  - -> calls -> [[unresolvedrefscalar]]
  - -> calls -> [[unresolvedreferror]]
  - <- contains <- [[runmasterprojectsmigration]]
- **__unresolved__::ref::begin** () -- 1 connections
  - <- calls <- [[runmigration]]
- **__unresolved__::ref::create_async_engine** () -- 1 connections
  - <- calls <- [[runmigration]]
- **__unresolved__::ref::scalar** () -- 1 connections
  - <- calls <- [[runmigration]]

## Internal Relationships
- run_migration -> calls -> __unresolved__::ref::create_async_engine [EXTRACTED]
- run_migration -> calls -> __unresolved__::ref::begin [EXTRACTED]
- run_migration -> calls -> __unresolved__::ref::scalar [EXTRACTED]

## Cross-Community Connections
- run_migration -> calls -> __unresolved__::ref::replace (-> [[unresolvedrefget-unresolvedrefexecute]])
- run_migration -> calls -> __unresolved__::ref::info (-> [[unresolvedrefget-unresolvedrefexecute]])
- run_migration -> calls -> __unresolved__::ref::execute (-> [[unresolvedrefget-unresolvedrefexecute]])
- run_migration -> calls -> __unresolved__::ref::text (-> [[unresolvedrefbasemodel-unresolvedreflogging]])
- run_migration -> calls -> __unresolved__::ref::error (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 run_migration, __unresolved__::ref::begin, __unresolved__::ref::create_async_engine를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 run_master_projects_migration.py이다.

### Key Facts
- async def run_migration(): """마이그레이션 실행""" try: # SQLAlchemy로 직접 DB 연결 (Supabase PostgreSQL) from sqlalchemy.ext.asyncio import create_async_engine from app.config import settings
