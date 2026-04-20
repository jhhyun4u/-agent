# 팀/본부/전사 KPI 대시보드 기능 계획 (Plan)

**버전**: v1.0
**작성일**: 2026-04-20
**상태**: DRAFT

---

## 1. 개요

**목표**: 팀장/본부장/경영진이 실시간으로 **제안 성과, 팀 성능, 경쟁사 분석, 제안 타임라인**을 모니터링할 수 있는 **통합 KPI 대시보드** 구축

**핵심 가치**:
- 역할별 자동 스코핑 (팀 → 본부 → 전사)
- 실시간 메트릭 조회 (p95 응답 시간 < 1초)
- 월간 이력 추이 분석 (Time-series 데이터)
- 드릴다운 기능 (대시보드 위젯 → 상세 데이터)
- 역할 기반 접근 제어 (RLS)

---

## 2. 요구사항

### 2.1 기본 요구사항

| 요구사항 | 설명 | 우선도 |
|---------|------|--------|
| **4가지 대시보드 유형** | Individual (개인) / Team (팀장) / Department (본부장) / Executive (경영진) | 높음 |
| **실시간 메트릭 조회** | GET /api/dashboard/{type}/metrics — 핵심 KPI 즉시 응답 | 높음 |
| **월간 이력 조회** | GET /api/dashboard/{type}/timeline — 최근 12개월 추이 | 높음 |
| **상세 데이터 드릴다운** | GET /api/dashboard/{type}/details — 필터/정렬 기반 상세 조회 | 높음 |
| **역할 기반 접근 제어** | RLS 정책 + 데이터 스코핑 (팀 → 본부 → 전사) | 높음 |
| **캐싱 전략** | Redis 캐시 (TTL 5분) + DB 쿼리 최적화 | 중간 |
| **필터링** | 기간 / 팀 / 지역 / 포지셔닝 / 기관별 필터 | 중간 |
| **차트 렌더링** | Recharts로 라인/바/파이 차트 | 높음 |

### 2.2 핵심 메트릭 정의

#### 2.2.1 개인 (Individual)
- **진행 중인 제안서**: 상태별 건수 (초안 / 작성중 / 완료 / 대기)
- **이번달 진도**: 완료도 (%) / 남은 일정 (일)
- **최근 결과**: 수주/낙찰 건수 + 금액

#### 2.2.2 팀 (Team)
- **팀 성과 요약**: 올해 YTD 수주율 (%) / 팀원 평균 수주건수
- **팀 구성**: 팀장 + 팀원 (n명) + 멤버십 기간
- **월별 수주율 추이**: 12개월 Time-series (라인 그래프)
- **포지셔닝별 성공률**: Primary / Secondary / Joint Bid 별 수주율 (%)
- **기관별 수주 현황**: Top 5 기관별 수주건수 + 금액

#### 2.2.3 본부 (Department)
- **본부 목표 vs 실적**: YTD 수주율 / 목표 수주율 / Variance (%)
- **팀별 성과 비교**: 팀별 수주율 + 평균 건당 금액 (테이블)
- **경쟁사 분석**: 경쟁사별 낙찰율 + 최근 3개월 추이
- **지역별 성과**: 지역별 수주건수 + 금액 (막대 그래프)
- **마감 임박 프로젝트**: 결재 대기 / D-7 이내 마감 경고

#### 2.2.4 경영진 (Executive)
- **전사 KPI**: 전사 수주율 / 수주 금액 / 제안건수 (카드)
- **본부별 성과 비교**: 본부별 수주율 테이블 (정렬/필터 가능)
- **분기별 추이**: 분기별 수주율 + 금액 (콤보 차트)
- **포지셔닝 정확도**: 포지셔닝별 수주율 (Treemap)
- **경쟁사 벤치마크**: 우리 vs 주요 경쟁사 수주율 (비교 테이블)
- **기관별 집중도**: Top 10 발주기관별 누적 금액

### 2.3 데이터 범위

**입력 테이블:**
- `proposals` — 제안서 메타 (status, team_id, created_at, result_amount)
- `proposal_results` — 제안 결과 (result, final_price, competitor_count, ranking, tech_score)
- `teams` — 팀 정보
- `divisions` — 본부 정보
- `users` — 사용자 + 팀/본부 할당

