# 팀/본부/전사 KPI 대시보드 기술 설계 (Design)

**버전**: v1.0
**작성일**: 2026-04-20
**상태**: DRAFT

---

## 1. 설계 개요

이 문서는 팀장/본부장/경영진을 위한 **KPI 대시보드**의 기술 설계를 정의합니다.

**범위:**
- 4가지 대시보드 유형 (Individual / Team / Department / Executive)
- 3개 API 엔드포인트 (metrics / timeline / details)
- 데이터 파이프라인 (DB aggregation → Cache → API response)
- Frontend 컴포넌트 (MetricsCard / Charts / Tables)

**설계 원칙:**
- **성능**: p95 응답 < 1초 (캐싱 + 쿼리 최적화)
- **정확성**: 메트릭 계산 자동화 (SQL aggregation)
- **확장성**: 메트릭 추가 용이 (신규 dashboard_metrics_history)
- **보안**: RLS + 역할 기반 데이터 필터링

---

## 2. 아키텍처

### 2.1 데이터 파이프라인

```
┌─────────────────────────────────────────────────────────────────┐
│ Database Layer                                                  │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ proposals + proposal_results                                 ││
│ │ + teams + divisions + users                                  ││
│ │                                                              ││
│ │ Materialized Views:                                          ││
│ │ • mv_team_performance (팀별 win_rate, total_proposals)       ││
│ │ • mv_positioning_accuracy (포지셔닝별 win_rate)              ││
│ │ • dashboard_metrics_history (월별 이력)                      ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Cache Layer (Redis)                                             │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ Key: dashboard:{type}:{user_id}                             ││
│ │ TTL: 5분 (metrics, timeline)                               ││
│ │ Value: JSON (metrics, timeline_data)                        ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Backend (FastAPI)                                               │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ GET /api/dashboard/metrics/{type}                           ││
│ │ GET /api/dashboard/timeline/{type}                          ││
│ │ GET /api/dashboard/details/{type}                           ││
│ │                                                             ││
│ │ Service: DashboardMetricsService                            ││
│ │ • compute_metrics() — KPI 계산                             ││
│ │ • fetch_timeline() — 월별 이력 조회                         ││
│ │ • scope_data() — 역할 기반 필터링                           ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│ Frontend (React + Recharts)                                     │
│ ┌─────────────────────────────────────────────────────────────┐│
│ │ DashboardLayout                                             ││
│ │ ├── MetricsCard (KPI 카드)                                 ││
│ │ ├── TimelineChart (월별 추이)                               ││
│ │ ├── TeamComparisonTable (팀별 비교)                         ││
│ │ ├── CompetitorAnalysisChart (경쟁사)                        ││
│ │ └── FilterPanel (필터 UI)                                   ││
│ └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. 데이터 스키마

### 3.1 신규 테이블

```sql
-- dashboard_metrics_history: 월별 메트릭 이력
CREATE TABLE dashboard_metrics_history (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- 메타데이터
    metric_type TEXT NOT NULL,           -- 'team_performance' | 'positioning_accuracy' | 'competitor_analysis'
    period DATE NOT NULL,                -- YYYY-MM-01 (월별)
    
    -- 조직 구조
    org_id UUID REFERENCES organizations(id),
    division_id UUID REFERENCES divisions(id),
    team_id UUID REFERENCES teams(id),
    
    -- 메트릭
    metric_key TEXT NOT NULL,            -- 'win_rate' | 'total_proposals' | 'total_won_amount' | ...
    metric_value DECIMAL(10,2),          -- 수치 값
    metric_string TEXT,                  -- 문자열 값 (예: positioning name)
    
    -- 메타
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);

-- 인덱스
CREATE INDEX idx_dmh_period ON dashboard_metrics_history(period DESC);
CREATE INDEX idx_dmh_team_period ON dashboard_metrics_history(team_id, period DESC);
CREATE INDEX idx_dmh_division_period ON dashboard_metrics_history(division_id, period DESC);
CREATE INDEX idx_dmh_metric_type ON dashboard_metrics_history(metric_type, period DESC);

