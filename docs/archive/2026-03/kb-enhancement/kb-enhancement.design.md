# KB 개선 Design

| 항목 | 내용 |
|------|------|
| Feature | kb-enhancement |
| 버전 | v1.0 |
| 작성일 | 2026-03-24 |
| 상태 | Design |
| Plan 참조 | `docs/01-plan/features/kb-enhancement.plan.md` |

---

## 1. Phase A — 자동 축적 강화

### 1-1. `auto_register_section()` — 섹션 자동 등록

**파일**: `app/services/content_library.py`

```python
async def auto_register_section(
    org_id: str,
    proposal_id: str,
    section_id: str,
    title: str,
    content: str,
    section_type: str,
    self_review_score: int | None = None,
    rfp_keywords: list[str] | None = None,
    industry: str | None = None,
) -> dict | None:
```

**로직**:
1. **품질 필터**: `len(content) < 500` → `None` (스킵)
2. **품질 필터**: `self_review_score is not None and self_review_score < 70` → `None`
3. **중복 체크**: `content_library`에서 `source_project_id == proposal_id AND title == title` → upsert
4. **등록**: `content_library.insert` or `update`
   - `type`: `"section_block"`
   - `status`: `"draft"` (승인 전까지 검색 미포함)
   - `source_project_id`: `proposal_id`
   - `industry`: RFP에서 추출 (있으면)
   - `tags`: `rfp_keywords[:10]` + `[section_type]`
   - `embedding`: `generate_embedding(embedding_text_for_content(title, content, tags))`
5. **반환**: 등록된 row dict 또는 `None`

### 1-2. `proposal_write_next` 연동

**파일**: `app/graph/nodes/proposal_nodes.py`

`proposal_write_next()` 함수의 `return` 직전, 새 섹션 생성 후 다음 코드 추가:

```python
# KB 자동 축적 (fire-and-forget, 실패 무시)
try:
    from app.services.content_library import auto_register_section
    rfp_dict = rfp_to_dict(state.get("rfp_analysis"))
    await auto_register_section(
        org_id=state.get("org_id", ""),
        proposal_id=state.get("project_id", ""),
        section_id=section_id,
        title=new_section.title,
        content=new_section.content,
        section_type=section_type,
        self_review_score=None,  # 개별 섹션 점수는 self_review 후 갱신
        rfp_keywords=rfp_dict.get("tech_keywords", []),
        industry=rfp_dict.get("domain", None),
    )
except Exception as e:
    logger.debug(f"섹션 KB 자동 축적 실패 (무시): {e}")
```

**삽입 위치**: L275 (`existing_sections = list(...)`) 이전, `new_section` 생성 직후.

### 1-3. `save_research_to_kb()` — 리서치 결과 축적

**파일**: `app/services/kb_updater.py`

```python
async def save_research_to_kb(
    org_id: str,
    proposal_id: str,
    research_brief: dict,
) -> int:
```

**로직**:
1. `research_brief["research_topics"]` 순회
2. 각 topic의 `data_points` 중 `credibility in ("high", "medium")` 필터
3. topic 단위로 1개 `content_library` row 생성:
   - `type`: `"research_data"`
   - `title`: `topic["topic"]`
   - `body`: `findings` + `data_points` 결합 텍스트
   - `tags`: `[topic["rfp_alignment"], "research", credibility]`
   - `source_project_id`: `proposal_id`
   - `status`: `"draft"`
   - `embedding`: 자동 생성
4. **반환**: 저장된 건수 (int)

### 1-4. `research_gather` 연동

**파일**: `app/graph/nodes/research_gather.py`

`return` 직전 (L133 부근) 추가:

```python
# KB 자동 축적 (리서치 결과)
try:
    from app.services.kb_updater import save_research_to_kb
    if result and not result.get("_parse_error"):
        saved = await save_research_to_kb(
            org_id=state.get("org_id", ""),
            proposal_id=state.get("project_id", ""),
            research_brief=result,
        )
        logger.info(f"리서치 KB 축적: {saved}건")
except Exception as e:
    logger.debug(f"리서치 KB 축적 실패 (무시): {e}")
```

### 1-5. `save_strategy_to_kb()` — 전략 결과 축적

**파일**: `app/services/kb_updater.py`

```python
async def save_strategy_to_kb(
    org_id: str,
    proposal_id: str,
    client_name: str,
    positioning: str,
    strategy_result: dict,
) -> dict | None:
```

