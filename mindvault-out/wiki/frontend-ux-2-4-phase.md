# Frontend UX 개선 계획서 & 2. 구현 범위 (4개 Phase)
Cohesion: 0.08 | Nodes: 26

## Key Nodes
- **Frontend UX 개선 계획서** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 7 connections
  - -> contains -> [[1]]
  - -> contains -> [[2-4-phase]]
  - -> contains -> [[3]]
  - -> contains -> [[4-phase]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
  - -> contains -> [[7-out-of-scope]]
- **2. 구현 범위 (4개 Phase)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 5 connections
  - -> contains -> [[phase-1-2]]
  - -> contains -> [[phase-2-3]]
  - -> contains -> [[phase-3-5]]
  - -> contains -> [[phase-4-3]]
  - <- contains <- [[frontend-ux]]
- **Phase 2 — 생산성 (단기, ~3일)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 5 connections
  - -> contains -> [[2-1-ai-diff-h1]]
  - -> contains -> [[2-2-h2]]
  - -> contains -> [[2-3-m3]]
  - -> contains -> [[2-4-kb-m4]]
  - <- contains <- [[2-4-phase]]
- **Phase 1 — 안정성 (즉시, ~2일)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 4 connections
  - -> contains -> [[1-1-c3]]
  - -> contains -> [[1-2-h3]]
  - -> contains -> [[1-3-ai-m1]]
  - <- contains <- [[2-4-phase]]
- **Phase 3 — 확장성 (중기, ~5일)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 4 connections
  - -> contains -> [[3-1-c1]]
  - -> contains -> [[3-2-c2]]
  - -> contains -> [[3-3-h4]]
  - <- contains <- [[2-4-phase]]
- **Phase 4 — 협업 (장기, ~3일)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 4 connections
  - -> contains -> [[4-1-h5]]
  - -> contains -> [[4-2-m5]]
  - -> contains -> [[4-3-m2]]
  - <- contains <- [[2-4-phase]]
- **1. 배경 및 목적** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 2 connections
  - -> contains -> [[ux]]
  - <- contains <- [[frontend-ux]]
- **1-1. 비저장 경고 (C3)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[phase-1-2]]
- **1-2. 키보드 단축키 (H3)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[phase-1-2]]
- **1-3. AI 응답 대기 표시 (M1)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[phase-1-2]]
- **2-1. AI 제안 인라인 Diff (H1)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[phase-2-3]]
- **2-2. 브레드크럼 네비게이션 (H2)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[phase-2-3]]
- **2-3. 산출물 뷰어 개선 (M3)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[phase-2-3]]
- **2-4. 사이드바 KB 메뉴 상태 유지 (M4)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[phase-2-3]]
- **3. 영향 범위** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[frontend-ux]]
- **3-1. 반응형 레이아웃 (C1)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[phase-3-5]]
- **3-2. 라이트/다크 모드 토글 (C2)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[phase-3-5]]
- **3-3. 버전 비교 전체화면 모드 (H4)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[phase-3-5]]
- **4-1. 댓글 마크다운 지원 (H5)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[phase-4-3]]
- **4-2. 접근성 개선 (M5)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[phase-4-3]]
- **4-3. 디자인 시스템 정리 (M2)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[phase-4-3]]
- **4. Phase별 우선순위 근거** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[frontend-ux]]
- **5. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[frontend-ux]]
- **6. 의존 관계** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[frontend-ux]]
- **7. 범위 외 (Out of Scope)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[frontend-ux]]
- **문제점 (UX 리뷰 결과)** (C:\project\tenopa proposer\-agent-master\docs\01-plan\features\frontend-ux-improvement.plan.md) -- 1 connections
  - <- contains <- [[1]]

