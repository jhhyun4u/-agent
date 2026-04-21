# Dashboard KPI 스테이징 배포 — 문서 인덱스
**Date:** 2026-05-01  
**Status:** ✅ READY FOR EXECUTION  
**Total Docs:** 4개 + 코드 (6가지 배포 아티팩트)

---

## 📚 배포 문서 맵

### 1️⃣ 시작 문서 → DASHBOARD_KPI_STAGING_DEPLOYMENT_SUMMARY.md
**용도:** 전체 배포 준비 상태 한눈에 파악  
**분량:** 12KB, 5분 읽음  
**내용:**
- 배포 개요 및 예상 시간
- 성공 기준 (25개 항목)
- 준비도 100% 검증
- 최종 승인 판정

**📌 가장 먼저 읽기!** → 배포 가능 여부 즉시 판단

---

### 2️⃣ 상세 배포 가이드 → DASHBOARD_KPI_STAGING_DEPLOYMENT_2026-05-01.md
**용도:** 3단계 배포 상세 절차 + 25분 검증 계획  
**분량:** 17KB, 20분 읽음  
**구성:**

#### Stage 1: DB 마이그레이션 (20분)
- Phase 1.1: SQL 마이그레이션 (copy-paste 준비)
- Phase 1.2: 5개 검증 쿼리
- Phase 1.3: 뷰 갱신

```sql
-- 예시: 마이그레이션 명령어
database/migrations/051_dashboard_kpi_metrics.sql
→ Supabase SQL Editor에 복사 → RUN
```

#### Stage 2: API 배포 (10분, Railway)
- Git push (자동 배포)
- 헬스 체크 3가지
- 성능 베이스라인

```bash
# 예시: 헬스 체크
curl https://[staging-api].railway.app/api/dashboard/health
→ 200 OK + { "status": "healthy" }
```

#### Stage 3: Frontend 배포 (10분, Vercel)
- Vercel auto-deploy
- 프리뷰 URL 로드
- 리소스 확인

#### 검증 (25분)
5개 대시보드 × 5개 항목 = 25개 체크리스트

```
┌─────────────────────┐
│ Individual (5)      │
│ Team (5)            │
│ Department (5)      │
│ Executive (5)       │
│ Responsive (5)      │
├─────────────────────┤
│ 총 25개 ✓ = GO     │
└─────────────────────┘
```

**📌 메인 가이드!** → 이것을 따라 배포 진행

---

### 3️⃣ 배포 추적 양식 → DASHBOARD_KPI_DEPLOYMENT_TRACKER_2026-05-01.md
**용도:** 배포 중 실시간 진행 상황 기록  
**분량:** 36KB, 참조용 (읽음 아님)  
**특징:**
- 각 단계별 체크박스 (☐ / ☑)
- 예상 결과 명시
- 시간 기록 칸
- 25개 검증 체크리스트

**사용 방법:**
```
1. 배포 시작 시: 이 파일 열기
2. 각 단계 진행하면서: 체크박스 채우기 (☑)
3. 시간 기록: "시작 시간" / "종료 시간" 입력
4. 최종 점수: 25/25 달성 시 "✅ GO FOR PRODUCTION"

예시:
┌─────────────────────────────────────────────┐
│ STEP 1: SQL 에디터 접속                      │
│ [☑] 1. Supabase 대시보드 열기   09:30      │
│ [☑] 2. Staging 프로젝트 선택    09:31      │
│ [☑] 3. SQL Editor 메뉴 클릭     09:32      │
│ 예상: SQL 에디터 빈 화면                    │
├─────────────────────────────────────────────┤
│ ✅ STEP 1 완료 (3분)                         │
└─────────────────────────────────────────────┘
```

**📌 배포 중 계속 참조!** → 진행 상황 기록용

---

### 4️⃣ 빠른 참조 가이드 → DASHBOARD_KPI_DEPLOYMENT_QUICK_REFERENCE.md
**용도:** 배포 중 명령어 + 문제 해결  
**분량:** 14KB, 빠른 복사용  
**구성:**

#### A. 배포 명령어 (copy-paste 준비)
```bash
# SQL 검증 쿼리
SELECT * FROM pg_matviews WHERE matviewname LIKE 'mv_dashboard_%';

# API 헬스 체크
curl https://[staging-api].railway.app/api/dashboard/health

# 성능 측정
for i in {1..10}; do time curl ...; done
```

