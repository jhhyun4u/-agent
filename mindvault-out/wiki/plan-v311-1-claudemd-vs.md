# Plan: 용역 제안서 자동 생성 에이전트 v3.1.1 완성 & 1. 현황 분석 (CLAUDE.md vs 실제 코드 비교)
Cohesion: 0.10 | Nodes: 20

## Key Nodes
- **Plan: 용역 제안서 자동 생성 에이전트 v3.1.1 완성** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 8 connections
  - -> contains -> [[1-claudemd-vs]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
- **1. 현황 분석 (CLAUDE.md vs 실제 코드 비교)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 4 connections
  - -> contains -> [[11-claudemd]]
  - -> contains -> [[12]]
  - -> contains -> [[13]]
  - <- contains <- [[plan-v311]]
- **2.2 단계별 목표** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 4 connections
  - -> contains -> [[phase-a]]
  - -> contains -> [[phase-b-phase]]
  - -> contains -> [[phase-c]]
  - <- contains <- [[2]]
- **5. 작업 우선순위** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 4 connections
  - -> contains -> [[critical]]
  - -> contains -> [[high-priority]]
  - -> contains -> [[medium-priority]]
  - <- contains <- [[plan-v311]]
- **2. 목표** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 3 connections
  - -> contains -> [[21]]
  - -> contains -> [[22]]
  - <- contains <- [[plan-v311]]
- **1.1 CLAUDE.md 문제점** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 1 connections
  - <- contains <- [[1-claudemd-vs]]
- **1.2 실제 구현 완료 항목** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 1 connections
  - <- contains <- [[1-claudemd-vs]]
- **1.3 미완성 / 문제 항목** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 1 connections
  - <- contains <- [[1-claudemd-vs]]
- **2.1 최종 목표** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 1 connections
  - <- contains <- [[2]]
- **3. 기술 스택 (갱신)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 1 connections
  - <- contains <- [[plan-v311]]
- **4. 아키텍처 구조 (현재 기준)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 1 connections
  - <- contains <- [[plan-v311]]
- **6. 제약 조건** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 1 connections
  - <- contains <- [[plan-v311]]
- **7. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 1 connections
  - <- contains <- [[plan-v311]]
- **8. 다음 단계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 1 connections
  - <- contains <- [[plan-v311]]
- **즉시 처리 (Critical)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **핵심 구현 (High Priority)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **품질 향상 (Medium Priority)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **Phase A — 기반 안정화 (즉시)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 1 connections
  - <- contains <- [[22]]
- **Phase B — Phase 실행 로직 구현 (핵심)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 1 connections
  - <- contains <- [[22]]
- **Phase C — 완성도 향상** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v33\proposal-agent-v311.plan.md) -- 1 connections
  - <- contains <- [[22]]

## Internal Relationships
- 1. 현황 분석 (CLAUDE.md vs 실제 코드 비교) -> contains -> 1.1 CLAUDE.md 문제점 [EXTRACTED]
- 1. 현황 분석 (CLAUDE.md vs 실제 코드 비교) -> contains -> 1.2 실제 구현 완료 항목 [EXTRACTED]
- 1. 현황 분석 (CLAUDE.md vs 실제 코드 비교) -> contains -> 1.3 미완성 / 문제 항목 [EXTRACTED]
- 2. 목표 -> contains -> 2.1 최종 목표 [EXTRACTED]
- 2. 목표 -> contains -> 2.2 단계별 목표 [EXTRACTED]
- 2.2 단계별 목표 -> contains -> Phase A — 기반 안정화 (즉시) [EXTRACTED]
- 2.2 단계별 목표 -> contains -> Phase B — Phase 실행 로직 구현 (핵심) [EXTRACTED]
- 2.2 단계별 목표 -> contains -> Phase C — 완성도 향상 [EXTRACTED]
- 5. 작업 우선순위 -> contains -> 즉시 처리 (Critical) [EXTRACTED]
- 5. 작업 우선순위 -> contains -> 핵심 구현 (High Priority) [EXTRACTED]
- 5. 작업 우선순위 -> contains -> 품질 향상 (Medium Priority) [EXTRACTED]
- Plan: 용역 제안서 자동 생성 에이전트 v3.1.1 완성 -> contains -> 1. 현황 분석 (CLAUDE.md vs 실제 코드 비교) [EXTRACTED]
- Plan: 용역 제안서 자동 생성 에이전트 v3.1.1 완성 -> contains -> 2. 목표 [EXTRACTED]
- Plan: 용역 제안서 자동 생성 에이전트 v3.1.1 완성 -> contains -> 3. 기술 스택 (갱신) [EXTRACTED]
- Plan: 용역 제안서 자동 생성 에이전트 v3.1.1 완성 -> contains -> 4. 아키텍처 구조 (현재 기준) [EXTRACTED]
- Plan: 용역 제안서 자동 생성 에이전트 v3.1.1 완성 -> contains -> 5. 작업 우선순위 [EXTRACTED]
- Plan: 용역 제안서 자동 생성 에이전트 v3.1.1 완성 -> contains -> 6. 제약 조건 [EXTRACTED]
- Plan: 용역 제안서 자동 생성 에이전트 v3.1.1 완성 -> contains -> 7. 성공 기준 [EXTRACTED]
- Plan: 용역 제안서 자동 생성 에이전트 v3.1.1 완성 -> contains -> 8. 다음 단계 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: 용역 제안서 자동 생성 에이전트 v3.1.1 완성, 1. 현황 분석 (CLAUDE.md vs 실제 코드 비교), 2.2 단계별 목표를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 proposal-agent-v311.plan.md이다.

### Key Facts
- Phase A — 기반 안정화 (즉시) 1. `main.py` import 오류 해결 — 서버가 정상 기동되도록 2. routes 버전 정리 — 단일 진입점 확립 3. CLAUDE.md 갱신 — 현재 v3.1.1 구조 반영
- 2.1 최종 목표 RFP를 입력하면 5-Phase 파이프라인을 통해 **실제 Claude API를 호출**하여 고품질 제안서(DOCX + PPTX)를 자동 생성한다.
- CLAUDE.md는 **v1.0 기준**으로 작성되어 실제 코드와 큰 괴리가 있음.
- - [x] FastAPI 기본 서버 구조 (`app/main.py`) - [x] RFP 파서 (`app/services/rfp_parser.py`) - [x] Claude 기반 제안서 생성기 (`app/services/proposal_generator.py`) - [x] DOCX 빌더 (`app/services/docx_builder.py`) - [x] PPTX 빌더 (`app/services/pptx_builder.py`) - [x] 세션 매니저 (`app/services/session_manager.py`) - [x]…
- - [ ] **main.py import 오류**: `from graph import build_supervisor_graph`, `from tools import create_default_registry`, `from config.claude_optimizer import TokenUsageTracker` — 해당 모듈 존재 여부 불확실 - [ ] **Phase 실행 로직이 Mock**: `/execute` 엔드포인트가 단순 카운터만 올리고 Claude API 실제 호출 없음 - [ ] **routes 버전 혼재**:…
