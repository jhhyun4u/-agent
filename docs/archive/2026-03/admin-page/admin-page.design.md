# Design: 관리자 페이지 개선

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | admin-page |
| 작성일 | 2026-03-07 |
| 기반 Plan | docs/01-plan/features/admin-page.plan.md |
| 범위 | P1 email 표시 + P2 팀 이름 수정 UI + P2 팀 통계 |

---

## 1. 현황 분석 (코드 기반)

### 백엔드 (`routes_team.py`)

| 엔드포인트 | 상태 | 비고 |
|-----------|------|------|
| `GET /teams/me` | 완료 | team_members + teams 조인 |
| `POST /teams` | 완료 | |
| `PATCH /teams/{id}` | **완료** | admin only — UI만 없음 |
| `DELETE /teams/{id}` | 완료 | admin only |
| `GET /teams/{id}/members` | 완료이지만 **email 없음** | `team_members.*` 만 반환 |
| `GET /teams/{id}/stats` | **없음** | 신규 추가 필요 |

### 프론트엔드 (`lib/api.ts`)

| 항목 | 상태 | 비고 |
|------|------|------|
| `TeamMember.email` 필드 | **없음** | 타입 추가 필요 |
| `api.teams.update()` | **완료** | `PATCH /teams/{id}` 호출 |
| `api.teams.stats()` | **없음** | 신규 메서드 필요 |

### 프론트엔드 (`admin/page.tsx`)

| 항목 | 상태 | 문제 |
|------|------|------|
| 팀원 식별자 | `m.user_id` (UUID) 표시 | 누구인지 알 수 없음 |
| 아바타 이니셜 | `m.user_id.slice(0,2)` | 무의미한 UUID 두 글자 |
| 팀 이름 수정 UI | **없음** | 백엔드는 준비됨 |
| 팀 통계 섹션 | **없음** | 백엔드 + 프론트 모두 필요 |

---

## 2. 변경 범위

### 변경 대상 파일

| 파일 | 변경 유형 | 내용 |
|------|---------|------|
| `app/api/routes_team.py` | 수정 | `GET /teams/{id}/members`에 email 포함, `GET /teams/{id}/stats` 추가 |
| `frontend/lib/api.ts` | 수정 | `TeamMember.email` 타입 추가, `api.teams.stats()` 추가 |
| `frontend/app/admin/page.tsx` | 수정 | email 표시, 팀 이름 편집 UI, 통계 섹션 |

### 변경 없는 파일 (YAGNI)

| 파일 | 이유 |
|------|------|
| `supabase/schema.sql` | DB 스키마 변경 없음 — auth.users는 기존 테이블 |
| `app/middleware/auth.py` | 인증 로직 변경 없음 |

---

## 3. 설계 (변경 후)

### 3.1 백엔드: email 포함 멤버 목록

**문제**: `team_members` 테이블에는 `user_id` (UUID)만 있고 email은 `auth.users` 테이블에 있음.
Supabase anon client는 `auth.users` 직접 조회 불가.

**해결**: `get_async_client(service_role=True)` 또는 `auth.admin.list_users()` 사용.

```python
# app/api/routes_team.py
@router.get("/teams/{team_id}/members")
async def list_team_members(team_id: str, user=Depends(get_current_user)):
    """팀원 목록 (email 포함)"""
    client = await get_async_client()
    await _require_team_member(client, team_id, user.id)

    res = (
        await client.table("team_members")
        .select("*")
        .eq("team_id", team_id)
        .execute()
    )
    members = res.data or []

    # auth.users에서 email 조회 (service_role 필요)
    user_ids = [m["user_id"] for m in members]
    email_map: dict[str, str] = {}
    try:
        from app.utils.supabase_client import get_service_client
        admin_client = get_service_client()
        for uid in user_ids:
            user_res = admin_client.auth.admin.get_user_by_id(uid)
            if user_res.user:
                email_map[uid] = user_res.user.email or ""
    except Exception:
        pass  # email 조회 실패 시 user_id로 폴백

    for m in members:
        m["email"] = email_map.get(m["user_id"], "")

    return {"members": members}
```

> **대안 (profiles 테이블 없을 경우)**: `auth.admin.list_users()`로 전체 조회 후 필터.
> Supabase Python SDK v2: `client.auth.admin.list_users()` 지원.

### 3.2 백엔드: 팀 통계 엔드포인트

```python
@router.get("/teams/{team_id}/stats")
async def get_team_stats(team_id: str, user=Depends(get_current_user)):
    """팀 제안서 통계 (member 이상)"""
    client = await get_async_client()
    await _require_team_member(client, team_id, user.id)

    res = (
        await client.table("proposals")
        .select("status, win_result")
        .eq("team_id", team_id)
        .execute()
    )
    proposals = res.data or []

    total = len(proposals)
    completed = sum(1 for p in proposals if p["status"] == "completed")
    processing = sum(1 for p in proposals if p["status"] in ("processing", "initialized"))
    failed = sum(1 for p in proposals if p["status"] == "failed")
    won = sum(1 for p in proposals if p.get("win_result") == "won")
    win_rate = round(won / completed * 100, 1) if completed > 0 else 0.0

    return {
        "total": total,
        "completed": completed,
        "processing": processing,
        "failed": failed,
        "won": won,
        "win_rate": win_rate,
    }
```

### 3.3 프론트엔드: api.ts 타입 + 메서드 추가

```typescript
// TeamMember 타입에 email 추가
export interface TeamMember {
  id: string;
  team_id: string;
  user_id: string;
  email: string;        // ← 추가
  role: string;
  joined_at: string;
}

// TeamStats 타입 신규
export interface TeamStats {
  total: number;
  completed: number;
  processing: number;
  failed: number;
  won: number;
  win_rate: number;
}

// api.teams에 stats() 추가
teams: {
  // ...기존...
  stats(teamId: string) {
    return request<TeamStats>("GET", `/teams/${teamId}/stats`);
  },
}
```

