# 9. 관리자 `/admin` (admin/manager 역할만) & 9-1. 이용자 관리 `/admin/users`
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **9. 관리자 `/admin` (admin/manager 역할만)** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 4 connections
  - -> contains -> [[9-1-adminusers]]
  - -> contains -> [[9-2-admin]]
  - -> contains -> [[9-3-adminprompts]]
  - -> contains -> [[9-4]]
- **9-1. 이용자 관리 `/admin/users`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[9-admin-adminmanager]]
- **9-2. 조직도 `/admin`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[9-admin-adminmanager]]
- **9-3. 프롬프트 관리 `/admin/prompts`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[9-admin-adminmanager]]
- **9-4. 권한 체크** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[9-admin-adminmanager]]

## Internal Relationships
- 9. 관리자 `/admin` (admin/manager 역할만) -> contains -> 9-1. 이용자 관리 `/admin/users` [EXTRACTED]
- 9. 관리자 `/admin` (admin/manager 역할만) -> contains -> 9-2. 조직도 `/admin` [EXTRACTED]
- 9. 관리자 `/admin` (admin/manager 역할만) -> contains -> 9-3. 프롬프트 관리 `/admin/prompts` [EXTRACTED]
- 9. 관리자 `/admin` (admin/manager 역할만) -> contains -> 9-4. 권한 체크 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 9. 관리자 `/admin` (admin/manager 역할만), 9-1. 이용자 관리 `/admin/users`, 9-2. 조직도 `/admin`를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 frontend-manual-test-checklist.md이다.

### Key Facts
- 9-1. 이용자 관리 `/admin/users` - [ ] 사용자 목록 테이블 - [ ] 역할 변경 (admin/manager/user) - [ ] 사용자 초대 기능 - [ ] 비활성화/삭제
- 9-2. 조직도 `/admin` - [ ] AdminOrgChart 렌더링 - [ ] 조직/본부/팀 계층 표시 - [ ] 편집 동작
- 9-3. 프롬프트 관리 `/admin/prompts` - [ ] 프롬프트 목록 표시 - [ ] 카탈로그 `/admin/prompts/catalog` - [ ] 프롬프트 상세 `/admin/prompts/[promptId]` - [ ] 프롬프트 개선 `/admin/prompts/[promptId]/improve` - [ ] 프롬프트 시뮬레이션 `/admin/prompts/[promptId]/simulate` - [ ] A/B 실험 `/admin/prompts/experiments`
- 9-4. 권한 체크 - [ ] 일반 사용자(user)로 `/admin` 접근 시 접근 거부 또는 메뉴 미표시
