# PSM-16: Q&A 기록 검색 가능 저장 — 설계 문서

> **요구사항 ID**: PSM-16 (Must)
> **기능명**: psm-16-qa-search
> **버전**: v1.0
> **작성일**: 2026-03-18
> **상태**: Design
> **Plan 참조**: `docs/01-plan/features/psm-16-qa-search.plan.md`

---

## 1. DB 마이그레이션

### 1-1. presentation_qa 테이블 확장

**파일**: `database/migrations/005_qa_search.sql`

```sql
-- PSM-16: Q&A 기록 검색 가능 저장
-- presentation_qa 테이블에 임베딩·콘텐츠 연결·카테고리·작성자 추가

ALTER TABLE presentation_qa
  ADD COLUMN IF NOT EXISTS embedding vector(1536),
  ADD COLUMN IF NOT EXISTS content_library_id UUID REFERENCES content_library(id),
  ADD COLUMN IF NOT EXISTS category TEXT DEFAULT 'general',
  ADD COLUMN IF NOT EXISTS created_by UUID REFERENCES users(id);

-- 시맨틱 검색용 IVFFlat 인덱스
CREATE INDEX IF NOT EXISTS idx_presentation_qa_embedding
  ON presentation_qa USING ivfflat (embedding vector_cosine_ops) WITH (lists = 10);

-- 조회 성능용 B-tree 인덱스
CREATE INDEX IF NOT EXISTS idx_presentation_qa_proposal_id
  ON presentation_qa (proposal_id);

CREATE INDEX IF NOT EXISTS idx_presentation_qa_category
  ON presentation_qa (category);

-- 시맨틱 검색 RPC 함수
CREATE OR REPLACE FUNCTION search_qa_by_embedding(
  query_embedding vector(1536),
  match_org_id UUID,
  match_count INT DEFAULT 10,
  filter_category TEXT DEFAULT NULL
)
RETURNS TABLE (
  id UUID,
  proposal_id UUID,
  question TEXT,
  answer TEXT,
  category TEXT,
  evaluator_reaction TEXT,
  memo TEXT,
  created_at TIMESTAMPTZ,
  similarity FLOAT
) AS $$
BEGIN
  RETURN QUERY
  SELECT
    pq.id,
    pq.proposal_id,
    pq.question,
    pq.answer,
    pq.category,
    pq.evaluator_reaction,
    pq.memo,
    pq.created_at,
    1 - (pq.embedding <=> query_embedding) AS similarity
  FROM presentation_qa pq
  JOIN proposals p ON p.id = pq.proposal_id
  WHERE p.org_id = match_org_id
    AND pq.embedding IS NOT NULL
    AND (filter_category IS NULL OR pq.category = filter_category)
  ORDER BY pq.embedding <=> query_embedding
  LIMIT match_count;
END;
$$ LANGUAGE plpgsql STABLE;
```

### 1-2. 카테고리 정의

| 카테고리 | 설명 | 예시 |
|----------|------|------|
| `technical` | 기술 관련 질문 | 시스템 아키텍처, 보안 체계 |
| `management` | 관리/프로세스 질문 | 프로젝트 관리 방법론, 일정 관리 |
| `pricing` | 가격/예산 질문 | 인건비 산정 근거, 직접비 비율 |
| `experience` | 수행 실적 질문 | 유사 사업 경험, 레퍼런스 |
| `team` | 투입 인력 질문 | 핵심 인력 경력, 상주 비율 |
| `general` | 기타/미분류 | 기본값 |

---

## 2. Pydantic 스키마

**파일**: `app/models/schemas.py` (기존 파일에 추가)

