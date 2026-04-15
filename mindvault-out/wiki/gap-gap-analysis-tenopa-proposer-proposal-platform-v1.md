# 섹션별 Gap 분석 & Gap Analysis: tenopa-proposer (proposal-platform-v1)
Cohesion: 0.22 | Nodes: 9

## Key Nodes
- **섹션별 Gap 분석** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\tenopa-proposer.analysis.md) -- 7 connections
  - -> contains -> [[1-95]]
  - -> contains -> [[2-db-phaseexecutor-96]]
  - -> contains -> [[3-storage-88]]
  - -> contains -> [[4-98]]
  - -> contains -> [[5-api-edge-functions-90]]
  - -> contains -> [[p2-minor]]
  - <- contains <- [[gap-analysis-tenopa-proposer-proposal-platform-v1]]
- **Gap Analysis: tenopa-proposer (proposal-platform-v1)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\tenopa-proposer.analysis.md) -- 2 connections
  - -> contains -> [[gap]]
  - -> contains -> [[match-rate]]
- **1. 아키텍처/인프라 (95%)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\tenopa-proposer.analysis.md) -- 1 connections
  - <- contains <- [[gap]]
- **2. DB 스키마 / phase_executor (96%)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\tenopa-proposer.analysis.md) -- 1 connections
  - <- contains <- [[gap]]
- **3. Storage (88%)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\tenopa-proposer.analysis.md) -- 1 connections
  - <- contains <- [[gap]]
- **4. 프론트엔드 (98%)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\tenopa-proposer.analysis.md) -- 1 connections
  - <- contains <- [[gap]]
- **5. 팀 협업 API / Edge Functions (90%)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\tenopa-proposer.analysis.md) -- 1 connections
  - <- contains <- [[gap]]
- **Match Rate 계산** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\tenopa-proposer.analysis.md) -- 1 connections
  - <- contains <- [[gap-analysis-tenopa-proposer-proposal-platform-v1]]
- **P2 — Minor (확인 필요)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\tenopa-proposer\tenopa-proposer.analysis.md) -- 1 connections
  - <- contains <- [[gap]]

## Internal Relationships
- 섹션별 Gap 분석 -> contains -> 1. 아키텍처/인프라 (95%) [EXTRACTED]
- 섹션별 Gap 분석 -> contains -> 2. DB 스키마 / phase_executor (96%) [EXTRACTED]
- 섹션별 Gap 분석 -> contains -> 3. Storage (88%) [EXTRACTED]
- 섹션별 Gap 분석 -> contains -> 4. 프론트엔드 (98%) [EXTRACTED]
- 섹션별 Gap 분석 -> contains -> 5. 팀 협업 API / Edge Functions (90%) [EXTRACTED]
- 섹션별 Gap 분석 -> contains -> P2 — Minor (확인 필요) [EXTRACTED]
- Gap Analysis: tenopa-proposer (proposal-platform-v1) -> contains -> 섹션별 Gap 분석 [EXTRACTED]
- Gap Analysis: tenopa-proposer (proposal-platform-v1) -> contains -> Match Rate 계산 [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 섹션별 Gap 분석, Gap Analysis: tenopa-proposer (proposal-platform-v1), 1. 아키텍처/인프라 (95%)를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 tenopa-proposer.analysis.md이다.

### Key Facts
- | 항목 | 설계 | 구현 | 상태 | |------|------|------|------| | FastAPI 라우터 (v3.1, team, g2b) | 3개 라우터 | 구현 완료 | ✅ | | JWT 인증 (get_current_user) | Bearer 검증 | app/middleware/auth.py | ✅ | | UUID4 proposal_id | uuid.uuid4() | routes_v31.py | ✅ | | CORS (settings.cors_origins) | 환경변수 연동 | 구현 완료 | ✅ | |…
- | 항목 | 설계 | 구현 | 상태 | |------|------|------|------| | proposal_phases 컬럼명 | phase_num, artifact_json | phase_num, artifact_json | ✅ | | proposals.status CHECK | "running" | "running" | ✅ | | proposals.failed_phase | INTEGER | phase_num(int) 직접 전달 | ✅ | | _update_status async | DB 업데이트 | bg_task…
- | 항목 | 설계 | 구현 | 상태 | |------|------|------|------| | storage_upload_failed 업데이트 | BOOLEAN 플래그 | 구현 완료 | ✅ | | 서명 URL 다운로드 | create_signed_url | routes_v31.py | ✅ | | 버킷명 | "proposals" | "proposal-files" | ❌ G4 | | HWPX Storage 업로드 | 설계 미명시 (추가) | 구현됨 | ✅ |
- | 항목 | 설계 | 구현 | 상태 | |------|------|------|------| | 전체 페이지 | 9개 페이지 | 구현 완료 | ✅ | | middleware.ts | @supabase/ssr | 구현 완료 | ✅ | | usePhaseStatus 훅 | Realtime 구독 | 구현 완료 | ✅ | | useProposals 훅 | SWR + 페이지네이션 | 구현 완료 | ✅ | | lib/api.ts 401 처리 | signOut + redirect | 구현 완료 | ✅ |
- | 항목 | 설계 | 구현 | 상태 | |------|------|------|------| | 팀 CRUD | 전체 | routes_team.py | ✅ | | 초대 upsert 흐름 | on_conflict 갱신 | 구현 완료 | ✅ | | proposal-complete | 완료 이메일 | 구현 완료 | ✅ | | comment-notify | team_id NULL 처리 | 구현 완료 | ✅ |
