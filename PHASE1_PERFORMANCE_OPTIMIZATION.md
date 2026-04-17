# Phase 1 성능 최적화 분석 & 실행 계획

**작성일:** 2026-04-17  
**대상:** Beta Testing (2026-04-17 ~ 04-30)  
**목표:** 응답시간 <3s, 메모리 안정화, 캐싱 효율성 최적화

---

## 📊 현재 성능 지표 (Baseline)

### 수집 대상
- **응답시간 P95:** TBD (모니터링 시작 필요)
- **메모리 사용량:** TBD (힙 스냅샷 필요)
- **데이터베이스 쿼리 시간:** TBD (쿼리 로그 분석 필요)
- **프론트엔드 번들 크기:** TBD (번들 분석 필요)
- **캐시 히트율:** TBD (캐시 메트릭 수집 필요)

---

## 🎯 최적화 전략 (3가지 우선순위)

### **P0: 데이터베이스 쿼리 최적화**

#### 1.1 현황
- **문제:** API 라우터에서 100+ SELECT 쿼리 발견
- **패턴:** N+1 쿼리 위험
- **영향:** DB 응답 지연 → API 응답 지연

#### 1.2 최적화 항목

| 파일 | 쿼리 수 | 최적화 기회 | 예상 개선 |
|------|--------|----------|---------|
| `routes_proposal.py` | 20+ | JOIN 최적화, 컬럼 선택 | -40% |
| `routes_analytics.py` | 15+ | 집계 쿼리 + 인덱싱 | -50% |
| `routes_kb.py` | 12+ | 검색 쿼리 + 전문 인덱스 | -60% |
| `routes_resources.py` | 18+ | 권한 필터 최적화 | -30% |
| `routes_vault_chat.py` | 10+ | 캐시 레이어 추가 | -80% |

#### 1.3 구현 계획

```python
# BEFORE: N+1 패턴
proposals = await client.table("proposals").select("*").execute()
for p in proposals.data:
    team = await client.table("teams").select("*").eq("id", p["team_id"]).execute()
    # ... 추가 쿼리

# AFTER: JOIN 최적화
proposals = await client.table("proposals").select(
    "*, teams(id, name), users(id, email)"
).execute()
```

#### 1.4 실행 순서
1. **Day 1-2:** 핫 경로(Hot Paths) 식별
   - `/api/proposals` (제안 목록)
   - `/api/workflow/state` (워크플로우 상태)
   - `/api/vault/search` (검색)

2. **Day 3-4:** 쿼리 재작성 및 테스트
   - SELECT 컬럼 최적화
   - JOIN 추가
   - 인덱스 추가 (DB)

3. **Day 5:** 성능 검증
   - 응답시간 측정
   - 메모리 사용량 확인

---

### **P1: 캐싱 전략 개선**

#### 2.1 현황
- **기존 캐싱:** 파일 기반 (bids.py), VaultCacheService (vault_chat.py)
- **문제:** 분산된 캐싱, TTL 관리 불일치, 캐시 무효화 없음
- **기회:** Redis 도입 또는 메모리 캐시 통합

#### 2.2 캐싱 레이어 아키텍처

```
Layer 1: 메모리 캐시 (응답 데이터, 임베딩 검색 결과)
├─ TTL: 5분
├─ 크기: 500MB (LRU 제거)
└─ 사용처: /api/vault/search, /api/kb/*

Layer 2: Redis (선택사항, Phase 2)
├─ TTL: 1시간
├─ 사용처: 사용자 세션, 생성된 콘텐츠
└─ 문제: 현재 인프라에 Redis 없음

Layer 3: 데이터베이스 쿼리 결과 캐시
├─ TTL: 30분
├─ 사용처: /api/analytics, /api/performance
└─ 구현: Supabase 쿼리 캐싱 (PostgREST)
```

#### 2.3 구현 사항

