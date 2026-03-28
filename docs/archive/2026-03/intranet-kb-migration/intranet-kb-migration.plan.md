# 인트라넷 KB 마이그레이션 — 상세 구현 계획

> **Feature**: intranet-kb-migration
> **Version**: v2.0
> **Date**: 2026-03-26
> **Status**: PLAN
> **방향**: MSSQL 2000 직접 마이그레이션 + `company_profile.json` 체계 전면 대체

---

## 1. 배경 및 목적

### 1-1. 현행 시스템의 한계

현재 수행실적 데이터는 **두 갈래**로 분리되어 있다:

**갈래 A: Excel → 로컬 JSON** (현행)
```
Excel (766건, 간략 메타)
  ↓ scripts/import_project_history.py
data/company_profile.json
  ↓ scripts/bid_scoring.py
search_matching_bids.py / daily_bid_scan.py (G2B 공고 매칭)
```

**갈래 B: Supabase DB** (SaaS 플랫폼)
```
capabilities (track_record 타입)
client_intelligence (발주기관)
market_price_data (시장가격)
content_library (재사용 콘텐츠)
```

**문제점**:
1. **갈래 A는 SaaS에서 활용 불가** — 로컬 JSON이라 LangGraph 노드/API에서 접근 안 됨
2. **Excel에 정보가 부족** — 과제명, 발주처, 부처, 금액, 키워드만. PM/팀/참여자/기간 상세 없음
3. **키워드 빈도 기반 매칭만 가능** — 벡터 유사도 검색 불가
4. **실제 문서 내용 없음** — 제안서/보고서 본문으로 RAG 불가
5. **갈래 A↔B 동기화 없음** — 같은 발주기관이 각각 별도 관리

### 1-2. 인트라넷이 제공하는 것

TENOPA 인트라넷 서버(Classic ASP + IIS + **MS SQL Server 2000**)에는:

| 현행 Excel | 인트라넷 DB (`Project_List`) | 차이 |
|-----------|---------------------------|------|
| 과제명, 발주처 | + **발주기관 담당자/전화/이메일** | 발주기관 DB 풍부화 |
| 관련부처 | (없음, 별도 매핑 필요) | — |
| 계약금액 | pr_account (텍스트) | 동일 |
| 연구책임자 | + **PM, PM멤버, 참여자, 공동수행사, 팀** | 인력 역량 자동화 |
| 키워드 | pr_key | 동일 |
| (없음) | **시작일/종료일, 진행률, 상태** | 기간 정보 추가 |
| (없음) | **파일 10종** (제안서~계약서) | **RAG의 핵심** |

### 1-3. 목표

1. **`company_profile.json` 체계를 Supabase DB로 완전 대체** — `intranet_projects` 테이블이 single source of truth
2. **인트라넷 문서(10종)를 청킹→임베딩→벡터 검색** — 제안서 작성 시 RAG 참조
3. **KB 자동 시드**: 프로젝트 메타 → `capabilities` + `client_intelligence` + `market_price_data`
4. **공고 매칭(bid_scoring) DB 전환**: JSON 대신 DB에서 키워드/발주처/예산 조회
5. 기존 `import_project_history.py` / `company_profile.json` 은 **레거시로 보존** (삭제 안 함, 새 시스템으로 대체)

---

## 2. 아키텍처 (Before/After)

### Before (현행)
```
[Excel 766건] ──Python──→ [company_profile.json] ──Python──→ [bid_scoring]
                                                              (로컬 스크립트만)

[Supabase KB] ← 수동 입력 또는 proposal 결과 기반 자동 등록
  ├── capabilities (소수)
  ├── client_intelligence (소수)
  └── content_library (proposal에서 추출)
```

### After (신규)
```
[MSSQL 2000] ──pymssql──→ [migrate_intranet.py] ──API──→ [Supabase DB]
[파일 서버] ──파일 읽기──→                        ──Upload──→ [Supabase Storage]

[Supabase DB]
  ├── intranet_projects (프로젝트 메타, Project_List 1:1) ─── NEW: single source of truth
  ├── intranet_documents (문서 파일 10종 × N프로젝트) ─── NEW
  ├── document_chunks (청크 + 벡터) ─── NEW
  │
  ├── capabilities (자동 시드: track_record) ─── ENRICHED
  ├── client_intelligence (자동 시드: 발주기관+담당자) ─── ENRICHED
  ├── market_price_data (자동 시드: 계약금액) ─── ENRICHED
  └── content_library (문서 청크 승격) ─── ENRICHED

[bid_scoring_v2.py] ──Supabase 조회──→ DB 기반 공고 매칭
  ├── 키워드 매칭: intranet_projects.keywords + capabilities
  ├── 발주처 매칭: client_intelligence (임베딩 유사도도 가능)
  ├── 예산 매칭: market_price_data
  └── 벡터 유사도: document_chunks (공고 제목 ↔ 과거 제안서)

[LangGraph 노드] ──knowledge_search.py──→ 통합 검색 (7개 영역)
  ├── research_gather: 인트라넷 문서에서 관련 자료 참조
  ├── strategy_generate: 동일 발주기관 과거 전략 참조
  └── proposal_write_next: 유사 제안서 섹션 컨텍스트 주입
```