-- RLS
ALTER TABLE dashboard_metrics_history ENABLE ROW LEVEL SECURITY;
CREATE POLICY "dashboard_metrics_team_policy" ON dashboard_metrics_history
    FOR SELECT USING (
        team_id IS NULL
        OR team_id IN (
            SELECT team_id FROM users WHERE id = auth.uid()
        )
        OR division_id IN (
            SELECT division_id FROM users WHERE id = auth.uid()
        )
        OR org_id IN (
            SELECT org_id FROM users WHERE id = auth.uid()
        )
    );
```

### 3.2 기존 테이블 활용

**mv_team_performance** (기존 — 확장)
```sql
-- 기존:
-- team_id, team_name, division_name, total_proposals, won_count, lost_count, 
-- win_rate, total_won_amount, avg_tech_score, quarter

-- 추가 메타데이터 (선택):
-- team_lead_id, team_size, positioning_count (by positioning)
```

**mv_positioning_accuracy** (기존 — 확장)
```sql
-- 기존:
-- positioning, total, won, lost, win_rate

-- 추가 메타데이터 (선택):
-- division_id, team_id (positioning 기반 팀 추적)
```

---

## 4. 핵심 메트릭 계산 로직

### 4.1 팀 대시보드 (Team)

**메트릭 정의:**

```python
# Metric 1: 팀 수주율 (Win Rate)
metric = {
    "key": "team_win_rate",
    "label": "팀 수주율",
    "period": "YTD",
    "value": ROUND(
        COUNT(proposal WHERE status='won' AND team_id=X) /
        NULLIF(COUNT(proposal WHERE status IN ('won','lost') AND team_id=X), 0) * 100
    ),
    "unit": "%",
    "target": 45,  # 기준선
    "trend": "up" | "down" | "neutral"  # 전월 대비
}

# Metric 2: 팀 수주 금액 (Total Won Amount)
metric = {
    "key": "team_total_won_amount",
    "label": "수주 금액",
    "period": "YTD",
    "value": SUM(final_price WHERE result='won' AND team_id=X),
    "unit": "원",
    "target": 5000000000,  # 목표 금액
    "trend": "up" | "down"
}

# Metric 3: 평균 건당 금액 (Average Deal Size)
metric = {
    "key": "team_avg_deal_size",
    "label": "평균 건당 금액",
    "value": AVG(final_price WHERE result='won' AND team_id=X),
    "unit": "원"
}

# Metric 4: 포지셔닝별 성공률
metric = {
    "positioning": "Primary",
    "win_rate": 55.2,
    "total": 23,
    "won": 13,
    "unit": "%"
}
```

**SQL 예시:**
```sql
-- Team Win Rate (YTD)
SELECT
    ROUND(
        COUNT(*) FILTER (WHERE p.status='won')::numeric /
        NULLIF(COUNT(*) FILTER (WHERE p.status IN ('won','lost')), 0) * 100, 1
    ) AS win_rate
FROM proposals p
WHERE p.team_id = $1
  AND DATE_TRUNC('year', p.created_at) = DATE_TRUNC('year', now());
```

### 4.2 본부 대시보드 (Department)

**메트릭 정의:**

```python
# Metric 1: 본부 수주율 vs 목표
metric = {
    "key": "division_win_rate_vs_target",
    "label": "수주율 vs 목표",
    "actual": 42.5,  # 실적
    "target": 45.0,  # 목표
    "variance": -2.5,  # %
    "status": "below_target"
}

# Metric 2: 팀별 성과 비교 (테이블)
metrics = [
    {
        "team_name": "팀A",
        "win_rate": 48.2,
        "total_proposals": 25,
        "won_count": 12,
        "total_won_amount": 2500000000,
        "avg_deal_size": 208000000
    },
    ...
]