#### B. 7가지 문제 해결
1. SQL 마이그레이션 실패
2. API 헬스 체크 실패 (500)
3. 응답 시간 느림 (> 3초)
4. 프론트엔드 404 오류
5. API 호출 실패 (401/403)
6. 데이터 표시 안 됨 (0)
7. 캐시 작동 안 함

**각 문제별:**
- 원인 분석 SQL/명령어
- 구체적인 해결 방법
- 긴급 연락처

**예시:**
```
문제 3: API 응답 시간 느림 (> 3초)
──────────────────────────────────
원인 분석:
  # 캐시 상태 확인
  curl ... | jq '.cache_hit'
  
  → true: 캐시 정상 (200ms 이내)
  → false: DB 조회 (1-2초 정상, > 3초는 느림)

해결:
  1. Redis 연결 확인 (REDIS_URL)
  2. DB 인덱스 확인
  3. Supabase 쿼리 성능 분석
```

**📌 배포 중 문제 발생 시!** → 이곳에서 빠르게 찾기

---

## 🔄 배포 실행 흐름

```
START
  ↓
[1] DASHBOARD_KPI_STAGING_DEPLOYMENT_SUMMARY.md 읽기 (5분)
    └─ 배포 가능 여부 판단 → NO? → STOP (준비 미완료)
  ↓
[2] DASHBOARD_KPI_STAGING_DEPLOYMENT_2026-05-01.md 열기
    └─ 3단계 + 검증 가이드 (메인 가이드)
  ↓
[3] DASHBOARD_KPI_DEPLOYMENT_TRACKER_2026-05-01.md 열기
    └─ 추적용 (진행 상황 기록)
  ↓
[4] Stage 1: DB 마이그레이션 (20분)
    └─ [2] 문서 따라 → [3]에 체크박스 입력
  ↓
[5] Stage 2: API 배포 (10분)
    └─ [2] 문서 따라 → [4] 빠른 참조로 명령어 실행
  ↓
[6] Stage 3: Frontend 배포 (10분)
    └─ [2] 문서 따라 → [3]에 진행 기록
  ↓
[7] 검증 (25분)
    └─ [2] 검증 체크리스트 따라 → [3]에 결과 입력
  ↓
[8] 최종 판정
    ├─ 25/25 ✓ → GO FOR PRODUCTION ✅
    ├─ 20-24/25 → GO WITH MINOR ISSUES ⚠
    └─ < 20/25 → HOLD & INVESTIGATE ❌
  ↓
END

문제 발생 시 언제든:
  → [4] DASHBOARD_KPI_DEPLOYMENT_QUICK_REFERENCE.md 참조
  → 해당 문제 섹션 찾아서 명령어/해결책 실행
```

---

## 🎯 배포 체크리스트 (한눈에 보기)

### Pre-Deployment (5분)
```
[ ] [1] SUMMARY 문서 읽음
[ ] [2] DEPLOYMENT 문서 열음
[ ] [3] TRACKER 문서 열음
[ ] Git status clean
[ ] 환경 변수 설정 완료
[ ] 롤백 계획 준비
```

### Stage 1: DB 마이그레이션 (20분)
```
[ ] SQL 파일 복사 (database/migrations/051_*)
[ ] Supabase SQL Editor 실행
[ ] 5개 검증 쿼리 모두 통과
  [ ] 뷰 생성 확인 (3개)
  [ ] 테이블 생성 확인 (1개)
  [ ] 인덱스 생성 확인 (11개)
  [ ] RLS 정책 확인 (1개)
  [ ] 샘플 데이터 확인
[ ] 뷰 갱신 함수 실행
[ ] [TRACKER] Stage 1 항목 모두 입력
```

### Stage 2: API 배포 (10분)
```
[ ] Git push (Railway auto-deploy 트리거)
[ ] Railway 배포 상태 모니터링 (Logs)
[ ] 3개 헬스 체크 실행
  [ ] 기본 헬스 체크 (200 OK)
  [ ] 개인 대시보드 메트릭 (200 OK)
  [ ] 팀 대시보드 메트릭 (200 OK)
[ ] 성능 베이스라인 기록 (10회 측정)
[ ] [TRACKER] Stage 2 항목 모두 입력
```

### Stage 3: Frontend 배포 (10분)
```
[ ] Vercel auto-deploy 확인 (Status: Ready)
[ ] 프리뷰 URL 로드 성공
[ ] DevTools Network 탭 확인 (모두 200 OK)
[ ] 4개 대시보드 탭 표시 확인
[ ] [TRACKER] Stage 3 항목 모두 입력
```