```python
# ── PSM-16: Q&A 기록 ──

QA_CATEGORIES = Literal[
    "technical", "management", "pricing", "experience", "team", "general"
]


class QARecordCreate(BaseModel):
    """Q&A 기록 생성."""
    question: str
    answer: str
    category: QA_CATEGORIES = "general"
    evaluator_reaction: Literal["positive", "neutral", "negative"] | None = None
    memo: str | None = None


class QARecordUpdate(BaseModel):
    """Q&A 기록 수정."""
    question: str | None = None
    answer: str | None = None
    category: QA_CATEGORIES | None = None
    evaluator_reaction: Literal["positive", "neutral", "negative"] | None = None
    memo: str | None = None


class QARecordResponse(BaseModel):
    """Q&A 기록 응답."""
    id: str
    proposal_id: str
    question: str
    answer: str
    category: str
    evaluator_reaction: str | None
    memo: str | None
    content_library_id: str | None
    created_at: str
    created_by: str | None


class QASearchResult(BaseModel):
    """Q&A 검색 결과."""
    id: str
    proposal_id: str
    question: str
    answer: str
    category: str
    evaluator_reaction: str | None
    memo: str | None
    created_at: str
    similarity: float | None = None
    proposal_name: str | None = None
    client: str | None = None
```

---

## 3. 서비스 계층

### 3-1. Q&A 서비스

**파일**: `app/services/qa_service.py`

