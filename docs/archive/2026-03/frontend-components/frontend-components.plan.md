# Plan: Frontend Components 분리 & Realtime 전환

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | frontend-components |
| 작성일 | 2026-03-07 |
| 기반 Plan | proposal-platform-v1.plan.md (아카이브) |
| 우선순위 | Medium |
| 선행 조건 | tenopa-proposer 백엔드 완료 (95%) |

---

## 1. 현황 분석

### 이미 구현된 것 (인라인)

갭 분석에서 "미구현"으로 분류했던 컴포넌트들은 실제로 **각 페이지에 인라인으로 이미 구현**되어 있음:

| 설계 컴포넌트 | 현재 위치 | 기능 상태 |
|-------------|---------|---------|
| PhaseProgress | `[id]/page.tsx` 인라인 | **동작 중** (3초 polling) |
| PhaseRetryButton | `[id]/page.tsx` 인라인 | **동작 중** |
| ResultViewer | `[id]/page.tsx` 인라인 | **동작 중** |
| CommentThread | `[id]/page.tsx` 인라인 | **동작 중** |
| FileUploadZone | `new/page.tsx` 인라인 | **동작 중** (드래그앤드롭, HWP 차단) |
| EmptyState | `proposals/page.tsx` 인라인 | **동작 중** |
| TeamInviteModal | `admin/page.tsx` 인라인 | **동작 중** |
| useProposals | `proposals/page.tsx` 인라인 | **동작 중** |

### 실제 갭

| 항목 | 설계 | 현재 구현 | 영향 |
|------|------|---------|------|
| usePhaseStatus.ts | Supabase Realtime WebSocket | 3초 polling interval | UX: 지연 없음, 서버 부하 소폭 증가 |
| 컴포넌트 파일 분리 | `/components/*.tsx` | 페이지 내 인라인 | 코드 재사용성, 유지보수성 |

---

## 2. 목표

### v1.1 목표 (이 사이클)

**Realtime 전환** (핵심):
- `lib/hooks/usePhaseStatus.ts` — Supabase Realtime WebSocket 구독
- `[id]/page.tsx` — polling → Realtime hook으로 교체

**선택적: 컴포넌트 분리** (코드 품질):
- YAGNI 검토: 현재 각 컴포넌트가 단 1곳에서만 사용 → 분리 효과 제한적
- 분리 여부는 Design 단계에서 결정

---

## 3. 사용자 의도

### 핵심 문제
1. **Realtime 지연**: 현재 polling(3초)은 설계 명세 위반. Supabase Realtime으로 즉시 업데이트 필요
2. **컴포넌트 재사용**: 향후 페이지 추가 시 인라인 코드 중복 발생 가능

### 성공 기준
- Phase 상태 변경 시 3초 이하 → 즉시(< 500ms) 반영
- Supabase Realtime 구독 해제 시 메모리 누수 없음
- 서버 재시작 후 Realtime 재연결 자동 처리

---

## 4. 기술 결정사항

| 결정 | 내용 | 이유 |
|------|------|------|
| Realtime 우선 | polling 제거, Realtime 전환 | 설계 명세 + 서버 부하 감소 |
| 컴포넌트 분리 보류 | 인라인 유지 (단일 사용처) | YAGNI — 실제 재사용 발생 시 분리 |
| usePhaseStatus hook | Supabase postgres_changes 구독 | [id]/page.tsx proposals UPDATE 이벤트 |

---

## 5. 작업 목록

### Phase A — Realtime 훅 구현
| 순서 | 파일 | 작업 |
|------|------|------|
| A1 | `frontend/lib/hooks/usePhaseStatus.ts` | Supabase Realtime 구독 훅 신규 구현 |
| A2 | `frontend/app/proposals/[id]/page.tsx` | polling 제거, usePhaseStatus 적용 |

### Phase B — (선택) useProposals 훅 분리
| 순서 | 파일 | 작업 |
|------|------|------|
| B1 | `frontend/lib/hooks/useProposals.ts` | 목록 fetch + 검색 + 페이지네이션 훅 분리 |
| B2 | `frontend/app/proposals/page.tsx` | 인라인 fetch 로직 → useProposals 적용 |

---

## 6. usePhaseStatus 설계

```typescript
// frontend/lib/hooks/usePhaseStatus.ts
import { useEffect, useState } from "react"
import { createClient } from "@/lib/supabase/client"

export interface PhaseStatus {
  status: string
  current_phase: string
  phases_completed: number
  failed_phase: string | null
  storage_upload_failed: boolean
}

export function usePhaseStatus(proposalId: string) {
  const [status, setStatus] = useState<PhaseStatus | null>(null)

  useEffect(() => {
    const supabase = createClient()

    // 초기 데이터 로드
    supabase
      .from("proposals")
      .select("status, current_phase, phases_completed, failed_phase, storage_upload_failed")
      .eq("id", proposalId)
      .single()
      .then(({ data }) => { if (data) setStatus(data) })

    // Realtime 구독
    const channel = supabase
      .channel(`proposal-${proposalId}`)
      .on("postgres_changes", {
        event: "UPDATE",
        schema: "public",
        table: "proposals",
        filter: `id=eq.${proposalId}`,
      }, (payload) => {
        setStatus(payload.new as PhaseStatus)
      })
      .subscribe()

    return () => { supabase.removeChannel(channel) }
  }, [proposalId])

  return status
}
```

---

## 7. 성공 기준

| 기준 | 검증 방법 |
|------|----------|
| Realtime 즉시 반영 | Phase 실행 중 current_phase 변경 → 500ms 이내 UI 갱신 |
| Realtime 구독 해제 | 페이지 이탈 시 채널 구독 해제 (DevTools Network 확인) |
| 메모리 누수 없음 | 10회 페이지 이동 후 WebSocket 연결 수 증가 없음 |
| polling 제거 | [id]/page.tsx에 setInterval 없음 |

---

## 8. 다음 단계

```
/pdca design frontend-components
```
