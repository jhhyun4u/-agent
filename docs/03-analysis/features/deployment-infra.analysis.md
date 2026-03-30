# deployment-infra Gap Analysis

- **Feature**: deployment-infra
- **Analysis Date**: 2026-03-22
- **Plan**: `docs/01-plan/features/deployment-infra.plan.md`
- **Match Rate**: 97% → **100% (수정 후)**

---

## 항목별 비교

| ID | Plan 항목 | 구현 상태 | Match |
|----|-----------|-----------|:-----:|
| DI-01 | GitHub Actions CI (lint+test+build) | `.github/workflows/ci.yml` — 3 jobs 병렬 | 100% |
| DI-02 | GitHub Actions CD (Railway) | `.github/workflows/deploy.yml` — CI→deploy chain | 100% |
| DI-03 | docker-compose.yml | `docker-compose.yml` — backend+postgres+frontend | 100% |
| DI-04 | 시크릿 점검 | git history 확인 완료, .env 미커밋 | 100% |
| DI-05 | README 프로덕션 가이드 | README.md 전면 개편 (아키텍처+배포+환경변수) | 100% |
| DI-06 | .env.production.example | 41줄, LOG_FORMAT=json, LOG_LEVEL=WARNING | 100% |

## 발견된 갭 (2건, 모두 수정 완료)

| GAP | 심각도 | 설명 | 조치 |
|-----|--------|------|------|
| GAP-1 | MEDIUM | CI에서 ruff 대신 ast.parse만 사용 | ruff check 추가 + pyproject.toml에 ruff dev dep 추가 |
| GAP-2 | LOW | uv cache 미설정 | `enable-cache: true` 추가 (backend-lint, backend-test) |

## 수정 내역

1. `.github/workflows/ci.yml`: `py_compile` → `ruff check app/` 교체, `enable-cache: true` 추가
2. `pyproject.toml`: `[dependency-groups] dev`에 `ruff>=0.8.0` 추가

## 최종 Match Rate: **100%**

모든 Plan 항목이 구현되고 갭이 해소됨.
