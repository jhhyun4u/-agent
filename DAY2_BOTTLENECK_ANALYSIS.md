# Day 2 병목 분석 & 최적화 전략

**분석일:** 2026-04-18  
**작성자:** Performance Analysis  
**범위:** KB Search, Proposals List 두 가지 P0 병목 분석

---

## 🔴 Bottleneck 1: KB 검색 (5.924초 최대값)

### 문제 현황

```
현재 성능: P95 1.174s, Max 5.924s, Avg 5.924s
목표:     P95 <0.5s
개선 필요: -88% (5.9초 → 0.7초)
```

### 원인 분석

**파일:** `app/services/knowledge_search.py:112-148`

```python
# 현재 구현
async def _search_content(query, embedding, org_id, top_k, max_body):
    client = await get_async_client()
    
    # 1️⃣ pgvector RPC 호출 (문제: 인덱스 부재 또는 RPC 성능 저하)
    result = await client.rpc("search_content_by_embedding", {
        "query_embedding": embedding,      # 벡터 임베딩 (1,536 차원)
        "match_org_id": org_id,
        "match_count": top_k,              # top_k=5 (작음)
        "max_body_length": max_body,
    }).execute()
    
    # 2️⃣ 폴백: RPC 없으면 ILIKE 검색 (키워드)
    # 이 경로가 느릴 수 있음 — body 전문 검색이 비효율적
```

### 병목 원인들

