# Plan: 관리자 페이지 개선

## 메타 정보

| 항목 | 내용 |
|------|------|
| Feature | admin-page |
| 작성일 | 2026-03-07 |
| 우선순위 | Medium |
| 선행 조건 | 팀 API 완료 (routes_team.py) |

---

## 1. 현황 분석

### 이미 구현된 것

| 기능 | 파일 | 상태 |
|------|------|------|
| 팀 목록 사이드바 | `admin/page.tsx` 인라인 | 동작 중 |
| 팀 생성 | `admin/page.tsx` 인라인 | 동작 중 |
| 팀원 목록 + 역할 변경 | `admin/page.tsx` 인라인 | 동작 중 (user_id 표시) |
| 팀원 제거 | `admin/page.tsx` 인라인 | 동작 중 |
| 이메일 초대 | `admin/page.tsx` 인라인 | 동작 중 |
| 초대 목록 + 취소 | `admin/page.tsx` 인라인 | 동작 중 |

### 실제 갭 (UX 문제)

| 항목 | 현재 | 목표 | 우선순위 |
|------|------|------|---------|
| 팀원 식별 | `user_id` (UUID) 표시 | 이메일 표시 | P1 |
| 팀 설정 | 없음 | 팀 이름 수정 | P2 |
| 팀 통계 | 없음 | 제안서 수 · 수주율 | P2 |
| 팀 삭제 | 없음 | admin만 가능 | P3 |

---

## 2. 목표

### v1.1 목표 (이 사이클)

**P1 — UX 필수 수정**:
- 팀원 표시를 `user_id` → `email` 로 개선
  - 백엔드: `GET /team/teams/{team_id}/members` 응답에 `email` 필드 포함
  - 프론트: 멤버 아바타에 이메일 두 글자 이니셜 표시

**P2 — 팀 설정 추가**:
- 팀 이름 수정 (admin 전용)
- 팀 통계 섹션: 팀 제안서 수, 완료/실패/진행 중 카운트

**P3 — (선택) 팀 삭제**:
- YAGNI: 사용 빈도 낮음, 이번 사이클에서 보류

---

## 3. 사용자 의도

### 핵심 문제
1. **멤버 식별 불가**: UUID만 보여서 누가 누군지 알 수 없음 → 이메일 표시 필수
2. **팀 관리 미완성**: 팀 이름 변경 불가, 팀 성과 파악 불가

### 성공 기준
- 팀원 목록에서 이메일로 멤버 식별 가능
- admin이 팀 이름을 수정할 수 있음
- 팀별 제안서 통계 확인 가능

---

## 4. 기술 결정사항

| 결정 | 내용 | 이유 |
|------|------|------|
| 이메일 노출 방식 | `auth.users` 직접 조회 불가 → `/team/teams/{id}/members`에 `email` 포함 | Supabase service_role로 auth.users 조회 |
| 팀 이름 수정 | `PATCH /team/teams/{id}` — 이미 `TeamUpdate` 스키마 존재 | routes_team.py에 PUT 엔드포인트 추가 필요 |
| 팀 통계 | `GET /team/teams/{id}/stats` 신규 엔드포인트 | proposals 테이블 집계 쿼리 |

---

## 5. 작업 목록

### Phase A — 백엔드 (P1+P2)
| 순서 | 파일 | 작업 |
|------|------|------|
| A1 | `app/api/routes_team.py` | `GET /teams/{id}/members` 응답에 `email` 추가 (service_role 조회) |
| A2 | `app/api/routes_team.py` | `PUT /teams/{id}` 팀 이름 수정 엔드포인트 추가 |
| A3 | `app/api/routes_team.py` | `GET /teams/{id}/stats` 팀 통계 엔드포인트 추가 |

### Phase B — 프론트엔드 (P1+P2)
| 순서 | 파일 | 작업 |
|------|------|------|
| B1 | `frontend/lib/api.ts` | `TeamMember.email` 필드 추가, `teams.stats()` 메서드 추가, `teams.update()` 메서드 추가 |
| B2 | `frontend/app/admin/page.tsx` | 팀원 표시를 user_id → email 이니셜 + 이메일 텍스트로 교체 |
| B3 | `frontend/app/admin/page.tsx` | 팀 이름 수정 UI (admin 전용 인라인 편집) 추가 |
| B4 | `frontend/app/admin/page.tsx` | 팀 통계 섹션 추가 (제안서 수, 수주율) |

---

## 6. API 설계

### A1: members에 email 포함

```python
# routes_team.py
@router.get("/teams/{team_id}/members")
async def list_team_members(team_id: str, user=Depends(get_current_user)):
    # 기존: team_members 테이블만 조회
    # 변경: service_role client로 auth.users email 병합
    members = await client.table("team_members")...
    # auth.admin.list_users() 또는 profiles 테이블 참조
    return {"members": [..., {"email": "..."}]}
```

### A2: 팀 이름 수정

```python
@router.put("/teams/{team_id}")
async def update_team(team_id: str, body: TeamUpdate, user=Depends(get_current_user)):
    await _require_team_admin(client, team_id, user.id)
    await client.table("teams").update({"name": body.name}).eq("id", team_id).execute()
    return {"ok": True}
```

### A3: 팀 통계

```python
@router.get("/teams/{team_id}/stats")
async def get_team_stats(team_id: str, user=Depends(get_current_user)):
    await _require_team_member(client, team_id, user.id)
    # proposals WHERE team_id = team_id GROUP BY status
    return {
        "total": int,
        "completed": int,
        "processing": int,
        "failed": int,
        "won": int,      # win_result = "won"
        "win_rate": float,
    }
```

---

## 7. 성공 기준

| 기준 | 검증 방법 |
|------|----------|
| 이메일 표시 | 팀원 목록에서 UUID 대신 이메일 확인 |
| 팀 이름 수정 | admin이 팀 이름 클릭 → 편집 → 저장 동작 |
| 팀 통계 | 통계 섹션에서 제안서 수 · 수주율 표시 |
| 권한 보호 | member는 팀 이름 수정 UI 미노출 |

---

## 8. 다음 단계

```
/pdca design admin-page
```
