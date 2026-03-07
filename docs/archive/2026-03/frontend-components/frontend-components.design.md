# Design: Frontend Components — Realtime 전환

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | frontend-components |
| 작성일 | 2026-03-07 |
| 기반 Plan | docs/01-plan/features/frontend-components.plan.md |
| 범위 | Supabase Realtime 전환 + (선택) useProposals 훅 분리 |

---

## 1. 변경 범위

### 변경 대상 파일

| 파일 | 변경 유형 | 내용 |
|------|---------|------|
| `frontend/lib/hooks/usePhaseStatus.ts` | 신규 | Supabase Realtime 구독 훅 |
| `frontend/app/proposals/[id]/page.tsx` | 수정 | polling → usePhaseStatus 교체 |

### 변경 없는 파일 (YAGNI)

| 파일 | 이유 |
|------|------|
| `frontend/lib/hooks/useProposals.ts` | proposals/page.tsx의 fetch 로직이 단순하고 1곳에서만 사용 |
| `frontend/components/*.tsx` | 모든 컴포넌트가 이미 인라인으로 동작 중, 분리 효과 없음 |

---

## 2. 현재 구현 (변경 전)

### `[id]/page.tsx` 현재 polling 패턴

```typescript
// 현재: 3초 interval polling
const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

const fetchStatus = useCallback(async () => {
  const s = await api.proposals.status(id);
  setStatus(s);
  if (s.status === "completed" || s.status === "failed") {
    if (pollingRef.current) clearInterval(pollingRef.current);
  }
}, [id]);

useEffect(() => {
  fetchStatus();
  pollingRef.current = setInterval(fetchStatus, 3000);  // ← 교체 대상
  return () => { if (pollingRef.current) clearInterval(pollingRef.current); };
}, [fetchStatus, fetchComments]);

async function handleRetry() {
  await api.proposals.execute(id);
  fetchStatus();
  pollingRef.current = setInterval(fetchStatus, 3000);  // ← 교체 대상
}
```

**문제점**:
- 3초마다 API 호출 → 불필요한 서버 부하
- Phase 완료 시 최대 3초 지연
- 탭 백그라운드에서도 polling 계속 실행

---

## 3. 설계 (변경 후)

### 3.1 usePhaseStatus 훅

```typescript
// frontend/lib/hooks/usePhaseStatus.ts
"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

export interface PhaseStatus {
  id: string;
  status: string;
  current_phase: string;
  phases_completed: number;
  failed_phase: string | null;
  storage_upload_failed: boolean;
  rfp_title: string;
  client_name: string;
  error?: string;
}

export function usePhaseStatus(proposalId: string) {
  const [status, setStatus] = useState<PhaseStatus | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!proposalId) return;
    const supabase = createClient();

    // 1. 초기 데이터 로드 (HTTP)
    supabase
      .from("proposals")
      .select("id, status, current_phase, phases_completed, failed_phase, storage_upload_failed, title, notes")
      .eq("id", proposalId)
      .single()
      .then(({ data }) => {
        if (data) {
          setStatus({
            id: data.id,
            status: data.status,
            current_phase: data.current_phase,
            phases_completed: data.phases_completed,
            failed_phase: data.failed_phase,
            storage_upload_failed: data.storage_upload_failed,
            rfp_title: data.title,
            client_name: "",  // proposals 테이블에 없음 — 세션에서 가져와야 함
            error: data.notes,
          });
        }
        setLoading(false);
      });

    // 2. Realtime 구독 (WebSocket)
    // proposals 테이블: REPLICA IDENTITY FULL 설정 완료 (schema.sql)
    const channel = supabase
      .channel(`proposal-${proposalId}`)
      .on(
        "postgres_changes",
        {
          event: "UPDATE",
          schema: "public",
          table: "proposals",
          filter: `id=eq.${proposalId}`,
        },
        (payload) => {
          const row = payload.new as Record<string, unknown>;
          setStatus((prev) => prev ? {
            ...prev,
            status: row.status as string,
            current_phase: row.current_phase as string,
            phases_completed: row.phases_completed as number,
            failed_phase: row.failed_phase as string | null,
            storage_upload_failed: row.storage_upload_failed as boolean,
            error: row.notes as string | undefined,
          } : null);
        }
      )
      .subscribe();

    // 3. 클린업: 페이지 이탈 시 채널 구독 해제
    return () => {
      supabase.removeChannel(channel);
    };
  }, [proposalId]);

  return { status, loading };
}
```

### 3.2 `[id]/page.tsx` 변경 사항

**제거**:
```typescript
// 삭제 대상
const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
const [status, setStatus] = useState<ProposalStatus_ | null>(null);
const fetchStatus = useCallback(async () => { ... }, [id]);

// useEffect 내 polling 코드
pollingRef.current = setInterval(fetchStatus, 3000);

// handleRetry 내 polling 재시작
pollingRef.current = setInterval(fetchStatus, 3000);
```