# Metric 3: 경쟁사 분석 (최근 3개월)
metric = {
    "competitors": [
        {
            "competitor_name": "경쟁사A",
            "our_lost_to_them": 5,
            "lost_rate": 25.0,  # (5 / 20) * 100
            "trend": "up"  # 최근 악화
        },
        ...
    ]
}
```

**SQL 예시:**
```sql
-- Division Team Comparison
SELECT
    t.id AS team_id,
    t.name AS team_name,
    COUNT(*) FILTER (WHERE p.status IN ('won','lost')) AS total,
    COUNT(*) FILTER (WHERE p.status='won') AS won,
    ROUND(
        COUNT(*) FILTER (WHERE p.status='won')::numeric /
        NULLIF(COUNT(*) FILTER (WHERE p.status IN ('won','lost')), 0) * 100, 1
    ) AS win_rate,
    SUM(p.result_amount) FILTER (WHERE p.status='won') AS total_won_amount
FROM proposals p
JOIN teams t ON t.id = p.team_id
WHERE t.division_id = $1
  AND p.status IN ('won', 'lost', 'cancelled')
GROUP BY t.id, t.name
ORDER BY win_rate DESC;
```

### 4.3 경영진 대시보드 (Executive)

**메트릭 정의:**

```python
# Metric 1: 전사 KPI (카드)
metric = {
    "key": "org_kpi",
    "cards": [
        {
            "label": "수주율",
            "value": 43.2,
            "unit": "%",
            "trend": "up",
            "period": "YTD"
        },
        {
            "label": "수주 금액",
            "value": 15000000000,
            "unit": "원",
            "trend": "up"
        },
        {
            "label": "제안 건수",
            "value": 87,
            "unit": "건"
        }
    ]
}

# Metric 2: 분기별 추이
metric = {
    "key": "quarterly_trend",
    "data": [
        {
            "quarter": "2025-Q1",
            "win_rate": 40.5,
            "total_amount": 3200000000,
            "proposal_count": 21
        },
        {
            "quarter": "2025-Q2",
            "win_rate": 42.1,
            "total_amount": 3600000000,
            "proposal_count": 24
        },
        ...
    ]
}

