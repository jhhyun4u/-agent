# Workflow UX PDCA Report

> STEP 0~5 워크플로 진행 과정의 실시간 가시성, 중간 개입, 산출물 검토 기능 구현

## 1. 요약

| 항목 | 내용 |
|------|------|
| 기능명 | workflow-ux |
| PDCA 사이클 | Plan → Do → Check → Report (Design 생략) |
| Match Rate | **92%** (GAP-04 HIGH 수정 후 **95%**) |
| 신규 파일 | 4개 (1,085줄) |
| 수정 파일 | 5개 |
| 백엔드 수정 | 없음 (기존 API 7개 활용) |
| TypeScript 에러 | 0건 |

## 2. 구현 내역

### Phase A: 실시간 진행 표시 + 중단/재개

| 파일 | 변경 | 줄 수 |
|------|------|------|
| `frontend/lib/hooks/useWorkflowStream.ts` (신규) | SSE 기반 실시간 노드 진행 추적 훅 | 133 |
| `frontend/components/PhaseGraph.tsx` (수정) | 세부 노드 펼침, 클릭 이벤트, 현재 노드명 표시 | 269 |
| `frontend/app/proposals/[id]/page.tsx` (수정) | 일시정지/재시도 버튼, paused 상태 UI | +55 |

### Phase B: STEP별 산출물 뷰어

| 파일 | 변경 | 줄 수 |
|------|------|------|
| `frontend/components/StepArtifactViewer.tsx` (신규) | 6종 전용 렌더러 + 타임트래블 버튼 | 521 |

렌더러 목록:
- `GoNoGoArtifact` — 수주 가능성, 포지셔닝, fatal_flaw, strategic_focus
- `RfpAnalyzeArtifact` — 케이스 유형, 평가항목, 핫버튼, 필수요건
- `StrategyArtifact` — Win/Ghost Theme, 핵심 메시지, 전략 대안
- `SelfReviewArtifact` — 4축 점수 바 차트, 3-페르소나 시뮬레이션
- `PlanArtifact` — 팀 구성, 스토리라인, quality_check, 예산
- `GenericArtifact` — JSON 접기/펼치기 fallback

### Phase C: 타임트래블 + 실시간 로그

| 파일 | 변경 | 줄 수 |
|------|------|------|
| `frontend/components/WorkflowLogPanel.tsx` (신규) | 터미널 스타일 SSE 로그, 접이식, 29개 노드 한글 매핑 | 161 |
| `frontend/components/StepArtifactViewer.tsx` | impact 경고 + goto 확인 다이얼로그 | (위 포함) |

### GAP-04 수정

| 파일 | 변경 |
|------|------|
| `frontend/app/proposals/[id]/page.tsx` | isPaused 감지 + "재개"/"산출물 확인" 버튼 |
| `frontend/components/WorkflowPanel.tsx` | paused 상태 분기 |
| `frontend/lib/api.ts` | ProposalStatus에 "cancelled"/"paused" 추가 |

## 3. 활용한 기존 API (백엔드 수정 0건)

| API | 용도 | 연결 UI |
|-----|------|---------|
| `GET /state` | 워크플로 현재 상태 | PhaseGraph, 상태바 |
| `GET /stream` (SSE) | 실시간 노드 이벤트 | useWorkflowStream → PhaseGraph + LogPanel |
| `POST /ai-abort` | 일시정지 | 상태바 "일시정지" 버튼 |
| `POST /ai-retry` | 재시도/재개 | 상태바 "재시도"/"재개" 버튼 |
| `GET /artifacts/{step}` | STEP별 산출물 | StepArtifactViewer |
| `POST /goto/{step}` | 타임트래블 | StepArtifactViewer "돌아가기" |
| `GET /impact/{step}` | 영향 범위 조회 | StepArtifactViewer 경고 다이얼로그 |

## 4. 잔여 갭 (LOW/MEDIUM, 향후 개선)

| ID | 심각도 | 설명 |
|----|:---:|------|
| GAP-01/11 | MEDIUM | on_chain_end 산출물 1줄 요약 미추출 |
| GAP-06 | MEDIUM | proposal_sections 전용 렌더러 (접기/펼치기) |
| GAP-02 | LOW | PHASES 상수 잔존 |
| GAP-07~10 | LOW | PPT 렌더러, Compliance, 가격전략, goto 후 전환 |

## 5. 커밋 이력

```
f063812 fix: GAP-04 paused 상태 UI + 갭 분석 문서
278e745 feat: 워크플로 UX 개선 — SSE 실시간 진행 + 산출물 뷰어 + 중단/재개 + 로그
```
