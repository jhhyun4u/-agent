# Frontend Design Gap 설계서

> **Feature**: frontend-design-gap
> **Plan**: `docs/01-plan/features/frontend-design-gap.plan.md`
> **Version**: v1.0 (2026-03-29)
> **목표**: 설계 문서(§13) 대비 프론트엔드 갭 해소 → 충실도 94% → 98%+

---

## 0. Plan 대비 현황 재평가

Plan 작성(2026-03-25) 이후 GoNoGoPanel이 v4.0으로 업데이트되어 Plan Phase A 항목이 **이미 구현 완료**됨.

| Plan Phase | Plan 설명 | 현재 상태 | 이 설계서 범위 |
|:----------:|-----------|:---------:|:--------------:|
| A | GoNoGoPanel 4축 점수 + 강점/리스크 | **구현 완료** (v4.0) | 제외 |
| B | 대시보드 역할별 위젯 | **미구현** (스코프 토글만 존재) | **포함** |
| C | 포지셔닝 변경 영향 미리보기 | **부분 구현** (인라인 callout, 모달 없음) | **포함** |
| D | UI 인프라 (Tiptap 확장 + cn 유틸) | **미구현** | **포함** |
| E | LOW 우선순위 | 선택적 | 제외 (별도 PDCA) |

**실제 구현 범위: Phase B + C + D (3개 Phase)**

---

## 1. Phase B — 대시보드 역할별 위젯

### 1.1 현재 구조

`app/(app)/dashboard/page.tsx`:
- `Scope` 타입: `"personal" | "team" | "division" | "company"`
- 위젯 토글 시스템 (localStorage 기반)
- 데이터: `WinRateStats`, `ProposalSummary[]`, `CalendarItem[]`, `RecommendedBid[]`
- 차트: `FailureReasonsPie`, `MonthlyTrendsLine`, `ClientWinRateBar`
- 분석: `TeamPerformanceData`, `PositioningWinRateData`

### 1.2 추가 위젯 설계

#### B-1. 결재 대기 위젯 (팀장용)

**표시 조건**: `scope === "team"`일 때 자동 표시

```typescript
// 데이터 소스: 기존 api.proposals.list 활용
const pendingReviews = proposals.filter(
  p => p.status === "review_pending" || p.has_pending_interrupt
);
```

**UI 구조**:
```
┌─────────────────────────────────────────────┐
│ 📋 결재 대기 (3건)                           │
├─────────────────────────────────────────────┤
│ ● OO시 도시재생 전략수립  │ review_rfp │ D-5 │
│ ● △△구 교통영향분석       │ go_no_go   │ D-3 │
│ ● □□부 스마트시티 ISP     │ review_plan│ D-12│
└─────────────────────────────────────────────┘
```

**컴포넌트 상세**:
- 각 행: 프로젝트명 + 대기 중인 interrupt 노드명 + D-day
- 클릭 → `/proposals/{id}` 이동 (해당 리뷰 단계로)
- D-3 이하: 빨간색 강조
- 빈 상태: "결재 대기 건이 없습니다" 메시지

**수정 파일**: `app/(app)/dashboard/page.tsx`
**추가 API 호출**: 없음 (기존 `proposals` 데이터 + `has_pending_interrupt` 필터)

#### B-2. 마감 임박 경고 위젯 (팀장용)

**표시 조건**: `scope === "team"`일 때 자동 표시

```typescript
// 기존 CalendarItem + ProposalSummary 조합
const urgentItems = calendarItems
  .filter(c => calcDDay(c.deadline) <= 7 && calcDDay(c.deadline) >= 0)
  .sort((a, b) => calcDDay(a.deadline) - calcDDay(b.deadline));
```

**UI 구조**:
```
┌─────────────────────────────────────────────┐
│ ⚠️ 마감 임박 (D-7 이내)                      │
├─────────────────────────────────────────────┤
│ 🔴 D-2  OO시 도시재생      제안서 미완성     │
│ 🟡 D-5  △△구 교통영향      제출서류 준비중   │
│ 🟡 D-7  □□부 스마트시티    전략 수립 중       │
└─────────────────────────────────────────────┘
```