---

## 3. 상세 구현 계획

### Phase 1: DB 스키마 + 마이그레이션 스크립트

#### 3-1-1. DB 마이그레이션

**새 파일**: `database/migrations/016_intranet_documents.sql`

**`intranet_projects`** — Project_List 1:1 매핑 (company_profile.json 대체)

```sql
CREATE TABLE intranet_projects (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) NOT NULL,

    -- 인트라넷 원본 식별자
    legacy_idx      INTEGER NOT NULL,
    legacy_code     TEXT,                  -- pr_code (2024-15)
    board_id        TEXT DEFAULT 'PR_PG',

    -- 프로젝트 메타 (Project_List 전 컬럼)
    project_name    TEXT NOT NULL,         -- pr_title
    client_name     TEXT,                  -- pr_com
    client_manager  TEXT,                  -- pr_com_manager
    client_tel      TEXT,                  -- pr_com_tel
    client_email    TEXT,                  -- pr_com_email
    start_date      DATE,
    end_date        DATE,
    budget_text     TEXT,                  -- pr_account 원본
    budget_krw      BIGINT,               -- 파싱 금액 (원)
    manager         TEXT,                  -- pr_manager (책임자)
    attendants      TEXT,                  -- pr_attendant
    partner         TEXT,                  -- pr_partner (공동수행사)
    pm              TEXT,                  -- pr_pm
    pm_members      TEXT,                  -- pr_pmem
    keywords        TEXT[],               -- pr_key 파싱
    team            TEXT,                  -- pr_team
    status          TEXT,                  -- TENOPA/STUDY/PROPOSE/GOING/COMPLETE/DELAY
    inout           TEXT,                  -- in(사내)/out(외부)
    progress_pct    INTEGER DEFAULT 0,

    -- company_profile.json 대체용 집계 지원
    department      TEXT,                  -- 관련부처 (Excel에 있었던 필드, 수동 매핑 가능)
    domain          TEXT,                  -- SI/SW개발, 정책연구, 성과분석, 컨설팅

    -- 마이그레이션 상태
    migration_status TEXT DEFAULT 'metadata_only', -- metadata_only | files_uploading | completed | failed
    file_count       INTEGER DEFAULT 0,

    -- KB 시드 연동 추적
    capability_id    UUID REFERENCES capabilities(id),
    client_intel_id  UUID REFERENCES client_intelligence(id),
    market_price_id  UUID REFERENCES market_price_data(id),

    -- 벡터 검색 (프로젝트 단위 유사도)
    embedding        vector(1536),

    created_at       TIMESTAMPTZ DEFAULT now(),
    updated_at       TIMESTAMPTZ DEFAULT now(),

    UNIQUE(org_id, legacy_idx, board_id)
);

CREATE INDEX idx_intranet_projects_org ON intranet_projects(org_id);
CREATE INDEX idx_intranet_projects_client ON intranet_projects(client_name);
CREATE INDEX idx_intranet_projects_status ON intranet_projects(status);
CREATE INDEX idx_intranet_projects_embedding ON intranet_projects
    USING ivfflat (embedding vector_cosine_ops) WITH (lists = 50);
```

핵심 차이점 (v1 대비):
- `intranet_projects` 자체에 `embedding` 추가 → **프로젝트 단위 유사도 검색** (공고 매칭에 활용)
- `department`, `domain` 컬럼 → company_profile의 `department_frequency` 대체
- `capability_id`, `client_intel_id`, `market_price_id` → KB 시드 추적

**`intranet_documents`** + **`document_chunks`** — v1과 동일 (변경 없음)

#### 3-1-2. 프로젝트 단위 벡터 검색 RPC (신규)

