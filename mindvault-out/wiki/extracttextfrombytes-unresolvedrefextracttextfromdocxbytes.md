# _extract_text_from_bytes & __unresolved__::ref::_extract_text_from_docx_bytes
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **_extract_text_from_bytes** (C:\project\tenopa proposer\-agent-master\app\services\asset_extractor.py) -- 4 connections
  - -> calls -> [[unresolvedrefextracttextfrompdfbytes]]
  - -> calls -> [[unresolvedrefextracttextfromdocxbytes]]
  - -> calls -> [[unresolvedrefdecode]]
  - <- contains <- [[assetextractor]]
- **__unresolved__::ref::_extract_text_from_docx_bytes** () -- 1 connections
  - <- calls <- [[extracttextfrombytes]]
- **__unresolved__::ref::_extract_text_from_pdf_bytes** () -- 1 connections
  - <- calls <- [[extracttextfrombytes]]

## Internal Relationships
- _extract_text_from_bytes -> calls -> __unresolved__::ref::_extract_text_from_pdf_bytes [EXTRACTED]
- _extract_text_from_bytes -> calls -> __unresolved__::ref::_extract_text_from_docx_bytes [EXTRACTED]

## Cross-Community Connections
- _extract_text_from_bytes -> calls -> __unresolved__::ref::decode (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 _extract_text_from_bytes, __unresolved__::ref::_extract_text_from_docx_bytes, __unresolved__::ref::_extract_text_from_pdf_bytes를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 asset_extractor.py이다.

### Key Facts
- def _extract_text_from_bytes(file_content: bytes, file_type: str) -> str: """파일 바이트에서 텍스트 추출
