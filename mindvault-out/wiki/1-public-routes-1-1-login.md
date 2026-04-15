# 1. 인증 (Public Routes) & 1-1. 로그인 `/login`
Cohesion: 0.40 | Nodes: 5

## Key Nodes
- **1. 인증 (Public Routes)** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 4 connections
  - -> contains -> [[1-1-login]]
  - -> contains -> [[1-2-onboarding]]
  - -> contains -> [[1-3-change-password]]
  - -> contains -> [[1-4-invitationsaccept]]
- **1-1. 로그인 `/login`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[1-public-routes]]
- **1-2. 온보딩 `/onboarding`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[1-public-routes]]
- **1-3. 비밀번호 변경 `/change-password`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[1-public-routes]]
- **1-4. 초대 수락 `/invitations/accept`** (C:\project\tenopa proposer\-agent-master\docs\05-test\frontend-manual-test-checklist.md) -- 1 connections
  - <- contains <- [[1-public-routes]]

## Internal Relationships
- 1. 인증 (Public Routes) -> contains -> 1-1. 로그인 `/login` [EXTRACTED]
- 1. 인증 (Public Routes) -> contains -> 1-2. 온보딩 `/onboarding` [EXTRACTED]
- 1. 인증 (Public Routes) -> contains -> 1-3. 비밀번호 변경 `/change-password` [EXTRACTED]
- 1. 인증 (Public Routes) -> contains -> 1-4. 초대 수락 `/invitations/accept` [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 1. 인증 (Public Routes), 1-1. 로그인 `/login`, 1-2. 온보딩 `/onboarding`를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 frontend-manual-test-checklist.md이다.

### Key Facts
- 1-1. 로그인 `/login` - [ ] 페이지 정상 렌더링 - [ ] 이메일/비밀번호 입력 필드 표시 - [ ] 빈 값 제출 시 유효성 검증 메시지 - [ ] 잘못된 자격증명 → 에러 메시지 표시 - [ ] 정상 로그인 → `/dashboard` 리다이렉트 - [ ] 로그인 상태에서 `/login` 접근 시 대시보드로 리다이렉트
- 1-2. 온보딩 `/onboarding` - [ ] 신규 사용자 첫 로그인 시 온보딩 페이지 표시 - [ ] 온보딩 완료 후 대시보드 이동
- 1-3. 비밀번호 변경 `/change-password` - [ ] 페이지 정상 렌더링 - [ ] 현재/새 비밀번호 입력 필드 - [ ] 비밀번호 불일치 시 에러 표시
- 1-4. 초대 수락 `/invitations/accept` - [ ] 초대 토큰 포함 URL 접근 시 수락 UI 표시