# Metric 3: 포지셔닝별 정확도 (Treemap)
metric = {
    "key": "positioning_accuracy_treemap",
    "data": [
        {
            "positioning": "Primary",
            "size": 45,  # win_rate %
            "count": 30,  # total proposals
            "color": "green"  # green (>50%) / yellow (40-50%) / red (<40%)
        },
        ...
    ]
}
```

---

## 5. API 설계

### 5.1 GET /api/dashboard/metrics/{dashboard_type}

**개요**: 실시간 KPI 조회 (캐시 활용)

**파라미터:**
```typescript
interface MetricsRequest {
    dashboard_type: "individual" | "team" | "department" | "executive",
    period?: "ytd" | "mtd" | "last_month" | "custom",  // default: "ytd"
    custom_start_date?: string,  // YYYY-MM-DD
    custom_end_date?: string,    // YYYY-MM-DD
}
```

**응답 (개인):**
```json
{
    "dashboard_type": "individual",
    "user_id": "uuid",
    "period": "ytd",
    "generated_at": "2026-04-20T10:00:00Z",
    "metrics": {
        "in_progress_proposals": 5,
        "completed_this_month": 2,
        "recent_won": 1,
        "recent_lost": 0,
        "total_amount_won": 500000000
    },
    "cache_hit": true,
    "cache_ttl_seconds": 240
}
```

**응답 (팀):**
```json
{
    "dashboard_type": "team",
    "team_id": "uuid",
    "team_name": "영업팀1",
    "period": "ytd",
    "generated_at": "2026-04-20T10:00:00Z",
    "metrics": {
        "win_rate": 48.2,
        "total_proposals": 25,
        "won_count": 12,
        "total_won_amount": 2500000000,
        "avg_deal_size": 208333333,
        "avg_tech_score": 82.5,
        "team_size": 5,
        "month_over_month_change": 2.3  // %
    },
    "positioning_breakdown": [
        {
            "positioning": "Primary",
            "win_rate": 55.2,
            "total": 23,
            "won": 13
        },
        {
            "positioning": "Secondary",
            "win_rate": 40.0,
            "total": 10,
            "won": 4
        }
    ],
    "cache_hit": true,
    "cache_ttl_seconds": 240
}
```

**응답 (본부):**
```json
{
    "dashboard_type": "department",
    "division_id": "uuid",
    "division_name": "영업본부",
    "period": "ytd",
    "generated_at": "2026-04-20T10:00:00Z",
    "metrics": {
        "win_rate": 42.5,
        "target_win_rate": 45.0,
        "variance": -2.5,
        "status": "below_target",
        "total_proposals": 87,
        "total_won_amount": 8500000000
    },
    "team_comparison": [
        {
            "team_id": "uuid",
            "team_name": "영업팀1",
            "win_rate": 48.2,
            "won_count": 12,
            "total_proposals": 25,
            "total_won_amount": 2500000000,
            "rank": 1
        },
        ...
    ],
    "competitor_top_3": [
        {
            "competitor_name": "경쟁사A",
            "lost_to_them_count": 5,
            "lost_rate": 25.0,
            "trend": "up"
        },
        ...
    ]
}
```

**응답 (경영진):**
```json
{
    "dashboard_type": "executive",
    "org_id": "uuid",
    "period": "ytd",
    "generated_at": "2026-04-20T10:00:00Z",
    "metrics": {
        "overall_win_rate": 43.2,
        "total_won_amount": 15000000000,
        "total_proposal_count": 87,
        "avg_proposal_value": 172413793
    },
    "division_comparison": [
        {
            "division_id": "uuid",
            "division_name": "영업본부",
            "win_rate": 42.5,
            "target_win_rate": 45.0,
            "total_proposals": 87,
            "total_won_amount": 8500000000,
            "status": "below_target"
        },
        ...
    ]
}
```

**HTTP 상태:**
- 200 OK (캐시 히트 또는 신규 계산)
- 400 Bad Request (파라미터 오류)
- 401 Unauthorized (미인증)
- 403 Forbidden (접근 권한 없음)

---

### 5.2 GET /api/dashboard/timeline/{dashboard_type}

**개요**: 월별 이력 조회 (최근 12개월 + 추이)

**파라미터:**
```typescript
interface TimelineRequest {
    dashboard_type: "team" | "department" | "executive",
    months: number = 12,  // 최근 N개월
    metric: "win_rate" | "total_amount" | "proposal_count"  // default: all
}
```

**응답:**
```json
{
    "dashboard_type": "team",
    "team_id": "uuid",
    "metric": "win_rate",
    "data": [
        {
            "month": "2025-05",
            "period_label": "May 2025",
            "win_rate": 35.0,
            "proposal_count": 20,
            "won_count": 7,
            "total_amount": 1200000000
        },
        {
            "month": "2025-06",
            "period_label": "Jun 2025",
            "win_rate": 42.1,
            "proposal_count": 24,
            "won_count": 10,
            "total_amount": 1800000000
        },
        ...
    ],
    "summary": {
        "trend": "up",  // up | down | flat
        "avg_win_rate": 41.2,
        "best_month": "2025-08",
        "best_month_value": 48.2
    }
}
```

---

### 5.3 GET /api/dashboard/details/{dashboard_type}

**개요**: 상세 데이터 드릴다운 (필터/정렬)

**파라미터:**
```typescript
interface DetailsRequest {
    dashboard_type: "team" | "department" | "executive",
    filter_type: "team" | "region" | "client" | "positioning",
    filter_value?: string,                          // 팀ID / 지역 / 기관명 / positioning
    sort_by?: "win_rate" | "amount" | "date",     // default: win_rate
    sort_order?: "asc" | "desc",
    limit?: number = 50,
    offset?: number = 0
}
```

**응답 (필터: 팀별):**
```json
{
    "dashboard_type": "department",
    "filter_type": "team",
    "total_count": 5,
    "data": [
        {
            "team_id": "uuid",
            "team_name": "영업팀1",
            "team_lead": "김팀장",
            "team_size": 5,
            "win_rate": 48.2,
            "total_proposals": 25,
            "won_count": 12,
            "total_won_amount": 2500000000,
            "recent_projects": [
                {
                    "proposal_id": "uuid",
                    "title": "프로젝트A",
                    "result": "won",
                    "amount": 300000000,
                    "result_date": "2026-04-15"
                },
                ...
            ]
        },
        ...
    ]
}
```

---

## 6. 캐싱 전략

### 6.1 Redis 캐시 키 구조

```
dashboard:metrics:{type}:{user_id}:{period}
  → TTL: 5분
  → Value: MetricsResponse (JSON)

