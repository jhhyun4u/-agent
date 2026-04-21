# Dashboard KPI 스테이징 배포 계획 (2026-04-21)

**상태:** 🟢 배포 준비 완료  
**일시:** 2026-04-21 17:00 UTC  
**소요 시간:** 1시간 (배포 30분 + 모니터링 30분)

---

## 배포 전 체크리스트

### 1️⃣ 코드 검증 ✅
- [x] 14/14 단위 테스트 통과
- [x] 3/3 핵심 통합 테스트 통과
- [x] 17/17 전체 테스트 스위트 통과
- [x] Python 구문 검증 완료
- [x] 임포트 오류 없음
- [x] 2개 커밋, 289줄 추가 코드

### 2️⃣ 배포 준비 ✅
- [x] 모든 파일 커밋됨
- [x] 브랜치: main (prod-ready)
- [x] 변경 사항 문서화됨
- [x] 롤백 계획 준비됨

### 3️⃣ 구성 요소 검증
```
✅ Backend API
  - GET /api/dashboard/metrics/{type}
  - GET /api/dashboard/timeline/{type}
  - GET /api/dashboard/details/{type}

✅ Database
  - mv_dashboard_team (팀 메트릭)
  - mv_dashboard_department (부서 메트릭)
  - mv_dashboard_executive (전사 메트릭)
  - dashboard_metrics_history (월별 이력)

✅ Frontend Components
  - ExecutiveDashboard.tsx (DoughnutChart 제거)
  - MetricCard, ChartContainer
  - Recharts 차트 (Line, Bar, Pie)

✅ Schema & Validation
  - DashboardTeamMetrics (month_over_month_change: optional)
  - DashboardDepartmentMetrics (competitor_top_3: optional)
  - DashboardTimelineResponse
  - DashboardDetailsResponse
```

---

## 배포 절차

### Phase 1: 사전 배포 (5분)
```bash
# 1. 최신 커밋 확인
git log --oneline -3

# 2. 변경 사항 검증
git diff HEAD~2

# 3. 스테이징 브랜치 생성 (선택)
git checkout -b staging/dashboard-kpi-20260421
```

### Phase 2: Railway 스테이징 배포 (15분)
```bash
# 1. 환경 변수 설정 확인
# - SUPABASE_URL
# - SUPABASE_ANON_KEY
# - SUPABASE_SERVICE_ROLE_KEY
# - REDIS_URL (캐싱)

# 2. Railway 배포 트리거
# Method 1: GitHub auto-deploy (권장)
git push origin staging/dashboard-kpi-20260421

# Method 2: Railway CLI (직접)
railway up
```

### Phase 3: 배포 후 검증 (20분)

#### A. 헬스 체크 (2분)
```bash
curl -X GET https://staging-api.tenopa.co.kr/api/health/check
# 응답: {"status": "ok", "timestamp": "2026-04-21T..."}
```

#### B. API 엔드포인트 테스트 (10분)

**1. 메트릭 조회 테스트**
```bash
curl -X GET \
  'https://staging-api.tenopa.co.kr/api/dashboard/metrics/team?team_id=t123' \
  -H 'Authorization: Bearer $TOKEN'

# 응답 구조:
# {
#   "dashboard_type": "team",
#   "team_id": "t123",
#   "team_name": "전략팀",
#   "win_rate": 52.3,
#   "total_proposals": 25,
#   "month_over_month_change": 0.0,  # Optional (default)
#   ...
# }
```

**2. 타임라인 조회 테스트**
```bash
curl -X GET \
  'https://staging-api.tenopa.co.kr/api/dashboard/timeline/team?team_id=t123&months=12' \
  -H 'Authorization: Bearer $TOKEN'

# 응답 구조:
# {
#   "dashboard_type": "team",
#   "metric": "win_rate",
#   "data": [
#     {"month": "2026-03", "period_label": "Mar 2026", "win_rate": 45.2, ...},
#     ...
#   ],
#   "summary": {"trend": "up", "avg_win_rate": 42.5, ...}
# }
```