## Internal Relationships
- 1. 배경 및 목적 -> contains -> 문제점 (UX 리뷰 결과) [EXTRACTED]
- 2. 구현 범위 (4개 Phase) -> contains -> Phase 1 — 안정성 (즉시, ~2일) [EXTRACTED]
- 2. 구현 범위 (4개 Phase) -> contains -> Phase 2 — 생산성 (단기, ~3일) [EXTRACTED]
- 2. 구현 범위 (4개 Phase) -> contains -> Phase 3 — 확장성 (중기, ~5일) [EXTRACTED]
- 2. 구현 범위 (4개 Phase) -> contains -> Phase 4 — 협업 (장기, ~3일) [EXTRACTED]
- Frontend UX 개선 계획서 -> contains -> 1. 배경 및 목적 [EXTRACTED]
- Frontend UX 개선 계획서 -> contains -> 2. 구현 범위 (4개 Phase) [EXTRACTED]
- Frontend UX 개선 계획서 -> contains -> 3. 영향 범위 [EXTRACTED]
- Frontend UX 개선 계획서 -> contains -> 4. Phase별 우선순위 근거 [EXTRACTED]
- Frontend UX 개선 계획서 -> contains -> 5. 성공 기준 [EXTRACTED]
- Frontend UX 개선 계획서 -> contains -> 6. 의존 관계 [EXTRACTED]
- Frontend UX 개선 계획서 -> contains -> 7. 범위 외 (Out of Scope) [EXTRACTED]
- Phase 1 — 안정성 (즉시, ~2일) -> contains -> 1-1. 비저장 경고 (C3) [EXTRACTED]
- Phase 1 — 안정성 (즉시, ~2일) -> contains -> 1-2. 키보드 단축키 (H3) [EXTRACTED]
- Phase 1 — 안정성 (즉시, ~2일) -> contains -> 1-3. AI 응답 대기 표시 (M1) [EXTRACTED]
- Phase 2 — 생산성 (단기, ~3일) -> contains -> 2-1. AI 제안 인라인 Diff (H1) [EXTRACTED]
- Phase 2 — 생산성 (단기, ~3일) -> contains -> 2-2. 브레드크럼 네비게이션 (H2) [EXTRACTED]
- Phase 2 — 생산성 (단기, ~3일) -> contains -> 2-3. 산출물 뷰어 개선 (M3) [EXTRACTED]
- Phase 2 — 생산성 (단기, ~3일) -> contains -> 2-4. 사이드바 KB 메뉴 상태 유지 (M4) [EXTRACTED]
- Phase 3 — 확장성 (중기, ~5일) -> contains -> 3-1. 반응형 레이아웃 (C1) [EXTRACTED]
- Phase 3 — 확장성 (중기, ~5일) -> contains -> 3-2. 라이트/다크 모드 토글 (C2) [EXTRACTED]
- Phase 3 — 확장성 (중기, ~5일) -> contains -> 3-3. 버전 비교 전체화면 모드 (H4) [EXTRACTED]
- Phase 4 — 협업 (장기, ~3일) -> contains -> 4-1. 댓글 마크다운 지원 (H5) [EXTRACTED]
- Phase 4 — 협업 (장기, ~3일) -> contains -> 4-2. 접근성 개선 (M5) [EXTRACTED]
- Phase 4 — 협업 (장기, ~3일) -> contains -> 4-3. 디자인 시스템 정리 (M2) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Frontend UX 개선 계획서, 2. 구현 범위 (4개 Phase), Phase 2 — 생산성 (단기, ~3일)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 frontend-ux-improvement.plan.md이다.

### Key Facts
- > 제안작업 담당자가 제안서를 작성하는 데 편리한 플랫폼으로 개선하기 위한 UX 리뷰 기반 4단계 로드맵
- Phase 1 — 안정성 (즉시, ~2일)
- 제안서 작성 효율 직접 향상. 담당자의 반복 작업 감소.
- 작성 중 데이터 유실 방지 + 기본 사용성 보강. 가장 시급하고 영향 큰 항목.
- 다양한 환경(모바일, 밝은 환경)에서의 사용성 확보.
