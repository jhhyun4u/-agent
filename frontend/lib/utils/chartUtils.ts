/**
 * Dashboard KPI — 차트 유틸 (Day 3 frontend)
 *
 * - Recharts 데이터 변환
 * - 포맷팅 함수
 * - 색상 팔레트
 */

import type {
  ChartDataPoint,
  TeamMember,
  TeamMetrics,
  DepartmentMetrics,
  IndividualMetrics,
} from "./dashboardTypes";

// ── 색상 팔레트 ──

export const CHART_COLORS = {
  success: "#3ecf8e",
  warning: "#f59e0b",
  danger: "#ef4444",
  info: "#3b82f6",
  secondary: "#8b5cf6",
  tertiary: "#ec4899",
  muted: "#8c8c8c",
  border: "#262626",
  bg: "#1c1c1c",
};

export const COLOR_ARRAY = [
  CHART_COLORS.success,
  CHART_COLORS.warning,
  CHART_COLORS.danger,
  CHART_COLORS.info,
  CHART_COLORS.secondary,
  CHART_COLORS.tertiary,
];

// ── 포맷팅 함수 ──

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`;
}

export function formatCurrency(value: number): string {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`;
  }
  if (value >= 1000) {
    return `${(value / 1000).toFixed(1)}K`;
  }
  return value.toString();
}

export function formatDays(days: number): string {
  return `${days}일`;
}

// ── 월별 데이터 변환 ──

export function transformMonthlyData(
  data: Array<{ month: string; count: number }>,
): ChartDataPoint[] {
  return data.map((d) => ({
    name: d.month,
    value: d.count,
  }));
}

// ── 팀 비교 데이터 변환 ──

export function transformTeamComparisonData(
  data: Array<{ team_id: string; team_name: string; win_rate: number }>,
): ChartDataPoint[] {
  return data.map((d) => ({
    name: d.team_name,
    value: parseFloat((d.win_rate * 100).toFixed(1)),
  }));
}

// ── 월별 추이 데이터 변환 ──

export function transformMonthlyTrendData(
  data: Array<{ month: string; won: number; failed: number }>,
): ChartDataPoint[] {
  return data.map((d) => ({
    name: d.month,
    won: d.won,
    failed: d.failed,
  }));
}

// ── 분기별 추이 데이터 변환 ──

export function transformQuarterlyTrendData(
  data: Array<{ quarter: string; proposals_count: number; won_count: number }>,
): ChartDataPoint[] {
  return data.map((d) => ({
    name: d.quarter,
    proposals: d.proposals_count,
    won: d.won_count,
  }));
}

// ── 부서 성과 비교 변환 ──

export function transformDepartmentComparisonData(
  data: Array<{
    department_id: string;
    department_name: string;
    win_rate: number;
    proposals_count: number;
  }>,
): ChartDataPoint[] {
  return data.map((d) => ({
    name: d.department_name,
    value: parseFloat((d.win_rate * 100).toFixed(1)),
    count: d.proposals_count,
  }));
}

// ── 경쟁사 비교 변환 ──

export function transformCompetitorComparisonData(
  data: Array<{ competitor_name: string; win_rate: number }>,
): ChartDataPoint[] {
  return data.map((d) => ({
    name: d.competitor_name,
    value: parseFloat((d.win_rate * 100).toFixed(1)),
  }));
}

// ── 포지셔닝 분포 변환 ──

export function transformPositioningDistributionData(
  data: Array<{ type: string; count: number }>,
): ChartDataPoint[] {
  const labels: Record<string, string> = {
    defensive: "🛡️ 수성형",
    offensive: "⚔️ 공격형",
    adjacent: "🔄 인접형",
  };

  return data.map((d) => ({
    name: labels[d.type] || d.type,
    value: d.count,
  }));
}

// ── 팀원 성과 변환 ──

export function transformTeamMembersData(
  members: TeamMember[],
): ChartDataPoint[] {
  return members
    .sort((a, b) => b.win_rate - a.win_rate)
    .map((m) => ({
      name: m.name,
      value: parseFloat((m.win_rate * 100).toFixed(1)),
      proposals: m.proposals_count,
    }));
}

// ── 포지셔닝 정확도 추이 변환 ──

export function transformAccuracyTrendData(
  data: Array<{ month: string; accuracy: number }>,
): ChartDataPoint[] {
  return data.map((d) => ({
    name: d.month,
    value: parseFloat((d.accuracy * 100).toFixed(1)),
  }));
}

// ── 상태 색상 ──

export function getStatusColor(
  value: number,
  threshold_high = 0.5,
  threshold_mid = 0.3,
): string {
  if (value >= threshold_high) return CHART_COLORS.success;
  if (value >= threshold_mid) return CHART_COLORS.warning;
  return CHART_COLORS.danger;
}

// ── 증감 방향 ──

export function getTrendDirection(
  current: number,
  previous: number,
): "up" | "down" | "flat" {
  if (current > previous) return "up";
  if (current < previous) return "down";
  return "flat";
}

// ── 포맷팅 통합 함수 ──

export function formatMetricValue(
  value: number,
  format: "number" | "percent" | "currency" = "number",
): string {
  switch (format) {
    case "percent":
      return formatPercent(value);
    case "currency":
      return formatCurrency(value);
    case "number":
    default:
      return value.toLocaleString("ko-KR", {
        maximumFractionDigits: 1,
      });
  }
}

// ── Tooltip 포맷팅 ──

export function formatTooltipValue(
  value: unknown,
  label: string,
  format: string = "number",
): string {
  if (typeof value !== "number") return "";

  if (format === "percent") {
    return `${label}: ${formatPercent(value / 100)}`;
  }
  if (format === "currency") {
    return `${label}: ${formatCurrency(value)}`;
  }
  return `${label}: ${value.toLocaleString("ko-KR")}`;
}
