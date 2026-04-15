# _setup_styles & __unresolved__::ref::_inject_char_styles
Cohesion: 0.50 | Nodes: 4

## Key Nodes
- **_setup_styles** (C:\project\tenopa proposer\-agent-master\app\services\hwpx_builder.py) -- 4 connections
  - -> calls -> [[unresolvedrefinjectfonts]]
  - -> calls -> [[unresolvedrefinjectcharstyles]]
  - -> calls -> [[unresolvedrefmarkdirty]]
  - <- contains <- [[hwpxbuilder]]
- **__unresolved__::ref::_inject_char_styles** () -- 1 connections
  - <- calls <- [[setupstyles]]
- **__unresolved__::ref::_inject_fonts** () -- 1 connections
  - <- calls <- [[setupstyles]]
- **__unresolved__::ref::mark_dirty** () -- 1 connections
  - <- calls <- [[setupstyles]]

## Internal Relationships
- _setup_styles -> calls -> __unresolved__::ref::_inject_fonts [EXTRACTED]
- _setup_styles -> calls -> __unresolved__::ref::_inject_char_styles [EXTRACTED]
- _setup_styles -> calls -> __unresolved__::ref::mark_dirty [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 _setup_styles, __unresolved__::ref::_inject_char_styles, __unresolved__::ref::_inject_fonts를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 hwpx_builder.py이다.

### Key Facts
- def _setup_styles(doc: HwpxDocument) -> dict[str, str]: """문서 header에 폰트·스타일 주입 후 style_name → charPrID 반환""" header = doc.headers[0] root = header._element _inject_fonts(root) style_ids = _inject_char_styles(root) header.mark_dirty() return style_ids
