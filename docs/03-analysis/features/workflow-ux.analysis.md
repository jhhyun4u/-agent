# Workflow UX Gap Analysis

> Plan 문서 vs 구현 비교 (2026-03-18)

## Match Rate: 92%

| 영역 | 점수 | 상태 |
|------|:---:|:---:|
| 2-1 세부 진행 표시 (SSE) | 93% | PASS |
| 2-2 중단/재개 버튼 | 85% | WARNING |
| 2-3 산출물 뷰어 | 90% | PASS |
| 2-4 타임트래블 | 95% | PASS |
| 2-5 로그 패널 | 95% | PASS |

## Gap 목록

### HIGH (1건)

| ID | 영역 | 설명 |
|----|------|------|
| GAP-04 | 2-2 | **paused 상태 전용 UI 미구현** — ai-abort 후 "재개"+"이전 단계로" 버튼 없음 |

### MEDIUM (4건)

| ID | 영역 | 설명 |
|----|------|------|
| GAP-01 | 2-1 | on_chain_end output 요약 미추출 (예: "RFP 분석 완료 — 케이스 A") |
| GAP-05 | 2-2 | WorkflowPanel.tsx에 paused 분기 미추가 |
| GAP-06 | 2-3 | proposal_sections 전용 렌더러 없음 (GenericArtifact 사용 중) |
| GAP-11 | 2-5 | 로그 완료 이벤트에 산출물 1줄 요약 미표시 |

### LOW (5건)

| ID | 영역 | 설명 |
|----|------|------|
| GAP-02 | 2-1 | PHASES 상수가 page.tsx에 잔존 (WORKFLOW_STEPS와 불일치) |
| GAP-07 | 2-3 | ppt_storyboard 전용 렌더러 없음 |
| GAP-08 | 2-3 | RfpAnalyze에 Compliance Matrix 미표시 |
| GAP-09 | 2-3 | Strategy에 가격 전략 미표시 |
| GAP-10 | 2-4 | goto 후 리뷰 패널 자동 전환 미구현 |

## 즉시 대응: GAP-04 (paused UI)

page.tsx + WorkflowPanel.tsx에 paused 상태 감지 + 재개/돌아가기 버튼 추가 필요.
