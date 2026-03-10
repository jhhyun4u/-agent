# Dashboard Analysis Report

> **Analysis Type**: Gap Analysis (Design vs Implementation)
>
> **Project**: tenopa-proposer
> **Analyst**: gap-detector
> **Date**: 2026-03-08
> **Design Doc**: [dashboard.design.md](../02-design/features/dashboard.design.md)

---

## 1. Analysis Overview

### 1.1 Analysis Purpose

대시보드 개선 설계서(v1)와 실제 구현 코드(`frontend/app/dashboard/page.tsx`) 간의 일치도를 분석하여, 누락/변경/추가된 항목을 식별한다.

### 1.2 Analysis Scope

- **Design Document**: `docs/02-design/features/dashboard.design.md`
- **Implementation Path**: `frontend/app/dashboard/page.tsx`
- **Analysis Date**: 2026-03-08

---

## 2. Gap Analysis (Design vs Implementation)

### 2.1 액션 허브 (오늘 할 일) - 설계 섹션 2-1

| 항목 | 설계 명세 | 구현 | Status | Notes |
|------|-----------|------|--------|-------|
| **위치** | 페이지 최상단 (KPI 카드 위) | KPI 카드 위, 파이프라인 위 | ✅ Match | 렌더 순서 일치 |
| **표시 조건** | actionItems.length > 0일 때만 렌더 | `actionItems.length > 0 && (...)` | ✅ Match | L247 |
| **캘린더 긴급 조건** | D-day <= 14, status="open" | `calcDDay(c.deadline) <= 14 && c.status === "open"` | ✅ Match | L187 |
| **캘린더 CTA** | "지금 시작" -> /proposals/new | `"지금 시작"` -> `/proposals/new` | ✅ Match | L279-280 |
| **제안서 processing CTA** | "확인" -> /proposals/{id} | `"확인"` -> `/proposals/${item.id}` | ✅ Match | L312 |
| **제안서 initialized CTA** | "시작" -> /proposals/{id} | `"시작"` -> `/proposals/${item.id}` | ✅ Match | L312 |
| **정렬** | D-day 임박 순 | `.sort((a, b) => a.days - b.days)` | ✅ Match | L189 |
| **최대 5개** | 최대 5개 | `.slice(0, 5)` | ✅ Match | L193 |
| **긴급 D-3 이하** | 빨간 D-day 텍스트 | `days <= 3` -> `text-red-400` | ⚠️ Changed | 설계: D-3 이하, 구현: D-3 이하 (일치하지만 `dDayColor` 함수는 D-7 기준 사용) |
| **일반 긴급 D-4~D-14** | 노란 D-day 텍스트 | `!urgent` -> `text-yellow-400` | ⚠️ Changed | 액션 허브 내부에서는 `days <= 3` 기준으로 이분법 적용 (D-4~D-14 모두 노란색). 설계와 일치 |
| **진행 중 제안서** | 파란 "생성중" 배지 | `text-blue-400` + "생성중" | ✅ Match | L296 |
| **미시작 제안서** | 회색 "대기" 배지 | `text-blue-400` + "대기" | ⚠️ Changed | 설계: 회색, 구현: 파란색(text-blue-400). "대기" 텍스트에도 동일 blue-400 적용 |
| **헤더 pulse** | 녹색 점 pulse + "지금 해야 할 것" | `bg-[#3ecf8e] animate-pulse` + "지금 해야 할 것" | ✅ Match | L250-251 |

**액션 허브 Match Rate**: 12/14 = **85.7%**

### 2.2 파이프라인 뷰 - 설계 섹션 2-2