**로직**:
1. `content_library`에 1 row 생성:
   - `type`: `"strategy_record"`
   - `title`: `f"전략: {client_name} ({positioning})"`
   - `body`: JSON → 텍스트 (win_theme, ghost_theme, key_messages, focus_areas, competitor_analysis 포함)
   - `tags`: `[positioning, client_name, "strategy"]`
   - `source_project_id`: `proposal_id`
   - `industry`: `strategy_result.get("domain", "")`
   - `status`: `"draft"`
   - `embedding`: 자동 생성
2. **반환**: 등록된 row dict

### 1-6. `strategy_generate` 연동

**파일**: `app/graph/nodes/strategy_generate.py`

`return` 직전 (L180 부근) 추가:

```python
# KB 자동 축적 (전략 결과)
try:
    from app.services.kb_updater import save_strategy_to_kb
    await save_strategy_to_kb(
        org_id=state.get("org_id", ""),
        proposal_id=state.get("project_id", ""),
        client_name=rfp_dict.get("client", ""),
        positioning=positioning,
        strategy_result=result,
    )
except Exception as e:
    logger.debug(f"전략 KB 축적 실패 (무시): {e}")
```

---

## 2. Phase B — 검색 품질 개선

### 2-1. DB 마이그레이션 — capabilities 임베딩

**파일**: `database/migrations/012_kb_enhancement.sql`

```sql
-- capabilities 테이블에 임베딩 컬럼 추가
ALTER TABLE capabilities
  ADD COLUMN IF NOT EXISTS embedding vector(1536);

-- IVFFlat 인덱스 (cosine similarity)
CREATE INDEX IF NOT EXISTS idx_capabilities_embedding
  ON capabilities USING ivfflat (embedding vector_cosine_ops)
  WITH (lists = 50);

-- 시맨틱 검색 RPC
CREATE OR REPLACE FUNCTION search_capabilities_by_embedding(
  query_embedding vector(1536),
  match_org_id UUID,
  match_count INT DEFAULT 5
)
RETURNS TABLE (
  id UUID,
  type TEXT,
  title TEXT,
  detail TEXT,
  keywords TEXT[],
  similarity FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
  RETURN QUERY
  SELECT
    c.id, c.type, c.title, c.detail, c.keywords,
    1 - (c.embedding <=> query_embedding) AS similarity
  FROM capabilities c
  WHERE c.org_id = match_org_id
    AND c.embedding IS NOT NULL
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
```

### 2-2. `_search_capabilities()` 시맨틱 전환

**파일**: `app/services/knowledge_search.py`

**변경 전** (L177-189):
```python
async def _search_capabilities(query: str, org_id: str, top_k: int) -> list[dict]:
    client = await get_async_client()
    result = await client.table("capabilities").select(
        "id, description, tech_area, track_record, keywords"
    ).eq("org_id", org_id).ilike("description", f"%{query}%").limit(top_k).execute()
    return result.data or []
```

**변경 후**:
```python
async def _search_capabilities(
    query: str,
    embedding: list[float],
    org_id: str,
    top_k: int,
) -> list[dict]:
    """역량 DB 시맨틱 검색 (B-1: 임베딩 적용)."""
    client = await get_async_client()
    try:
        result = await client.rpc("search_capabilities_by_embedding", {
            "query_embedding": embedding,
            "match_org_id": org_id,
            "match_count": top_k,
        }).execute()
        items = result.data or []
        for item in items:
            item["match_type"] = "semantic"
        return items
    except Exception:
        logger.info("search_capabilities_by_embedding RPC 미등록, 키워드 검색 폴백")
        result = await client.table("capabilities").select(
            "id, type, title, detail, keywords"
        ).eq("org_id", org_id).or_(
            f"title.ilike.%{query}%,detail.ilike.%{query}%"
        ).limit(top_k).execute()
        items = result.data or []
        for item in items:
            item["match_type"] = "keyword"
        return items
```

**호출부 변경** (L49):
```python
# 변경 전
tasks["capability"] = _search_capabilities(query, org_id, top_k)
# 변경 후
tasks["capability"] = _search_capabilities(query, query_embedding, org_id, top_k)
```

### 2-3. 키워드 폴백 개선

**파일**: `app/services/knowledge_search.py`

#### content 폴백 (L88 부근)
```python
# 변경 전
).ilike("title", f"%{query}%").limit(top_k).execute()
# 변경 후
).or_(f"title.ilike.%{query}%,body.ilike.%{query}%").limit(top_k).execute()
```

