# API 에러 마이그레이션 갭 분석

- **Feature**: api (HTTPException → TenopAPIError 마이그레이션)
- **분석일**: 2026-03-26
- **Match Rate**: 93%

## 1. 분석 범위

| 항목 | 값 |
|------|-----|
| 대상 디렉토리 | `app/api/routes_*.py`, `app/exceptions.py` |
| 검사 파일 수 | 24개 라우트 파일 + exceptions.py + main.py |
| 마이그레이션 대상 | HTTPException 155건 (15개 파일) |
| 신규 에러 클래스 | 16개 (TEAM 3, BID 2, G2B 2, FILE 2, GEN 7) |

## 2. 마이그레이션 완성도

| 검사 항목 | 결과 |
|-----------|------|
| `raise HTTPException` in `app/api/` | **0건** — PASS |
| `from fastapi import HTTPException` in `app/api/` | **0건** — PASS |
| `except HTTPException` in `app/api/` | **0건** — PASS |
| TenopAPIError handler (main.py) | **등록 확인** — PASS |
| HTTP status code 보존 | **전수 확인** — PASS |
| 구문 검증 (27 route files) | **전체 정상** — PASS |

**app/api/ 마이그레이션율: 100%**

## 3. 발견된 갭

### MEDIUM (개선 권장)

| ID | 파일 | 내용 | 영향 |
|----|------|------|------|
| GAP-1 | `routes_admin.py`, `routes_users.py` | `ADMIN_001` 코드가 7개 다른 에러에 재사용됨 (400 vs 422 혼용) | 에러 코드 의미 모호 |
| GAP-2 | `routes_admin.py:432` | `KB_001` 코드 충돌: 원래 의미(KB import validation)와 다른 용도(field not editable) | 코드 충돌 |
| GAP-3 | `routes_pricing.py` | `PRICING_001`, `PROPOSAL_001` 미등록 프리픽스 사용 | 컨벤션 불일치 |

### LOW (참고)

| ID | 파일 | 내용 |
|----|------|------|
| GAP-4 | `routes_auth.py` | `AUTH_005` 3가지 다른 의미 (400/403/500) |
| GAP-5 | `routes_admin.py` | `ADMIN_002` 인라인 사용 불일치 (400 vs 404) |
| GAP-6 | `app/middleware/auth.py` | 레거시 미들웨어에 HTTPException 2건 잔존 (deprecated 파일) |
| GAP-7 | 5개 라우트 파일 | `routes_notification`, `routes_analytics`, `routes_qa`, `routes_streams`, `routes_stats`에 에러 핸들링 없음 |

## 4. 권장 조치

1. **GAP-1**: `AdminValidationError(ADMIN_001, 422)` + `AdminInvalidInputError(ADMIN_006, 400)` 분리
2. **GAP-2**: `routes_admin.py:432`의 `KB_001` → `ADMIN_008` 등 별도 코드 사용
3. **GAP-3**: `PRICING_` 프리픽스 등록 또는 기존 `PROP_002`/`GEN_001`로 대체
4. **GAP-6**: 레거시 미들웨어 삭제 시 자동 해소 (낮은 우선순위)
5. **GAP-7**: 구현 시 try/except → InternalServiceError 래핑 고려

## 5. 결론

| 지표 | 값 |
|------|-----|
| **Match Rate** | **93%** |
| 마이그레이션 완성도 | 100% (app/api/) |
| HIGH 갭 | 0건 |
| MEDIUM 갭 | 3건 (에러 코드 충돌/불일치) |
| LOW 갭 | 4건 (레거시, 참고사항) |

마이그레이션 자체는 완벽히 완료. MEDIUM 갭은 기존 코드(`routes_admin.py`, `routes_pricing.py`)의 인라인 `TenopAPIError(...)` 사용 패턴에서 발생하며, 이번 마이그레이션 범위 밖의 기존 코드 문제.
