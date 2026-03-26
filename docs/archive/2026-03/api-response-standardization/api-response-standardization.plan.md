# Plan: API 응답 구조 표준화

> **Feature**: api-response-standardization
> **Version**: 1.0
> **Date**: 2026-03-26
> **Status**: Plan

---

## 1. 배경 및 문제 정의

### 1.1 현황 진단

28개 FastAPI 라우트 파일에서 **4가지 서로 다른 응답 래핑 패턴**이 혼재:

| 패턴 | 형태 | 사용 파일 수 |
|------|------|:-----------:|
| A — `{"items": [...], "total": N}` | KB, Notification, Admin, Resources, Submission Docs | 5 |
| B — `{"data": [...], "count": N}` | Bids, QA, Team, KB search | 4 |
| C — Raw dict/Pydantic (무래핑) | Workflow, Artifacts, Auth, Files, Pricing 등 | 17 |
| D — 커스텀 도메인 형식 | Analytics, G2B, Bids(일부) | 6+ |

### 1.2 구체적 문제점

1. **프론트엔드 파싱 불일치**: `res.items`, `res.data`, `res.total`, `res.meta.total` 등 4가지 이상의 접근 패턴이 혼용됨
2. **response_model 미사용 77%**: 20/26 파일이 raw dict 반환 → OpenAPI 스키마 없음, SDK 자동생성 불가
3. **status 필드 부재 62%**: 16/26 파일이 성공/실패 구분 필드 없음 → HTTP status code에만 의존
4. **리스트 응답 형식 5종**: items vs data, total vs count, 페이지네이션 메타데이터 위치 불일치
5. **에러 응답은 100% 표준화됨** — TenopAPIError 기반. 성공 응답만 문제.

### 1.3 프론트엔드 영향도

```
res.items 사용:  archive, dashboard, proposals, kb/clients, kb/competitors
res.data 사용:   monitoring, bids, ArtifactReviewPanel
res.meta 사용:   monitoring(일부)
직접 접근:       나머지 대부분
```

---

## 2. 목표

| # | 목표 | 측정 기준 |
|---|------|----------|
| G-1 | 모든 API 엔드포인트에 통일된 응답 래퍼 적용 | 래핑 패턴 1종으로 수렴 |
| G-2 | 모든 리스트 엔드포인트에 페이지네이션 메타 포함 | `total`, `offset`, `limit` 필드 100% |
| G-3 | response_model 적용률 100% | OpenAPI 스키마 자동 생성 확인 |
| G-4 | 프론트엔드 api.ts 동기화 | 빌드 에러 0, 통일된 파싱 패턴 |

### 2.1 비목표 (Non-Goals)

- 에러 응답 구조 변경 (이미 표준화됨)
- API 엔드포인트 URL 변경 (기존 경로 유지)
- 비즈니스 로직 변경

---

## 3. 표준 응답 형식 정의

### 3.1 단건 응답

```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2026-03-26T12:00:00Z"
  }
}
```

### 3.2 리스트 응답

```json
{
  "data": [ ... ],
  "meta": {
    "total": 100,
    "offset": 0,
    "limit": 20,
    "timestamp": "2026-03-26T12:00:00Z"
  }
}
```

### 3.3 빈 응답 (작업 완료)

```json
{
  "data": null,
  "meta": {
    "message": "삭제되었습니다.",
    "timestamp": "2026-03-26T12:00:00Z"
  }
}
```

### 3.4 에러 응답 (기존 유지)

```json
{
  "error_code": "SECT_001",
  "message": "섹션이 다른 사용자에 의해 잠겨 있습니다.",
  "detail": { ... }
}
```

### 3.5 설계 결정: `status` 필드 제외

- HTTP status code가 이미 성공/실패를 구분함
- 에러 응답은 `error_code` 필드 유무로 구분 가능
- 불필요한 `"status": "ok"` 제거로 페이로드 간소화

### 3.6 설계 결정: `data` 키 통일

- 기존 `items` (5곳), `data` (4곳), `results` (1곳) → **`data`로 통일**
- 이유: REST API 관례, 단건/리스트 동일 키, 프론트엔드 파싱 단순화

### 3.7 설계 결정: `meta` 분리

- 페이지네이션(`total`, `offset`, `limit`)과 기타 메타(`timestamp`, `message`)를 `meta` 객체로 분리
- 이유: `data`와 메타데이터의 명확한 경계, 향후 확장 용이

---

## 4. 구현 범위

### 4.1 Phase A — 표준 래퍼 유틸리티 + Pydantic 모델 (기반)

| # | 작업 | 대상 파일 | 예상 |
|---|------|----------|------|
| A-1 | 표준 응답 래퍼 함수 | `app/api/response.py` (신규) | ~80줄 |
| A-2 | Generic Pydantic 응답 모델 | `app/models/response_models.py` (신규) | ~60줄 |
| A-3 | main.py에 응답 미들웨어 등록 (선택) | `app/main.py` | ~10줄 |

`response.py` 핵심 설계:

```python
from typing import TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")

class Meta(BaseModel):
    total: int | None = None
    offset: int | None = None
    limit: int | None = None
    timestamp: str
    message: str | None = None

class ApiResponse(BaseModel, Generic[T]):
    data: T
    meta: Meta

# 헬퍼 함수
def ok(data, *, total=None, offset=None, limit=None, message=None) -> dict:
    ...

def ok_list(items, *, total, offset=0, limit=20) -> dict:
    ...
```

### 4.2 Phase B — 라우트 마이그레이션 (핵심)

26개 라우트 파일을 3개 그룹으로 나누어 순차 적용:

**그룹 1 — 핵심 CRUD (8파일, 영향도 HIGH)**

| # | 파일 | 현재 패턴 | 엔드포인트 수 | 변경 |
|---|------|----------|:-----------:|------|
| B-1 | routes_proposal.py | Pydantic | ~8 | response_model → ApiResponse[T] |
| B-2 | routes_workflow.py | Raw dict | ~6 | return → ok() 래핑 |
| B-3 | routes_artifacts.py | Raw dict | ~5 | return → ok() 래핑 |
| B-4 | routes_bids.py | `{"data":}` | ~15 | `{"data":}` → ok() 통일 |
| B-5 | routes_kb.py | `{"items":}` | ~12 | `{"items":}` → ok_list() |
| B-6 | routes_notification.py | `{"items":}` | ~4 | `{"items":}` → ok_list() |
| B-7 | routes_auth.py | Raw dict | ~4 | return → ok() |
| B-8 | routes_users.py | response_model | ~10 | 유지 + ApiResponse 래핑 |

**그룹 2 — 도메인 서비스 (10파일, 영향도 MEDIUM)**

| # | 파일 | 엔드포인트 수 |
|---|------|:-----------:|
| B-9 | routes_qa.py | ~5 |
| B-10 | routes_analytics.py | ~4 |
| B-11 | routes_performance.py | ~5 |
| B-12 | routes_streams.py | ~3 |
| B-13 | routes_submission_docs.py | ~11 |
| B-14 | routes_prompt_evolution.py | ~15 |
| B-15 | routes_files.py | ~5 |
| B-16 | routes_bid_submission.py | ~4 |
| B-17 | routes_admin.py | ~5 |
| B-18 | routes_team.py | ~5 |

**그룹 3 — 보조/참조 (8파일, 영향도 LOW)**

| # | 파일 | 엔드포인트 수 |
|---|------|:-----------:|
| B-19 | routes_pricing.py | ~3 |
| B-20 | routes_templates.py | ~3 |
| B-21 | routes_resources.py | ~3 |
| B-22 | routes_calendar.py | ~4 |
| B-23 | routes_presentation.py | ~3 |
| B-24 | routes_stats.py | ~2 |
| B-25 | routes_project_archive.py | ~4 |
| B-26 | routes_g2b.py | ~2 (외부 API 포맷 유지) |

### 4.3 Phase C — 프론트엔드 동기화

| # | 작업 | 대상 파일 | 예상 |
|---|------|----------|------|
| C-1 | api.ts 타입 업데이트 | `frontend/lib/api.ts` | ~40줄 |
| C-2 | api.ts 메서드 파싱 통일 | `frontend/lib/api.ts` | ~100줄 |
| C-3 | 페이지 컴포넌트 res.items → res.data | ~15개 .tsx 파일 | ~50줄 |
| C-4 | TypeScript 빌드 검증 | - | 0 에러 |

api.ts 표준 파서:

```typescript
interface ApiResponse<T> {
  data: T;
  meta: { total?: number; offset?: number; limit?: number; timestamp: string; message?: string };
}

// 기존: const res = await api.get<{items: T[]; total: number}>(...)
// 변경: const res = await api.get<ApiResponse<T[]>>(...)
// 접근: res.data (items), res.meta.total
```

### 4.4 예외 항목

| 라우트 | 예외 사유 |
|--------|----------|
| routes_g2b.py | 나라장터 외부 API 포맷(`page_no`/`num_of_rows`)을 그대로 프록시. 내부 변환 시 오히려 혼란 |
| routes_workflow.py `/stream` SSE | Server-Sent Events는 JSON 응답 아님. 래핑 불가 |
| routes_presentation.py FileResponse | 바이너리 파일 반환. 래핑 불가 |
| routes_v31.py | 레거시 호환 라우트. 추후 삭제 예정 |

---

## 5. 위험 및 완화

| 위험 | 영향 | 완화 |
|------|------|------|
| 프론트엔드 대규모 파싱 변경 | 빌드 실패/런타임 에러 | Phase B-C 동시 적용, 그룹별 순차 |
| 기존 Pydantic response_model 충돌 | 이중 래핑 | response_model을 ApiResponse[T]로 교체 |
| 외부 연동 API 응답 변경 | Teams webhook 등 | 외부 연동 엔드포인트 예외 목록 관리 |

---

## 6. 구현 순서

```
Phase A (기반)     →  Phase B 그룹1  →  Phase C (프론트 동기화)
  response.py            핵심 CRUD 8파일       api.ts + 15개 .tsx
  response_models.py
                    →  Phase B 그룹2  →  Phase C 추가 동기화
                         도메인 10파일
                    →  Phase B 그룹3
                         보조 8파일
```

### 6.1 예상 규모

| 항목 | 수치 |
|------|------|
| 신규 파일 | 2 (response.py, response_models.py) |
| 수정 파일 (백엔드) | 26 라우트 + main.py |
| 수정 파일 (프론트) | api.ts + ~15개 .tsx |
| 총 변경 라인 | ~1,200줄 (추정) |
| 영향 엔드포인트 | ~130개 |

---

## 7. 성공 기준

| # | 기준 | 검증 방법 |
|---|------|----------|
| S-1 | 모든 JSON 엔드포인트가 `{data, meta}` 형식 | 갭분석 100% |
| S-2 | response_model 사용률 100% | Grep 검색 |
| S-3 | 프론트엔드 빌드 에러 0 | `npm run build` |
| S-4 | 기존 기능 회귀 없음 | 주요 시나리오 수동 검증 |
| S-5 | OpenAPI 문서에 응답 스키마 표시 | /docs 확인 |