#### lesson 폴백 (L171 부근)
```python
# 변경 전
).eq("org_id", org_id).limit(top_k).execute()
# 변경 후
).eq("org_id", org_id).or_(
    f"strategy_summary.ilike.%{query}%,"
    f"effective_points.ilike.%{query}%,"
    f"weak_points.ilike.%{query}%"
).limit(top_k).execute()
```

#### match_type 표시 (모든 검색 함수)

각 `_search_*` 함수의 결과에 `match_type` 필드 추가:
- 시맨틱 성공: `"semantic"`
- 키워드 폴백: `"keyword"`

### 2-4. 하이브리드 랭킹

**파일**: `app/services/knowledge_search.py`

`unified_search()` 내부, `return grouped` 직전에 랭킹 적용:

```python
def _apply_hybrid_ranking(items: list[dict]) -> list[dict]:
    """content 영역에 하이브리드 랭킹 적용.

    final_score = similarity × 0.5 + quality_score × 0.3 + freshness × 0.2
    """
    from datetime import datetime, timezone

    now = datetime.now(timezone.utc)
    for item in items:
        sim = item.get("similarity") or 0.0
        quality = (item.get("quality_score") or 0.0) / 100.0  # 0~1 정규화
        # freshness: 6개월 이내 = 1.0, 이후 감쇠
        updated = item.get("updated_at", "")
        try:
            if updated:
                dt = datetime.fromisoformat(str(updated).replace("Z", "+00:00"))
                days = (now - dt).days
                freshness = max(0, 1.0 - max(0, days - 180) * 0.005)
            else:
                freshness = 0.5
        except (ValueError, TypeError):
            freshness = 0.5

        item["_rank_score"] = sim * 0.5 + quality * 0.3 + freshness * 0.2

    return sorted(items, key=lambda x: x.get("_rank_score", 0), reverse=True)
```

**적용 위치** (`unified_search()` 내부):
```python
# content 영역에만 랭킹 적용
if "content" in grouped and grouped["content"]:
    grouped["content"] = _apply_hybrid_ranking(grouped["content"])
```

---

## 3. Phase C — 활용도 강화

### 3-1. `find_similar_cases()` — 유사 과거 사례 매칭

**파일**: `app/graph/context_helpers.py`

```python
async def find_similar_cases(
    project_name: str,
    client_name: str,
    org_id: str,
    top_k: int = 3,
) -> str:
    """RFP 사업명 기반 유사 과거 사례 시맨틱 검색 → 텍스트 반환."""
    try:
        from app.services.knowledge_search import unified_search
        results = await unified_search(
            query=f"{project_name} {client_name}",
            org_id=org_id,
            filters={"areas": ["lesson"]},
            top_k=top_k,
        )
        lessons = results.get("lesson", [])
        if not lessons:
            return ""

        parts = []
        for ls in lessons:
            r = "수주" if ls.get("result") == "won" else "패찰"
            parts.append(
                f"- [{r}] {ls.get('title', ls.get('strategy_summary', '')[:60])}"
                f" (포지셔닝: {ls.get('positioning', '-')})"
                f" — 강점: {ls.get('effective_points', '-')[:80]},"
                f" 약점: {ls.get('weak_points', '-')[:80]}"
            )
        return "\n\n## 유사 과거 사례 (시맨틱 매칭 top {top_k})\n".format(top_k=top_k) + "\n".join(parts)
    except Exception as e:
        logger.debug(f"유사 사례 검색 실패: {e}")
        return ""
```

### 3-2. `go_no_go` 노드에 유사 사례 주입

**파일**: `app/graph/nodes/go_no_go.py`

KB 조회 블록(L36~47) 이후, `pricing_context` 블록 이전에 추가:

```python
    # 유사 과거 사례 시맨틱 매칭 (C-1)
    similar_cases_text = ""
    if mode == "full":
        from app.graph.context_helpers import find_similar_cases
        similar_cases_text = await find_similar_cases(
            project_name=rfp_dict.get("project_name", ""),
            client_name=rfp_dict.get("client", ""),
            org_id=state.get("org_id", ""),
        )
```

프롬프트에 주입 (L111 `{pricing_context}` 이전):
```
{similar_cases_text}
```

### 3-3. `strategy_generate` 노드에 과거 전략 참조

**파일**: `app/graph/nodes/strategy_generate.py`

KB 조회 블록(L52~60) 이후 추가:

