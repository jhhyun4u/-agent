# 갭 분석 MEDIUM 항목 보완 (§28)

> **소속**: proposal-agent-v1 설계 문서 v3.5
> **관련 파일**: [15a-gap-high-archive.md](15a-gap-high-archive.md)
> **원본 섹션**: §28

---

## 28. ★ 갭 분석 MEDIUM 항목 보완 설계 (v3.1)

> **아키텍처 결정 (v3.1)**: Pattern A(모놀리식 StateGraph) + LangGraph `Send()` 병렬처리 유지 확정.
> 근거: ① 구조화된 순차 프로세스(RFP→전략→작성→검증)에 적합, ② 토큰 비용 효율(~80K vs ~200K),
> ③ 단일 상태로 Compliance Matrix 추적 용이, ④ 소규모 팀 운영 부담 최소화.
>
> 갭 분석 MEDIUM 심각도 12건을 아래에서 설계 보완합니다.

### 28-1. OB-05a: 콘텐츠 라이브러리 초기 시딩 (DOCX 자동 추출)

> **목적**: 기존 제안서(DOCX 파일)에서 섹션별 콘텐츠를 자동 추출하여 콘텐츠 라이브러리에 시딩.

#### API 엔드포인트

```python
# app/api/routes_onboarding.py

@router.post("/api/onboarding/seed-content")
async def seed_content_from_docx(
    files: list[UploadFile] = File(...),
    user: dict = Depends(require_role("admin", "lead")),
):
    """
    OB-05a: DOCX 파일에서 섹션 자동 추출 → 콘텐츠 라이브러리 초기 시딩.
    - 최대 10개 파일, 파일당 50MB 이하
    - 제목 스타일(Heading 1~3) 기준으로 섹션 분리
    """
    results = []
    for file in files[:10]:
        validate_file(file, allowed_types=["docx"], max_size_mb=50)
        sections = await extract_sections_from_docx(file)
        seeded = []
        for section in sections:
            content_id = await insert_content_library(
                org_id=user["org_id"],
                type="proposal_section",
                title=section["heading"],
                body=section["body"],
                source_file=file.filename,
                tags=section.get("tags", []),
                status="draft",  # 관리자 검토 후 게시
            )
            # 임베딩 생성
            embedding = await embedding_service.generate(
                f"{section['heading']}\n{section['body'][:2000]}"
            )
            await update_content_embedding(content_id, embedding)
            seeded.append({"id": content_id, "title": section["heading"]})
        results.append({"file": file.filename, "sections_extracted": len(seeded), "items": seeded})
    return {"seeded_files": len(results), "details": results}
```

#### DOCX 섹션 추출 서비스

```python
# app/services/docx_extractor.py

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH

async def extract_sections_from_docx(file: UploadFile) -> list[dict]:
    """
    DOCX 파일의 Heading 스타일을 기준으로 섹션 분리.
    - Heading 1~3: 새 섹션 시작
    - 본문 단락: 현재 섹션에 누적
    - 표: '[표: N행×M열]' 형태로 텍스트 변환 후 포함
    """
    doc = Document(await file.read())
    sections = []
    current_heading = None
    current_body = []

    for para in doc.paragraphs:
        style_name = para.style.name.lower()
        if style_name.startswith("heading"):
            # 이전 섹션 저장
            if current_heading and current_body:
                sections.append({
                    "heading": current_heading,
                    "body": "\n".join(current_body).strip(),
                    "tags": _infer_tags(current_heading),
                })
            current_heading = para.text.strip()
            current_body = []
        elif current_heading:
            if para.text.strip():
                current_body.append(para.text.strip())

    # 마지막 섹션
    if current_heading and current_body:
        sections.append({
            "heading": current_heading,
            "body": "\n".join(current_body).strip(),
            "tags": _infer_tags(current_heading),
        })

    return sections

def _infer_tags(heading: str) -> list[str]:
    """제목 키워드 기반 자동 태그 추론."""
    tag_keywords = {
        "사업이해": ["사업이해", "understanding"],
        "수행방법": ["수행방법", "methodology"],
        "수행체계": ["수행체계", "organization"],
        "일정": ["일정", "schedule"],
        "보안": ["보안", "security"],
        "인력": ["인력", "team"],
    }
    tags = []
    for tag, keywords in tag_keywords.items():
        if any(kw in heading for kw in keywords):
            tags.append(tag)
    return tags or ["general"]
```

### 28-2. CL-10: 오래된 콘텐츠 감지 (6개월 미갱신 알림)

> **목적**: 6개월 이상 미갱신된 콘텐츠를 감지하여 담당자에게 갱신 알림 발송.

```python
# app/services/scheduled_monitor.py 에 추가

async def detect_stale_content():
    """
    CL-10: 6개월 미갱신 콘텐츠 감지 → 팀장/작성자에게 알림.
    매주 월요일 09:00 실행.
    """
    from datetime import datetime, timezone, timedelta

    stale_threshold = datetime.now(timezone.utc) - timedelta(days=180)

    stale_items = await supabase.table("content_library") \
        .select("id, title, org_id, created_by, updated_at, type, tags") \
        .eq("status", "published") \
        .lt("updated_at", stale_threshold.isoformat()) \
        .execute()

    for item in stale_items.data:
        # 중복 알림 방지: 최근 30일 이내 동일 알림 확인
        recent_notification = await supabase.table("notifications") \
            .select("id") \
            .eq("type", "stale_content") \
            .eq("reference_id", item["id"]) \
            .gt("created_at", (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()) \
            .limit(1) \
            .execute()

        if recent_notification.data:
            continue

        # 작성자에게 알림
        await create_notification(
            user_id=item["created_by"],
            type="stale_content",
            reference_id=item["id"],
            title=f"📋 콘텐츠 갱신 필요: {item['title'][:40]}",
            body=f"마지막 수정일: {item['updated_at'][:10]}. 6개월 이상 경과되어 갱신을 권장합니다.",
        )

    logger.info("stale_content_check", stale_count=len(stale_items.data))

# 매주 월요일 09:00 실행
scheduler.add_job(detect_stale_content, "cron", day_of_week="mon", hour=9, minute=0)
```

### 28-3. CL-11: 콘텐츠 갭 분석

> **목적**: 최근 제안서에서 자주 요청되었으나 콘텐츠 라이브러리에 없는 영역을 자동 식별.

