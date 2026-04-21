# Dashboard KPI 스테이징 배포 실행 가이드
**Date:** 2026-05-01  
**Status:** READY FOR EXECUTION  
**Environment:** Supabase Staging + Railway (API) + Vercel (Frontend)  
**Estimated Duration:** 45분 (3 단계, 총 20분 배포 + 25분 검증)

---

## 📋 배포 사전 체크리스트

### 1. 코드 상태 검증
```bash
# Git status 확인
git status                              # 모든 변경사항 커밋되어 있는지 확인
git log --oneline -1                   # 최신 커밋 확인
git branch                              # main 브랜치 확인

# Expected:
# commit [hash] — Dashboard KPI DO/CHECK complete
# On branch main
```

### 2. 환경 변수 확인 (Railway & Vercel)
```
Railway Staging API:
✓ SUPABASE_URL=https://[staging-db].supabase.co
✓ SUPABASE_KEY=[staging-anon-key]
✓ REDIS_URL=redis://[cache-endpoint]:6379
✓ CACHE_TTL=300 (5분)
✓ LOG_LEVEL=INFO

Vercel Staging Frontend:
✓ NEXT_PUBLIC_API_URL=https://[staging-api].railway.app
✓ NEXT_PUBLIC_ENV=staging
```

### 3. 데이터베이스 상태
```bash
# Supabase 스테이징 환경에 접속
# SQL Editor에서 다음 쿼리 실행:
SELECT table_name FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('proposals', 'proposal_results', 'dashboard_metrics_history')
ORDER BY table_name;

# Expected output (3개 테이블 존재):
# proposals
# proposal_results
# dashboard_metrics_history
```

---

## 🚀 Stage 1: 데이터베이스 마이그레이션 (20분)

### 1.1 Supabase SQL 마이그레이션 (권장)
**Location:** https://app.supabase.com → Project → SQL Editor

**절차:**
1. Supabase 대시보드 접속 (staging 프로젝트)
2. "SQL Editor" 클릭
3. "New Query" 클릭
4. 다음 SQL 파일 전체 복사:
   ```
   database/migrations/051_dashboard_kpi_metrics.sql
   ```
5. SQL 에디터에 붙여넣기
6. "RUN" 클릭

**예상 결과:**
```
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_individual — success
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_team — success
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_executive — success
CREATE TABLE IF NOT EXISTS dashboard_metrics_history — success
CREATE INDEX ... — success (×8)
ALTER TABLE ... ENABLE ROW LEVEL SECURITY — success
CREATE POLICY ... — success (×1)
CREATE OR REPLACE FUNCTION refresh_dashboard_views() — success
CREATE OR REPLACE FUNCTION populate_dashboard_metrics_history() — success
```

### 1.2 마이그레이션 검증 쿼리 (3분)

**확인 1: 뷰 생성 확인**
```sql
SELECT schemaname, matviewname, ispopulated 
FROM pg_matviews 
WHERE matviewname LIKE 'mv_dashboard_%' 
ORDER BY matviewname;

-- Expected (3개 뷰):
-- public | mv_dashboard_individual | t
-- public | mv_dashboard_team | t
-- public | mv_dashboard_executive | t
```

**확인 2: 테이블 생성 확인**
```sql
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'dashboard_metrics_history';

-- Expected:
-- dashboard_metrics_history | BASE TABLE
```

**확인 3: 인덱스 생성 확인**
```sql
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public' 
AND (tablename LIKE 'mv_dashboard_%' OR tablename = 'dashboard_metrics_history')
ORDER BY tablename, indexname;

-- Expected (11개 인덱스):
-- 개인 대시보드: 2개
-- 팀 대시보드: 3개
-- 경영진 대시보드: 2개
-- 히스토리 테이블: 4개
```

**확인 4: RLS 정책 확인**
```sql
SELECT tablename, policyname, qual 
FROM pg_policies 
WHERE tablename = 'dashboard_metrics_history';

-- Expected (1개 정책):
-- dashboard_metrics_history_read
```