```python
"""
Q&A 기록 검색 가능 저장 서비스 (PSM-16)

발표 현장 Q&A → presentation_qa 저장 → content_library 등록
→ 임베딩 생성 → 교훈 아카이브 요약 기록.
"""

import logging
from app.utils.supabase_client import get_async_client
from app.services.embedding_service import generate_embedding

logger = logging.getLogger(__name__)


async def save_qa_records(
    proposal_id: str,
    qa_records: list[dict],
    created_by: str | None = None,
) -> list[dict]:
    """
    Q&A 기록 일괄 저장 + KB 연동.

    1) presentation_qa 테이블 저장
    2) content_library에 qa_record 유형 등록 (status=published)
    3) 임베딩 생성 → presentation_qa.embedding + content_library.embedding
    4) lessons_learned에 Q&A 요약 기록

    Returns: 생성된 Q&A 레코드 목록
    """
    client = await get_async_client()

    # 프로젝트 정보 조회
    proposal = await client.table("proposals").select(
        "id, name, client, org_id, industry"
    ).eq("id", proposal_id).single().execute()
    if not proposal.data:
        raise ValueError(f"프로젝트 미존재: {proposal_id}")

    p = proposal.data
    saved = []

    for qa in qa_records:
        # 1) presentation_qa 저장
        qa_row = {
            "proposal_id": proposal_id,
            "question": qa["question"],
            "answer": qa["answer"],
            "category": qa.get("category", "general"),
            "evaluator_reaction": qa.get("evaluator_reaction"),
            "memo": qa.get("memo"),
            "created_by": created_by,
        }
        result = await client.table("presentation_qa").insert(qa_row).execute()
        qa_record = result.data[0]

        # 2) content_library에 qa_record 등록
        content_body = f"Q: {qa['question']}\nA: {qa['answer']}"
        cl_row = {
            "org_id": p["org_id"],
            "type": "qa_record",
            "title": f"[Q&A] {qa['question'][:50]}",
            "body": content_body,
            "source_project_id": proposal_id,
            "industry": p.get("industry"),
            "tags": [qa.get("category", "general"), "qa", "presentation"],
            "status": "published",
            "author_id": created_by,
        }
        cl_result = await client.table("content_library").insert(cl_row).execute()
        content_id = cl_result.data[0]["id"]

        # presentation_qa에 content_library_id 연결
        await client.table("presentation_qa").update({
            "content_library_id": content_id,
        }).eq("id", qa_record["id"]).execute()

        # 3) 임베딩 생성
        try:
            embedding = await generate_embedding(content_body)
            await client.table("presentation_qa").update({
                "embedding": embedding,
            }).eq("id", qa_record["id"]).execute()
            await client.table("content_library").update({
                "embedding": embedding,
            }).eq("id", content_id).execute()
        except Exception as e:
            logger.warning(f"Q&A 임베딩 생성 실패 (계속 진행): {e}")

        qa_record["content_library_id"] = content_id
        saved.append(qa_record)

    # 4) 교훈 아카이브에 Q&A 요약 기록
    if qa_records:
        await _save_qa_lesson_summary(client, proposal_id, p, qa_records, created_by)

    return saved


async def _save_qa_lesson_summary(
    client, proposal_id: str, proposal: dict,
    qa_records: list[dict], created_by: str | None,
) -> None:
    """Q&A 요약을 교훈 아카이브에 기록."""
    try:
        qa_summary = "\n".join(
            f"• Q: {qa['question'][:80]} → A: {qa['answer'][:80]}"
            for qa in qa_records
        )
        lesson_row = {
            "proposal_id": proposal_id,
            "org_id": proposal["org_id"],
            "category": "qa_insight",
            "strategy_summary": f"발표 Q&A ({len(qa_records)}건) - {proposal.get('name', '')}",
            "effective_points": qa_summary,
            "result": "presented",
            "client_name": proposal.get("client", ""),
            "created_by": created_by,
        }
        result = await client.table("lessons_learned").insert(lesson_row).execute()

        # 교훈 임베딩 생성
        if result.data:
            from app.services.kb_updater import generate_lesson_embedding
            lesson = result.data[0]
            await generate_lesson_embedding(
                lesson["id"],
                lesson_row["strategy_summary"],
                qa_summary,
            )
    except Exception as e:
        logger.warning(f"Q&A 교훈 요약 저장 실패 (계속 진행): {e}")


async def get_proposal_qa(proposal_id: str) -> list[dict]:
    """프로젝트별 Q&A 기록 조회."""
    client = await get_async_client()
    result = await client.table("presentation_qa").select(
        "id, proposal_id, question, answer, category, "
        "evaluator_reaction, memo, content_library_id, created_at, created_by"
    ).eq("proposal_id", proposal_id).order("created_at").execute()
    return result.data or []


async def update_qa_record(qa_id: str, updates: dict) -> dict:
    """개별 Q&A 기록 수정 + 임베딩 재생성."""
    client = await get_async_client()

    # 업데이트
    result = await client.table("presentation_qa").update(
        {k: v for k, v in updates.items() if v is not None}
    ).eq("id", qa_id).execute()
    if not result.data:
        raise ValueError(f"Q&A 레코드 미존재: {qa_id}")

    qa = result.data[0]

    # question 또는 answer 변경 시 임베딩 + content_library 동기화
    if "question" in updates or "answer" in updates:
        content_body = f"Q: {qa['question']}\nA: {qa['answer']}"
        try:
            embedding = await generate_embedding(content_body)
            await client.table("presentation_qa").update({
                "embedding": embedding,
            }).eq("id", qa_id).execute()

            if qa.get("content_library_id"):
                await client.table("content_library").update({
                    "title": f"[Q&A] {qa['question'][:50]}",
                    "body": content_body,
                    "embedding": embedding,
                }).eq("id", qa["content_library_id"]).execute()
        except Exception as e:
            logger.warning(f"Q&A 임베딩 업데이트 실패: {e}")

    return qa


async def delete_qa_record(qa_id: str) -> None:
    """개별 Q&A 기록 삭제 + content_library 연결 해제."""
    client = await get_async_client()

    # content_library_id 조회
    qa = await client.table("presentation_qa").select(
        "id, content_library_id"
    ).eq("id", qa_id).single().execute()
    if not qa.data:
        raise ValueError(f"Q&A 레코드 미존재: {qa_id}")

    # content_library에서도 삭제
    if qa.data.get("content_library_id"):
        await client.table("content_library").delete().eq(
            "id", qa.data["content_library_id"]
        ).execute()

    # presentation_qa 삭제
    await client.table("presentation_qa").delete().eq("id", qa_id).execute()


async def search_qa(
    query: str,
    org_id: str,
    category: str | None = None,
    limit: int = 10,
) -> list[dict]:
    """
    Q&A 하이브리드 검색 (시맨틱 + 키워드 폴백).

    1) pgvector RPC: search_qa_by_embedding
    2) 폴백: 키워드 ILIKE 검색
    """
    client = await get_async_client()

    # 시맨틱 검색 시도
    try:
        query_embedding = await generate_embedding(query)
        result = await client.rpc("search_qa_by_embedding", {
            "query_embedding": query_embedding,
            "match_org_id": org_id,
            "match_count": limit,
            "filter_category": category,
        }).execute()

        items = result.data or []

        # 프로젝트 이름/발주기관 부가정보 보강
        if items:
            proposal_ids = list({it["proposal_id"] for it in items})
            proposals = await client.table("proposals").select(
                "id, name, client"
            ).in_("id", proposal_ids).execute()
            pmap = {p["id"]: p for p in (proposals.data or [])}
            for it in items:
                p = pmap.get(it["proposal_id"], {})
                it["proposal_name"] = p.get("name")
                it["client"] = p.get("client")

        return items

    except Exception:
        logger.info("search_qa_by_embedding RPC 미등록, 키워드 검색 폴백")
        return await _keyword_search_qa(client, query, org_id, category, limit)


async def _keyword_search_qa(
    client, query: str, org_id: str, category: str | None, limit: int,
) -> list[dict]:
    """키워드 폴백 검색."""
    q = client.table("presentation_qa").select(
        "id, proposal_id, question, answer, category, "
        "evaluator_reaction, memo, created_at, "
        "proposals!inner(name, client, org_id)"
    ).eq("proposals.org_id", org_id)

    if category:
        q = q.eq("category", category)

    # question 또는 answer에 키워드 포함
    q = q.or_(f"question.ilike.%{query}%,answer.ilike.%{query}%")
    result = await q.order("created_at", desc=True).limit(limit).execute()

    items = []
    for row in result.data or []:
        prop = row.pop("proposals", {})
        row["proposal_name"] = prop.get("name")
        row["client"] = prop.get("client")
        row["similarity"] = None
        items.append(row)
    return items
```

