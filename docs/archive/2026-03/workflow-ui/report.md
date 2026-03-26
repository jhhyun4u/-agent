# Workflow UI — PDCA Completion Report

> **Feature**: workflow-ui (제안 작업 워크플로 UI 개선)
> **Date**: 2026-03-25
> **Match Rate**: 97%
> **PDCA Cycle**: Do → Check → Act → Report (단일 세션)

---

## 1. Summary

제안서 상세 페이지의 워크플로 UI를 3가지 핵심 영역에서 개선:

1. **PhaseGraph v4** — SVG 원주 진행률, Start/Finish 버튼, Gate 승인 박스
2. **ArtifactReviewPanel** — Claude Desktop 스타일 읽기 전용 산출물 뷰어
3. **Resizable Right Panel** — 드래그 핸들로 300~800px 너비 조절

---

## 2. PDCA Phases

### Plan
- 별도 Plan 문서 없이 사용자 요청 기반으로 직접 구현 (incremental feature)

### Design
- 기존 설계 문서 §13-1-1 (PhaseGraph), §13-4/§13-5 (WorkflowPanel/ReviewPanel) 참조

### Do (구현)

#### 수정 파일 (5개)

| File | Lines | Changes |
|------|:-----:|---------|
| `PhaseGraph.tsx` | 496 | v4 전면 재작성: SVG ProgressCircle, StepNode, GateBox, useStepProgress 훅 |
| `ArtifactReviewPanel.tsx` | ~600 | 신규: 읽기 전용 뷰어 + 10개 타입별 렌더러 |
| `DetailRightPanel.tsx` | ~500 | review_pending 시 ArtifactReviewPanel 자동 전환, workflowState prop 추가 |
| `DetailCenterPanel.tsx` | 303 | onGateApprove 전달, WorkflowPanel 스크롤 연동 |
| `proposals/[id]/page.tsx` | 626 | 리사이즈 핸들, 제목 변경, workflowState 전달 |

#### 핵심 구현 상세

**PhaseGraph v4**
- `ProgressCircle`: SVG 원주 위 진행 아크 + 마커 점 (예상 시간 대비 경과율, 최대 95%)
- `StepNode`: 원 내부 % 표시 (active) / 체크 아이콘 (completed) / 번호 (pending)
- Start 버튼: `nextPendingStepIdx` 계산 → 다음 실행 가능 단계에만 표시
- Finish 배지: 완료 단계에 녹색 pill
- `useStepProgress` 훅: 500ms 인터벌로 경과 시간 계산
- `GateBox`: 6개 Gate 정의, active 시 승인 버튼 + ping 애니메이션

**ArtifactReviewPanel**
- 10개 전용 렌더러: GoNoGo, RfpAnalyze, SearchResults, Strategy, BidPlan, Plan, Proposal, SelfReview, PptStoryboard, Generic
- ProposalContent: AI 이슈 플래그 (self_review 자동 로드 → 70점 미만 섹션 강조)
- 공통 블록: Section, KV, Tag, Bullets

**Resizable Panel**
- mousedown/mousemove/mouseup 이벤트 체인
- 드래그 중 `cursor: col-resize` + `user-select: none`
- 핸들: 1px 바 + hover 시 녹색 강조

### Check (Gap Analysis)

| Metric | Value |
|--------|:-----:|
| Initial Match Rate | 92% |
| Gaps Found | 6건 (0 HIGH, 2 MEDIUM, 4 LOW) |
| Added Features | 8건 |
| Intentional Changes | 3건 |

### Act (Iteration)

| Gap | Severity | Action |
|-----|:--------:|--------|
| GAP-01 | MEDIUM | 의도적 허용 — 모바일 세로 레이아웃 별도 구현 |
| GAP-02 | MEDIUM | **수정** — AI 이슈 플래그 추가 (ProposalContent) |
| GAP-03 | LOW | **수정** — PptStoryboardContent 렌더러 추가 |
| GAP-04 | LOW | **수정** — SearchResultsContent 렌더러 추가 |
| GAP-05 | LOW | **수정** — BidPlanContent 렌더러 추가 |
| GAP-06 | LOW | **수정** — ProposalContent에 proposalId prop 추가 |

**Post-iteration Match Rate: 97%**

---

## 3. Key Decisions

| Decision | Rationale |
|----------|-----------|
| 읽기 전용 뷰어 (승인/재작업 제거) | 승인 액션은 중앙 WorkflowPanel에서 처리, 우측은 순수 콘텐츠 뷰어 역할 |
| Gate 승인 → WorkflowPanel 스크롤 | Gate 박스에서 직접 approve 대신 리뷰 패널로 이동하여 피드백과 함께 승인 |
| SVG 원주 진행률 | 작업자가 예상 시간 대비 현재 진행 상태를 직관적으로 파악 |
| 리사이즈 핸들 (300~800px) | 산출물 내용이 길 때 넓게, 워크플로 집중 시 좁게 조절 가능 |

---

## 4. Remaining Items

| Item | Severity | Status |
|------|:--------:|--------|
| 모바일 세로 타임라인 레이아웃 | LOW | 별도 이터레이션으로 추후 구현 |
| handleAbort/handleRetry raw fetch → api 통일 | LOW | 기존 레거시, 기능 영향 없음 |
| 설계 문서 역반영 (ADD-01~08) | LOW | 설계 업데이트 시 반영 |

---

## 5. TypeScript Build

```
npx tsc --noEmit → 0 errors
```

---

## 6. Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-25 | Initial — PhaseGraph v4 + ArtifactReviewPanel + Resizable Panel |