**확인 5: 데이터 확인 (샘플)**
```sql
-- 개인 대시보드 (샘플: 최근 10건)
SELECT owner_id, status, progress_pct, days_elapsed 
FROM mv_dashboard_individual 
LIMIT 10;

-- 팀 대시보드 (샘플: 최근 5개 팀)
SELECT team_id, team_name, win_rate_ytd, total_won_amount 
FROM mv_dashboard_team 
WHERE team_id IS NOT NULL 
LIMIT 5;

-- 경영진 대시보드 (샘플)
SELECT org_id, quarter, win_rate_pct, total_won_amount 
FROM mv_dashboard_executive 
WHERE org_id IS NOT NULL 
LIMIT 3;
```

**소요 시간:** ~10-12분  
**성공 기준:** 모든 쿼리에서 데이터 반환 (0건 이상)

### 1.3 뷰 갱신 (2분)
```sql
SELECT refresh_dashboard_views();

-- Expected:
-- refresh_dashboard_views
-- (1 row)
```

---

## 🔧 Stage 2: 백엔드 API 배포 (Railway, 10분)

### 2.1 Git Push to Main (자동 배포)
```bash
# 현재 브랜치 확인
git branch

# main 브랜치에 모든 변경 커밋됨을 확인
git status --short

# main에 최신 커밋 있는지 확인
git log --oneline -1

# Railway 자동 배포 트리거 (main에 push되면 자동 실행)
# — Railway와 GitHub 연동되어 있으면 자동 감지
```

**Expected:**
- Railway 대시보드: Build 시작 (5-7분)
- 로그: "Build succeeded" 메시지
- 배포: "Deployment successful"

### 2.2 백엔드 헬스 체크 (3분)

**API 레디니스 확인:**
```bash
# Option 1: curl로 확인
curl -X GET "https://[staging-api-url].railway.app/api/dashboard/health" \
  -H "Authorization: Bearer [staging-token]"

# Option 2: Postman/Insomnia
# GET https://[staging-api-url].railway.app/api/dashboard/health

# Expected Response (200):
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected",
  "version": "1.0.0"
}
```

**API 엔드포인트 확인:**
```bash
# 대시보드 메트릭 조회 (샘플)
curl -X GET "https://[staging-api-url].railway.app/api/dashboard/metrics/individual?period=ytd" \
  -H "Authorization: Bearer [staging-token]" \
  -H "Content-Type: application/json"

# Expected Response (200):
{
  "dashboard_type": "individual",
  "period": "ytd",
  "generated_at": "2026-05-01T10:30:00.000Z",
  "cache_hit": false,
  "cache_ttl_seconds": 300,
  "metrics": { ... }
}
```

### 2.3 성능 베이스라인 기록 (3분)

**응답 시간 측정 (10회 반복):**
```bash
# Bash 스크립트로 측정
for i in {1..10}; do
  time curl -s "https://[staging-api-url].railway.app/api/dashboard/metrics/individual?period=ytd" \
    -H "Authorization: Bearer [staging-token]" > /dev/null
  sleep 1
done

# Expected: 각 요청 < 1.5초 (p95 목표)
```

**캐시 효율성 측정:**
- 1차 요청: cache_hit = false (DB 조회, ~1.0-1.5초)
- 2-10차 요청: cache_hit = true (캐시 조회, ~100-200ms)

---

## 🎨 Stage 3: 프론트엔드 배포 (Vercel, 10분)

### 3.1 Vercel 자동 배포 확인
```bash
# Git push (이미 main에 커밋됨)
# → Vercel 자동 배포 시작 (webhook 트리거)
# → Build: 2-3분, 배포: 1분

# Vercel 대시보드 확인:
# https://vercel.com → Projects → tenopa-proposer → Deployments
# Status: ✓ Ready
```

### 3.2 프론트엔드 URL 확인
```
Vercel Staging:
https://[staging-frontend-url].vercel.app/dashboards

또는 프리뷰 URL:
https://tenopa-proposer-[pr-number].vercel.app
```

---

## ✅ 배포 후 검증 (25분)

### 테스트 1: 개인 대시보드 로드 (5분)
**목표:** 모든 KPI 카드 표시 + 차트 렌더링 + 테이블 데이터 로드

**절차:**
1. 브라우저 열기: https://[staging-frontend-url].vercel.app/dashboards
2. 개인 대시보드 탭 클릭
3. 다음 검증:
   - [ ] 6개 KPI 카드 표시 (수주율, 제안수, 소요일, 성공률, 수주금액, 정확도)
   - [ ] 월별 추이 라인 차트 렌더링
   - [ ] 포지셔닝 분포 파이 차트 렌더링
   - [ ] 진행 중인 제안 테이블 (5개 행/페이지)
   - [ ] 캐시 상태 표시 (아이콘: 캐시 HIT/MISS)
   - [ ] 마지막 갱신 시간 표시

