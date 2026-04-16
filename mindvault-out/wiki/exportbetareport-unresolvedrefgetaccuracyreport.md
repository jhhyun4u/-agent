# export_beta_report & __unresolved__::ref::get_accuracy_report
Cohesion: 0.29 | Nodes: 7

## Key Nodes
- **export_beta_report** (C:\project\tenopa proposer\app\services\beta_metrics_tracker.py) -- 11 connections
  - -> calls -> [[unresolvedrefisoformat]]
  - -> calls -> [[unresolvedrefutcnow]]
  - -> calls -> [[unresolvedrefgetnpsscore]]
  - -> calls -> [[unresolvedrefgetaccuracyreport]]
  - -> calls -> [[unresolvedrefgetgolivereadiness]]
  - -> calls -> [[unresolvedrefgetuserfeedbacksummary]]
  - -> calls -> [[unresolvedrefrange]]
  - -> calls -> [[unresolvedrefgetstepmetrics]]
  - -> calls -> [[unresolvedrefgetstepsatisfaction]]
  - -> calls -> [[unresolvedreferror]]
  - <- contains <- [[betametricstracker]]
- **__unresolved__::ref::get_accuracy_report** () -- 2 connections
  - <- calls <- [[getgolivereadiness]]
  - <- calls <- [[exportbetareport]]
- **__unresolved__::ref::get_nps_score** () -- 2 connections
  - <- calls <- [[getgolivereadiness]]
  - <- calls <- [[exportbetareport]]
- **__unresolved__::ref::get_step_metrics** () -- 2 connections
  - <- calls <- [[getgolivereadiness]]
  - <- calls <- [[exportbetareport]]
- **__unresolved__::ref::get_go_live_readiness** () -- 1 connections
  - <- calls <- [[exportbetareport]]
- **__unresolved__::ref::get_step_satisfaction** () -- 1 connections
  - <- calls <- [[exportbetareport]]
- **__unresolved__::ref::get_user_feedback_summary** () -- 1 connections
  - <- calls <- [[exportbetareport]]

## Internal Relationships
- export_beta_report -> calls -> __unresolved__::ref::get_nps_score [EXTRACTED]
- export_beta_report -> calls -> __unresolved__::ref::get_accuracy_report [EXTRACTED]
- export_beta_report -> calls -> __unresolved__::ref::get_go_live_readiness [EXTRACTED]
- export_beta_report -> calls -> __unresolved__::ref::get_user_feedback_summary [EXTRACTED]
- export_beta_report -> calls -> __unresolved__::ref::get_step_metrics [EXTRACTED]
- export_beta_report -> calls -> __unresolved__::ref::get_step_satisfaction [EXTRACTED]

## Cross-Community Connections
- export_beta_report -> calls -> __unresolved__::ref::isoformat (-> [[unresolvedrefget-unresolvedrefexecute]])
- export_beta_report -> calls -> __unresolved__::ref::utcnow (-> [[unresolvedrefget-unresolvedrefexecute]])
- export_beta_report -> calls -> __unresolved__::ref::range (-> [[unresolvedrefget-unresolvedrefexecute]])
- export_beta_report -> calls -> __unresolved__::ref::error (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 export_beta_report, __unresolved__::ref::get_accuracy_report, __unresolved__::ref::get_nps_score를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 beta_metrics_tracker.py이다.

### Key Facts
- async def export_beta_report(self) -> Dict[str, Any]: """전체 베타 테스트 보고서""" try: report = { "generated_at": datetime.utcnow().isoformat(), "test_period": "2026-04-17 ~ 2026-04-30",
