# frontend-design-gap 갭 분석 보고서 & 3. 상세 체크리스트
Cohesion: 0.15 | Nodes: 14

## Key Nodes
- **frontend-design-gap 갭 분석 보고서** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.analysis.md) -- 6 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6]]
- **3. 상세 체크리스트** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.analysis.md) -- 5 connections
  - -> contains -> [[phase-d-ui]]
  - -> contains -> [[phase-b]]
  - -> contains -> [[phase-c]]
  - -> contains -> [[not-scope]]
  - <- contains <- [[frontend-design-gap]]
- **4. 발견된 갭** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.analysis.md) -- 3 connections
  - -> contains -> [[medium-1]]
  - -> contains -> [[low-2]]
  - <- contains <- [[frontend-design-gap]]
- **1. 분석 범위** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.analysis.md) -- 2 connections
  - -> contains -> [[6]]
  - <- contains <- [[frontend-design-gap]]
- **5. 권장 조치** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.analysis.md) -- 2 connections
  - -> contains -> [[98]]
  - <- contains <- [[frontend-design-gap]]
- **분석 파일 (6개)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.analysis.md) -- 2 connections
  - <- contains <- [[1]]
  - <- contains <- [[frontend-design-gap]]
- **2. 종합 점수** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.analysis.md) -- 1 connections
  - <- contains <- [[frontend-design-gap]]
- **98%+ 달성을 위해** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.analysis.md) -- 1 connections
  - <- contains <- [[5]]
- **LOW (2건, 의도적 편차)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.analysis.md) -- 1 connections
  - <- contains <- [[4]]
- **MEDIUM (1건)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.analysis.md) -- 1 connections
  - <- contains <- [[4]]
- **스타일 가이드 + NOT Scope** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.analysis.md) -- 1 connections
  - <- contains <- [[3]]
- **Phase B (대시보드 위젯)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.analysis.md) -- 1 connections
  - <- contains <- [[3]]
- **Phase C (포지셔닝 모달)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.analysis.md) -- 1 connections
  - <- contains <- [[3]]
- **Phase D (UI 인프라)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-design-gap\frontend-design-gap.analysis.md) -- 1 connections
  - <- contains <- [[3]]

## Internal Relationships
- 1. 분석 범위 -> contains -> 분석 파일 (6개) [EXTRACTED]
- 3. 상세 체크리스트 -> contains -> Phase D (UI 인프라) [EXTRACTED]
- 3. 상세 체크리스트 -> contains -> Phase B (대시보드 위젯) [EXTRACTED]
- 3. 상세 체크리스트 -> contains -> Phase C (포지셔닝 모달) [EXTRACTED]
- 3. 상세 체크리스트 -> contains -> 스타일 가이드 + NOT Scope [EXTRACTED]
- 4. 발견된 갭 -> contains -> MEDIUM (1건) [EXTRACTED]
- 4. 발견된 갭 -> contains -> LOW (2건, 의도적 편차) [EXTRACTED]
- 5. 권장 조치 -> contains -> 98%+ 달성을 위해 [EXTRACTED]
- frontend-design-gap 갭 분석 보고서 -> contains -> 1. 분석 범위 [EXTRACTED]
- frontend-design-gap 갭 분석 보고서 -> contains -> 2. 종합 점수 [EXTRACTED]
- frontend-design-gap 갭 분석 보고서 -> contains -> 3. 상세 체크리스트 [EXTRACTED]
- frontend-design-gap 갭 분석 보고서 -> contains -> 4. 발견된 갭 [EXTRACTED]
- frontend-design-gap 갭 분석 보고서 -> contains -> 5. 권장 조치 [EXTRACTED]
- frontend-design-gap 갭 분석 보고서 -> contains -> 분석 파일 (6개) [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 frontend-design-gap 갭 분석 보고서, 3. 상세 체크리스트, 4. 발견된 갭를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 frontend-design-gap.analysis.md이다.

### Key Facts
- > **Feature**: frontend-design-gap > **Design**: `docs/02-design/features/frontend-design-gap.design.md` > **Date**: 2026-03-29 > **Analyzer**: gap-detector
- 3개 Phase: D (UI 인프라), B (대시보드 역할별 위젯), C (포지셔닝 영향 모달) Phase A 제외 (이미 v4.0 구현), Phase E 제외 (별도 PDCA)
- | 파일 | Phase | 상태 | |------|:-----:|:----:| | `frontend/lib/utils.ts` | D | 신규 | | `frontend/package.json` | D | 수정 | | `frontend/components/ProposalEditor.tsx` | D | 수정 | | `frontend/app/(app)/dashboard/page.tsx` | B | 수정 | | `frontend/components/PositioningImpactModal.tsx` | C | 신규 | |…
- | 카테고리 | 점수 | 상태 | |----------|:----:|:----:| | Phase D - UI 인프라 (16항목) | 94% | PASS | | Phase B - 대시보드 위젯 (15항목) | 87% | PASS | | Phase C - 포지셔닝 모달 (10항목) | 100% | PASS | | 스타일 가이드 (4항목) | 100% | PASS | | NOT Scope (5항목) | 100% | PASS | | **종합 (50항목)** | **94%** | **PASS** | | **보정 (의도적 LOW 제외)**…
- 1. **GAP-1 수정**: 본부별 비교 테이블에 5번째 "전월 대비" 컬럼 추가. `teamPerfData`에서 이전 달 데이터를 비교하여 ▲/▼ 화살표 표시 필요.
