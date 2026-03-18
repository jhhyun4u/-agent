# Workflow UX 개선 계획서

> STEP 0~5 워크플로 진행 과정의 실시간 가시성, 중간 개입, 산출물 검토 기능 구현

## 1. 배경 및 목적

### 현재 문제점
- **"처리 중" 화면이 텅 빔**: 스피너 + "Phase N/5" + 경과 시간만 표시, 어떤 노드가 실행 중인지 알 수 없음
- **중단/재개 불가**: `ai-abort`, `ai-retry` API는 있으나 UI 버튼 없음
- **STEP별 산출물 미노출**: `artifacts/{step}` API는 있으나 뷰어 UI 없음
- **타임트래블 접근 불가**: `goto/{step}` API는 있으나 UI 없음
- **SSE 미활용**: `stream` API로 실시간 이벤트를 받을 수 있으나, 5초 HTTP 폴링만 사용 중

### 핵심 사실: 백엔드 API는 이미 전부 구현되어 있음
프론트엔드 UI만 구현하면 됨. 백엔드 수정 없음.

## 2. 구현 범위 (5개 영역)

### 2-1. 세부 진행 표시 (실시간 노드 로그)

**목적**: STEP 처리 중일 때 현재 실행 중인 노드와 완료된 노드를 실시간으로 표시

**현재 상태**:
- `PhaseGraph` 컴포넌트: 6단계 수평 원형 그래프 (완료/진행/대기만 구분)
- `usePhaseStatus` 훅: Supabase Realtime + 5초 폴링
- `PHASES` 상수 (page.tsx:36): 5단계 정의 (WORKFLOW_STEPS 6단계와 불일치)

**구현 내용**:
- SSE 기반 실시간 노드 진행 훅 (`useWorkflowStream`) 신규 생성
  - `GET /stream` SSE 연결
  - `on_chain_start` → 노드 시작 표시
  - `on_chain_end` → 노드 완료 + 산출물 미리보기
- `PhaseGraph` 확장: STEP 내부 세부 노드 펼침 (아코디언)
  - 예: STEP 1 클릭 → rfp_analyze(완료), research_gather(진행중), go_no_go(대기)
- 진행 중 노드의 **작업 내용 실시간 표시**
  - SSE `on_chain_end` 이벤트의 output에서 핵심 데이터 추출
  - 예: "RFP 분석 완료 — 케이스 A, 평가항목 8개, 핫버튼 3개 추출"
  - 예: "Go/No-Go 판정 — 수주 가능성 75%, 포지셔닝: 공격형"

**사용 API**: `GET /proposals/{id}/stream` (SSE), `GET /proposals/{id}/state`

**수정 파일**:
- 신규: `frontend/lib/hooks/useWorkflowStream.ts`
- 수정: `frontend/components/PhaseGraph.tsx` — 세부 노드 펼침 UI
- 수정: `frontend/app/proposals/[id]/page.tsx` — PHASES 상수 → WORKFLOW_STEPS 통일

### 2-2. 중단/재개 버튼

**목적**: 처리 중인 워크플로를 일시정지하고, 산출물 확인 후 재개

**현재 상태**:
- `POST /ai-abort` — paused 상태 전환 (구현됨)
- `POST /ai-retry` — 중단 지점부터 재실행 (구현됨)
- UI 버튼 없음

**구현 내용**:
- 처리 중 상태바에 "일시정지" 버튼 추가
- paused 상태에서 "재개" + "이전 단계로" 버튼 표시
- 실패 시 "재시도" 버튼 (기존 failedPhaseN 재시작과 통합)

**사용 API**: `POST /ai-abort`, `POST /ai-retry`

**수정 파일**:
- 수정: `frontend/app/proposals/[id]/page.tsx` — 상태바에 버튼 추가

### 2-3. STEP별 산출물 뷰어

**목적**: 완료된 각 STEP의 산출물을 클릭해서 검토

