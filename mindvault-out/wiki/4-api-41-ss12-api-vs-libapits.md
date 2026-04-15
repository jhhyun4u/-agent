# 4. API 연동 비교 & 4.1 SS12 API vs `lib/api.ts` 클라이언트
Cohesion: 0.67 | Nodes: 3

## Key Nodes
- **4. API 연동 비교** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-gaps\frontend.analysis.md) -- 2 connections
  - -> contains -> [[41-ss12-api-vs-libapits]]
  - -> contains -> [[42-api]]
- **4.1 SS12 API vs `lib/api.ts` 클라이언트** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-gaps\frontend.analysis.md) -- 1 connections
  - <- contains <- [[4-api]]
- **4.2 API 경로 불일치** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\frontend-gaps\frontend.analysis.md) -- 1 connections
  - <- contains <- [[4-api]]

## Internal Relationships
- 4. API 연동 비교 -> contains -> 4.1 SS12 API vs `lib/api.ts` 클라이언트 [EXTRACTED]
- 4. API 연동 비교 -> contains -> 4.2 API 경로 불일치 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 4. API 연동 비교, 4.1 SS12 API vs `lib/api.ts` 클라이언트, 4.2 API 경로 불일치를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 frontend.analysis.md이다.

### Key Facts
- 4.1 SS12 API vs `lib/api.ts` 클라이언트
- | API 그룹 | 설계 | 구현 | 일치율 | 누락/차이 | |----------|:----:|:----:|:------:|-----------| | SS12-1 워크플로 제어 | 12개 | 10개 | 83% | `POST /proposals/from-rfp`, `POST /proposals/from-search` 미구현 (레거시 `/v3.1/proposals/generate`로 대체) | | SS12-2 resume 다형성 | 10종 | 구현 | 90% | `WorkflowResumeData` 타입이 모든 케이스 포괄.…
- | 항목 | 설계 | 구현 | 영향 | |------|------|------|------| | 프로젝트 생성 | `POST /api/proposals` | `POST /api/v3.1/proposals/generate` | HIGH - 레거시 v3.1 API 사용 중 | | 제안서 상태 | `GET /api/proposals/{id}/state` | `GET /api/v3.1/proposals/{id}/status` | HIGH - 레거시 API 경로 | | 제안서 결과 | (artifacts API) | `GET…