**출력:**
- API 응답 (JSON) — `/api/dashboard/{type}/metrics`, `/api/dashboard/{type}/timeline`, `/api/dashboard/{type}/details`
- Frontend 렌더링 — 4가지 대시보드 레이아웃

**시간 범위:**
- 기본: 최근 12개월 + YTD
- 필터 가능: 사용자 선택 기간

---

## 3. 현황 분석

### 3.1 기존 구현

**Phase 4 완료 사항:**
- ✅ `proposal_results` 테이블 생성 (result, final_price, competitor_count, ranking, tech_score, won_by)
- ✅ `mv_team_performance` — 팀별 성과 집계 (win_rate, total_proposals, won_count, avg_tech_score)
- ✅ `mv_positioning_accuracy` — 포지셔닝별 수주율 (win_rate)
- ✅ 기존 대시보드 (`dashboard.design.md`) — 팀/본부/전체 스코프, 9개 위젯

**미구현 부분:**
- ❌ KPI 메트릭 API 엔드포인트 (metrics, timeline, details)
- ❌ 월간 이력 테이블 (Time-series 데이터 저장)
- ❌ 캐싱 레이어 (Redis)
- ❌ 대시보드 고도화 UI (Recharts 차트, 필터 UI)
- ❌ 백엔드 쿼리 최적화 (JOIN, aggregation)

### 3.2 의존성

**DB 테이블:**
- `proposals` (status, result_amount, team_id, created_at, positioning)
- `proposal_results` (result, final_price, competitor_count, ranking)
- `teams`, `divisions`, `users` (조직 구조)
- `mv_team_performance`, `mv_positioning_accuracy` (기존 뷰)

**내부 서비스:**
- `app/services/token_manager.py` — 토큰 관리 (기존)
- `app/services/ai_status_manager.py` — 상태 추적 (기존)

**외부 라이브러리:**
- `Recharts` — 차트 렌더링 (프론트)
- `Redis` — 캐싱 (옵션)

---

## 4. 구현 범위

### 4.1 백엔드 (API)

**새 엔드포인트:**

| 메서드 | 경로 | 기능 | 데이터 크기 |
|--------|------|------|----------|
| GET | `/api/dashboard/metrics/{dashboard_type}` | 실시간 KPI 조회 (팀/본부/전사) | ~1KB |
| GET | `/api/dashboard/timeline/{dashboard_type}` | 월간 이력 (12개월) | ~5KB |
| GET | `/api/dashboard/details/{dashboard_type}` | 상세 데이터 (필터/정렬) | ~50KB |
| GET | `/api/dashboard/team-comparison` | 팀별 성과 비교 (테이블) | ~10KB |
| GET | `/api/dashboard/competitor-analysis` | 경쟁사 분석 | ~5KB |

**의존성:**
- `app/api/deps.py` — 인증 (get_current_user)
- `app/services/auth_service.py` — 역할 기반 스코핑
- `app/services/` — 새 서비스 생성 (DashboardMetricsService)

### 4.2 프론트엔드 (UI)

**새 컴포넌트:**

| 컴포넌트 | 기능 |
|---------|------|
| `DashboardLayout` | 4가지 대시보드 타입 + 스코프 탭 + 필터 UI |
| `MetricsCard` | KPI 카드 (숫자 + 추이 화살표) |
| `TimelineChart` | 월간 추이 (라인 그래프) |
| `TeamComparisonTable` | 팀별 성과 비교 (테이블) |
| `CompetitorAnalysisChart` | 경쟁사 벤치마크 (바 차트) |
| `FilterPanel` | 기간/팀/지역/포지셔닝 필터 |

**라이브러리:**
- `Recharts` — 차트
- `shadcn/ui` — UI 컴포넌트
- `react-query` — 데이터 페칭

### 4.3 데이터베이스

**새 테이블:**

