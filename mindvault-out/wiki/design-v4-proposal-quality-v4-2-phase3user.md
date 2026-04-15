# Design: 제안서 품질 강화 v4 (proposal-quality-v4) & 2. PHASE3_USER 변경 설계
Cohesion: 0.20 | Nodes: 12

## Key Nodes
- **Design: 제안서 품질 강화 v4 (proposal-quality-v4)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.design.md) -- 5 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-phase3user]]
  - -> contains -> [[3-phase4system]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
- **2. PHASE3_USER 변경 설계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.design.md) -- 4 connections
  - -> contains -> [[2-1-bidpricestrategy]]
  - -> contains -> [[2-2-risksmitigations]]
  - -> contains -> [[2-3-2]]
  - <- contains <- [[design-v4-proposal-quality-v4]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.design.md) -- 3 connections
  - <- has_code_example <- [[2-1-bidpricestrategy]]
  - <- has_code_example <- [[2-2-risksmitigations]]
  - <- has_code_example <- [[3-phase4system]]
- **4. 변경 전후 비교** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.design.md) -- 3 connections
  - -> contains -> [[phase3user]]
  - -> contains -> [[phase4system]]
  - <- contains <- [[design-v4-proposal-quality-v4]]
- **2-1. bid_price_strategy 구조 교체** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[2-phase3user]]
- **2-2. risks_mitigations 구조 교체** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[2-phase3user]]
- **3. PHASE4_SYSTEM 변경 설계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[design-v4-proposal-quality-v4]]
- **1. 변경 파일** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.design.md) -- 1 connections
  - <- contains <- [[design-v4-proposal-quality-v4]]
- **2-3. 작성 지침 2줄 추가 (기존 지침 끝에)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.design.md) -- 1 connections
  - <- contains <- [[2-phase3user]]
- **5. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.design.md) -- 1 connections
  - <- contains <- [[design-v4-proposal-quality-v4]]
- **PHASE3_USER 필드 변화** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.design.md) -- 1 connections
  - <- contains <- [[4]]
- **PHASE4_SYSTEM 원칙 변화** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-quality-v4\proposal-quality-v4.design.md) -- 1 connections
  - <- contains <- [[4]]

## Internal Relationships
- 2-1. bid_price_strategy 구조 교체 -> has_code_example -> python [EXTRACTED]
- 2-2. risks_mitigations 구조 교체 -> has_code_example -> python [EXTRACTED]
- 2. PHASE3_USER 변경 설계 -> contains -> 2-1. bid_price_strategy 구조 교체 [EXTRACTED]
- 2. PHASE3_USER 변경 설계 -> contains -> 2-2. risks_mitigations 구조 교체 [EXTRACTED]
- 2. PHASE3_USER 변경 설계 -> contains -> 2-3. 작성 지침 2줄 추가 (기존 지침 끝에) [EXTRACTED]
- 3. PHASE4_SYSTEM 변경 설계 -> has_code_example -> python [EXTRACTED]
- 4. 변경 전후 비교 -> contains -> PHASE3_USER 필드 변화 [EXTRACTED]
- 4. 변경 전후 비교 -> contains -> PHASE4_SYSTEM 원칙 변화 [EXTRACTED]
- Design: 제안서 품질 강화 v4 (proposal-quality-v4) -> contains -> 1. 변경 파일 [EXTRACTED]
- Design: 제안서 품질 강화 v4 (proposal-quality-v4) -> contains -> 2. PHASE3_USER 변경 설계 [EXTRACTED]
- Design: 제안서 품질 강화 v4 (proposal-quality-v4) -> contains -> 3. PHASE4_SYSTEM 변경 설계 [EXTRACTED]
- Design: 제안서 품질 강화 v4 (proposal-quality-v4) -> contains -> 4. 변경 전후 비교 [EXTRACTED]
- Design: 제안서 품질 강화 v4 (proposal-quality-v4) -> contains -> 5. 성공 기준 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Design: 제안서 품질 강화 v4 (proposal-quality-v4), 2. PHASE3_USER 변경 설계, python를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-quality-v4.design.md이다.

### Key Facts
- 2-1. bid_price_strategy 구조 교체
- **변경 전 (line 144-148):** ```python "bid_price_strategy": {{ "recommended_price_ratio": "예산 대비 추천 입찰가 비율 (예: 88%)", "rationale": "이 입찰가를 추천하는 이유 (기술-가격 트레이드오프, 경쟁 예상 가격 포함, 3문장)", "price_competitiveness_message": "제안서 본문에서 가격 경쟁력을 어필하는 방식 (1~2문장)" }}, ```
- **변경 전 (line 144-148):** ```python "bid_price_strategy": {{ "recommended_price_ratio": "예산 대비 추천 입찰가 비율 (예: 88%)", "rationale": "이 입찰가를 추천하는 이유 (기술-가격 트레이드오프, 경쟁 예상 가격 포함, 3문장)", "price_competitiveness_message": "제안서 본문에서 가격 경쟁력을 어필하는 방식 (1~2문장)" }}, ```
- **변경 전 (line 156-163):** ```python "risks_mitigations": [ {{ "risk": "사업 수행 중 발생 가능한 리스크 (구체적)", "probability": "high/medium/low", "impact": "high/medium/low", "mitigation": "구체적 선제 대응 방안" }} ], ```
- **추가 위치:** `반론 선제 대응(Objection Handling)` 원칙 다음 줄