**컴포넌트 상세**:
- D-day 컬러: D-3 이하 빨간, D-7 이하 노란
- 현재 상태(current_step) 표시로 병목 파악
- 클릭 → 해당 프로젝트 이동

**수정 파일**: `app/(app)/dashboard/page.tsx`
**추가 API 호출**: 없음 (기존 데이터 활용)

#### B-3. 본부별 비교 테이블 (경영진용)

**표시 조건**: `scope === "company"`일 때 자동 표시

```typescript
// 기존 api.analytics.teamPerformance() 데이터 활용
// TeamPerformanceData 타입 이미 정의됨
```

**UI 구조**:
```
┌──────────────────────────────────────────────────────────┐
│ 📊 본부별 성과 비교                                        │
├──────────┬────────┬────────┬──────────┬─────────────────┤
│ 본부      │ 진행건 │ 수주율  │ 평균 소요 │ 전월 대비       │
├──────────┼────────┼────────┼──────────┼─────────────────┤
│ 도시계획부 │ 12     │ 42%    │ 18일     │ ▲ +5%          │
│ 교통부     │ 8      │ 38%    │ 22일     │ ▼ -2%          │
│ 환경부     │ 5      │ 55%    │ 15일     │ ▲ +12%         │
└──────────┴────────┴────────┴──────────┴─────────────────┘
```

**컴포넌트 상세**:
- `api.analytics.teamPerformance()` 응답을 division 레벨로 집계
- 수주율 기준 정렬 (기본) + 컬럼 헤더 클릭 정렬
- 전월 대비 증감 화살표 (▲ green / ▼ red)

**수정 파일**: `app/(app)/dashboard/page.tsx`
**추가 API 호출**: 없음 (`teamPerformance` 이미 호출됨)

### 1.3 위젯 조건부 렌더링 로직

```typescript
// 기존 위젯 토글 시스템에 역할별 위젯 추가
const roleWidgets = {
  team: ["pendingReviews", "urgentDeadlines"],     // 팀장
  company: ["divisionComparison"],                  // 경영진
};

// scope 변경 시 해당 역할 위젯 자동 표시
useEffect(() => {
  if (scope === "team" || scope === "company") {
    // roleWidgets[scope] 위젯들을 위젯 목록 상단에 삽입
  }
}, [scope]);
```

---

## 2. Phase C — 포지셔닝 변경 영향 미리보기 모달

### 2.1 현재 구현

`GoNoGoPanel.tsx`:
- `impactInfo` state로 `api.workflow.impact()` 호출
- 인라인 amber callout으로 재생성 대상 STEP 표시
- **모달 없음** — 변경 확정/취소 워크플로 부재

### 2.2 PositioningImpactModal 설계

**트리거**: GoNoGoPanel에서 포지셔닝 드롭다운 변경 시

#### 컴포넌트 인터페이스

```typescript
// components/PositioningImpactModal.tsx

interface PositioningImpactModalProps {
  open: boolean;
  onClose: () => void;
  onConfirm: (newPositioning: string) => void;
  proposalId: string;
  currentPositioning: string;
  newPositioning: string;
}
```

#### UI 구조

```
┌──────────────────────────────────────────────┐
│ ⚠️ 포지셔닝 변경 영향 분석                     │  ← 헤더
├──────────────────────────────────────────────┤
│                                              │
│  현재: 🛡️ 방어형  →  변경: ⚔️ 공격형           │  ← 변경 요약
│                                              │
│ ┌──────────────────────────────────────────┐ │
│ │ 영향 받는 항목                            │ │
│ │                                          │ │
│ │ • Ghost Theme 변경                       │ │
│ │ • Win Theme 재설정                       │ │
│ │ • 가격 전략 재계산 필요                    │ │
│ │ • 인력 구성 재검토 필요                    │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ ┌──────────────────────────────────────────┐ │
│ │ 📋 재생성 범위                            │ │
│ │                                          │ │
│ │ STEP 2 전략 수립          → 재실행        │ │
│ │ STEP 3 계획               → 재실행        │ │
│ │ STEP 4 제안서 작성         → 재실행        │ │
│ │ STEP 5 PPT                → 재실행        │ │
│ └──────────────────────────────────────────┘ │
│                                              │
│ ⚠️ 승인 상태가 초기화됩니다.                    │  ← 경고
│                                              │
│          [취소]          [변경 확정]           │  ← 액션
└──────────────────────────────────────────────┘
```