**현재 상태**:
- `GET /artifacts/{step}` — 모든 STEP 산출물 조회 가능 (구현됨)
- 결과물 탭 = DOCX/PPTX 다운로드 버튼만 표시
- Go/No-Go, 전략, 계획 등 중간 산출물 뷰어 없음

**구현 내용**:
- `PhaseGraph`에서 완료된 STEP 노드 클릭 → 하단에 산출물 패널 표시
- STEP별 산출물 렌더러:
  | STEP | artifact key | 표시 내용 |
  |------|-------------|----------|
  | 0 | search_results | 추천 공고 목록 (fit_score 순) |
  | 1-① | rfp_analyze | 케이스 유형, 평가항목, 핫버튼, 필수요건, Compliance Matrix |
  | 1 | research_gather | 리서치 주제별 발견 + 신뢰도 태그 |
  | 1-② | go_no_go | 수주 가능성 점수, 포지셔닝, 강점/리스크, fatal_flaw/strategic_focus |
  | 2 | strategy | Win Theme, Ghost Theme, 대안 비교, 가격 전략 |
  | 3 | plan (storylines) | 목차 + 섹션별 스토리라인 + quality_check |
  | 3 | plan (bid_price) | 예산 산정 내역 + Budget Narrative |
  | 4 | proposal_sections | 섹션별 본문 (접기/펼치기) + self_check 점수 |
  | 4 | self_review | 4축 점수 + 3-페르소나 평가 + 약한 섹션 |
  | 5 | ppt_storyboard | 슬라이드 목차 + 시각 전략 미리보기 |

- 신규 컴포넌트: `StepArtifactViewer` — artifact key별 렌더링 분기

**사용 API**: `GET /proposals/{id}/artifacts/{step}`

**수정 파일**:
- 신규: `frontend/components/StepArtifactViewer.tsx`
- 수정: `frontend/components/PhaseGraph.tsx` — 노드 클릭 이벤트 + 산출물 패널 연결
- 수정: `frontend/app/proposals/[id]/page.tsx` — 산출물 패널 영역 추가

### 2-4. 타임트래블 UI

**목적**: 이전 STEP으로 돌아가서 수정 후 재실행

**현재 상태**:
- `POST /goto/{step}` — 체크포인트 복원 (구현됨)
- `GET /impact/{step}` — 영향 받는 downstream 노드 조회 (구현됨)
- UI 없음

**구현 내용**:
- 완료된 STEP 산출물 뷰어에 "이 단계로 돌아가기" 버튼
- 클릭 시 `impact` API 호출 → "STEP X~Y를 재실행해야 합니다" 경고 표시
- 확인 시 `goto` API 호출 → 해당 STEP으로 복원
- 복원 후 자동으로 resume 대기 상태 (리뷰 패널 표시)

**사용 API**: `POST /goto/{step}`, `GET /impact/{step}`

**수정 파일**:
- 수정: `frontend/components/StepArtifactViewer.tsx` — 타임트래블 버튼 추가
- 수정: `frontend/lib/api.ts` — goto, impact 메서드 (이미 존재 확인)

### 2-5. 실시간 로그 패널

**목적**: SSE 기반 노드별 실행 로그를 화면 하단에 스트리밍

**현재 상태**:
- `GET /stream` SSE API (구현됨) — on_chain_start/end 이벤트
- `GET /ai-logs` — DB 저장된 이력 조회 (구현됨)
- 프론트엔드에서 미소비

**구현 내용**:
- 2-1의 `useWorkflowStream` 훅과 공유
- 하단 접이식 로그 패널 (터미널 스타일)
  - 타임스탬프 + 노드명 + 이벤트 타입
  - 완료 이벤트에 핵심 산출물 1줄 요약
  - 에러 이벤트 빨간색 강조
- 토글 버튼으로 접기/펼치기