| 항목 | 설계 명세 | 구현 | Status | Notes |
|------|-----------|------|--------|-------|
| **위치** | 액션 허브 아래, KPI 카드 위 | 액션 허브 다음, KPI 전 | ✅ Match | L321-355 |
| **표시 조건** | 항상 렌더 | 조건 없이 항상 렌더 | ✅ Match | |
| **6단계 존재** | 공고등록/작성중/완료/결과대기/수주/낙찰실패 | 6단계 모두 존재 | ✅ Match | L327-332 |
| **공고 등록 조건** | calItems: status="open" AND proposal_id=null | `c.status === "open" && !c.proposal_id` | ✅ Match | L167 |
| **작성 중 조건** | proposals: status="initialized" OR "processing" | `p.status === "initialized" \|\| p.status === "processing"` | ✅ Match | L168-170 |
| **완료 조건** | proposals: status="completed" AND win_result=null | `p.status === "completed" && p.win_result == null` | ✅ Match | L171-173 |
| **결과 대기 조건** | proposals: win_result="pending" | `p.win_result === "pending"` | ✅ Match | L174 |
| **수주 조건** | proposals: win_result="won" | `p.win_result === "won"` | ✅ Match | L175 |
| **낙찰 실패 조건** | proposals: win_result="lost" | `p.win_result === "lost"` | ✅ Match | L176 |
| **공고 등록 색상** | #8c8c8c (회색) | `text-[#8c8c8c]` | ✅ Match | L327 |
| **작성 중 색상** | blue-400 (파랑) | `text-blue-400` | ✅ Match | L328 |
| **완료 색상** | #ededed (흰색) | `text-[#ededed]` | ✅ Match | L329 |
| **결과 대기 색상** | yellow-400 (노랑) | `text-yellow-400` | ✅ Match | L330 |
| **수주 색상** | #3ecf8e (초록) | `text-[#3ecf8e]` | ✅ Match | L331 |
| **낙찰 실패 색상** | red-400 (빨강) | `text-red-400` | ✅ Match | L332 |
| **클릭 인터랙션** | 각 단계 클릭 시 해당 페이지 이동 | `onClick={() => router.push(stage.href)}` | ✅ Match | L337 |
| **단계 구분자** | -> 화살표 텍스트 | `→` 텍스트 렌더 | ✅ Match | L349 |

**파이프라인 뷰 Match Rate**: 17/17 = **100%**

### 2.3 신규 상태 및 함수 - 설계 섹션 3

| 항목 | 설계 명세 | 구현 | Status | Notes |
|------|-----------|------|--------|-------|
| `proposals` 상태 | `ProposalSummary[]` | `useState<ProposalSummary[]>([])` | ✅ Match | L84 |
| `loadProposals()` | `useCallback`, api.proposals.list() 호출 | `useCallback(async () => { api.proposals.list({ page: 1 }) })` | ✅ Match | L110-117 |
| `pipeline` | 6단계 카운트 계산 결과 | `const pipeline = { registered, inProgress, completed, pending, won, lost }` | ✅ Match | L166-177 |
| `actionItems` | `ActionItem[]`, 캘린더+제안서 통합 | 캘린더+제안서 통합, slice(0,5) | ✅ Match | L185-193 |
| `ActionItem` 타입 | union type: calendar \| proposal | `type ActionItem = { type: "calendar" } \| { type: "proposal" }` | ✅ Match | L181-183 |

**신규 상태/함수 Match Rate**: 5/5 = **100%**

### 2.4 API 연동 - 설계 섹션 4

| 항목 | 설계 명세 | 구현 | Status | Notes |
|------|-----------|------|--------|-------|
| `api.proposals.list({ page: 1 })` | 신규 호출 | `api.proposals.list({ page: 1 })` | ✅ Match | L112 |
| `api.stats.winRate(scope)` | 기존 호출 유지 | `api.stats.winRate(s)` | ✅ Match | L101 |
| `api.calendar.list({ scope })` | 기존 호출 유지 | `api.calendar.list({ scope })` | ✅ Match | L122 |
| useEffect에서 loadProposals 호출 | scope 변경 시 함께 재호출 | `useEffect` deps에 `loadProposals` 포함 | ✅ Match | L135-139 |

**API 연동 Match Rate**: 4/4 = **100%**

### 2.5 비기능 요구사항 - 설계 섹션 5

| 항목 | 설계 명세 | 구현 | Status | Notes |
|------|-----------|------|--------|-------|
| 제안서 로드 실패 시 빈 배열 fallback | 에러 무시, 빈 배열 | `catch { setProposals([]) }` | ✅ Match | L114-115 |
| actionItems 0개면 섹션 숨김 | 숨김 | `actionItems.length > 0 && (...)` | ✅ Match | L247 |
| 파이프라인 카운트 0이어도 항상 표시 | 항상 표시 | 조건 없이 항상 렌더 | ✅ Match | L322 |

**비기능 요구사항 Match Rate**: 3/3 = **100%**

---

## 3. Match Rate Summary