```python
# app/services/content_gap_analyzer.py

import structlog
from collections import Counter

logger = structlog.get_logger()

async def analyze_content_gaps(org_id: str) -> dict:
    """
    CL-11: 콘텐츠 갭 분석.
    최근 6개월 제안서에서 AI가 참조 시도했으나 KB에서 찾지 못한 영역 분석.

    데이터 소스:
    1. ai_task_logs에서 kb_miss_tags (KB 검색 실패 태그 기록)
    2. 자가진단 결과에서 grounding_ratio가 낮은 섹션
    3. 플레이스홀더 '[KB 데이터 필요:]' 빈도
    """
    from datetime import datetime, timezone, timedelta

    six_months_ago = (datetime.now(timezone.utc) - timedelta(days=180)).isoformat()

    # 1. KB miss 태그 수집
    miss_logs = await supabase.table("ai_task_logs") \
        .select("metadata") \
        .eq("org_id", org_id) \
        .gt("created_at", six_months_ago) \
        .not_.is_("metadata->>kb_miss_tags", "null") \
        .execute()

    miss_tags = []
    for log in miss_logs.data:
        tags = log.get("metadata", {}).get("kb_miss_tags", [])
        miss_tags.extend(tags)

    # 2. 플레이스홀더 빈도 분석
    placeholder_logs = await supabase.table("artifacts") \
        .select("content, section_id") \
        .eq("org_id", org_id) \
        .gt("created_at", six_months_ago) \
        .execute()

    placeholder_sections = []
    for artifact in placeholder_logs.data:
        if "[KB 데이터 필요:" in (artifact.get("content") or ""):
            placeholder_sections.append(artifact["section_id"])

    # 3. 갭 영역 집계 및 정렬
    gap_counter = Counter(miss_tags + placeholder_sections)
    top_gaps = gap_counter.most_common(20)

    # 4. 기존 콘텐츠와 대조하여 순수 갭만 추출
    existing_tags = await supabase.table("content_library") \
        .select("tags") \
        .eq("org_id", org_id) \
        .eq("status", "published") \
        .execute()

    existing_tag_set = set()
    for item in existing_tags.data:
        existing_tag_set.update(item.get("tags") or [])

    pure_gaps = [
        {"area": tag, "request_count": count, "has_content": tag in existing_tag_set}
        for tag, count in top_gaps
    ]

    logger.info("content_gap_analysis", org_id=org_id, gap_count=len(pure_gaps))

    return {
        "total_misses": len(miss_tags),
        "top_gaps": pure_gaps,
        "recommendation": [
            g["area"] for g in pure_gaps
            if not g["has_content"] and g["request_count"] >= 3
        ],
    }
```

#### API 엔드포인트

```python
# app/api/routes_kb.py 에 추가

@router.get("/api/kb/content-gaps")
async def get_content_gaps(user: dict = Depends(require_role("admin", "lead"))):
    """CL-11: 콘텐츠 갭 분석 결과 조회."""
    return await analyze_content_gaps(user["org_id"])
```

#### DB 스키마 확장

```sql
-- ai_task_logs에 KB miss 태그 기록 지원
-- metadata JSONB 필드에 kb_miss_tags: string[] 포함
-- (이미 JSONB이므로 스키마 변경 불필요, 노드에서 기록 로직만 추가)

-- 예: node 실행 시 KB 검색 실패 기록
-- metadata: { "kb_miss_tags": ["보안관제실적", "클라우드마이그레이션"], "search_query": "..." }
```

### 28-4. CMP-06: 경쟁 빈도 자동 집계

> **목적**: competitor_history에서 경쟁 빈도를 자동 집계하여 경쟁사 프로필에 반영.

```sql
-- PostgreSQL 뷰: 경쟁사별 경쟁 빈도 자동 집계
CREATE OR REPLACE VIEW competitor_frequency AS
SELECT
    c.id AS competitor_id,
    c.name AS competitor_name,
    c.org_id,
    COUNT(ch.id) AS total_encounters,
    COUNT(ch.id) FILTER (WHERE ch.result = 'won') AS won_against,
    COUNT(ch.id) FILTER (WHERE ch.result = 'lost') AS lost_against,
    ROUND(
        COUNT(ch.id) FILTER (WHERE ch.result = 'won')::NUMERIC /
        NULLIF(COUNT(ch.id), 0) * 100, 1
    ) AS win_rate_pct,
    MAX(ch.created_at) AS last_encounter,
    -- 최근 12개월 빈도
    COUNT(ch.id) FILTER (
        WHERE ch.created_at > NOW() - INTERVAL '12 months'
    ) AS encounters_last_12m,
    -- 자주 경쟁하는 분야 (최빈값)
    MODE() WITHIN GROUP (ORDER BY ch.industry) AS primary_industry
FROM competitors c
LEFT JOIN competitor_history ch ON c.id = ch.competitor_id
GROUP BY c.id, c.name, c.org_id;

-- RLS: 조직 기반 필터
ALTER VIEW competitor_frequency OWNER TO authenticated;
CREATE POLICY "org_filter" ON competitor_frequency
    FOR SELECT USING (org_id = auth.jwt()->>'org_id');

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_competitor_history_created
    ON competitor_history(competitor_id, created_at DESC);
```

#### API 엔드포인트

```python
# app/api/routes_kb.py 에 추가

@router.get("/api/kb/competitors/{id}/frequency")
async def get_competitor_frequency(
    id: str,
    user: dict = Depends(get_current_user),
):
    """CMP-06: 경쟁사 경쟁 빈도 조회."""
    result = await supabase.table("competitor_frequency") \
        .select("*") \
        .eq("competitor_id", id) \
        .single() \
        .execute()
    return result.data

@router.get("/api/kb/competitors/frequency-ranking")
async def get_competitor_frequency_ranking(
    user: dict = Depends(get_current_user),
    limit: int = Query(default=10, le=50),
):
    """CMP-06: 경쟁사 빈도 순위 (상위 N개)."""
    result = await supabase.table("competitor_frequency") \
        .select("*") \
        .eq("org_id", user["org_id"]) \
        .order("total_encounters", desc=True) \
        .limit(limit) \
        .execute()
    return result.data
```

### 28-5. LRN-08: 포지셔닝 판단 정확도 검증 통계