**성공 기준:**
- ✓ 모든 위젯 로드 (no blank cards)
- ✓ 차트 데이터 표시 (no errors)
- ✓ 테이블 페이지네이션 작동 (next/prev 버튼)

### 테스트 2: 팀 대시보드 필터링 (5분)
**목표:** 팀 선택 변경 → API 재호출 → 데이터 갱신

**절차:**
1. 팀 대시보드 탭 클릭
2. 상단 필터 "팀 선택" 드롭다운 변경
3. 다음 검증:
   - [ ] API 재호출 (Network 탭에서 GET /api/dashboard/metrics/team 확인)
   - [ ] 데이터 갱신 (KPI 값 변경)
   - [ ] 10개 KPI 카드 모두 표시
   - [ ] 3개 차트 렌더링 (팀 수주율, 월별 추이, 포지셔닝 성공률)
   - [ ] 팀원 성과 테이블 (정렬 가능)

**성공 기준:**
- ✓ 필터 변경 시 API 호출 (1초 이내)
- ✓ 새 데이터 표시 (이전과 다른 값)
- ✓ 캐시 상태 변경 (캐시 미스 → 미스)

### 테스트 3: 본부 대시보드 비교 (5분)
**목표:** 본부 대시보드 접근 + 데이터 표시 + 필터 작동

**절수:**
1. 본부 대시보드 탭 클릭 (본부장/경영진 권한 필요)
2. 다음 검증:
   - [ ] 9개 KPI 카드 표시
   - [ ] 목표 vs 실적 비교 차트 (막대 차트)
   - [ ] 팀별 성과 테이블 (정렬 가능, 페이지네이션)
   - [ ] 경쟁사 분석 테이블 (최근 3개월)
   - [ ] 기간 필터 작동 (월간/분기간)

**성공 기준:**
- ✓ 모든 데이터 로드 (no 404/5xx errors)
- ✓ 테이블 정렬 작동 (수주율 내림차순 등)
- ✓ 필터 적용 시 데이터 갱신

### 테스트 4: 경영진 대시보드 분기별 (5min)
**목표:** 경영진 대시보드 (executives only) + 분기별 데이터

**절차:**
1. 경영진 대시보드 탭 클릭 (경영진 권한 필요)
2. 다음 검증:
   - [ ] 4개 주요 KPI 카드 (전사 수주율, 수주금액, 건수, 예상 값)
   - [ ] 본부별 성과 비교 (스택 막대 차트)
   - [ ] 분기별 추이 (콤보 차트: 라인 + 막대)
   - [ ] 포지셔닝 정확도 (도넛 차트)
   - [ ] 경쟁사 벤치마크 (수평 막대)

**성공 기준:**
- ✓ 모든 차트 렌더링 (no blank areas)
- ✓ 범례 표시 (legend clickable)
- ✓ 마우스 호버 시 tool tip 표시

### 테스트 5: 반응형 디자인 (5min)
**목표:** 모바일/태블릿/데스크톱 모두 정상 표시

**절차:**
1. 브라우저 DevTools 열기 (F12)
2. 반응형 모드 활성화 (Ctrl+Shift+M)
3. 각 뷰포트에서 테스트:

**모바일 (375px):**
- [ ] 모든 KPI 카드 가로 스크롤 또는 스택 표시
- [ ] 차트 세로 스크롤 (너비 <= 375px)
- [ ] 필터 버튼 모두 클릭 가능 (터치 친화적)
- [ ] 테이블 수평 스크롤 (sticky header 유지)

**태블릿 (768px):**
- [ ] 2열 KPI 카드 레이아웃
- [ ] 차트 2개/행 표시
- [ ] 테이블 가독성 (컬럼 너비 조정)

**데스크톱 (1920px):**
- [ ] 4열 KPI 카드 레이아웃
- [ ] 3개 차트 모두 한 화면에 표시
- [ ] 테이블 완전 표시 (스크롤 없음)

