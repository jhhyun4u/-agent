# 2. Detailed Comparison & prompt-admin v2.0 Gap Analysis
Cohesion: 0.12 | Nodes: 17

## Key Nodes
- **2. Detailed Comparison** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 7 connections
  - -> contains -> [[21-db-schema-4-100]]
  - -> contains -> [[22-backend-service-promptanalyzerpy-5-98]]
  - -> contains -> [[23-api-endpoints-6-100]]
  - -> contains -> [[24-frontend-pages-7-98]]
  - -> contains -> [[25-frontend-components-8-96]]
  - -> contains -> [[26-apits-10-100]]
  - <- contains <- [[prompt-admin-v20-gap-analysis]]
- **prompt-admin v2.0 Gap Analysis** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 7 connections
  - -> contains -> [[1-category-scores]]
  - -> contains -> [[2-detailed-comparison]]
  - -> contains -> [[3-gap-summary]]
  - -> contains -> [[4-implementation-order-verification-9]]
  - -> contains -> [[5-file-summary]]
  - -> contains -> [[6-design-goals]]
  - -> contains -> [[7-conclusion]]
- **7. Conclusion** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 3 connections
  - -> contains -> [[gap-2-2026-03-26]]
  - -> contains -> [[low]]
  - <- contains <- [[prompt-admin-v20-gap-analysis]]
- **5. File Summary** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 2 connections
  - -> contains -> [[vs]]
  - <- contains <- [[prompt-admin-v20-gap-analysis]]
- **1. Category Scores** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 1 connections
  - <- contains <- [[prompt-admin-v20-gap-analysis]]
- **2.1 DB Schema (§4) — 100%** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 1 connections
  - <- contains <- [[2-detailed-comparison]]
- **2.2 Backend Service — prompt_analyzer.py (§5) — 98%** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 1 connections
  - <- contains <- [[2-detailed-comparison]]
- **2.3 API Endpoints (§6) — 100%** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 1 connections
  - <- contains <- [[2-detailed-comparison]]
- **2.4 Frontend Pages (§7) — 98%** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 1 connections
  - <- contains <- [[2-detailed-comparison]]
- **2.5 Frontend Components (§8) — 96%** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 1 connections
  - <- contains <- [[2-detailed-comparison]]
- **2.6 api.ts 타입 + 메서드 (§10) — 100%** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 1 connections
  - <- contains <- [[2-detailed-comparison]]
- **3. Gap Summary** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 1 connections
  - <- contains <- [[prompt-admin-v20-gap-analysis]]
- **4. Implementation Order Verification (§9)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 1 connections
  - <- contains <- [[prompt-admin-v20-gap-analysis]]
- **6. Design Goals 달성 평가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 1 connections
  - <- contains <- [[prompt-admin-v20-gap-analysis]]
- **GAP-2 해소 내역 (2026-03-26)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 1 connections
  - <- contains <- [[7-conclusion]]
- **잔여 LOW 항목** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 1 connections
  - <- contains <- [[7-conclusion]]
- **설계 명세 vs 실제** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\prompt-admin-v2\prompt-admin-v2.analysis.md) -- 1 connections
  - <- contains <- [[5-file-summary]]

## Internal Relationships
- 2. Detailed Comparison -> contains -> 2.1 DB Schema (§4) — 100% [EXTRACTED]
- 2. Detailed Comparison -> contains -> 2.2 Backend Service — prompt_analyzer.py (§5) — 98% [EXTRACTED]
- 2. Detailed Comparison -> contains -> 2.3 API Endpoints (§6) — 100% [EXTRACTED]
- 2. Detailed Comparison -> contains -> 2.4 Frontend Pages (§7) — 98% [EXTRACTED]
- 2. Detailed Comparison -> contains -> 2.5 Frontend Components (§8) — 96% [EXTRACTED]
- 2. Detailed Comparison -> contains -> 2.6 api.ts 타입 + 메서드 (§10) — 100% [EXTRACTED]
- 5. File Summary -> contains -> 설계 명세 vs 실제 [EXTRACTED]
- 7. Conclusion -> contains -> GAP-2 해소 내역 (2026-03-26) [EXTRACTED]
- 7. Conclusion -> contains -> 잔여 LOW 항목 [EXTRACTED]
- prompt-admin v2.0 Gap Analysis -> contains -> 1. Category Scores [EXTRACTED]
- prompt-admin v2.0 Gap Analysis -> contains -> 2. Detailed Comparison [EXTRACTED]
- prompt-admin v2.0 Gap Analysis -> contains -> 3. Gap Summary [EXTRACTED]
- prompt-admin v2.0 Gap Analysis -> contains -> 4. Implementation Order Verification (§9) [EXTRACTED]
- prompt-admin v2.0 Gap Analysis -> contains -> 5. File Summary [EXTRACTED]
- prompt-admin v2.0 Gap Analysis -> contains -> 6. Design Goals 달성 평가 [EXTRACTED]
- prompt-admin v2.0 Gap Analysis -> contains -> 7. Conclusion [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 2. Detailed Comparison, prompt-admin v2.0 Gap Analysis, 7. Conclusion를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 prompt-admin-v2.analysis.md이다.

### Key Facts
- 2.1 DB Schema (§4) — 100%
- > **Feature**: prompt-admin-v2 > **Date**: 2026-03-26 > **Design Doc**: `docs/02-design/features/prompt-admin-v2.design.md` (v2.0) > **Overall Match Rate**: **100%** > **Status**: PASS
- **Overall Match Rate: 100%** — PASS (≥90% threshold).
- | Category | Score | Status | |----------|:-----:|:------:| | DB Schema (§4) | 100% | PASS | | Backend Service — prompt_analyzer.py (§5) | 98% | PASS | | API Endpoints (§6) | 100% | PASS | | Frontend Pages (§7) | 98% | PASS | | Frontend Components (§8) | 96% | PASS | | api.ts 타입 + 메서드 (§10) | 100%…
- | Design | Implementation | Match | |--------|---------------|:-----:| | `prompt_analysis_snapshots` 테이블 | `013_prompt_analysis.sql` | ✅ | | 컬럼: id, prompt_id, period_start, period_end | 완전 일치 | ✅ | | 컬럼: proposals_used, win_count, loss_count, win_rate | 완전 일치 | ✅ | | 컬럼: avg_quality,…
