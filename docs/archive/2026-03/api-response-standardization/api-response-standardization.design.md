# Design: API 응답 구조 표준화

> **Feature**: api-response-standardization
> **Version**: 1.0
> **Date**: 2026-03-26
> **Status**: Design
> **Plan**: [api-response-standardization.plan.md](../../01-plan/features/api-response-standardization.plan.md)

---

## 1. 표준 응답 스키마

### 1.1 성공 응답 (단건)

```json
{
  "data": { "id": "abc", "title": "..." },
  "meta": { "timestamp": "2026-03-26T12:00:00Z" }
}
```

### 1.2 성공 응답 (리스트 + 페이지네이션)

```json
{
  "data": [ {...}, {...} ],
  "meta": {
    "total": 100,
    "offset": 0,
    "limit": 20,
    "timestamp": "2026-03-26T12:00:00Z"
  }
}
```

### 1.3 성공 응답 (작업 완료, 데이터 없음)

```json
{
  "data": null,
  "meta": { "message": "삭제되었습니다.", "timestamp": "2026-03-26T12:00:00Z" }
}
```

### 1.4 에러 응답 (변경 없음)

기존 `TenopAPIError` 구조 유지:
```json
{
  "error_code": "SECT_001",
  "message": "섹션이 다른 사용자에 의해 잠겨 있습니다.",
  "detail": { "locked_by": "user-123" }
}
```

### 1.5 설계 원칙

| 원칙 | 설명 |
|------|------|
| `data` 키 통일 | 단건/리스트 모두 `data` — `items`, `results` 등 제거 |
| `meta` 분리 | 페이지네이션/타임스탬프/메시지를 `meta`로 분리 |
| `status` 필드 없음 | HTTP status code로 충분. 에러는 `error_code` 유무로 구분 |
| 하위 호환 기간 없음 | 프론트엔드를 동시 수정하므로 즉시 전환 |
| 예외 보존 | SSE, FileResponse, G2B 프록시, v31 레거시는 현행 유지 |

---

## 2. Backend — 표준 래퍼 모듈

### 2.1 `app/api/response.py` (신규)

```python
"""표준 API 응답 래퍼.

모든 엔드포인트는 이 모듈의 함수를 통해 응답을 반환한다.
"""

from datetime import datetime, timezone
from typing import Any


def ok(data: Any, *, message: str | None = None) -> dict:
    """단건 성공 응답.

    Usage:
        return ok({"id": "abc", "title": "..."})
        return ok(None, message="삭제되었습니다.")
    """
    meta: dict[str, Any] = {"timestamp": _now()}
    if message:
        meta["message"] = message
    return {"data": data, "meta": meta}


def ok_list(
    items: list,
    *,
    total: int,
    offset: int = 0,
    limit: int = 20,
) -> dict:
    """리스트 성공 응답 (페이지네이션 포함).

    Usage:
        return ok_list(result.data, total=count, offset=offset, limit=limit)
    """
    return {
        "data": items,
        "meta": {
            "total": total,
            "offset": offset,
            "limit": limit,
            "timestamp": _now(),
        },
    }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")
```

**설계 결정**: Pydantic `ApiResponse[T]` Generic 모델은 만들지 않는다.

- 이유 1: 기존 엔드포인트 대부분이 raw dict를 반환하며 `response_model`을 쓰지 않음. 전부 Pydantic화하면 변경량이 3배 증가.
- 이유 2: `ok()` / `ok_list()` 함수면 구조 통일에 충분. OpenAPI 스키마는 Phase 2에서 점진 적용.
- 이유 3: 기존 `response_model` 사용 파일(6개)은 반환 후 미들웨어에서 래핑하거나 개별 교체.

### 2.2 기존 `response_model` 처리 전략

6개 파일(routes_users, routes_streams, routes_submission_docs, routes_stats, routes_proposal, routes_bids)이 이미 `response_model`을 사용 중.

**전략**: `response_model` 제거 → `ok()`로 래핑.

```python
# Before (routes_users.py)
@router.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, ...):
    ...
    return user_data

# After
@router.get("/api/users/{user_id}")
async def get_user(user_id: str, ...):
    ...
    return ok(user_data)
```

이유: `response_model`과 `ok()` 래핑을 동시 사용하면 이중 직렬화/필터링 문제 발생. 단일 패턴으로 통일.

---

## 3. 라우트별 변환 명세

### 3.1 그룹 1 — 핵심 CRUD (8파일)

#### routes_proposal.py

