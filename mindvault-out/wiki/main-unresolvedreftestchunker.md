# main & __unresolved__::ref::test_chunker
Cohesion: 0.29 | Nodes: 7

## Key Nodes
- **main** (C:\project\tenopa proposer\-agent-master\test_document_ingestion.py) -- 11 connections
  - -> calls -> [[unresolvedrefprint]]
  - -> calls -> [[unresolvedrefappend]]
  - -> calls -> [[unresolvedreftestimports]]
  - -> calls -> [[unresolvedreftestschemas]]
  - -> calls -> [[unresolvedreftestchunker]]
  - -> calls -> [[unresolvedreftestfileextraction]]
  - -> calls -> [[unresolvedreftestdoctypevalidation]]
  - -> calls -> [[unresolvedreftestdoctypemapping]]
  - -> calls -> [[unresolvedrefsum]]
  - -> calls -> [[unresolvedreflen]]
  - <- contains <- [[testdocumentingestion]]
- **__unresolved__::ref::test_chunker** () -- 1 connections
  - <- calls <- [[main]]
- **__unresolved__::ref::test_doc_type_mapping** () -- 1 connections
  - <- calls <- [[main]]
- **__unresolved__::ref::test_doc_type_validation** () -- 1 connections
  - <- calls <- [[main]]
- **__unresolved__::ref::test_file_extraction** () -- 1 connections
  - <- calls <- [[main]]
- **__unresolved__::ref::test_imports** () -- 1 connections
  - <- calls <- [[main]]
- **__unresolved__::ref::test_schemas** () -- 1 connections
  - <- calls <- [[main]]

## Internal Relationships
- main -> calls -> __unresolved__::ref::test_imports [EXTRACTED]
- main -> calls -> __unresolved__::ref::test_schemas [EXTRACTED]
- main -> calls -> __unresolved__::ref::test_chunker [EXTRACTED]
- main -> calls -> __unresolved__::ref::test_file_extraction [EXTRACTED]
- main -> calls -> __unresolved__::ref::test_doc_type_validation [EXTRACTED]
- main -> calls -> __unresolved__::ref::test_doc_type_mapping [EXTRACTED]

## Cross-Community Connections
- main -> calls -> __unresolved__::ref::print (-> [[unresolvedrefget-unresolvedreflen]])
- main -> calls -> __unresolved__::ref::append (-> [[unresolvedrefget-unresolvedreflen]])
- main -> calls -> __unresolved__::ref::sum (-> [[unresolvedrefget-unresolvedreflen]])
- main -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 main, __unresolved__::ref::test_chunker, __unresolved__::ref::test_doc_type_mapping를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 test_document_ingestion.py이다.

### Key Facts
- async def main(): """모든 테스트 실행""" print("\n" + "="*60) print("Document Ingestion API Test") print("="*60 + "\n")
