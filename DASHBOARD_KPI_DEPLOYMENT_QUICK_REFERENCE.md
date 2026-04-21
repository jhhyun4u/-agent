# Dashboard KPI 스테이징 배포 — 빠른 참조 가이드
**Date:** 2026-05-01  
**Purpose:** 배포 중 빠른 명령어 및 문제 해결 가이드

---

## 🚀 배포 단계별 핵심 명령어

### STAGE 1: 데이터베이스 마이그레이션 (Supabase)

#### 3개 SQL 쿼리 (copy-paste 준비)

**쿼리 1: 전체 마이그레이션 실행**
```sql
-- database/migrations/051_dashboard_kpi_metrics.sql 전체 파일 복사
-- Supabase SQL Editor에 붙여넣고 RUN 클릭
```

**쿼리 2: 뷰 생성 확인**
```sql
SELECT schemaname, matviewname, ispopulated 
FROM pg_matviews 
WHERE matviewname LIKE 'mv_dashboard_%' 
ORDER BY matviewname;
-- 예상: 3개 행 (all ispopulated = t)
```

**쿼리 3: 테이블 + 인덱스 확인**
```sql
SELECT 
  'table' as type, table_name, COUNT(*) as count
FROM information_schema.tables 
WHERE table_schema = 'public' AND table_name = 'dashboard_metrics_history'
GROUP BY table_name
UNION ALL
SELECT 
  'index' as type, tablename, COUNT(*) as count
FROM pg_indexes 
WHERE schemaname = 'public' AND (tablename LIKE 'mv_dashboard_%' OR tablename = 'dashboard_metrics_history')
GROUP BY tablename
ORDER BY type, count DESC;
-- 예상: 1개 table + 11개 indices
```

**쿼리 4: RLS 정책 확인**
```sql
SELECT tablename, policyname 
FROM pg_policies 
WHERE tablename = 'dashboard_metrics_history';
-- 예상: 1개 행 (dashboard_metrics_history_read)
```

**쿼리 5: 데이터 샘플 확인**
```sql
-- 개인
SELECT COUNT(*) as individual_count FROM mv_dashboard_individual;

-- 팀
SELECT COUNT(*) as team_count FROM mv_dashboard_team WHERE team_id IS NOT NULL;

-- 경영진
SELECT COUNT(*) as executive_count FROM mv_dashboard_executive WHERE org_id IS NOT NULL;
```

---

### STAGE 2: 백엔드 배포 (Railway)

#### 자동 배포 확인
```bash
# 1. 현재 브랜치 확인
git branch
# 예상: * main

# 2. 최신 커밋 확인
git log --oneline -1
# 예상: [hash] Dashboard KPI DO/CHECK complete

# 3. Railway 자동 배포 확인
# → Vercel 대시보드: https://railway.app
# → Projects > tenopa-proposer > Deployments
# → Status: ✅ Success
```

#### API 헬스 체크 (3개 테스트)

**테스트 1: 헬스 체크**
```bash
curl -X GET "https://[staging-api].railway.app/api/dashboard/health" \
  -H "Authorization: Bearer [token]"

# 예상 응답:
# {
#   "status": "healthy",
#   "database": "connected",
#   "cache": "connected",
#   "version": "1.0.0"
# }
```

**테스트 2: 개인 대시보드**
```bash
curl -X GET "https://[staging-api].railway.app/api/dashboard/metrics/individual?period=ytd" \
  -H "Authorization: Bearer [token]" \
  -H "Content-Type: application/json" | jq '.'
```

**테스트 3: 팀 대시보드**
```bash
curl -X GET "https://[staging-api].railway.app/api/dashboard/metrics/team?period=ytd" \
  -H "Authorization: Bearer [token]" | jq '.metrics'
```

#### 성능 측정 (응답 시간)
```bash
# 10회 측정 (캐시 히트 패턴 확인)
for i in {1..10}; do
  echo "=== Request $i ==="
  time curl -s "https://[staging-api].railway.app/api/dashboard/metrics/individual?period=ytd" \
    -H "Authorization: Bearer [token]" | jq '.cache_hit'
  sleep 1
done

# 예상 패턴:
# Request 1: cache_hit = false, ~1000-1500ms
# Request 2-5: cache_hit = true, ~100-200ms
# Request 5 이후: cache_hit = false (TTL=300초 후 갱신), ~1000-1500ms
```