| 엔드포인트 | 현재 반환 | 변환 |
|-----------|----------|------|
| `POST /proposals` | `{"proposal_id", "title", "mode", "entry_point"}` | `ok({...})` |
| `POST /from-rfp` | `{"proposal_id", "title", "mode", "entry_point"}` | `ok({...})` |
| `POST /from-bid` | `{"proposal_id", "title", ...}` | `ok({...})` |
| `GET /proposals` | `{"items": [...], "total": N}` | `ok_list(items, total=N)` |
| `GET /proposals/{id}` | `{proposal 객체}` | `ok(proposal)` |
| `DELETE /proposals/{id}` | `{"deleted": True}` | `ok(None, message="삭제되었습니다.")` |

#### routes_workflow.py

| 엔드포인트 | 현재 반환 | 변환 |
|-----------|----------|------|
| `POST /start` | `{"proposal_id", "thread_id", "next_step"}` | `ok({...})` |
| `GET /state` | `{"proposal_id", "current_step", "sections", ...}` | `ok({...})` |
| `POST /resume` | `{"proposal_id", "result", "next_step"}` | `ok({...})` |
| `GET /history` | `{"proposal_id", "history": [...]}` | `ok({"proposal_id", "history"})` |
| `POST /goto` | `{"proposal_id", "restored_step", ...}` | `ok({...})` |
| `GET /locks` | `{"locks": [...]}` | `ok({"locks": [...]})` |
| `POST /release-lock` | `{"released": True}` | `ok(None, message="잠금이 해제되었습니다.")` |
| `GET /impact` | `{"proposal_id", "impact": {...}}` | `ok({...})` |
| `POST /retry` | `{...}` | `ok({...})` |
| `GET /ai-logs` | `{"proposal_id", "logs": [...]}` | `ok({"proposal_id", "logs"})` |
| `GET /stream` (SSE) | EventSourceResponse | **예외 — 변환 안 함** |

#### routes_artifacts.py

| 엔드포인트 | 현재 반환 | 변환 |
|-----------|----------|------|
| `GET /{step}` | `{"step", "artifact"}` | `ok({...})` |
| `PUT /{step}` | `{"saved": True, "updated_at"}` | `ok({...})` |
| `GET /diff` | `{"diff", "versions"}` | `ok({...})` |
| `POST /regenerate` | `{"regenerated": True, "section_id", ...}` | `ok({...})` |
| `POST /ai-assist` | `{"suggestion", "mode"}` | `ok({...})` |
| `GET /compliance` | `{matrix}` | `ok(matrix)` |
| `POST /compliance/check` | `{"checked", "issues"}` | `ok({...})` |
| `GET /download/docx` | FileResponse | **예외** |
| `GET /download/hwpx` | FileResponse | **예외** |

#### routes_bids.py

| 패턴 | 현재 | 변환 |
|------|------|------|
| 리스트 | `{"data": [...]}` | `ok_list(items, total=N)` |
| 단건 | `{"data": {...}}` | `ok(item)` — `data` 언래핑 후 재래핑 |
| 작업 | `{"status": "ok", "queued": N}` | `ok({"queued": N}, message="큐에 추가됨")` |
| 페이지 | `{"data": [...], "meta": {"total", "page"}}` | `ok_list(items, total=N, offset=...)` |

#### routes_kb.py

| 패턴 | 현재 | 변환 |
|------|------|------|
| 리스트 | `{"items": [...], "total": N}` | `ok_list(items, total=N)` |
| 검색 | `{"query", "total", "results": [...]}` | `ok_list(results, total=N)` — `query`는 meta 확장 |
| 작업 | `{"status": "ok"}` | `ok(None, message="저장되었습니다.")` |
| 단건 | `{**item, "bid_history": [...]}` | `ok({...})` |

#### routes_notification.py

| 패턴 | 현재 | 변환 |
|------|------|------|
| 리스트 | `{"items": [...], "unread_count": N}` | `ok_list(items, total=N)` + meta에 `unread_count` 추가 |
| 작업 | `{"status": "ok"}` | `ok(None, message="완료")` |

#### routes_auth.py

| 엔드포인트 | 현재 | 변환 |
|-----------|------|------|
| `GET /me` | `{user 객체}` | `ok(user)` |
| `POST /sync-profile` | `{user 객체}` | `ok(user)` |
| `POST /logout` | `{"message": "로그아웃"}` | `ok(None, message="로그아웃 되었습니다.")` |

#### routes_users.py

| 패턴 | 현재 | 변환 |
|------|------|------|
| 단건 | `response_model=UserResponse` | `response_model` 제거 → `ok(user)` |
| 리스트 | `response_model=UserListResponse` | `response_model` 제거 → `ok_list(users, total=N)` |
| 생성 | `response_model=TeamResponse` | `response_model` 제거 → `ok(team)` |

