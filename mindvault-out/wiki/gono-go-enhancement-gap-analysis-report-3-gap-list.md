# Go/No-Go Enhancement Gap Analysis Report & 3. Gap List
Cohesion: 0.24 | Nodes: 10

## Key Nodes
- **Go/No-Go Enhancement Gap Analysis Report** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\go-no-go-enhancement\go-no-go-enhancement.analysis.md) -- 6 connections
  - -> references -> [[unresolvedrefgonogoenhancementdesign]]
  - -> contains -> [[1-overall-scores]]
  - -> contains -> [[2-match-rate-calculation]]
  - -> contains -> [[3-gap-list]]
  - -> contains -> [[4-recommended-actions]]
  - -> contains -> [[version-history]]
- **3. Gap List** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\go-no-go-enhancement\go-no-go-enhancement.analysis.md) -- 4 connections
  - -> contains -> [[medium]]
  - -> contains -> [[low]]
  - -> contains -> [[design-x-implementation-o]]
  - <- contains <- [[gono-go-enhancement-gap-analysis-report]]
- **4. Recommended Actions** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\go-no-go-enhancement\go-no-go-enhancement.analysis.md) -- 3 connections
  - -> contains -> [[medium]]
  - -> contains -> [[low]]
  - <- contains <- [[gono-go-enhancement-gap-analysis-report]]
- **LOW (의도적 차이 / 문서 갱신만 필요)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\go-no-go-enhancement\go-no-go-enhancement.analysis.md) -- 2 connections
  - <- contains <- [[3-gap-list]]
  - <- contains <- [[4-recommended-actions]]
- **MEDIUM (수정 필요)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\go-no-go-enhancement\go-no-go-enhancement.analysis.md) -- 2 connections
  - <- contains <- [[3-gap-list]]
  - <- contains <- [[4-recommended-actions]]
- **__unresolved__::ref::go_no_go_enhancement_design** () -- 1 connections
  - <- references <- [[gono-go-enhancement-gap-analysis-report]]
- **1. Overall Scores** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\go-no-go-enhancement\go-no-go-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[gono-go-enhancement-gap-analysis-report]]
- **2. Match Rate Calculation** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\go-no-go-enhancement\go-no-go-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[gono-go-enhancement-gap-analysis-report]]
- **추가 개선 (Design X, Implementation O)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\go-no-go-enhancement\go-no-go-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[3-gap-list]]
- **Version History** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\go-no-go-enhancement\go-no-go-enhancement.analysis.md) -- 1 connections
  - <- contains <- [[gono-go-enhancement-gap-analysis-report]]

## Internal Relationships
- 3. Gap List -> contains -> MEDIUM (수정 필요) [EXTRACTED]
- 3. Gap List -> contains -> LOW (의도적 차이 / 문서 갱신만 필요) [EXTRACTED]
- 3. Gap List -> contains -> 추가 개선 (Design X, Implementation O) [EXTRACTED]
- 4. Recommended Actions -> contains -> MEDIUM (수정 필요) [EXTRACTED]
- 4. Recommended Actions -> contains -> LOW (의도적 차이 / 문서 갱신만 필요) [EXTRACTED]
- Go/No-Go Enhancement Gap Analysis Report -> references -> __unresolved__::ref::go_no_go_enhancement_design [EXTRACTED]
- Go/No-Go Enhancement Gap Analysis Report -> contains -> 1. Overall Scores [EXTRACTED]
- Go/No-Go Enhancement Gap Analysis Report -> contains -> 2. Match Rate Calculation [EXTRACTED]
- Go/No-Go Enhancement Gap Analysis Report -> contains -> 3. Gap List [EXTRACTED]
- Go/No-Go Enhancement Gap Analysis Report -> contains -> 4. Recommended Actions [EXTRACTED]
- Go/No-Go Enhancement Gap Analysis Report -> contains -> Version History [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Go/No-Go Enhancement Gap Analysis Report, 3. Gap List, 4. Recommended Actions를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 go-no-go-enhancement.analysis.md이다.

### Key Facts
- > **Analysis Type**: Design vs Implementation Gap Analysis > > **Project**: 용역제안 Coworker > **Analyst**: AI (gap-detector) > **Date**: 2026-03-26 > **Design Doc**: [go-no-go-enhancement.design.md](../02-design/features/go-no-go-enhancement.design.md)
- 즉시 수정 (MEDIUM) 1. `scripts/seed_data.py`에 "SW품질인증", "여성기업 확인" 시드 2건 추가
- | # | Item | Design | Implementation | Reason | |---|------|--------|----------------|--------| | GAP-1 | score_tag 타입 | `Literal[5종]` | `str` | 런타임 값은 항상 유효, str이 더 유연 | | GAP-2 | 자격 부분충족 fatal | is_fatal=False | "필수" 키워드면 is_fatal=True | 보수적 판단 (비즈니스상 더 안전) | | GAP-3 | _ai_strategic_assessment…
- | # | Item | Design | Implementation | Fix | |---|------|--------|----------------|-----| | GAP-8 | Seed: SW품질인증 + 여성기업 확인 | 11건 정의 | 9건만 구현 | seed_data.py에 2건 추가 |
- | Category | Score | Status | |----------|:-----:|:------:| | Design Match | 94% | PASS | | Scoring Logic Accuracy | 100% | PASS | | Gate Logic (70/85 thresholds) | 100% | PASS | | Frontend Component Match | 96% | PASS | | DB Schema Match | 97% | PASS | | Error Handling / Fallback | 100% | PASS | |…
