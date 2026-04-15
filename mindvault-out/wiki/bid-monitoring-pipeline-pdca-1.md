# bid-monitoring-pipeline — PDCA 완료 보고서 & 1. 요약
Cohesion: 0.22 | Nodes: 9

## Key Nodes
- **bid-monitoring-pipeline — PDCA 완료 보고서** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\bid-monitoring-pipeline.report.md) -- 7 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7-pdca]]
- **1. 요약** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\bid-monitoring-pipeline.report.md) -- 2 connections
  - -> contains -> [[before-after]]
  - <- contains <- [[bid-monitoring-pipeline-pdca]]
- **2. 구현 내역** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\bid-monitoring-pipeline.report.md) -- 1 connections
  - <- contains <- [[bid-monitoring-pipeline-pdca]]
- **3. 파이프라인 흐름** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\bid-monitoring-pipeline.report.md) -- 1 connections
  - <- contains <- [[bid-monitoring-pipeline-pdca]]
- **4. 갭 분석 결과** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\bid-monitoring-pipeline.report.md) -- 1 connections
  - <- contains <- [[bid-monitoring-pipeline-pdca]]
- **5. 기술 결정** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\bid-monitoring-pipeline.report.md) -- 1 connections
  - <- contains <- [[bid-monitoring-pipeline-pdca]]
- **6. 잔여 작업 / 향후 개선** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\bid-monitoring-pipeline.report.md) -- 1 connections
  - <- contains <- [[bid-monitoring-pipeline-pdca]]
- **7. PDCA 사이클 요약** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\bid-monitoring-pipeline.report.md) -- 1 connections
  - <- contains <- [[bid-monitoring-pipeline-pdca]]
- **Before → After** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\bid-monitoring-pipeline.report.md) -- 1 connections
  - <- contains <- [[1]]

## Internal Relationships
- 1. 요약 -> contains -> Before → After [EXTRACTED]
- bid-monitoring-pipeline — PDCA 완료 보고서 -> contains -> 1. 요약 [EXTRACTED]
- bid-monitoring-pipeline — PDCA 완료 보고서 -> contains -> 2. 구현 내역 [EXTRACTED]
- bid-monitoring-pipeline — PDCA 완료 보고서 -> contains -> 3. 파이프라인 흐름 [EXTRACTED]
- bid-monitoring-pipeline — PDCA 완료 보고서 -> contains -> 4. 갭 분석 결과 [EXTRACTED]
- bid-monitoring-pipeline — PDCA 완료 보고서 -> contains -> 5. 기술 결정 [EXTRACTED]
- bid-monitoring-pipeline — PDCA 완료 보고서 -> contains -> 6. 잔여 작업 / 향후 개선 [EXTRACTED]
- bid-monitoring-pipeline — PDCA 완료 보고서 -> contains -> 7. PDCA 사이클 요약 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 bid-monitoring-pipeline — PDCA 완료 보고서, 1. 요약, 2. 구현 내역를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 bid-monitoring-pipeline.report.md이다.

### Key Facts
- | 항목 | 내용 | |------|------| | 피처명 | 공고 모니터링 백그라운드 파이프라인 | | PDCA 완료일 | 2026-03-25 | | Match Rate | **97%** (BUG-1 수정 후) | | 신규 파일 | 2개 | | 수정 파일 | 3개 | | 총 코드량 | ~450줄 (Python 350 + TypeScript 100) |
- 공고 모니터링 시스템의 **클릭 시 실시간 처리(30초+)** 병목을 해결하기 위해, scored/crawl 결과를 **백그라운드에서 사전 처리**하는 파이프라인을 구축했다.
- ``` Trigger (crawl/monitor/manual) │ ▼ Step 1: ensure_bid_in_db() │ DB 존재 확인 → 없으면 G2B API 조회 → upsert ▼ Step 2: download_and_extract() │ raw_data에서 첨부파일 URL 추출 │ → 우선순위: 제안요청서 > 과업지시서 > 공고문 (최대 3파일) │ → 로컬 캐시: data/bid_attachments/{bid_no}/ │ → 텍스트 추출 → content_text DB 저장 ▼ Step 3:…
- | 항목 | 건수 | 조치 | |------|:----:|------| | HIGH (BUG) | 1 | `scheduled_monitor.py` dict→dataclass 접근 수정 **완료** | | MEDIUM (ADD) | 1 | `/bids/pipeline/trigger` 엔드포인트 — 설계 보완 가능 | | LOW | 7 | 의도적 변경/코드 품질 개선 — 조치 불필요 |
- | 결정 | 근거 | |------|------| | 로컬 파일 캐시 (Supabase Storage 대신) | Supabase 불안정 → 로컬이 더 신뢰성 높음 | | Semaphore(5) 동시성 제한 | G2B rate limit + Claude API 보호 | | score >= 80/100 임계값 | Claude API 비용 관리 (100회/일 이내) | | 인메모리 파이프라인 상태 | 30분 TTL, 서버 재시작 시 초기화 (충분) |