**3. 상세 조회 테스트**
```bash
curl -X GET \
  'https://staging-api.tenopa.co.kr/api/dashboard/details/team?filter_type=team&limit=10' \
  -H 'Authorization: Bearer $TOKEN'

# 응답 구조:
# {
#   "dashboard_type": "team",
#   "filter_type": "team",
#   "total_count": 15,
#   "data": [
#     {
#       "team_id": "t123",
#       "team_name": "전략팀",
#       "win_rate": 52.3,
#       "recent_projects": [...]
#     }
#   ]
# }
```

#### C. Frontend 컴포넌트 테스트 (5분)
```bash
# 1. ExecutiveDashboard 로드 테스트
npm run dev  # 로컬 개발 서버
# 브라우저: http://localhost:3000/dashboard/executive
# 확인: 4개 KPI 카드 렌더링, 3개 차트 표시 (DoughnutChart 없음)

# 2. 차트 렌더링 확인
# - 분기별 수주 추이 (BarChart)
# - 부서별 성과 (PieChart with innerRadius)
# - 포지셔닝 정확도 (LineChart)
```

#### D. 성능 모니터링 (3분)
```bash
# Response time 확인
time curl -X GET 'https://staging-api.tenopa.co.kr/api/dashboard/metrics/executive'

# 기준:
# - p95 < 1초 (캐시 히트)
# - p95 < 2초 (캐시 미스)

# Redis 캐시 hit rate 확인
# - 동일 요청 5분 내 재요청 시 100% hit 예상
```

---

## 롤백 계획

### 롤백이 필요한 경우:
1. **Critical API Error (500):** Endpoints 응답 불가
2. **Database Connection Failure:** mv_dashboard_* 조회 불가
3. **Schema Validation Error:** Pydantic validation 오류 > 1%

### 롤백 절차:
```bash
# 1. 이전 커밋으로 롤백 (1분)
git revert HEAD
git push origin main

# 2. Railway 자동 재배포 트리거
# → 이전 스테이징 이미지 복구

# 3. 검증 (5분)
curl -X GET https://staging-api.tenopa.co.kr/api/health/check
```

---

## 모니터링 메트릭

### 배포 후 30분 모니터링
| 메트릭 | 기준 | 상태 |
|--------|------|------|
| API 응답 시간 (p95) | < 1.5초 | ⏳ 모니터링 |
| 에러율 | < 1% | ⏳ 모니터링 |
| Redis 캐시 Hit Rate | > 70% | ⏳ 모니터링 |
| DB 커넥션 풀 | < 80% | ⏳ 모니터링 |

### 알람 임계값
- 🔴 Critical: p95 > 3초 OR 에러율 > 5%
- 🟡 Warning: p95 > 2초 OR 에러율 > 2%

---

## 배포 후 체크리스트

- [ ] 3개 API 엔드포인트 응답 확인 (2xx)
- [ ] 캐시 히트율 > 70% 확인
- [ ] 응답 시간 p95 < 1.5초 확인
- [ ] 에러율 < 1% 확인
- [ ] Frontend 컴포넌트 렌더링 확인
- [ ] Database 쿼리 성능 확인
- [ ] 로그 에러 없음 확인
- [ ] 30분 모니터링 완료
- [ ] 배포 완료 문서화

---

## 배포 후 다음 단계

✅ 스테이징 배포 완료 → **프로덕션 배포 준비 (2026-04-25)**

### Phase 6 스케줄:
- 2026-04-25 10:00 UTC: 프로덕션 배포
- 2026-04-25 10:00 ~ 11:00 UTC: 헬스 체크 및 모니터링
- 2026-04-25 11:00 이후: 24시간 모니터링

---

**배포 담당자:** AI Coworker  
**승인:** 대기 중  
**상태:** 🟢 배포 준비 완료
