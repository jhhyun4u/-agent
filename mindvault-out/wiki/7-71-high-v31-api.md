# 7. 항목별 상세 갭 & 7.1 [HIGH] 레거시 v3.1 API 경로 혼용
Cohesion: 0.29 | Nodes: 7

## Key Nodes
- **7. 항목별 상세 갭** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-gaps\frontend.analysis.md) -- 6 connections
  - -> contains -> [[71-high-v31-api]]
  - -> contains -> [[72-high-3]]
  - -> contains -> [[73-high-azure-ad-sso]]
  - -> contains -> [[74-medium-api]]
  - -> contains -> [[75-medium-api]]
  - -> contains -> [[76-medium-gono-go]]
- **7.1 [HIGH] 레거시 v3.1 API 경로 혼용** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-gaps\frontend.analysis.md) -- 1 connections
  - <- contains <- [[7]]
- **7.2 [HIGH] 프로젝트 3가지 진입 경로 미구현** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-gaps\frontend.analysis.md) -- 1 connections
  - <- contains <- [[7]]
- **7.3 [HIGH] Azure AD SSO 미구현** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-gaps\frontend.analysis.md) -- 1 connections
  - <- contains <- [[7]]
- **7.4 [MEDIUM] 대시보드 역할별 API 미연동** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-gaps\frontend.analysis.md) -- 1 connections
  - <- contains <- [[7]]
- **7.5 [MEDIUM] 성과 추적 API 미연동** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-gaps\frontend.analysis.md) -- 1 connections
  - <- contains <- [[7]]
- **7.6 [MEDIUM] Go/No-Go 패널 상세 정보 부족** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-gaps\frontend.analysis.md) -- 1 connections
  - <- contains <- [[7]]

## Internal Relationships
- 7. 항목별 상세 갭 -> contains -> 7.1 [HIGH] 레거시 v3.1 API 경로 혼용 [EXTRACTED]
- 7. 항목별 상세 갭 -> contains -> 7.2 [HIGH] 프로젝트 3가지 진입 경로 미구현 [EXTRACTED]
- 7. 항목별 상세 갭 -> contains -> 7.3 [HIGH] Azure AD SSO 미구현 [EXTRACTED]
- 7. 항목별 상세 갭 -> contains -> 7.4 [MEDIUM] 대시보드 역할별 API 미연동 [EXTRACTED]
- 7. 항목별 상세 갭 -> contains -> 7.5 [MEDIUM] 성과 추적 API 미연동 [EXTRACTED]
- 7. 항목별 상세 갭 -> contains -> 7.6 [MEDIUM] Go/No-Go 패널 상세 정보 부족 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 7. 항목별 상세 갭, 7.1 [HIGH] 레거시 v3.1 API 경로 혼용, 7.2 [HIGH] 프로젝트 3가지 진입 경로 미구현를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 frontend.analysis.md이다.

### Key Facts
- 7.1 [HIGH] 레거시 v3.1 API 경로 혼용
- **현황**: `lib/api.ts`에서 `proposals.generate()`, `proposals.status()`, `proposals.result()`, 다운로드 URL이 모두 `/v3.1/` 프리픽스를 사용. 설계(SS12-1)는 `/api/proposals/*` 통합 경로.
- **현황**: 설계에서 정의한 3가지 프로젝트 생성 경로: 1. `POST /api/proposals` — 공고 검색(STEP 0)부터 시작 2. `POST /api/proposals/from-search` — 공고번호 직접 지정 3. `POST /api/proposals/from-rfp` — RFP 파일 업로드
- **현황**: 설계(SS12-6)에서는 Azure AD(Entra ID) SSO를 통한 MS365 환경 통합을 명시. 현재 구현은 Supabase Auth email/password.
- **현황**: 설계(SS12-8)에서 8개 역할별 대시보드 API를 정의했으나, 프론트엔드에서는 `stats.winRate(scope)` 1개만 호출. 나머지 7개 API 미연동.
