# api-response-standardization Gap Analysis & 1. Category Scores (after iteration 1)
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **api-response-standardization Gap Analysis** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\api-response-standardization\api-response-standardization.analysis.md) -- 4 connections
  - -> contains -> [[1-category-scores-after-iteration-1]]
  - -> contains -> [[2-gaps-all-resolved]]
  - -> contains -> [[3]]
  - -> contains -> [[4-low]]
- **1. Category Scores (after iteration 1)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\api-response-standardization\api-response-standardization.analysis.md) -- 1 connections
  - <- contains <- [[api-response-standardization-gap-analysis]]
- **2. Gaps (all resolved)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\api-response-standardization\api-response-standardization.analysis.md) -- 1 connections
  - <- contains <- [[api-response-standardization-gap-analysis]]
- **3. 최종 검증 결과** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\api-response-standardization\api-response-standardization.analysis.md) -- 1 connections
  - <- contains <- [[api-response-standardization-gap-analysis]]
- **4. 잔여 LOW 항목** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\api-response-standardization\api-response-standardization.analysis.md) -- 1 connections
  - <- contains <- [[api-response-standardization-gap-analysis]]

## Internal Relationships
- api-response-standardization Gap Analysis -> contains -> 1. Category Scores (after iteration 1) [EXTRACTED]
- api-response-standardization Gap Analysis -> contains -> 2. Gaps (all resolved) [EXTRACTED]
- api-response-standardization Gap Analysis -> contains -> 3. 최종 검증 결과 [EXTRACTED]
- api-response-standardization Gap Analysis -> contains -> 4. 잔여 LOW 항목 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 api-response-standardization Gap Analysis, 1. Category Scores (after iteration 1), 2. Gaps (all resolved)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 api-response-standardization.analysis.md이다.

### Key Facts
- > **Feature**: api-response-standardization > **Date**: 2026-03-26 > **Design Doc**: `docs/02-design/features/api-response-standardization.design.md` (v1.0) > **Overall Match Rate**: **72%** → **99%** (after iteration 1) > **Status**: PASS
- | Category | v0 | v1 | Status | |----------|:--:|:--:|:------:| | response.py module (§2.1) | 100% | 100% | PASS | | Route wrapper adoption (§3) | 87% | 100% | PASS | | response_model removal (§2.2) | 0% | 100% | PASS | | Exception preservation (§3.4) | 100% | 100% | PASS | | Frontend types (§4.1)…
- | ID | Severity | Description | Resolution | |----|:--------:|------------|-----------| | ~~GAP-1~~ | ~~HIGH~~ | routes_proposal.py 미래핑 | ✅ 4 return문 ok()/ok_list() 래핑 | | ~~GAP-2~~ | ~~MEDIUM~~ | routes_auth.py 2/3 Pydantic 직접 반환 | ✅ ok(None, message=) 래핑 | | ~~GAP-3~~ | ~~MEDIUM~~ |…
- ``` grep "response_model=" routes_*.py     → 0건 (g2b/v31 제외) grep 'return {"items":' routes_*.py    → 0건 grep 'return {"status": "ok"' routes_*.py → 1건 (routes_g2b.py — 예외 정상) ```
- | # | 항목 | 비고 | |---|------|------| | 1 | routes_g2b.py 예외 유지 | 설계 §3.4 의도적 예외 | | 2 | routes_v31.py 예외 유지 | 레거시 삭제 예정 |