> **목적**: AI가 추천한 포지셔닝(aggressive/moderate/conservative) vs 실제 수주 결과를 비교하여 정확도 통계를 산출.

```sql
-- 포지셔닝 정확도 분석 뷰
CREATE OR REPLACE VIEW positioning_accuracy AS
SELECT
    p.org_id,
    p.ai_positioning AS recommended_positioning,
    p.final_positioning AS actual_positioning,
    p.status AS result,
    -- AI 추천과 실제 선택 일치 여부
    CASE WHEN p.ai_positioning = p.final_positioning THEN TRUE ELSE FALSE END AS ai_adopted,
    -- 결과별 집계 (수주/패찰)
    CASE WHEN p.status = 'won' THEN 1 ELSE 0 END AS is_won,
    CASE WHEN p.status = 'lost' THEN 1 ELSE 0 END AS is_lost,
    p.created_at
FROM proposals p
WHERE p.status IN ('won', 'lost')
  AND p.ai_positioning IS NOT NULL;

-- 요약 통계 뷰
CREATE OR REPLACE VIEW positioning_accuracy_summary AS
SELECT
    org_id,
    recommended_positioning,
    COUNT(*) AS total_cases,
    SUM(is_won) AS won_count,
    SUM(is_lost) AS lost_count,
    ROUND(SUM(is_won)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 1) AS win_rate_pct,
    -- AI 추천 채택률
    COUNT(*) FILTER (WHERE ai_adopted) AS adopted_count,
    ROUND(
        COUNT(*) FILTER (WHERE ai_adopted)::NUMERIC / NULLIF(COUNT(*), 0) * 100, 1
    ) AS adoption_rate_pct,
    -- AI 추천 채택 시 수주율 vs 미채택 시 수주율
    ROUND(
        SUM(CASE WHEN ai_adopted AND is_won = 1 THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(COUNT(*) FILTER (WHERE ai_adopted), 0) * 100, 1
    ) AS adopted_win_rate_pct,
    ROUND(
        SUM(CASE WHEN NOT ai_adopted AND is_won = 1 THEN 1 ELSE 0 END)::NUMERIC /
        NULLIF(COUNT(*) FILTER (WHERE NOT ai_adopted), 0) * 100, 1
    ) AS non_adopted_win_rate_pct
FROM positioning_accuracy
GROUP BY org_id, recommended_positioning;
```

#### proposals 테이블 확장

```sql
-- AI 추천 포지셔닝 기록 컬럼 (기존 final_positioning과 별도)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS ai_positioning TEXT;
-- go_no_go 노드에서 AI가 추천한 포지셔닝을 여기에 저장
-- final_positioning은 Human 승인 후 확정된 포지셔닝
```

#### API 엔드포인트

```python
# app/api/routes_stats.py 에 추가

@router.get("/api/stats/positioning-accuracy")
async def get_positioning_accuracy(
    user: dict = Depends(require_role("admin", "lead")),
):
    """LRN-08: 포지셔닝 판단 정확도 통계."""
    result = await supabase.table("positioning_accuracy_summary") \
        .select("*") \
        .eq("org_id", user["org_id"]) \
        .execute()
    return {
        "summary": result.data,
        "insight": _generate_positioning_insight(result.data),
    }

def _generate_positioning_insight(data: list[dict]) -> str:
    """포지셔닝 정확도 인사이트 생성."""
    if not data:
        return "아직 충분한 데이터가 없습니다. 최소 10건의 수주/패찰 결과가 필요합니다."

    best = max(data, key=lambda x: x.get("win_rate_pct") or 0)
    return (
        f"가장 높은 수주율: {best['recommended_positioning']} "
        f"({best['win_rate_pct']}%, {best['total_cases']}건). "
        f"AI 추천 채택 시 수주율: {best.get('adopted_win_rate_pct', 'N/A')}%."
    )
```

### 28-6. KBS-07: 검색 이력 분석

> **목적**: KB 통합 검색 이력을 저장하고 자주 검색하는 패턴을 분석하여 콘텐츠 갭 발견 및 검색 개선에 활용.

#### DB 스키마

```sql
CREATE TABLE search_history (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id      UUID REFERENCES organizations(id) NOT NULL,
    user_id     UUID REFERENCES users(id) NOT NULL,
    query       TEXT NOT NULL,
    query_type  TEXT NOT NULL,             -- 'keyword' | 'semantic' | 'hybrid'
    filters     JSONB DEFAULT '{}',        -- 적용된 필터 (kb_types, tags, date_range 등)
    result_count INT DEFAULT 0,
    clicked_ids UUID[] DEFAULT '{}',       -- 사용자가 클릭한 결과 ID 목록
    source      TEXT DEFAULT 'manual',     -- 'manual' (사용자 검색) | 'ai_auto' (AI 자동 참조)
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_search_history_org ON search_history(org_id, created_at DESC);
CREATE INDEX idx_search_history_query ON search_history USING gin(to_tsvector('simple', query));

-- RLS
ALTER TABLE search_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "org_members" ON search_history
    FOR ALL USING (org_id = auth.jwt()->>'org_id');
```

#### 검색 패턴 분석 서비스

```python
# app/services/search_analytics.py

async def get_search_patterns(org_id: str, days: int = 90) -> dict:
    """
    KBS-07: 검색 패턴 분석.
    - 인기 검색어 Top 20
    - 결과 0건 검색어 (콘텐츠 갭 후보)
    - 시간대별 검색 빈도
    """
    from datetime import datetime, timezone, timedelta

    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()

    history = await supabase.table("search_history") \
        .select("query, result_count, source, created_at") \
        .eq("org_id", org_id) \
        .gt("created_at", since) \
        .execute()

    queries = [h["query"] for h in history.data]
    zero_result_queries = [h["query"] for h in history.data if h["result_count"] == 0]

    from collections import Counter
    return {
        "total_searches": len(history.data),
        "unique_queries": len(set(queries)),
        "top_queries": Counter(queries).most_common(20),
        "zero_result_queries": Counter(zero_result_queries).most_common(10),
        "ai_auto_ratio": sum(1 for h in history.data if h["source"] == "ai_auto") / max(len(history.data), 1),
    }
```

#### 통합 검색 함수에 이력 기록 추가

