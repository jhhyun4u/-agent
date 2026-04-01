# 제안 프로젝트 목록 페이지 최적화

## 개요

기존 `proposals/page.tsx`의 복잡한 구조를 분리하여 재사용 가능한 컴포넌트와 유틸리티 함수로 리팩토링했습니다.

---

## 생성된 새 파일

### 1. `lib/proposals-utils.ts`

**목적**: 제안서 페이지에서 반복되는 유틸리티 함수 및 상수 중앙화

**제공하는 기능**:

- **상수 정의**:
  - `POS_LABELS`: 포지셔닝 아이콘/색상/레이블 매핑
  - `STEP_MAP`: 워크플로 단계 매핑
  - `TABLE_COLUMNS`: 테이블 컬럼 정의 (너비, 키, 레이블, 정렬 가능 여부 등)
  - `GRID_LAYOUT_CLASS`: CSS Grid 클래스명 (`grid-cols-[1.5fr_100px_80px_100px_100px_110px_100px_100px_36px]`)
  - `SCOPE_LABELS`: 스코프 탭 레이블

- **유틸리티 함수**:
  - `getStepInfo(phase)`: 단계 번호와 라벨 반환
  - `formatDeadline(deadline)`: 마감일 포맷팅 + D-Day 계산
  - `formatBudget(amount)`: 전체 예산 포맷팅
  - `formatBudgetCompact(amount)`: 간단한 예산 포맷 (테이블용, `₩X억`)
  - `deriveStatus(proposal)`: 제안서 상태 도출 (배지 색상, 상태명, 툴팁)
  - `createSortComparator(key, direction)`: 정렬 함수 생성

**이점**:

- 한 곳에서 모든 상수와 함수를 관리
- 테스트 용이
- 다른 컴포넌트에서 재사용 가능

---

### 2. `components/ProposalsTableHeader.tsx`

**목적**: 테이블 헤더를 독립적인 컴포넌트로 분리

**Props**:

- `sortKey`: 현재 정렬 키
- `sortAsc`: 오름차순 여부
- `onSort`: 정렬 클릭 핸들러

**개선 사항**:

- 헤더 렌더링 로직 분리
- 동적 정렬 버튼 생성
- `TABLE_COLUMNS`에서 열 정보를 읽어 자동 렌더링

---

### 3. `components/ProposalsTableRow.tsx`

**목적**: 테이블 행을 재사용 가능한 컴포넌트로 분리

**Props**:

- `proposal`: 제안서 데이터
- `menuOpen`: 현재 열려있는 메뉴 ID
- `onMenuToggle`: 메뉴 토글 콜백
- `onMenuAction`: 메뉴 액션 콜백 (view, resume, delete)

**포함된 기능**:

- 프로젝트명 + 결과 표시
- 포지셔닝 아이콘/레이블
- 단계 + 진행도 바
- 예정가 (budget) 포맷팅
- 입찰가 (bid_amount) 포맷팅 및 색상 코딩
- 마감일 (D-Day 강조)
- 발주처 (client_name)
- 상태 배지 + 툴팁
- 컨텍스트 메뉴

**개선 사항**:

- 행 렌더링 로직을 단순화한 컴포넌트로 분리
- 모든 포맷팅 함수 활용
- 클릭 핸들러를 콜백으로 추상화

---

### 4. `components/ProposalsTableSkeleton.tsx`

**목적**: 로딩 상태 스켈레톤을 재사용 가능한 컴포넌트로 분리

**Props**:

- `rows` (optional, default: 5): 표시할 행의 수

**개선 사항**:

- 스켈레톤 로더를 컴포넌트화
- `GRID_LAYOUT_CLASS` 사용하여 실제 테이블과 동일한 레이아웃 유지
- 동적 행 개수 설정 가능

---

## 리팩토링된 파일

### `app/(app)/proposals/page.tsx`

**변경 사항**:

1. **Imports 정리**:

   ```typescript
   // Before: 각 상수와 함수 인라인 정의
   // After: 모두 proposals-utils에서 import
   ```

2. **코드 라인 수 감소**:
   - Before: ~799줄
   - After: ~650줄 (약 19% 감소)

3. **테이블 렌더링 간소화**:

   ```typescript
   // Before: 복잡한 정렬 로직 + 행 렌더링 인라인
   [...]
     .sort((a, b) => {
       if (!sortKey) return 0;
       const dir = sortAsc ? 1 : -1;
       // 복잡한 정렬 로직...
     })
     .map((p) => {
       // 복잡한 행 렌더링 로직...
     })

   // After: 간단한 구조
   [...]
     .sort(sortKey ? createSortComparator(sortKey, sortAsc ? 1 : -1) : () => 0)
     .map((p) => <ProposalsTableRow ... />)
   ```

4. **컴포넌트 사용**:
   - `<ProposalsTableSkeleton rows={5} />` ← 로딩 상태
   - `<ProposalsTableHeader ... />` ← 헤더
   - `<ProposalsTableRow ... />` ← 각 행

---

## 성능 개선

| 항목          | Before             | After                  | 개선     |
| ------------- | ------------------ | ---------------------- | -------- |
| 파일 크기     | ~799줄             | ~650줄                 | 19% 감소 |
| 유지보수성    | 낮음 (인라인 코드) | 높음 (분리된 컴포넌트) | ✓        |
| 재사용성      | 낮음               | 높음 (3개 컴포넌트)    | ✓        |
| 가독성        | 복잡함             | 명확함                 | ✓        |
| 테스트 가능성 | 어려움             | 용이함                 | ✓        |

---

## 기능 검증 체크리스트

- [x] 테이블 열 정렬 (단계, 마감일)
- [x] 예정가 (budget) 표시
- [x] 입찰가 (bid_amount) 표시 (AI 추천, Human 결정)
- [x] 발주처 (client_name) 표시
- [x] 상태 배지 및 색상 코딩
- [x] 포지셔닝 아이콘/레이블
- [x] 마감일 D-Day 강조
- [x] 컨텍스트 메뉴 (상세보기, 재개, 삭제)
- [x] 로딩 스켈레톤
- [x] 검색 및 필터
- [x] 스코프 탭 (개인/팀/본부/전체)

---

## 다음 단계 (선택 사항)

1. **DataTable.tsx 통합**:
   - 기존 `components/DataTable.tsx`의 제네릭 테이블 기능과 통합 검토

2. **단위 테스트 추가**:
   - `proposals-utils.ts` 함수들의 단위 테스트
   - `ProposalsTableRow.tsx` 컴포넌트 테스트

3. **추가 정렬 기능**:
   - 예정가, 입찰가로 정렬 가능하게 확장 (필요시)

4. **접근성 개선**:
   - ARIA 속성 추가
   - 키보드 네비게이션 개선

---

## 사용 예시

```typescript
import {
  getStepInfo,
  formatDeadline,
  formatBudgetCompact,
  deriveStatus,
  createSortComparator,
  SCOPE_LABELS,
  POS_LABELS,
} from "@/lib/proposals-utils";
import {
  ProposalsTableHeader,
  ProposalsTableRow,
  ProposalsTableSkeleton,
} from "@/components";

// 단계 정보 조회
const { step, label } = getStepInfo("strategy_generate"); // { step: 2, label: "전략수립" }

// 마감일 포맷팅
const { text, urgent, dDay } = formatDeadline("2026-04-15");

// 예산 포맷팅
const formatted = formatBudgetCompact(1500000000); // "₩15억"

// 상태 도출
const { label, dotColor, textColor, tooltip } = deriveStatus(proposal);

// 정렬
const comparator = createSortComparator("deadline", 1);
const sorted = proposals.sort(comparator);
```