---

### STAGE 3: 프론트엔드 배포 (Vercel)

#### 자동 배포 확인
```
Vercel 대시보드: https://vercel.com
Project: tenopa-proposer
Status: Ready ✅
Preview URL: https://[project]-[hash].vercel.app
```

#### 페이지 로드 확인
```bash
# 브라우저에서 열기
https://[staging-frontend].vercel.app/dashboards

# DevTools (F12) → Network 탭
# 예상:
# ✅ All requests 200 OK
# ✅ Page load time < 3s
# ✅ No JS errors (Console 탭)
```

---

## 🔧 문제 해결 가이드

### 문제 1: SQL 마이그레이션 실패
**증상:** Supabase SQL Editor에서 빨간 에러 메시지

**원인 분석:**
```sql
-- 원인 1: 뷰 이미 존재
SELECT * FROM pg_matviews WHERE matviewname LIKE 'mv_dashboard_%';
-- IF NOT EXISTS 절이 있으므로 무시됨, 다시 실행해도 OK

-- 원인 2: 테이블 이미 존재
SELECT * FROM information_schema.tables WHERE table_name = 'dashboard_metrics_history';
-- IF NOT EXISTS 절이 있으므로 무시됨, 다시 실행해도 OK

-- 원인 3: 권한 부족
SELECT current_user;
-- 예상: postgres 또는 service role 사용자
-- 해결: Supabase "SQL Editor" 사용 (자동으로 올바른 권한)
```

**해결:**
1. 전체 SQL 코드 다시 복사 (파일에서)
2. 공백 문자 확인 (줄 바꿈, 탭 등)
3. Supabase SQL Editor "Clear" 버튼으로 이전 쿼리 삭제
4. 다시 붙여넣고 RUN 클릭

---

### 문제 2: API 헬스 체크 실패 (500 에러)
**증상:** `curl /api/dashboard/health` → 500 Internal Server Error

**원인 분석:**
```bash
# 1. Railway 로그 확인
# https://railway.app > Deployments > Logs
# 에러 메시지 확인 (Python traceback)

# 2. 데이터베이스 연결 확인
curl -X GET "https://[staging-api].railway.app/api/dashboard/health" \
  -H "Authorization: Bearer [token]" -v
# 응답: { "database": "disconnected" }?

# 3. 환경 변수 확인
# Railway Dashboard > Variables > SUPABASE_URL, SUPABASE_KEY 존재?
```

**해결:**
1. Railway 로그에서 에러 메시지 복사
2. Backend 개발자에게 전달
3. 일반적인 원인:
   - [ ] SUPABASE_URL 잘못됨 → 확인 및 수정
   - [ ] SUPABASE_KEY 만료됨 → Supabase 대시보드에서 새 키 생성
   - [ ] 데이터베이스 마이그레이션 미완료 → STAGE 1 재실행

---

### 문제 3: API 응답 시간 느림 (> 3초)
**증상:** `curl /api/dashboard/metrics/individual` → 3초 이상 소요

**원인 분석:**
```bash
# 1. 캐시 상태 확인
curl -X GET "https://[staging-api].railway.app/api/dashboard/metrics/individual?period=ytd" \
  -H "Authorization: Bearer [token]" | jq '.cache_hit'
# true → 캐시 정상 (200ms 이내)
# false → DB 조회 (1-2초 정상, > 3초는 느림)

# 2. 데이터베이스 쿼리 성능 확인 (Supabase)
-- Supabase > Logs > Database Logs
-- 쿼리 실행 시간 > 2초?

# 3. 네트워크 지연 확인
curl -w "Time: %{time_total}s\n" -X GET "https://[staging-api].railway.app/api/dashboard/metrics/individual" \
  -H "Authorization: Bearer [token]" -o /dev/null -s
# > 2초: 네트워크 or 서버 문제
```

**해결:**
1. **캐시 미스 (DB 조회) > 2초:**
   - DB 쿼리 최적화 필요 (인덱스 확인)
   - Supabase에서 쿼리 실행 시간 확인:
     ```sql
     EXPLAIN ANALYZE
     SELECT * FROM mv_dashboard_individual LIMIT 10;
     ```