```python
# app/services/knowledge_search.py 수정 (기존 unified_search에 추가)

async def unified_search(query: str, user: dict, **filters) -> dict:
    """기존 통합 검색 + KBS-07 이력 기록."""
    results = await _do_search(query, user["org_id"], **filters)

    # 검색 이력 비동기 기록 (검색 성능에 영향 없도록)
    asyncio.create_task(
        insert_search_history(
            org_id=user["org_id"],
            user_id=user["id"],
            query=query,
            query_type=filters.get("search_type", "hybrid"),
            filters=filters,
            result_count=len(results.get("items", [])),
            source="manual",
        )
    )

    return results
```

### 28-7. COST-05~07: 월간 예산 상한 / 경고 / AI 정지

> **목적**: 조직별 월간 API 비용 예산을 설정하고, 임계값 초과 시 경고 및 AI 호출 자동 정지.

#### DB 스키마

```sql
-- 조직별 비용 예산 설정
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS monthly_budget_usd NUMERIC(10,2);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS budget_alert_threshold NUMERIC(3,2) DEFAULT 0.80;
-- budget_alert_threshold: 예산 대비 경고 비율 (기본 80%)

-- 월간 비용 집계 뷰
CREATE OR REPLACE VIEW monthly_cost_summary AS
SELECT
    org_id,
    DATE_TRUNC('month', created_at) AS month,
    SUM(input_tokens) AS total_input_tokens,
    SUM(output_tokens) AS total_output_tokens,
    SUM(cached_tokens) AS total_cached_tokens,
    SUM(cost_usd) AS total_cost_usd
FROM token_usage
GROUP BY org_id, DATE_TRUNC('month', created_at);
```

#### 비용 관리 서비스

```python
# app/services/budget_manager.py

import structlog
from decimal import Decimal

logger = structlog.get_logger()

class BudgetManager:
    """COST-05~07: 월간 API 비용 예산 관리."""

    async def check_budget(self, org_id: str) -> dict:
        """
        현재 월 비용을 예산과 비교.
        Returns: { "allowed": bool, "usage_pct": float, "status": str }
        """
        org = await get_organization(org_id)
        budget = org.get("monthly_budget_usd")

        if not budget:
            return {"allowed": True, "usage_pct": 0, "status": "no_budget_set"}

        current_cost = await self._get_current_month_cost(org_id)
        usage_pct = float(current_cost / Decimal(str(budget)) * 100) if budget > 0 else 0
        threshold = float(org.get("budget_alert_threshold", 0.80)) * 100

        status = "normal"
        if usage_pct >= 100:
            status = "exceeded"
        elif usage_pct >= threshold:
            status = "warning"

        return {
            "allowed": usage_pct < 100,
            "usage_pct": round(usage_pct, 1),
            "status": status,
            "current_cost_usd": float(current_cost),
            "budget_usd": float(budget),
        }

    async def enforce_budget(self, org_id: str) -> bool:
        """
        COST-07: AI 호출 전 예산 확인. 초과 시 False 반환.
        claude_client.py에서 매 호출 전 실행.
        """
        result = await self.check_budget(org_id)

        if result["status"] == "warning":
            # COST-06: 경고 알림 (중복 방지: 하루 1회)
            await self._send_budget_alert_if_needed(org_id, result)

        if result["status"] == "exceeded":
            # COST-07: AI 호출 정지
            logger.warning("budget_exceeded", org_id=org_id, **result)
            await self._send_budget_exceeded_alert(org_id, result)
            return False

        return True

    async def _get_current_month_cost(self, org_id: str) -> Decimal:
        from datetime import datetime, timezone
        first_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0)
        result = await supabase.table("token_usage") \
            .select("cost_usd") \
            .eq("org_id", org_id) \
            .gte("created_at", first_of_month.isoformat()) \
            .execute()
        return sum(Decimal(str(r["cost_usd"])) for r in result.data)

    async def _send_budget_alert_if_needed(self, org_id: str, result: dict):
        """하루 1회 중복 방지 경고."""
        from datetime import datetime, timezone, timedelta
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0)
        existing = await supabase.table("notifications") \
            .select("id") \
            .eq("type", "budget_warning") \
            .eq("org_id", org_id) \
            .gte("created_at", today_start.isoformat()) \
            .limit(1) \
            .execute()
        if not existing.data:
            admins = await get_org_admins(org_id)
            for admin in admins:
                await create_notification(
                    user_id=admin["id"],
                    type="budget_warning",
                    title=f"⚠️ API 비용 예산 {result['usage_pct']}% 도달",
                    body=f"현재 ${result['current_cost_usd']:.2f} / 예산 ${result['budget_usd']:.2f}",
                    org_id=org_id,
                )

    async def _send_budget_exceeded_alert(self, org_id: str, result: dict):
        """예산 초과 긴급 알림."""
        admins = await get_org_admins(org_id)
        for admin in admins:
            await create_notification(
                user_id=admin["id"],
                type="budget_exceeded",
                title="🚨 API 비용 예산 초과 — AI 호출 정지됨",
                body=f"현재 ${result['current_cost_usd']:.2f} / 예산 ${result['budget_usd']:.2f}. 관리자 설정에서 예산을 조정하거나 다음 달까지 대기하세요.",
                org_id=org_id,
            )

budget_manager = BudgetManager()
```

#### claude_client.py 통합

```python
# app/services/claude_client.py 수정 (기존 generate 함수에 예산 체크 추가)

async def claude_generate(prompt: str, org_id: str, **kwargs):
    """Claude API 호출 (COST-05~07 예산 체크 포함)."""
    # 예산 확인
    if not await budget_manager.enforce_budget(org_id):
        raise BudgetExceededError(
            "월간 API 비용 예산을 초과했습니다. 관리자에게 문의하세요."
        )

    response = await client.messages.create(...)
    # ... (기존 로직)
```

### 28-8. OPS-04~08: Claude API 장애 대응 및 운영 복원력

> **목적**: Claude API 장애 시 재시도·폴백·그레이스풀 디그레이데이션 전략과 운영 메트릭 수집.

#### 재시도 및 Circuit Breaker