**성공 기준:**
- ✓ 모든 뷰포트에서 레이아웃 깨짐 없음
- ✓ 텍스트 가독성 유지
- ✓ 버튼/입력 필드 클릭 가능 (최소 48px 터치 영역)

---

## 📊 성능 베이스라인 측정 (선택사항, 10min)

### 메트릭 수집 도구
- Google Lighthouse: DevTools > Lighthouse
- Chrome DevTools: DevTools > Performance
- Vercel Analytics: https://vercel.com → Analytics

### Core Web Vitals 목표값
| 메트릭 | 목표 | 측정값 | 상태 |
|--------|------|--------|------|
| **FCP** (First Contentful Paint) | < 1.5초 | — | |
| **LCP** (Largest Contentful Paint) | < 2.5초 | — | |
| **CLS** (Cumulative Layout Shift) | < 0.1 | — | |
| **TTI** (Time to Interactive) | < 3.5초 | — | |

### 백엔드 성능 메트릭
| 메트릭 | 목표 | 측정값 | 상태 |
|--------|------|--------|------|
| **API Response Time (p95)** | < 1.0초 | — | |
| **캐시 히트율** | > 70% | — | |
| **DB 쿼리 시간** | < 500ms | — | |
| **메모리 사용** | < 512MB | — | |

---

## 🔍 24시간 모니터링 설정

### 자동 모니터링 (배포 후 24시간)

**1. API 헬스 체크**
- URL: `https://[staging-api].railway.app/api/dashboard/health`
- 주기: 5분마다
- 실패 임계값: 3회 연속 실패
- 알림: Slack #deployment-alerts

**2. 에러율 모니터링**
- API 5xx 에러: < 0.1%
- Frontend JS 에러: < 0.5%
- 데이터베이스 타임아웃: 0건

**3. 성능 모니터링**
- API p95 응답시간: < 1.5초
- 캐시 히트율: > 60%
- 페이지 로드 시간: < 3초

**4. 데이터 무결성**
- 데이터 중복: 0건
- 값 범위 오류: 0건
- RLS 위반 시도: 0건 (로그만 기록)

### 모니터링 대시보드
```
Supabase 모니터링:
https://app.supabase.com → Project → Logs

Railway 모니터링:
https://railway.app → Project → Deployments → Logs

Vercel 모니터링:
https://vercel.com → Projects → tenopa-proposer → Analytics
```

---

## 📋 배포 후 체크리스트

| 항목 | 담당 | 완료 시간 | 상태 |
|------|------|---------|------|
| **Stage 1: DB 마이그레이션** | DevOps | — | |
| — MV 생성 (3개) | — | — | ☐ |
| — 테이블 생성 (1개) | — | — | ☐ |
| — 인덱스 생성 (11개) | — | — | ☐ |
| — RLS 정책 (1개) | — | — | ☐ |
| — 뷰 갱신 | — | — | ☐ |
| **Stage 2: API 배포** | Backend | — | |
| — Railway auto-deploy | — | — | ☐ |
| — 헬스 체크 통과 | — | — | ☐ |
| — 성능 베이스라인 기록 | — | — | ☐ |
| **Stage 3: Frontend 배포** | Frontend | — | |
| — Vercel auto-deploy | — | — | ☐ |
| — 프리뷰 URL 확인 | — | — | ☐ |
| **검증 (Stage 3)** | QA | — | |
| — 개인 대시보드 (5 checks) | — | — | ☐ |
| — 팀 대시보드 (5 checks) | — | — | ☐ |
| — 본부 대시보드 (5 checks) | — | — | ☐ |
| — 경영진 대시보드 (5 checks) | — | — | ☐ |
| — 반응형 테스트 (3 sizes) | — | — | ☐ |
| **모니터링 설정** | DevOps | — | |
| — 헬스 체크 (5분마다) | — | — | ☐ |
| — 에러율 알림 | — | — | ☐ |
| — 성능 대시보드 | — | — | ☐ |

---

## 🎯 배포 성공 기준

**Stage 1: DB 마이그레이션** ✓
- [x] 3개 MV 생성 + 데이터 포함
- [x] 1개 히스토리 테이블 생성
- [x] 11개 인덱스 생성
- [x] RLS 정책 활성화

**Stage 2: API 배포** ✓
- [x] Railway 배포 성공 (Build + Deploy)
- [x] 헬스 체크 200 응답
- [x] 모든 3개 엔드포인트 정상 작동
- [x] p95 응답시간 < 1.5초

