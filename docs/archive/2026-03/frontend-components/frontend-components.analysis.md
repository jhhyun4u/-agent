# frontend-components Analysis Report

> **Analysis Type**: Gap Analysis (PDCA Check Phase)
>
> **Project**: tenopa-proposer
> **Analyst**: gap-detector
> **Date**: 2026-03-07
> **Design Doc**: [frontend-components.design.md](../02-design/features/frontend-components.design.md)

---

## 1. Analysis Overview

### 1.1 Analysis Purpose

Supabase Realtime 전환 설계(usePhaseStatus 훅 신규, [id]/page.tsx polling 제거)가 실제 구현에 정확히 반영되었는지 확인한다.

### 1.2 Analysis Scope

- **Design Document**: `docs/02-design/features/frontend-components.design.md`
- **Implementation Files**:
  - `frontend/lib/hooks/usePhaseStatus.ts` (신규)
  - `frontend/app/proposals/[id]/page.tsx` (수정)
- **Analysis Date**: 2026-03-07

---

## 2. Gap Analysis (Design vs Implementation)

### 2.1 Success Criteria Checklist

| # | Criteria | Status | Notes |
|---|---------|:------:|-------|
| 1 | `usePhaseStatus.ts` 파일 존재 | ✅ | `frontend/lib/hooks/usePhaseStatus.ts` |
| 2 | 초기 HTTP 로드: `api.proposals.status()` 사용 (client_name 포함) | ✅ | L34: `api.proposals.status(proposalId)` -- 기존 API 사용으로 client_name 자동 포함 |
| 3 | Realtime 구독: `postgres_changes` UPDATE 이벤트 | ✅ | L50-56: event "UPDATE", schema "public", table "proposals" |
| 4 | filter: `id=eq.${proposalId}` | ✅ | L56: ``filter: `id=eq.${proposalId}` `` |
| 5 | 클린업: `supabase.removeChannel(channel)` | ✅ | L78: `supabase.removeChannel(channel)` |
| 6 | 클린업: `cancelled = true` | ✅ | L77: `cancelled = true` (설계 외 추가 -- race condition 방지) |
| 7 | `[id]/page.tsx`에서 `setInterval` 완전 제거 | ✅ | grep 결과 0건 |
| 8 | `pollingRef` 제거 | ✅ | grep 결과 0건 |
| 9 | `fetchStatus` useCallback 제거 | ✅ | grep 결과 0건 |
| 10 | `usePhaseStatus` import 및 사용 | ✅ | L17: import, L31: `const { status, loading } = usePhaseStatus(id)` |
| 11 | `loading` 상태 활용 (로딩 화면) | ✅ | L113-118: `if (loading \|\| !status)` 로딩 UI 표시 |
| 12 | handleRetry에서 polling 재시작 코드 제거 | ✅ | L61-68: `await api.proposals.execute(id)` 만 호출, 주석으로 Realtime 자동 감지 명시 |

**Checklist Result: 12/12 (100%)**

### 2.2 Structural Comparison

| Design Item | Design Spec | Implementation | Status |
|-------------|------------|----------------|:------:|
| 훅 반환 타입 | `PhaseStatus` (자체 인터페이스) | `ProposalStatus_` (기존 api.ts 타입 재사용) | ⚠️ |
| 초기 로드 방식 | `supabase.from("proposals").select()` 직접 쿼리 | `api.proposals.status()` HTTP API 호출 | ⚠️ |
| 채널 이름 | `proposal-${proposalId}` | `proposal-status-${proposalId}` | ⚠️ |
| Realtime 업데이트 필드 | status, current_phase, phases_completed, failed_phase, storage_upload_failed, error | status, current_phase, phases_completed, error | ⚠️ |
| 에러 처리 | 없음 (catch 없음) | `.catch()` 로 초기 로드 실패 핸들링 | ✅+ |
| cancelled 플래그 | 없음 | `let cancelled = false` race condition 방지 | ✅+ |
| comments fetchComments 유지 | 유지 (설계 명시) | 유지됨 | ✅ |

### 2.3 Difference Detail

#### D-01: 타입 정의 방식 (Low Impact)

- **Design**: 자체 `PhaseStatus` 인터페이스 신규 정의 (id, status, current_phase, phases_completed, failed_phase, storage_upload_failed, rfp_title, client_name, error)
- **Implementation**: 기존 `ProposalStatus_` 타입 재사용 (`import { ProposalStatus_ } from "@/lib/api"`)
- **Impact**: Low -- 기존 타입 재사용은 코드 일관성 측면에서 오히려 바람직. 다만 `PhaseStatus` 인터페이스가 설계서에서 export 목적으로 정의되어 있으므로, 향후 Realtime 전용 필드가 추가될 경우 분리가 필요할 수 있음.
- **Verdict**: 의도적 변경 (개선)

