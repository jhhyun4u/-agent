# _run_all_steps & __unresolved__::ref::_download_and_extract
Cohesion: 0.50 | Nodes: 4

## Key Nodes
- **_run_all_steps** (C:\project\tenopa proposer\app\services\bid_pipeline.py) -- 5 connections
  - -> calls -> [[unresolvedrefensurebidindb]]
  - -> calls -> [[unresolvedrefupdatestatus]]
  - -> calls -> [[unresolvedrefdownloadandextract]]
  - -> calls -> [[unresolvedrefrunanalysisifneeded]]
  - <- contains <- [[bidpipeline]]
- **__unresolved__::ref::_download_and_extract** () -- 1 connections
  - <- calls <- [[runallsteps]]
- **__unresolved__::ref::_ensure_bid_in_db** () -- 1 connections
  - <- calls <- [[runallsteps]]
- **__unresolved__::ref::_run_analysis_if_needed** () -- 1 connections
  - <- calls <- [[runallsteps]]

## Internal Relationships
- _run_all_steps -> calls -> __unresolved__::ref::_ensure_bid_in_db [EXTRACTED]
- _run_all_steps -> calls -> __unresolved__::ref::_download_and_extract [EXTRACTED]
- _run_all_steps -> calls -> __unresolved__::ref::_run_analysis_if_needed [EXTRACTED]

## Cross-Community Connections
- _run_all_steps -> calls -> __unresolved__::ref::_update_status (-> [[unresolvedrefget-unresolvedrefexecute]])

## Context
이 커뮤니티는 _run_all_steps, __unresolved__::ref::_download_and_extract, __unresolved__::ref::_ensure_bid_in_db를 중심으로 calls 관계로 연결되어 있다. 주요 소스 파일은 bid_pipeline.py이다.

### Key Facts
- async def _process_single(bid_no: str, raw_data: dict | None) -> bool: async with _SEMAPHORE: _pipeline_status[bid_no] = { "step": "db_save", "progress": "1/4", "started_at": datetime.now(timezone.utc).isoformat(), "error": None, } try: # 건당 전체 타임아웃 (DB + 첨부 + AI) await…
