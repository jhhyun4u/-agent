# assign_document & __unresolved__::ref::update_document_status
Cohesion: 1.00 | Nodes: 2

## Key Nodes
- **assign_document** (C:\project\tenopa proposer\-agent-master\app\services\submission_docs_service.py) -- 2 connections
  - -> calls -> [[unresolvedrefupdatedocumentstatus]]
  - <- contains <- [[submissiondocsservice]]
- **__unresolved__::ref::update_document_status** () -- 1 connections
  - <- calls <- [[assigndocument]]

## Internal Relationships
- assign_document -> calls -> __unresolved__::ref::update_document_status [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 assign_document, __unresolved__::ref::update_document_status를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 submission_docs_service.py이다.

### Key Facts
- async def assign_document(doc_id: str, assignee_id: str) -> dict: """담당자 배정.""" return await update_document_status(doc_id, { "assignee_id": assignee_id, "status": "assigned", })
