# Dashboard KPI 스테이징 배포 실행 추적표
**Date:** 2026-05-01  
**Target:** Staging Environment (Supabase + Railway + Vercel)  
**Duration:** 45분 (Stage 1-3: 20분 배포 + 25분 검증)

---

## 📊 배포 단계별 진행 상태

### STAGE 1: 데이터베이스 마이그레이션 (20분)

#### Phase 1.1: SQL 마이그레이션 (12분)
**Location:** Supabase SQL Editor (https://app.supabase.com)
**File:** `database/migrations/051_dashboard_kpi_metrics.sql`

**진행 상황:**

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: SQL 에디터 접속                                      │
├─────────────────────────────────────────────────────────────┤
│ [ ] 1. Supabase 대시보드 열기                                 │
│ [ ] 2. Staging 프로젝트 선택                                  │
│ [ ] 3. "SQL Editor" 메뉴 클릭                                 │
│ [ ] 4. "New Query" 버튼 클릭                                  │
│ 예상: SQL 에디터 빈 화면                                      │
└─────────────────────────────────────────────────────────────┘
```

**소요 시간:** 1-2분

```
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: SQL 코드 복사 및 실행                                 │
├─────────────────────────────────────────────────────────────┤
│ [ ] 1. 파일 열기: database/migrations/051_dashboard_kpi_metrics.sql
│ [ ] 2. 전체 내용 선택 (Ctrl+A)                                │
│ [ ] 3. 복사 (Ctrl+C)                                         │
│ [ ] 4. SQL 에디터에 붙여넣기 (Ctrl+V)                          │
│ [ ] 5. "RUN" 버튼 클릭                                        │
│ 예상: "Query executed successfully" 메시지                    │
└─────────────────────────────────────────────────────────────┘
```

**소요 시간:** 3-4분
**예상 결과:**
```
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_individual
│ ✅ Success

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_team  
│ ✅ Success

CREATE MATERIALIZED VIEW IF NOT EXISTS mv_dashboard_executive
│ ✅ Success

CREATE TABLE IF NOT EXISTS dashboard_metrics_history
│ ✅ Success

CREATE INDEX [×8 indices]
│ ✅ Success (×8)

ALTER TABLE dashboard_metrics_history ENABLE ROW LEVEL SECURITY
│ ✅ Success

CREATE POLICY dashboard_metrics_history_read
│ ✅ Success

CREATE OR REPLACE FUNCTION refresh_dashboard_views()
│ ✅ Success

CREATE OR REPLACE FUNCTION populate_dashboard_metrics_history()
│ ✅ Success

---
Query executed successfully.
Duration: [X]ms
```

#### Phase 1.2: 마이그레이션 검증 (8분)

**검증 1: 뷰 생성 확인** (2분)

```sql
-- 쿼리 실행
SELECT schemaname, matviewname, ispopulated 
FROM pg_matviews 
WHERE matviewname LIKE 'mv_dashboard_%' 
ORDER BY matviewname;

-- 예상 결과 (3개 뷰)
┌───────────┬──────────────────────────┬─────────────┐
│ schemaname│ matviewname              │ ispopulated │
├───────────┼──────────────────────────┼─────────────┤
│ public    │ mv_dashboard_executive   │ t           │
│ public    │ mv_dashboard_individual  │ t           │
│ public    │ mv_dashboard_team        │ t           │
└───────────┴──────────────────────────┴─────────────┘

상태: [ ] 3개 뷰 모두 ispopulated = true
```

**검증 2: 테이블 생성 확인** (1분)

```sql
-- 쿼리 실행
SELECT table_name, table_type 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name = 'dashboard_metrics_history';

-- 예상 결과
┌──────────────────────────┬─────────────┐
│ table_name               │ table_type  │
├──────────────────────────┼─────────────┤
│ dashboard_metrics_history│ BASE TABLE  │
└──────────────────────────┴─────────────┘

상태: [ ] 테이블 생성됨 (BASE TABLE)
```

**검증 3: 인덱스 생성 확인** (2분)

```sql
-- 쿼리 실행
SELECT indexname, tablename 
FROM pg_indexes 
WHERE schemaname = 'public' 
AND (tablename LIKE 'mv_dashboard_%' OR tablename = 'dashboard_metrics_history')
ORDER BY tablename, indexname;

-- 예상 결과 (11개 인덱스)
┌────────────────────────────────────┬──────────────────────────┐
│ indexname                          │ tablename                │
├────────────────────────────────────┼──────────────────────────┤
│ idx_dmh_division_period            │ dashboard_metrics_history│
│ idx_dmh_metric_type                │ dashboard_metrics_history│
│ idx_dmh_org_period                 │ dashboard_metrics_history│
│ idx_dmh_period                     │ dashboard_metrics_history│
│ idx_dmh_team_period                │ dashboard_metrics_history│
│ idx_mv_dashboard_executive_month   │ mv_dashboard_executive   │
│ idx_mv_dashboard_executive_org     │ mv_dashboard_executive   │
│ idx_mv_dashboard_executive_quarter │ mv_dashboard_executive   │
│ idx_mv_dashboard_individual_owner  │ mv_dashboard_individual  │
│ idx_mv_dashboard_individual_status │ mv_dashboard_individual  │
│ idx_mv_dashboard_team_division     │ mv_dashboard_team        │
│ idx_mv_dashboard_team_org          │ mv_dashboard_team        │
│ idx_mv_dashboard_team_team_id      │ mv_dashboard_team        │
└────────────────────────────────────┴──────────────────────────┘

상태: [ ] 11개 인덱스 모두 생성됨 (개인 2 + 팀 3 + 경영진 3 + 히스토리 4 = 12개)
```

**검증 4: RLS 정책 확인** (1min)

```sql
-- 쿼리 실행
SELECT tablename, policyname, qual 
FROM pg_policies 
WHERE tablename = 'dashboard_metrics_history';

-- 예상 결과 (1개 정책)
┌──────────────────────────┬────────────────────────────┬─────────────────┐
│ tablename                │ policyname                 │ qual            │
├──────────────────────────┼────────────────────────────┼─────────────────┤
│ dashboard_metrics_history│ dashboard_metrics_history_r│ ((SELECT role... │
└──────────────────────────┴────────────────────────────┴─────────────────┘

상태: [ ] RLS 정책 생성됨 (dashboard_metrics_history_read)
```

**검증 5: 샘플 데이터 확인** (2분)

```sql
-- 쿼리 1: 개인 대시보드 (최근 10건)
SELECT COUNT(*), MAX(created_at) 
FROM mv_dashboard_individual;

예상: (count >= 0, created_at = NOW())
상태: [ ] 쿼리 실행 성공

-- 쿼리 2: 팀 대시보드 (최근 5개 팀)
SELECT COUNT(DISTINCT team_id), MAX(team_id) 
FROM mv_dashboard_team 
WHERE team_id IS NOT NULL;

예상: (count >= 0)
상태: [ ] 쿼리 실행 성공

-- 쿼리 3: 경영진 대시보드
SELECT COUNT(*), MAX(quarter) 
FROM mv_dashboard_executive 
WHERE org_id IS NOT NULL;

예상: (count >= 0)
상태: [ ] 쿼리 실행 성공
```

#### Phase 1.3: 뷰 갱신 (1분)

```sql
-- 쿼리 실행
SELECT refresh_dashboard_views();

-- 예상 결과
┌──────────────────────────┐
│ refresh_dashboard_views  │
├──────────────────────────┤
│ (1 row)                  │
└──────────────────────────┘

상태: [ ] 뷰 갱신 완료
```

**Stage 1 완료 체크:**
- [ ] 3개 MV 생성 + 데이터 포함
- [ ] 1개 히스토리 테이블 생성 + RLS 활성화
- [ ] 11개 인덱스 생성
- [ ] 뷰 갱신 완료
- **Stage 1 완료 시간:** _____ (예상: 20분)

---

### STAGE 2: 백엔드 API 배포 (Railway, 10분)

#### Phase 2.1: Git Push & Auto-Deploy (5분)

```bash
# 단계 1: 현재 브랜치 확인
$ git branch
  main
* main
# 상태: [ ] main 브랜치 활성화

# 단계 2: 변경 상태 확인
$ git status --short
  M .bkit/audit/2026-04-20.jsonl
  M .bkit/runtime/agent-state.json
  M .bkit/state/memory.json
# 상태: [ ] 모든 변경 커밋됨 (이미 커밋된 상태 확인)

# 단계 3: 최신 커밋 확인
$ git log --oneline -1
  [hash] Dashboard KPI DO/CHECK complete
# 상태: [ ] 최신 커밋 확인됨

# 단계 4: Railway 자동 배포 트리거 (git push 시 자동 실행)
# Railway 대시보드: https://railway.app
# 프로젝트: tenopa-proposer (staging)
# 상태: [ ] Railway 자동 배포 트리거됨
```

**예상 Railway 배포 로그:**
```
[09:30:00] Starting build...
[09:30:15] Installing dependencies...
[09:31:00] Building application...
[09:33:00] Uploading artifacts...
[09:34:00] Deploying to staging...
[09:35:00] Deployment successful! ✓
  URL: https://[staging-api-hash].railway.app
  Status: Healthy
  Uptime: 99.9%
```

**배포 상태 확인:**
```
Railway 대시보드 확인:
[ ] Build status: ✅ Success
[ ] Deploy status: ✅ Success
[ ] Service status: ✅ Running
[ ] Logs: No errors
```

#### Phase 2.2: 헬스 체크 (3분)

**테스트 1: 기본 헬스 체크**

```bash
$ curl -X GET "https://[staging-api-url].railway.app/api/dashboard/health" \
  -H "Authorization: Bearer [staging-token]"

# 예상 응답 (200 OK)
{
  "status": "healthy",
  "database": "connected",
  "cache": "connected",
  "version": "1.0.0",
  "timestamp": "2026-05-01T10:35:00.000Z"
}

상태: [ ] 200 OK 응답
```

**테스트 2: 개인 대시보드 메트릭 조회**

```bash
$ curl -X GET "https://[staging-api-url].railway.app/api/dashboard/metrics/individual?period=ytd" \
  -H "Authorization: Bearer [staging-token]" \
  -H "Content-Type: application/json"

# 예상 응답 (200 OK)
{
  "dashboard_type": "individual",
  "period": "ytd",
  "generated_at": "2026-05-01T10:35:30.000Z",
  "cache_hit": false,
  "cache_ttl_seconds": 300,
  "metrics": {
    "win_rate": 42.5,
    "total_proposals": 12,
    "avg_cycle_days": 28,
    "success_rate": 75,
    "total_won_amount": 2500000,
    "positioning_accuracy": 85
  }
}

상태: [ ] 200 OK 응답 + 메트릭 데이터
```

**테스트 3: 팀 대시보드 메트릭 조회**

```bash
$ curl -X GET "https://[staging-api-url].railway.app/api/dashboard/metrics/team?period=ytd" \
  -H "Authorization: Bearer [staging-token]"

# 예상 응답 (200 OK + 팀 메트릭)
{
  "dashboard_type": "team",
  "period": "ytd",
  "metrics": { ... }
}

상태: [ ] 200 OK 응답
```

#### Phase 2.3: 성능 베이스라인 (2min)

```bash
# 응답 시간 측정 (10회 반복)
for i in {1..10}; do
  START=$(date +%s%N)
  curl -s "https://[staging-api-url].railway.app/api/dashboard/metrics/individual?period=ytd" \
    -H "Authorization: Bearer [staging-token]" > /dev/null
  END=$(date +%s%N)
  DURATION=$(( ($END - $START) / 1000000 ))
  echo "Request $i: ${DURATION}ms"
  sleep 1
done

# 예상 결과
Request 1: 1045ms (캐시 미스, DB 조회)
Request 2: 145ms (캐시 히트)
Request 3: 132ms (캐시 히트)
Request 4: 148ms (캐시 히트)
Request 5: 1087ms (캐시 만료, DB 재조회)
...

성능 목표: p95 < 1.0초 (캐시 미스), p95 < 200ms (캐시 히트)
상태: [ ] 성능 기준 충족
```

**Stage 2 완료 체크:**
- [ ] Railway 자동 배포 성공
- [ ] 헬스 체크 200 OK
- [ ] 3개 메트릭 엔드포인트 정상 작동
- [ ] 성능 p95 < 1.5초
- **Stage 2 완료 시간:** _____ (예상: 10분)

---

### STAGE 3: 프론트엔드 배포 (Vercel, 10분)

#### Phase 3.1: Vercel 자동 배포 (5분)

```
Vercel 대시보드: https://vercel.com → Projects → tenopa-proposer

배포 상태:
[ ] Build 시작 (자동 트리거, git push 감지)
[ ] Build 진행 (npm install → npm run build)
[ ] Build 완료 (2-3분 소요)
[ ] Deploy 시작 (프리뷰 URL 할당)
[ ] Deploy 완료 (3-5분 소요)

최종 상태:
[ ] ✅ Ready (프리뷰 URL 활성화)

프리뷰 URL:
https://tenopa-proposer-[pr-number].vercel.app
또는
https://[staging-frontend-url].vercel.app
```

**예상 Vercel 배포 로그:**
```
[09:40:00] Preparing build...
[09:40:30] Installing dependencies (npm ci)...
[09:41:00] Building application (npm run build)...
[09:42:30] Build completed successfully ✓
[09:42:45] Deploying build...
[09:43:00] Deployment successful! ✓
  Preview URL: https://[url].vercel.app
  Status: Ready
  Cache: ✓ Enabled
```

#### Phase 3.2: 프론트엔드 로드 확인 (2분)

```
단계 1: 브라우저 열기
[ ] 프리뷰 URL 입력: https://[staging-frontend-url].vercel.app/dashboards

단계 2: 페이지 로드 확인
[ ] 페이지 로드 성공 (no 404/5xx)
[ ] 모든 리소스 로드됨 (CSS, JS, 폰트)
[ ] 대시보드 탭 4개 표시 (Individual | Team | Department | Executive)

단계 3: DevTools Network 확인 (F12 → Network)
[ ] 모든 API 요청 200 OK
[ ] 로드 시간: < 3초 (LCP)
[ ] 에러: 0개
```

**Stage 3 완료 체크:**
- [ ] Vercel 자동 배포 성공
- [ ] 프리뷰 URL 로드 성공
- [ ] 모든 리소스 로드됨
- **Stage 3 완료 시간:** _____ (예상: 10분)

---

## ✅ 검증 단계 (25분)

### Test 1: 개인 대시보드 (5분)

```
브라우저 URL: https://[staging-frontend-url].vercel.app/dashboards
현재 사용자: [test-user-1@tenopa.co.kr]
```

**검증 항목:**

```
┌─────────────────────────────────────────────────────────────┐
│ ✓ KPI 카드 (6개)                                             │
├─────────────────────────────────────────────────────────────┤
│ [ ] 수주율 (Win Rate): 42.5%                                 │
│ [ ] 총 제안 (Proposals): 12건                                │
│ [ ] 소요일 (Cycle Days): 28일                                │
│ [ ] 성공률 (Success Rate): 75%                               │
│ [ ] 수주금액 (Total Won): 2,500,000원                        │
│ [ ] 정확도 (Positioning Accuracy): 85%                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ✓ 차트 (2개)                                                 │
├─────────────────────────────────────────────────────────────┤
│ [ ] 월별 추이 (라인 차트)                                     │
│      - X축: 월 (1월~현재)                                    │
│      - Y축: 제안 수                                          │
│      - 데이터: 실시간 (캐시된)                               │
│ [ ] 포지셔닝 분포 (파이 차트)                                 │
│      - Defensive / Offensive / Adjacent 구분                 │
│      - 범례: 클릭 가능                                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ✓ 테이블 (1개)                                               │
├─────────────────────────────────────────────────────────────┤
│ [ ] 진행 중인 제안 테이블                                     │
│      - 컬럼: 제안 ID, 상태, 마감일, 예상금액                 │
│      - 페이지네이션: 5행/페이지                              │
│      - 정렬: 마감일 (오름차순)                               │
│      - 클릭: 상세 보기 가능                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ✓ UI 요소                                                    │
├─────────────────────────────────────────────────────────────┤
│ [ ] 새로고침 버튼: 클릭 가능                                  │
│ [ ] 캐시 상태: "캐시 HIT" 또는 "캐시 MISS" 표시              │
│ [ ] 마지막 갱신 시간: "갱신됨: 1분 전" 표시                  │
│ [ ] 에러: 없음 (no red alerts)                               │
└─────────────────────────────────────────────────────────────┘

테스트 결과: [ ] 통과 (5/5 ✓)
```

### Test 2: 팀 대시보드 필터링 (5분)

```
선행 조건: 팀장 이상 권한 사용자 로그인
팀 ID: [test-team-1]
```

**검증 항목:**

```
┌─────────────────────────────────────────────────────────────┐
│ ✓ 필터 변경 (팀 선택 드롭다운)                                │
├─────────────────────────────────────────────────────────────┤
│ [ ] 드롭다운 열림: [현재팀] 선택됨                            │
│ [ ] 다른 팀 선택: [test-team-2] 클릭                          │
│ [ ] API 호출: GET /api/dashboard/metrics/team?team_id=...  │
│ [ ] 응답 시간: < 1초                                        │
│ [ ] 데이터 갱신: 이전과 다른 값 표시                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ✓ KPI 카드 (10개)                                            │
├─────────────────────────────────────────────────────────────┤
│ [ ] 팀 수주율 (YTD)                                           │
│ [ ] 팀 제안 수                                               │
│ [ ] 평균 거래 규모 (Avg Deal Size)                           │
│ [ ] 팀 활용률 (Utilization)                                  │
│ [ ] 포지셔닝 성공률                                           │
│ [ ] 평균 소요일                                               │
│ [ ] 월별 수주율 (MTD)                                        │
│ [ ] 진행 중인 제안                                            │
│ [ ] 팀원 평균 수주율                                          │
│ [ ] 기술 점수 (Avg Tech Score)                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ✓ 차트 (3개)                                                 │
├─────────────────────────────────────────────────────────────┤
│ [ ] 팀 수주율 (막대 차트, 월별)                               │
│ [ ] 월별 추이 (라인 차트, 12개월)                             │
│ [ ] 포지셔닝 성공률 (도넛 차트)                               │
└─────────────────────────────────────────────────────────────┘

테스트 결과: [ ] 통과 (3/3 ✓)
```

### Test 3: 본부 대시보드 비교 (5min)

```
선행 조건: 본부장 이상 권한 사용자 로그인
본부 ID: [test-division-1]
```

**검증 항목:**

```
┌─────────────────────────────────────────────────────────────┐
│ ✓ KPI 카드 (9개)                                             │
├─────────────────────────────────────────────────────────────┤
│ [ ] 본부 목표 vs 실적 (Variance)                             │
│ [ ] 팀 수 (Team Count)                                      │
│ [ ] 본부 전체 수주율                                          │
│ [ ] 본부 수주 금액                                            │
│ [ ] 평균 거래 규모                                            │
│ [ ] 평균 소요일                                               │
│ [ ] 진행 중인 제안                                            │
│ [ ] 월별 목표 달성률 (MTD Target %)                          │
│ [ ] 분기 예상 완성률 (Quarter Forecast)                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ✓ 차트 (4개)                                                 │
├─────────────────────────────────────────────────────────────┤
│ [ ] 목표 vs 실적 (막대 차트)                                  │
│ [ ] 팀별 성과 비교 (수평 막대)                                │
│ [ ] 경쟁사 분석 (라인 차트, 최근 3개월)                       │
│ [ ] 지역별 성과 (지도 또는 테이블)                            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ✓ 테이블 (1개 + 필터)                                        │
├─────────────────────────────────────────────────────────────┤
│ [ ] 팀별 성과 테이블                                          │
│      - 정렬: 수주율 내림차순 (클릭 가능)                      │
│      - 페이지네이션: 10행/페이지                             │
│      - 필터: 기간 변경 (월간/분기간)                         │
└─────────────────────────────────────────────────────────────┘

테스트 결과: [ ] 통과 (4/4 ✓)
```

### Test 4: 경영진 대시보드 분기별 (5min)

```
선행 조건: 경영진 권한 사용자 로그인
조직 ID: [test-org-1]
```

**검증 항목:**

```
┌─────────────────────────────────────────────────────────────┐
│ ✓ KPI 카드 (4개)                                             │
├─────────────────────────────────────────────────────────────┤
│ [ ] 전사 수주율 (%)                                          │
│ [ ] 전사 수주 금액 (원)                                       │
│ [ ] 완료된 제안 수 (건)                                       │
│ [ ] 예상 분기 매출 (원)                                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ✓ 차트 (3개)                                                 │
├─────────────────────────────────────────────────────────────┤
│ [ ] 본부별 성과 비교 (스택 막대 차트)                         │
│      - X축: 본부 이름                                       │
│      - Y축: 수주율 (%)                                      │
│      - 범례: Won / Lost / Cancelled                        │
│ [ ] 분기별 추이 (콤보 차트)                                   │
│      - 왼쪽 Y축: 수주율 (%)                                  │
│      - 오른쪽 Y축: 수주 금액 (원)                            │
│      - 라인: 수주율                                          │
│      - 막대: 수주 금액                                       │
│ [ ] 포지셔닝 정확도 (도넛 차트)                               │
│      - Defensive / Offensive / Adjacent %                   │
│      - 범례: 클릭 가능 (토글 기능)                           │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ✓ UI 요소                                                    │
├─────────────────────────────────────────────────────────────┤
│ [ ] 기간 필터: 분기/월별 선택 가능                            │
│ [ ] 범례 클릭: 차트 시리즈 토글                              │
│ [ ] 호버: Tool tip 표시 (데이터값 포함)                      │
│ [ ] 드릴다운: 본부 클릭 → 팀 상세 데이터 (예정)              │
└─────────────────────────────────────────────────────────────┘

테스트 결과: [ ] 통과 (3/3 ✓)
```

### Test 5: 반응형 디자인 (5min)

```
도구: Chrome DevTools (F12) → Responsive Design Mode (Ctrl+Shift+M)
브라우저: Chrome / Firefox / Safari (모두 동일)
```

**모바일 (375px):**

```
┌─────────────────────────────────────────────────────────────┐
│ ✓ 레이아웃                                                   │
├─────────────────────────────────────────────────────────────┤
│ [ ] KPI 카드: 1열 (세로 스택)                                │
│ [ ] 차트: 세로 배치 (높이 > 너비)                            │
│ [ ] 테이블: 수평 스크롤 (sticky header)                      │
│ [ ] 버튼: 터치 친화적 (최소 48px)                            │
│ [ ] 텍스트: 가독성 유지 (font-size >= 14px)                 │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ ✓ 상호작용                                                   │
├─────────────────────────────────────────────────────────────┤
│ [ ] 필터 드롭다운: 클릭 가능 (no overflow)                    │
│ [ ] 차트: 호버 없음 (터치 대응, tap 제스처)                   │
│ [ ] 테이블: 스크롤 가능 (overscroll 없음)                     │
│ [ ] 새로고침: 1-2초 (로딩 인디케이터 표시)                    │
└─────────────────────────────────────────────────────────────┘
```

**태블릿 (768px):**

```
┌─────────────────────────────────────────────────────────────┐
│ ✓ 레이아웃                                                   │
├─────────────────────────────────────────────────────────────┤
│ [ ] KPI 카드: 2열 (또는 flexible wrap)                       │
│ [ ] 차트: 2개/행 배치                                        │
│ [ ] 테이블: 모두 보임 (좌우 스크롤 최소화)                    │
│ [ ] 비율: 가로:세로 = 16:9 또는 4:3                          │
└─────────────────────────────────────────────────────────────┘
```

**데스크톱 (1920px):**

```
┌─────────────────────────────────────────────────────────────┐
│ ✓ 레이아웃                                                   │
├─────────────────────────────────────────────────────────────┤
│ [ ] KPI 카드: 4열 (1행에 모두)                               │
│ [ ] 차트: 3개 모두 1행에 표시                                │
│ [ ] 테이블: 스크롤 없음 (full viewport)                      │
│ [ ] 여백: 적절함 (padding >= 32px)                          │
│ [ ] 최대 너비: 제한됨 (max-width 설정, 예: 1400px)           │
└─────────────────────────────────────────────────────────────┘
```

테스트 결과: [ ] 통과 (3/3 ✓, 모든 뷰포트)

---

## 📊 검증 총점

| 대시보드 | 로드 | KPI | 차트 | 테이블 | 필터 | 점수 |
|---------|------|-----|------|--------|------|------|
| Individual | ☐ | ☐ | ☐ | ☐ | ☐ | 0/5 |
| Team | ☐ | ☐ | ☐ | ☐ | ☐ | 0/5 |
| Department | ☐ | ☐ | ☐ | ☐ | ☐ | 0/5 |
| Executive | ☐ | ☐ | ☐ | ☐ | ☐ | 0/5 |
| Responsive | ☐ | ☐ | ☐ | ☐ | ☐ | 0/5 |
| **TOTAL** | | | | | | **0/25** |

**최종 판정:**
```
[ ] 25/25 (100%) → GO FOR PRODUCTION ✅
[ ] 20-24/25 (80-96%) → GO WITH MINOR ISSUES
[ ] 15-19/25 (60-76%) → HOLD & INVESTIGATE
[ ] < 15/25 (< 60%) → ROLLBACK & FIX
```

---

## ⏱️ 배포 일정 추적

| Phase | 시작 시간 | 종료 시간 | 소요 시간 | 상태 |
|-------|---------|---------|---------|------|
| **Pre-Check** | | | | |
| 코드 상태 검증 | — | — | 2분 | ☐ |
| 환경 변수 확인 | — | — | 2분 | ☐ |
| DB 상태 확인 | — | — | 3분 | ☐ |
| **Stage 1** | | | | |
| SQL 마이그레이션 | — | — | 12분 | ☐ |
| 마이그레이션 검증 | — | — | 8분 | ☐ |
| **Stage 2** | | | | |
| Git Push & Deploy | — | — | 5분 | ☐ |
| 헬스 체크 | — | — | 3분 | ☐ |
| 성능 베이스라인 | — | — | 2분 | ☐ |
| **Stage 3** | | | | |
| Vercel 배포 | — | — | 5분 | ☐ |
| 로드 확인 | — | — | 2분 | ☐ |
| **검증** | | | | |
| Test 1: Individual | — | — | 5분 | ☐ |
| Test 2: Team | — | — | 5분 | ☐ |
| Test 3: Department | — | — | 5분 | ☐ |
| Test 4: Executive | — | — | 5분 | ☐ |
| Test 5: Responsive | — | — | 5분 | ☐ |
| **TOTAL** | **——** | **——** | **~67분** | |

**예상 배포 완료:** 2026-05-01 11:07 UTC (10:00 시작 기준)

---

**배포 실행 준비 완료! 위의 각 단계를 순서대로 진행하세요.**