#### 데이터 소스

```typescript
// 기존 API 활용
const impact = await api.workflow.impact(proposalId, "go_no_go");
// 응답: { affected_steps: number[], message: string }
```

#### 영향 항목 매핑

```typescript
const IMPACT_ITEMS: Record<string, string[]> = {
  "defensive→offensive": ["Ghost Theme 변경", "Win Theme 재설정", "가격 전략 재계산", "인력 구성 재검토"],
  "offensive→defensive": ["Win Theme 축소", "가격 안정화", "리스크 최소화 전략"],
  "defensive→adjacent": ["Ghost Theme 조정", "틈새 전략 수립", "차별화 포인트 재설정"],
  // ... 기타 조합
};
```

#### GoNoGoPanel 연동

```typescript
// GoNoGoPanel.tsx 수정 — 포지셔닝 변경 시 모달 트리거
const handlePositioningChange = (newPos: string) => {
  if (newPos !== currentPositioning) {
    setShowImpactModal(true);
    setPendingPositioning(newPos);
  }
};

const handleImpactConfirm = (confirmedPos: string) => {
  setPositioning(confirmedPos);
  setShowImpactModal(false);
  // 기존 impactInfo 인라인 callout도 업데이트
};
```

**신규 파일**: `components/PositioningImpactModal.tsx`
**수정 파일**: `components/GoNoGoPanel.tsx` (모달 트리거 + state 추가)

---

## 3. Phase D — UI 인프라 보강

### 3.1 cn() 유틸 함수

**목적**: 조건부 Tailwind 클래스 결합 표준화

```typescript
// lib/utils.ts (신규)
import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

**적용 범위**: 신규/수정 컴포넌트에서 사용. 기존 컴포넌트는 점진적 마이그레이션 (이 PDCA 범위 외).

**패키지 설치**:
```bash
npm install clsx tailwind-merge
```

### 3.2 Tiptap 확장

**목적**: 편집기 테이블 편집 + 빈 에디터 가이드 텍스트

**패키지 설치**:
```bash
npm install @tiptap/extension-table @tiptap/extension-table-row @tiptap/extension-table-cell @tiptap/extension-table-header @tiptap/extension-placeholder
```

**ProposalEditor.tsx 수정**:

```typescript
// 추가 import
import Table from "@tiptap/extension-table";
import TableRow from "@tiptap/extension-table-row";
import TableCell from "@tiptap/extension-table-cell";
import TableHeader from "@tiptap/extension-table-header";
import Placeholder from "@tiptap/extension-placeholder";

// useEditor extensions 배열에 추가
const editor = useEditor({
  extensions: [
    StarterKit,
    Highlight.configure({ multicolor: false }),
    // ↓ 신규 추가
    Table.configure({ resizable: true }),
    TableRow,
    TableCell,
    TableHeader,
    Placeholder.configure({
      placeholder: "이 섹션의 내용을 작성하세요...",
    }),
  ],
  // ...
});
```

**Toolbar 확장**:
```typescript
// 기존 Toolbar에 테이블 삽입 버튼 추가
<button
  onClick={() =>
    editor.chain().focus().insertTable({ rows: 3, cols: 3, withHeaderRow: true }).run()
  }
  title="표 삽입"
>
  ⊞
