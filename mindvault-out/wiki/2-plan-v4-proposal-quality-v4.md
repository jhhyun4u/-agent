# 2. 변경 계획 & Plan: 제안서 품질 강화 v4 (proposal-quality-v4)
Cohesion: 0.22 | Nodes: 10

## Key Nodes
- **2. 변경 계획** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.plan.md) -- 4 connections
  - -> contains -> [[2-1-bidpricestrategy]]
  - -> contains -> [[2-2-risksmitigations]]
  - -> contains -> [[2-3-phase4system-price-anchoring]]
  - <- contains <- [[plan-v4-proposal-quality-v4]]
- **Plan: 제안서 품질 강화 v4 (proposal-quality-v4)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.plan.md) -- 4 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3-yagni]]
  - -> contains -> [[4]]
- **json** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.plan.md) -- 2 connections
  - <- has_code_example <- [[2-1-bidpricestrategy]]
  - <- has_code_example <- [[2-2-risksmitigations]]
- **2-1. bid_price_strategy — 시나리오화 + 가치 기반 논리 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.plan.md) -- 2 connections
  - -> has_code_example -> [[json]]
  - <- contains <- [[2]]
- **2-2. risks_mitigations — 숫자 점수화** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.plan.md) -- 2 connections
  - -> has_code_example -> [[json]]
  - <- contains <- [[2]]
- **3. YAGNI 검토** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.plan.md) -- 2 connections
  - -> contains -> [[v4]]
  - <- contains <- [[plan-v4-proposal-quality-v4]]
- **1. 핵심 문제** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.plan.md) -- 1 connections
  - <- contains <- [[plan-v4-proposal-quality-v4]]
- **2-3. PHASE4_SYSTEM — Price Anchoring 원칙 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **4. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.plan.md) -- 1 connections
  - <- contains <- [[plan-v4-proposal-quality-v4]]
- **v4 포함** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.plan.md) -- 1 connections
  - <- contains <- [[3-yagni]]

## Internal Relationships
- 2. 변경 계획 -> contains -> 2-1. bid_price_strategy — 시나리오화 + 가치 기반 논리 추가 [EXTRACTED]
- 2. 변경 계획 -> contains -> 2-2. risks_mitigations — 숫자 점수화 [EXTRACTED]
- 2. 변경 계획 -> contains -> 2-3. PHASE4_SYSTEM — Price Anchoring 원칙 추가 [EXTRACTED]
- 2-1. bid_price_strategy — 시나리오화 + 가치 기반 논리 추가 -> has_code_example -> json [EXTRACTED]
- 2-2. risks_mitigations — 숫자 점수화 -> has_code_example -> json [EXTRACTED]
- 3. YAGNI 검토 -> contains -> v4 포함 [EXTRACTED]
- Plan: 제안서 품질 강화 v4 (proposal-quality-v4) -> contains -> 1. 핵심 문제 [EXTRACTED]
- Plan: 제안서 품질 강화 v4 (proposal-quality-v4) -> contains -> 2. 변경 계획 [EXTRACTED]
- Plan: 제안서 품질 강화 v4 (proposal-quality-v4) -> contains -> 3. YAGNI 검토 [EXTRACTED]
- Plan: 제안서 품질 강화 v4 (proposal-quality-v4) -> contains -> 4. 성공 기준 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 2. 변경 계획, Plan: 제안서 품질 강화 v4 (proposal-quality-v4), json를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-quality-v4.plan.md이다.

### Key Facts
- 2-1. bid_price_strategy — 시나리오화 + 가치 기반 논리 추가
- ```json "bid_price_strategy": { "value_basis": "발주처가 이 사업에서 인지하는 핵심 가치 (정량적 효과 추정, 예: 업무 효율 30% 향상 = 연 X억 절감)", "scenarios": { "bear": { "price_ratio": "85%", "condition": "경쟁사 3개 이상, 가격 경쟁 심화 시" }, "base": { "price_ratio": "88%", "condition": "일반적 경쟁 환경 (기본 추천)" }, "bull": { "price_ratio": "92%",…
- ```json "bid_price_strategy": { "value_basis": "발주처가 이 사업에서 인지하는 핵심 가치 (정량적 효과 추정, 예: 업무 효율 30% 향상 = 연 X억 절감)", "scenarios": { "bear": { "price_ratio": "85%", "condition": "경쟁사 3개 이상, 가격 경쟁 심화 시" }, "base": { "price_ratio": "88%", "condition": "일반적 경쟁 환경 (기본 추천)" }, "bull": { "price_ratio": "92%",…
- ```json "risks_mitigations": [{ "risk": "리스크 설명", "probability": 3,       // 1(매우 낮음)~5(매우 높음) "impact": 4,            // 1(경미)~5(치명적) "risk_score": 12,       // probability × impact (자동 계산) "priority": "high",     // 20-25:critical, 12-19:high, 6-11:medium, 1-5:low "mitigation": "대응 방안" }] ```
- v4 포함 - PHASE3_USER: `bid_price_strategy` 구조 확장 (value_basis + scenarios) - PHASE3_USER: `risks_mitigations` 숫자화 (probability/impact 1-5 + risk_score + priority) - PHASE3_USER: 지침 2줄 추가 - PHASE4_SYSTEM: Price Anchoring 원칙 1줄
