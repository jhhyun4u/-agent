# Design: 관리자 페이지 개선 & 3. 설계 (변경 후)
Cohesion: 0.11 | Nodes: 22

## Key Nodes
- **Design: 관리자 페이지 개선** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 8 connections
  - -> contains -> [[1]]
  - -> contains -> [[2]]
  - -> contains -> [[3]]
  - -> contains -> [[4]]
  - -> contains -> [[5-getserviceclient]]
  - -> contains -> [[6]]
  - -> contains -> [[7]]
  - -> contains -> [[8]]
- **3. 설계 (변경 후)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 5 connections
  - -> contains -> [[31-email]]
  - -> contains -> [[32]]
  - -> contains -> [[33-apits]]
  - -> contains -> [[34-adminpagetsx]]
  - <- contains <- [[design]]
- **typescript** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 4 connections
  - <- has_code_example <- [[33-apits]]
  - <- has_code_example <- [[a-email-p1]]
  - <- has_code_example <- [[b-ui-p2-admin-only]]
  - <- has_code_example <- [[c-p2]]
- **1. 현황 분석 (코드 기반)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 4 connections
  - -> contains -> [[routesteampy]]
  - -> contains -> [[libapits]]
  - -> contains -> [[adminpagetsx]]
  - <- contains <- [[design]]
- **3.4 프론트엔드: admin/page.tsx 변경** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 4 connections
  - -> contains -> [[a-email-p1]]
  - -> contains -> [[b-ui-p2-admin-only]]
  - -> contains -> [[c-p2]]
  - <- contains <- [[3]]
- **python** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 3 connections
  - <- has_code_example <- [[31-email]]
  - <- has_code_example <- [[32]]
  - <- has_code_example <- [[5-getserviceclient]]
- **2. 변경 범위** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 2 connections
  - -> contains -> [[yagni]]
  - <- contains <- [[design]]
- **3.1 백엔드: email 포함 멤버 목록** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[3]]
- **3.2 백엔드: 팀 통계 엔드포인트** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[3]]
- **3.3 프론트엔드: api.ts 타입 + 메서드 추가** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[3]]
- **5. get_service_client 유틸 확인 필요** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 2 connections
  - -> has_code_example -> [[python]]
  - <- contains <- [[design]]
- **A. 팀원 email 표시 (P1)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[34-adminpagetsx]]
- **B. 팀 이름 수정 UI (P2, admin only)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[34-adminpagetsx]]
- **C. 팀 통계 섹션 (P2)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 2 connections
  - -> has_code_example -> [[typescript]]
  - <- contains <- [[34-adminpagetsx]]
- **4. 엣지 케이스** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 1 connections
  - <- contains <- [[design]]
- **6. 구현 순서** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 1 connections
  - <- contains <- [[design]]
- **7. 성공 기준** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 1 connections
  - <- contains <- [[design]]
- **8. 다음 단계** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 1 connections
  - <- contains <- [[design]]
- **프론트엔드 (`admin/page.tsx`)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 1 connections
  - <- contains <- [[1]]
- **프론트엔드 (`lib/api.ts`)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 1 connections
  - <- contains <- [[1]]
- **백엔드 (`routes_team.py`)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 1 connections
  - <- contains <- [[1]]
- **변경 없는 파일 (YAGNI)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\admin-page\admin-page.design.md) -- 1 connections
  - <- contains <- [[2]]

## Internal Relationships
- 1. 현황 분석 (코드 기반) -> contains -> 백엔드 (`routes_team.py`) [EXTRACTED]
- 1. 현황 분석 (코드 기반) -> contains -> 프론트엔드 (`lib/api.ts`) [EXTRACTED]
- 1. 현황 분석 (코드 기반) -> contains -> 프론트엔드 (`admin/page.tsx`) [EXTRACTED]
- 2. 변경 범위 -> contains -> 변경 없는 파일 (YAGNI) [EXTRACTED]
- 3. 설계 (변경 후) -> contains -> 3.1 백엔드: email 포함 멤버 목록 [EXTRACTED]
- 3. 설계 (변경 후) -> contains -> 3.2 백엔드: 팀 통계 엔드포인트 [EXTRACTED]
- 3. 설계 (변경 후) -> contains -> 3.3 프론트엔드: api.ts 타입 + 메서드 추가 [EXTRACTED]
- 3. 설계 (변경 후) -> contains -> 3.4 프론트엔드: admin/page.tsx 변경 [EXTRACTED]
- 3.1 백엔드: email 포함 멤버 목록 -> has_code_example -> python [EXTRACTED]
- 3.2 백엔드: 팀 통계 엔드포인트 -> has_code_example -> python [EXTRACTED]
- 3.3 프론트엔드: api.ts 타입 + 메서드 추가 -> has_code_example -> typescript [EXTRACTED]
- 3.4 프론트엔드: admin/page.tsx 변경 -> contains -> A. 팀원 email 표시 (P1) [EXTRACTED]
- 3.4 프론트엔드: admin/page.tsx 변경 -> contains -> B. 팀 이름 수정 UI (P2, admin only) [EXTRACTED]
- 3.4 프론트엔드: admin/page.tsx 변경 -> contains -> C. 팀 통계 섹션 (P2) [EXTRACTED]
- 5. get_service_client 유틸 확인 필요 -> has_code_example -> python [EXTRACTED]
- A. 팀원 email 표시 (P1) -> has_code_example -> typescript [EXTRACTED]
- B. 팀 이름 수정 UI (P2, admin only) -> has_code_example -> typescript [EXTRACTED]
- C. 팀 통계 섹션 (P2) -> has_code_example -> typescript [EXTRACTED]
- Design: 관리자 페이지 개선 -> contains -> 1. 현황 분석 (코드 기반) [EXTRACTED]
- Design: 관리자 페이지 개선 -> contains -> 2. 변경 범위 [EXTRACTED]
- Design: 관리자 페이지 개선 -> contains -> 3. 설계 (변경 후) [EXTRACTED]
- Design: 관리자 페이지 개선 -> contains -> 4. 엣지 케이스 [EXTRACTED]
- Design: 관리자 페이지 개선 -> contains -> 5. get_service_client 유틸 확인 필요 [EXTRACTED]
- Design: 관리자 페이지 개선 -> contains -> 6. 구현 순서 [EXTRACTED]
- Design: 관리자 페이지 개선 -> contains -> 7. 성공 기준 [EXTRACTED]
- Design: 관리자 페이지 개선 -> contains -> 8. 다음 단계 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Design: 관리자 페이지 개선, 3. 설계 (변경 후), typescript를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 admin-page.design.md이다.

### Key Facts
- 3.1 백엔드: email 포함 멤버 목록
- ```typescript // TeamMember 타입에 email 추가 export interface TeamMember { id: string; team_id: string; user_id: string; email: string;        // ← 추가 role: string; joined_at: string; }
- 백엔드 (`routes_team.py`)
- ```python app/api/routes_team.py @router.get("/teams/{team_id}/members") async def list_team_members(team_id: str, user=Depends(get_current_user)): """팀원 목록 (email 포함)""" client = await get_async_client() await _require_team_member(client, team_id, user.id)
- **문제**: `team_members` 테이블에는 `user_id` (UUID)만 있고 email은 `auth.users` 테이블에 있음. Supabase anon client는 `auth.users` 직접 조회 불가.