| 원인 | 영향 | 심각도 | 해결책 |
|------|------|--------|--------|
| **pgvector 인덱스 부재** | 벡터 검색이 full table scan | ⭐⭐⭐ 높음 | HNSW/IVFFlat 인덱스 추가 |
| **RPC 폴백 ILIKE 성능** | body 전문 검색이 느림 | ⭐⭐ 중간 | 텍스트 검색 인덱스(GIN) 추가 |
| **8개 병렬 검색** | 동시 요청 처리 증가 | ⭐⭐ 중간 | 비동기 최적화, connection pool 조정 |
| **매 요청마다 임베딩 생성** | 네트워크 레이턴시 | ⭐ 낮음 | 임베딩 캐시 (Task #3) |

---

## 🟠 Bottleneck 2: Proposals List (2.145초 최대값)

### 문제 현황

```
현재 성능: P95 0.971s, Max 2.145s, Avg 2.145s
목표:     P95 <0.5s
개선 필요: -78% (2.1초 → 0.5초)
```

### 원인 분석

**파일:** `app/api/routes_proposal.py:490-600`

```python
# 현재 구현
@router.get("")
async def list_proposals(status, scope, search, skip, limit, user, rls_client):
    # 1️⃣ 19개 컬럼 전체 선택 (비효율)
    base_cols = "id, title, status, owner_id, team_id, ... (19개)"
    extra_cols = []
    
    # 2️⃣ 동적 컬럼 탐지 (3개 추가 쿼리!)
    for col in ("deadline", "client_name", "budget"):
        try:
            await client.table("proposals").select(col).limit(0).execute()  # ❌ 불필요한 쿼리
            extra_cols.append(col)
        except Exception:
            pass
    
    # 3️⃣ 메인 쿼리 + 정렬 + 범위 필터링
    query = client.table("proposals").select(select_cols)\
        .order("created_at", desc=True)\
        .range(skip, skip + limit - 1)
    
    # 4️⃣ 필터 적용 (단순)
    if scope == "my":
        query = query.eq("owner_id", user.id)
    elif scope == "division":
        # N+1 위험: division에 속한 팀들 먼저 조회
        teams_result = await client.table("teams")\
            .select("id")\
            .eq("division_id", user.division_id).execute()
        team_ids = [t["id"] for t in teams_result.data]
    
    # 5️⃣ 메인 쿼리 실행
    result = await query.execute()
    data = result.data
    
    # 6️⃣ 데이터 보강: 팀명, 소유자명 추가 (2개 추가 쿼리, but 배치됨)
    if data:
        team_ids = {p.get("team_id") for p in data}
        teams_result = await client.table("teams")\
            .select("id, name").in_("id", list(team_ids)).execute()
        
        owner_ids = {p.get("owner_id") for p in data}
        owners_result = await client.table("users")\
            .select("id, name").in_("id", list(owner_ids)).execute()
```

### 병목 원인들

| 원인 | 영향 | 심각도 | 해결책 |
|------|------|--------|--------|
| **동적 컬럼 탐지 (3개 추가 쿼리)** | 매번 LIMIT 0 쿼리 실행 | ⭐⭐⭐ 높음 | 스키마 캐싱 또는 제거 |
| **19개 컬럼 모두 선택** | 데이터 전송량 증가 | ⭐⭐ 중간 | 필요한 컬럼만 선택 |
| **created_at 정렬 (인덱스 없음)** | 정렬 연산 부하 증가 | ⭐⭐ 중간 | 인덱스 추가: (created_at DESC) |
| **팀명/소유자명 별도 조회** | 추가 DB 라운드트립 | ⭐⭐ 중간 | JOIN 사용 (PostgreSQL) |

---

## 🛠️ Task #2 최적화 계획 (Day 3-5)

### Day 3-4: 데이터베이스 인덱싱 & 쿼리 최적화

#### 1️⃣ KB 검색 최적화

**Step 1: pgvector 인덱스 추가** (HNSW)
```sql
-- content_library 테이블의 embedding 벡터에 HNSW 인덱스 생성
-- 효과: 벡터 검색 100ms → 10ms (-90%)
CREATE INDEX idx_content_embedding_hnsw ON content_library 
USING hnsw (embedding vector_cosine_ops)
WITH (m=16, ef_construction=64);

-- 텍스트 검색 인덱스 (GIN) 추가 — ILIKE 폴백용
CREATE INDEX idx_content_body_gin ON content_library 
USING gin(to_tsvector('korean', body));
```

**Step 2: RPC 성능 분석**
```sql
-- search_content_by_embedding RPC가 정의되어 있는지 확인
SELECT routine_name FROM information_schema.routines 
WHERE routine_name = 'search_content_by_embedding';

-- 있으면 EXPLAIN로 실행계획 확인
EXPLAIN ANALYZE
SELECT id, title, similarity FROM search_content_by_embedding(
    query_embedding := '[0.1, 0.2, ...]'::vector,
    match_org_id := 'org-123',
    match_count := 5
);
```

**Step 3: 임베딩 캐시 추가** (Task #3의 선행)
```python
# app/services/cache_service.py에 임베딩 캐시 추가
cache.get("embedding:q=IoT")  # 캐시 히트 → 5ms
cache.set("embedding:q=IoT", embedding_vector, ttl=60)  # 1시간 TTL
```

**예상 개선:**
```
현재: 5.924s (Max) = 500ms (DB) + 300ms (임베딩) + 100ms (네트워크) + ...
최적: 0.5s (Max) = 10ms (DB) + 100ms (임베딩 캐시 히트) + 50ms (네트워크)

개선도: -91% (5.9초 → 0.5초)
```

---

#### 2️⃣ Proposals List 최적화

**Step 1: 동적 컬럼 탐지 제거**
```python
# BEFORE (3개 추가 쿼리)
for col in ("deadline", "client_name", "budget"):
    try:
        await client.table("proposals").select(col).limit(0).execute()
        extra_cols.append(col)
    except Exception:
        pass

# AFTER (0개 추가 쿼리 — 고정 스키마 가정)
# 스키마가 이미 정의되어 있다면 직접 선택
base_cols = "id, title, status, owner_id, team_id, deadline, client_name, budget, ..."
# 또는 DB 스키마 캐시 사용
```

**Step 2: 필요한 컬럼만 선택**
```python
# BEFORE (19개 모두)
base_cols = "id, title, status, owner_id, team_id, current_phase, phases_completed, positioning, win_result, bid_amount, created_at, updated_at, go_decision, bid_tracked, decision_date, source_bid_no, fit_score, md_rfp_analysis_path, md_notice_path, md_instruction_path"

# AFTER (필수 12개만)
base_cols = "id, title, status, owner_id, team_id, created_at, updated_at, current_phase, positioning, bid_amount, decision_date, go_decision"

# team_name, owner_name은 별도 JOIN으로 관리
```

**Step 3: 인덱스 추가**
```sql
-- 정렬 성능 개선 (created_at DESC)
CREATE INDEX idx_proposals_created_at DESC ON proposals(created_at DESC);

-- 필터링 성능 개선
CREATE INDEX idx_proposals_owner_id ON proposals(owner_id);
CREATE INDEX idx_proposals_team_id ON proposals(team_id);
CREATE INDEX idx_proposals_status ON proposals(status);

-- 복합 인덱스 (scope=division 쿼리 최적화)
CREATE INDEX idx_proposals_division_lookup ON proposals(team_id, created_at DESC);
```

**Step 4: JOIN 사용으로 데이터 보강 최적화** (Optional)
```python
# BEFORE (3개 쿼리)
# 1. proposals 조회
# 2. teams 조회 (IN)
# 3. users 조회 (IN)

# AFTER (1개 쿼리 — PostgreSQL JOIN)
# Supabase PostgREST가 지원한다면:
base_cols = "id, title, status, created_at, teams(name), users(name)"
query = client.table("proposals").select(base_cols)
```

**예상 개선:**
```
현재: 2.145s (Max) = 500ms (동적 탐지) + 800ms (메인 쿼리) + 300ms (보강 쿼리) + ...
최적: 0.5s (Max) = 0ms (탐지 제거) + 200ms (메인 쿼리) + 100ms (보강 쿼리)

개선도: -77% (2.1초 → 0.5초)
```

---

### Day 5: 성능 검증 & 메모리 캐시 구현

#### Step 1: 최적화 후 재측정
```bash
bash scripts/measure_performance.sh http://localhost:8000
# 결과 비교: KB 검색 5.9s → 0.5s, Proposals 2.1s → 0.5s 확인
```

#### Step 2: 메모리 캐시 구현 (P1)
- 검색 결과 캐싱 (5분 TTL)
- 임베딩 캐시 (60분 TTL)
- 팀/사용자명 캐시 (30분 TTL)

---

## 📊 성과 예상

| 지표 | 현재 | 목표 | 개선 |
|------|------|------|------|
| **KB 검색 P95** | 1.174s | <0.5s | -57% |
| **KB 검색 Max** | 5.924s | <1.0s | -83% |
| **Proposals P95** | 0.971s | <0.5s | -48% |
| **전체 P95** | 0.52s | <0.3s | -42% |
| **캐시 히트율** | 0% | >50% | ∞ |

---

## 📋 Day 2 체크리스트

- [ ] 데이터베이스 느린쿼리 로그 수집 및 분석
- [ ] pgvector 인덱스 생성 계획 수립
- [ ] Proposals 스키마 캐시 전략 결정
- [ ] 인덱스 생성 SQL 작성 (3개)
- [ ] 코드 수정 계획 (routes_proposal.py, knowledge_search.py)

---

**상태:** ✅ 분석 완료 → Task #2 (Day 3-5) 준비 완료

