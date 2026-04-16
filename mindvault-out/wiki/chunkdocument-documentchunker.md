# chunk_document & document_chunker
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **chunk_document** (C:\project\tenopa proposer\app\services\document_chunker.py) -- 8 connections
  - -> calls -> [[unresolvedreflen]]
  - -> calls -> [[unresolvedrefstrip]]
  - -> calls -> [[unresolvedrefget]]
  - -> calls -> [[unresolvedrefchunkslides]]
  - -> calls -> [[unresolvedrefchunkarticles]]
  - -> calls -> [[unresolvedrefchunkbyheadings]]
  - -> calls -> [[unresolvedrefchunkbywindow]]
  - <- contains <- [[documentchunker]]
- **document_chunker** (C:\project\tenopa proposer\app\services\document_chunker.py) -- 7 connections
  - -> contains -> [[chunkdocument]]
  - -> contains -> [[chunkbyheadings]]
  - -> contains -> [[chunkslides]]
  - -> contains -> [[chunkarticles]]
  - -> contains -> [[chunkbywindow]]
  - -> imports -> [[unresolvedrefre]]
  - -> imports -> [[unresolvedrefdataclasses]]
- **__unresolved__::ref::_chunk_by_window** () -- 4 connections
  - <- calls <- [[chunkdocument]]
  - <- calls <- [[chunkbyheadings]]
  - <- calls <- [[chunkslides]]
  - <- calls <- [[chunkarticles]]
- **__unresolved__::ref::_chunk_articles** () -- 1 connections
  - <- calls <- [[chunkdocument]]
- **__unresolved__::ref::_chunk_by_headings** () -- 1 connections
  - <- calls <- [[chunkdocument]]
- **__unresolved__::ref::_chunk_slides** () -- 1 connections
  - <- calls <- [[chunkdocument]]

## Internal Relationships
- chunk_document -> calls -> __unresolved__::ref::_chunk_slides [EXTRACTED]
- chunk_document -> calls -> __unresolved__::ref::_chunk_articles [EXTRACTED]
- chunk_document -> calls -> __unresolved__::ref::_chunk_by_headings [EXTRACTED]
- chunk_document -> calls -> __unresolved__::ref::_chunk_by_window [EXTRACTED]
- document_chunker -> contains -> chunk_document [EXTRACTED]

## Cross-Community Connections
- chunk_document -> calls -> __unresolved__::ref::len (-> [[unresolvedrefget-unresolvedrefexecute]])
- chunk_document -> calls -> __unresolved__::ref::strip (-> [[unresolvedrefget-unresolvedrefexecute]])
- chunk_document -> calls -> __unresolved__::ref::get (-> [[unresolvedrefget-unresolvedrefexecute]])
- document_chunker -> contains -> _chunk_by_headings (-> [[unresolvedrefget-unresolvedrefexecute]])
- document_chunker -> contains -> _chunk_slides (-> [[unresolvedrefget-unresolvedrefexecute]])
- document_chunker -> contains -> _chunk_articles (-> [[unresolvedrefreact-unresolvedreflibapi]])
- document_chunker -> contains -> _chunk_by_window (-> [[unresolvedrefget-unresolvedrefexecute]])
- document_chunker -> imports -> __unresolved__::ref::re (-> [[unresolvedrefbasemodel-unresolvedreflogging]])
- document_chunker -> imports -> __unresolved__::ref::dataclasses (-> [[unresolvedrefbasemodel-unresolvedreflogging]])

## Context
이 커뮤니티는 chunk_document, document_chunker, __unresolved__::ref::_chunk_by_window를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 document_chunker.py이다.

### Key Facts
- def chunk_document( text: str, doc_type: str, doc_subtype: str = "", max_chunk_chars: int = 3000, window_chars: int = 2000, overlap_chars: int = 200, ) -> list[Chunk]: """문서 유형에 따라 적절한 청킹 전략 선택.""" if not text or len(text.strip()) < 50: return []