```sql
-- 공고 제목으로 유사 과거 프로젝트 검색 (bid_scoring 대체)
CREATE OR REPLACE FUNCTION search_projects_by_embedding(
    query_embedding vector(1536),
    match_org_id UUID,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    project_name TEXT,
    client_name TEXT,
    department TEXT,
    budget_krw BIGINT,
    keywords TEXT[],
    start_date DATE,
    end_date DATE,
    status TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql AS $$
BEGIN
    RETURN QUERY
    SELECT
        ip.id, ip.project_name, ip.client_name, ip.department,
        ip.budget_krw, ip.keywords, ip.start_date, ip.end_date,
        ip.status,
        1 - (ip.embedding <=> query_embedding) AS similarity
    FROM intranet_projects ip
    WHERE ip.org_id = match_org_id
      AND ip.embedding IS NOT NULL
    ORDER BY ip.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
```

#### 3-1-3. 마이그레이션 스크립트

**새 파일**: `scripts/migrate_intranet.py`

v1 계획의 스크립트에 추가되는 핵심 변경:

```python
"""
인트라넷 MSSQL 2000 → 용역제안 Coworker SaaS 마이그레이션 도구 v2

v1 대비 변경:
- 프로젝트 메타 임포트 시 벡터 임베딩 생성 (프로젝트 단위 유사도 검색)
- KB 자동 시드: capabilities, client_intelligence, market_price_data 동시 생성
- company_profile.json 대체: keyword_index, search_keywords를 DB 집계로 대체
- department 매핑: 기존 Excel의 관련부처 정보를 별도 CSV로 보완 가능
"""

FILE_SLOTS = [
    FileSlot("file_proposal",    doc_type="proposal",     doc_subtype="기술제안서"),
    FileSlot("file_proposal_pt", doc_type="presentation", doc_subtype="제안발표자료"),
    FileSlot("file_middle",      doc_type="report",       doc_subtype="중간보고서"),
    FileSlot("file_middle_pt",   doc_type="presentation", doc_subtype="중간발표자료"),
    FileSlot("file_final",       doc_type="report",       doc_subtype="최종보고서"),
    FileSlot("file_final_pt",    doc_type="presentation", doc_subtype="최종발표자료"),
    FileSlot("file_summary",     doc_type="report",       doc_subtype="요약서"),
    FileSlot("file_contract",    doc_type="contract",     doc_subtype="계약서"),
    FileSlot("file_etc01",       doc_type="reference",    doc_subtype="기타"),
    FileSlot("file_etc02",       doc_type="reference",    doc_subtype="기타"),
]

class IntranetMigrator:
    """MSSQL 2000 → Supabase 마이그레이션."""

    async def run(self, board_id="PR_PG", status_filter=None):
        """
        전체 마이그레이션 실행.

        status_filter=None: 전체 프로젝트 (STUDY/PROPOSE/GOING/COMPLETE 모두)
        status_filter="COMPLETE": 완료 프로젝트만
        """
        projects = self.fetch_projects(board_id, status_filter)
        print(f"총 {len(projects)}건 프로젝트 발견")

        for project in tqdm(projects, desc="마이그레이션"):
            # Step 1: 프로젝트 메타 + 임베딩 + KB 시드
            result = await self.import_project(project)
            if result["action"] == "skipped":
                continue

            # Step 2: 파일 10종 업로드
            for slot in FILE_SLOTS:
                file_path = self.find_file(project, slot)
                if file_path and file_path.exists():
                    await self.upload_file(result["id"], slot, file_path)

    async def import_project(self, row: dict) -> dict:
        """
        단일 프로젝트 임포트.

        1. intranet_projects 생성 (중복 시 스킵)
        2. 프로젝트 임베딩 생성 (제목+키워드+발주기관 → 벡터)
        3. capabilities 시드 (track_record)
        4. client_intelligence 시드 (발주기관+담당자 연락처)
        5. market_price_data 시드 (계약금액)
        """
        # ... (API 호출 구현)

    def _build_embedding_text(self, row: dict) -> str:
        """프로젝트 메타로 임베딩 텍스트 생성."""
        parts = [
            row.get("pr_title", ""),
            row.get("pr_com", ""),
            row.get("pr_key", ""),
            row.get("pr_team", ""),
        ]
        return " | ".join(filter(None, parts))
```

#### 3-1-4. 부처(department) 보완 전략

인트라넷 DB에는 `관련부처` 컬럼이 없다. 기존 Excel에는 있었으므로:

**옵션 A (추천)**: 기존 Excel의 발주처→부처 매핑을 CSV로 추출하여 마이그레이션 시 병합
```python
# scripts/dept_mapping.csv
# 발주처,관련부처
# 한국과학기술기획평가원,과학기술정보통신부
# 한국연구재단,과학기술정보통신부
# ...

class IntranetMigrator:
    def __init__(self, ...):
        self.dept_map = self._load_dept_mapping()  # CSV → {client: department}

    async def import_project(self, row):
        department = self.dept_map.get(row["pr_com"], "")
        # → intranet_projects.department에 저장
```

**옵션 B**: 마이그레이션 후 관리자가 프론트엔드에서 부처 매핑

### Phase 2: 공고 매칭 DB 전환 (bid_scoring 대체)

#### 3-2-1. 새 스코어링 모듈

**새 파일**: `app/services/bid_scoring_service.py`

기존 `scripts/bid_scoring.py`의 로직을 DB 기반으로 재구현:

```python
"""
DB 기반 공고 적합도 스코어링 (company_profile.json 대체)

Before: company_profile.json → keyword_index, client_frequency, department_frequency
After:  intranet_projects (Supabase) → SQL 집계 + 벡터 유사도
"""

class BidScoringService:
    """DB 기반 공고 스코어링."""

    async def score_bid(self, org_id: str, bid: dict) -> dict:
        """
        공고 적합도 스코어 (0~100).

        v1 (JSON 기반):
          키워드 빈도 40 + 발주처 빈도 30 + 부처 빈도 20 + 예산 범위 10

        v2 (DB 기반, 개선):
          벡터 유사도 30 + 키워드 매칭 20 + 발주처 경험 25 + 부처 경험 15 + 예산 범위 10
        """
        title = bid.get("bidNtceNm", "")
        client = bid.get("ntceInsttNm", "") or bid.get("dminsttNm", "")
        budget = parse_budget(bid.get("presmptPrce") or bid.get("asignBdgtAmt"))

        # ── 1. 벡터 유사도 (30점) — NEW ──
        # 공고 제목 임베딩 → 과거 프로젝트와 cosine similarity
        embedding = await generate_embedding(title)
        similar = await self._search_similar_projects(org_id, embedding, top_k=5)
        if similar:
            avg_sim = sum(s["similarity"] for s in similar) / len(similar)
            vector_score = min(avg_sim * 40, 30.0)  # 0.75 이상이면 30점
        else:
            vector_score = 0.0

        # ── 2. 키워드 매칭 (20점) ──
        # DB: intranet_projects에서 keywords 빈도 집계
        keyword_stats = await self._get_keyword_stats(org_id)
        matched_kw = [kw for kw in keyword_stats if kw.lower() in title.lower()]
        kw_score = min(len(matched_kw) * 5, 20.0)

        # ── 3. 발주처 경험 (25점) ──
        # DB: intranet_projects에서 client_name 빈도
        client_count = await self._count_client_projects(org_id, client)
        client_score = min(15.0 + client_count * 2, 25.0) if client_count > 0 else 0.0

        # ── 4. 부처 경험 (15점) ──
        dept_score = await self._score_department(org_id, client, title)

        # ── 5. 예산 범위 (10점) ──
        budget_score = self._score_budget(budget)

        total = round(vector_score + kw_score + client_score + dept_score + budget_score)

        return {
            "score": total,
            "matched_keywords": matched_kw,
            "similar_projects": [s["project_name"] for s in similar[:3]],
            "client_project_count": client_count,
            "score_detail": {
                "vector_similarity": round(vector_score, 1),
                "keyword": round(kw_score, 1),
                "client": round(client_score, 1),
                "department": round(dept_score, 1),
                "budget": round(budget_score, 1),
            },
        }

    async def _search_similar_projects(self, org_id, embedding, top_k=5):
        """intranet_projects 벡터 검색."""
        client = await get_async_client()
        result = await client.rpc("search_projects_by_embedding", {
            "query_embedding": embedding,
            "match_org_id": org_id,
            "match_count": top_k,
        }).execute()
        return result.data or []

    async def _get_keyword_stats(self, org_id) -> dict[str, int]:
        """DB에서 키워드 빈도 집계 (company_profile.keyword_index.domain_keywords 대체)."""
        client = await get_async_client()
        result = await client.table("intranet_projects").select(
            "keywords"
        ).eq("org_id", org_id).execute()

        freq: dict[str, int] = {}
        for row in result.data or []:
            for kw in (row.get("keywords") or []):
                freq[kw] = freq.get(kw, 0) + 1
        return freq

    async def _count_client_projects(self, org_id, client_name) -> int:
        """발주기관 수행 횟수 (company_profile.keyword_index.client_frequency 대체)."""
        client = await get_async_client()
        result = await client.table("intranet_projects").select(
            "id", count="exact"
        ).eq("org_id", org_id).ilike("client_name", f"%{client_name}%").execute()
        return result.count or 0
```

#### 3-2-2. 기존 스크립트 래퍼

**수정 파일**: `scripts/bid_scoring.py`

기존 `load_profile()` 함수에 DB 폴백 추가 (하위 호환):

```python
def load_profile() -> dict:
    """
    DB 우선, JSON 폴백.
    - DB(intranet_projects)에 데이터 있으면 → DB에서 집계
    - 없으면 → 기존 company_profile.json 로드
    """
    try:
        # DB 모드 시도
        profile = asyncio.run(_load_from_db())
        if profile and profile["company"]["stats"]["total_projects"] > 0:
            return profile
    except Exception:
        pass

    # JSON 폴백
    with open(PROFILE_PATH, encoding="utf-8") as f:
        return json.load(f)
```

### Phase 3: 문서 처리 파이프라인 + 검색 통합

v1 계획의 Phase B와 동일:
- `document_chunker.py`: 4종 청킹 전략 (section/slide/article/window)
- `document_ingestion.py`: 업로드 → 추출 → 청킹 → 임베딩 → 저장
- `knowledge_search.py`: 7번째 영역 `"intranet_doc"` + 8번째 `"intranet_project"` 추가
- `file_utils.py`: PPTX/XLSX 추출기 추가

### Phase 4: LangGraph 노드 연동

v1 계획의 Phase C와 동일:
- `research_gather.py`: 인트라넷 문서 참조
- `strategy_generate.py`: 동일 발주기관 과거 전략
- `context_helpers.py`: `include_intranet_docs` 파라미터

---

## 4. company_profile.json → DB 전환 상세 매핑

기존 JSON 구조와 DB 대응:

```
company_profile.json                   →  DB (Supabase)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
company.name                           →  organizations.name
company.stats.total_projects           →  SELECT COUNT(*) FROM intranet_projects
company.stats.avg_budget_krw           →  SELECT AVG(budget_krw) FROM intranet_projects
company.stats.total_budget_krw         →  SELECT SUM(budget_krw) FROM intranet_projects

track_records[].title                  →  intranet_projects.project_name
track_records[].client                 →  intranet_projects.client_name
track_records[].department             →  intranet_projects.department
track_records[].budget_krw             →  intranet_projects.budget_krw
track_records[].period                 →  start_date ~ end_date 계산
track_records[].keywords               →  intranet_projects.keywords (TEXT[])

keyword_index.domain_keywords          →  SELECT unnest(keywords), COUNT(*)
                                          FROM intranet_projects GROUP BY 1
keyword_index.client_frequency         →  SELECT client_name, COUNT(*)
                                          FROM intranet_projects GROUP BY 1
keyword_index.department_frequency     →  SELECT department, COUNT(*)
                                          FROM intranet_projects WHERE department IS NOT NULL GROUP BY 1

search_keywords (빈도≥5)              →  위 집계에서 HAVING COUNT(*) >= 5
```

**추가로 가능해지는 것** (JSON에서는 불가능했던):
- `벡터 유사도 검색`: 공고 제목 → 과거 프로젝트 임베딩 매칭
- `문서 본문 RAG`: 과거 제안서 내용에서 관련 섹션 자동 참조
- `시간 범위 필터`: start_date/end_date로 최근 N년 실적만 검색
- `상태 필터`: COMPLETE만, 또는 GOING 포함 등 동적 필터
- `팀별 분석`: pr_team 기반 팀별 수행 현황
- `PM 역량 추적`: pm, pm_members에서 개인별 수행 이력

---

## 5. 파일 목록

### 새 파일 (8개)

| 파일 | 설명 | 예상 줄 수 |
|------|------|-----------|
| `database/migrations/016_intranet_documents.sql` | DB 스키마 (3 테이블 + 2 RPC + RLS) | ~180 |
| `scripts/migrate_intranet.py` | MSSQL 2000 마이그레이션 도구 | ~350 |
| `scripts/migrate_intranet.env.example` | 설정 템플릿 | ~15 |
| `scripts/dept_mapping.csv` | 발주처→부처 매핑 (기존 Excel에서 추출) | ~200행 |
| `app/services/document_ingestion.py` | 문서 수집 파이프라인 | ~250 |
| `app/services/document_chunker.py` | 지능형 청킹 (4종 전략) | ~180 |
| `app/services/bid_scoring_service.py` | DB 기반 공고 스코어링 (v2) | ~200 |
| `app/api/routes_intranet.py` | API 라우트 (8 엔드포인트) | ~280 |

### 수정 파일 (5개)

| 파일 | 변경 내용 |
|------|----------|
| `app/utils/file_utils.py` | PPTX/XLSX 추출기 + 디스패처 확장 (+60줄) |
| `app/services/knowledge_search.py` | `"intranet_doc"` + `"intranet_project"` 영역 추가 (+60줄) |
| `app/config.py` | 인트라넷 관련 설정 (+5줄) |
| `app/main.py` | 라우터 등록 (+3줄) |
| `scripts/bid_scoring.py` | DB 우선/JSON 폴백 load_profile() (+30줄) |

### 레거시 보존 (삭제 안 함)

| 파일 | 비고 |
|------|------|
| `scripts/import_project_history.py` | 레거시. 새 시스템 정착 후 제거 검토 |
| `data/company_profile.json` | bid_scoring.py가 폴백으로 참조. 새 시스템 정착 후 제거 |

---

## 6. 실행 순서

```
Phase 1: 기반 구축
  Step 1: 016_intranet_documents.sql (DB 스키마)
  Step 2: file_utils.py (PPTX/XLSX 추출기)
  Step 3: document_chunker.py (청킹)
  Step 4: document_ingestion.py (수집 파이프라인)
  Step 5: routes_intranet.py + main.py (API)
  Step 6: config.py (설정)

Phase 2: 마이그레이션 실행
  Step 7: dept_mapping.csv (부처 매핑 준비)
  Step 8: migrate_intranet.py (마이그레이션 스크립트)
  Step 9: 사내 PC에서 dry-run → 본 실행

Phase 3: 검색 + 스코어링 전환
  Step 10: knowledge_search.py (통합 검색 확장)
  Step 11: bid_scoring_service.py (DB 기반 스코어링)
  Step 12: bid_scoring.py (DB 우선 폴백)

Phase 4: LangGraph 연동
  Step 13: research_gather / strategy_generate / context_helpers 확장

검증:
  Step 14: ruff check + mypy
  Step 15: E2E 검증 (마이그레이션 → 검색 → 공고 매칭 → 제안서 작성 시 참조)
```

---

## 7. 검증 방법

1. **마이그레이션 dry-run**: `DRY_RUN=true`로 MSSQL 연결 + 건수 확인
2. **KB 시드 확인**: `capabilities`, `client_intelligence`, `market_price_data` 자동 생성 건수
3. **벡터 검색**: 공고 제목으로 `search_projects_by_embedding()` → 유사 과거 프로젝트 반환
4. **공고 스코어링 비교**: 동일 공고에 대해 v1(JSON) vs v2(DB) 스코어 비교
5. **문서 RAG**: 업로드된 제안서에서 키워드 검색 → 관련 청크 반환
6. **ruff check + mypy**: 코드 품질
7. **통합 검색**: `/api/kb/search?q=키워드&areas=intranet_doc,intranet_project`

---

## 8. 리스크 및 대응

| 리스크 | 대응 |
|--------|------|
| MSSQL 2000 + pymssql 연결 실패 | FreeTDS `tds_version=7.0`, 대안: pyodbc + ODBC Driver |
| EUC-KR 인코딩 깨짐 | `charset='cp949'` + 파일명 `os.fsencode()` |
| 부처 매핑 누락 | dept_mapping.csv + 관리자 수동 보완 UI |
| bid_scoring 호환성 | JSON 폴백 유지, 점진적 전환 |
| 대용량 파일 처리 | 100MB 제한, 실패 시 skip + 로깅 |
| 임베딩 비용 | 프로젝트 ~500건 × 1 + 문서 ~2000건 × ~10청크 ≈ $2~5 |

---

## 9. 의존성

```
# 마이그레이션 스크립트 (사내 PC)
pymssql>=2.2.0         # MSSQL 2000 (TDS 7.0)
httpx>=0.27.0          # SaaS API 호출
tqdm>=4.66.0           # 진행률
python-dotenv>=1.0.0   # .env 설정

# 프로젝트 기존 의존성 (추가 불필요)
# openpyxl, python-pptx, PyPDF2, python-docx
```