**2.3.1 메모리 캐시 통합 (Priority)**
```python
# app/services/cache_service.py (새 파일)

from functools import lru_cache
from datetime import datetime, timedelta
from typing import Any, Optional

class MemoryCache:
    """LRU 메모리 캐시 (최대 500MB)"""
    
    def __init__(self, max_size_mb: int = 500):
        self._cache = {}
        self._ttl = {}
        self.max_size = max_size_mb * 1024 * 1024
        self.current_size = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """캐시 조회, TTL 확인"""
        if key not in self._cache:
            return None
        
        if key in self._ttl:
            if datetime.now() > self._ttl[key]:
                del self._cache[key]
                del self._ttl[key]
                return None
        
        return self._cache[key]
    
    async def set(self, key: str, value: Any, ttl_minutes: int = 5) -> None:
        """캐시 저장 (LRU 제거 적용)"""
        self._cache[key] = value
        self._ttl[key] = datetime.now() + timedelta(minutes=ttl_minutes)
        
        # LRU 제거 (크기 초과시)
        if self.current_size > self.max_size:
            self._evict_oldest()
    
    def _evict_oldest(self) -> None:
        """가장 오래된 항목 제거"""
        if self._cache:
            oldest_key = min(self._ttl, key=self._ttl.get)
            del self._cache[oldest_key]
            del self._ttl[oldest_key]

# 사용 예
cache = MemoryCache()

@router.get("/api/vault/search")
async def search(q: str):
    cache_key = f"search:{q}"
    cached = await cache.get(cache_key)
    if cached:
        return cached  # 캐시 히트
    
    # 검색 실행
    results = await vault_search(q)
    await cache.set(cache_key, results, ttl_minutes=5)
    return results
```

**2.3.2 캐시 무효화 전략**
```python
# 제안서 업데이트시 관련 캐시 제거
async def invalidate_proposal_cache(proposal_id: str):
    """제안서 변경시 캐시 무효화"""
    patterns = [
        f"proposals:{proposal_id}:*",
        f"vault:search:*{proposal_id}*",
    ]
    for pattern in patterns:
        await cache.delete_pattern(pattern)
```

#### 2.4 예상 효과
| 캐시 전략 | 예상 개선 | 구현 난이도 |
|----------|---------|-----------|
| 메모리 캐시 | -60% 응답시간 (캐시 히트시) | 낮음 (3일) |
| Signed URL 캐싱 | -40% 스토리지 요청 | 중간 (2일) |
| 쿼리 결과 캐싱 | -50% DB 부하 | 중간 (3일) |

---

### **P2: 프론트엔드 번들 최적화**

#### 3.1 현황
- **번들 크기:** TBD (측정 필요)
- **목표:** < 500KB (gzip)

#### 3.2 최적화 기회

```bash
# 번들 분석 (현재 상태)
# $ next/built-in: npm run build && npm run analyze

# 최적화 항목:
1. Code Splitting (경로별 lazy loading)
2. 이미지 최적화 (next/image)
3. 폰트 최적화 (next/font)
4. CSS-in-JS 최소화
5. 미사용 라이브러리 제거
```

#### 3.3 구현 순서 (선택사항)
- Week 1: 번들 분석 + 점수화
- Week 2: 코드 분할 + 이미지 최적화
- Week 3: 폰트 최적화 + CSS 최소화

---

## 📋 실행 체크리스트 (Daily)

### **Week 1 (2026-04-17 ~ 04-24)**

#### **Day 1-2: 핫 경로 식별 & 성능 기준선 수집**
- [ ] 성능 모니터링 대시보드 활성화
- [ ] DB 쿼리 로그 활성화
- [ ] 프론트엔드 성능 프로파일링 시작
- [ ] Beta 테스터 5명 시스템 할당

**측정할 메트릭:**
```
- API 응답시간 (경로별)
- DB 쿼리 시간 (상위 10)
- 메모리 사용량 (힙 최대)
- 프론트엔드 LCP (Largest Contentful Paint)
- 캐시 히트율 (현재 0%)
```

#### **Day 3-4: 쿼리 최적화 (P0)**
- [ ] `/api/proposals` 쿼리 재작성
- [ ] `/api/workflow/state` JOIN 추가
- [ ] `/api/vault/search` 페이지네이션 최적화
- [ ] 인덱스 추가 (team_id, owner_id, status)

**예상 변경:**
```python
# routes_proposal.py: 쿼리 최적화
# Before: 5개 SELECT (team, users, status, count 분리)
# After: 1개 SELECT with JOINs → -80% 쿼리 수

# routes_analytics.py: 집계 최적화  
# Before: 메모리에서 집계
# After: DB에서 GROUP BY → -70% 데이터 전송
```

#### **Day 5: 메모리 캐시 구현 (P1)**
- [ ] CacheService 구현
- [ ] 검색 결과 캐싱 추가
- [ ] 캐시 무효화 로직 추가
- [ ] 단위 테스트 작성

**구현 파일:**
```
app/services/cache_service.py (새 파일, 300줄)
app/api/routes_vault_chat.py (수정, +50줄)
tests/test_cache_service.py (새 파일, 100줄)
```

---

### **Week 2 (2026-04-24 ~ 04-30)**

