/**
 * Dashboard KPI — 타입 정의 (Day 3 frontend)
 *
 * - 개인/팀/본부/경영진 대시보드 공용 타입
 * - API 응답 스키마 매핑
 */

// ── 대시보드 유형 ──

export type DashboardType = "individual" | "team" | "department" | "executive";

// ── KPI 카드 공용 타입 ──

export interface MetricCard {
  title: string;
  value: number | string;
  unit?: string;
  format?: "number" | "percent" | "currency";
  trend?: {
    value: number;
    direction: "up" | "down" | "flat";
  };
  status?: "success" | "warning" | "danger" | "neutral";
}

// ── 개인 대시보드 ──

export interface IndividualMetrics {
  win_rate: number; // 0.0~1.0
  proposals_count: number;
  avg_cycle_time_days: number;
  success_rate: number; // 0.0~1.0
  total_value_won: number;
  positioning_accuracy: number; // 0.0~1.0
  monthly_proposals: Array<{
    month: string; // YYYY-MM
    count: number;
  }>;
  positioning_distribution: Array<{
    type: "defensive" | "offensive" | "adjacent";
    count: number;
  }>;
  in_progress_proposals: Array<{
    id: string;
    title: string;
    status: string;
    deadline: string;
    value: number;
  }>;
}

// ── 팀 대시보드 ──

export interface TeamMember {
  id: string;
  name: string;
  win_rate: number;
  proposals_count: number;
  contribution_percentage: number;
}

export interface TeamMetrics {
  win_rate: number;
  proposals_count: number;
  avg_price: number;
  team_utilization: number; // 0.0~1.0
  positioning_success: number; // 0.0~1.0
  avg_cycle_time_days: number;
  value_won: number;
  cost_per_win: number;
  quality_score: number; // 0.0~1.0
  risk_score: number; // 0.0~1.0
  team_comparison: Array<{
    team_id: string;
    team_name: string;
    win_rate: number;
  }>;
  monthly_trend: Array<{
    month: string; // YYYY-MM
    won: number;
    failed: number;
  }>;
  team_members: TeamMember[];
}

// ── 본부 대시보드 ──

export interface DepartmentMetrics {
  target_vs_actual: {
    target: number;
    actual: number;
    percentage: number; // 0.0~1.0
  };
  team_performance: Array<{
    team_id: string;
    team_name: string;
    win_rate: number;
    proposals_count: number;
  }>;
  competitor_analysis: Array<{
    competitor_name: string;
    win_rate: number;
  }>;
  avg_price: number;
  positioning_accuracy: number; // 0.0~1.0
  quarterly_trend: Array<{
    quarter: string; // Q1 2026
    proposals_count: number;
    won_count: number;
  }>;
  team_details: Array<{
    team_id: string;
    team_name: string;
    win_rate: number;
    total_proposals: number;
    total_value: number;
    avg_cycle_days: number;
  }>;
}

// ── 경영진 대시보드 ──

export interface ExecutiveMetrics {
  company_win_rate: number; // 0.0~1.0
  monthly_proposals_count: number;
  avg_win_amount: number;
  positioning_accuracy: number; // 0.0~1.0
  monthly_summary: {
    proposals_count: number;
    won_count: number;
    month_over_month_change: number; // 퍼센트 포인트
  };
  quarterly_trend: Array<{
    quarter: string; // Q1 2026
    proposals_count: number;
    won_count: number;
  }>;
  department_performance: Array<{
    department_id: string;
    department_name: string;
    win_rate: number;
    proposals_count: number;
  }>;
  positioning_accuracy_trend: Array<{
    month: string; // YYYY-MM
    accuracy: number; // 0.0~1.0
  }>;
}

// ── API 응답 ──

export interface DashboardMetricsResponse {
  success: boolean;
  data: {
    metrics:
      | IndividualMetrics
      | TeamMetrics
      | DepartmentMetrics
      | ExecutiveMetrics;
    cache_hit: boolean;
    cache_ttl_seconds: number;
    timestamp: string;
  };
}

// ── 필터 ──

export interface DashboardFilters {
  period: "ytd" | "mtd" | "custom";
  custom_start_date?: string; // YYYY-MM-DD
  custom_end_date?: string; // YYYY-MM-DD
  team_id?: string;
  metric?: string;
}

// ── 차트 데이터 ──

export interface ChartDataPoint {
  name: string;
  value: number;
  [key: string]: string | number;
}

// ── 테이블 행 ──

export interface TableRow {
  [key: string]: string | number | boolean;
}