2. **캐시 히트 > 200ms:**
   - Redis 연결 문제
   - Railway Redis endpoint 확인

3. **네트워크 지연 > 1초:**
   - Railway 지역 확인 (nearest region 선택)
   - DNS 확인: `nslookup [staging-api].railway.app`

---

### 문제 4: 프론트엔드 404 오류
**증상:** https://[staging-frontend].vercel.app/dashboards → 404 Not Found

**원인 분석:**
```bash
# 1. Vercel 배포 상태 확인
# https://vercel.com > Projects > tenopa-proposer
# Status: Ready? or Building/Error?

# 2. URL 확인
# 올바른 URL: https://[project-name]-[hash].vercel.app/dashboards
# 오타 확인: 대문자/소문자, 슬래시 위치

# 3. 페이지 존재 여부
# frontend/app/dashboards 디렉토리/파일 존재?
# 또는 frontend/pages/dashboards.tsx?
```

**해결:**
1. Vercel "Deployments" 탭에서 배포 상태 확인 → "Ready" 상태인지 확인
2. Preview URL 정확히 복사 (대시보드 UI에서 "Copy URL")
3. `/dashboards` 대신 `/dashboards/individual` 시도
4. 프론트엔드 개발자에게 페이지 경로 확인 요청

---

### 문제 5: 프론트엔드 API 호출 실패 (401/403)
**증상:** DevTools Network 탭에서 GET /api/dashboard/metrics → 401 Unauthorized

**원인 분석:**
```javascript
// Browser Console (F12 > Console)
// 다음 코드 실행
fetch('https://[staging-api].railway.app/api/dashboard/metrics/individual', {
  headers: {
    'Authorization': 'Bearer [token]'
  }
}).then(r => r.json()).then(console.log);

// 응답 확인:
// { "detail": "미인증" } → 토큰 만료 or 잘못됨
// { "detail": "권한 없음" } → 사용자 role 확인 필요
```

**해결:**
1. **토큰 만료:**
   - 프론트엔드 로그아웃 → 재로그인
   - 또는 localStorage에서 토큰 삭제: `localStorage.removeItem('token')`

2. **권한 부족:**
   - 개인 대시보드 요청: 모든 사용자 OK
   - 팀 대시보드 요청: 팀장 이상 필요 (user.role in ['lead', 'director', 'executive', 'admin'])
   - 본부 대시보드 요청: 본부장 이상 필요 (user.role in ['director', 'executive', 'admin'])
   - 경영진 대시보드 요청: 경영진만 (user.role in ['executive', 'admin'])

3. **API URL 오류:**
   - .env.local에서 `NEXT_PUBLIC_API_URL` 확인
   - 오타: `railwa.app` (X) vs `railway.app` (O)

---

### 문제 6: 데이터 표시 안 됨 (KPI = 0 or blank)
**증상:** 대시보드 로드되지만 모든 KPI가 0 또는 "—"

**원인 분석:**
```sql
-- Supabase SQL Editor에서 실행
-- 뷰에 데이터 있는지 확인

-- 개인
SELECT COUNT(*) FROM mv_dashboard_individual;
-- 예상: > 0

-- 팀
SELECT COUNT(*) FROM mv_dashboard_team WHERE team_id IS NOT NULL;
-- 예상: > 0

-- 경영진
SELECT COUNT(*) FROM mv_dashboard_executive WHERE org_id IS NOT NULL;
-- 예상: > 0

-- 만약 모두 0이면?
SELECT COUNT(*) FROM proposals;
-- 예상: > 0 (원본 데이터 확인)
```

**해결:**
1. **원본 데이터 없음:**
   - proposals 테이블에 실제 데이터 있는지 확인
   - 테스트 데이터 생성 필요 (scripts/seed_data.py 실행)

2. **뷰 갱신 안 됨:**
   ```sql
   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_individual;
   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_team;
   REFRESH MATERIALIZED VIEW CONCURRENTLY mv_dashboard_executive;
   ```

3. **사용자 RLS 필터링:**
   - 현재 로그인한 사용자의 owner_id or team_id와 일치하는 데이터만 표시
   - 다른 사용자로 테스트해보기

---

### 문제 7: 캐시 작동 안 함
**증상:** 같은 요청을 반복해도 `cache_hit` = false (항상 DB 조회)

