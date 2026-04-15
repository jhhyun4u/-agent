# ux-improvements Gap Analysis Report & Minor Observations (Non-Blocking)
Cohesion: 0.22 | Nodes: 9

## Key Nodes
- **ux-improvements Gap Analysis Report** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\ux-improvements\ux-improvements.analysis.md) -- 6 connections
  - -> contains -> [[overall-scores]]
  - -> contains -> [[requirement-by-requirement-results]]
  - -> contains -> [[new-files-6-components-1145-lines]]
  - -> contains -> [[modified-files-7]]
  - -> contains -> [[minor-observations-non-blocking]]
  - -> contains -> [[typescript-build]]
- **Minor Observations (Non-Blocking)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\ux-improvements\ux-improvements.analysis.md) -- 3 connections
  - -> contains -> [[gap-1-low-kbusagehistory]]
  - -> contains -> [[gap-2-low-duplicatebidwarning]]
  - <- contains <- [[ux-improvements-gap-analysis-report]]
- **GAP-1 (LOW): KbUsageHistory — 근사 검색** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\ux-improvements\ux-improvements.analysis.md) -- 1 connections
  - <- contains <- [[minor-observations-non-blocking]]
- **GAP-2 (LOW): DuplicateBidWarning — 제목 기반 매칭** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\ux-improvements\ux-improvements.analysis.md) -- 1 connections
  - <- contains <- [[minor-observations-non-blocking]]
- **Modified Files (7)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\ux-improvements\ux-improvements.analysis.md) -- 1 connections
  - <- contains <- [[ux-improvements-gap-analysis-report]]
- **New Files (6 components, ~1,145 lines)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\ux-improvements\ux-improvements.analysis.md) -- 1 connections
  - <- contains <- [[ux-improvements-gap-analysis-report]]
- **Overall Scores** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\ux-improvements\ux-improvements.analysis.md) -- 1 connections
  - <- contains <- [[ux-improvements-gap-analysis-report]]
- **Requirement-by-Requirement Results** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\ux-improvements\ux-improvements.analysis.md) -- 1 connections
  - <- contains <- [[ux-improvements-gap-analysis-report]]
- **TypeScript Build** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\ux-improvements\ux-improvements.analysis.md) -- 1 connections
  - <- contains <- [[ux-improvements-gap-analysis-report]]

## Internal Relationships
- Minor Observations (Non-Blocking) -> contains -> GAP-1 (LOW): KbUsageHistory — 근사 검색 [EXTRACTED]
- Minor Observations (Non-Blocking) -> contains -> GAP-2 (LOW): DuplicateBidWarning — 제목 기반 매칭 [EXTRACTED]
- ux-improvements Gap Analysis Report -> contains -> Overall Scores [EXTRACTED]
- ux-improvements Gap Analysis Report -> contains -> Requirement-by-Requirement Results [EXTRACTED]
- ux-improvements Gap Analysis Report -> contains -> New Files (6 components, ~1,145 lines) [EXTRACTED]
- ux-improvements Gap Analysis Report -> contains -> Modified Files (7) [EXTRACTED]
- ux-improvements Gap Analysis Report -> contains -> Minor Observations (Non-Blocking) [EXTRACTED]
- ux-improvements Gap Analysis Report -> contains -> TypeScript Build [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 ux-improvements Gap Analysis Report, Minor Observations (Non-Blocking), GAP-1 (LOW): KbUsageHistory — 근사 검색를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 ux-improvements.analysis.md이다.

### Key Facts
- > **Date**: 2026-03-21 > **Match Rate**: 98% > **Status**: PASS (>= 90%)
- GAP-1 (LOW): KbUsageHistory — 근사 검색 - `api.kb.search(contentTitle)`로 사용 이력 조회 (전용 API 부재) - 향후 `/api/kb/{id}/usages` 엔드포인트 추가 시 정확도 향상
- GAP-2 (LOW): DuplicateBidWarning — 제목 기반 매칭 - `p.title?.includes(bidNo)`로 중복 체크 (proposals에 bid_no 컬럼 부재) - 향후 bid_no 컬럼 추가 시 정확 매칭 가능
- - `frontend/app/proposals/[id]/page.tsx` — +WorkflowResumeBanner, +GuidedTour - `frontend/app/proposals/new/page.tsx` — +DuplicateBidWarning - `frontend/app/dashboard/page.tsx` — +위젯 토글, +GuidedTour - `frontend/app/kb/content/page.tsx` — +KbUsageHistory - `frontend/app/admin/page.tsx` —…
- - `frontend/components/WorkflowResumeBanner.tsx` (196 lines) - `frontend/components/GuidedTour.tsx` (265 lines) - `frontend/components/StreamDependencyGraph.tsx` (209 lines) - `frontend/components/DuplicateBidWarning.tsx` (100 lines) - `frontend/components/KbUsageHistory.tsx` (123 lines) -…
