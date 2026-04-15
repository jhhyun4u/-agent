# 29-1. prompt-enhancement 추가 필드 (§32-8 merged) & 29-1-1. PHASE3_USER 추가 출력 필드
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **29-1. prompt-enhancement 추가 필드 (§32-8 merged)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 2 connections
  - -> contains -> [[29-1-1-phase3user]]
  - -> contains -> [[29-1-2-phase4system]]
- **29-1-1. PHASE3_USER 추가 출력 필드** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 1 connections
  - <- contains <- [[29-1-prompt-enhancement-32-8-merged]]
- **29-1-2. PHASE4_SYSTEM 추가 원칙** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\proposal-agent-v1\design\12-prompts.md) -- 1 connections
  - <- contains <- [[29-1-prompt-enhancement-32-8-merged]]

## Internal Relationships
- 29-1. prompt-enhancement 추가 필드 (§32-8 merged) -> contains -> 29-1-1. PHASE3_USER 추가 출력 필드 [EXTRACTED]
- 29-1. prompt-enhancement 추가 필드 (§32-8 merged) -> contains -> 29-1-2. PHASE4_SYSTEM 추가 원칙 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 29-1. prompt-enhancement 추가 필드 (§32-8 merged), 29-1-1. PHASE3_USER 추가 출력 필드, 29-1-2. PHASE4_SYSTEM 추가 원칙를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 12-prompts.md이다.

### Key Facts
- > `docs/02-design/features/prompt-enhancement.design.md` 보완 사항. > 구현: `app/services/phase_prompts.py`
- | 필드 | 설명 | 설계 문서 상태 | |---|---|---| | `alternatives_considered` | 대안 비교 | 기존 (prompt-enhancement §2-1) | | `risks_mitigations` | 리스크 대응 | 기존 | | `implementation_checklist` | 추진 체크리스트 | 기존 | | `logic_model` | 투입→활동→산출→결과→영향 Logic Model | ★ 신규 추가 | | `objection_responses` | 예상 반론 + 대응 논리 | ★ 신규 추가 |
