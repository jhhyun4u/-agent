# Toolbar & ProposalEditor
Cohesion: 0.08 | Nodes: 24

## Key Nodes
- **Toolbar** (C:\project\tenopa proposer\frontend\components\ProposalEditor.tsx) -- 15 connections
  - -> calls -> [[unresolvedrefbtn]]
  - -> calls -> [[unresolvedrefisactive]]
  - -> calls -> [[unresolvedrefrun]]
  - -> calls -> [[unresolvedreftogglebold]]
  - -> calls -> [[unresolvedreffocus]]
  - -> calls -> [[unresolvedrefchain]]
  - -> calls -> [[unresolvedreftoggleitalic]]
  - -> calls -> [[unresolvedreftogglestrike]]
  - -> calls -> [[unresolvedreftoggleheading]]
  - -> calls -> [[unresolvedreftogglebulletlist]]
  - -> calls -> [[unresolvedreftoggleorderedlist]]
  - -> calls -> [[unresolvedreftoggleblockquote]]
  - -> calls -> [[unresolvedreftogglehighlight]]
  - -> calls -> [[unresolvedrefinserttable]]
  - <- contains <- [[proposaleditor]]
- **ProposalEditor** (C:\project\tenopa proposer\frontend\components\ProposalEditor.tsx) -- 11 connections
  - -> contains -> [[proposaleditorprops]]
  - -> contains -> [[toolbar]]
  - -> imports -> [[unresolvedrefreact]]
  - -> imports -> [[unresolvedreftiptapreact]]
  - -> imports -> [[unresolvedreftiptapstarterkit]]
  - -> imports -> [[unresolvedreftiptapextensionhighlight]]
  - -> imports -> [[unresolvedreftiptapextensiontable]]
  - -> imports -> [[unresolvedreftiptapextensiontablerow]]
  - -> imports -> [[unresolvedreftiptapextensiontablecell]]
  - -> imports -> [[unresolvedreftiptapextensiontableheader]]
  - -> imports -> [[unresolvedreftiptapextensionplaceholder]]
- **__unresolved__::ref::focus** () -- 2 connections
  - <- calls <- [[toolbar]]
  - <- calls <- [[reviewpanel]]
- **__unresolved__::ref::__tiptap_extension_highlight_** () -- 1 connections
  - <- imports <- [[proposaleditor]]
- **__unresolved__::ref::__tiptap_extension_placeholder_** () -- 1 connections
  - <- imports <- [[proposaleditor]]
- **__unresolved__::ref::__tiptap_extension_table_** () -- 1 connections
  - <- imports <- [[proposaleditor]]
- **__unresolved__::ref::__tiptap_extension_table_cell_** () -- 1 connections
  - <- imports <- [[proposaleditor]]
- **__unresolved__::ref::__tiptap_extension_table_header_** () -- 1 connections
  - <- imports <- [[proposaleditor]]
- **__unresolved__::ref::__tiptap_extension_table_row_** () -- 1 connections
  - <- imports <- [[proposaleditor]]
- **__unresolved__::ref::__tiptap_react_** () -- 1 connections
  - <- imports <- [[proposaleditor]]
- **__unresolved__::ref::__tiptap_starter_kit_** () -- 1 connections
  - <- imports <- [[proposaleditor]]
- **__unresolved__::ref::btn** () -- 1 connections
  - <- calls <- [[toolbar]]
- **__unresolved__::ref::chain** () -- 1 connections
  - <- calls <- [[toolbar]]
- **__unresolved__::ref::inserttable** () -- 1 connections
  - <- calls <- [[toolbar]]
- **__unresolved__::ref::isactive** () -- 1 connections
  - <- calls <- [[toolbar]]
- **__unresolved__::ref::toggleblockquote** () -- 1 connections
  - <- calls <- [[toolbar]]
- **__unresolved__::ref::togglebold** () -- 1 connections
  - <- calls <- [[toolbar]]
- **__unresolved__::ref::togglebulletlist** () -- 1 connections
  - <- calls <- [[toolbar]]
