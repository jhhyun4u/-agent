# python & 29. ★ ProposalForge 프롬프트 설계 통합 (v3.2)
Cohesion: 0.14 | Nodes: 21

## Key Nodes
- **python** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 12 connections
  - <- has_code_example <- [[16-1]]
  - <- has_code_example <- [[16-3-1]]
  - <- has_code_example <- [[16-3-2-sourcetaggerpy]]
  - <- has_code_example <- [[16-3-3-4]]
  - <- has_code_example <- [[rfp]]
  - <- has_code_example <- [[29-3-presentationstrategy]]
  - <- has_code_example <- [[29-4-gonogo-5]]
  - <- has_code_example <- [[29-5-strategygenerate-swot]]
  - <- has_code_example <- [[29-6-planprice]]
  - <- has_code_example <- [[29-7-selfreview-3]]
  - <- has_code_example <- [[29-8-proposalsection]]
  - <- has_code_example <- [[29-9-ppt]]
- **29. ★ ProposalForge 프롬프트 설계 통합 (v3.2)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 11 connections
  - -> contains -> [[29-1]]
  - -> contains -> [[29-2-researchgather]]
  - -> contains -> [[29-3-presentationstrategy]]
  - -> contains -> [[29-4-gonogo-5]]
  - -> contains -> [[29-5-strategygenerate-swot]]
  - -> contains -> [[29-6-planprice]]
  - -> contains -> [[29-7-selfreview-3]]
  - -> contains -> [[29-8-proposalsection]]
  - -> contains -> [[29-9-ppt]]
  - -> contains -> [[29-10]]
  - -> contains -> [[29-11-proposalforge-tenopa]]
- **16-3. ★ v3.0 AI 산출물 신뢰성 규칙 (TRS-01~12 구현)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 4 connections
  - -> contains -> [[16-3-1]]
  - -> contains -> [[16-3-2-sourcetaggerpy]]
  - -> contains -> [[16-3-3-4]]
  - <- contains <- [[16]]
- **16. 프롬프트 설계 원칙** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 3 connections
  - -> contains -> [[16-1]]
  - -> contains -> [[16-2]]
  - -> contains -> [[16-3-v30-ai-trs-0112]]
- **16-1. 공통 컨텍스트 주입** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[16]]
- **16-3-1. 시스템 프롬프트 — 신뢰성 지시 블록** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[16-3-v30-ai-trs-0112]]
- **16-3-2. 출처 태그 후처리 — source_tagger.py** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[16-3-v30-ai-trs-0112]]
- **16-3-3. 자가진단 4축 확장 — 근거 신뢰성 축 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[16-3-v30-ai-trs-0112]]
- **29-2. 신규 노드: `research_gather`** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 2 connections
  - -> contains -> [[rfp]]
  - <- contains <- [[29-proposalforge-v32]]
- **29-3. 신규 노드: `presentation_strategy`** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[29-proposalforge-v32]]
- **29-4. 기존 프롬프트 보강 — `go_no_go` (발주기관 인텔리전스 5단계)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[29-proposalforge-v32]]
- **29-5. 기존 프롬프트 보강 — `strategy_generate` (경쟁 SWOT + 시나리오 + 연구질문)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[29-proposalforge-v32]]
- **29-6. 기존 프롬프트 보강 — `plan_price` (원가기준·노임단가·입찰시뮬레이션)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[29-proposalforge-v32]]
- **29-7. 기존 프롬프트 보강 — `self_review` (3인 페르소나 시뮬레이션)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[29-proposalforge-v32]]
- **29-8. 기존 프롬프트 보강 — `proposal_section` (자체검증 체크리스트)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[29-proposalforge-v32]]
- **29-9. PPT 프롬프트 신규 생성** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[29-proposalforge-v32]]
- **핵심 설계 원칙: RFP-적응형 리서치** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[29-2-researchgather]]
- **16-2. 단계별 프롬프트 핵심** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 1 connections
  - <- contains <- [[16]]
- **29-1. 그래프 플로우 변경 요약** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 1 connections
  - <- contains <- [[29-proposalforge-v32]]
- **29-10. 토큰 예산 갱신 요약** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 1 connections
  - <- contains <- [[29-proposalforge-v32]]
- **29-11. ProposalForge 에이전트 → TENOPA 노드 매핑 참조표** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 1 connections
  - <- contains <- [[29-proposalforge-v32]]