```python
# app/services/api_resilience.py

import structlog
import asyncio
from datetime import datetime, timezone, timedelta
from enum import Enum

logger = structlog.get_logger()

class CircuitState(Enum):
    CLOSED = "closed"       # 정상
    OPEN = "open"           # 차단 (장애)
    HALF_OPEN = "half_open" # 시험 재개

class ClaudeCircuitBreaker:
    """
    OPS-04~05: Claude API Circuit Breaker.
    연속 실패 시 호출 차단, 일정 시간 후 시험 재개.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,     # 초
        half_open_max_calls: int = 2,
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0

    async def call(self, func, *args, **kwargs):
        """Circuit Breaker를 통한 API 호출."""
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.half_open_calls = 0
                logger.info("circuit_breaker_half_open")
            else:
                raise ServiceUnavailableError("Claude API 일시적 장애. 잠시 후 재시도하세요.")

        try:
            result = await self._retry_with_backoff(func, *args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    async def _retry_with_backoff(self, func, *args, max_retries=3, **kwargs):
        """OPS-04: 지수 백오프 재시도."""
        for attempt in range(max_retries):
            try:
                return await func(*args, **kwargs)
            except (httpx.TimeoutException, httpx.HTTPStatusError) as e:
                if attempt == max_retries - 1:
                    raise
                wait = min(2 ** attempt * 1.0, 30)  # 1s, 2s, 4s... max 30s
                logger.warning("claude_api_retry",
                    attempt=attempt + 1,
                    wait_seconds=wait,
                    error=str(e)[:100],
                )
                await asyncio.sleep(wait)

    def _on_success(self):
        self.failure_count = 0
        if self.state == CircuitState.HALF_OPEN:
            self.half_open_calls += 1
            if self.half_open_calls >= self.half_open_max_calls:
                self.state = CircuitState.CLOSED
                logger.info("circuit_breaker_closed")

    def _on_failure(self):
        self.failure_count += 1
        self.last_failure_time = datetime.now(timezone.utc)
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            logger.error("circuit_breaker_open", failure_count=self.failure_count)

    def _should_attempt_reset(self) -> bool:
        if self.last_failure_time is None:
            return True
        elapsed = (datetime.now(timezone.utc) - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

circuit_breaker = ClaudeCircuitBreaker()
```

#### Graceful Degradation (OPS-06)

```python
# app/services/degradation.py

DEGRADATION_RESPONSES = {
    "rfp_analyze": "⚠️ AI 분석이 일시적으로 불가합니다. RFP 문서는 업로드되었으며, AI 복구 후 자동으로 분석이 재개됩니다.",
    "strategy_generate": "⚠️ AI 전략 생성이 일시적으로 불가합니다. 수동으로 전략을 입력하거나, AI 복구를 기다려주세요.",
    "proposal_section": "⚠️ AI 섹션 생성이 일시적으로 불가합니다. 직접 작성 모드로 전환합니다.",
    "self_review": "⚠️ AI 자가진단이 일시적으로 불가합니다. 수동 검토를 진행해주세요.",
}

async def get_degradation_response(step: str) -> dict | None:
    """
    OPS-06: AI 장애 시 단계별 폴백 응답.
    None 반환 시 정상 처리, dict 반환 시 폴백 모드.
    """
    if circuit_breaker.state == CircuitState.OPEN:
        return {
            "status": "degraded",
            "message": DEGRADATION_RESPONSES.get(step, "⚠️ AI 기능이 일시적으로 불가합니다."),
            "manual_mode_available": True,
        }
    return None
```

#### 운영 메트릭 수집 (OPS-07~08)

```python
# app/services/metrics_collector.py

import structlog
from datetime import datetime, timezone

logger = structlog.get_logger()

class MetricsCollector:
    """OPS-07~08: 운영 메트릭 수집 및 에러 모니터링."""

    async def record_api_call(self, step: str, duration_ms: float, success: bool, tokens: dict):
        """API 호출 메트릭 기록."""
        await supabase.table("api_metrics").insert({
            "step": step,
            "duration_ms": duration_ms,
            "success": success,
            "input_tokens": tokens.get("input", 0),
            "output_tokens": tokens.get("output", 0),
            "cached_tokens": tokens.get("cached", 0),
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()

    async def record_error(self, step: str, error_type: str, detail: str):
        """에러 이벤트 기록."""
        await supabase.table("error_events").insert({
            "step": step,
            "error_type": error_type,
            "detail": detail[:500],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }).execute()
        logger.error("api_error", step=step, error_type=error_type)

metrics = MetricsCollector()
```

#### 메트릭 DB 스키마

```sql
CREATE TABLE api_metrics (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    step        TEXT NOT NULL,
    duration_ms NUMERIC(10,2),
    success     BOOLEAN NOT NULL DEFAULT TRUE,
    input_tokens INT DEFAULT 0,
    output_tokens INT DEFAULT 0,
    cached_tokens INT DEFAULT 0,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE error_events (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    step        TEXT NOT NULL,
    error_type  TEXT NOT NULL,
    detail      TEXT,
    resolved    BOOLEAN DEFAULT FALSE,
    created_at  TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_api_metrics_step ON api_metrics(step, created_at DESC);
CREATE INDEX idx_error_events_unresolved ON error_events(resolved, created_at DESC) WHERE NOT resolved;
```

#### 메트릭 대시보드 API

```python
# app/api/routes_stats.py 에 추가

@router.get("/api/stats/api-health")
async def get_api_health_stats(
    user: dict = Depends(require_role("admin")),
    hours: int = Query(default=24, le=168),
):
    """OPS-07: API 상태 메트릭 대시보드."""
    from datetime import datetime, timezone, timedelta
    since = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()

    metrics_data = await supabase.table("api_metrics") \
        .select("step, duration_ms, success") \
        .gte("created_at", since) \
        .execute()

    errors = await supabase.table("error_events") \
        .select("step, error_type, created_at") \
        .gte("created_at", since) \
        .execute()

    return {
        "period_hours": hours,
        "total_calls": len(metrics_data.data),
        "success_rate": sum(1 for m in metrics_data.data if m["success"]) / max(len(metrics_data.data), 1) * 100,
        "avg_duration_ms": sum(m["duration_ms"] for m in metrics_data.data) / max(len(metrics_data.data), 1),
        "error_count": len(errors.data),
        "circuit_breaker_state": circuit_breaker.state.value,
    }
```

### 28-9. RET-01~05: 데이터 보존 및 삭제 정책

> **목적**: 데이터 유형별 보존 기간 정의, 자동 아카이브, soft delete, 물리 삭제 스케줄.

#### 보존 정책 정의