### 3.2 그룹 2 — 도메인 서비스 (10파일)

동일 패턴 적용. 핵심 변환 규칙:

| 현재 패턴 | 변환 |
|----------|------|
| `{"items": [...], "total": N}` | `ok_list(items, total=N)` |
| `{"data": [...]}` | `ok_list(items, total=len(items))` |
| `{"status": "ok"}` | `ok(None, message="완료")` |
| `{"status": "ok", "key": val}` | `ok({"key": val})` |
| `{...도메인 객체}` | `ok({...})` |
| `response_model=X` | `response_model` 제거 → `ok()` |

개별 주의사항:

| 파일 | 특이사항 |
|------|---------|
| routes_qa.py | `{"data": [...]}` → `ok_list()` |
| routes_analytics.py | 집계 결과 raw dict → `ok()` |
| routes_streams.py | `response_model` 3곳 제거 |
| routes_submission_docs.py | `response_model` 8곳 제거 |
| routes_prompt_evolution.py | `{"prompts": [...]}` → `ok_list()`, `{"heatmap": [...]}` → `ok()` |
| routes_admin.py | `{"items": [...]}` → `ok_list()` |
| routes_performance.py | `{"status": "ok", ...}` → `ok()` |
| routes_files.py | `{"files": [...]}` → `ok_list()` |
| routes_bid_submission.py | raw dict → `ok()` |
| routes_team.py | Mixed → `ok()` / `ok_list()` |

### 3.3 그룹 3 — 보조 (8파일)

| 파일 | 변환 요약 |
|------|----------|
| routes_pricing.py | raw list → `ok_list()` |
| routes_templates.py | raw list → `ok_list()` |
| routes_resources.py | `{"items":}` → `ok_list()` |
| routes_calendar.py | Mixed → `ok()` / `ok_list()` |
| routes_presentation.py | FileResponse 유지, 메타 EP → `ok()` |
| routes_stats.py | `response_model` 제거 → `ok()` |
| routes_project_archive.py | `{"status": "ok"}` → `ok(None)` |
| routes_g2b.py | **예외 유지** — 외부 API 프록시 |

### 3.4 예외 목록 (변환 안 함)

| 파일 | 엔드포인트 | 사유 |
|------|-----------|------|
| routes_workflow.py | `GET /stream` | SSE (EventSourceResponse) |
| routes_artifacts.py | `GET /download/docx`, `/hwpx` | FileResponse |
| routes_presentation.py | `GET /download` | FileResponse |
| routes_g2b.py | 전체 | 외부 API 포맷 프록시 |
| routes_v31.py | 전체 | 레거시 — 삭제 예정 |

---

## 4. Frontend 변환 명세

### 4.1 `frontend/lib/api.ts` — 표준 타입 추가

```typescript
/** 표준 API 응답 */
export interface ApiResponse<T> {
  data: T;
  meta: {
    total?: number;
    offset?: number;
    limit?: number;
    timestamp: string;
    message?: string;
  };
}

/** 리스트 응답 (페이지네이션) */
export type ApiListResponse<T> = ApiResponse<T[]>;
```

### 4.2 `request()` 함수 수정

```typescript
// 기존: raw JSON 반환
async function request<T>(method: string, url: string, ...): Promise<T> {
  ...
  return await res.json();
}

// 변경 불필요 — 타입 파라미터만 ApiResponse<T>로 교체
// 호출부에서 res.data, res.meta.total 등으로 접근
```

### 4.3 호출부 변환 패턴

```typescript
// Before (res.items 패턴)
const res = await api.proposals.list(...);
setProposals(res.items);
setTotal(res.total);

// After (res.data 패턴)
const res = await api.proposals.list(...);
setProposals(res.data);
setTotal(res.meta.total ?? res.data.length);
```

### 4.4 변환 대상 페이지 (15개)

| # | 파일 | 현재 패턴 | 변환 |
|---|------|----------|------|
| 1 | `proposals/page.tsx` | `res.items`, `res.total` | `res.data`, `res.meta.total` |
| 2 | `dashboard/page.tsx` | `res.items` | `res.data` |
| 3 | `archive/page.tsx` | `res.items`, `res.total` | `res.data`, `res.meta.total` |
| 4 | `kb/clients/page.tsx` | `res.items` | `res.data` |
| 5 | `kb/competitors/page.tsx` | `res.items` | `res.data` |
| 6 | `monitoring/page.tsx` | `res.data`, `res.meta.total` | 이미 `data` — `meta` 경로만 확인 |
| 7 | `monitoring/settings/page.tsx` | `res.data.xxx` | `res.data.xxx` — 변경 없음 가능성 |
| 8 | `DuplicateBidWarning.tsx` | `res.items` | `res.data` |
| 9 | `ArtifactReviewPanel.tsx` | `res.data` | 확인 후 유지/변환 |
| 10-15 | KB/QA/알림 등 추가 페이지 | 혼합 | 개별 확인 |

