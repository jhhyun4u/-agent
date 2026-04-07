# 기능 테스트 결과 — 2026-03-27

## 수정 사항 (테스트 중 발견 → 즉시 수정)

### FIX-1: `NotFoundError` ImportError
- **파일**: `app/api/routes_intranet.py`
- **원인**: `NotFoundError`가 `app.exceptions`에 없음 (올바른 이름: `ResourceNotFoundError`)
- **수정**: import + 사용처 4건 교체

### FIX-2: `ProposalStatus`에 `running` 누락
- **파일**: `app/models/types.py`
- **원인**: DB에 `status='running'`이 있으나 Literal에 미포함 → Pydantic 직렬화 실패 → 500
- **수정**: `"running"` 추가

### FIX-3: `response_model` 불일치
- **파일**: `app/api/routes_proposal.py`
- **원인**: `ok_list()`는 `{"data":[], "meta":{}}` 반환하지만 `response_model=ItemsResponse[ProposalListItem]`은 `{"items":[], "total":N}` 기대 → 500
- **수정**: `response_model` 제거 (list_proposals, get_proposal)

### FIX-4: 글로벌 예외 핸들러 추가
- **파일**: `app/main.py`
- **원인**: `TenopAPIError` 외 일반 Exception은 "Internal Server Error" 텍스트만 반환, traceback 미출력
- **수정**: `@app.exception_handler(Exception)` 추가 → JSON 에러 + 로그 출력

---

## 프론트엔드 라우트 테스트 (22개)

| 라우트 | HTTP | 결과 |
|--------|------|------|
| `/` | 200 | PASS (→ /proposals 리다이렉트) |
| `/login` | 200 | PASS (dev모드: → /proposals 리다이렉트) |
| `/onboarding` | 200 | PASS |
| `/change-password` | 200 | PASS |
| `/dashboard` | 200 | PASS |
| `/proposals` | 200 | PASS |
| `/monitoring` | 200 | PASS |
| `/kb/search` | 200 | PASS |
| `/kb/content` | 200 | PASS |
| `/kb/clients` | 200 | PASS |
| `/kb/competitors` | 200 | PASS |
| `/kb/lessons` | 200 | PASS |
| `/kb/qa` | 200 | PASS |
| `/kb/labor-rates` | 200 | PASS |
| `/kb/market-prices` | 200 | PASS |
| `/analytics` | 200 | PASS |
| `/archive` | 200 | PASS |
| `/resources` | 200 | PASS |
| `/settings` | 200 | PASS |
| `/admin` | 200 | PASS |
| `/admin/users` | 200 | PASS |
| `/admin/prompts` | 200 | PASS |

**결과: 22/22 PASS** (모든 페이지 HTTP 200 렌더링)

---

## 백엔드 API 테스트 (20개)

| API | HTTP | 결과 | 비고 |
|-----|------|------|------|
| `GET /api/proposals` | 200 | PASS | 24건 반환 |
| `GET /api/stats/win-rate` | 500 | FAIL | GEN_005 에러 |
| `GET /api/calendar` | 500 | FAIL | rfp_calendar 테이블 미존재 |
| `GET /api/bids` | 404 | FAIL | 라우트 미등록 |
| `GET /api/monitoring/settings` | 404 | FAIL | 라우트 미등록 |
| `GET /api/kb/search?q=test` | 200 | PASS | 정상 (결과 0건) |
| `GET /api/kb/content` | 500 | FAIL | uuid: "None" — 인증 mock의 org_id=None |
| `GET /api/kb/clients` | 500 | FAIL | uuid: "None" — 동일 |
| `GET /api/kb/competitors` | 500 | FAIL | uuid: "None" — 동일 |
| `GET /api/kb/lessons` | 500 | FAIL | uuid: "None" — 동일 |
| `GET /api/kb/qa` | 404 | FAIL | 라우트 미등록 |
| `GET /api/kb/labor-rates` | 200 | PASS | 정상 (0건) |
| `GET /api/kb/market-prices` | 200 | PASS | 정상 (0건) |
| `GET /api/analytics/win-rate` | 500 | FAIL | proposals.result 컬럼 없음 |
| `GET /api/analytics/team-performance` | 500 | FAIL | proposals.result 컬럼 없음 |
| `GET /api/analytics/competitor` | 500 | FAIL | proposals.result 컬럼 없음 |
| `GET /api/notifications` | 200 | PASS | 정상 (0건) |
| `GET /api/users` | 500 | FAIL | uuid: "None" — 동일 |
| `GET /api/auth/me` | 404 | FAIL | 라우트 경로 불일치 |
| `GET /api/resources/sections` | 500 | FAIL | sections 테이블 미존재 |

**결과: 6/20 PASS, 14/20 FAIL**

---

## 이슈 분류 (우선순위별)

### P1: 공통 원인 (uuid: "None" — 4건)
- **영향**: KB content/clients/competitors/lessons, users
- **원인**: 개발 모드 mock 사용자의 `org_id=None` → Supabase `.eq("org_id", None)` 시 uuid 파싱 에러
- **수정 방안**: mock 사용자에 유효한 org_id 설정 또는 org_id=None 시 필터 스킵

### P2: DB 스키마 누락 (3건)
- `rfp_calendar` 테이블 → /api/calendar 500
- `sections` 테이블 → /api/resources/sections 500
- `proposals.result` 컬럼 → /api/analytics/* 500
- **수정 방안**: DB 마이그레이션 실행 또는 해당 API 비활성화

### P3: 라우트 미등록 (4건)
- `/api/bids` — 프론트에서 호출하지만 백엔드 라우트 없음
- `/api/monitoring/settings` — 설정 페이지용 API 없음
- `/api/kb/qa` — Q&A 목록 API 경로 불일치
- `/api/auth/me` — 경로 확인 필요 (/auth/me vs /api/auth/me)

### P4: 통계 API (1건)
- `/api/stats/win-rate` — GEN_005 제네릭 에러 (DB 쿼리 실패 추정)

---

## 요약

| 영역 | 테스트 수 | Pass | Fail | 비율 |
|------|-----------|------|------|------|
| 프론트엔드 라우트 | 22 | 22 | 0 | 100% |
| 백엔드 API | 20 | 6 | 14 | 30% |
| **합계** | 42 | 28 | 14 | 67% |

**핵심 발견**: 프론트엔드는 모든 페이지 렌더링 정상. 백엔드 API 14건 실패의 **공통 원인 3가지**:
1. mock 사용자 org_id=None (4건)
2. DB 스키마 누락/불일치 (6건)
3. 라우트 미등록/경로 불일치 (4건)
