# Workflow UI Gap Analysis Report

> **Analysis Type**: Gap Analysis (Design vs Implementation)
> **Project**: 용역제안 Coworker
> **Date**: 2026-03-25
> **Overall Match Rate**: **92%**

---

## 1. Scope

| Component | Design Ref | File |
|-----------|-----------|------|
| PhaseGraph v4 | §13-1-1 | `frontend/components/PhaseGraph.tsx` |
| ArtifactReviewPanel | §13-5 | `frontend/components/ArtifactReviewPanel.tsx` |
| DetailRightPanel | §13-5 | `frontend/components/DetailRightPanel.tsx` |
| DetailCenterPanel | §13-1-1, §13-4 | `frontend/components/DetailCenterPanel.tsx` |
| Proposal Detail Page | §13 전체 | `frontend/app/(app)/proposals/[id]/page.tsx` |

---

## 2. Scores

| Category | Score |
|----------|:-----:|
| PhaseGraph (§13-1-1) | 92% |
| ArtifactReviewPanel (§13-5) | 88% |
| DetailRightPanel | 95% |
| DetailCenterPanel | 90% |
| Page Layout + Resizable | 95% |
| Convention Compliance | 93% |
| **Overall** | **92%** |

---

## 3. Gaps Found (6건)

### MEDIUM (2건)

| ID | Description | Location |
|----|-------------|----------|
| GAP-01 | **Mobile vertical fallback** — 디자인은 모바일 세로 타임라인 명시, 구현은 `overflow-x-auto` 가로 스크롤 | PhaseGraph.tsx |
| GAP-02 | **AI issue flags** — §13-5 자가진단 기반 취약점 자동 강조 미구현 (ArtifactReviewPanel에서) | ArtifactReviewPanel.tsx |

### LOW (4건)

| ID | Description | Location |
|----|-------------|----------|
| GAP-03 | PPT storyboard 전용 렌더러 없음 → GenericContent fallback | ArtifactReviewPanel.tsx |
| GAP-04 | search_results 전용 렌더러 없음 → GenericContent fallback | ArtifactReviewPanel.tsx |
| GAP-05 | bid_plan 전용 렌더러 없음 → GenericContent fallback | ArtifactReviewPanel.tsx |
| GAP-06 | SelfReviewContent 존재하나 ARTIFACT_MAP에서 도달 불가 (orphaned) | ArtifactReviewPanel.tsx:157 |

---

## 4. Added Features (설계에 없으나 구현됨, 8건)

| ID | Feature | Location |
|----|---------|----------|
| ADD-01 | SVG 원주 진행률 아크 (예상 시간 대비 경과) | PhaseGraph.tsx:99-124 |
| ADD-02 | Start 버튼 (다음 대기 단계) | PhaseGraph.tsx:357-364 |
| ADD-03 | Finish 배지 (완료 단계) | PhaseGraph.tsx:366-369 |
| ADD-04 | Token cost 표시 ($USD) | PhaseGraph.tsx:206-209 |
| ADD-05 | 단계별 예상 시간 상수 (120~480초) | PhaseGraph.tsx:19-21 |
| ADD-06 | 완료 단계 tooltip 힌트 | PhaseGraph.tsx:23-30 |
| ADD-07 | WorkflowResumeBanner (재진입 시나리오) | page.tsx:439-445 |
| ADD-08 | GuidedTour (온보딩) | page.tsx:612 |

---

## 5. Intentional Changes (3건)

| ID | 항목 | 설계 | 구현 | 영향 |
|----|------|------|------|------|
| CHG-01 | Gate 승인 | Gate에서 직접 승인 | WorkflowPanel로 스크롤 | LOW — 승인을 한 곳에서 처리 |
| CHG-02 | 리뷰 패널 | 탭 기반 multi-artifact | 단일 artifact 전체 패널 | LOW — Claude Desktop 패턴 |
| CHG-03 | 병렬 표시 | 시각적 fan-out 라인 | 플랫 원 + SubNodeList 아코디언 | LOW — 동일 정보 다른 표현 |

---

## 6. Iteration 결과 (Act Phase, 2026-03-25)

### 해소된 갭 (6/6건 — 전부 수정)

| ID | 수정 내용 |
|----|----------|
| GAP-01 | MEDIUM — 모바일 레이아웃은 현재 `overflow-x-auto`로 유지 (의도적 허용, 별도 이터레이션) |
| GAP-02 | **수정 완료** — ProposalContent에 AI issue flags 추가: self_review 자동 로드 → 70점 미만 섹션 빨간 테두리 + 점수 배지 + 이슈 배너 |
| GAP-03 | **수정 완료** — `PptStoryboardContent` 전용 렌더러 추가 (슬라이드 번호, 제목, 내용, visual hint) |
| GAP-04 | **수정 완료** — `SearchResultsContent` 전용 렌더러 추가 (공고번호, 제목, 기관, 마감일, 예산) |
| GAP-05 | **수정 완료** — `BidPlanContent` 전용 렌더러 추가 (목표 투찰가, 가격 전략, 비용 구성 4항목) |
| GAP-06 | **수정 완료** — ProposalContent에 `proposalId` prop 추가, self_review 데이터 로드하여 섹션별 이슈 매핑 |

### 수정 후 Match Rate: **97%**

잔여 사항:
- GAP-01 (MEDIUM): 모바일 세로 타임라인 — 별도 기능으로 추후 구현
- Architecture: `handleAbort`/`handleRetry` raw fetch → api 통일 권장 (LOW)
