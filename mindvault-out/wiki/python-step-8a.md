# python & STEP 8A: 고객 관점 설득 중심 섹션별 검토 설계
Cohesion: 0.15 | Nodes: 19

## Key Nodes
- **python** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 8 connections
  - <- has_code_example <- [[1-proposalcustomeranalysis]]
  - <- has_code_example <- [[ai]]
  - <- has_code_example <- [[2-1-analyzesectionrequirement]]
  - <- has_code_example <- [[2-2-getcustomercentricsectionprompt]]
  - <- has_code_example <- [[2-2-ai-validatesectioncustomerfocus]]
  - <- has_code_example <- [[ui]]
  - <- has_code_example <- [[3-proposalsectionsconsolidation]]
  - <- has_code_example <- [[statepy]]
- **STEP 8A: 고객 관점 설득 중심 섹션별 검토 설계** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 8 connections
  - -> contains -> [[step-8a]]
  - -> contains -> [[1-proposalcustomeranalysis]]
  - -> contains -> [[2-proposalwritecustomercentric]]
  - -> contains -> [[2-2-ai-validatesectioncustomerfocus]]
  - -> contains -> [[2-3-human-review-interrupt]]
  - -> contains -> [[3-proposalsectionsconsolidation]]
  - -> contains -> [[statepy]]
  - <- contains <- [[step-8a]]
- **📊 상태 필드 확장 (state.py)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 7 connections
  - -> has_code_example -> [[python]]
  - -> contains -> [[phase-1-proposalcustomeranalysis]]
  - -> contains -> [[phase-2-proposalwritecustomercentric]]
  - -> contains -> [[phase-3-ai-validatesectioncustomerfocus]]
  - -> contains -> [[phase-4-human-review]]
  - -> contains -> [[phase-5-proposalsectionsconsolidation]]
  - <- contains <- [[step-8a]]
- **✍️ 2️⃣ 섹션별 작성 (proposal_write_customer_centric)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 4 connections
  - -> contains -> [[2-1-analyzesectionrequirement]]
  - -> contains -> [[2-2-getcustomercentricsectionprompt]]
  - -> contains -> [[2-3]]
  - <- contains <- [[step-8a]]
- **🔍 1️⃣ 고객 요구사항 분석 (proposal_customer_analysis)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 3 connections
  - -> has_code_example -> [[python]]
  - -> contains -> [[ai]]
  - <- contains <- [[step-8a]]
- **2-1) 섹션 작성 전 분석 (_analyze_section_requirement)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[2-proposalwritecustomercentric]]
- **2-2) 고객 관점 섹션 프롬프트 (get_customer_centric_section_prompt)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[2-proposalwritecustomercentric]]
- **2-3) 섹션 산출물 예시** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 2 connections
  - -> has_code_example -> [[markdown]]
  - <- contains <- [[2-proposalwritecustomercentric]]
- **🔍 2️⃣-2 섹션 완성 후 AI 자체 검증 (validate_section_customer_focus)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[step-8a]]
- **👤 2️⃣-3 Human Review (Interrupt)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 2 connections
  - -> contains -> [[ui]]
  - <- contains <- [[step-8a]]
- **✅ 3️⃣ 모든 섹션 완성 후 통합 검증 (proposal_sections_consolidation)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[step-8a]]
- **AI 분석 프롬프트** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[1-proposalcustomeranalysis]]
- **화면 UI 정보 (참고용)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[2-3-human-review-interrupt]]
- **markdown** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 1 connections
  - <- has_code_example <- [[2-3]]
- **Phase 1: 고객 분석 (proposal_customer_analysis)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 1 connections
  - <- contains <- [[statepy]]
- **Phase 2: 섹션 작성 강화 (proposal_write_customer_centric)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 1 connections
  - <- contains <- [[statepy]]
- **Phase 3: AI 자체 검증 (validate_section_customer_focus)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 1 connections
  - <- contains <- [[statepy]]
- **Phase 4: Human Review 및 라우팅** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 1 connections
  - <- contains <- [[statepy]]
- **Phase 5: 통합 검증 (proposal_sections_consolidation)** (C:\project\tenopa proposer\-agent-master\docs\02-design\STEP-8A-customer-centric-proposal-review.md) -- 1 connections
  - <- contains <- [[statepy]]