---

## 4. API 엔드포인트

**파일**: `app/api/routes_qa.py`

```python
"""
Q&A 기록 CRUD + 검색 API (PSM-16)

POST   /api/proposals/{id}/qa          — Q&A 일괄 등록
GET    /api/proposals/{id}/qa          — 프로젝트별 Q&A 조회
PUT    /api/proposals/{id}/qa/{qa_id}  — 개별 Q&A 수정
DELETE /api/proposals/{id}/qa/{qa_id}  — 개별 Q&A 삭제
GET    /api/kb/qa/search               — 조직 전체 Q&A 검색
"""

import logging

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user, require_project_access
from app.models.schemas import QARecordCreate, QARecordUpdate, QARecordResponse, QASearchResult
from app.services.qa_service import (
    save_qa_records,
    get_proposal_qa,
    update_qa_record,
    delete_qa_record,
    search_qa,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["qa"])


@router.post("/api/proposals/{proposal_id}/qa", status_code=201)
async def create_qa_records(
    proposal_id: str,
    records: list[QARecordCreate],
    user=Depends(get_current_user),
):
    """Q&A 기록 일괄 등록 + KB 자동 연동."""
    _ = await require_project_access(proposal_id, user)
    qa_dicts = [r.model_dump() for r in records]
    saved = await save_qa_records(proposal_id, qa_dicts, created_by=user["id"])
    return {"data": saved, "count": len(saved)}


@router.get("/api/proposals/{proposal_id}/qa")
async def list_qa_records(
    proposal_id: str,
    user=Depends(get_current_user),
):
    """프로젝트별 Q&A 기록 조회."""
    _ = await require_project_access(proposal_id, user)
    records = await get_proposal_qa(proposal_id)
    return {"data": records, "count": len(records)}


@router.put("/api/proposals/{proposal_id}/qa/{qa_id}")
async def update_qa(
    proposal_id: str,
    qa_id: str,
    body: QARecordUpdate,
    user=Depends(get_current_user),
):
    """개별 Q&A 기록 수정."""
    _ = await require_project_access(proposal_id, user)
    updated = await update_qa_record(qa_id, body.model_dump(exclude_unset=True))
    return {"data": updated}


@router.delete("/api/proposals/{proposal_id}/qa/{qa_id}", status_code=204)
async def remove_qa(
    proposal_id: str,
    qa_id: str,
    user=Depends(get_current_user),
):
    """개별 Q&A 기록 삭제."""
    _ = await require_project_access(proposal_id, user)
    await delete_qa_record(qa_id)


@router.get("/api/kb/qa/search")
async def search_qa_records(
    query: str = Query(..., min_length=1),
    category: str | None = Query(None),
    limit: int = Query(10, ge=1, le=50),
    user=Depends(get_current_user),
):
    """조직 전체 Q&A 검색 (시맨틱 + 키워드 하이브리드)."""
    org_id = user.get("org_id")
    results = await search_qa(query, org_id, category=category, limit=limit)
    return {"data": results, "count": len(results)}
```