```python
    # 과거 전략 레코드 조회 (C-2)
    past_strategy_text = ""
    try:
        from app.utils.supabase_client import get_async_client as _get_db
        db = await _get_db()
        past = await (
            db.table("content_library")
            .select("title, body, tags")
            .eq("type", "strategy_record")
            .ilike("title", f"%{rfp_dict.get('client', '')}%")
            .order("created_at", desc=True)
            .limit(2)
            .execute()
        )
        if past.data:
            parts = []
            for p in past.data:
                parts.append(f"- {p['title']}\n  {(p.get('body') or '')[:300]}")
            past_strategy_text = "\n\n## 과거 전략 레코드 (이 발주기관)\n" + "\n".join(parts)
    except Exception:
        pass
```

프롬프트 `{pricing_strategy_context}` 앞에 `{past_strategy_text}` 삽입:
```python
    if past_strategy_text:
        prompt += past_strategy_text
```

### 3-4. `proposal_write_next` 유사 콘텐츠 주입

**파일**: `app/graph/nodes/proposal_nodes.py`

`_build_context()` 내부, `return` 직전 (L171 부근)에 추가:

```python
    # 유사 콘텐츠 자동 추천 (C-3)
    reference_content = ""
    try:
        from app.services.content_library import suggest_content_for_section
        suggestions = await suggest_content_for_section(
            section_topic=f"{section_id} {section_type}",
            org_id=state.get("org_id", ""),
            top_k=3,
        )
        if suggestions:
            parts = []
            for s in suggestions[:3]:
                excerpt = (s.get("body_excerpt") or s.get("body", ""))[:300]
                score = s.get("quality_score", 0)
                parts.append(f"- [{score}점] {s.get('title', '')}: {excerpt}")
            reference_content = "\n\n## 참고 콘텐츠 (KB 유사 콘텐츠, 참고하되 그대로 복사 금지)\n" + "\n".join(parts)
    except Exception:
        pass
```

`return` dict에 추가:
```python
    "reference_content": reference_content,
```

**프롬프트 반영**: `section_prompts.py`의 각 프롬프트 마지막에 `{reference_content}` 변수 추가.

### 3-5. `plan_story` KB 참조

**파일**: `app/graph/nodes/plan_nodes.py`

`plan_story()` 함수 내부, evidence_candidates 생성 후 추가:

```python
    # KB 유사 콘텐츠 보강 (C-4)
    try:
        from app.services.content_library import suggest_content_for_section
        rfp_dict = rfp_to_dict(state.get("rfp_analysis"))
        suggestions = await suggest_content_for_section(
            section_topic=rfp_dict.get("project_name", ""),
            org_id=state.get("org_id", ""),
            top_k=5,
        )
        if suggestions:
            kb_evidence = "\n\n과거 수주 제안서 참고 콘텐츠:\n"
            for s in suggestions[:5]:
                kb_evidence += f"- {s.get('title', '')}: {(s.get('body_excerpt') or '')[:200]}\n"
            evidence_text += kb_evidence
    except Exception:
        pass
```

---

## 4. Phase D — 관리 UX 개선

### 4-1. `GET /api/kb/health` — 건강도 대시보드

**파일**: `app/api/routes_kb.py`

```python
@router.get("/kb/health")
async def kb_health(user=Depends(get_current_user)):
    """KB 건강도 현황: 영역별 건수, 임베딩 커버리지, 평균 품질."""
    client = await get_async_client()
    org_id = user["org_id"]

    areas = {
        "content": {"table": "content_library", "embedding_col": "embedding", "quality_col": "quality_score"},
        "client": {"table": "client_intelligence", "embedding_col": "embedding", "quality_col": None},
        "competitor": {"table": "competitors", "embedding_col": "embedding", "quality_col": None},
        "lesson": {"table": "lessons_learned", "embedding_col": "embedding", "quality_col": None},
        "capability": {"table": "capabilities", "embedding_col": "embedding", "quality_col": None},
        "qa": {"table": "presentation_qa", "embedding_col": "embedding", "quality_col": None},
    }

    result = {}
    for area, cfg in areas.items():
        # total
        total_res = await client.table(cfg["table"]).select("id", count="exact").eq("org_id", org_id).execute()
        total = total_res.count or 0

        # with_embedding (embedding IS NOT NULL)
        embed_res = await client.rpc("count_with_embedding", {
            "table_name": cfg["table"],
            "org": org_id,
        }).execute()
        with_embed = embed_res.data if isinstance(embed_res.data, int) else 0

        coverage = round(with_embed / total * 100, 1) if total > 0 else 0

        entry = {"total": total, "with_embedding": with_embed, "coverage": coverage}

        # avg_quality (content만)
        if cfg["quality_col"]:
            avg_res = await client.rpc("avg_quality_score", {"org": org_id}).execute()
            entry["avg_quality"] = round(avg_res.data or 0, 1)

        result[area] = entry

    return result
```

