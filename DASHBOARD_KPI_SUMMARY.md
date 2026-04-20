# 팀/본부/전사 KPI 대시보드 — PLAN & DESIGN 완료 보고서

**작성일**: 2026-04-20  
**작성자**: Claude Code  
**상태**: ✅ PLAN & DESIGN 완료

---

## 📋 작업 완료 현황

### 문서 생성

| 문서 | 경로 | 라인 | 상태 |
|------|------|------|------|
| **PLAN** | `docs/01-plan/features/dashboard-kpi.plan.md` | 259줄 | ✅ 완료 |
| **DESIGN** | `docs/02-design/features/dashboard-kpi.design.md` | 976줄 | ✅ 완료 |
| **합계** | | **1,235줄** | ✅ |

---

## 📊 PLAN 문서 요약

### 1. 기능 정의

**4가지 대시보드 유형:**

1. **개인 (Individual)**
   - 자신의 진행 중인 제안서 현황
   - 이번달 진도 + 최근 결과

2. **팀 (Team)**
   - 팀 수주율 (YTD)
   - 팀원 평균 수주건수
   - 월별 추이 (12개월)
   - 포지셔닝별 성공률

3. **본부 (Department)**
   - 본부 목표 vs 실적 (Variance)
   - 팀별 성과 비교 (테이블)
   - 경쟁사 분석 (최근 3개월 낙찰율)
   - 지역별 성과

4. **경영진 (Executive)**
   - 전사 KPI (수주율 / 금액 / 건수)
   - 본부별 성과 비교 (정렬/필터)
   - 분기별 추이 (콤보 차트)
   - 포지셔닝 정확도 (Treemap)
   - 경쟁사 벤치마크

### 2. 핵심 요구사항

| 요구사항 | 설명 | 우선도 |
|---------|------|--------|
| 4가지 대시보드 유형 | Individual / Team / Department / Executive | 높음 |
| 실시간 메트릭 조회 | p95 응답 < 1초 | 높음 |
| 월간 이력 조회 | 최근 12개월 추이 | 높음 |
| 역할 기반 접근 제어 | RLS + 데이터 스코핑 | 높음 |
| 캐싱 전략 | Redis (TTL 5분) | 중간 |
| 드릴다운 기능 | 위젯 → 상세 데이터 | 중간 |

### 3. 성공 기준

| 기준 | 목표 | 검증 |
|------|------|------|
| **응답 성능** | p95 < 1초 | Apache JMeter |
| **정확성** | 메트릭 오류율 < 0.1% | Unit test |
| **데이터 가용성** | 월간 데이터 12개월 이상 | DB 쿼리 |
| **접근 제어** | 데이터 누수 0건 | E2E test (RLS) |
| **테스트 커버리지** | API > 80%, UI > 70% | Pytest + RTL |

### 4. 예상 구현 일정

| Phase | 작업 | 기간 |
|-------|------|------|
| 1 | DB 스키마 설계 + 마이그레이션 | 1일 |
| 2 | 백엔드 API (3개 엔드포인트) | 2일 |
| 3 | 프론트엔드 컴포넌트 | 2일 |
| 4 | 캐싱 + 최적화 | 1일 |
| 5 | 테스트 (Unit + Integration + E2E) | 1일 |
| **총 기간** | | **5-6일** |

---

## 🏗️ DESIGN 문서 요약

### 1. 아키텍처

```
DB (proposals + proposal_results + MV)
  ↓
Cache (Redis, TTL 5분)
  ↓
Backend API (FastAPI, 3개 엔드포인트)
  ↓
Frontend (React + Recharts)
```

### 2. 핵심 API (3개 엔드포인트)

#### 2.1 GET /api/dashboard/metrics/{dashboard_type}
- **기능**: 실시간 KPI 조회
- **응답**: MetricsResponse (캐시 5분)
- **데이터 크기**: ~1KB
- **예시**: 
  ```json
  {
    "dashboard_type": "team",
    "metrics": {
      "win_rate": 48.2,
      "total_proposals": 25,
      "won_count": 12,
      "total_won_amount": 2500000000
    }
  }
  ```

#### 2.2 GET /api/dashboard/timeline/{dashboard_type}
- **기능**: 월별 이력 (12개월 Time-series)
- **응답**: TimelineResponse (캐시 10분)
- **데이터 크기**: ~5KB
- **예시**: 월별 수주율 + 금액 + 건수

#### 2.3 GET /api/dashboard/details/{dashboard_type}
- **기능**: 상세 드릴다운 (필터/정렬/페이징)
- **응답**: DetailsResponse
- **데이터 크기**: ~50KB
- **파라미터**: filter_type, filter_value, sort_by, limit, offset

### 3. 핵심 메트릭 (3가지)

#### 3.1 팀 대시보드 메트릭