```sql
-- 월간 메트릭 이력 (Time-series)
CREATE TABLE dashboard_metrics_history (
    id UUID PRIMARY KEY,
    metric_type TEXT,              -- 'team_performance' | 'positioning_accuracy' | ...
    period DATE,                   -- YYYY-MM-01 (월별)
    team_id UUID,                  -- NULL이면 전사/본부 수준
    division_id UUID,              -- NULL이면 전사 수준
    metric_key TEXT,               -- 'win_rate' | 'total_proposals' | ...
    metric_value DECIMAL(10,2),
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX idx_dashboard_metrics_period ON dashboard_metrics_history(period);
CREATE INDEX idx_dashboard_metrics_team ON dashboard_metrics_history(team_id, period);
```

**쿼리 최적화:**
- `mv_team_performance` 인덱스 확충 (division_id 추가)
- `proposal_results` 클러스터링 인덱스 (created_at)

---

## 5. 설계 원칙

| 원칙 | 설명 |
|------|------|
| **성능 우선** | p95 응답 시간 < 1초 (캐싱 + 쿼리 최적화) |
| **역할 기반** | RLS + 서버 사이드 스코핑으로 데이터 누수 방지 |
| **확장성** | 메트릭 추가 용이 (dashboard_metrics_history 신규) |
| **재사용성** | MetricsCard 등 컴포넌트 모듈화 |
| **신뢰성** | 데이터 일관성 (Materialized View 자동 갱신) |

---

## 6. 성공 기준

| 기준 | 목표 | 검증 방법 |
|------|------|---------|
| **응답 성능** | p95 < 1초 | 부하 테스트 (Apache JMeter) |
| **정확성** | 메트릭 계산 오류율 < 0.1% | Unit test (mock 데이터) |
| **데이터 가용성** | 월간 데이터 최소 12개월 | DB 쿼리 검증 |
| **접근 제어** | 역할별 데이터 누수 0건 | E2E 테스트 (RLS 검증) |
| **사용성** | 대시보드 로드 < 2초 | Chrome DevTools 측정 |
| **커버리지** | API 테스트 > 80%, UI 테스트 > 70% | Pytest + React Testing Library |

---

## 7. 위험요소 및 완화 전략

| 위험 | 영향 | 완화 전략 |
|------|------|---------|
| **Materialized View 갱신 지연** | 메트릭 최신성 저하 | 일일 자동 갱신 Job + 수동 갱신 API |
| **대규모 데이터 조회 성능** | 응답 시간 > 1초 | 월별 집계 테이블 + Redis 캐시 |
| **데이터 일관성** | 팀/본부 전환 시 데이터 불일치 | 트랜잭션 + 검증 쿼리 |
| **기존 대시보드와 중복** | 유지보수 복잡성 | 기존 9개 위젯과 명확 구분 (KPI ⊆ 기존 대시보드) |

---

## 8. 구현 일정 (예상)

| Phase | 작업 | 기간 |
|-------|------|------|
| 1 | DB 스키마 설계 + 마이그레이션 | 1일 |
| 2 | 백엔드 API (metrics, timeline, details) | 2일 |
| 3 | 프론트엔드 컴포넌트 + 통합 | 2일 |
| 4 | 캐싱 레이어 + 성능 최적화 | 1일 |
| 5 | 테스트 (Unit + Integration + E2E) | 1일 |
| **총 기간** | | **5-6일** |

---

## 9. 영향도

### 9.1 기존 시스템

**변경 영향:**
- `proposals` 테이블: 조회만 (변경 없음)
- `proposal_results` 테이블: 데이터 추가 (변경 없음)
- 기존 대시보드: 통합 (겹치는 위젯 없음)

**의존하는 기능:**
- 제안서 CRUD (제안 생성/수정 → proposal_results 갱신)
- 결재 시스템 (승인/거절 → proposal status 변경)
- G2B 공고 모니터링 (공고 데이터 입수)

### 9.2 신규 의존성

**추가 라이브러리:**
- Backend: `redis` (캐싱)
- Frontend: `recharts` (차트) — 기존 사용 중

---

## 10. 참고 자료

- [기존 대시보드 설계](../features/dashboard.design.md) — 9개 위젯, 스코프 정의
- [Proposal Results 스키마](../../database/migrations/004_performance_views.sql)
- [팀 성과 View](../../database/migrations/004_performance_views.sql#L39-L59)
