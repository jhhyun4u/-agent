# _shade_row & __unresolved__::ref::get_or_add_tcpr
Cohesion: 0.50 | Nodes: 4

## Key Nodes
- **_shade_row** (C:\project\tenopa proposer\app\services\bidding\artifacts\cost_sheet_builder.py) -- 6 connections
  - -> calls -> [[unresolvedrefoxmlelement]]
  - -> calls -> [[unresolvedrefset]]
  - -> calls -> [[unresolvedrefqn]]
  - -> calls -> [[unresolvedrefappend]]
  - -> calls -> [[unresolvedrefgetoraddtcpr]]
  - <- contains <- [[costsheetbuilder]]
- **__unresolved__::ref::get_or_add_tcpr** () -- 1 connections
  - <- calls <- [[shaderow]]
- **__unresolved__::ref::oxmlelement** () -- 1 connections
  - <- calls <- [[shaderow]]
- **__unresolved__::ref::qn** () -- 1 connections
  - <- calls <- [[shaderow]]

## Internal Relationships
- _shade_row -> calls -> __unresolved__::ref::oxmlelement [EXTRACTED]
- _shade_row -> calls -> __unresolved__::ref::qn [EXTRACTED]
- _shade_row -> calls -> __unresolved__::ref::get_or_add_tcpr [EXTRACTED]

## Cross-Community Connections
- _shade_row -> calls -> __unresolved__::ref::set (-> [[unresolvedrefget-unresolvedrefexecute]])
- _shade_row -> calls -> __unresolved__::ref::append (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 _shade_row, __unresolved__::ref::get_or_add_tcpr, __unresolved__::ref::oxmlelement를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 cost_sheet_builder.py이다.

### Key Facts
- def _shade_row(row, color: str = "F2F2F2"): """행 배경색 설정.""" from docx.oxml.ns import qn from docx.oxml import OxmlElement for cell in row.cells: shading = OxmlElement("w:shd") shading.set(qn("w:fill"), color) shading.set(qn("w:val"), "clear") cell._tc.get_or_add_tcPr().append(shading)