### 4-1. 라우터 등록

**파일**: `app/main.py` (기존 파일 수정)

```python
# 추가할 import
from app.api.routes_qa import router as qa_router

# app.include_router() 블록에 추가
app.include_router(qa_router)
```

---

## 5. 워크플로 연동

### 5-1. 설계 결정: 워크플로 외부 등록 방식

Q&A 기록은 **발표 이후** 수동으로 등록하는 것이 자연스러움 (발표 현장에서 즉시 입력하지 않음).
따라서 LangGraph 워크플로 내부에 노드를 추가하지 않고, **API 직접 호출** 방식 채택.

- 프론트엔드: 프로젝트 상세 → Q&A 탭에서 수동 입력
- 타이밍: `review_ppt` 승인 후 또는 프로젝트 상태가 `presented`/`won`/`lost` 일 때
- 워크플로에서는 `review_ppt` 승인 시 interrupt_data에 "Q&A 입력을 잊지 마세요" 안내 메시지만 추가

### 5-2. review_ppt 안내 메시지

**파일**: `app/graph/nodes/review_node.py` (기존 파일 수정)

```python
# review_node 함수 내 interrupt_data 구성 부분에 추가
# step_name == "ppt" 일 때:
if step_name == "ppt":
    interrupt_data["qa_reminder"] = (
        "발표 완료 후, 프로젝트 상세 → Q&A 탭에서 "
        "질의응답 기록을 등록하면 향후 제안에 활용됩니다."
    )
```

---

## 6. 프론트엔드

### 6-1. QaPanel 컴포넌트

**파일**: `frontend/components/QaPanel.tsx`

**Props**: `{ proposalId: string }`

**기능**:
- Q&A 기록 목록 조회 (`GET /api/proposals/{id}/qa`)
- 새 Q&A 추가 폼 (질문, 답변, 카테고리 드롭다운, 평가위원 반응, 메모)
- 개별 Q&A 수정 (인라인 편집)
- 개별 Q&A 삭제 (확인 다이얼로그)
- 일괄 등록 지원 (여러 Q&A를 한 번에 제출)

**UI 구조**:
```
┌─────────────────────────────────────────────┐
│ Q&A 기록 (N건)                    [+ 추가]  │
├─────────────────────────────────────────────┤
│ ┌─ Q&A #1 ────────────────────── [수정|삭제]│
│ │ Q: 프로젝트 관리 방법론은?                │
│ │ A: PMI PMBOK 기반 ...                    │
│ │ 카테고리: management | 반응: positive     │
│ └───────────────────────────────────────────│
│ ┌─ Q&A #2 ────────────────────── [수정|삭제]│
│ │ Q: 보안 인증 현황은?                      │
│ │ A: ISO 27001 인증 보유 ...                │
│ │ 카테고리: technical | 반응: neutral       │
│ └───────────────────────────────────────────│
├─────────────────────────────────────────────┤
│ 새 Q&A 추가                                │
│ 질문: [___________________________]         │
│ 답변: [___________________________]         │
│ 카테고리: [드롭다운 ▾]  반응: [드롭다운 ▾]  │
│ 메모: [___________________________]         │
│                            [등록]           │
└─────────────────────────────────────────────┘
```