- **__unresolved__::ref::toggleheading** () -- 1 connections
  - <- calls <- [[toolbar]]
- **__unresolved__::ref::togglehighlight** () -- 1 connections
  - <- calls <- [[toolbar]]
- **__unresolved__::ref::toggleitalic** () -- 1 connections
  - <- calls <- [[toolbar]]
- **__unresolved__::ref::toggleorderedlist** () -- 1 connections
  - <- calls <- [[toolbar]]
- **__unresolved__::ref::togglestrike** () -- 1 connections
  - <- calls <- [[toolbar]]
- **ProposalEditorProps** (C:\project\tenopa proposer\frontend\components\ProposalEditor.tsx) -- 1 connections
  - <- contains <- [[proposaleditor]]

## Internal Relationships
- Toolbar -> calls -> __unresolved__::ref::btn [EXTRACTED]
- Toolbar -> calls -> __unresolved__::ref::isactive [EXTRACTED]
- Toolbar -> calls -> __unresolved__::ref::togglebold [EXTRACTED]
- Toolbar -> calls -> __unresolved__::ref::focus [EXTRACTED]
- Toolbar -> calls -> __unresolved__::ref::chain [EXTRACTED]
- Toolbar -> calls -> __unresolved__::ref::toggleitalic [EXTRACTED]
- Toolbar -> calls -> __unresolved__::ref::togglestrike [EXTRACTED]
- Toolbar -> calls -> __unresolved__::ref::toggleheading [EXTRACTED]
- Toolbar -> calls -> __unresolved__::ref::togglebulletlist [EXTRACTED]
- Toolbar -> calls -> __unresolved__::ref::toggleorderedlist [EXTRACTED]
- Toolbar -> calls -> __unresolved__::ref::toggleblockquote [EXTRACTED]
- Toolbar -> calls -> __unresolved__::ref::togglehighlight [EXTRACTED]
- Toolbar -> calls -> __unresolved__::ref::inserttable [EXTRACTED]
- ProposalEditor -> contains -> ProposalEditorProps [EXTRACTED]
- ProposalEditor -> contains -> Toolbar [EXTRACTED]
- ProposalEditor -> imports -> __unresolved__::ref::__tiptap_react_ [EXTRACTED]
- ProposalEditor -> imports -> __unresolved__::ref::__tiptap_starter_kit_ [EXTRACTED]
- ProposalEditor -> imports -> __unresolved__::ref::__tiptap_extension_highlight_ [EXTRACTED]
- ProposalEditor -> imports -> __unresolved__::ref::__tiptap_extension_table_ [EXTRACTED]
- ProposalEditor -> imports -> __unresolved__::ref::__tiptap_extension_table_row_ [EXTRACTED]
- ProposalEditor -> imports -> __unresolved__::ref::__tiptap_extension_table_cell_ [EXTRACTED]
- ProposalEditor -> imports -> __unresolved__::ref::__tiptap_extension_table_header_ [EXTRACTED]
- ProposalEditor -> imports -> __unresolved__::ref::__tiptap_extension_placeholder_ [EXTRACTED]

## Cross-Community Connections
- Toolbar -> calls -> __unresolved__::ref::run (-> [[unresolvedrefprint-unresolvedrefpath]])
- ProposalEditor -> imports -> __unresolved__::ref::_react_ (-> [[unresolvedrefreact-unresolvedreflibapi]])

## Context
이 커뮤니티는 Toolbar, ProposalEditor, __unresolved__::ref::focus를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 ProposalEditor.tsx이다.

### Key Facts
- return ( <div className={`flex flex-col h-full ${className}`}> {/* 도구바 */} <Toolbar editor={editor} />
- /** * ProposalEditor — Tiptap 기반 제안서 에디터 (§13-10) * * - Tiptap starter-kit + Highlight (AI 코멘트) * - 섹션별 편집 * - 자동 저장 (debounce 3초) */
- interface ProposalEditorProps { content: string; onUpdate: (html: string) => void; /** 에디터 내용이 변경될 때 즉시 호출 (debounce 전) */ onChange?: () => void; className?: string; }
