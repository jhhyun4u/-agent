# Plan: 관리자 페이지 개선 & 6. API 설계
Cohesion: 0.13 | Nodes: 17

## Key Nodes
- **Plan: 관리자 페이지 개선** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 8 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5]]
  - -> contains -> [[6-api]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
- **6. API 설계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 4 connections
  - -> contains -> [[a1-members-email]]
  - -> contains -> [[a2]]
  - -> contains -> [[a3]]
  - <- contains <- [[plan]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 3 connections
  - <- has_code_example <- [[a1-members-email]]
  - <- has_code_example <- [[a2]]
  - <- has_code_example <- [[a3]]
- **5. 작업 목록** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 3 connections
  - -> contains -> [[phase-a-p1p2]]
  - -> contains -> [[phase-b-p1p2]]
  - <- contains <- [[plan]]
- **1. 현황 분석** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 2 connections
  - -> contains -> [[ux]]
  - <- contains <- [[plan]]
- **2. 목표** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 2 connections
  - -> contains -> [[v11]]
  - <- contains <- [[plan]]
- **A1: members에 email 포함** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[6-api]]
- **A2: 팀 이름 수정** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[6-api]]
- **A3: 팀 통계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[6-api]]
- **3. 사용자 의도** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **4. 기술 결정사항** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **7. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **8. 다음 단계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 1 connections
  - <- contains <- [[plan]]
- **Phase A — 백엔드 (P1+P2)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **Phase B — 프론트엔드 (P1+P2)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 1 connections
  - <- contains <- [[5]]
- **실제 갭 (UX 문제)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 1 connections
  - <- contains <- [[1]]
- **v1.1 목표 (이 사이클)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.plan.md) -- 1 connections
  - <- contains <- [[2]]

## Internal Relationships
- 1. 현황 분석 -> contains -> 실제 갭 (UX 문제) [EXTRACTED]
- 2. 목표 -> contains -> v1.1 목표 (이 사이클) [EXTRACTED]
- 5. 작업 목록 -> contains -> Phase A — 백엔드 (P1+P2) [EXTRACTED]
- 5. 작업 목록 -> contains -> Phase B — 프론트엔드 (P1+P2) [EXTRACTED]
- 6. API 설계 -> contains -> A1: members에 email 포함 [EXTRACTED]
- 6. API 설계 -> contains -> A2: 팀 이름 수정 [EXTRACTED]
- 6. API 설계 -> contains -> A3: 팀 통계 [EXTRACTED]
- A1: members에 email 포함 -> has_code_example -> python [EXTRACTED]
- A2: 팀 이름 수정 -> has_code_example -> python [EXTRACTED]
- A3: 팀 통계 -> has_code_example -> python [EXTRACTED]
- Plan: 관리자 페이지 개선 -> contains -> 1. 현황 분석 [EXTRACTED]
- Plan: 관리자 페이지 개선 -> contains -> 2. 목표 [EXTRACTED]
- Plan: 관리자 페이지 개선 -> contains -> 3. 사용자 의도 [EXTRACTED]
- Plan: 관리자 페이지 개선 -> contains -> 4. 기술 결정사항 [EXTRACTED]
- Plan: 관리자 페이지 개선 -> contains -> 5. 작업 목록 [EXTRACTED]
- Plan: 관리자 페이지 개선 -> contains -> 6. API 설계 [EXTRACTED]
- Plan: 관리자 페이지 개선 -> contains -> 7. 성공 기준 [EXTRACTED]
- Plan: 관리자 페이지 개선 -> contains -> 8. 다음 단계 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Plan: 관리자 페이지 개선, 6. API 설계, python를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 admin-page.plan.md이다.

### Key Facts
- A1: members에 email 포함
- ```python routes_team.py @router.get("/teams/{team_id}/members") async def list_team_members(team_id: str, user=Depends(get_current_user)): # 기존: team_members 테이블만 조회 # 변경: service_role client로 auth.users email 병합 members = await client.table("team_members")... # auth.admin.list_users() 또는 profiles…
- Phase A — 백엔드 (P1+P2) | 순서 | 파일 | 작업 | |------|------|------| | A1 | `app/api/routes_team.py` | `GET /teams/{id}/members` 응답에 `email` 추가 (service_role 조회) | | A2 | `app/api/routes_team.py` | `PUT /teams/{id}` 팀 이름 수정 엔드포인트 추가 | | A3 | `app/api/routes_team.py` | `GET /teams/{id}/stats` 팀 통계 엔드포인트 추가…
- ```python routes_team.py @router.get("/teams/{team_id}/members") async def list_team_members(team_id: str, user=Depends(get_current_user)): # 기존: team_members 테이블만 조회 # 변경: service_role client로 auth.users email 병합 members = await client.table("team_members")... # auth.admin.list_users() 또는 profiles…
- ```python @router.put("/teams/{team_id}") async def update_team(team_id: str, body: TeamUpdate, user=Depends(get_current_user)): await _require_team_admin(client, team_id, user.id) await client.table("teams").update({"name": body.name}).eq("id", team_id).execute() return {"ok": True} ```
