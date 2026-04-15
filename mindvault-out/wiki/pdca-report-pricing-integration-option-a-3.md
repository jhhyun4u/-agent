# PDCA Report: pricing-integration (Option A — 통합) & 3. 완료 항목
Cohesion: 0.22 | Nodes: 9

## Key Nodes
- **PDCA Report: pricing-integration (Option A — 통합)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pricing-integration.report.md) -- 6 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4-ui]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
- **3. 완료 항목** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pricing-integration.report.md) -- 3 connections
  - -> contains -> [[option-c]]
  - -> contains -> [[bidplanreviewpanel]]
  - <- contains <- [[pdca-report-pricing-integration-option-a]]
- **1. 개요** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pricing-integration.report.md) -- 1 connections
  - <- contains <- [[pdca-report-pricing-integration-option-a]]
- **2. 의사결정 과정** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pricing-integration.report.md) -- 1 connections
  - <- contains <- [[pdca-report-pricing-integration-option-a]]
- **4. 빠른 견적 UI** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pricing-integration.report.md) -- 1 connections
  - <- contains <- [[pdca-report-pricing-integration-option-a]]
- **5. 라우트 변경** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pricing-integration.report.md) -- 1 connections
  - <- contains <- [[pdca-report-pricing-integration-option-a]]
- **6. 교훈** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pricing-integration.report.md) -- 1 connections
  - <- contains <- [[pdca-report-pricing-integration-option-a]]
- **유지 (기존 하위 컴포넌트, BidPlanReviewPanel에서 사용)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pricing-integration.report.md) -- 1 connections
  - <- contains <- [[3]]
- **유지 (Option C에서 구현, 그대로 활용)** (C:\project\tenopa proposer\-agent-master\docs\04-report\features\pricing-integration.report.md) -- 1 connections
  - <- contains <- [[3]]

## Internal Relationships
- 3. 완료 항목 -> contains -> 유지 (Option C에서 구현, 그대로 활용) [EXTRACTED]
- 3. 완료 항목 -> contains -> 유지 (기존 하위 컴포넌트, BidPlanReviewPanel에서 사용) [EXTRACTED]
- PDCA Report: pricing-integration (Option A — 통합) -> contains -> 1. 개요 [EXTRACTED]
- PDCA Report: pricing-integration (Option A — 통합) -> contains -> 2. 의사결정 과정 [EXTRACTED]
- PDCA Report: pricing-integration (Option A — 통합) -> contains -> 3. 완료 항목 [EXTRACTED]
- PDCA Report: pricing-integration (Option A — 통합) -> contains -> 4. 빠른 견적 UI [EXTRACTED]
- PDCA Report: pricing-integration (Option A — 통합) -> contains -> 5. 라우트 변경 [EXTRACTED]
- PDCA Report: pricing-integration (Option A — 통합) -> contains -> 6. 교훈 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 PDCA Report: pricing-integration (Option A — 통합), 3. 완료 항목, 1. 개요를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 pricing-integration.report.md이다.

### Key Facts
- > 독립 가격 시뮬레이터 제거 + 워크플로 집중 + 빠른 견적 이관
- 삭제 | 파일 | 설명 | |------|------| | `app/(app)/pricing/page.tsx` | 독립 시뮬레이터 페이지 | | `app/(app)/pricing/history/page.tsx` | 시뮬레이션 이력 페이지 | | `components/pricing/PricingSimulator.tsx` | 독립 시뮬레이터 컴포넌트 |
- | 항목 | 내용 | |------|------| | Feature | pricing-integration | | 기간 | 2026-03-26 (단일 세션) | | 최초 방향 | Option C (양립) → 구현 완료 | | 최종 방향 | Option A (통합) → 방향 전환 후 재구현 | | 빌드 | TypeScript 에러 0, 경고 0, 정적 페이지 29개 |
- 1. 독립 도구 vs 워크플로 통합 검토 → 3가지 옵션 제시 2. Option C(양립) 채택 → 구현 완료 (apply 엔드포인트 + 프로젝트 연결 + 시뮬레이션 불러오기) 3. 재검토 후 **Option A(통합)로 전환** — 이용자가 맥락 없이 시뮬레이션하는 경우가 드물다고 판단
- `/proposals/new` — 공고 모니터링에서 진입 시, 예산이 있는 공고에만 표시:
