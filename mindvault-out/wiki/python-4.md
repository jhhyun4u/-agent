# python & 4. 상세 설계
Cohesion: 0.24 | Nodes: 13

## Key Nodes
- **python** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bid-monitoring-pipeline.design.md) -- 8 connections
  - <- has_code_example <- [[4-1-bidpipelinepy]]
  - <- has_code_example <- [[step-1-ensurebidindb]]
  - <- has_code_example <- [[step-2-downloadandextract]]
  - <- has_code_example <- [[step-3-runanalysisifneeded]]
  - <- has_code_example <- [[4-2-bidattachmentstorepy]]
  - <- has_code_example <- [[4-3-1-bidscrawl]]
  - <- has_code_example <- [[4-3-2-bidspipelinestatus]]
  - <- has_code_example <- [[4-4-scheduledmonitorpy]]
- **4. 상세 설계** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bid-monitoring-pipeline.design.md) -- 5 connections
  - -> contains -> [[4-1-bidpipelinepy]]
  - -> contains -> [[4-2-bidattachmentstorepy]]
  - -> contains -> [[4-3-api-routesbidspy]]
  - -> contains -> [[4-4-scheduledmonitorpy]]
  - -> contains -> [[4-5]]
- **4-1. `bid_pipeline.py` — 파이프라인 오케스트레이터** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bid-monitoring-pipeline.design.md) -- 5 connections
  - -> has_code_example -> [[python]]
  - -> contains -> [[step-1-ensurebidindb]]
  - -> contains -> [[step-2-downloadandextract]]
  - -> contains -> [[step-3-runanalysisifneeded]]
  - <- contains <- [[4]]
- **4-3. API 변경 — `routes_bids.py`** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bid-monitoring-pipeline.design.md) -- 3 connections
  - -> contains -> [[4-3-1-bidscrawl]]
  - -> contains -> [[4-3-2-bidspipelinestatus]]
  - <- contains <- [[4]]
- **4-2. `bid_attachment_store.py` — 첨부파일 다운로드/저장** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bid-monitoring-pipeline.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[4]]
- **4-3-1. `/bids/crawl` 후 파이프라인 자동 트리거** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bid-monitoring-pipeline.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[4-3-api-routesbidspy]]
- **4-3-2. `/bids/pipeline/status` — 진행 상태 조회** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bid-monitoring-pipeline.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[4-3-api-routesbidspy]]
- **4-4. `scheduled_monitor.py` 연동** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bid-monitoring-pipeline.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[4]]
- **4-5. 프론트엔드 — 분석 진행 상태 표시** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bid-monitoring-pipeline.design.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[4]]
- **Step 1: `_ensure_bid_in_db()`** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bid-monitoring-pipeline.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[4-1-bidpipelinepy]]
- **Step 2: `_download_and_extract()`** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bid-monitoring-pipeline.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[4-1-bidpipelinepy]]
- **Step 3: `_run_analysis_if_needed()`** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bid-monitoring-pipeline.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[4-1-bidpipelinepy]]
- **typescript** (C:\project\tenopa proposer\-agent-master\docs\02-design\features\bid-monitoring-pipeline.design.md) -- 1 connections
  - <- has_code_example <- [[4-5]]

## Internal Relationships
- 4. 상세 설계 -> contains -> 4-1. `bid_pipeline.py` — 파이프라인 오케스트레이터 [EXTRACTED]
- 4. 상세 설계 -> contains -> 4-2. `bid_attachment_store.py` — 첨부파일 다운로드/저장 [EXTRACTED]
- 4. 상세 설계 -> contains -> 4-3. API 변경 — `routes_bids.py` [EXTRACTED]
- 4. 상세 설계 -> contains -> 4-4. `scheduled_monitor.py` 연동 [EXTRACTED]
- 4. 상세 설계 -> contains -> 4-5. 프론트엔드 — 분석 진행 상태 표시 [EXTRACTED]
- 4-1. `bid_pipeline.py` — 파이프라인 오케스트레이터 -> has_code_example -> python [EXTRACTED]
- 4-1. `bid_pipeline.py` — 파이프라인 오케스트레이터 -> contains -> Step 1: `_ensure_bid_in_db()` [EXTRACTED]
- 4-1. `bid_pipeline.py` — 파이프라인 오케스트레이터 -> contains -> Step 2: `_download_and_extract()` [EXTRACTED]
- 4-1. `bid_pipeline.py` — 파이프라인 오케스트레이터 -> contains -> Step 3: `_run_analysis_if_needed()` [EXTRACTED]
- 4-2. `bid_attachment_store.py` — 첨부파일 다운로드/저장 -> has_code_example -> python [EXTRACTED]
- 4-3-1. `/bids/crawl` 후 파이프라인 자동 트리거 -> has_code_example -> python [EXTRACTED]
- 4-3-2. `/bids/pipeline/status` — 진행 상태 조회 -> has_code_example -> python [EXTRACTED]
- 4-3. API 변경 — `routes_bids.py` -> contains -> 4-3-1. `/bids/crawl` 후 파이프라인 자동 트리거 [EXTRACTED]
- 4-3. API 변경 — `routes_bids.py` -> contains -> 4-3-2. `/bids/pipeline/status` — 진행 상태 조회 [EXTRACTED]
- 4-4. `scheduled_monitor.py` 연동 -> has_code_example -> python [EXTRACTED]
- 4-5. 프론트엔드 — 분석 진행 상태 표시 -> has_code_example -> typescript [EXTRACTED]
- Step 1: `_ensure_bid_in_db()` -> has_code_example -> python [EXTRACTED]
- Step 2: `_download_and_extract()` -> has_code_example -> python [EXTRACTED]
- Step 3: `_run_analysis_if_needed()` -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 python, 4. 상세 설계, 4-1. `bid_pipeline.py` — 파이프라인 오케스트레이터를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 bid-monitoring-pipeline.design.md이다.

### Key Facts
- ```python app/services/bid_pipeline.py """ 공고 모니터링 백그라운드 파이프라인.
- 4-1. `bid_pipeline.py` — 파이프라인 오케스트레이터
- ```python app/services/bid_pipeline.py """ 공고 모니터링 백그라운드 파이프라인.
- 4-3-1. `/bids/crawl` 후 파이프라인 자동 트리거
- ```python app/services/bid_attachment_store.py """ G2B 공고 첨부파일 다운로드 + 로컬 캐시 + 텍스트 추출.
