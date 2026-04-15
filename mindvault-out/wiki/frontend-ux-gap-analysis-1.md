# Frontend UX 개선 — Gap Analysis & 1차 분석에서 발견된 갭 및 수정 내역
Cohesion: 0.50 | Nodes: 4

## Key Nodes
- **Frontend UX 개선 — Gap Analysis** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\frontend-ux-improvement.analysis.md) -- 3 connections
  - -> contains -> [[phase]]
  - -> contains -> [[1]]
  - -> contains -> [[partial]]
- **1차 분석에서 발견된 갭 및 수정 내역** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\frontend-ux-improvement.analysis.md) -- 1 connections
  - <- contains <- [[frontend-ux-gap-analysis]]
- **잔여 PARTIAL 항목 (의도적 허용)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\frontend-ux-improvement.analysis.md) -- 1 connections
  - <- contains <- [[frontend-ux-gap-analysis]]
- **Phase별 점수 (수정 후)** (C:\project\tenopa proposer\-agent-master\docs\03-analysis\frontend-ux-improvement.analysis.md) -- 1 connections
  - <- contains <- [[frontend-ux-gap-analysis]]

## Internal Relationships
- Frontend UX 개선 — Gap Analysis -> contains -> Phase별 점수 (수정 후) [EXTRACTED]
- Frontend UX 개선 — Gap Analysis -> contains -> 1차 분석에서 발견된 갭 및 수정 내역 [EXTRACTED]
- Frontend UX 개선 — Gap Analysis -> contains -> 잔여 PARTIAL 항목 (의도적 허용) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Frontend UX 개선 — Gap Analysis, 1차 분석에서 발견된 갭 및 수정 내역, 잔여 PARTIAL 항목 (의도적 허용)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 frontend-ux-improvement.analysis.md이다.

### Key Facts
- > Design: `docs/02-design/features/frontend-ux-improvement.design.md` > 분석 일자: 2026-03-21
- | # | 갭 항목 | 등급 | 수정 여부 | 비고 | |---|--------|------|-----------|------| | GAP-1 | Breadcrumb 미사용 | MEDIUM | **수정 완료** | ProposalEditView 헤더에 통합 | | GAP-2 | 사이드바 모바일 오버레이 | HIGH | **수정 완료** | lg:hidden 햄버거 + 오버레이 드로어 추가 | | GAP-3 | PhaseGraph aria-label | MEDIUM | **수정 완료** | 노드별 `aria-label` + 상태…
- | # | 항목 | 이유 | |---|------|------| | P-1 | ProposalEditor toolbar aria — 일부 `ariaLabel || label` 패턴 | label 자체가 "B","I" 등이므로 `ariaLabel` 인자로 "볼드","이탤릭" 전달하여 동작. 3개 버튼에만 명시적 전달, 나머지는 한국어 라벨("• 목록" 등)이라 충분 | | P-2 | diff-match-patch 미설치 | `require()` + `computeSimpleDiff` 폴백 패턴으로 라이브러리 없이도 동작. 설치 시…
- | Phase | 점수 | 상태 | |-------|------|------| | Phase 1 안정성 | 12/12 = 100% | PASS | | Phase 2 생산성 | 9.5/10 = 95% | PASS | | Phase 3 확장성 | 11/11 = 100% | PASS | | Phase 4 협업 | 10/11 = 91% | PASS |