#### **Day 6-7: 성능 검증 & 튜닝**
- [ ] 응답시간 <3s 검증 (P95)
- [ ] 메모리 안정성 확인 (heap leak 없음)
- [ ] 캐시 히트율 측정 (목표 50%+)
- [ ] 개별 쿼리 성능 리뷰

**검증 데이터:**
```
메트릭          목표         현재    Pass/Fail
응답시간 P95    <3s          TBD    
메모리 피크      <500MB       TBD    
캐시 히트율     >50%         0%     
DB CPU          <60%         TBD    
```

#### **Day 8-10: 최적화 반복 & 문서화**
- [ ] 성능 리포트 작성
- [ ] 최적화 가이드 문서화
- [ ] 개발팀 교육 (쿼리 최적화 패턴)
- [ ] Phase 2 성능 목표 설정

---

## 🔍 모니터링 대시보드 설정

### 추적할 메트릭

**1. API 성능**
```sql
-- 성능 최악 경로 (Top 10)
SELECT 
  endpoint,
  COUNT(*) as request_count,
  AVG(response_time_ms) as avg_time,
  MAX(response_time_ms) as max_time,
  PERCENTILE_CONT(0.95) WITHIN GROUP(ORDER BY response_time_ms) as p95
FROM api_logs
WHERE created_at > NOW() - INTERVAL '1 hour'
GROUP BY endpoint
ORDER BY avg_time DESC
LIMIT 10;
```

**2. 데이터베이스 성능**
```sql
-- 느린 쿼리 (>1s)
SELECT 
  query_hash,
  query,
  COUNT(*) as execution_count,
  AVG(duration_ms) as avg_duration,
  MAX(duration_ms) as max_duration
FROM pg_stat_statements
WHERE mean_exec_time > 1000
ORDER BY mean_exec_time DESC;
```

**3. 메모리 사용량**
```python
# FastAPI 미들웨어에서 수집
import psutil

@app.middleware("http")
async def memory_monitor(request, call_next):
    process = psutil.Process()
    mem_before = process.memory_info().rss / 1024 / 1024  # MB
    
    response = await call_next(request)
    
    mem_after = process.memory_info().rss / 1024 / 1024
    response.headers["X-Memory-Delta"] = f"{mem_after - mem_before:.2f}MB"
    
    return response
```

---

## 📊 성공 기준

| 메트릭 | 목표 | 권장 | 선택 |
|--------|------|------|------|
| **응답시간 (P95)** | <3s | 평가 KPI | ✅ |
| **메모리 피크** | <800MB | 안정성 | ✅ |
| **캐시 히트율** | >50% | 효율성 | ✅ |
| **DB CPU** | <60% | 리소스 | ✅ |
| **에러율** | <0.1% | 신뢰성 | ✅ |

---

## 🚀 Quick Start (오늘부터 시작)

### **지금 해야 할 5가지 (Today)**

1. ✅ **성능 기준선 수집** (30분)
   ```bash
   # 현재 응답시간 측정
   curl -w "@curl-format.txt" -o /dev/null -s \
     http://localhost:8000/api/proposals?skip=0&limit=10
   ```

2. ✅ **DB 슬로우 로그 활성화** (15분)
   ```sql
   ALTER SYSTEM SET log_min_duration_statement = 1000;
   SELECT pg_reload_conf();
   ```

3. ✅ **메모리 모니터링 시작** (20분)
   ```python
   # app/middleware/memory_monitor.py 추가
   ```

4. ✅ **핫 경로 프로파일링** (30분)
   ```bash
   # routes_proposal.py, routes_vault_chat.py 단계별 로깅 추가
   ```

5. ✅ **캐시 서비스 구현** (2시간)
   ```bash
   # app/services/cache_service.py 작성
   # 기본 LRU 캐시 100줄
   ```

---

## 💡 추가 참고

### 성능 최적화 Best Practices
- **쿼리:** 항상 필요한 컬럼만 SELECT
- **인덱싱:** `(owner_id, created_at DESC)` 복합 인덱스
- **캐싱:** TTL은 데이터 변경 빈도에 맞추기 (5분 ~ 1시간)
- **페이지네이션:** limit=100 최대값 설정
- **배치 처리:** N+1 방지, bulk insert/update 사용

### 측정 도구
- **응답시간:** Prometheus + Grafana (이미 구성)
- **메모리:** psutil, py-spy
- **DB 성능:** pg_stat_statements (PostgreSQL)
- **프론트엔드:** Lighthouse, Web Vitals API

---

**업데이트:** 2026-04-17  
**담당:** Backend Lead (성능 최적화)  
**검토:** 2026-04-24 (중간 점검)  
**완료:** 2026-04-30 (Beta 완료 시)