dashboard:timeline:{type}:{user_id}:{metric}
  → TTL: 10분 (Timeline은 덜 자주 변경)
  → Value: TimelineResponse (JSON)

dashboard:details:{type}:{filter_type}:{filter_value}
  → TTL: 5분
  → Value: DetailsResponse (JSON)
```

### 6.2 캐시 무효화 전략

**Event-driven 무효화:**
```python
# Event: Proposal 생성/수정/완료
on_proposal_updated(proposal_id):
    # 팀 대시보드 무효화
    cache.delete(f"dashboard:metrics:team:{proposal.team_lead_id}:*")
    
    # 본부 대시보드 무효화
    division = proposal.team.division
    for user in division.users:
        cache.delete(f"dashboard:metrics:department:{user.id}:*")
    
    # 전사 대시보드 무효화
    cache.delete("dashboard:metrics:executive:*:*")

# Event: proposal_results 업데이트 (수주/낙찰 시)
on_result_registered(proposal_id, result):
    on_proposal_updated(proposal_id)
    cache.delete(f"dashboard:timeline:*:*:*")  # timeline도 무효화
```

---

## 7. 역할 기반 접근 제어 (RBAC)

### 7.1 권한 매트릭스

| 대시보드 | 개인 | 팀장 | 본부장 | 경영진 |
|---------|------|------|--------|-------|
| Individual (자기 제안) | ✅ | ✅ | ✅ | ✅ |
| Team (팀 데이터) | ✅ 팀원 데이터만 | ✅ | ❌ | ❌ |
| Department (본부 데이터) | ❌ | ❌ | ✅ | ✅ |
| Executive (전사 데이터) | ❌ | ❌ | ❌ | ✅ |

### 7.2 서버 사이드 필터링 (Python)

```python
async def get_dashboard_metrics(
    dashboard_type: str,
    current_user: User = Depends(get_current_user)
) -> MetricsResponse:
    # 권한 검증
    if dashboard_type == "team":
        if current_user.role not in ["lead", "director", "executive"]:
            raise HTTPException(403, "팀 대시보드 접근 권한 없음")
        team_id = current_user.team_id
    
    elif dashboard_type == "department":
        if current_user.role not in ["director", "executive"]:
            raise HTTPException(403, "본부 대시보드 접근 권한 없음")
        division_id = current_user.division_id
    
    elif dashboard_type == "executive":
        if current_user.role != "executive":
            raise HTTPException(403, "경영진 대시보드 접근 권한 없음")
        org_id = current_user.org_id
    
    # 캐시 조회
    cache_key = f"dashboard:metrics:{dashboard_type}:{current_user.id}"
    if cached := await cache.get(cache_key):
        return cached
    
    # DB 쿼리 (필터 적용)
    metrics = await compute_metrics(dashboard_type, current_user)
    
    # 캐시 저장
    await cache.set(cache_key, metrics, ex=300)
    return metrics