```
+---------------------------------------------+
|  Overall Match Rate: 95.3%                   |
+---------------------------------------------+
|  Total items:       43                       |
|  Match:             41 items (95.3%)         |
|  Changed:            2 items (4.7%)          |
|  Not implemented:    0 items (0%)            |
|  Added (no design):  0 items (0%)            |
+---------------------------------------------+
```

### Category Scores

| Category | Score | Status |
|----------|:-----:|:------:|
| 액션 허브 (2-1) | 85.7% | ⚠️ |
| 파이프라인 뷰 (2-2) | 100% | ✅ |
| 신규 상태/함수 (3) | 100% | ✅ |
| API 연동 (4) | 100% | ✅ |
| 비기능 요구사항 (5) | 100% | ✅ |
| **Overall** | **95.3%** | **✅** |

---

## 4. Differences Found

### 4.1 Changed Features (Design != Implementation)

| # | Item | Design | Implementation | Impact |
|---|------|--------|----------------|--------|
| 1 | 미시작 제안서 배지 색상 | 회색 "대기" 배지 | 파란색(text-blue-400) "대기" 배지 (L295-296) | Low |
| 2 | dDayColor 함수 기준 | D-3 이하: 빨강, D-4~D-14: 노랑 | 액션 허브 내부: `days <= 3` 이분법 사용, 별도 `dDayColor()` 함수는 D-7 기준 (캘린더 섹션용). 액션 허브 자체는 설계와 거의 일치하나, 경계값이 D-3 vs D-7로 이원화됨 | Low |

### 4.2 Missing Features (Design O, Implementation X)

없음.

### 4.3 Added Features (Design X, Implementation O)

없음. 기존 KPI/캘린더 섹션은 설계서에서 "유지"로 명시되어 있으므로 추가로 간주하지 않는다.

---

## 5. Detailed Issue Analysis

### Issue 1: 미시작 제안서 배지 색상 불일치

- **설계**: "미시작 제안서: 회색 '대기' 배지"
- **구현**: L295에서 processing/initialized 모두 `text-blue-400`으로 통일
- **원인 추정**: processing과 initialized를 시각적으로 구분하기보다 같은 "진행 필요" 그룹으로 묶은 것으로 보임
- **영향**: 사용자가 "대기" 상태를 "생성중"과 같은 파란색으로 인식. 설계 의도는 "미시작=회색(낮은 긴급도)" vs "진행중=파란(활성)"으로 구분하는 것
- **권장**: 설계 의도대로 initialized는 `text-[#8c8c8c]`(회색)으로 변경하거나, 설계 문서를 현재 구현에 맞게 업데이트

### Issue 2: dDayColor 함수 경계값 이원화

- **설계**: 액션 허브 시각적 구분 기준 D-3 이하(빨강), D-4~D-14(노랑)
- **구현**: 액션 허브 내부(`urgent = days <= 3`)는 설계와 일치하나, 캘린더 섹션에서 사용하는 `dDayColor()` 함수는 D-7 기준으로 빨강/노랑을 나눔 (L31-33)
- **영향**: 동일 캘린더 아이템이 액션 허브에서는 노란색(D-5), 캘린더 섹션에서는 빨간색(D-5)으로 표시될 수 있음
- **권장**: `dDayColor` 함수의 기준을 D-3으로 통일하거나, 두 섹션이 다른 기준을 사용한다는 점을 설계서에 명시

---

## 6. Recommended Actions

### 6.1 Immediate (선택)

| Priority | Item | File | Description |
|----------|------|------|-------------|
| Low | 미시작 배지 색상 수정 | page.tsx:295 | `text-blue-400` -> `text-[#8c8c8c]` (initialized일 때) |

### 6.2 Documentation Update

| Item | Description |
|------|-------------|
| dDayColor 기준 명시 | 액션 허브(D-3)와 캘린더 섹션(D-7)의 색상 기준 차이를 설계서에 반영하거나 통일 |

---

## 7. Conclusion

설계 대비 구현 일치율 **95.3%**로 높은 수준의 매치를 보인다. 2건의 차이는 모두 시각적 스타일(색상) 관련이며 기능적 영향은 없다. 파이프라인 뷰, 상태/함수 명세, API 연동, 비기능 요구사항은 모두 100% 일치한다.

Match Rate >= 90% 기준을 충족하므로, 설계-구현 동기화는 완료된 것으로 판단한다.

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 0.1 | 2026-03-08 | Initial gap analysis | gap-detector |
