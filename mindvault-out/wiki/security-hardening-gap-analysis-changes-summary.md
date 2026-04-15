# Security Hardening Gap Analysis & Changes Summary
Cohesion: 0.22 | Nodes: 9

## Key Nodes
- **Security Hardening Gap Analysis** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\security-hardening\security-hardening.analysis.md) -- 6 connections
  - -> contains -> [[overview]]
  - -> contains -> [[score-summary-iteration-2]]
  - -> contains -> [[finding-status]]
  - -> contains -> [[intentional-accepts]]
  - -> contains -> [[deferred-to-infrastructure]]
  - -> contains -> [[changes-summary]]
- **Changes Summary** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\security-hardening\security-hardening.analysis.md) -- 3 connections
  - -> contains -> [[p0-iteration-1-critical-high]]
  - -> contains -> [[iteration-2-medium-low-quick-win]]
  - <- contains <- [[security-hardening-gap-analysis]]
- **Deferred to Infrastructure** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\security-hardening\security-hardening.analysis.md) -- 1 connections
  - <- contains <- [[security-hardening-gap-analysis]]
- **Finding Status (최종)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\security-hardening\security-hardening.analysis.md) -- 1 connections
  - <- contains <- [[security-hardening-gap-analysis]]
- **Intentional Accepts (의도적 허용)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\security-hardening\security-hardening.analysis.md) -- 1 connections
  - <- contains <- [[security-hardening-gap-analysis]]
- **Iteration 2 — MEDIUM + LOW Quick-Win** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\security-hardening\security-hardening.analysis.md) -- 1 connections
  - <- contains <- [[changes-summary]]
- **Overview** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\security-hardening\security-hardening.analysis.md) -- 1 connections
  - <- contains <- [[security-hardening-gap-analysis]]
- **P0 (Iteration 1) — CRITICAL + HIGH 해소** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\security-hardening\security-hardening.analysis.md) -- 1 connections
  - <- contains <- [[changes-summary]]
- **Score Summary (Iteration 2 후)** (C:\project\tenopa proposer\-agent-master\docs\archive\2026-03\security-hardening\security-hardening.analysis.md) -- 1 connections
  - <- contains <- [[security-hardening-gap-analysis]]

## Internal Relationships
- Changes Summary -> contains -> P0 (Iteration 1) — CRITICAL + HIGH 해소 [EXTRACTED]
- Changes Summary -> contains -> Iteration 2 — MEDIUM + LOW Quick-Win [EXTRACTED]
- Security Hardening Gap Analysis -> contains -> Overview [EXTRACTED]
- Security Hardening Gap Analysis -> contains -> Score Summary (Iteration 2 후) [EXTRACTED]
- Security Hardening Gap Analysis -> contains -> Finding Status (최종) [EXTRACTED]
- Security Hardening Gap Analysis -> contains -> Intentional Accepts (의도적 허용) [EXTRACTED]
- Security Hardening Gap Analysis -> contains -> Deferred to Infrastructure [EXTRACTED]
- Security Hardening Gap Analysis -> contains -> Changes Summary [EXTRACTED]

## Cross-Community Connections

## Context
이 커뮤니티는 Security Hardening Gap Analysis, Changes Summary, Deferred to Infrastructure를 중심으로 contains 관계로 연결되어 있다. 주요 소스 파일은 security-hardening.analysis.md이다.

### Key Facts
- > Date: 2026-03-20 | Match Rate: **43% → 65% → 83%** | Iterations: 2 | Status: P1 완료
- P0 (Iteration 1) — CRITICAL + HIGH 해소 - `app/api/deps.py`: `get_rls_client` 의존성 추가 - `app/api/routes_proposal.py`: `get_current_user` 교체, RLS 적용, 크기 검증 - `app/api/routes_workflow.py`: `require_project_access` 12개 엔드포인트 - `app/api/routes_artifacts.py`: `require_project_access` 9개 엔드포인트 -…
- | ID | 필요 작업 | |----|----------| | L-4 | Supabase Dashboard → Auth → Password Policy 설정 | | L-5 | DB 마이그레이션: `REVOKE DELETE ON audit_logs FROM authenticated` | | L-6 | 프론트엔드 ErrorBoundary 컴포넌트 구현 |
- | ID | Severity | Finding | Status | Iteration | |----|:--------:|---------|:------:|:---------:| | C-1 | CRITICAL | .env secrets in git | FIXED | 기존 | | C-2 | CRITICAL | RLS bypass | FIXED | P0 | | H-1 | HIGH | Unauthenticated proposal CRUD | FIXED | P0 | | H-2 | HIGH | Missing project access on…
- | ID | 사유 | |----|------| | H-5 | Bearer 토큰 인증 방식으로 CSRF 실질 위험 LOW. SameSite는 Supabase Auth 관리 | | M-1 | session_timeout_minutes=30 설정. JWT 만료는 Supabase Auth가 관리 | | M-3 | API 응답에서 제거 완료. 서버 로그의 exc_info는 운영 목적 | | M-7 | Pydantic 타입 검증 + initial_state 화이트리스트 존재. 의미론적 enum은 미래 개선 |