```

---

## 8. Frontend 컴포넌트 설계

### 8.1 컴포넌트 트리

```
DashboardLayout
├── Header
│   ├── Title ("대시보드")
│   ├── ScopeSelector (tabs: "팀" | "본부" | "전체")
│   └── FilterPanel
│       ├── DateRangePicker
│       ├── TeamFilter
│       ├── RegionFilter
│       └── PositioningFilter
│
├── MetricsSection
│   ├── MetricsCard (KPI 1)
│   │   ├── Label
│   │   ├── Value
│   │   ├── Unit
│   │   ├── TrendIndicator (↑/↓)
│   │   └── TargetLine
│   ├── MetricsCard (KPI 2)
│   └── MetricsCard (KPI 3)
│
├── TimelineSection
│   ├── Title ("월별 추이")
│   └── TimelineChart (Recharts LineChart)
│       ├── XAxis (months)
│       ├── YAxis (win_rate / amount / count)
│       ├── Line (metric)
│       └── Tooltip
│
├── ComparisonSection (팀/본부/경영진용)
│   └── ComparisonTable
│       ├── Column: Team/Division Name
│       ├── Column: Win Rate
│       ├── Column: Total Amount
│       ├── Sorting
│       └── Pagination
│
└── AnalysisSection (경영진용)
    ├── CompetitorChart (BarChart)
    ├── PositioningTreemap
    └── ClientDistributionChart
```

### 8.2 MetricsCard 컴포넌트

```typescript
interface MetricsCardProps {
    label: string;
    value: number;
    unit: string;
    target?: number;
    trend?: "up" | "down" | "neutral";
    trend_percentage?: number;
    onClick?: () => void;  // 드릴다운
}

export function MetricsCard({
    label,
    value,
    unit,
    target,
    trend,
    trend_percentage
}: MetricsCardProps) {
    return (
        <Card className="bg-white p-4 rounded-lg shadow-sm">
            <div className="flex justify-between items-start">
                <div>
                    <p className="text-sm font-medium text-gray-600">{label}</p>
                    <p className="text-2xl font-bold text-gray-900">
                        {value.toLocaleString()} {unit}
                    </p>
                </div>
                <div className="text-right">
                    {trend && (
                        <div className={`text-sm font-semibold ${
                            trend === "up" ? "text-green-600" : "text-red-600"
                        }`}>
                            {trend === "up" ? "↑" : "↓"} {trend_percentage}%
                        </div>
                    )}
                </div>
            </div>
            {target && (
                <div className="mt-2 flex items-center justify-between">
                    <span className="text-xs text-gray-500">목표</span>
                    <span className="text-xs font-semibold text-gray-700">
                        {target.toLocaleString()} {unit}
                    </span>
                </div>
            )}
        </Card>
    );
}
```

### 8.3 TimelineChart 컴포넌트

```typescript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from "recharts";

export function TimelineChart({ data, metric }: TimelineChartProps) {
    return (
        <LineChart width={800} height={300} data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
                dataKey="month" 
                tick={{ fontSize: 12 }}
            />
            <YAxis 
                label={{ value: metric === "win_rate" ? "수주율 (%)" : "금액 (원)", angle: -90, position: "insideLeft" }}
            />
            <Tooltip 
                formatter={(value) => metric === "win_rate" ? `${value}%` : `${value.toLocaleString()}원`}
            />
            <Legend />
            <Line 
                type="monotone" 
                dataKey={metric} 
                stroke="#2563eb" 
                dot={{ fill: "#2563eb" }}
            />
        </LineChart>
    );
}
```

---

## 9. 데이터베이스 최적화

### 9.1 인덱스 전략

```sql
-- dashboard_metrics_history 인덱스
CREATE INDEX idx_dmh_period ON dashboard_metrics_history(period DESC);
CREATE INDEX idx_dmh_team_period ON dashboard_metrics_history(team_id, period DESC);
CREATE INDEX idx_dmh_division_period ON dashboard_metrics_history(division_id, period DESC);
CREATE INDEX idx_dmh_type_period ON dashboard_metrics_history(metric_type, period DESC);

-- proposals 인덱스 (기존 강화)
CREATE INDEX idx_proposals_team_status ON proposals(team_id, status);
CREATE INDEX idx_proposals_team_created ON proposals(team_id, created_at DESC);