### 검증 (25분)
```
Individual Dashboard (5개)
  [ ] 6개 KPI 카드
  [ ] 2개 차트
  [ ] 1개 테이블
  [ ] UI 요소 (새로고침, 캐시 상태, 시간)
  [ ] 로드 성공

Team Dashboard (5개)
  [ ] 필터 변경 → API 재호출
  [ ] 10개 KPI 카드
  [ ] 3개 차트
  [ ] 팀원 성과 테이블
  [ ] 데이터 갱신 확인

Department Dashboard (5개)
  [ ] 9개 KPI 카드
  [ ] 4개 차트 (목표vs실적, 팀비교, 경쟁사, 지역)
  [ ] 팀별 성과 테이블
  [ ] 기간 필터
  [ ] 정렬 및 페이지네이션

Executive Dashboard (5개)
  [ ] 4개 주요 KPI
  [ ] 본부별 성과 (스택 막대)
  [ ] 분기별 추이 (콤보)
  [ ] 포지셔닝 정확도 (도넛)
  [ ] 범례 클릭 가능

Responsive Design (5개)
  [ ] 모바일 375px (1열, 세로 스크롤)
  [ ] 태블릿 768px (2열, 레이아웃)
  [ ] 데스크톱 1920px (4열, 완전 표시)
  [ ] 버튼 클릭 가능 (48px)
  [ ] 텍스트 가독성 (font-size >= 14px)

최종 점수: [ ] 25/25
```

### Post-Deployment (10분)
```
[ ] 최종 판정: ✅ GO FOR PRODUCTION
[ ] 모니터링 설정 (24시간)
  [ ] API 헬스 체크 (5분마다)
  [ ] 에러율 모니터링
  [ ] 성능 메트릭
  [ ] 데이터 무결성
[ ] 배포 완료 보고서 작성
[ ] 사용자 공지 (Slack)
```

---

## 📊 배포 아티팩트 목록

| 아티팩트 | 유형 | 파일 | 라인 |
|---------|------|------|------|
| **SQL 마이그레이션** | Database | `051_dashboard_kpi_metrics.sql` | 280 |
| **API 라우터** | Backend | `routes_dashboard.py` | 400+ |
| **API 서비스** | Backend | `dashboard_metrics_service.py` | 350+ |
| **React 컴포넌트** | Frontend | 11개 파일 (TS) | 2,331 |
| **테스트** | QA | pytest + RTL | 100+ |
| **설계 문서** | Doc | `DESIGN` | 976 |

---

## 🕐 예상 배포 일정

```
Start: 2026-05-01 10:00 UTC

10:00-10:05 (5분)   → 사전 확인 + 문서 읽기
10:05-10:25 (20분)  → Stage 1: DB 마이그레이션
10:25-10:35 (10분)  → Stage 2: API 배포
10:35-10:45 (10분)  → Stage 3: Frontend 배포
10:45-11:10 (25분)  → 검증 (25개 항목)

Expected Completion: 2026-05-01 11:10 UTC (70분)
Safety Margin: 10-20분 (예상 초과 고려)

Final Time: 2026-05-01 11:10-11:30 UTC
```

---

## ✅ 최종 체크

| 항목 | 상태 | 비고 |
|------|------|------|
| **문서 준비** | ✅ 4개 | SUMMARY / DEPLOYMENT / TRACKER / REFERENCE |
| **코드 준비** | ✅ 6개 | SQL + API + Service + 4 Dashboards |
| **테스트 준비** | ✅ 100+ | 단위 + 통합 + E2E + RTL |
| **환경 준비** | ✅ 3개 | Supabase + Railway + Vercel |
| **배포 승인** | ✅ YES | 모든 기준 충족 |

---

## 🚀 배포 시작!

**1단계:** 이 문서 (인덱스) 읽음 ✅
**2단계:** DASHBOARD_KPI_STAGING_DEPLOYMENT_SUMMARY.md 읽기
**3단계:** DASHBOARD_KPI_STAGING_DEPLOYMENT_2026-05-01.md 따라 배포 진행
**4단계:** DASHBOARD_KPI_DEPLOYMENT_TRACKER_2026-05-01.md에 진행 상황 기록
**5단계:** 문제 발생 시 DASHBOARD_KPI_DEPLOYMENT_QUICK_REFERENCE.md 참조

---

**배포 준비가 완료되었습니다!**

다음 단계: [DASHBOARD_KPI_STAGING_DEPLOYMENT_SUMMARY.md] 열기 →