```python
# app/config.py 에 추가

DATA_RETENTION_POLICIES = {
    # RET-01: 제안 프로젝트 데이터
    "proposals": {
        "active_retention_years": 5,       # 활성 보존 5년
        "archive_after_years": 3,          # 3년 후 아카이브
        "hard_delete_after_years": 7,      # 7년 후 물리 삭제
    },
    # RET-02: 산출물 (제안서, PPT 등)
    "artifacts": {
        "active_retention_years": 5,
        "archive_after_years": 3,
        "hard_delete_after_years": 7,
    },
    # RET-03: 감사 로그
    "audit_logs": {
        "active_retention_years": 5,
        "archive_after_years": 5,
        "hard_delete_after_years": 10,     # 법적 보존 기간 고려
    },
    # RET-04: AI 작업 로그 / 토큰 사용 로그
    "ai_task_logs": {
        "active_retention_years": 3,
        "archive_after_years": 1,
        "hard_delete_after_years": 5,
    },
    "token_usage": {
        "active_retention_years": 3,
        "archive_after_years": 1,
        "hard_delete_after_years": 5,
    },
    # RET-05: 알림
    "notifications": {
        "active_retention_years": 1,
        "archive_after_years": 0.5,        # 6개월 후 아카이브
        "hard_delete_after_years": 2,
    },
}
```

#### 자동 아카이브 / 삭제 스케줄러

```python
# app/services/data_retention.py

import structlog
from datetime import datetime, timezone, timedelta
from app.config import DATA_RETENTION_POLICIES

logger = structlog.get_logger()

async def run_retention_policies():
    """
    RET-01~05: 데이터 보존 정책 실행.
    매월 1일 02:00 실행.

    단계:
    1. archive_after 경과 데이터 → archived=true 마킹 (soft archive)
    2. hard_delete_after 경과 + archived 데이터 → 물리 삭제
    3. Supabase Storage의 연관 파일도 함께 처리
    """
    for table_name, policy in DATA_RETENTION_POLICIES.items():
        archive_threshold = datetime.now(timezone.utc) - timedelta(
            days=policy["archive_after_years"] * 365
        )
        delete_threshold = datetime.now(timezone.utc) - timedelta(
            days=policy["hard_delete_after_years"] * 365
        )

        # 1. 아카이브 (soft)
        archive_result = await supabase.table(table_name) \
            .update({"archived": True}) \
            .eq("archived", False) \
            .lt("created_at", archive_threshold.isoformat()) \
            .execute()

        archived_count = len(archive_result.data) if archive_result.data else 0

        # 2. 물리 삭제 (아카이브 후 보존 기간 초과)
        delete_result = await supabase.table(table_name) \
            .delete() \
            .eq("archived", True) \
            .lt("created_at", delete_threshold.isoformat()) \
            .execute()

        deleted_count = len(delete_result.data) if delete_result.data else 0

        if archived_count > 0 or deleted_count > 0:
            logger.info("retention_policy_executed",
                table=table_name,
                archived=archived_count,
                deleted=deleted_count,
            )

            await insert_audit_log(
                action="retention_policy",
                resource_type=table_name,
                detail={
                    "archived": archived_count,
                    "deleted": deleted_count,
                    "archive_threshold": archive_threshold.isoformat(),
                    "delete_threshold": delete_threshold.isoformat(),
                },
            )

# 매월 1일 02:00 실행
scheduler.add_job(run_retention_policies, "cron", day=1, hour=2, minute=0)
```

#### DB 스키마 확장

```sql
-- 아카이브 지원 컬럼 추가 (대상 테이블별)
ALTER TABLE proposals ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;
ALTER TABLE artifacts ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;
ALTER TABLE audit_logs ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;
ALTER TABLE ai_task_logs ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;
ALTER TABLE token_usage ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;
ALTER TABLE notifications ADD COLUMN IF NOT EXISTS archived BOOLEAN DEFAULT FALSE;

-- 아카이브 데이터 파티셔닝 인덱스
CREATE INDEX idx_proposals_archived ON proposals(archived, created_at) WHERE archived = TRUE;
CREATE INDEX idx_audit_logs_archived ON audit_logs(archived, created_at) WHERE archived = TRUE;
```

### 28-10. NFR-18~20: 브라우저 호환성 / WCAG 접근성 / 반응형 설계

> **목적**: 프론트엔드 비기능 요구사항 — 지원 브라우저, 접근성 표준, 반응형 설계 가이드라인.

#### NFR-18: 브라우저 호환성

```
지원 브라우저 (데스크톱 우선):
- Chrome 120+ (주 대상)
- Microsoft Edge 120+ (Chromium 기반)
- Firefox 120+ (호환성 테스트)
- Safari 17+ (macOS 사용자 대응)

비지원:
- Internet Explorer (전체)
- 모바일 브라우저 (Phase 2 대응 예정)

구현 가이드:
- Next.js browserslist 설정: "last 2 Chrome versions, last 2 Edge versions, last 2 Firefox versions, last 2 Safari versions"
- Polyfill: core-js (필요 시 next.config.js에서 자동 적용)
- CSS: CSS Grid + Flexbox (IE 호환 불필요)
- JS: ES2020+ 문법 사용 가능 (Optional Chaining, Nullish Coalescing 등)
```

#### NFR-19: WCAG 2.1 Level AA 접근성

```
접근성 요구사항 (WCAG 2.1 Level AA):

1. 시맨틱 HTML:
   - 모든 페이지에 <main>, <nav>, <header>, <footer> 랜드마크 사용
   - 제목 계층 구조 준수 (h1 → h2 → h3, 건너뛰기 금지)
   - 버튼/링크 구분: 네비게이션은 <a>, 동작은 <button>

2. 키보드 내비게이션:
   - 모든 인터랙티브 요소 Tab 접근 가능
   - 포커스 순서 논리적 (tabindex 남용 금지)
   - 모달/드롭다운: Escape 키로 닫기, 포커스 트랩
   - Skip to main content 링크 제공

3. ARIA:
   - 커스텀 컴포넌트에 적절한 role, aria-label, aria-describedby
   - 동적 콘텐츠 변경 시 aria-live="polite" (AI 진행 상태 등)
   - 로딩 상태: aria-busy="true"

4. 색상/대비:
   - 텍스트 대비 비율: 4.5:1 이상 (일반), 3:1 이상 (큰 텍스트)
   - 색상만으로 정보 전달 금지 (아이콘/텍스트 병행)
   - 상태 표시: 색상 + 아이콘 + 텍스트 레이블

5. 폼 접근성:
   - 모든 입력 필드에 연결된 <label>
   - 오류 메시지: aria-invalid + aria-describedby로 연결
   - 필수 필드: aria-required="true"

프론트엔드 도구:
- eslint-plugin-jsx-a11y (빌드 시 접근성 린트)
- @axe-core/react (개발 모드 런타임 감사)
```