### 6-2. 프로젝트 상세 페이지 통합

**파일**: `frontend/app/proposals/[id]/page.tsx` (기존 파일 수정)

- 기존 탭 구조에 "Q&A" 탭 추가
- QaPanel 컴포넌트 렌더링
- 프로젝트 상태가 `presented`, `won`, `lost` 일 때만 Q&A 탭 활성화

### 6-3. KB Q&A 검색 페이지

**파일**: `frontend/app/kb/qa/page.tsx`

**기능**:
- 검색바 (키워드 입력 → `GET /api/kb/qa/search`)
- 카테고리 필터 드롭다운
- 검색 결과 카드 목록
- 카드: 질문, 답변 (요약), 카테고리 뱃지, 출처 프로젝트명, 발주기관, 등록일, 유사도 점수

**UI 구조**:
```
┌─────────────────────────────────────────────┐
│ Q&A 지식 검색                               │
├─────────────────────────────────────────────┤
│ [검색어 입력_______________] [카테고리 ▾] 🔍│
├─────────────────────────────────────────────┤
│ ┌─ 유사도 92% ──────────────────────────────│
│ │ Q: 프로젝트 관리 방법론은?                │
│ │ A: PMI PMBOK 기반 테일러링 방법론을 ...   │
│ │ 📁 ○○기관 시스템 구축 | management       │
│ │ 📅 2026-02-15                             │
│ └───────────────────────────────────────────│
│ ┌─ 유사도 87% ──────────────────────────────│
│ │ Q: 유사 사업 수행 경험?                   │
│ │ A: 최근 3년간 5건의 ...                   │
│ │ 📁 △△연구소 ISP | experience             │
│ │ 📅 2026-01-20                             │
│ └───────────────────────────────────────────│
└─────────────────────────────────────────────┘
```

### 6-4. API 클라이언트

**파일**: `frontend/lib/api.ts` (기존 파일에 추가)

```typescript
// Q&A API 메서드
export const qaApi = {
  list: (proposalId: string) =>
    fetchApi<{ data: QARecord[]; count: number }>(
      `/api/proposals/${proposalId}/qa`
    ),
  create: (proposalId: string, records: QARecordCreate[]) =>
    fetchApi<{ data: QARecord[]; count: number }>(
      `/api/proposals/${proposalId}/qa`,
      { method: "POST", body: JSON.stringify(records) }
    ),
  update: (proposalId: string, qaId: string, body: QARecordUpdate) =>
    fetchApi<{ data: QARecord }>(
      `/api/proposals/${proposalId}/qa/${qaId}`,
      { method: "PUT", body: JSON.stringify(body) }
    ),
  delete: (proposalId: string, qaId: string) =>
    fetchApi<void>(
      `/api/proposals/${proposalId}/qa/${qaId}`,
      { method: "DELETE" }
    ),
  search: (query: string, category?: string, limit?: number) =>
    fetchApi<{ data: QASearchResult[]; count: number }>(
      `/api/kb/qa/search?query=${encodeURIComponent(query)}` +
      (category ? `&category=${category}` : "") +
      (limit ? `&limit=${limit}` : "")
    ),
};
```

### 6-5. TypeScript 타입

```typescript
interface QARecord {
  id: string;
  proposal_id: string;
  question: string;
  answer: string;
  category: string;
  evaluator_reaction: string | null;
  memo: string | null;
  content_library_id: string | null;
  created_at: string;
  created_by: string | null;
}

interface QARecordCreate {
  question: string;
  answer: string;
  category?: string;
  evaluator_reaction?: string | null;
  memo?: string | null;
}

interface QARecordUpdate {
  question?: string;
  answer?: string;
  category?: string;
  evaluator_reaction?: string | null;
  memo?: string | null;
}

interface QASearchResult extends QARecord {
  similarity: number | null;
  proposal_name: string | null;
  client: string | null;
}
```

---

## 7. 통합 KB 검색 연동

### 7-1. knowledge_search.py 확장

**파일**: `app/services/knowledge_search.py` (기존 파일 수정)