```python
# Metric 1: 팀 수주율 (Win Rate %)
win_rate = (won_count / (won_count + lost_count)) * 100
# Metric 2: 수주 금액 (원)
total_won_amount = SUM(final_price WHERE result='won')
# Metric 3: 포지셔닝별 성공률
positioning_breakdown = {
    "Primary": 55.2%,
    "Secondary": 40.0%,
    ...
}
```

#### 3.2 본부 대시보드 메트릭

```python
# Metric 1: 본부 목표 vs 실적 (Variance)
variance = actual_win_rate - target_win_rate
# Metric 2: 팀별 성과 비교 (테이블)
team_comparison = [
    {"team_name": "팀A", "win_rate": 48.2, ...},
    ...
]
# Metric 3: 경쟁사 분석 (낙찰율)
competitor_analysis = [
    {"competitor": "경쟁사A", "lost_rate": 25%, ...},
    ...
]
```

#### 3.3 경영진 대시보드 메트릭

```python
# Metric 1: 전사 KPI (카드)
overall_win_rate = 43.2%
total_won_amount = 15000000000원
# Metric 2: 분기별 추이 (콤보 차트)
quarterly_trend = [
    {"quarter": "2025-Q1", "win_rate": 40.5%, ...},
    ...
]
# Metric 3: 포지셔닝 정확도 (Treemap)
positioning_accuracy = [
    {"positioning": "Primary", "win_rate": 45%, ...},
    ...
]
```

### 4. 데이터베이스 설계

**신규 테이블: dashboard_metrics_history**

```sql
CREATE TABLE dashboard_metrics_history (
    id UUID PRIMARY KEY,
    metric_type TEXT,          -- 'team_performance' | 'positioning_accuracy'
    period DATE,               -- YYYY-MM-01 (월별)
    team_id / division_id / org_id UUID,
    metric_key TEXT,           -- 'win_rate' | 'total_proposals'
    metric_value DECIMAL(10,2),
    created_at TIMESTAMPTZ
);
```

**인덱스:**
- `idx_dmh_period` — 월별 빠른 조회
- `idx_dmh_team_period` — 팀별 + 월별
- `idx_dmh_division_period` — 본부별 + 월별
- `idx_dmh_type_period` — 메트릭 타입 + 월별

### 5. 캐싱 전략

**Redis 키 구조:**
```
dashboard:metrics:{type}:{user_id}:{period}
  → TTL: 5분
  
dashboard:timeline:{type}:{user_id}:{metric}
  → TTL: 10분

dashboard:details:{type}:{filter_type}:{filter_value}
  → TTL: 5분
```

**무효화 전략:**
- Event-driven (Proposal 생성/수정/완료)
- Time-based (TTL 만료)
- Manual (admin 요청 시)

### 6. Frontend 컴포넌트 (React + Recharts)

| 컴포넌트 | 용도 |
|---------|------|
| `DashboardLayout` | 레이아웃 + 스코프 탭 + 필터 |
| `MetricsCard` | KPI 카드 (숫자 + 추이 화살표) |
| `TimelineChart` | 월별 추이 (라인 그래프) |
| `TeamComparisonTable` | 팀별 성과 비교 (정렬/필터) |
| `CompetitorAnalysisChart` | 경쟁사 벤치마크 (바 차트) |
| `FilterPanel` | 기간/팀/지역/포지셔닝 필터 |

### 7. 역할 기반 접근 제어 (RBAC)

| 대시보드 | 개인 | 팀장 | 본부장 | 경영진 |
|---------|------|------|--------|-------|
| Individual | ✅ | ✅ | ✅ | ✅ |
| Team | ✅ 팀원만 | ✅ | ❌ | ❌ |
| Department | ❌ | ❌ | ✅ | ✅ |
| Executive | ❌ | ❌ | ❌ | ✅ |

---

## 🎯 핵심 설계 결정

### 1. 아키텍처 선택

**선택**: DB → Cache → API → Frontend

**근거:**
- 성능: 캐싱으로 p95 < 1초 달성
- 확장성: 메트릭 추가 용이
- 신뢰성: Materialized View로 데이터 일관성 보장

### 2. 메트릭 정의

**선택**: SQL aggregation 기반 (Materialized View 활용)

**근거:**
- 정확성: DB 수준의 정확한 계산
- 성능: 사전 계산으로 쿼리 시간 단축
- 유지보수: 중앙 집중식 메트릭 정의

### 3. 캐싱 전략

**선택**: Redis + Event-driven 무효화

**근거:**
- 응답 속도: 캐시 히트 시 < 100ms
- 데이터 신선도: 5분 TTL로 최신성 보장
- 비용 효율: 불필요한 DB 쿼리 감소

### 4. 접근 제어

**선택**: 서버 사이드 필터링 + RLS 정책

**근거:**
- 보안: 클라이언트에서 권한 우회 불가
- 신뢰성: 데이터 누수 방지
- 명확성: 권한 규칙 한 곳에서 관리

---