#### NFR-20: 반응형 설계

```
반응형 브레이크포인트 (데스크톱 우선):

| 이름 | 범위 | 대상 |
|------|------|------|
| desktop-xl | ≥1440px | 대형 모니터 (기본 레이아웃) |
| desktop | 1024–1439px | 일반 데스크톱/노트북 |
| tablet | 768–1023px | 태블릿 / 좁은 브라우저 |
| mobile | <768px | 참고용 (Phase 2) |

레이아웃 전략:
- Sidebar (KB 패널, 프로젝트 목록): desktop-xl에서 고정, desktop에서 접이식, tablet에서 오버레이
- 워크플로 타임라인: 가로 스크롤 (desktop), 세로 스택 (tablet)
- 리뷰 패널 (diff 뷰): 나란히 비교 (desktop-xl), 위/아래 (desktop 이하)
- 대시보드 카드: 3열 (desktop-xl), 2열 (desktop), 1열 (tablet)

CSS 구현:
- Tailwind CSS 반응형 유틸리티: sm:, md:, lg:, xl:
- Container queries (컴포넌트 단위 반응형, @container)
- 최소 터치 영역: 44px × 44px (WCAG 2.5.5)
```

### 28-11. TRS-06: 인라인 출처 클릭 이동 프론트엔드 UI

> **목적**: AI 산출물의 인라인 출처 마커(예: `[역량DB-PRJ-023]`)를 클릭하면 해당 KB 항목으로 이동하는 프론트엔드 컴포넌트.

#### 출처 마커 파서 컴포넌트

```typescript
// frontend/components/SourceMarker.tsx

interface SourceMarkerProps {
  content: string;
  onSourceClick: (sourceRef: SourceReference) => void;
}

interface SourceReference {
  type: 'capability' | 'content' | 'client' | 'competitor' | 'lesson' | 'rfp' | 'g2b' | 'estimate';
  id: string;
  label: string;
}

/**
 * TRS-06: 인라인 출처 마커를 파싱하여 클릭 가능한 링크로 변환.
 *
 * 지원 마커 패턴:
 * - [역량DB-PRJ-023] → capabilities 테이블
 * - [콘텐츠-SEC-045] → content_library 테이블
 * - [발주처-CLI-012] → client_intel 테이블
 * - [경쟁사-CMP-007] → competitors 테이블
 * - [교훈-LSN-003] → lessons_learned 테이블
 * - [RFP-p12] → RFP 원문 페이지
 * - [G2B-공고번호] → G2B 공고 상세
 * - [추정] → 추정 데이터 (클릭 불가, 경고 스타일)
 */
const SOURCE_PATTERN = /\[(역량DB|콘텐츠|발주처|경쟁사|교훈|RFP|G2B|추정|일반지식)-([^\]]+)\]/g;

const SOURCE_TYPE_MAP: Record<string, SourceReference['type']> = {
  '역량DB': 'capability',
  '콘텐츠': 'content',
  '발주처': 'client',
  '경쟁사': 'competitor',
  '교훈': 'lesson',
  'RFP': 'rfp',
  'G2B': 'g2b',
  '추정': 'estimate',
};

export function SourceMarker({ content, onSourceClick }: SourceMarkerProps) {
  const parts = parseSourceMarkers(content);

  return (
    <span>
      {parts.map((part, i) =>
        part.isSource ? (
          <button
            key={i}
            className={`inline-source-marker ${part.ref!.type === 'estimate' ? 'source-warning' : 'source-link'}`}
            onClick={() => part.ref!.type !== 'estimate' && onSourceClick(part.ref!)}
            title={part.ref!.type === 'estimate' ? '추정 데이터 (KB 출처 없음)' : `${part.ref!.label} 원본 보기`}
            aria-label={`출처: ${part.ref!.label}`}
          >
            {part.text}
          </button>
        ) : (
          <span key={i}>{part.text}</span>
        )
      )}
    </span>
  );
}

function parseSourceMarkers(content: string) {
  const parts: Array<{ text: string; isSource: boolean; ref?: SourceReference }> = [];
  let lastIndex = 0;

  for (const match of content.matchAll(SOURCE_PATTERN)) {
    if (match.index! > lastIndex) {
      parts.push({ text: content.slice(lastIndex, match.index!), isSource: false });
    }
    const typeName = match[1];
    const id = match[2];
    parts.push({
      text: match[0],
      isSource: true,
      ref: {
        type: SOURCE_TYPE_MAP[typeName] || 'content',
        id,
        label: match[0],
      },
    });
    lastIndex = match.index! + match[0].length;
  }

  if (lastIndex < content.length) {
    parts.push({ text: content.slice(lastIndex), isSource: false });
  }

  return parts;
}
```

#### CSS 스타일

```css
/* frontend/styles/source-markers.css */

.inline-source-marker {
  display: inline;
  font-size: 0.85em;
  padding: 1px 4px;
  border-radius: 3px;
  cursor: pointer;
  font-family: inherit;
  border: none;
  background: none;
}

.source-link {
  color: #2563eb;
  background-color: #eff6ff;
  border-bottom: 1px dashed #2563eb;
}

.source-link:hover {
  background-color: #dbeafe;
  text-decoration: underline;
}

.source-warning {
  color: #d97706;
  background-color: #fffbeb;
  border-bottom: 1px dashed #d97706;
  cursor: default;
}
```

#### KB 항목 상세 패널 (사이드시트)