## Internal Relationships
- 16. 프롬프트 설계 원칙 -> contains -> 16-1. 공통 컨텍스트 주입 [EXTRACTED]
- 16. 프롬프트 설계 원칙 -> contains -> 16-2. 단계별 프롬프트 핵심 [EXTRACTED]
- 16. 프롬프트 설계 원칙 -> contains -> 16-3. ★ v3.0 AI 산출물 신뢰성 규칙 (TRS-01~12 구현) [EXTRACTED]
- 16-1. 공통 컨텍스트 주입 -> has_code_example -> python [EXTRACTED]
- 16-3-1. 시스템 프롬프트 — 신뢰성 지시 블록 -> has_code_example -> python [EXTRACTED]
- 16-3-2. 출처 태그 후처리 — source_tagger.py -> has_code_example -> python [EXTRACTED]
- 16-3-3. 자가진단 4축 확장 — 근거 신뢰성 축 추가 -> has_code_example -> python [EXTRACTED]
- 16-3. ★ v3.0 AI 산출물 신뢰성 규칙 (TRS-01~12 구현) -> contains -> 16-3-1. 시스템 프롬프트 — 신뢰성 지시 블록 [EXTRACTED]
- 16-3. ★ v3.0 AI 산출물 신뢰성 규칙 (TRS-01~12 구현) -> contains -> 16-3-2. 출처 태그 후처리 — source_tagger.py [EXTRACTED]
- 16-3. ★ v3.0 AI 산출물 신뢰성 규칙 (TRS-01~12 구현) -> contains -> 16-3-3. 자가진단 4축 확장 — 근거 신뢰성 축 추가 [EXTRACTED]
- 29-2. 신규 노드: `research_gather` -> contains -> 핵심 설계 원칙: RFP-적응형 리서치 [EXTRACTED]
- 29-3. 신규 노드: `presentation_strategy` -> has_code_example -> python [EXTRACTED]
- 29-4. 기존 프롬프트 보강 — `go_no_go` (발주기관 인텔리전스 5단계) -> has_code_example -> python [EXTRACTED]
- 29-5. 기존 프롬프트 보강 — `strategy_generate` (경쟁 SWOT + 시나리오 + 연구질문) -> has_code_example -> python [EXTRACTED]
- 29-6. 기존 프롬프트 보강 — `plan_price` (원가기준·노임단가·입찰시뮬레이션) -> has_code_example -> python [EXTRACTED]
- 29-7. 기존 프롬프트 보강 — `self_review` (3인 페르소나 시뮬레이션) -> has_code_example -> python [EXTRACTED]
- 29-8. 기존 프롬프트 보강 — `proposal_section` (자체검증 체크리스트) -> has_code_example -> python [EXTRACTED]
- 29-9. PPT 프롬프트 신규 생성 -> has_code_example -> python [EXTRACTED]
- 29. ★ ProposalForge 프롬프트 설계 통합 (v3.2) -> contains -> 29-1. 그래프 플로우 변경 요약 [EXTRACTED]
- 29. ★ ProposalForge 프롬프트 설계 통합 (v3.2) -> contains -> 29-2. 신규 노드: `research_gather` [EXTRACTED]
- 29. ★ ProposalForge 프롬프트 설계 통합 (v3.2) -> contains -> 29-3. 신규 노드: `presentation_strategy` [EXTRACTED]
- 29. ★ ProposalForge 프롬프트 설계 통합 (v3.2) -> contains -> 29-4. 기존 프롬프트 보강 — `go_no_go` (발주기관 인텔리전스 5단계) [EXTRACTED]
- 29. ★ ProposalForge 프롬프트 설계 통합 (v3.2) -> contains -> 29-5. 기존 프롬프트 보강 — `strategy_generate` (경쟁 SWOT + 시나리오 + 연구질문) [EXTRACTED]
- 29. ★ ProposalForge 프롬프트 설계 통합 (v3.2) -> contains -> 29-6. 기존 프롬프트 보강 — `plan_price` (원가기준·노임단가·입찰시뮬레이션) [EXTRACTED]
- 29. ★ ProposalForge 프롬프트 설계 통합 (v3.2) -> contains -> 29-7. 기존 프롬프트 보강 — `self_review` (3인 페르소나 시뮬레이션) [EXTRACTED]
- 29. ★ ProposalForge 프롬프트 설계 통합 (v3.2) -> contains -> 29-8. 기존 프롬프트 보강 — `proposal_section` (자체검증 체크리스트) [EXTRACTED]
- 29. ★ ProposalForge 프롬프트 설계 통합 (v3.2) -> contains -> 29-9. PPT 프롬프트 신규 생성 [EXTRACTED]
- 29. ★ ProposalForge 프롬프트 설계 통합 (v3.2) -> contains -> 29-10. 토큰 예산 갱신 요약 [EXTRACTED]
- 29. ★ ProposalForge 프롬프트 설계 통합 (v3.2) -> contains -> 29-11. ProposalForge 에이전트 → TENOPA 노드 매핑 참조표 [EXTRACTED]
- 핵심 설계 원칙: RFP-적응형 리서치 -> has_code_example -> python [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 python, 29. ★ ProposalForge 프롬프트 설계 통합 (v3.2), 16-3. ★ v3.0 AI 산출물 신뢰성 규칙 (TRS-01~12 구현)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 12-prompts.md이다.

### Key Facts
- ```python COMMON_CONTEXT = """ 현재 제안 컨텍스트 - 사업명: {project_name} - 발주기관: {client} - 🏷️ 포지셔닝: {positioning} ({positioning_label}) - 모드: {mode}
- > **배경**: ProposalForge 13개 에이전트 상세 프롬프트 설계서를 Pattern A(모놀리식 StateGraph) 구조 내에서 흡수. > ProposalForge는 Pattern B(오케스트레이터+전문에이전트) 기반이므로 아키텍처는 변경하지 않고, **프롬프트 내용**만 노드 레벨로 통합. > 7개 리서치 서브에이전트 → 1개 `research_gather` 노드로 통합하되, **획일적 7차원 템플릿이 아닌 RFP-적응형**으로 설계 (사업 범주에 따라 조사 차원 자체를 동적 도출).
- > 요구사항 §12-0의 신뢰성 정책을 시스템 프롬프트 + 후처리로 구현한다.
- > **★ v3.0 토큰 최적화 원칙** (§21 참조): > - `COMMON_CONTEXT`는 **Prompt Caching 대상** — `cache_control: {"type": "ephemeral"}` 적용 > - 피드백 이력은 **최근 3회(feedback_window_size)만** 포함 > - KB 참조는 **Top-5, 각 500자 이내**로 요약 후 주입 > - STEP별 컨텍스트 예산 준수 (§21 token_manager.py STEP_BUDGETS 참조)
- ```python app/prompts/trustworthiness.py
