# Plan: 프론트엔드 핵심 컴포넌트

> **Feature**: frontend-core-components
> **Date**: 2026-03-16
> **Status**: Plan
> **Design Reference**: `docs/02-design/features/proposal-agent-v1/09-frontend.md` (§13)

---

## 1. 목표

현재 프론트엔드는 페이지 스캐폴딩만 존재하고 핵심 UI 컴포넌트가 스텁 상태이다.
설계 문서 §13에 정의된 **6개 핵심 컴포넌트**를 구현하여 제안서 작성→리뷰→분석 워크플로를 완성한다.

## 2. 범위

### 2-1. In Scope (이번 Plan)

| # | 컴포넌트 | 설계 섹션 | 라우트 | 우선순위 |
|---|---------|----------|--------|:--------:|
| C1 | **PhaseGraph** | §13-1-1 | `/proposals/[id]` 내장 | P0 |
| C2 | **WorkflowPanel** | §13-4, §13-5, §13-7 | `/proposals/[id]` 내장 | P0 |
| C3 | **EvaluationView** | §13-11 | `/proposals/[id]/evaluation` | P0 |
| C4 | **AnalyticsPage** | §13-12 | `/analytics` | P1 |
| C5 | **ProposalEditor** | §13-10 | `/proposals/[id]/edit` | P1 |
| C6 | **KbManagement** | §13-13 | `/kb/labor-rates`, `/kb/market-prices` | P2 |

### 2-2. Out of Scope (이번 Plan 제외)

- Tiptap 공동 편집 (Yjs) — v2 이후
- AI 인라인 질문 (실시간 Claude 호출) — ProposalEditor v2
- RfpSearchPanel (§13-2) — 기존 `/bids` 페이지로 대체
- RFP 파일 업로드 게이트 (§13-3) — `/proposals/new`에 이미 존재
- 역할별 대시보드 (§13-8) — 기존 `/dashboard`로 충분
- 역량 DB 인라인 편집 (§13-9) — v2 이후
- 섹션 잠금 (§24) — 백엔드 미구현

### 2-3. 사전 조건

- [x] 백엔드 API: routes_workflow.py (start/state/resume/stream/history/token-usage) ✅
- [x] 백엔드 API: routes_artifacts.py (artifacts/docx/pptx/compliance) ✅
- [x] 백엔드 API: routes_analytics.py (7개 엔드포인트) ✅
- [x] ProposalState에 evaluation_simulation, compliance_matrix 필드 ✅
- [ ] API 클라이언트 (`lib/api.ts`)에 workflow/analytics/artifacts 메서드 추가 필요

## 3. 기술 결정

### 3-1. 신규 의존성

```
npm install recharts @tiptap/react @tiptap/starter-kit @tiptap/extension-highlight
npm install @radix-ui/react-tabs @radix-ui/react-accordion @radix-ui/react-tooltip
```

**shadcn/ui**: 도입하지 않음. Radix 프리미티브 + Tailwind로 일관성 유지 (기존 패턴 유지).
**이유**: 현재 4,500줄이 모두 Tailwind 인라인으로 작성됨. shadcn 마이그레이션은 별도 작업.

### 3-2. 컴포넌트 구조

```
frontend/
├── components/
│   ├── AppSidebar.tsx          (기존)
│   ├── PhaseGraph.tsx          (C1) 수평 워크플로 그래프
│   ├── WorkflowPanel.tsx       (C2) Go/No-Go + 리뷰 + 병렬 진행
│   ├── EvaluationRadar.tsx     (C3) Recharts 레이더 차트
│   ├── EvaluationView.tsx      (C3) 모의평가 전체 뷰
│   ├── AnalyticsCharts.tsx     (C4) 차트 모음 (Line/Bar/Pie)
│   ├── ProposalEditor.tsx      (C5) Tiptap 3단 에디터
│   ├── EditorTocPanel.tsx      (C5) 좌측 목차+Compliance
│   ├── EditorAiPanel.tsx       (C5) 우측 AI 어시스턴트
│   └── DataTable.tsx           (C6) 범용 CRUD 테이블
├── app/
│   ├── proposals/[id]/
│   │   ├── page.tsx            (기존 — C1, C2 통합)
│   │   ├── evaluation/page.tsx (C3 신규)
│   │   └── edit/page.tsx       (C5 신규)
│   ├── analytics/page.tsx      (C4 신규)
│   └── kb/
│       ├── labor-rates/page.tsx    (C6 신규)
│       └── market-prices/page.tsx  (C6 신규)
└── lib/
    └── api.ts                  (확장: workflow, analytics, artifacts 메서드)
```

### 3-3. API 클라이언트 확장

`lib/api.ts`에 추가할 메서드:

```typescript
// Workflow
workflow: {
  start(id: string, state?: object): Promise<...>,
  getState(id: string): Promise<...>,
  resume(id: string, data: object): Promise<...>,
  getTokenUsage(id: string): Promise<...>,
  stream(id: string): EventSource,
},
// Artifacts
artifacts: {
  get(id: string, step: string): Promise<...>,
  downloadDocx(id: string): string,  // URL
  downloadPptx(id: string): string,  // URL
  getCompliance(id: string): Promise<...>,
},
// Analytics
analytics: {
  failureReasons(params): Promise<...>,
  positioningWinRate(params): Promise<...>,
  monthlyTrends(params): Promise<...>,
  winRate(params): Promise<...>,
  teamPerformance(params): Promise<...>,
  competitor(params): Promise<...>,
  clientWinRate(params): Promise<...>,
},
```

## 4. 구현 순서 (Phase 단위)

### Phase A: 인프라 + API 클라이언트 (선행)
1. `npm install` 의존성 추가
2. `lib/api.ts` 확장 (workflow, artifacts, analytics 메서드)
3. TypeScript 타입 정의 (WorkflowState, EvaluationResult, AnalyticsData 등)

### Phase B: PhaseGraph + WorkflowPanel (C1, C2)
1. `PhaseGraph.tsx` — 수평 노드 그래프 (6 STEP, 상태 뱃지)
2. `WorkflowPanel.tsx` — Go/No-Go 패널 + 리뷰 패널 + 병렬 진행 표시
3. `proposals/[id]/page.tsx` 리팩토링 — 기존 수직 타임라인을 C1+C2로 교체
4. SSE 연동 — `workflow.stream()` → PhaseGraph 실시간 갱신

### Phase C: EvaluationView (C3)
1. `EvaluationRadar.tsx` — Recharts `<RadarChart>` 4축 (compliance/strategy/quality/trustworthiness)
2. `EvaluationView.tsx` — 평가위원 3인 점수 카드 + 레이더 + 취약점 TOP 3 + 예상 Q&A
3. `proposals/[id]/evaluation/page.tsx` — 라우트 + 데이터 fetch

### Phase D: AnalyticsPage (C4)
1. `AnalyticsCharts.tsx` — Recharts LineChart/BarChart/PieChart 래퍼
2. `analytics/page.tsx` — 4개 차트 패널 (실패원인, 포지셔닝별, 월별 추이, 기관별)
3. 기간 필터 + 접근 권한 (lead 이상)

### Phase E: ProposalEditor (C5)
1. `EditorTocPanel.tsx` — 목차 트리 + Compliance Matrix 표시
2. `EditorAiPanel.tsx` — 요건 충족률 게이지 + Win Strategy 체크 + KB 출처 + 변경 이력
3. `ProposalEditor.tsx` — Tiptap 에디터 (인라인 AI 코멘트 하이라이트)
4. `proposals/[id]/edit/page.tsx` — 3단 레이아웃 + 자동 저장 + DOCX 내보내기

### Phase F: KB 관리 (C6)
1. `DataTable.tsx` — 범용 CRUD 테이블 (필터/정렬/페이지네이션)
2. `kb/labor-rates/page.tsx` — 노임단가 관리 (기관/연도/등급/단가)
3. `kb/market-prices/page.tsx` — 낙찰가 벤치마크 (도메인/예산/낙찰률)

## 5. 검증 기준

| # | 기준 | 검증 방법 |
|---|------|----------|
| V1 | PhaseGraph가 6 STEP + 현재 단계 + 체크포인트 표시 | 수동 확인 |
| V2 | WorkflowPanel에서 resume API 호출 → 그래프 갱신 | 수동 확인 |
| V3 | EvaluationView 레이더 차트 4축 렌더링 | 수동 확인 |
| V4 | AnalyticsPage 4개 차트 렌더링 (빈 데이터 포함) | 수동 확인 |
| V5 | ProposalEditor Tiptap 로딩 + 섹션 표시 | 수동 확인 |
| V6 | KB 테이블 CRUD 동작 | 수동 확인 |
| V7 | `npm run build` 에러 없음 | CI |
| V8 | 기존 페이지 (dashboard, bids, resources) 동작 유지 | 수동 확인 |

## 6. 리스크

| 리스크 | 영향 | 완화 |
|--------|------|------|
| Tiptap 번들 크기 (~300KB) | 초기 로딩 지연 | dynamic import + lazy loading |
| Recharts SSR 호환성 | 빌드 에러 | `'use client'` + dynamic import |
| 백엔드 API 응답 형식 불일치 | 타입 에러 | 실제 API 응답으로 타입 검증 |
| 기존 인라인 Tailwind 스타일 충돌 | UI 깨짐 | 컴포넌트별 격리, 기존 패턴 유지 |

## 7. 추정 규모

| Phase | 신규 파일 | 수정 파일 | 예상 줄 수 |
|-------|:---------:|:---------:|:----------:|
| A (인프라) | 0 | 2 | ~200 |
| B (PhaseGraph+Workflow) | 2 | 1 | ~600 |
| C (Evaluation) | 3 | 0 | ~500 |
| D (Analytics) | 2 | 1 | ~400 |
| E (ProposalEditor) | 4 | 0 | ~1,200 |
| F (KB 관리) | 3 | 1 | ~500 |
| **합계** | **14** | **5** | **~3,400** |