**수정 파일**:
- 신규: `frontend/components/WorkflowLogPanel.tsx`
- 수정: `frontend/app/proposals/[id]/page.tsx` — 로그 패널 영역 추가

## 3. 구현 우선순위 및 의존성

```
Phase A (핵심): 2-1 세부 진행 + 2-2 중단/재개
  → SSE 훅 기반, 즉시 체감 가능한 UX 개선
  → 의존성 없음

Phase B (산출물): 2-3 산출물 뷰어
  → Phase A의 PhaseGraph 확장 위에 구축
  → 10개 artifact renderer 구현 (가장 작업량 많음)

Phase C (고급): 2-4 타임트래블 + 2-5 로그 패널
  → Phase B의 산출물 뷰어 위에 타임트래블 버튼 추가
  → 로그 패널은 독립적
```

## 4. 신규/수정 파일 목록

### 신규 파일 (3개)
| 파일 | 용도 |
|------|------|
| `frontend/lib/hooks/useWorkflowStream.ts` | SSE 실시간 스트림 훅 |
| `frontend/components/StepArtifactViewer.tsx` | STEP별 산출물 렌더러 |
| `frontend/components/WorkflowLogPanel.tsx` | 하단 실시간 로그 패널 |

### 수정 파일 (4개)
| 파일 | 변경 내용 |
|------|----------|
| `frontend/components/PhaseGraph.tsx` | 세부 노드 펼침 + 클릭 이벤트 + 산출물 연결 |
| `frontend/app/proposals/[id]/page.tsx` | PHASES→WORKFLOW_STEPS 통일, 중단/재개 버튼, 산출물/로그 패널 영역 |
| `frontend/components/WorkflowPanel.tsx` | paused 상태 UI 추가 |
| `frontend/lib/api.ts` | 누락 메서드 확인 (대부분 이미 존재) |

### 백엔드 수정: 없음
모든 API가 이미 구현됨 (state, stream, abort, retry, goto, impact, artifacts, ai-logs)

## 5. 기존 재사용 자산

| 자산 | 위치 | 용도 |
|------|------|------|
| `usePhaseStatus` 훅 | `frontend/lib/hooks/usePhaseStatus.ts` | 폴링 fallback (SSE 실패 시) |
| `WORKFLOW_STEPS` 상수 | `frontend/lib/api.ts:1725` | 6단계 + 노드 매핑 |
| `WorkflowPanel` | `frontend/components/WorkflowPanel.tsx` | 리뷰 게이트 UI (재사용) |
| `GoNoGoPanel` | `frontend/components/GoNoGoPanel.tsx` | Go/No-Go 산출물 뷰어 (참조) |
| `EvaluationView` | `frontend/components/EvaluationView.tsx` | self_review 시각화 (참조) |
| `api.workflow.*` | `frontend/lib/api.ts` | stream, goto, impact, abort, retry |
| `api.artifacts.*` | `frontend/lib/api.ts` | get, getCompliance |

## 6. 검증 방법

1. **TypeScript 빌드**: `npx tsc --noEmit` 에러 0건
2. **SSE 연결 테스트**: dev 서버에서 워크플로 시작 → 브라우저 DevTools Network탭에서 SSE 이벤트 수신 확인
3. **산출물 렌더링**: 완료된 제안서의 각 STEP 클릭 → artifact 데이터 정상 표시
4. **중단/재개**: 처리 중 일시정지 → paused UI → 재개 → 정상 계속
5. **타임트래블**: 완료된 STEP에서 "돌아가기" → impact 경고 → goto → 복원 확인

## 7. 비기능 요구사항

- SSE 연결 끊김 시 5초 폴링 자동 fallback (기존 usePhaseStatus 패턴)
- 산출물 뷰어 lazy loading (열 때만 API 호출)
- 로그 패널 최대 200줄 유지 (오래된 로그 자동 삭제)
- 모바일 반응형 불필요 (내부 도구)