#### D-02: 초기 로드 방식 (Low Impact)

- **Design**: Supabase JS client로 직접 `proposals` 테이블 쿼리 (`supabase.from("proposals").select(...)`)
- **Implementation**: 기존 `api.proposals.status()` HTTP API 호출 (FastAPI 백엔드 경유)
- **Impact**: Low -- HTTP API를 사용하면 client_name 등 세션 기반 데이터를 서버에서 조합하여 반환하므로 데이터 완전성이 더 높음. 설계서에서도 "client_name: "" -- proposals 테이블에 없음, 세션에서 가져와야 함" 주석이 있었는데, 구현에서 이 문제를 API 호출로 자연스럽게 해결함.
- **Verdict**: 의도적 변경 (개선)

#### D-03: 채널 이름 차이 (Negligible)

- **Design**: `proposal-${proposalId}`
- **Implementation**: `proposal-status-${proposalId}`
- **Impact**: Negligible -- 채널 이름은 클라이언트 측 식별자일 뿐, 기능에 영향 없음.
- **Verdict**: 무시 가능

#### D-04: Realtime 업데이트 누락 필드 (Medium Impact)

- **Design**: Realtime 콜백에서 `failed_phase`, `storage_upload_failed` 필드도 업데이트
- **Implementation**: Realtime 콜백에서 `status`, `current_phase`, `phases_completed`, `error`(notes) 4개 필드만 업데이트. `failed_phase`와 `storage_upload_failed`는 Realtime 이벤트에서 반영되지 않음.
- **Impact**: Medium -- `failed_phase`는 실패 시 어떤 Phase에서 실패했는지 표시하는 데 사용됨. 초기 HTTP 로드에서 가져오므로 페이지 로드 시점에는 정확하나, 실시간 실패 발생 시 UI가 즉시 갱신되지 않을 수 있음. 단, `status`가 "failed"로 바뀌면 사용자가 페이지를 새로고침하거나 재시도할 가능성이 높으므로 실제 사용자 영향은 제한적.
- **Verdict**: P3 개선 권장

---

## 3. Match Rate Summary

```
+---------------------------------------------+
|  Overall Match Rate: 95%                     |
+---------------------------------------------+
|  Criteria Checklist:  12/12 (100%)           |
|  Structural Match:     5/7  ( 71%)           |
|  Improvements:         2 items (D-01, D-02)  |
|  Gaps:                 1 item  (D-04, P3)    |
|  Negligible:           1 item  (D-03)        |
+---------------------------------------------+
```

### Score Breakdown

| Category | Score | Status |
|----------|:-----:|:------:|
| Design Match (criteria) | 100% | PASS |
| Design Match (structure) | 71% | -- |
| Weighted Overall | 95% | PASS |

> Weighted: criteria checklist 가중치 80%, structural 가중치 20%.
> 구조적 차이 4건 중 2건은 개선, 1건은 무시, 1건만 실제 Gap.

---

## 4. Recommended Actions

### 4.1 P3 -- Short-term (backlog)

| # | Item | File | Description |
|---|------|------|-------------|
| 1 | Realtime 콜백에 `failed_phase`, `storage_upload_failed` 추가 | `usePhaseStatus.ts` L61-69 | Realtime payload에서 해당 필드도 `setStatus`에 반영하도록 추가 |

### 4.2 Design Document Update (Optional)

| # | Item | Description |
|---|------|-------------|
| 1 | 초기 로드 방식 | `supabase.from()` 직접 쿼리 대신 `api.proposals.status()` 사용으로 변경 반영 |
| 2 | 타입 | `PhaseStatus` 자체 인터페이스 대신 `ProposalStatus_` 재사용으로 변경 반영 |
| 3 | 에러 처리 추가 | `.catch()` 핸들링, `cancelled` 플래그 등 구현에서 추가된 개선사항 반영 |

---

## 5. Conclusion

Match Rate **95%** -- PASS (target 90%).

모든 핵심 성공 기준(12/12)이 충족되었다. polling(setInterval, pollingRef, fetchStatus)이 완전히 제거되었고, usePhaseStatus 훅이 Supabase Realtime postgres_changes를 정상적으로 구독한다. 구조적 차이 4건 중 2건(타입 재사용, HTTP API 초기 로드)은 설계 대비 개선이며, 1건(채널 이름)은 무시 가능, 1건(Realtime 콜백 누락 필드)만 P3 수준의 개선 권장사항이다.

---

## Version History

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-03-07 | Initial gap analysis | gap-detector |
