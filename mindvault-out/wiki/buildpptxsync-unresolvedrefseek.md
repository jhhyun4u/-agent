# _build_pptx_sync & __unresolved__::ref::seek
Cohesion: 0.33 | Nodes: 6

## Key Nodes
- **_build_pptx_sync** (C:\project\tenopa proposer\-agent-master\app\services\pptx_builder.py) -- 10 connections
  - -> calls -> [[unresolvedrefpresentation]]
  - -> calls -> [[unresolvedrefaddtitleslide]]
  - -> calls -> [[unresolvedrefaddtocslide]]
  - -> calls -> [[unresolvedrefaddcontentslide]]
  - -> calls -> [[unresolvedrefaddclosingslide]]
  - -> calls -> [[unresolvedrefbytesio]]
  - -> calls -> [[unresolvedrefsave]]
  - -> calls -> [[unresolvedrefseek]]
  - -> calls -> [[unresolvedrefread]]
  - <- contains <- [[pptxbuilder]]
- **__unresolved__::ref::seek** () -- 2 connections
  - <- calls <- [[buildpptxsync]]
  - <- calls <- [[buildcostsheet]]
- **__unresolved__::ref::_add_closing_slide** () -- 1 connections
  - <- calls <- [[buildpptxsync]]
- **__unresolved__::ref::_add_content_slide** () -- 1 connections
  - <- calls <- [[buildpptxsync]]
- **__unresolved__::ref::_add_title_slide** () -- 1 connections
  - <- calls <- [[buildpptxsync]]
- **__unresolved__::ref::_add_toc_slide** () -- 1 connections
  - <- calls <- [[buildpptxsync]]

## Internal Relationships
- _build_pptx_sync -> calls -> __unresolved__::ref::_add_title_slide [EXTRACTED]
- _build_pptx_sync -> calls -> __unresolved__::ref::_add_toc_slide [EXTRACTED]
- _build_pptx_sync -> calls -> __unresolved__::ref::_add_content_slide [EXTRACTED]
- _build_pptx_sync -> calls -> __unresolved__::ref::_add_closing_slide [EXTRACTED]
- _build_pptx_sync -> calls -> __unresolved__::ref::seek [EXTRACTED]

## Cross-Community Connections
- _build_pptx_sync -> calls -> __unresolved__::ref::presentation (-> [[unresolvedrefget-unresolvedreflen]])
- _build_pptx_sync -> calls -> __unresolved__::ref::bytesio (-> [[unresolvedrefget-unresolvedreflen]])
- _build_pptx_sync -> calls -> __unresolved__::ref::save (-> [[unresolvedrefget-unresolvedreflen]])
- _build_pptx_sync -> calls -> __unresolved__::ref::read (-> [[unresolvedrefget-unresolvedreflen]])

## Context
이 커뮤니티는 _build_pptx_sync, __unresolved__::ref::seek, __unresolved__::ref::_add_closing_slide를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 pptx_builder.py이다.

### Key Facts
- async def build_pptx( slides: list[dict[str, Any]], proposal_name: str = "용역 제안서", presentation_strategy: dict[str, Any] | None = None, ) -> bytes: """ppt_slides 리스트 → PPTX 바이트.""" return await asyncio.to_thread( _build_pptx_sync, slides, proposal_name, presentation_strategy, )
