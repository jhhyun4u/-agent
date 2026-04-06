# deployment-infra Plan

> CI/CD 파이프라인 + docker-compose + 시크릿 관리 + 배포 문서화

- **Feature**: deployment-infra
- **Created**: 2026-03-22
- **Status**: Plan
- **Priority**: HIGH

---

## 1. 배경 및 동기

배포 준비 점검 결과 백엔드(96%)·프론트엔드(95%)는 프로덕션 수준이나, **인프라/DevOps 영역(60%)** 에 주요 갭이 존재한다.

| 갭 항목 | 심각도 | 현재 상태 |
|---------|--------|-----------|
| CI/CD 파이프라인 | CRITICAL | 미존재 |
| docker-compose.yml | HIGH | 미존재 |
| 시크릿 관리 | CRITICAL | .env 파일에 실제 키 노출 가능성 |
| 배포 문서 | HIGH | 로컬 개발만 문서화 |
| robots.txt | LOW | Disallow: / (프로덕션 SEO 차단) |

### 목표
- 인프라 준비도 60% → **95%** 이상으로 끌어올리기
- 첫 프로덕션 배포까지의 블로커 제거

---

## 2. 범위 (Scope)

### In-Scope

| ID | 항목 | 설명 |
|----|------|------|
| DI-01 | GitHub Actions CI | PR 시 lint + test + build 자동 검증 |
| DI-02 | GitHub Actions CD | main 머지 시 Backend(Railway) + Frontend(Vercel) 자동 배포 |
| DI-03 | docker-compose.yml | 로컬 통합 개발 환경 (backend + PostgreSQL + frontend) |
| DI-04 | 시크릿 점검 | git history 확인 + 키 로테이션 가이드 |
| DI-05 | 배포 문서 | README 프로덕션 섹션 + 배포 런북 |
| DI-06 | .env.production.example | 프로덕션 환경변수 템플릿 |

### Out-of-Scope
- Kubernetes/Terraform (현 규모에 불필요)
- 모니터링/알림 시스템 (별도 PDCA 사이클)
- CDN/캐시 전략 (별도)
- DB 백업 자동화 (Supabase 매니지드에서 제공)

---

## 3. 구현 항목 상세

### DI-01: GitHub Actions CI

**파일**: `.github/workflows/ci.yml`

**트리거**: PR → main, push → main

**잡 구성**:
```
jobs:
  backend-lint:    # ruff check
  backend-test:    # pytest (Supabase 불필요한 유닛 테스트)
  frontend-lint:   # next lint
  frontend-build:  # next build (TypeScript 타입 체크 포함)
```

**환경**:
- Python 3.11 + uv
- Node 20 + npm

**예상 소요**: 2~4분 (병렬 실행)

### DI-02: GitHub Actions CD

**파일**: `.github/workflows/deploy.yml`

**트리거**: push → main (CI 통과 후)

**백엔드 (Railway)**:
- Railway CLI 또는 GitHub integration으로 자동 배포
- Railway는 Dockerfile 감지하여 자동 빌드
- `RAILWAY_TOKEN` GitHub Secret 필요

**프론트엔드 (Vercel)**:
- Vercel GitHub integration으로 자동 배포 (별도 workflow 불필요)
- Vercel 프로젝트 설정에서 `frontend/` 루트 디렉토리 지정

### DI-03: docker-compose.yml

**파일**: `docker-compose.yml` (프로젝트 루트)

**서비스 구성**:
```yaml
services:
  backend:     # Dockerfile 기반, .env 마운트, 포트 8000
  postgres:    # postgres:16-alpine, 볼륨 영속화
  frontend:    # node:20-alpine, npm run dev, 포트 3000
```

**용도**: 로컬 통합 테스트 전용 (프로덕션은 Railway + Vercel + Supabase)

**주의**: Supabase 로컬 에뮬레이터 대신 단순 PostgreSQL 사용 (Auth/RLS 테스트는 Supabase 직접 연결)

### DI-04: 시크릿 점검

**체크리스트**:
1. `git log --all --diff-filter=A -- .env` 로 .env 커밋 이력 확인
2. `.env` 커밋 이력 존재 시 BFG Repo-Cleaner로 제거
3. 모든 API 키 로테이션 (Anthropic, Supabase, G2B)
4. GitHub Secrets에 프로덕션 키 등록

### DI-05: 배포 문서

**README.md 프로덕션 섹션 추가**:
- 프로덕션 환경변수 설정 가이드
- Railway/Vercel 배포 절차
- DB 마이그레이션 순서
- 헬스체크 확인 방법

### DI-06: .env.production.example

**파일**: `.env.production.example`

`.env.example`과 동일 구조 + 프로덕션 권장값:
- `LOG_FORMAT=json`
- `LOG_LEVEL=WARNING`
- `CORS_ORIGINS` 프로덕션 도메인
- `FRONTEND_URL` 프로덕션 URL

---

## 4. 구현 순서

```
DI-04 (시크릿 점검)          ← 최우선, 보안
  ↓
DI-06 (.env.production.example)  ← 간단, 빠른 완료
  ↓
DI-03 (docker-compose.yml)   ← 로컬 테스트 환경
  ↓
DI-01 (CI workflow)           ← 자동 검증
  ↓
DI-02 (CD workflow)           ← 자동 배포
  ↓
DI-05 (배포 문서)             ← 마무리 문서화
```

---

## 5. 기술 결정

| 결정 | 선택 | 이유 |
|------|------|------|
| CI/CD 도구 | GitHub Actions | 코드 저장소와 통합, 무료 티어 충분 |
| 백엔드 배포 | Railway | Dockerfile 자동 감지, 환경변수 UI, 무료 크레딧 |
| 프론트엔드 배포 | Vercel | Next.js 최적화, GitHub 자동 연동 |
| DB | Supabase (매니지드) | 이미 사용 중, 별도 인프라 불필요 |
| 로컬 DB | PostgreSQL 16 (docker) | 경량, Supabase 호환 |
| 시크릿 관리 | GitHub Secrets + 플랫폼 환경변수 | 현 규모에 적합, Vault 불필요 |

---

## 6. 리스크

| 리스크 | 영향 | 완화 |
|--------|------|------|
| .env 키 git history 노출 | HIGH | DI-04에서 즉시 점검 + 로테이션 |
| Railway 무료 크레딧 소진 | MEDIUM | 사용량 모니터링, 유료 전환 계획 |
| CI 시간 초과 | LOW | 병렬 잡 + 캐시 (uv cache, npm cache) |

---

## 7. 완료 기준

- [ ] `.env` git history에 시크릿 미포함 확인
- [ ] PR 시 CI 자동 실행 (lint + test + build)
- [ ] main 머지 시 Railway 자동 배포
- [ ] `docker-compose up`으로 로컬 통합 환경 기동
- [ ] README에 프로덕션 배포 가이드 포함
- [ ] `/health` 엔드포인트 프로덕션 응답 확인
