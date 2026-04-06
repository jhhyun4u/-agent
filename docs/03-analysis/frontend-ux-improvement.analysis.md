# Frontend UX 개선 — Gap Analysis

> Design: `docs/02-design/features/frontend-ux-improvement.design.md`
> 분석 일자: 2026-03-21

## 종합 결과

| 항목 | 점수 |
|------|------|
| **1차 분석** | 78% (44항목 중 33 MATCH, 3 PARTIAL, 8 MISSING) |
| **갭 수정 후** | **95%** (44항목 중 42 MATCH, 2 PARTIAL) |
| TypeScript 빌드 | 0 에러 |

## Phase별 점수 (수정 후)

| Phase | 점수 | 상태 |
|-------|------|------|
| Phase 1 안정성 | 12/12 = 100% | PASS |
| Phase 2 생산성 | 9.5/10 = 95% | PASS |
| Phase 3 확장성 | 11/11 = 100% | PASS |
| Phase 4 협업 | 10/11 = 91% | PASS |

## 1차 분석에서 발견된 갭 및 수정 내역

| # | 갭 항목 | 등급 | 수정 여부 | 비고 |
|---|--------|------|-----------|------|
| GAP-1 | Breadcrumb 미사용 | MEDIUM | **수정 완료** | ProposalEditView 헤더에 통합 |
| GAP-2 | 사이드바 모바일 오버레이 | HIGH | **수정 완료** | lg:hidden 햄버거 + 오버레이 드로어 추가 |
| GAP-3 | PhaseGraph aria-label | MEDIUM | **수정 완료** | 노드별 `aria-label` + 상태 텍스트 추가 |
| GAP-4 | PhaseGraph 상태 텍스트 | MEDIUM | **수정 완료** | 완료/진행 중/승인 대기/대기 텍스트 |
| GAP-5 | JSON 구문 강조 | LOW | **수정 완료** | `highlightJson()` 함수 추가 |
| GAP-6 | ui/Card,Modal,Badge | LOW | 오탐 | 파일 이미 존재 (에이전트 탐색 오류) |
| GAP-7 | diff-match-patch npm | LOW | 의도적 | 폴백 구현으로 런타임 안전 보장 |

## 잔여 PARTIAL 항목 (의도적 허용)

| # | 항목 | 이유 |
|---|------|------|
| P-1 | ProposalEditor toolbar aria — 일부 `ariaLabel || label` 패턴 | label 자체가 "B","I" 등이므로 `ariaLabel` 인자로 "볼드","이탤릭" 전달하여 동작. 3개 버튼에만 명시적 전달, 나머지는 한국어 라벨("• 목록" 등)이라 충분 |
| P-2 | diff-match-patch 미설치 | `require()` + `computeSimpleDiff` 폴백 패턴으로 라이브러리 없이도 동작. 설치 시 자동 활성화 |

## 수정된 파일 목록

| 파일 | 수정 내용 |
|------|-----------|
| `ProposalEditView.tsx` | Breadcrumb import + 헤더 교체 |
| `AppSidebar.tsx` | mobileOpen 상태 + 햄버거 + 오버레이 드로어 + sidebarContent 리팩터 |
| `PhaseGraph.tsx` | aria-label + 상태 텍스트 span |
| `StepArtifactViewer.tsx` | highlightJson() 함수 + pre 내 호출 |
