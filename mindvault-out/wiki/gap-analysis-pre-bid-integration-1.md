# Gap Analysis: pre-bid-integration & 1. 섹션별 분석
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **Gap Analysis: pre-bid-integration** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\pre-bid-integration.analysis.md) -- 4 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-low]]
  - -> contains -> [[3-design-9]]
  - -> contains -> [[4]]
- **1. 섹션별 분석** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\pre-bid-integration.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-pre-bid-integration]]
- **2. 미세 차이 (LOW — 조치 불요)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\pre-bid-integration.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-pre-bid-integration]]
- **3. 검증 항목 (Design §9)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\pre-bid-integration.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-pre-bid-integration]]
- **4. 결론** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\pre-bid-integration.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-pre-bid-integration]]

## Internal Relationships
- Gap Analysis: pre-bid-integration -> contains -> 1. 섹션별 분석 [EXTRACTED]
- Gap Analysis: pre-bid-integration -> contains -> 2. 미세 차이 (LOW — 조치 불요) [EXTRACTED]
- Gap Analysis: pre-bid-integration -> contains -> 3. 검증 항목 (Design §9) [EXTRACTED]
- Gap Analysis: pre-bid-integration -> contains -> 4. 결론 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Gap Analysis: pre-bid-integration, 1. 섹션별 분석, 2. 미세 차이 (LOW — 조치 불요)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 pre-bid-integration.analysis.md이다.

### Key Facts
- | 항목 | 내용 | |------|------| | Feature | pre-bid-integration | | 버전 | v1.0 | | 분석일 | 2026-03-21 | | Design 참조 | `docs/02-design/features/pre-bid-integration.design.md` | | **Match Rate** | **98%** |
- | Section | 설계 항목 | 항목 수 | 일치 | 점수 | |---------|----------|:------:|:----:|:----:| | §2 G2B API (`g2b_service.py`) | SERVICE_PREFIX, fetch_all_pre_specs, fetch_all_procurement_plans | 15 | 15 | 100% | | §3 스코어러 (`bid_scorer.py`) | normalize 어댑터 x2, BidScore.bid_stage, _NOISE_PREFIXES | 20 | 20 |…
- | # | 항목 | 설계 | 구현 | 심각도 | 판정 | |---|------|------|------|:------:|:----:| | 1 | `sources` 타입 (api.ts) | `{ 입찰공고: number; 사전규격: number; 발주계획: number }` (고정 키) | `Record<string, number>` (동적 키) | LOW | 의도적 — 유연성 확보 | | 2 | 예외 타입 체크 (bid_fetcher.py) | `isinstance(_, Exception)` | `isinstance(_,…
- | # | 검증 | 결과 | 근거 | |---|------|:----:|------| | V1 | `/api/bids/scored` 응답에 `sources` 필드 | PASS | `routes_bids.py:422` | | V2 | 사전규격 API 미신청 → graceful skip | PASS | `g2b_service.py` fetch_all_pre_specs 첫 페이지 except → `[]` | | V3 | 발주계획 API 미신청 → graceful skip | PASS | `g2b_service.py`…
- **Match Rate 98% ≥ 90% — Act 이터레이션 불요.**
