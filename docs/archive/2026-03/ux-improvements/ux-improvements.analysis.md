# ux-improvements Gap Analysis Report

> **Date**: 2026-03-21
> **Match Rate**: 98%
> **Status**: PASS (>= 90%)

## Overall Scores

| Category | Score | Status |
|----------|:-----:|:------:|
| Component Existence | 100% (7/7) | PASS |
| Integration Completeness | 100% (13/13 checks) | PASS |
| Feature Quality | 97% | PASS |
| **Overall Match Rate** | **98%** | PASS |

## Requirement-by-Requirement Results

| Req # | Feature | Priority | Score | Status |
|:-----:|---------|:--------:|:-----:|:------:|
| 1 | WorkflowResumeBanner | HIGH | 100% | PASS |
| 2 | GuidedTour + HelpTooltip | HIGH | 100% | PASS |
| 3 | StreamDependencyGraph | MEDIUM | 100% | PASS |
| 4 | DuplicateBidWarning | MEDIUM | 98% | PASS |
| 5 | KbUsageHistory | MEDIUM | 95% | PASS |
| 6 | Dashboard Widget Toggle | LOW | 100% | PASS |
| 7 | AdminOrgChart + RoleMatrix | LOW | 100% | PASS |

## New Files (6 components, ~1,145 lines)

- `frontend/components/WorkflowResumeBanner.tsx` (196 lines)
- `frontend/components/GuidedTour.tsx` (265 lines)
- `frontend/components/StreamDependencyGraph.tsx` (209 lines)
- `frontend/components/DuplicateBidWarning.tsx` (100 lines)
- `frontend/components/KbUsageHistory.tsx` (123 lines)
- `frontend/components/AdminOrgChart.tsx` (252 lines)

## Modified Files (7)

- `frontend/app/proposals/[id]/page.tsx` — +WorkflowResumeBanner, +GuidedTour
- `frontend/app/proposals/new/page.tsx` — +DuplicateBidWarning
- `frontend/app/dashboard/page.tsx` — +위젯 토글, +GuidedTour
- `frontend/app/kb/content/page.tsx` — +KbUsageHistory
- `frontend/app/admin/page.tsx` — +AdminOrgChart 뷰 전환
- `frontend/components/WorkflowPanel.tsx` — +HelpTooltip
- `frontend/components/StreamDashboard.tsx` — +StreamDependencyGraph

## Minor Observations (Non-Blocking)

### GAP-1 (LOW): KbUsageHistory — 근사 검색
- `api.kb.search(contentTitle)`로 사용 이력 조회 (전용 API 부재)
- 향후 `/api/kb/{id}/usages` 엔드포인트 추가 시 정확도 향상

### GAP-2 (LOW): DuplicateBidWarning — 제목 기반 매칭
- `p.title?.includes(bidNo)`로 중복 체크 (proposals에 bid_no 컬럼 부재)
- 향후 bid_no 컬럼 추가 시 정확 매칭 가능

## TypeScript Build

0 errors confirmed.
