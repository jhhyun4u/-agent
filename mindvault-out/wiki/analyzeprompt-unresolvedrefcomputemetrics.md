# analyze_prompt & __unresolved__::ref::_compute_metrics
Cohesion: 0.22 | Nodes: 9

## Key Nodes
- **analyze_prompt** (C:\project\tenopa proposer\app\services\prompt_analyzer.py) -- 9 connections
  - -> calls -> [[unresolvedrefcomputemetrics]]
  - -> calls -> [[unresolvedrefclassifyeditpatterns]]
  - -> calls -> [[unresolvedrefsummarizefeedback]]
  - -> calls -> [[unresolvedrefcomparewinloss]]
  - -> calls -> [[unresolvedrefcomputetrend]]
  - -> calls -> [[unresolvedrefcomputepriority]]
  - -> calls -> [[unresolvedrefgeneratehypothesis]]
  - -> calls -> [[unresolvedrefsavesnapshot]]
  - <- contains <- [[promptanalyzer]]
- **__unresolved__::ref::_compute_metrics** () -- 1 connections
  - <- calls <- [[analyzeprompt]]
- **__unresolved__::ref::_compute_priority** () -- 1 connections
  - <- calls <- [[analyzeprompt]]
- **__unresolved__::ref::_generate_hypothesis** () -- 1 connections
  - <- calls <- [[analyzeprompt]]
- **__unresolved__::ref::_save_snapshot** () -- 1 connections
  - <- calls <- [[analyzeprompt]]
- **__unresolved__::ref::_summarize_feedback** () -- 1 connections
  - <- calls <- [[analyzeprompt]]
- **__unresolved__::ref::classify_edit_patterns** () -- 1 connections
  - <- calls <- [[analyzeprompt]]
- **__unresolved__::ref::compare_win_loss** () -- 1 connections
  - <- calls <- [[analyzeprompt]]
- **__unresolved__::ref::compute_trend** () -- 1 connections
  - <- calls <- [[analyzeprompt]]

## Internal Relationships
- analyze_prompt -> calls -> __unresolved__::ref::_compute_metrics [EXTRACTED]
- analyze_prompt -> calls -> __unresolved__::ref::classify_edit_patterns [EXTRACTED]
- analyze_prompt -> calls -> __unresolved__::ref::_summarize_feedback [EXTRACTED]
- analyze_prompt -> calls -> __unresolved__::ref::compare_win_loss [EXTRACTED]
- analyze_prompt -> calls -> __unresolved__::ref::compute_trend [EXTRACTED]
- analyze_prompt -> calls -> __unresolved__::ref::_compute_priority [EXTRACTED]
- analyze_prompt -> calls -> __unresolved__::ref::_generate_hypothesis [EXTRACTED]
- analyze_prompt -> calls -> __unresolved__::ref::_save_snapshot [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 analyze_prompt, __unresolved__::ref::_compute_metrics, __unresolved__::ref::_compute_priority를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 prompt_analyzer.py이다.

### Key Facts
- async def analyze_prompt(prompt_id: str, days: int = 90) -> dict: """프롬프트의 최근 N일 데이터를 종합 분석.""" metrics = await _compute_metrics(prompt_id, days) edit_patterns = await classify_edit_patterns(prompt_id, limit=30) feedback = await _summarize_feedback(prompt_id, days) win_loss = await…
