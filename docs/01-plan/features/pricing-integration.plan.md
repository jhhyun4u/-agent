# Plan: pricing-integration (Option A — 통합)

> 독립 가격 시뮬레이터 제거 + 워크플로 STEP 2.5에 집중 + 빠른 견적 이관

## 1. 배경

`/pricing` 독립 도구와 워크플로 STEP 2.5가 동일한 하위 컴포넌트를 공유하지만, 이용자가 두 곳에서 같은 작업을 반복하게 되는 UX 문제가 있음. 검토 결과 Option A(통합) 채택.

## 2. 목표

- `/pricing` 독립 페이지 제거 → 네비게이션 단순화
- 사전 검토 니즈 → `/proposals/new`에서 "빠른 견적" 버튼으로 이관
- 워크플로 STEP 2.5에서 기존 시뮬레이션 이력 불러오기 유지

## 3. 범위

### In-Scope
1. `/pricing`, `/pricing/history` 페이지 삭제
2. 사이드바에서 "가격 시뮬레이터" 메뉴 제거
3. `PricingSimulator.tsx` 컴포넌트 삭제
4. `/proposals/new`에 빠른 견적(quickEstimate) UI 추가
5. `BidPlanReviewPanel`에 기존 시뮬레이션 불러오기 유지 (Option C에서 구현)

### Out-of-Scope
- 하위 컴포넌트(ScenarioCards 등 8개) 삭제 — BidPlanReviewPanel에서 사용
- 백엔드 pricing API 삭제 — 워크플로 bid_plan 노드에서 사용
- apply 엔드포인트 삭제 — 향후 활용 가능

## 4. 수용 기준

- [x] `/pricing` 페이지 접근 불가 (404)
- [x] 사이드바에 "가격 시뮬레이터" 메뉴 없음
- [x] `/proposals/new`에서 예산 있는 공고 → "빠른 견적" 버튼 → 추천가+수주확률 표시
- [x] STEP 2.5에서 기존 시뮬레이션 불러오기 정상 동작
- [x] TypeScript 빌드 에러 0건
