# Security Hardening Gap Analysis

> Date: 2026-03-20 | Match Rate: **43% → 65% → 83%** | Iterations: 2 | Status: P1 완료

## Overview

보안 감사 21건 (CRITICAL 2, HIGH 5, MEDIUM 8, LOW 6) 대비 현재 구현 상태 분석.
3회 반복(초기 + P0 + P1) 후 가중치 기준 83% 달성. 잔여는 외부 설정/인프라 의존.

## Score Summary (Iteration 2 후)

| Severity | Total | Fixed | Partial | Not Fixed | Score |
|----------|:-----:|:-----:|:-------:|:---------:|:-----:|
| CRITICAL | 2 | 2 | 0 | 0 | 100% |
| HIGH | 5 | 4 | 1 | 0 | 90% |
| MEDIUM | 8 | 5 | 3 | 0 | 81% |
| LOW | 6 | 3 | 0 | 3 | 50% |
| **Weighted** | **21** | **14** | **4** | **3** | **83%** |

## Finding Status (최종)

| ID | Severity | Finding | Status | Iteration |
|----|:--------:|---------|:------:|:---------:|
| C-1 | CRITICAL | .env secrets in git | FIXED | 기존 |
| C-2 | CRITICAL | RLS bypass | FIXED | P0 |
| H-1 | HIGH | Unauthenticated proposal CRUD | FIXED | P0 |
| H-2 | HIGH | Missing project access on workflow | FIXED | P0 |
| H-3 | HIGH | SSRF in rfp_parser | FIXED | P0 |
| H-4 | HIGH | No upload size limit | FIXED | P0 |
| H-5 | HIGH | CSRF with credentials | PARTIAL | 의도적 허용 (Bearer token) |
| M-1 | MEDIUM | Session timeout | PARTIAL | Supabase Auth 위임 |
| M-2 | MEDIUM | SQL injection | FIXED | 기존 |
| M-3 | MEDIUM | Log data leakage | PARTIAL | exc_info 서버전용 |
| M-4 | MEDIUM | Path traversal | FIXED | Iter 2 |
| M-5 | MEDIUM | Rate limit gaps | FIXED | Iter 2 |
| M-6 | MEDIUM | Artifact access control | FIXED | P0 |
| M-7 | MEDIUM | Resume data validation | PARTIAL | Pydantic 기본 검증 |
| M-8 | MEDIUM | Error detail exposure | FIXED | P0 + Iter 2 |
| L-1 | LOW | HSTS header | FIXED | Iter 2 |
| L-2 | LOW | Security headers | FIXED | Iter 2 |
| L-3 | LOW | API version exposure | FIXED | Iter 2 |
| L-4 | LOW | Password complexity | NOT_FIXED | Supabase Auth 외부 |
| L-5 | LOW | Audit tamper protection | NOT_FIXED | DB 마이그레이션 필요 |
| L-6 | LOW | Frontend error boundary | NOT_FIXED | 프론트엔드 별도 |

## Intentional Accepts (의도적 허용)

| ID | 사유 |
|----|------|
| H-5 | Bearer 토큰 인증 방식으로 CSRF 실질 위험 LOW. SameSite는 Supabase Auth 관리 |
| M-1 | session_timeout_minutes=30 설정. JWT 만료는 Supabase Auth가 관리 |
| M-3 | API 응답에서 제거 완료. 서버 로그의 exc_info는 운영 목적 |
| M-7 | Pydantic 타입 검증 + initial_state 화이트리스트 존재. 의미론적 enum은 미래 개선 |

## Deferred to Infrastructure

| ID | 필요 작업 |
|----|----------|
| L-4 | Supabase Dashboard → Auth → Password Policy 설정 |
| L-5 | DB 마이그레이션: `REVOKE DELETE ON audit_logs FROM authenticated` |
| L-6 | 프론트엔드 ErrorBoundary 컴포넌트 구현 |

## Changes Summary

### P0 (Iteration 1) — CRITICAL + HIGH 해소
- `app/api/deps.py`: `get_rls_client` 의존성 추가
- `app/api/routes_proposal.py`: `get_current_user` 교체, RLS 적용, 크기 검증
- `app/api/routes_workflow.py`: `require_project_access` 12개 엔드포인트
- `app/api/routes_artifacts.py`: `require_project_access` 9개 엔드포인트
- `app/services/rfp_parser.py`: `_validate_url` SSRF 방지
- `app/api/routes_g2b.py`: `str(e)` 제거

### Iteration 2 — MEDIUM + LOW Quick-Win
- `app/middleware/security_headers.py`: HSTS + 보안 헤더
- `app/api/routes_files.py`: 파일명 살균 + 크기 검증 + rate limit
- `app/main.py`: 프로덕션 docs 비활성화, 보안 헤더 미들웨어
- `app/api/routes_workflow.py`: SSE str(e) 제거, resume/abort/retry rate limit