</button>
```

**수정 파일**: `components/ProposalEditor.tsx`, `package.json`

---

## 4. 파일 변경 요약

### 신규 파일 (2개)

| 파일 | Phase | 예상 줄수 | 설명 |
|------|:-----:|:---------:|------|
| `components/PositioningImpactModal.tsx` | C | ~120 | 포지셔닝 변경 영향 모달 |
| `lib/utils.ts` | D | ~6 | cn() 유틸 함수 |

### 수정 파일 (3개)

| 파일 | Phase | 변경 내용 |
|------|:-----:|-----------|
| `app/(app)/dashboard/page.tsx` | B | 결재대기 + 마감임박 + 본부비교 위젯 3개 추가 (~150줄) |
| `components/GoNoGoPanel.tsx` | C | 포지셔닝 변경 시 모달 트리거 + state (~20줄) |
| `components/ProposalEditor.tsx` | D | Table/Placeholder 확장 import + Toolbar 버튼 (~30줄) |

### 패키지 추가 (package.json)

| 패키지 | Phase | 용도 |
|--------|:-----:|------|
| `clsx` | D | 조건부 클래스 결합 |
| `tailwind-merge` | D | Tailwind 클래스 충돌 해소 |
| `@tiptap/extension-table` | D | 편집기 테이블 |
| `@tiptap/extension-table-row` | D | 테이블 행 |
| `@tiptap/extension-table-cell` | D | 테이블 셀 |
| `@tiptap/extension-table-header` | D | 테이블 헤더 |
| `@tiptap/extension-placeholder` | D | 편집기 플레이스홀더 |

---

## 5. 구현 순서

```
Phase D (UI 인프라)              ← 가장 독립적, npm install 선행
  ↓
Phase B (대시보드 역할별 위젯)    ← cn() 활용 가능, API 추가 호출 없음
  ↓
Phase C (포지셔닝 모달)          ← GoNoGoPanel 수정, 모달 신규
```

> Phase D를 먼저 진행하는 이유: `cn()` 함수를 Phase B, C에서 활용 가능.
> Phase B와 C는 독립적이므로 병렬 가능하나, GoNoGoPanel과 대시보드 파일이 다르므로 순서 무관.

---

## 6. 스타일 가이드

기존 프로젝트 컨벤션 준수:

| 항목 | 규칙 |
|------|------|
| 컴포넌트 | `"use client"` 선언, 함수 컴포넌트 + default export |
| 색상 | 다크 모드 우선 (`bg-[#1c1c1c]`, `text-[#ededed]`, `border-[#333]`) |
| 간격 | Tailwind 유틸리티 직접 사용 |
| 상태 | `useState` + `useEffect` (외부 상태관리 없음) |
| API | `@/lib/api`의 `api` 객체 사용 |
| 에러 | try-catch + 사용자 메시지 (`setError("...")`) |

---

## 7. 성공 기준

| 지표 | 현재 | 목표 | 검증 방법 |
|------|:----:|:----:|-----------|
| 갭 분석 종합 | 94% | 98%+ | `/pdca analyze` |
| 대시보드 §13-8 충실도 | 75% | 90% | 역할별 위젯 표시 확인 |
| 포지셔닝 §13-6 | 부분 | 완성 | 모달 동작 확인 |
| UI 인프라 §31-3 | 75% | 85% | Tiptap 표 삽입 + cn() 작동 |
| TypeScript 빌드 에러 | 0 | 0 | `npm run build` |

---

## 8. 범위 외 (NOT Scope)

| 항목 | 사유 |
|------|------|
| GoNoGoPanel 4축 점수 | Plan Phase A — 이미 v4.0 구현 완료 |
| shadcn/ui 전면 도입 | Radix + Tailwind로 기능 동일, 마이그레이션 비용 대비 효과 미미 |
| Plan Phase E LOW 항목 | 별도 PDCA로 관리 (병렬 미리보기, AI 하이라이트, 결재선 등) |
| Azure AD SSO | 인프라 의존, 별도 PDCA |
| 기존 컴포넌트 cn() 마이그레이션 | 점진적으로 진행, 이 PDCA 범위 외 |