**원인 분석:**
```bash
# 1. Redis 연결 확인
# Railway 환경 변수 확인:
# REDIS_URL = redis://[host]:6379

# 2. API 로그 확인
# Railway Logs에서 캐시 관련 로그:
# "💾 대시보드 캐시 HIT" vs "❌ 캐시 연결 실패"

# 3. 캐시 TTL 확인
# API 응답에서 cache_ttl_seconds = 300?
```

**해결:**
1. **Redis 연결 실패:**
   - Railway REDIS_URL 확인 (redis://... 형식)
   - Redis 서비스 running 상태 확인

2. **캐시 TTL 너무 짧음:**
   - CACHE_TTL 환경 변수 확인 (기본값: 300초)
   - 너무 짧으면 항상 미스 발생

3. **캐시 키 불일치:**
   - 같은 `period`, `dashboard_type`, `user_id`로 요청해야 같은 캐시 히트
   - period를 ytd → mtd로 바꾸면 다른 캐시

---

## ✅ 배포 체크리스트

### Pre-Deployment
- [ ] Git status clean (모든 변경 커밋)
- [ ] 환경 변수 설정 (Railway, Vercel)
- [ ] 데이터베이스 백업 완료 (optional)
- [ ] 롤백 계획 준비

### STAGE 1: DB 마이그레이션
- [ ] SQL 파일 전체 복사 (동일하게)
- [ ] Supabase SQL Editor 실행
- [ ] 5개 검증 쿼리 모두 통과
- [ ] 뷰 갱신 함수 실행

### STAGE 2: API 배포
- [ ] Git push 완료 (Railway auto-deploy 트리거)
- [ ] Railway 배포 성공 확인 (Logs)
- [ ] 3개 API 헬스 체크 통과
- [ ] 성능 베이스라인 기록

### STAGE 3: Frontend 배포
- [ ] Vercel auto-deploy 확인
- [ ] Preview URL 로드 성공
- [ ] 모든 리소스 로드됨 (Network 탭 200 OK)

### 검증 (25개 항목)
- [ ] Individual Dashboard (5/5)
- [ ] Team Dashboard (5/5)
- [ ] Department Dashboard (5/5)
- [ ] Executive Dashboard (5/5)
- [ ] Responsive Design (5/5)

### Post-Deployment
- [ ] 모니터링 설정 (헬스 체크, 에러율)
- [ ] 배포 완료 보고서 작성
- [ ] 사용자 공지 (스테이징 URL 안내)

---

## 📞 긴급 연락처

| 담당 | 이메일 | 전화 | 응답시간 |
|------|--------|------|---------|
| 데이터베이스 (Supabase) | db@tenopa.co.kr | — | 15분 |
| 백엔드/API (Railway) | backend@tenopa.co.kr | — | 15분 |
| 프론트엔드 (Vercel) | frontend@tenopa.co.kr | — | 15분 |
| 운영/배포 | ops@tenopa.co.kr | — | 30분 |

---

## 🔄 롤백 빠른 실행

**STAGE 3 Frontend 롤백:**
```
1. https://vercel.com > Projects > tenopa-proposer
2. Deployments 탭 > 이전 배포 선택
3. "Promote to Production" 클릭
4. 재배포 자동 진행 (2-3분)
```

**STAGE 2 API 롤백:**
```
1. https://railway.app > Projects > tenopa-proposer
2. Deployments 탭 > 이전 배포 선택
3. 배포 클릭 > 재시작
4. 자동 복구 (3-5분)
```

**STAGE 1 DB 롤백:**
```sql
-- Supabase SQL Editor
-- 마이그레이션 제거 (주의: 데이터 손실 위험)
DROP MATERIALIZED VIEW IF EXISTS mv_dashboard_individual CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_dashboard_team CASCADE;
DROP MATERIALIZED VIEW IF EXISTS mv_dashboard_executive CASCADE;
DROP TABLE IF EXISTS dashboard_metrics_history CASCADE;
DROP FUNCTION IF EXISTS refresh_dashboard_views() CASCADE;
DROP FUNCTION IF EXISTS populate_dashboard_metrics_history() CASCADE;
```

---

**모든 명령어가 준비되었습니다! 배포를 시작하세요. 🚀**