## 📈 영향도 분석

### 긍정적 영향

1. **경영진 의사결정** 지원 (실시간 KPI 모니터링)
2. **팀 성과 관리** 개선 (비교/분석 가능)
3. **조직 학습** 가속화 (경쟁사 분석 + 트렌드)
4. **데이터 기반 문화** 구축

### 기술적 영향

1. **기존 시스템** 영향 없음 (조회만 추가)
2. **신규 의존성** 최소 (Redis 선택)
3. **DB 성능** 중립 (인덱스 최적화)
4. **스케일링** 용이 (메트릭 모듈화)

### 위험요소 및 완화

| 위험 | 영향 | 완화 전략 |
|------|------|---------|
| MV 갱신 지연 | 메트릭 최신성 저하 | 일일 자동 갱신 Job |
| 대규모 데이터 조회 | 응답 시간 > 1초 | 월별 집계 테이블 + 캐시 |
| 데이터 일관성 | 팀/본부 전환 시 불일치 | 트랜잭션 + 검증 쿼리 |

---

## ✅ 다음 단계 (구현)

### Phase 1: DB 마이그레이션 (1일)
- [ ] `dashboard_metrics_history` 테이블 생성
- [ ] 기존 데이터 마이그레이션 (MV → history)
- [ ] 인덱스 생성 + 검증

### Phase 2: 백엔드 API (2일)
- [ ] `DashboardMetricsService` 클래스 구현
- [ ] 3개 엔드포인트 구현 (metrics, timeline, details)
- [ ] 역할 기반 필터링 + RBAC
- [ ] Unit test (20개 테스트)

### Phase 3: 프론트엔드 (2일)
- [ ] 6개 컴포넌트 구현 (MetricsCard, Charts, Tables, Filter)
- [ ] 4가지 대시보드 레이아웃
- [ ] React Query 통합 (데이터 페칭)
- [ ] UI test (15개 테스트)

### Phase 4: 캐싱 + 최적화 (1일)
- [ ] Redis 통합 (DashboardMetricsService)
- [ ] Event-driven 무효화 (on_proposal_updated)
- [ ] 쿼리 최적화 (EXPLAIN ANALYZE)
- [ ] 부하 테스트 (p95 검증)

### Phase 5: 테스트 + 배포 (1일)
- [ ] E2E 테스트 (10개 시나리오)
- [ ] 데이터 검증 (RLS 확인)
- [ ] 성능 모니터링 설정
- [ ] 배포 (Stage → Production)

---

## 📚 참고 자료

### 생성된 문서
- `docs/01-plan/features/dashboard-kpi.plan.md` — 요구사항 정의
- `docs/02-design/features/dashboard-kpi.design.md` — 기술 설계

### 기존 참고 문서
- `docs/02-design/features/dashboard.design.md` — 기존 9개 위젯
- `database/migrations/004_performance_views.sql` — proposal_results + MV
- `CLAUDE.md` — 프로젝트 개요

---

## 📊 통계

| 항목 | 수치 |
|------|------|
| 생성 문서 | 2개 |
| 총 라인 수 | 1,235줄 |
| 섹션 수 | 32개 |
| API 엔드포인트 | 3개 |
| 메트릭 타입 | 4개 (Individual/Team/Dept/Exec) |
| 핵심 메트릭 | 12개 |
| Frontend 컴포넌트 | 6개 |
| 예상 구현 일정 | 5-6일 |
| 테스트 목표 | 80% API, 70% UI |

---

## ✨ 주요 특징

1. **4가지 대시보드 유형** — 역할별 자동 스코핑
2. **실시간 성능** — p95 < 1초 (캐싱)
3. **월간 추이 분석** — 12개월 Time-series 데이터
4. **드릴다운 기능** — 대시보드 → 상세 데이터
5. **역할 기반 접근** — RLS + 서버 사이드 필터링
6. **경쟁사 분석** — 낙찰율 + 벤치마크
7. **포지셔닝 정확도** — Treemap 시각화
8. **필터/정렬** — 기간/팀/지역/포지셔닝

---

## 🎓 학습 포인트

### 1. 메트릭 정의의 중요성
- SQL aggregation 기반 메트릭이 정확성 보장
- Materialized View로 사전 계산 → 성능 향상

### 2. 캐싱 전략
- Event-driven 무효화 → 데이터 신선도 + 성능
- TTL 설정으로 메모리 효율성 확보

### 3. 접근 제어 설계
- 서버 사이드 필터링 필수 (클라이언트 우회 방지)
- RLS + 애플리케이션 로직 2중 검증

### 4. Frontend 확장성
- 컴포넌트 모듈화로 대시보드 추가 용이
- Recharts로 다양한 차트 타입 지원

---

**문서 작성 완료**: 2026-04-20 10:00 UTC  
**다음 단계**: Phase 1 DB 마이그레이션 시작 (예정: 2026-04-21)