**추가**:
```typescript
import { usePhaseStatus } from "@/lib/hooks/usePhaseStatus";

// polling 대체
const { status, loading } = usePhaseStatus(id);

// handleRetry — polling 재시작 불필요, Realtime이 자동으로 받음
async function handleRetry() {
  await api.proposals.execute(id);
  // Realtime이 DB 변경을 자동 감지하므로 별도 refresh 불필요
}
```

**유지**:
```typescript
// comments는 Realtime 대상 아님 — fetchComments 유지
const [comments, setComments] = useState<Comment_[]>([]);
const fetchComments = useCallback(async () => { ... }, [id]);

useEffect(() => {
  fetchComments();
}, [fetchComments]);
```

---

## 4. 의존성 확인

### Supabase Realtime 전제 조건

| 조건 | 상태 | 위치 |
|------|------|------|
| `REPLICA IDENTITY FULL` on proposals | 완료 | schema.sql line 142 |
| Supabase Dashboard Replication 활성화 | 수동 작업 필요 | Dashboard > Database > Replication |
| `@supabase/ssr` createBrowserClient | 완료 | lib/supabase/client.ts |
| `NEXT_PUBLIC_SUPABASE_URL` | 완료 | .env.local |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | 완료 | .env.local |

> **주의**: Supabase Dashboard에서 proposals 테이블 Replication을 수동으로 활성화해야 Realtime이 동작함.
> `Dashboard > Database > Replication > proposals 테이블 토글 ON`

### ProposalStatus_ 타입 확인

현재 `api.ts`의 `ProposalStatus_` 타입이 `usePhaseStatus` 반환 타입과 호환되어야 함.
변경 후 `status` 상태를 `api.ts` 타입 대신 `PhaseStatus` 타입으로 직접 사용.

---

## 5. 엣지 케이스

| 케이스 | 처리 방법 |
|-------|---------|
| Realtime 연결 실패 | 초기 HTTP 로드는 성공 → status 표시됨. Realtime만 없으면 UI 멈춤 → polling 폴백 고려 |
| 완료/실패 이후 재구독 | completed/failed 시 removeChannel 불필요 (이벤트가 와도 무시) |
| 탭 전환 | visibilitychange 이벤트 없음 — Supabase SDK가 백그라운드에서도 WebSocket 유지 |
| 서버 재시작 | Supabase Realtime은 별도 인프라 — 백엔드 재시작과 무관 |
| 다중 탭 | 각 탭이 독립 채널 구독 — 중복 이벤트 없음 |

### Realtime 연결 실패 폴백 (선택 구현)

```typescript
// channel.subscribe() 콜백으로 상태 체크
const channel = supabase
  .channel(`proposal-${proposalId}`)
  .on("postgres_changes", ..., handler)
  .subscribe((status) => {
    if (status === "CHANNEL_ERROR" || status === "TIMED_OUT") {
      // 폴백: 30초마다 1회 HTTP 폴링으로 전환
      console.warn("Realtime 연결 실패 — 폴백 polling 시작");
    }
  });
```

> v1에서는 폴백 생략 가능. Supabase Realtime 안정성은 높음.

---

## 6. 구현 순서

```
Step 1: usePhaseStatus.ts 신규 파일 작성
  → frontend/lib/hooks/ 디렉토리 생성
  → usePhaseStatus.ts 구현

Step 2: [id]/page.tsx 수정
  → pollingRef, setInterval 제거
  → fetchStatus useCallback 제거 (또는 manual refresh용으로 유지)
  → usePhaseStatus import + 적용
  → handleRetry에서 polling 재시작 코드 제거

Step 3: 타입 정합성 확인
  → PhaseStatus 타입과 기존 ProposalStatus_ 타입 비교
  → 필요 시 api.ts ProposalStatus_ 타입 통일

Step 4: Supabase Dashboard 설정 확인
  → proposals 테이블 Replication ON 여부 확인
  → 로컬 개발: docker 환경에서 Realtime 활성화 여부 확인
```

---

## 7. 파일 변경 전체 요약

| 파일 | 유형 | 핵심 변경 |
|------|------|---------|
| `frontend/lib/hooks/usePhaseStatus.ts` | 신규 | Supabase Realtime 구독 + 초기 HTTP 로드 |
| `frontend/app/proposals/[id]/page.tsx` | 수정 | polling 제거, usePhaseStatus 적용 |

---

## 8. 성공 기준

| 기준 | 검증 방법 |
|------|----------|
| Realtime 즉시 반영 | Phase 실행 중 current_phase 변경 → 500ms 이내 UI 갱신 |
| polling 제거 | Network 탭에서 3초 간격 API 호출 없음 |
| 채널 구독 해제 | 페이지 이탈 시 DevTools > Network > WS 연결 종료 확인 |
| 재시도 동작 | 실패 후 재시도 버튼 → Phase 상태 Realtime으로 갱신 |
| 로딩 상태 | loading=true 동안 스피너 표시 |

---

## 9. 다음 단계

```
/pdca do frontend-components
```