```typescript
// frontend/components/SourceDetailPanel.tsx

interface SourceDetailPanelProps {
  sourceRef: SourceReference | null;
  onClose: () => void;
}

/**
 * TRS-06: 출처 클릭 시 원본 데이터를 사이드 패널로 표시.
 * 종류별 API 호출하여 원본 데이터 로드.
 */
export function SourceDetailPanel({ sourceRef, onClose }: SourceDetailPanelProps) {
  const { data, isLoading } = useSourceDetail(sourceRef);

  if (!sourceRef) return null;

  const apiEndpoints: Record<string, string> = {
    capability: '/api/kb/capabilities',
    content: '/api/kb/content',
    client: '/api/kb/clients',
    competitor: '/api/kb/competitors',
    lesson: '/api/kb/lessons',
    rfp: '/api/proposals', // RFP 원문은 프로젝트 컨텍스트
    g2b: '/api/g2b/notices',
  };

  return (
    <aside className="source-detail-panel" role="complementary" aria-label="출처 상세">
      <header>
        <h3>출처 상세: {sourceRef.label}</h3>
        <button onClick={onClose} aria-label="닫기">✕</button>
      </header>
      {isLoading ? (
        <div aria-busy="true">로딩 중...</div>
      ) : (
        <div className="source-content">
          {/* 종류별 상세 렌더링 */}
          <SourceContent type={sourceRef.type} data={data} />
        </div>
      )}
    </aside>
  );
}
```

### 28-12. TRS-12: 불확실성 명시 후처리 검증 로직

> **목적**: AI 출력에서 확신도 표기(높음/보통/낮음)가 실제로 부착되었는지 후처리로 검증.

```python
# app/services/uncertainty_validator.py

import re
import structlog

logger = structlog.get_logger()

# 확신도 태그 패턴
CONFIDENCE_PATTERN = re.compile(
    r'\[(확신도[:\s]*(높음|보통|낮음))\]'
    r'|'
    r'\[confidence[:\s]*(high|medium|low)\]',
    re.IGNORECASE,
)

# 불확실성 표현 (확신도 태그가 필요한 문맥)
UNCERTAINTY_INDICATORS = [
    r'추정(됩니다|으로|치)',
    r'예상(됩니다|으로)',
    r'대략\s',
    r'약\s+\d+',
    r'~\d+',
    r'정확하지\s*않',
    r'확인\s*필요',
    r'검증\s*필요',
    r'\[추정\]',
    r'\[일반지식\]',
]
UNCERTAINTY_REGEX = re.compile('|'.join(UNCERTAINTY_INDICATORS))


def validate_uncertainty_markers(content: str, section_id: str = "") -> dict:
    """
    TRS-12: 불확실성 표기 검증.

    검사 항목:
    1. 추정/예상 표현이 있는 단락에 확신도 태그가 있는지
    2. [추정] 또는 [일반지식] 태그가 있으면 확신도 '낮음' 또는 '보통'인지
    3. 수치 데이터에 출처 태그 없이 확신도 태그도 없는 경우 경고
    """
    paragraphs = content.split('\n\n')
    issues = []
    stats = {
        "total_paragraphs": len(paragraphs),
        "uncertain_paragraphs": 0,
        "properly_tagged": 0,
        "missing_tags": 0,
    }

    for i, para in enumerate(paragraphs):
        has_uncertainty = bool(UNCERTAINTY_REGEX.search(para))
        has_confidence_tag = bool(CONFIDENCE_PATTERN.search(para))

        if has_uncertainty:
            stats["uncertain_paragraphs"] += 1

            if has_confidence_tag:
                stats["properly_tagged"] += 1

                # [추정]/[일반지식]이 있으면 확신도 '높음'은 부적절
                if ('[추정]' in para or '[일반지식]' in para):
                    confidence_match = CONFIDENCE_PATTERN.search(para)
                    if confidence_match:
                        level = (confidence_match.group(2) or confidence_match.group(3) or "").lower()
                        if level in ('높음', 'high'):
                            issues.append({
                                "paragraph_index": i,
                                "type": "confidence_mismatch",
                                "detail": "추정/일반지식 데이터에 확신도 '높음'은 부적절합니다.",
                                "suggestion": "확신도를 '보통' 또는 '낮음'으로 변경하세요.",
                            })
            else:
                stats["missing_tags"] += 1
                issues.append({
                    "paragraph_index": i,
                    "type": "missing_confidence",
                    "detail": f"불확실한 표현이 포함된 단락에 확신도 태그가 없습니다.",
                    "excerpt": para[:100],
                    "suggestion": "[확신도: 보통] 또는 [확신도: 낮음] 태그를 추가하세요.",
                })

    compliance_rate = (
        stats["properly_tagged"] / max(stats["uncertain_paragraphs"], 1) * 100
    )

    result = {
        "section_id": section_id,
        "stats": stats,
        "compliance_rate": round(compliance_rate, 1),
        "issues": issues,
        "passed": len(issues) == 0,
    }

    if issues:
        logger.warning("uncertainty_validation_issues",
            section_id=section_id,
            issue_count=len(issues),
            compliance_rate=compliance_rate,
        )

    return result
```

#### 자가진단 통합

```python
# app/graph/nodes/self_review.py 에 통합 (기존 4축 진단에 추가)

async def _run_trustworthiness_checks(state: ProposalState) -> dict:
    """
    기존 근거 신뢰성 검사 (16-3-3)에 TRS-12 불확실성 검증 추가.
    """
    from app.services.uncertainty_validator import validate_uncertainty_markers

    sections = state.get("proposal_sections", {})
    all_issues = []

    for section_id, content in sections.items():
        result = validate_uncertainty_markers(content, section_id)
        if not result["passed"]:
            all_issues.extend(result["issues"])

    return {
        "uncertainty_check": {
            "total_issues": len(all_issues),
            "issues": all_issues[:20],  # 상위 20건만
            "needs_rework": len(all_issues) > 5,  # 5건 초과 시 재작업 권고
        }
    }
```

---

> **v3.1 MEDIUM 보완 요약**: 12건 모두 설계 반영 완료.
> - 콘텐츠 라이프사이클: OB-05a (시딩), CL-10 (미갱신 알림), CL-11 (갭 분석)
> - KB 분석: CMP-06 (경쟁 빈도 뷰), LRN-08 (포지셔닝 정확도 뷰), KBS-07 (검색 이력)
> - 운영 안정성: COST-05~07 (예산 관리), OPS-04~08 (복원력+메트릭), RET-01~05 (데이터 보존)
> - 프론트엔드: NFR-18~20 (브라우저/접근성/반응형), TRS-06 (출처 클릭 UI), TRS-12 (불확실성 검증)

---