## Internal Relationships
- 🔍 1️⃣ 고객 요구사항 분석 (proposal_customer_analysis) -> has_code_example -> python [EXTRACTED]
- 🔍 1️⃣ 고객 요구사항 분석 (proposal_customer_analysis) -> contains -> AI 분석 프롬프트 [EXTRACTED]
- 2-1) 섹션 작성 전 분석 (_analyze_section_requirement) -> has_code_example -> python [EXTRACTED]
- 2-2) 고객 관점 섹션 프롬프트 (get_customer_centric_section_prompt) -> has_code_example -> python [EXTRACTED]
- 2-3) 섹션 산출물 예시 -> has_code_example -> markdown [EXTRACTED]
- 🔍 2️⃣-2 섹션 완성 후 AI 자체 검증 (validate_section_customer_focus) -> has_code_example -> python [EXTRACTED]
- 👤 2️⃣-3 Human Review (Interrupt) -> contains -> 화면 UI 정보 (참고용) [EXTRACTED]
- ✍️ 2️⃣ 섹션별 작성 (proposal_write_customer_centric) -> contains -> 2-1) 섹션 작성 전 분석 (_analyze_section_requirement) [EXTRACTED]
- ✍️ 2️⃣ 섹션별 작성 (proposal_write_customer_centric) -> contains -> 2-2) 고객 관점 섹션 프롬프트 (get_customer_centric_section_prompt) [EXTRACTED]
- ✍️ 2️⃣ 섹션별 작성 (proposal_write_customer_centric) -> contains -> 2-3) 섹션 산출물 예시 [EXTRACTED]
- ✅ 3️⃣ 모든 섹션 완성 후 통합 검증 (proposal_sections_consolidation) -> has_code_example -> python [EXTRACTED]
- AI 분석 프롬프트 -> has_code_example -> python [EXTRACTED]
- 📊 상태 필드 확장 (state.py) -> has_code_example -> python [EXTRACTED]
- 📊 상태 필드 확장 (state.py) -> contains -> Phase 1: 고객 분석 (proposal_customer_analysis) [EXTRACTED]
- 📊 상태 필드 확장 (state.py) -> contains -> Phase 2: 섹션 작성 강화 (proposal_write_customer_centric) [EXTRACTED]
- 📊 상태 필드 확장 (state.py) -> contains -> Phase 3: AI 자체 검증 (validate_section_customer_focus) [EXTRACTED]
- 📊 상태 필드 확장 (state.py) -> contains -> Phase 4: Human Review 및 라우팅 [EXTRACTED]
- 📊 상태 필드 확장 (state.py) -> contains -> Phase 5: 통합 검증 (proposal_sections_consolidation) [EXTRACTED]
- STEP 8A: 고객 관점 설득 중심 섹션별 검토 설계 -> contains -> STEP 8A: 고객 관점 설득 중심 섹션별 검토 설계 [EXTRACTED]
- STEP 8A: 고객 관점 설득 중심 섹션별 검토 설계 -> contains -> 🔍 1️⃣ 고객 요구사항 분석 (proposal_customer_analysis) [EXTRACTED]
- STEP 8A: 고객 관점 설득 중심 섹션별 검토 설계 -> contains -> ✍️ 2️⃣ 섹션별 작성 (proposal_write_customer_centric) [EXTRACTED]
- STEP 8A: 고객 관점 설득 중심 섹션별 검토 설계 -> contains -> 🔍 2️⃣-2 섹션 완성 후 AI 자체 검증 (validate_section_customer_focus) [EXTRACTED]
- STEP 8A: 고객 관점 설득 중심 섹션별 검토 설계 -> contains -> 👤 2️⃣-3 Human Review (Interrupt) [EXTRACTED]
- STEP 8A: 고객 관점 설득 중심 섹션별 검토 설계 -> contains -> ✅ 3️⃣ 모든 섹션 완성 후 통합 검증 (proposal_sections_consolidation) [EXTRACTED]
- STEP 8A: 고객 관점 설득 중심 섹션별 검토 설계 -> contains -> 📊 상태 필드 확장 (state.py) [EXTRACTED]
- 화면 UI 정보 (참고용) -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 python, STEP 8A: 고객 관점 설득 중심 섹션별 검토 설계, 📊 상태 필드 확장 (state.py)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 STEP-8A-customer-centric-proposal-review.md이다.

### Key Facts
- 입력 ```python { "rfp_analysis": RFPAnalysis,  # eval_items, hot_buttons, mandatory_reqs "strategy": Strategy,          # positioning, win_theme } ```
- > **설계일**: 2026-03-29 > **목표**: 섹션별 작성 & Human 검토 → 고객 니즈 기반 개선 루프 > **핵심 원칙**: "발주기관을 설득한다" = "발주기관의 pain point를 해결한다"
- ```python class ProposalState(TypedDict): # ... 기존 필드들 ...
- 목적 모든 섹션 작성 전에 **발주기관의 관점을 한 번에 정리**하고, 이를 각 섹션의 작성 지침으로 사용합니다.
- ```python async def _analyze_section_requirement( section_id: str, section_title: str, customer_context: dict, eval_items: list ) -> dict: """이 섹션이 충족해야 할 고객 니즈를 정리"""
