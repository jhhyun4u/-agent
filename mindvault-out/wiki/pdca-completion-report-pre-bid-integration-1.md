# PDCA Completion Report: pre-bid-integration & 1. 목적
Cohesion: 0.25 | Nodes: 8

## Key Nodes
- **PDCA Completion Report: pre-bid-integration** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pre-bid-integration.report.md) -- 7 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4-gap-analysis]]
  - -> contains -> [[5-pre-bid-integration]]
  - -> contains -> [[6]]
  - -> contains -> [[7-pdca]]
- **1. 목적** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pre-bid-integration.report.md) -- 1 connections
  - <- contains <- [[pdca-completion-report-pre-bid-integration]]
- **2. 변경 파일 및 내용** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pre-bid-integration.report.md) -- 1 connections
  - <- contains <- [[pdca-completion-report-pre-bid-integration]]
- **3. 핵심 설계 결정** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pre-bid-integration.report.md) -- 1 connections
  - <- contains <- [[pdca-completion-report-pre-bid-integration]]
- **4. Gap Analysis 결과** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pre-bid-integration.report.md) -- 1 connections
  - <- contains <- [[pdca-completion-report-pre-bid-integration]]
- **5. 세션 내 추가 변경 (pre-bid-integration 외)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pre-bid-integration.report.md) -- 1 connections
  - <- contains <- [[pdca-completion-report-pre-bid-integration]]
- **6. 잔여 사항** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pre-bid-integration.report.md) -- 1 connections
  - <- contains <- [[pdca-completion-report-pre-bid-integration]]
- **7. PDCA 문서** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pre-bid-integration.report.md) -- 1 connections
  - <- contains <- [[pdca-completion-report-pre-bid-integration]]

## Internal Relationships
- PDCA Completion Report: pre-bid-integration -> contains -> 1. 목적 [EXTRACTED]
- PDCA Completion Report: pre-bid-integration -> contains -> 2. 변경 파일 및 내용 [EXTRACTED]
- PDCA Completion Report: pre-bid-integration -> contains -> 3. 핵심 설계 결정 [EXTRACTED]
- PDCA Completion Report: pre-bid-integration -> contains -> 4. Gap Analysis 결과 [EXTRACTED]
- PDCA Completion Report: pre-bid-integration -> contains -> 5. 세션 내 추가 변경 (pre-bid-integration 외) [EXTRACTED]
- PDCA Completion Report: pre-bid-integration -> contains -> 6. 잔여 사항 [EXTRACTED]
- PDCA Completion Report: pre-bid-integration -> contains -> 7. PDCA 문서 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 PDCA Completion Report: pre-bid-integration, 1. 목적, 2. 변경 파일 및 내용를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 pre-bid-integration.report.md이다.

### Key Facts
- | 항목 | 내용 | |------|------| | Feature | pre-bid-integration | | 완료일 | 2026-03-21 | | PDCA 사이클 | Plan → Design → Do → Check → Report (단일 세션) | | Match Rate | **98%** | | Act 이터레이션 | 0회 (98% ≥ 90%) |
- AI 추천(`/api/bids/scored`) 경로에 **사전규격**과 **발주계획** 수집을 통합하여, 입찰공고 게시 전 2~4주 앞서 기회를 포착할 수 있도록 개선.
- | # | 파일 | 변경 | 추가 라인 | |---|------|------|----------| | 1 | `app/services/g2b_service.py` | SERVICE_PREFIX `OrderPlanSttusService: "ao"` + `fetch_all_pre_specs()` + `fetch_all_procurement_plans()` | +90 | | 2 | `app/services/bid_scorer.py` | `normalize_pre_spec_for_scoring()`,…
- | 결정 | 근거 | |------|------| | **정규화 어댑터 패턴** | 사전규격/발주계획 필드를 입찰공고 형식으로 변환 → `score_bid()` 수정 없이 재활용 | | **`asyncio.gather` + `return_exceptions=True`** | 3소스 병렬 수집, 개별 API 실패 시 나머지만으로 결과 반환 | | **`_bid_stage` 마커 필드** | 정규화 dict에 소스 구분 태그 삽입 → BidScore까지 전파 → 프론트 뱃지 | | **수의시담 제외** | `bidMethdNm`에…
- - **62개 설계 항목** 전체 구현 완료 - **미세 차이 2건** (LOW, 의도적 개선): 1. `sources` 타입: 고정 키 → `Record<string, number>` (유연성) 2. 예외 체크: `Exception` → `BaseException` (asyncio 호환) - **검증 8개 항목** 전체 PASS (V1~V8)