### 4-2. `POST /api/kb/reindex` — 일괄 임베딩 생성

**파일**: `app/api/routes_kb.py`, `app/services/embedding_service.py`

```python
async def batch_reindex(
    areas: list[str],
    org_id: str,
    batch_size: int = 50,
) -> dict:
    """임베딩 없는 레코드에 대해 배치 임베딩 생성."""
```

**로직**:
1. 지정 영역의 `embedding IS NULL` 레코드 조회
2. `batch_size` 단위로 텍스트 조합 → `generate_embeddings_batch()`
3. 결과를 DB 업데이트
4. 반환: `{"total": int, "processed": int, "failed": int}`

**영역별 텍스트 조합 함수**:
- content: `embedding_text_for_content(title, body, tags)`
- capability: `f"{type} | {title} | {detail}"`
- client: `embedding_text_for_client(client_name, client_type, notes)`
- competitor: `embedding_text_for_competitor(company_name, primary_area, strengths)`
- lesson: `embedding_text_for_lesson(strategy_summary, effective_points, weak_points, industry)`

### 4-3. `GET /api/kb/content/duplicates` — 중복 탐지

**파일**: `app/services/content_library.py`

```python
async def find_duplicates(
    org_id: str,
    threshold: float = 0.9,
    limit: int = 20,
) -> list[dict]:
    """코사인 유사도 기준 중복 콘텐츠 쌍 검출."""
```

**로직**:
1. `content_library`에서 `org_id` + `embedding IS NOT NULL` 레코드 조회
2. DB-side RPC `find_content_duplicates(org_id, threshold, limit)`:
   ```sql
   SELECT a.id AS id_a, b.id AS id_b,
          a.title AS title_a, b.title AS title_b,
          1 - (a.embedding <=> b.embedding) AS similarity
   FROM content_library a
   JOIN content_library b ON a.id < b.id AND a.org_id = b.org_id
   WHERE a.org_id = match_org_id
     AND 1 - (a.embedding <=> b.embedding) > threshold
   ORDER BY similarity DESC
   LIMIT match_limit;
   ```
3. 반환: `[{"id_a": str, "title_a": str, "id_b": str, "title_b": str, "similarity": float}]`

### 4-4. 프론트엔드 KB 건강도 위젯

**파일**: `frontend/lib/api.ts`

```typescript
export interface KbHealthArea {
  total: number;
  with_embedding: number;
  coverage: number;
  avg_quality?: number;
}

export type KbHealthResponse = Record<string, KbHealthArea>;

// api.kb 객체에 추가
health: () => fetchApi<KbHealthResponse>("/kb/health"),
reindex: (areas: string[]) => fetchApi<{ total: number; processed: number; failed: number }>("/kb/reindex", { method: "POST", body: JSON.stringify({ areas }) }),
duplicates: (threshold?: number) => fetchApi<Array<{ id_a: string; title_a: string; id_b: string; title_b: string; similarity: number }>>(`/kb/content/duplicates?threshold=${threshold || 0.9}`),
```

**파일**: `frontend/app/(app)/kb/search/page.tsx`

KB 검색 페이지 상단에 건강도 요약 위젯 추가:
- 6개 영역 바: total 건수 + 커버리지(%) 프로그레스 바
- content 영역: 평균 품질 점수 표시
- 전체 임베딩 커버리지 비율 표시
- "재인덱싱" 버튼 (커버리지 < 90% 영역에 표시)

---

## 5. 수정 파일 요약