### 3.4 프론트엔드: admin/page.tsx 변경

#### A. 팀원 email 표시 (P1)

```typescript
// 변경 전
<div className="w-8 h-8 rounded-full bg-gray-200 ...">
  {m.user_id.slice(0, 2).toUpperCase()}
</div>
<span>{m.user_id}</span>

// 변경 후
<div className="w-8 h-8 rounded-full bg-gray-200 ...">
  {(m.email || m.user_id).slice(0, 2).toUpperCase()}
</div>
<span>{m.email || m.user_id}</span>
```

#### B. 팀 이름 수정 UI (P2, admin only)

```typescript
// 상태 추가
const [editingName, setEditingName] = useState(false);
const [teamNameInput, setTeamNameInput] = useState("");

// handleRenameTeam 추가
async function handleRenameTeam(e: React.FormEvent) {
  e.preventDefault();
  if (!selectedTeamId || !teamNameInput.trim()) return;
  try {
    await api.teams.update(selectedTeamId, teamNameInput.trim());
    await fetchTeams();
    setEditingName(false);
    flash("팀 이름이 변경되었습니다.");
  } catch (err: unknown) {
    setError(err instanceof Error ? err.message : "이름 변경 실패");
  }
}

// 팀 상세 헤더에 인라인 편집 UI
{isAdmin && editingName ? (
  <form onSubmit={handleRenameTeam} className="flex gap-2">
    <input value={teamNameInput} onChange={...} className="..." />
    <button type="submit">저장</button>
    <button type="button" onClick={() => setEditingName(false)}>취소</button>
  </form>
) : (
  <h2>{selectedMembership?.teams.name}
    {isAdmin && (
      <button onClick={() => { setTeamNameInput(selectedMembership?.teams.name ?? ""); setEditingName(true); }}
        className="ml-2 text-xs text-gray-400 hover:text-gray-600">수정</button>
    )}
  </h2>
)}
```

#### C. 팀 통계 섹션 (P2)

```typescript
// 상태 추가
const [stats, setStats] = useState<TeamStats | null>(null);

// fetchTeamDetail에 stats 추가
const [memRes, invRes, statsRes] = await Promise.all([
  api.teams.members.list(selectedTeamId),
  api.teams.invitations.list(selectedTeamId).catch(() => ({ invitations: [] })),
  api.teams.stats(selectedTeamId).catch(() => null),
]);
setStats(statsRes);

// UI (팀원 섹션 위에 배치)
{stats && (
  <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
    <h2 className="font-semibold text-gray-900 mb-4">팀 통계</h2>
    <div className="grid grid-cols-3 gap-4 text-center">
      <div><p className="text-2xl font-bold text-gray-900">{stats.total}</p><p className="text-xs text-gray-500">전체 제안서</p></div>
      <div><p className="text-2xl font-bold text-green-600">{stats.completed}</p><p className="text-xs text-gray-500">완료</p></div>
      <div><p className="text-2xl font-bold text-blue-600">{stats.win_rate}%</p><p className="text-xs text-gray-500">수주율</p></div>
    </div>
  </div>
)}
```

---

## 4. 엣지 케이스

| 케이스 | 처리 |
|--------|------|
| auth.admin API 미지원 환경 | `email_map` 빈 dict → `user_id` 폴백 (graceful degradation) |
| 팀 제안서 0개 | `stats.total = 0`, `win_rate = 0.0` |
| member가 팀 이름 수정 시도 | 백엔드 403, 프론트 isAdmin 체크로 UI 미노출 |
| 팀 이름 빈 문자열 | 버튼 disabled 처리 |
| stats API 실패 | `.catch(() => null)` → stats 섹션 미표시 |

---

## 5. get_service_client 유틸 확인 필요

`get_async_client()`가 service_role인지 anon인지 확인 후:
- **anon key**: `auth.admin` API 사용 불가 → `get_service_client()` 별도 구현 필요
- **service_role key**: 직접 `client.auth.admin.get_user_by_id()` 호출 가능

```python
# app/utils/supabase_client.py에 추가 필요 (anon인 경우)
def get_service_client():
    from supabase import create_client
    import os
    return create_client(
        os.environ["SUPABASE_URL"],
        os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    )
```

---

## 6. 구현 순서

```
Step 1: app/utils/supabase_client.py — service client 확인/추가
Step 2: app/api/routes_team.py — list_team_members에 email 포함
Step 3: app/api/routes_team.py — get_team_stats 추가
Step 4: frontend/lib/api.ts — TeamMember.email, TeamStats 타입, stats() 메서드
Step 5: frontend/app/admin/page.tsx — email 표시 교체
Step 6: frontend/app/admin/page.tsx — 팀 이름 수정 UI
Step 7: frontend/app/admin/page.tsx — 통계 섹션 추가
```

---

## 7. 성공 기준

| 기준 | 검증 |
|------|------|
| 팀원 목록에서 이메일 표시 | UUID 대신 실제 이메일 확인 |
| auth.admin 실패 시 폴백 | user_id로 대체 표시 (에러 없음) |
| admin이 팀 이름 수정 | 수정 → 저장 → 사이드바 갱신 |
| member는 수정 UI 미노출 | isAdmin=false 시 수정 버튼 없음 |
| 팀 통계 표시 | 제안서 수 · 수주율 정확히 집계 |
| stats API 실패 시 | 통계 섹션 미표시 (에러 없음) |

---

## 8. 다음 단계

```
/pdca do admin-page
```