-- proposal_results 인덱스 (기존 강화)
CREATE INDEX idx_proposal_results_result_created ON proposal_results(result, created_at DESC);
```

### 9.2 쿼리 최적화 팁

**BAD (N+1 문제):**
```python
teams = get_all_teams(division_id)
for team in teams:
    team.metrics = calculate_team_metrics(team.id)  # N번의 쿼리
```

**GOOD (단일 쿼리):**
```python
metrics = db.query("""
    SELECT
        t.id, t.name,
        COUNT(*) FILTER (WHERE p.status IN ('won','lost')) AS total,
        COUNT(*) FILTER (WHERE p.status='won') AS won,
        ...
    FROM proposals p
    JOIN teams t ON t.id = p.team_id
    WHERE t.division_id = $1
    GROUP BY t.id, t.name
""")
```

---

## 10. 에러 처리 및 Fallback

### 10.1 캐시 미스 시나리오

```python
async def get_dashboard_metrics(dashboard_type: str, user: User):
    cache_key = f"dashboard:metrics:{dashboard_type}:{user.id}"
    
    # 1차: 캐시 조회
    if cached := await cache.get(cache_key):
        return cached
    
    # 2차: DB 쿼리 + 계산
    try:
        metrics = await compute_metrics(dashboard_type, user)
        await cache.set(cache_key, metrics, ex=300)
        return metrics
    except Exception as e:
        # 3차: 최근 갱신된 데이터 반환 (stale cache)
        if stale := await cache.get(f"{cache_key}:stale"):
            logger.error(f"Dashboard metrics error, returning stale cache: {e}")
            return stale
        # 마지막: 기본값 반환
        return get_default_metrics(dashboard_type)
```

### 10.2 데이터 검증

```python
def validate_metrics(metrics: MetricsResponse) -> bool:
    """메트릭 유효성 검증"""
    # win_rate는 0~100%
    assert 0 <= metrics.win_rate <= 100
    # proposal_count는 0 이상
    assert metrics.total_proposals >= 0
    # won_count <= total_proposals
    assert metrics.won_count <= metrics.total_proposals
    return True
```

---

## 11. 배포 및 마이그레이션

### 11.1 DB 마이그레이션 순서

```sql
-- 1. dashboard_metrics_history 테이블 생성
CREATE TABLE dashboard_metrics_history (...);

-- 2. 기존 데이터 마이그레이션
INSERT INTO dashboard_metrics_history (...)
SELECT 
    ... FROM mv_team_performance
    UNION ALL
    ... FROM mv_positioning_accuracy;

-- 3. 인덱스 생성
CREATE INDEX idx_dmh_period ON dashboard_metrics_history(period DESC);

-- 4. MV 갱신 함수 추가 (선택)
CREATE OR REPLACE FUNCTION refresh_dashboard_history() ...;
```

### 11.2 API 배포 단계

1. **Stage 1**: 백엔드 API 배포 (no frontend yet)
2. **Stage 2**: 프론트엔드 컴포넌트 배포
3. **Stage 3**: 캐싱 레이어 활성화 (redis)
4. **Stage 4**: 성능 모니터링 + 쿼리 최적화

---

## 12. 모니터링 및 알림

### 12.1 주요 메트릭

```
- Dashboard API 응답 시간 (p95 < 1초)
- 캐시 히트율 (목표: > 80%)
- DB 쿼리 실행 시간 (p95 < 500ms)
- 데이터 신선도 (최대 5분)
```

### 12.2 알림 규칙

```yaml
alert_rules:
  - name: "DashboardMetricsResponseTime"
    threshold: "p95 > 2s"
    action: "log + page_on_call"
  
  - name: "CacheHitRateDropped"
    threshold: "hit_rate < 50%"
    action: "log + investigate"
  
  - name: "DataStalenessExceeded"
    threshold: "last_refresh > 10m"
    action: "trigger_refresh + alert"
```

---

## 13. 참고 자료

- [PLAN 문서](dashboard-kpi.plan.md)
- [기존 대시보드 설계](dashboard.design.md)
- [Proposal Results 스키마](../database/migrations/004_performance_views.sql)
- [Recharts 문서](https://recharts.org/)