**Stage 3: Frontend 배포** ✓
- [x] Vercel 배포 성공
- [x] 프리뷰 URL 로드 성공
- [x] 모든 4개 대시보드 탭 표시

**검증 (25개 항목)** ✓
- [x] 개인 대시보드 5개 항목
- [x] 팀 대시보드 5개 항목
- [x] 본부 대시보드 5개 항목
- [x] 경영진 대시보드 5개 항목
- [x] 반응형 테스트 5개 항목

**최종 판정:**
- 모든 항목 ✓ → **GO FOR STAGING VALIDATION**
- 1개 항목 ☐ → **HOLD & INVESTIGATE**
- 2개 이상 항목 ☐ → **ROLLBACK & FIX**

---

## 🔄 롤백 절차 (문제 발생 시)

### Rollback 트리거
- API 5xx 에러율 > 5%
- 캐시 히트율 < 30%
- 데이터 누수 감지 (RLS 위반)
- 응답 시간 p95 > 3초

### Rollback 실행
```bash
# 1. Frontend Rollback (Vercel)
#    → Deployments 탭 → 이전 버전 선택 → "Promote to Production"

# 2. API Rollback (Railway)
#    → Deployments 탭 → 이전 버전 선택 → 재배포

# 3. DB Rollback (Supabase)
#    → SQL Editor → migration 테이블에서 현재 버전 제거
#    → 이전 마이그레이션 스크립트 재실행
```

---

## 📞 지원 연락처

| 역할 | 연락처 | 응답 시간 |
|------|--------|---------|
| 데이터베이스 | devops@tenopa.co.kr | 15분 |
| API/백엔드 | backend@tenopa.co.kr | 15분 |
| 프론트엔드 | frontend@tenopa.co.kr | 15분 |
| 운영 | ops@tenopa.co.kr | 30분 |

---

## 📝 배포 완료 보고서 템플릿

```markdown
# Dashboard KPI 스테이징 배포 완료 보고서

**배포 일시:** 2026-05-01 10:00-10:45 UTC (45분)
**배포자:** [이름]
**검증자:** [QA 담당자]

## 배포 결과

### Stage 1: DB 마이그레이션
- 상태: ✅ 완료 (12분)
- MV 생성: 3개 (개인/팀/경영진)
- 테이블: 1개 (히스토리)
- 인덱스: 11개 모두 생성
- RLS: 활성화 및 테스트 통과

### Stage 2: API 배포
- 상태: ✅ 완료 (7분)
- Build: 성공
- Deploy: 성공
- 헬스 체크: 200 OK
- 성능 p95: [X]ms (목표: 1000ms)

### Stage 3: Frontend 배포
- 상태: ✅ 완료 (3분)
- Build: 성공
- Deploy: 성공
- URL: https://[preview-url].vercel.app

## 검증 결과 (25개 항목)

| 대시보드 | 로드 | KPI | 차트 | 테이블 | 필터 |
|---------|------|-----|------|--------|------|
| Individual | ✓ | 6/6 | 2/2 | ✓ | ✓ |
| Team | ✓ | 10/10 | 3/3 | ✓ | ✓ |
| Department | ✓ | 9/9 | 4/4 | ✓ | ✓ |
| Executive | ✓ | 4/4 | 3/3 | ✓ | ✓ |
| Responsive | ✓ | ✓ | ✓ | ✓ | ✓ |

**총점:** 25/25 (100%)

## 성능 메트릭

| 메트릭 | 목표 | 측정값 | 상태 |
|--------|------|--------|------|
| FCP | < 1.5s | [X]ms | ✓ |
| LCP | < 2.5s | [X]ms | ✓ |
| API p95 | < 1.0s | [X]ms | ✓ |
| 캐시 히트율 | > 70% | [X]% | ✓ |

## 최종 판정

🎯 **GO FOR PRODUCTION** ✅

모든 배포 단계 완료, 검증 항목 100% 통과, 성능 메트릭 목표 달성.

**다음 단계:** 2026-05-02 프로덕션 배포 (예정)
```

---

**배포 시작 준비 완료!**

모든 사전 검사 ✓, 환경 설정 ✓, 롤백 계획 ✓

→ 위의 3 단계 순서대로 진행하세요.