| # | 파일 | Phase | 변경 | 라인 |
|---|------|:-----:|------|:----:|
| 1 | `app/services/content_library.py` | A,D | `auto_register_section()` + `find_duplicates()` | +70 |
| 2 | `app/services/kb_updater.py` | A | `save_research_to_kb()` + `save_strategy_to_kb()` | +65 |
| 3 | `app/graph/nodes/proposal_nodes.py` | A,C | 섹션 KB 축적 + 유사 콘텐츠 주입 | +30 |
| 4 | `app/graph/nodes/research_gather.py` | A | KB 축적 호출 | +10 |
| 5 | `app/graph/nodes/strategy_generate.py` | A,C | KB 축적 + 과거 전략 참조 | +25 |
| 6 | `database/migrations/012_kb_enhancement.sql` | B | capabilities embedding + 2 RPC | +55 |
| 7 | `app/services/knowledge_search.py` | B | 시맨틱 전환 + 폴백 개선 + 랭킹 | +60 (수정) |
| 8 | `app/graph/context_helpers.py` | C | `find_similar_cases()` | +30 |
| 9 | `app/graph/nodes/go_no_go.py` | C | 유사 사례 프롬프트 주입 | +10 |
| 10 | `app/graph/nodes/plan_nodes.py` | C | KB 콘텐츠 보강 | +15 |
| 11 | `app/api/routes_kb.py` | D | health + reindex + duplicates 3개 API | +100 |
| 12 | `app/services/embedding_service.py` | D | `batch_reindex()` | +40 |
| 13 | `frontend/lib/api.ts` | D | KbHealth 타입 + 3 API | +15 |
| 14 | `frontend/app/(app)/kb/search/page.tsx` | D | 건강도 위젯 | +60 |
| **합계** | | | | **~585줄** |

## 6. 구현 순서

```
Phase A — 자동 축적
  Step 1: content_library.py    — auto_register_section()
  Step 2: kb_updater.py         — save_research_to_kb(), save_strategy_to_kb()
  Step 3: proposal_nodes.py     — 섹션 완료 시 KB 축적 호출
  Step 4: research_gather.py    — 리서치 결과 KB 저장
  Step 5: strategy_generate.py  — 전략 결과 KB 저장

Phase B — 검색 개선
  Step 6: 012_kb_enhancement.sql — capabilities embedding + RPC
  Step 7: knowledge_search.py   — 시맨틱 전환 + 폴백 + 랭킹

Phase C — 활용 강화
  Step 8: context_helpers.py    — find_similar_cases()
  Step 9: go_no_go.py           — 유사 사례 주입
  Step 10: strategy_generate.py — 과거 전략 참조 주입
  Step 11: proposal_nodes.py    — 유사 콘텐츠 주입
  Step 12: plan_nodes.py        — KB 콘텐츠 보강

Phase D — 관리 UX
  Step 13: embedding_service.py — batch_reindex()
  Step 14: routes_kb.py         — 3개 API (health, reindex, duplicates)
  Step 15: api.ts               — 타입 + API
  Step 16: kb/search/page.tsx   — 건강도 위젯
```

## 7. 검증 항목

| # | Phase | 검증 | 기대 결과 |
|---|:-----:|------|----------|
| V1 | A | `proposal_write_next` 실행 후 `content_library` 조회 | 500자+ 섹션이 `draft`/`section_block`으로 등록, 임베딩 존재 |
| V2 | A | 500자 미만 섹션 | 등록 안 됨 (스킵) |
| V3 | A | 동일 제안서 rewrite | upsert (중복 없음) |
| V4 | A | `research_gather` 후 KB 조회 | `research_data` 타입 저장, high/medium만 |
| V5 | A | `strategy_generate` 후 KB 조회 | `strategy_record` 타입 저장 |
| V6 | B | capabilities 시맨틱 검색 (RPC 존재 시) | similarity 기반 정렬 결과 |
| V7 | B | capabilities 시맨틱 검색 (RPC 미존재 시) | title+detail 키워드 폴백 |
| V8 | B | content 키워드 폴백 | body ILIKE도 검색됨 |
| V9 | B | lesson 키워드 폴백 | strategy_summary, effective_points, weak_points 검색됨 |
| V10 | B | 하이브리드 랭킹 | quality_score 높은 콘텐츠가 상위 |
| V11 | C | Go/No-Go 프롬프트 | "유사 과거 사례" 섹션 포함 |
| V12 | C | strategy_generate 프롬프트 | "과거 전략 레코드" 섹션 포함 |
| V13 | C | proposal_write_next 프롬프트 | "참고 콘텐츠" 섹션 포함 |
| V14 | D | `GET /api/kb/health` | 6개 영역별 건수+커버리지 |
| V15 | D | `POST /api/kb/reindex` | 임베딩 없는 레코드에 임베딩 생성 |
| V16 | D | `GET /api/kb/content/duplicates` | 유사도 90%+ 쌍 반환 |
| V17 | D | TypeScript 빌드 | 에러 0건 |