### 4.5 api.ts 메서드 반환 타입 변환

```typescript
// Before
proposals: {
  list(...) { return request<{items: Proposal[]; total: number}>(...) }
}

// After
proposals: {
  list(...) { return request<ApiListResponse<Proposal>>(...) }
}
```

---

## 5. Implementation Order

### Phase A — 기반 (신규 1파일)

| # | 작업 | 파일 | 줄 |
|---|------|------|:--:|
| A-1 | 표준 래퍼 함수 `ok()`, `ok_list()` | `app/api/response.py` | ~35 |

### Phase B-1 — 핵심 CRUD (8파일)

| # | 작업 | 파일 |
|---|------|------|
| B-1 | routes_proposal.py | `{"items":}` → `ok_list()`, 나머지 → `ok()` |
| B-2 | routes_workflow.py | Raw dict → `ok()` (SSE 제외) |
| B-3 | routes_artifacts.py | Raw dict → `ok()` (FileResponse 제외) |
| B-4 | routes_bids.py | `{"data":}` → `ok()` / `ok_list()` |
| B-5 | routes_kb.py | `{"items":}` → `ok_list()` |
| B-6 | routes_notification.py | `{"items":}` → `ok_list()` |
| B-7 | routes_auth.py | Raw dict → `ok()` |
| B-8 | routes_users.py | `response_model` 제거 → `ok()` / `ok_list()` |

### Phase B-2 — 도메인 (10파일)

| # | 파일 |
|---|------|
| B-9 | routes_qa.py |
| B-10 | routes_analytics.py |
| B-11 | routes_performance.py |
| B-12 | routes_streams.py |
| B-13 | routes_submission_docs.py |
| B-14 | routes_prompt_evolution.py |
| B-15 | routes_files.py |
| B-16 | routes_bid_submission.py |
| B-17 | routes_admin.py |
| B-18 | routes_team.py |

### Phase B-3 — 보조 (6파일, G2B/v31 제외)

| # | 파일 |
|---|------|
| B-19 | routes_pricing.py |
| B-20 | routes_templates.py |
| B-21 | routes_resources.py |
| B-22 | routes_calendar.py |
| B-23 | routes_stats.py |
| B-24 | routes_project_archive.py |

### Phase C — 프론트엔드 동기화

| # | 작업 | 파일 |
|---|------|------|
| C-1 | `ApiResponse<T>` 타입 추가 | `frontend/lib/api.ts` |
| C-2 | 메서드 반환 타입 변경 | `frontend/lib/api.ts` |
| C-3 | 페이지 파싱 변경 | ~15개 .tsx |
| C-4 | TypeScript 빌드 검증 | `npm run build` |

---

## 6. File Summary

### 신규 (1파일)

| # | 파일 | 줄 |
|---|------|:--:|
| 1 | `app/api/response.py` | ~35 |

### 수정 — 백엔드 (24파일)

| 그룹 | 파일 수 | 주요 변경 |
|------|:-------:|----------|
| 그룹 1 (핵심) | 8 | return 문 래핑 + response_model 제거 |
| 그룹 2 (도메인) | 10 | return 문 래핑 + response_model 제거 |
| 그룹 3 (보조) | 6 | return 문 래핑 |

### 수정 — 프론트엔드 (~16파일)

| # | 파일 | 변경 |
|---|------|------|
| 1 | `frontend/lib/api.ts` | +타입 +반환타입 교체 (~100줄) |
| 2-16 | 15개 .tsx | `res.items` → `res.data`, `res.total` → `res.meta.total` |

### 예외 (4파일 — 변경 안 함)

`routes_g2b.py`, `routes_v31.py`, SSE 엔드포인트, FileResponse 엔드포인트

### 총계

| 항목 | 수치 |
|------|------|
| 신규 파일 | 1 |
| 수정 파일 (백엔드) | 24 |
| 수정 파일 (프론트) | ~16 |
| 총 수정 파일 | ~41 |
| 영향 엔드포인트 | ~120 |
| 예상 변경 줄 | ~1,000 |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-03-26 | 초판 — `ok()`/`ok_list()` 래퍼 + 24 라우트 + 16 프론트 파일 |
