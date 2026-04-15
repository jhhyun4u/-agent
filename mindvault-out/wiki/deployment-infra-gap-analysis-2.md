# deployment-infra Gap Analysis & 발견된 갭 (2건, 모두 수정 완료)
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **deployment-infra Gap Analysis** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\deployment-infra.analysis.md) -- 2 connections
  - -> contains -> [[2]]
  - -> contains -> [[match-rate-100]]
- **발견된 갭 (2건, 모두 수정 완료)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\deployment-infra.analysis.md) -- 1 connections
  - <- contains <- [[deployment-infra-gap-analysis]]
- **최종 Match Rate: **100%**** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\features\deployment-infra.analysis.md) -- 1 connections
  - <- contains <- [[deployment-infra-gap-analysis]]

## Internal Relationships
- deployment-infra Gap Analysis -> contains -> 발견된 갭 (2건, 모두 수정 완료) [EXTRACTED]
- deployment-infra Gap Analysis -> contains -> 최종 Match Rate: **100%** [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 deployment-infra Gap Analysis, 발견된 갭 (2건, 모두 수정 완료), 최종 Match Rate: **100%**를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 deployment-infra.analysis.md이다.

### Key Facts
- - **Feature**: deployment-infra - **Analysis Date**: 2026-03-22 - **Plan**: `docs/01-plan/features/deployment-infra.plan.md` - **Match Rate**: 97% → **100% (수정 후)**
- | GAP | 심각도 | 설명 | 조치 | |-----|--------|------|------| | GAP-1 | MEDIUM | CI에서 ruff 대신 ast.parse만 사용 | ruff check 추가 + pyproject.toml에 ruff dev dep 추가 | | GAP-2 | LOW | uv cache 미설정 | `enable-cache: true` 추가 (backend-lint, backend-test) |
- 모든 Plan 항목이 구현되고 갭이 해소됨.