`unified_search`의 `all_areas`에 `"qa"` 영역을 추가하고, `_search_qa` 함수를 추가.

```python
# all_areas에 "qa" 추가
all_areas = ["content", "client", "competitor", "lesson", "capability", "qa"]

# 새 영역 검색 task 추가
if "qa" in areas:
    tasks["qa"] = _search_qa(query, query_embedding, org_id, top_k)


async def _search_qa(
    query: str,
    embedding: list[float],
    org_id: str,
    top_k: int,
) -> list[dict]:
    """Q&A 시맨틱 검색."""
    client = await get_async_client()
    try:
        result = await client.rpc("search_qa_by_embedding", {
            "query_embedding": embedding,
            "match_org_id": org_id,
            "match_count": top_k,
        }).execute()
        return result.data or []
    except Exception:
        logger.info("search_qa_by_embedding RPC 미등록, 키워드 검색 폴백")
        result = await client.table("presentation_qa").select(
            "id, question, answer, category, created_at"
        ).eq("proposals.org_id", org_id).or_(
            f"question.ilike.%{query}%,answer.ilike.%{query}%"
        ).limit(top_k).execute()
        return result.data or []
```

---

## 8. 파일 변경 목록

| 유형 | 파일 | 변경 내용 |
|------|------|----------|
| **신규** | `database/migrations/005_qa_search.sql` | 테이블 확장 + 인덱스 + RPC |
| **신규** | `app/services/qa_service.py` | Q&A CRUD + KB 연동 + 검색 서비스 |
| **신규** | `app/api/routes_qa.py` | Q&A API 5개 엔드포인트 |
| **신규** | `frontend/components/QaPanel.tsx` | Q&A 입력/관리 컴포넌트 |
| **신규** | `frontend/app/kb/qa/page.tsx` | KB Q&A 검색 페이지 |
| **수정** | `app/models/schemas.py` | QARecordCreate/Update/Response/SearchResult 추가 |
| **수정** | `app/main.py` | qa_router 등록 |
| **수정** | `app/graph/nodes/review_node.py` | PPT 리뷰 시 Q&A 안내 메시지 |
| **수정** | `app/services/knowledge_search.py` | qa 영역 추가 |
| **수정** | `frontend/app/proposals/[id]/page.tsx` | Q&A 탭 추가 |
| **수정** | `frontend/lib/api.ts` | qaApi 메서드 추가 |

---

## 9. 구현 순서 (의존성 기준)

```
1. DB 마이그레이션 (005_qa_search.sql)
2. Pydantic 스키마 (schemas.py 확장)
3. qa_service.py (신규)
4. routes_qa.py (신규) + main.py 등록
5. knowledge_search.py 확장
6. review_node.py Q&A 안내 추가
7. QaPanel.tsx + proposals/[id]/page.tsx Q&A 탭
8. kb/qa/page.tsx + api.ts 확장
```

---

## 10. 검증 체크리스트

- [ ] `POST /api/proposals/{id}/qa` — Q&A 등록 시 presentation_qa + content_library + embedding 동시 생성
- [ ] `GET /api/proposals/{id}/qa` — 프로젝트별 Q&A 시간순 조회
- [ ] `PUT /api/proposals/{id}/qa/{qa_id}` — 수정 시 임베딩 재생성 + content_library 동기화
- [ ] `DELETE /api/proposals/{id}/qa/{qa_id}` — 삭제 시 content_library도 삭제
- [ ] `GET /api/kb/qa/search` — 시맨틱 검색 결과 + 프로젝트명/발주기관 부가정보
- [ ] 시맨틱 검색 RPC 미등록 시 키워드 폴백 동작
- [ ] `unified_search`에서 qa 영역 포함 확인
- [ ] `review_ppt` 승인 시 Q&A 입력 안내 메시지 노출
- [ ] QaPanel: 일괄 등록, 수정, 삭제 UI 동작
- [ ] KB Q&A 페이지: 검색 + 카테고리 필터 + 결과 카드
- [ ] 인증: require_project_access 적용 확인
